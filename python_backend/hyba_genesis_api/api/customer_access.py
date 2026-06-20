"""Customer access control plane for commercial QaaS and CIaaS APIs.

Provides admin API-key issuance, hashed API-key authentication, tiered quotas,
request/monthly compute-unit metering, and optional Redis-backed distributed
counters/state via HYBA_REDIS_URL.
"""

from __future__ import annotations

import hashlib
import os
import threading
import uuid
from datetime import UTC, datetime
from typing import Any, Dict, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel, Field

from hyba_genesis_api.api.admin import require_admin
from hyba_genesis_api.auth.jwt_handler import TokenPayload

router = APIRouter(prefix="/api/admin/customer-access", tags=["customer-access"])

CustomerTier = Literal["developer", "production", "enterprise"]


class APIKeyCreateRequest(BaseModel):
    """Admin request to create an API key for a customer."""

    customer_id: str = Field(min_length=3, max_length=80)
    customer_name: str = Field(min_length=3, max_length=80)
    tier: CustomerTier = "developer"
    quota_requests_per_month: int = Field(default=10000, ge=100, le=10000000)
    quota_compute_units_per_month: int = Field(default=1000, ge=100, le=10000000)
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


class UsageMetrics(BaseModel):
    """Current usage metrics for a customer."""

    requests_this_month: int
    compute_units_this_month: int
    requests_remaining: int
    compute_units_remaining: int
    month: str


class _CustomerRegistry:
    """Thread-safe registry for customer API keys and usage tracking."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._customers: Dict[str, CustomerInfo] = {}  # key_id -> CustomerInfo
        self._api_key_to_customer: Dict[str, str] = {}  # api_key_hash -> key_id
        self._usage: Dict[str, UsageMetrics] = {}  # key_id -> UsageMetrics

        # Optional Redis backing for distributed state
        self._redis_client: Optional[Any] = None
        redis_url = os.getenv("HYBA_REDIS_URL")
        if redis_url:
            try:
                import redis

                self._redis_client = redis.from_url(redis_url, decode_responses=True)
                self._redis_client.ping()
            except Exception:
                self._redis_client = None

    def _hash_api_key(self, api_key: str) -> str:
        return hashlib.sha256(api_key.encode()).hexdigest()

    def create_api_key(self, request: APIKeyCreateRequest) -> APIKeyResponse:
        with self._lock:
            key_id = f"key-{uuid.uuid4().hex[:16]}"
            raw_api_key = f"hyba-{key_id}-{uuid.uuid4().hex[:24]}"
            api_key_hash = self._hash_api_key(raw_api_key)

            now = datetime.now(UTC).isoformat()
            customer = CustomerInfo(
                customer_id=request.customer_id,
                customer_name=request.customer_name,
                tier=request.tier,
                quota_requests_per_month=request.quota_requests_per_month,
                quota_compute_units_per_month=request.quota_compute_units_per_month,
                api_key_hash=api_key_hash,
                key_id=key_id,
                created_at=now,
                metadata=request.metadata,
            )

            self._customers[key_id] = customer
            self._api_key_to_customer[api_key_hash] = key_id

            # Initialize usage metrics
            current_month = datetime.now(UTC).strftime("%Y-%m")
            usage = UsageMetrics(
                requests_this_month=0,
                compute_units_this_month=0,
                requests_remaining=request.quota_requests_per_month,
                compute_units_remaining=request.quota_compute_units_per_month,
                month=current_month,
            )
            self._usage[key_id] = usage

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
                except Exception:
                    pass

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
                        )
            except Exception:
                pass

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
                )

            usage = self._usage[key_id]

            # Check quota
            if usage.requests_remaining < request_cost:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Monthly request quota exceeded",
                )
            if usage.compute_units_remaining < compute_cost:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Monthly compute unit quota exceeded",
                )

            # Increment usage
            usage.requests_this_month += request_cost
            usage.compute_units_this_month += compute_cost
            usage.requests_remaining -= request_cost
            usage.compute_units_remaining -= compute_cost

            # Update Redis if available
            if self._redis_client:
                try:
                    self._redis_client.hincrby(f"usage:{key_id}", "requests", request_cost)
                    self._redis_client.hincrby(f"usage:{key_id}", "compute", compute_cost)
                except Exception:
                    pass

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
                    )
            except Exception:
                pass

        # Fallback to in-memory
        with self._lock:
            if key_id not in self._usage or self._usage[key_id].month != current_month:
                self._usage[key_id] = UsageMetrics(
                    requests_this_month=0,
                    compute_units_this_month=0,
                    requests_remaining=customer.quota_requests_per_month,
                    compute_units_remaining=customer.quota_compute_units_per_month,
                    month=current_month,
                )
            return self._usage[key_id]


# Global registry instance
customer_registry = _CustomerRegistry()


async def require_api_key(x_api_key: str = Header(...)) -> CustomerInfo:
    """FastAPI dependency to authenticate and authorize API key."""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-API-Key header required",
        )
    return customer_registry.get_customer_by_api_key(x_api_key)


@router.post("/api-keys", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    request: APIKeyCreateRequest,
    payload: TokenPayload = Depends(require_admin),
):
    """Admin endpoint to create an API key for a customer."""
    return customer_registry.create_api_key(request)


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
