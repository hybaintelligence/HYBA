"""Customer access control plane for commercial QaaS and CIaaS APIs.

Provides admin API-key issuance, HMAC-SHA256 API-key authentication, tiered quotas,
request/monthly compute-unit metering, and optional Redis-backed distributed
counters/state via HYBA_REDIS_URL.

Enterprise Security Model:
- API keys are hashed using HMAC-SHA256 with a secret pepper (HYBA_API_KEY_SECRET)
- Redis failures are logged with structured error context (never silently swallowed)
- All exception paths include specific error types and observability hooks
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import secrets
import threading
import uuid
from datetime import datetime, timezone
UTC = timezone.utc
from typing import Any, Dict, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel, Field

from hyba_genesis_api.api.admin import require_admin
from hyba_genesis_api.auth.jwt_handler import TokenPayload
from hyba_genesis_api.core.telemetry import (
    record_billing_quota_rejection,
    record_billing_usage,
    set_billing_quota_remaining,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/customer-access", tags=["customer-access"])

# Separate router for admin customer API keys at the path expected by tests
admin_router = APIRouter(prefix="/api/admin", tags=["customer-access-admin"])

CustomerTier = Literal["developer", "production", "enterprise"]

DEFAULT_TIER_PRICING_USD_PER_UNIT: dict[CustomerTier, dict[str, float]] = {
    "developer": {"qaas": 0.0025, "ciaas": 0.0010, "default": 0.0010},
    "production": {"qaas": 0.0020, "ciaas": 0.0008, "default": 0.0008},
    "enterprise": {"qaas": 0.0015, "ciaas": 0.0006, "default": 0.0006},
}


class CustomerApiKeyIssueRequest(BaseModel):
    """Admin request to create an API key for a customer."""

    customer_id: str = Field(min_length=3, max_length=80)
    customer_name: str = Field(default="", min_length=0, max_length=80)
    tier: CustomerTier = "developer"
    monthly_compute_units: int = Field(default=1000, ge=1, le=10000000)
    monthly_requests: int = Field(default=10000, ge=1, le=10000000)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class APIKeyResponse(BaseModel):
    """Response containing the raw API key (only shown once)."""

    api_key: str
    customer_id: str
    customer_name: str
    tier: CustomerTier
    quota_requests_per_month: int
    quota_compute_units_per_month: int
    created_at: str
    key_id: str


class CustomerInfo(BaseModel):
    """Customer information for internal use."""

    customer_id: str
    customer_name: str
    tier: CustomerTier
    quota_requests_per_month: int
    quota_compute_units_per_month: int
    api_key_hash: str
    key_id: str
    created_at: str
    metadata: Dict[str, Any]
    pricing_usd_per_unit: Dict[str, float] = Field(default_factory=dict)


# Alias for compatibility with existing code
CustomerPrincipal = CustomerInfo


class UsageMetrics(BaseModel):
    """Current usage metrics for a customer."""

    requests_this_month: int
    compute_units_this_month: int
    requests_remaining: int
    compute_units_remaining: int
    month: str
    estimated_charges_usd: float = 0.0
    pricing_usd_per_unit: Dict[str, float] = Field(default_factory=dict)


class _CustomerRegistry:
    """Thread-safe registry for customer API keys and usage tracking.

    Enterprise-grade security:
    - HMAC-SHA256 for API key hashing with secret pepper
    - Structured error logging for all Redis operations
    - Explicit exception handling with observability
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._customers: Dict[str, CustomerInfo] = {}  # key_id -> CustomerInfo
        self._api_key_to_customer: Dict[str, str] = {}  # api_key_hash -> key_id
        self._usage: Dict[str, UsageMetrics] = {}  # key_id -> UsageMetrics
        self._local_counters: Dict[str, Dict[str, int]] = {}  # customer_id -> {product: count}

        # Load HMAC secret for API key hashing (required for enterprise security)
        self._hmac_secret = os.getenv("HYBA_API_KEY_SECRET")
        if not self._hmac_secret:
            # Generate ephemeral secret for development (single-instance only)
            self._hmac_secret = secrets.token_hex(32)
            logger.warning(
                "HYBA_API_KEY_SECRET not set; using ephemeral secret. "
                "Set HYBA_API_KEY_SECRET in production for distributed deployments."
            )

        # Optional Redis backing for distributed state
        self._redis_client: Optional[Any] = None
        self._redis_available = False
        redis_url = os.getenv("HYBA_REDIS_URL")
        if redis_url:
            try:
                import redis

                self._redis_client = redis.from_url(redis_url, decode_responses=True)
                self._redis_client.ping()
                self._redis_available = True
                logger.info("Redis connection established for distributed state")
            except (ImportError, ConnectionError, TimeoutError) as e:
                logger.error(
                    "Redis initialization failed",
                    extra={"error": str(e), "redis_url": redis_url},
                )
                self._redis_client = None
                self._redis_available = False

    def _hash_api_key(self, api_key: str) -> str:
        """Hash API key using HMAC-SHA256 with secret pepper.

        This is the enterprise standard for API key hashing:
        - Prevents rainbow table attacks via secret pepper
        - Fast enough for request-time authentication
        - Used by Stripe, AWS, GitHub, etc.
        """
        return hmac.new(
            self._hmac_secret.encode(),
            api_key.encode(),
            hashlib.sha256,
        ).hexdigest()

    def _tenant_hash(self, customer: CustomerInfo) -> str:
        return hashlib.sha256(customer.customer_id.encode()).hexdigest()[:16]

    def _pricing_for(self, tier: CustomerTier, metadata: Dict[str, Any]) -> Dict[str, float]:
        pricing = dict(DEFAULT_TIER_PRICING_USD_PER_UNIT[tier])
        override = metadata.get("pricing_usd_per_unit") if isinstance(metadata, dict) else None
        if isinstance(override, dict):
            for product, value in override.items():
                if isinstance(product, str) and isinstance(value, (int, float)) and value >= 0:
                    pricing[product] = float(value)
        return pricing

    def _unit_price(self, customer: CustomerInfo, product: str) -> float:
        family = product.split(".", 1)[0]
        return customer.pricing_usd_per_unit.get(
            product,
            customer.pricing_usd_per_unit.get(family, customer.pricing_usd_per_unit.get("default", 0.0)),
        )

    def _estimated_charge(self, customer: CustomerInfo, product: str, units: int) -> float:
        return round(max(0, units) * self._unit_price(customer, product), 6)

    def issue_key(self, request: CustomerApiKeyIssueRequest) -> APIKeyResponse:
        with self._lock:
            key_id = f"key-{uuid.uuid4().hex[:16]}"
            raw_api_key = f"hyba_live_{key_id}_{uuid.uuid4().hex[:24]}"
            api_key_hash = self._hash_api_key(raw_api_key)

            now = datetime.now(UTC).isoformat()
            customer = CustomerInfo(
                customer_id=request.customer_id,
                customer_name=request.customer_name,
                tier=request.tier,
                quota_requests_per_month=request.monthly_requests,
                quota_compute_units_per_month=request.monthly_compute_units,
                api_key_hash=api_key_hash,
                key_id=key_id,
                created_at=now,
                metadata=request.metadata,
                pricing_usd_per_unit=self._pricing_for(request.tier, request.metadata),
            )

            self._customers[key_id] = customer
            self._api_key_to_customer[api_key_hash] = key_id

            # Initialize usage metrics
            current_month = datetime.now(UTC).strftime("%Y-%m")
            usage = UsageMetrics(
                requests_this_month=0,
                compute_units_this_month=0,
                requests_remaining=request.monthly_requests,
                compute_units_remaining=request.monthly_compute_units,
                month=current_month,
                pricing_usd_per_unit=customer.pricing_usd_per_unit,
            )
            self._usage[key_id] = usage
            self._local_counters[request.customer_id] = {}

            # Back to Redis if available
            if self._redis_client:
                try:
                    self._redis_client.hset(
                        f"customer:{key_id}",
                        mapping={
                            "customer_id": customer.customer_id,
                            "customer_name": customer.customer_name,
                            "tier": customer.tier,
                            "quota_requests": str(customer.quota_requests_per_month),
                            "quota_compute": str(customer.quota_compute_units_per_month),
                            "api_key_hash": api_key_hash,
                            "created_at": now,
                        },
                    )
                    self._redis_client.set(f"api_key:{api_key_hash}", key_id)
                except (ConnectionError, TimeoutError) as e:
                    logger.error(
                        "Redis write failed during API key issuance",
                        extra={
                            "key_id": key_id,
                            "customer_id": customer.customer_id,
                            "error": str(e),
                        },
                    )
                    # Continue with in-memory state; Redis is best-effort distributed cache

            return APIKeyResponse(
                api_key=raw_api_key,
                customer_id=customer.customer_id,
                customer_name=customer.customer_name,
                tier=customer.tier,
                quota_requests_per_month=customer.quota_requests_per_month,
                quota_compute_units_per_month=customer.quota_compute_units_per_month,
                created_at=now,
                key_id=key_id,
            )

    def get_customer_by_api_key(self, api_key: str) -> CustomerInfo:
        api_key_hash = self._hash_api_key(api_key)

        # Check Redis first if available
        if self._redis_client:
            try:
                key_id = self._redis_client.get(f"api_key:{api_key_hash}")
                if key_id:
                    customer_data = self._redis_client.hgetall(f"customer:{key_id}")
                    if customer_data:
                        return CustomerInfo(
                            customer_id=customer_data["customer_id"],
                            customer_name=customer_data["customer_name"],
                            tier=customer_data["tier"],
                            quota_requests_per_month=int(customer_data["quota_requests"]),
                            quota_compute_units_per_month=int(customer_data["quota_compute"]),
                            api_key_hash=customer_data["api_key_hash"],
                            key_id=key_id,
                            created_at=customer_data["created_at"],
                            metadata={},
                            pricing_usd_per_unit=self._pricing_for(customer_data["tier"], {}),
                        )
            except (ConnectionError, TimeoutError, ValueError, KeyError) as e:
                logger.warning(
                    "Redis read failed during authentication; falling back to in-memory state",
                    extra={"error": str(e)},
                )

        # Fallback to in-memory
        with self._lock:
            key_id = self._api_key_to_customer.get(api_key_hash)
            if not key_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key",
                )
            return self._customers[key_id]

    def check_and_increment_usage(
        self, customer: CustomerInfo, request_cost: int = 1, compute_cost: int = 1
    ) -> UsageMetrics:
        key_id = customer.key_id
        current_month = datetime.now(UTC).strftime("%Y-%m")

        with self._lock:
            # Reset monthly counters if month changed
            if key_id not in self._usage or self._usage[key_id].month != current_month:
                self._usage[key_id] = UsageMetrics(
                    requests_this_month=0,
                    compute_units_this_month=0,
                    requests_remaining=customer.quota_requests_per_month,
                    compute_units_remaining=customer.quota_compute_units_per_month,
                    month=current_month,
                    pricing_usd_per_unit=customer.pricing_usd_per_unit,
                )

            usage = self._usage[key_id]

            # Check quota
            tenant_hash = self._tenant_hash(customer)
            if usage.requests_remaining < request_cost:
                record_billing_quota_rejection(tenant_hash, "requests", customer.tier)
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail="Monthly request quota exceeded",
                )
            if usage.compute_units_remaining < compute_cost:
                record_billing_quota_rejection(tenant_hash, "compute_units", customer.tier)
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail="Monthly compute unit quota exceeded",
                )

            # Increment usage
            usage.requests_this_month += request_cost
            usage.compute_units_this_month += compute_cost
            usage.requests_remaining -= request_cost
            usage.compute_units_remaining -= compute_cost
            set_billing_quota_remaining(
                self._tenant_hash(customer),
                customer.tier,
                usage.requests_remaining,
                usage.compute_units_remaining,
            )

            # Update Redis if available
            if self._redis_client:
                try:
                    self._redis_client.hincrby(f"usage:{key_id}", "requests", request_cost)
                    self._redis_client.hincrby(f"usage:{key_id}", "compute", compute_cost)
                except (ConnectionError, TimeoutError) as e:
                    logger.error(
                        "Redis usage increment failed",
                        extra={
                            "key_id": key_id,
                            "request_cost": request_cost,
                            "compute_cost": compute_cost,
                            "error": str(e),
                        },
                    )
                    # Critical: Usage tracking failure on metered platform
                    # In-memory state is authoritative; log for reconciliation

            return usage

    def get_usage_metrics(self, customer: CustomerInfo) -> UsageMetrics:
        key_id = customer.key_id
        current_month = datetime.now(UTC).strftime("%Y-%m")

        # Try Redis first
        if self._redis_client:
            try:
                usage_data = self._redis_client.hgetall(f"usage:{key_id}")
                if usage_data:
                    return UsageMetrics(
                        requests_this_month=int(usage_data.get("requests", 0)),
                        compute_units_this_month=int(usage_data.get("compute", 0)),
                        requests_remaining=customer.quota_requests_per_month
                        - int(usage_data.get("requests", 0)),
                        compute_units_remaining=customer.quota_compute_units_per_month
                        - int(usage_data.get("compute", 0)),
                        month=current_month,
                        estimated_charges_usd=self._usage.get(key_id, UsageMetrics(
                            requests_this_month=0,
                            compute_units_this_month=0,
                            requests_remaining=0,
                            compute_units_remaining=0,
                            month=current_month,
                        )).estimated_charges_usd,
                        pricing_usd_per_unit=customer.pricing_usd_per_unit,
                    )
            except (ConnectionError, TimeoutError, ValueError, KeyError) as e:
                logger.warning(
                    "Redis usage read failed; returning in-memory metrics",
                    extra={"key_id": key_id, "error": str(e)},
                )

        # Fallback to in-memory
        with self._lock:
            if key_id not in self._usage or self._usage[key_id].month != current_month:
                self._usage[key_id] = UsageMetrics(
                    requests_this_month=0,
                    compute_units_this_month=0,
                    requests_remaining=customer.quota_requests_per_month,
                    compute_units_remaining=customer.quota_compute_units_per_month,
                    month=current_month,
                    pricing_usd_per_unit=customer.pricing_usd_per_unit,
                )
            return self._usage[key_id]

    def meter(self, customer: CustomerInfo, product: str, units: int) -> Dict[str, Any]:
        """Record usage for a specific product and return usage meter data."""
        # Check quota before recording usage
        self.check_and_increment_usage(customer, request_cost=1, compute_cost=units)

        customer_id = customer.customer_id
        with self._lock:
            if customer_id not in self._local_counters:
                self._local_counters[customer_id] = {}
            if product not in self._local_counters[customer_id]:
                self._local_counters[customer_id][product] = 0
            self._local_counters[customer_id][product] += units
            estimated_charge = self._estimated_charge(customer, product, units)
            usage = self._usage[customer.key_id]
            usage.estimated_charges_usd = round(usage.estimated_charges_usd + estimated_charge, 6)
            usage.pricing_usd_per_unit = customer.pricing_usd_per_unit
            record_billing_usage(self._tenant_hash(customer), product, customer.tier, units, estimated_charge)
            return {
                "product": product,
                "units": units,
                "unit_price_usd": self._unit_price(customer, product),
                "estimated_charge_usd": estimated_charge,
                "currency": "USD",
                "quota_enforced": True,
            }

    def set_state(self, key: str, value: Any) -> None:
        """Store state for a given key."""
        with self._lock:
            if not hasattr(self, "_state"):
                self._state = {}
            self._state[key] = value


# Global registry instance
customer_access = _CustomerRegistry()
customer_registry = customer_access  # Alias for backward compatibility


async def require_api_key(x_api_key: str = Header(...)) -> CustomerInfo:
    """FastAPI dependency to authenticate and authorize API key."""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-API-Key header required",
        )
    return customer_registry.get_customer_by_api_key(x_api_key)


# Alias for compatibility with existing code
require_customer_api_key = require_api_key


@router.post("/api-keys", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    request: CustomerApiKeyIssueRequest,
    payload: TokenPayload = Depends(require_admin),
):
    """Admin endpoint to create an API key for a customer."""
    return customer_access.issue_key(request)


@admin_router.post("/customer-api-keys", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def issue_customer_api_key(
    request: CustomerApiKeyIssueRequest,
    payload: TokenPayload = Depends(require_admin),
):
    """Admin endpoint to issue an API key for a customer."""
    return customer_access.issue_key(request)


@router.get("/customers/{customer_id}/usage", response_model=UsageMetrics)
async def get_customer_usage(
    customer_id: str,
    payload: TokenPayload = Depends(require_admin),
):
    """Admin endpoint to get customer usage metrics."""
    # Find customer by customer_id
    for customer in customer_registry._customers.values():
        if customer.customer_id == customer_id:
            return customer_registry.get_usage_metrics(customer)
    raise HTTPException(status_code=404, detail="Customer not found")
