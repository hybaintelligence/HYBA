"""Customer API-key authentication, metering, and optional Redis state for QaaS/CIaaS."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Dict, Literal, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status

from hyba_genesis_api.api.admin import require_admin
from pydantic import BaseModel, Field

try:
    import redis
except Exception:  # pragma: no cover - dependency is optional at import time
    redis = None  # type: ignore[assignment]

ApiKeyTier = Literal["developer", "production", "sovereign"]

_TIER_LIMITS: dict[ApiKeyTier, dict[str, int]] = {
    "developer": {"requests_per_minute": 60, "monthly_compute_units": 50_000},
    "production": {"requests_per_minute": 1_000, "monthly_compute_units": 10_000_000},
    "sovereign": {"requests_per_minute": 10_000, "monthly_compute_units": 1_000_000_000},
}


class CustomerApiKeyIssueRequest(BaseModel):
    customer_id: str = Field(
        min_length=3,
        max_length=80,
        pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_.:-]*$",
    )
    tier: ApiKeyTier = "production"
    requests_per_minute: Optional[int] = Field(default=None, ge=1, le=100_000)
    monthly_compute_units: Optional[int] = Field(default=None, ge=1, le=10_000_000_000)


class CustomerApiKeyIssueResponse(BaseModel):
    customer_id: str
    tier: ApiKeyTier
    api_key: str
    key_prefix: str
    quotas: Dict[str, int]
    created_at: str


@dataclass(frozen=True)
class CustomerPrincipal:
    customer_id: str
    tier: ApiKeyTier
    key_hash: str
    quotas: Dict[str, int]


class CustomerAccessRegistry:
    """Enterprise access-control façade with Redis-backed counters when configured.

    API keys are stored only as SHA-256 hashes.  Redis is used for horizontally
    shared metering and state snapshots when HYBA_REDIS_URL is present; otherwise
    deterministic in-process maps keep local tests and single-node deployments
    operational without changing public semantics.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._keys: dict[str, CustomerPrincipal] = {}
        self._local_counters: dict[str, int] = {}
        self._redis = None
        redis_url = os.getenv("HYBA_REDIS_URL")
        if redis_url and redis is not None:
            self._redis = redis.Redis.from_url(redis_url, decode_responses=True)

    def _hash_key(self, api_key: str) -> str:
        pepper = os.getenv("HYBA_CUSTOMER_KEY_PEPPER", "hyba-local-development-pepper")
        return hmac.new(pepper.encode(), api_key.encode(), hashlib.sha256).hexdigest()

    def issue_key(self, request: CustomerApiKeyIssueRequest) -> CustomerApiKeyIssueResponse:
        secret = f"hyba_live_{secrets.token_urlsafe(32)}"
        quotas = dict(_TIER_LIMITS[request.tier])
        if request.requests_per_minute is not None:
            quotas["requests_per_minute"] = request.requests_per_minute
        if request.monthly_compute_units is not None:
            quotas["monthly_compute_units"] = request.monthly_compute_units
        key_hash = self._hash_key(secret)
        principal = CustomerPrincipal(request.customer_id, request.tier, key_hash, quotas)
        with self._lock:
            self._keys[key_hash] = principal
        created_at = datetime.now(UTC).isoformat()
        self.set_state(
            f"customer:{request.customer_id}:profile",
            {"tier": request.tier, "quotas": quotas, "created_at": created_at},
        )
        return CustomerApiKeyIssueResponse(
            customer_id=request.customer_id,
            tier=request.tier,
            api_key=secret,
            key_prefix=secret[:18],
            quotas=quotas,
            created_at=created_at,
        )

    def authenticate(self, api_key: str) -> CustomerPrincipal:
        key_hash = self._hash_key(api_key)
        principal = self._keys.get(key_hash)
        if principal is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid customer API key")
        return principal

    def meter(self, principal: CustomerPrincipal, *, product: str, units: int) -> Dict[str, Any]:
        now = datetime.now(UTC)
        minute_key = f"meter:{principal.customer_id}:{product}:{now:%Y%m%d%H%M}"
        month_key = f"meter:{principal.customer_id}:{product}:{now:%Y%m}"
        if self._redis is not None:
            pipe = self._redis.pipeline()
            pipe.incr(minute_key, 1)
            pipe.expire(minute_key, 120)
            pipe.incrby(month_key, units)
            pipe.expire(month_key, 60 * 60 * 24 * 40)
            minute_count, _, month_units, _ = pipe.execute()
        else:
            with self._lock:
                self._local_counters[minute_key] = self._local_counters.get(minute_key, 0) + 1
                self._local_counters[month_key] = self._local_counters.get(month_key, 0) + units
                minute_count = self._local_counters[minute_key]
                month_units = self._local_counters[month_key]
        if int(minute_count) > principal.quotas["requests_per_minute"]:
            raise HTTPException(status_code=429, detail="customer request-rate quota exceeded")
        if int(month_units) > principal.quotas["monthly_compute_units"]:
            raise HTTPException(status_code=402, detail="customer monthly compute-unit quota exceeded")
        return {
            "customer_id": principal.customer_id,
            "product": product,
            "units": units,
            "minute_requests": int(minute_count),
            "month_units": int(month_units),
            "quota": principal.quotas,
        }

    def set_state(self, key: str, value: Dict[str, Any]) -> None:
        if self._redis is not None:
            self._redis.set(f"hyba:commercial:{key}", json.dumps(value, sort_keys=True))

    def backend(self) -> str:
        return "redis" if self._redis is not None else "in-memory"


customer_access = CustomerAccessRegistry()


def require_customer_api_key(x_api_key: str = Header(alias="X-API-Key")) -> CustomerPrincipal:
    return customer_access.authenticate(x_api_key)


admin_router = APIRouter(prefix="/api/admin/customer-api-keys", tags=["customer-access"])


@admin_router.post("", response_model=CustomerApiKeyIssueResponse, status_code=status.HTTP_201_CREATED)
async def issue_customer_api_key(
    request: CustomerApiKeyIssueRequest,
    _payload: Any = Depends(require_admin),
):
    return customer_access.issue_key(request)


@admin_router.get("/state", response_model=Dict[str, str])
async def customer_access_state(_payload: Any = Depends(require_admin)):
    return {"distributed_state_backend": customer_access.backend()}
