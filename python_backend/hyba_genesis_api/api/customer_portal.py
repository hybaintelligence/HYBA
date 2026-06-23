"""Customer Portal API.

Self-service customer management, usage tracking, API key provisioning, and
billing visibility. The portal is tenant-bound and fail-closed in production when
customer-portal auth is not configured.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Header, HTTPException, Request, status
from pydantic import BaseModel, Field

from ..database import get_db_connection, initialize_database

router = APIRouter(prefix="/api/customer", tags=["customer_portal"])


class CreateTenantAPIKeyRequest(BaseModel):
    label: str = Field(..., min_length=1, max_length=100)
    rotation_days: int = Field(default=90, ge=1, le=730)


class UsageResponse(BaseModel):
    compute_units_used: int
    compute_units_quota: int
    current_period_cost: float
    currency: str
    period_start: str
    period_end: str
    breakdown: Dict[str, int]


class UsageHistoryResponse(BaseModel):
    history: List[Dict[str, Any]]
    total_records: int


class QuotaAlertConfig(BaseModel):
    enabled: bool
    threshold_percent: int = Field(ge=50, le=100)
    notification_email: Optional[str]


class PaymentMethodRequest(BaseModel):
    provider: str = Field(..., min_length=2, max_length=50)
    token: str = Field(..., min_length=6)
    last4: str = Field(..., pattern=r"^\d{4}$")
    card_type: Optional[str] = Field(default=None, max_length=32)


def _is_production() -> bool:
    return os.getenv("NODE_ENV", os.getenv("HYBA_ENV", "development")).lower() == "production"


def _auth_disabled() -> bool:
    return os.getenv("HYBA_CUSTOMER_PORTAL_AUTH_DISABLED", "false").lower() == "true"


def _portal_token() -> str:
    return os.getenv("HYBA_CUSTOMER_PORTAL_TOKEN", "").strip()


def _store_path() -> Optional[Path]:
    raw = os.getenv("HYBA_CUSTOMER_PORTAL_STORE", "").strip()
    return Path(raw) if raw else None


def _empty_store() -> Dict[str, Any]:
    return {"tenants": {}}


def _load_store() -> Dict[str, Any]:
    path = _store_path()
    if not path:
        return _empty_store()
    if not path.exists():
        return _empty_store()
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return _empty_store()


def _save_store(store: Dict[str, Any]) -> None:
    path = _store_path()
    if not path:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(store, indent=2, sort_keys=True), encoding="utf-8")


def _tenant_record(store: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
    tenants = store.setdefault("tenants", {})
    tenant = tenants.setdefault(
        tenant_id,
        {
            "instances": [],
            "api_keys": [],
            "workloads": [],
            "payment_methods": [],
            "subscription": {
                "tier": "developer",
                "compute_units_quota": 1000,
                "cost_per_unit": 0.01,
                "currency": "USD",
            },
            "uptime": {"last_30_days_percent": None},
        },
    )
    tenant.setdefault("api_keys", [])
    tenant.setdefault("workloads", [])
    tenant.setdefault("instances", [])
    tenant.setdefault("payment_methods", [])
    return tenant


def _require_tenant_access(
    tenant_id: str,
    tenant_header: Optional[str],
    token_header: Optional[str],
) -> None:
    if tenant_header and tenant_header != tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant boundary violation")

    configured = _portal_token()
    if configured:
        if not token_header or not hmac.compare_digest(token_header, configured):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Customer portal token required")
        return

    if _is_production() and not _auth_disabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Customer portal token is not configured",
        )


def _tenant_from_request(request: Request) -> str:
    tenant_id = request.headers.get("X-HYBA-Tenant-ID") or request.headers.get("X-HYBA-Customer-ID") or "default"
    _require_tenant_access(
        tenant_id,
        request.headers.get("X-HYBA-Tenant-ID"),
        request.headers.get("X-HYBA-Customer-Token"),
    )
    return tenant_id


def _secret() -> bytes:
    secret = os.getenv("HYBA_API_KEY_SECRET", "local-customer-portal-secret")
    return secret.encode("utf-8")


def _hash_secret(value: str) -> str:
    return hmac.new(_secret(), value.encode("utf-8"), hashlib.sha256).hexdigest()


def _generate_api_key() -> tuple[str, str]:
    api_key = f"hyba_live_{secrets.token_urlsafe(32)}"
    return api_key, _hash_secret(api_key)


def _current_period(now: Optional[datetime] = None) -> tuple[datetime, datetime]:
    now = now or datetime.utcnow()
    period_start = datetime(now.year, now.month, 1)
    if now.month == 12:
        period_end = datetime(now.year + 1, 1, 1) - timedelta(seconds=1)
    else:
        period_end = datetime(now.year, now.month + 1, 1) - timedelta(seconds=1)
    return period_start, period_end


def _safe_db() -> sqlite3.Connection:
    initialize_database()
    return get_db_connection()


def calculate_usage(customer_id: str, period_start: datetime, period_end: datetime) -> Dict[str, int]:
    """Calculate usage from real usage_logs rows for the requested period."""
    breakdown: Dict[str, int] = {}
    try:
        conn = _safe_db()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT service_type, COALESCE(SUM(compute_units), 0) AS units
            FROM usage_logs
            WHERE customer_id = ? AND timestamp >= ? AND timestamp <= ?
            GROUP BY service_type
            """,
            (customer_id, period_start.isoformat(), period_end.isoformat()),
        )
        for row in cursor.fetchall():
            breakdown[str(row[0])] = int(row[1] or 0)
        conn.close()
    except sqlite3.Error:
        return {}
    return breakdown


def get_customer_tier(customer_id: str) -> Dict[str, Any]:
    """Read the active customer subscription, defaulting to developer tier."""
    default = {
        "tier": "developer",
        "compute_units_quota": 1000,
        "cost_per_unit": 0.01,
        "currency": "USD",
    }
    try:
        conn = _safe_db()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT tier, compute_units_quota, cost_per_unit, currency
            FROM customer_subscriptions
            WHERE customer_id = ? AND status = 'active'
            ORDER BY subscription_start DESC
            LIMIT 1
            """,
            (customer_id,),
        )
        row = cursor.fetchone()
        conn.close()
        if not row:
            return default
        return {
            "tier": row[0],
            "compute_units_quota": int(row[1]),
            "cost_per_unit": float(row[2]),
            "currency": row[3],
        }
    except sqlite3.Error:
        return default


def _invoice_count(customer_id: str) -> int:
    try:
        conn = _safe_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM invoices WHERE customer_id = ?", (customer_id,))
        count = int(cursor.fetchone()[0] or 0)
        conn.close()
        return count
    except sqlite3.Error:
        return 0


def _usage_response(customer_id: str, period_start: datetime, period_end: datetime) -> UsageResponse:
    tier_info = get_customer_tier(customer_id)
    breakdown = calculate_usage(customer_id, period_start, period_end)
    total_units = sum(breakdown.values())
    cost = round(total_units * float(tier_info["cost_per_unit"]), 4)
    return UsageResponse(
        compute_units_used=total_units,
        compute_units_quota=int(tier_info["compute_units_quota"]),
        current_period_cost=cost,
        currency=str(tier_info["currency"]),
        period_start=period_start.isoformat(),
        period_end=period_end.isoformat(),
        breakdown=breakdown,
    )


def _public_api_keys(tenant: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {
            "key_id": key["key_id"],
            "label": key.get("label", key.get("name", "API key")),
            "status": key.get("status", "active"),
            "created_at": key.get("created_at"),
            "last_used_at": key.get("last_used_at"),
            "rotation_days": key.get("rotation_days"),
        }
        for key in tenant.get("api_keys", [])
        if key.get("status") != "deleted"
    ]


@router.get("/{tenant_id}/dashboard")
async def tenant_dashboard(
    tenant_id: str,
    x_hyba_tenant_id: Optional[str] = Header(default=None),
    x_hyba_customer_token: Optional[str] = Header(default=None),
):
    _require_tenant_access(tenant_id, x_hyba_tenant_id, x_hyba_customer_token)
    store = _load_store()
    tenant = _tenant_record(store, tenant_id)
    period_start, period_end = _current_period()
    usage = _usage_response(tenant_id, period_start, period_end)
    quota_remaining = max(usage.compute_units_quota - usage.compute_units_used, 0)

    return {
        "tenant_id": tenant_id,
        "instances": tenant.get("instances", []),
        "monthly_usage": {
            "compute_units": usage.compute_units_used,
            "estimated_cost_usd": usage.current_period_cost,
        },
        "quota_remaining": {
            "compute_units": quota_remaining,
            "monthly_quota": usage.compute_units_quota,
        },
        "api_keys": _public_api_keys(tenant),
        "billing_summary": {
            "current_month_usd": usage.current_period_cost,
            "invoice_count": _invoice_count(tenant_id),
            "next_billing_date": period_end.isoformat(),
        },
        "uptime": tenant.get("uptime", {"last_30_days_percent": None}),
        "data_provenance": {
            "usage_source": "usage_logs",
            "subscription_source": "customer_subscriptions",
            "demo_fixtures_enabled": os.getenv("HYBA_PORTAL_DEMO_FIXTURES", "false").lower() == "true",
        },
    }


@router.get("/{tenant_id}/workloads")
async def tenant_workloads(
    tenant_id: str,
    x_hyba_tenant_id: Optional[str] = Header(default=None),
    x_hyba_customer_token: Optional[str] = Header(default=None),
):
    _require_tenant_access(tenant_id, x_hyba_tenant_id, x_hyba_customer_token)
    store = _load_store()
    tenant = _tenant_record(store, tenant_id)
    workloads = list(tenant.get("workloads", []))

    if not workloads:
        try:
            conn = _safe_db()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT execution_id, service_type, compute_units, timestamp
                FROM usage_logs
                WHERE customer_id = ?
                ORDER BY timestamp DESC
                LIMIT 50
                """,
                (tenant_id,),
            )
            tier_info = get_customer_tier(tenant_id)
            workloads = [
                {
                    "execution_id": row[0] or f"usage-{idx}",
                    "workload_type": row[1],
                    "status": "success",
                    "duration_ms": 0,
                    "cost_usd": round(int(row[2] or 0) * float(tier_info["cost_per_unit"]), 4),
                    "timestamp": row[3],
                }
                for idx, row in enumerate(cursor.fetchall())
            ]
            conn.close()
        except sqlite3.Error:
            workloads = []

    total_cost = round(sum(float(item.get("cost_usd", 0)) for item in workloads), 4)
    success_rate = None if not workloads else sum(1 for item in workloads if item.get("status") == "success") / len(workloads)
    return {"executions": workloads, "total_cost": total_cost, "success_rate": success_rate}


@router.post("/{tenant_id}/api-keys", status_code=status.HTTP_201_CREATED)
async def create_tenant_api_key(
    tenant_id: str,
    request: CreateTenantAPIKeyRequest,
    x_hyba_tenant_id: Optional[str] = Header(default=None),
    x_hyba_customer_token: Optional[str] = Header(default=None),
):
    _require_tenant_access(tenant_id, x_hyba_tenant_id, x_hyba_customer_token)
    store = _load_store()
    tenant = _tenant_record(store, tenant_id)
    api_key, key_hash = _generate_api_key()
    key_id = f"key_{secrets.token_hex(8)}"
    now = datetime.utcnow().isoformat()
    tenant["api_keys"].append(
        {
            "key_id": key_id,
            "key_hash": key_hash,
            "label": request.label,
            "rotation_days": request.rotation_days,
            "created_at": now,
            "status": "active",
        }
    )
    _save_store(store)
    return {
        "key_id": key_id,
        "api_key": api_key,
        "label": request.label,
        "created_at": now,
        "status": "active",
    }


@router.delete("/{tenant_id}/api-keys/{key_id}")
async def revoke_tenant_api_key(
    tenant_id: str,
    key_id: str,
    x_hyba_tenant_id: Optional[str] = Header(default=None),
    x_hyba_customer_token: Optional[str] = Header(default=None),
):
    _require_tenant_access(tenant_id, x_hyba_tenant_id, x_hyba_customer_token)
    store = _load_store()
    tenant = _tenant_record(store, tenant_id)
    for key in tenant.get("api_keys", []):
        if key.get("key_id") == key_id and key.get("status") != "deleted":
            key["status"] = "deleted"
            key["deleted_at"] = datetime.utcnow().isoformat()
            _save_store(store)
            return {"status": "revoked", "key_id": key_id}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")


@router.post("/{tenant_id}/payment-methods", status_code=status.HTTP_201_CREATED)
async def create_payment_method(
    tenant_id: str,
    request: PaymentMethodRequest,
    x_hyba_tenant_id: Optional[str] = Header(default=None),
    x_hyba_customer_token: Optional[str] = Header(default=None),
):
    _require_tenant_access(tenant_id, x_hyba_tenant_id, x_hyba_customer_token)
    if not re.fullmatch(r"\d{4}", request.last4):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="last4 must be four digits")
    store = _load_store()
    tenant = _tenant_record(store, tenant_id)
    payment_method_id = f"pm_{secrets.token_hex(8)}"
    created_at = datetime.utcnow().isoformat()
    tenant["payment_methods"].append(
        {
            "payment_method_id": payment_method_id,
            "provider": request.provider,
            "token_hash": _hash_secret(request.token),
            "last4": request.last4,
            "card_type": request.card_type,
            "created_at": created_at,
            "status": "active",
        }
    )
    _save_store(store)
    return {
        "payment_method_id": payment_method_id,
        "provider": request.provider,
        "last4": request.last4,
        "card_type": request.card_type,
        "created_at": created_at,
        "status": "active",
    }


@router.get("/usage", response_model=UsageResponse)
async def get_usage(request: Request):
    tenant_id = _tenant_from_request(request)
    period_start, period_end = _current_period()
    return _usage_response(tenant_id, period_start, period_end)


@router.get("/usage/history", response_model=UsageHistoryResponse)
async def get_usage_history(request: Request, months: int = 6):
    tenant_id = _tenant_from_request(request)
    history = []
    now = datetime.utcnow()
    for i in range(max(1, min(months, 24))):
        year = now.year
        month = now.month - i
        while month <= 0:
            month += 12
            year -= 1
        period_start = datetime(year, month, 1)
        if month == 12:
            period_end = datetime(year + 1, 1, 1) - timedelta(seconds=1)
        else:
            period_end = datetime(year, month + 1, 1) - timedelta(seconds=1)
        usage = _usage_response(tenant_id, period_start, period_end)
        history.append(
            {
                "period_start": usage.period_start,
                "period_end": usage.period_end,
                "compute_units_used": usage.compute_units_used,
                "cost": usage.current_period_cost,
                "currency": usage.currency,
                "breakdown": usage.breakdown,
            }
        )
    return UsageHistoryResponse(history=history, total_records=len(history))


@router.get("/quota-alerts")
async def get_quota_alert_config(request: Request):
    customer_id = _tenant_from_request(request)
    conn = _safe_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT enabled, threshold_percent, notification_email FROM quota_alerts WHERE customer_id = ?",
        (customer_id,),
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return {"enabled": True, "threshold_percent": 90, "notification_email": None}
    return {"enabled": bool(row[0]), "threshold_percent": row[1], "notification_email": row[2]}


@router.put("/quota-alerts")
async def update_quota_alert_config(config: QuotaAlertConfig, request: Request):
    customer_id = _tenant_from_request(request)
    conn = _safe_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR REPLACE INTO quota_alerts (
            customer_id, enabled, threshold_percent, notification_email, updated_at
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (customer_id, config.enabled, config.threshold_percent, config.notification_email, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()
    return {"status": "updated", "config": config.dict()}


@router.get("/billing/invoices")
async def get_invoices(request: Request, limit: int = 12):
    customer_id = _tenant_from_request(request)
    conn = _safe_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT invoice_id, period, amount, currency, status, issued_at, paid_at
        FROM invoices
        WHERE customer_id = ?
        ORDER BY issued_at DESC
        LIMIT ?
        """,
        (customer_id, max(1, min(limit, 100))),
    )
    invoices = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"invoices": invoices, "total": len(invoices)}


@router.get("/billing/current")
async def get_current_bill(request: Request):
    customer_id = _tenant_from_request(request)
    now = datetime.utcnow()
    period_start, _ = _current_period(now)
    usage = _usage_response(customer_id, period_start, now)
    estimated = usage.current_period_cost if now.day <= 0 else round(usage.current_period_cost * 30 / now.day, 4)
    return {
        "period": f"{now.year}-{now.month:02d}",
        "compute_units_used": usage.compute_units_used,
        "current_amount": usage.current_period_cost,
        "currency": usage.currency,
        "breakdown": usage.breakdown,
        "estimated_month_end": estimated,
    }
