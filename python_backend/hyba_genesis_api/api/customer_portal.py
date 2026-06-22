"""Customer self-service portal API surface.

The portal is deliberately evidence-first: runtime counters, invoices, and
workload history are read from an explicit portal store instead of fabricated
telemetry. Local deployments can enable opt-in demo fixtures with
``HYBA_PORTAL_DEMO_FIXTURES=true``; production environments should point
``HYBA_CUSTOMER_PORTAL_STORE`` at a durable JSON volume or replace this adapter
with a database-backed implementation.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import threading
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator

router = APIRouter(prefix="/api/customer", tags=["customer-portal"])

InstanceStatus = Literal["provisioned", "running", "stopped", "degraded"]
InvoiceStatus = Literal["draft", "open", "paid", "void", "uncollectible"]
WorkloadStatus = Literal["success", "failed", "cancelled", "running"]


class CreateApiKeyRequest(BaseModel):
    """Request for a customer-managed API key."""

    label: str = Field(default="Portal generated key", min_length=1, max_length=80)
    rotation_days: int = Field(default=90, ge=1, le=365)
    plan_monthly_compute_units: int = Field(default=1000, ge=1, le=10000000)
    plan_monthly_requests: int = Field(default=10000, ge=1, le=10000000)


class PaymentMethodRequest(BaseModel):
    """Payment-method token details from a PCI-compliant provider."""

    provider: str = Field(default="stripe", min_length=2, max_length=32)
    token: str = Field(min_length=8, max_length=256)
    last4: str = Field(min_length=4, max_length=4)
    card_type: str = Field(default="card", min_length=2, max_length=32)

    @field_validator("last4")
    @classmethod
    def last4_digits_only(cls, value: str) -> str:
        if not value.isdigit():
            raise ValueError("last4 must contain only digits")
        return value


class PortalStore:
    """Small durable portal store for launch readiness and local operation."""

    def __init__(self, path: str | None = None) -> None:
        self.path = Path(path or os.getenv("HYBA_CUSTOMER_PORTAL_STORE", "data/customer_portal.json"))
        self._lock = threading.RLock()
        self._secret = os.getenv("HYBA_API_KEY_SECRET") or "development-customer-portal-secret"
        if not self.path.exists():
            self._write(self._initial_state())

    def _initial_state(self) -> dict[str, Any]:
        if os.getenv("HYBA_PORTAL_DEMO_FIXTURES", "false").lower() == "true":
            return {
                "tenants": {
                    "demo-enterprise": {
                        "instances": [
                            {"id": "demo-qaas-prod", "status": "running", "region": "us-east-1"},
                            {"id": "demo-qaas-dr", "status": "provisioned", "region": "us-west-2"},
                        ],
                        "quota": {"compute_units": 100000, "requests": 10000},
                        "api_keys": [],
                        "workloads": [],
                        "invoices": [],
                        "payment_methods": [],
                        "settings": {
                            "billing_contact": "finance@example.com",
                            "notification_preferences": {"quota_alert_percent": 80},
                        },
                    }
                }
            }
        return {"tenants": {}}

    def _read(self) -> dict[str, Any]:
        with self._lock:
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except FileNotFoundError:
                state = self._initial_state()
                self._write(state)
                return state
            except json.JSONDecodeError as exc:
                raise HTTPException(status_code=500, detail="Customer portal store is corrupt") from exc

    def _write(self, state: dict[str, Any]) -> None:
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
            tmp.replace(self.path)

    def tenant(self, tenant_id: str) -> dict[str, Any]:
        state = self._read()
        tenants = state.setdefault("tenants", {})
        return tenants.setdefault(
            tenant_id,
            {
                "instances": [],
                "quota": {"compute_units": 0, "requests": 0},
                "api_keys": [],
                "workloads": [],
                "invoices": [],
                "payment_methods": [],
                "settings": {"notification_preferences": {"quota_alert_percent": 80}},
            },
        )

    def update_tenant(self, tenant_id: str, tenant: dict[str, Any]) -> None:
        state = self._read()
        state.setdefault("tenants", {})[tenant_id] = tenant
        self._write(state)

    def hash_api_key(self, raw_api_key: str) -> str:
        return hmac.new(self._secret.encode(), raw_api_key.encode(), hashlib.sha256).hexdigest()


store = PortalStore()


def _billing_month() -> tuple[datetime, datetime, str]:
    now = datetime.now(UTC)
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return start, now, start.strftime("%Y-%m")


def _parse_date(value: str | None, field_name: str) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid {field_name}; expected ISO-8601") from exc


def _month_workloads(tenant: dict[str, Any], month_start: datetime, month_end: datetime) -> list[dict[str, Any]]:
    workloads = []
    for workload in tenant.get("workloads", []):
        executed_at = _parse_date(workload.get("timestamp"), "workload.timestamp")
        if executed_at and month_start <= executed_at <= month_end:
            workloads.append(workload)
    return workloads


@router.get("/{tenant_id}/dashboard")
async def customer_dashboard(tenant_id: str) -> dict[str, object]:
    """Return dashboard status, usage, quota, keys, billing, and data provenance."""
    month_start, now, month_label = _billing_month()
    tenant = store.tenant(tenant_id)
    workloads = _month_workloads(tenant, month_start, now)
    monthly_units = int(sum(int(item.get("compute_units", 0)) for item in workloads))
    monthly_cost = round(sum(float(item.get("cost_usd", 0.0)) for item in workloads), 2)
    quota = tenant.get("quota", {})
    compute_quota = int(quota.get("compute_units", 0))
    active_keys = [key for key in tenant.get("api_keys", []) if key.get("status") == "active"]
    invoices = tenant.get("invoices", [])
    return {
        "tenant_id": tenant_id,
        "instances": tenant.get("instances", []),
        "monthly_usage": {
            "month": month_label,
            "start_date": month_start.isoformat(),
            "end_date": now.isoformat(),
            "compute_units": monthly_units,
            "estimated_cost_usd": monthly_cost,
        },
        "quota_remaining": {
            "compute_units": max(compute_quota - monthly_units, 0),
            "monthly_quota": compute_quota,
        },
        "api_keys": active_keys,
        "billing_summary": {
            "current_month_usd": monthly_cost,
            "invoice_count": len(invoices),
            "next_billing_date": (month_start + timedelta(days=32)).replace(day=1).date().isoformat(),
        },
        "settings": tenant.get("settings", {}),
        "uptime": tenant.get("uptime", {"last_30_days_percent": None, "source": "not_configured"}),
        "data_provenance": {
            "source": "HYBA_CUSTOMER_PORTAL_STORE",
            "demo_fixtures_enabled": os.getenv("HYBA_PORTAL_DEMO_FIXTURES", "false").lower() == "true",
            "generated_at": now.isoformat(),
        },
    }


@router.get("/{tenant_id}/workloads")
async def customer_workloads(
    tenant_id: str,
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
) -> dict[str, object]:
    """Return tenant workload execution history and aggregate trends."""
    start = _parse_date(start_date, "start_date") or datetime.min.replace(tzinfo=UTC)
    end = _parse_date(end_date, "end_date") or datetime.max.replace(tzinfo=UTC)
    tenant = store.tenant(tenant_id)
    executions = []
    for workload in tenant.get("workloads", []):
        executed_at = _parse_date(workload.get("timestamp"), "workload.timestamp")
        if executed_at and start <= executed_at <= end:
            executions.append(workload)
    successful = sum(1 for item in executions if item.get("status") == "success")
    total = len(executions)
    return {
        "tenant_id": tenant_id,
        "start_date": start_date,
        "end_date": end_date,
        "executions": executions,
        "total_cost": round(sum(float(item.get("cost_usd", 0.0)) for item in executions), 2),
        "success_rate": round(successful / total, 4) if total else None,
        "cost_trends": {"daily": None, "weekly": None, "monthly": None, "source": "insufficient_history"},
    }


@router.post("/{tenant_id}/api-keys", status_code=status.HTTP_201_CREATED)
async def create_api_key(tenant_id: str, request: CreateApiKeyRequest) -> dict[str, str]:
    """Create a portal-managed API key and persist only its HMAC digest."""
    tenant = store.tenant(tenant_id)
    raw = f"hyba_live_{secrets.token_urlsafe(32)}"
    digest = store.hash_api_key(raw)
    now = datetime.now(UTC)
    record = {
        "key_id": f"portal-{digest[:16]}",
        "key_hash": digest,
        "label": request.label,
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(days=request.rotation_days)).isoformat(),
        "status": "active",
    }
    tenant.setdefault("api_keys", []).append(record)
    quota = tenant.setdefault("quota", {})
    quota["compute_units"] = max(int(quota.get("compute_units", 0)), request.plan_monthly_compute_units)
    quota["requests"] = max(int(quota.get("requests", 0)), request.plan_monthly_requests)
    store.update_tenant(tenant_id, tenant)
    return {**record, "api_key": raw}


@router.delete("/{tenant_id}/api-keys/{key_id}")
async def revoke_api_key(tenant_id: str, key_id: str) -> dict[str, str]:
    """Revoke a customer portal API key."""
    tenant = store.tenant(tenant_id)
    for key in tenant.setdefault("api_keys", []):
        if key.get("key_id") == key_id:
            key["status"] = "revoked"
            key["revoked_at"] = datetime.now(UTC).isoformat()
            store.update_tenant(tenant_id, tenant)
            return {"key_id": key_id, "revoked_at": key["revoked_at"]}
    raise HTTPException(status_code=404, detail="API key not found")


@router.get("/{tenant_id}/billing/invoices")
async def billing_invoices(tenant_id: str) -> dict[str, object]:
    """Return invoice history for the tenant."""
    tenant = store.tenant(tenant_id)
    invoices = tenant.get("invoices", [])
    today = date.today()
    next_month = (today.replace(day=1) + timedelta(days=32)).replace(day=1)
    return {
        "tenant_id": tenant_id,
        "invoices": invoices,
        "total_ytd": round(sum(float(invoice.get("amount_usd", 0.0)) for invoice in invoices), 2),
        "next_billing_date": next_month.isoformat(),
    }


@router.post("/{tenant_id}/payment-methods", status_code=status.HTTP_201_CREATED)
async def add_payment_method(tenant_id: str, request: PaymentMethodRequest) -> dict[str, str]:
    """Register a tokenized payment method without storing card PAN data."""
    tenant = store.tenant(tenant_id)
    token_digest = hashlib.sha256(request.token.encode()).hexdigest()
    method = {
        "method_id": f"pm-{token_digest[:16]}",
        "provider": request.provider,
        "last4": request.last4,
        "card_type": request.card_type,
        "created_at": datetime.now(UTC).isoformat(),
    }
    tenant.setdefault("payment_methods", []).append(method)
    store.update_tenant(tenant_id, tenant)
    return method
