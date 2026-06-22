"""Billing integration helpers for metered HYBA product surfaces."""

from __future__ import annotations

import inspect
import uuid
from datetime import UTC, datetime
from typing import Any, Callable, Dict, TypeVar

from fastapi import HTTPException

from hyba_genesis_api.api.billing_rollback import get_billing_rollback_manager
from hyba_genesis_api.api.customer_access import CustomerPrincipal, customer_access
from hyba_genesis_api.api.quota_manager import get_quota_manager

T = TypeVar("T")

_AUDIT_LOG: list[Dict[str, Any]] = []
_INVOICES: list[Dict[str, Any]] = []


def get_billing_audit_log() -> list[Dict[str, Any]]:
    return list(_AUDIT_LOG)


def get_generated_invoices() -> list[Dict[str, Any]]:
    return list(_INVOICES)


def reset_billing_evidence() -> None:
    _AUDIT_LOG.clear()
    _INVOICES.clear()


def _invoice(customer: CustomerPrincipal, product: str, units: int, usage: Dict[str, Any]) -> Dict[str, Any]:
    amount = float(usage.get("estimated_charge_usd", 0.0) or 0.0)
    invoice = {
        "invoice_id": f"inv_{uuid.uuid4().hex[:16]}",
        "customer_id": customer.customer_id,
        "product": product,
        "units": units,
        "amount_usd": round(amount, 6),
        "status": "draft",
        "created_at": datetime.now(UTC).isoformat(),
    }
    _INVOICES.append(invoice)
    return invoice


def _audit(customer: CustomerPrincipal, endpoint: str, request_id: str, units: int, outcome: str) -> Dict[str, Any]:
    entry = {
        "customer_id": customer.customer_id,
        "endpoint": endpoint,
        "timestamp_iso8601": datetime.now(UTC).isoformat(),
        "request_id": request_id,
        "quota_deducted": units if outcome == "success" else 0,
        "outcome": outcome,
    }
    _AUDIT_LOG.append(entry)
    return entry


def execute_with_billing(
    *,
    principal: CustomerPrincipal,
    product: str,
    endpoint: str,
    units: int,
    execute: Callable[[], T],
    execution_id: str | None = None,
) -> tuple[T, Dict[str, Any], Dict[str, Any]]:
    """Meter a product call and roll it back if execution fails."""
    request_id = execution_id or f"exec_{uuid.uuid4().hex}"
    quota_manager = get_quota_manager()
    if quota_manager.get_status(principal.customer_id)["total_quota"] == 0:
        quota_manager.provision_quota(principal.customer_id, principal.quota_compute_units_per_month)
    quota_manager.consume_quota(principal.customer_id, units, request_id)
    usage = customer_access.meter(principal, product=product, units=units)
    try:
        if len(inspect.signature(execute).parameters) == 1:
            result = execute(usage)  # type: ignore[misc]
        else:
            result = execute()
    except HTTPException as exc:
        customer_access.refund_metered_usage(principal, product=product, units=units)
        quota_manager.refund_quota(principal.customer_id, units, request_id, str(exc.detail))
        rollback = get_billing_rollback_manager().refund_on_failure(
            request_id, principal.customer_id, units, str(exc.detail)
        )
        _audit(principal, endpoint, request_id, units, "failure")
        exc.detail = {"message": exc.detail, "billing_rollback": rollback}
        raise
    except Exception as exc:
        customer_access.refund_metered_usage(principal, product=product, units=units)
        quota_manager.refund_quota(principal.customer_id, units, request_id, exc.__class__.__name__)
        get_billing_rollback_manager().refund_on_failure(
            request_id, principal.customer_id, units, exc.__class__.__name__
        )
        _audit(principal, endpoint, request_id, units, "failure")
        raise
    invoice = _invoice(principal, product, units, usage)
    _audit(principal, endpoint, request_id, units, "success")
    return result, usage, invoice
