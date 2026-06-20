from __future__ import annotations

from fastapi import HTTPException

from hyba_genesis_api.api.customer_access import CustomerApiKeyIssueRequest, customer_access
from hyba_genesis_api.core.telemetry import get_prometheus_metrics


def test_per_tenant_pricing_quota_and_prometheus_metrics():
    issued = customer_access.issue_key(
        CustomerApiKeyIssueRequest(
            customer_id="billing-observability-tenant",
            tier="enterprise",
            monthly_compute_units=3,
            monthly_requests=2,
            metadata={"pricing_usd_per_unit": {"qaas.execute": 0.25}},
        )
    )
    customer = customer_access.get_customer_by_api_key(issued.api_key)

    meter = customer_access.meter(customer, "qaas.execute", 2)

    assert meter["unit_price_usd"] == 0.25
    assert meter["estimated_charge_usd"] == 0.5
    usage = customer_access.get_usage_metrics(customer)
    assert usage.compute_units_remaining == 1
    assert usage.requests_remaining == 1
    assert usage.estimated_charges_usd == 0.5

    try:
        customer_access.meter(customer, "qaas.execute", 2)
    except HTTPException as exc:
        assert exc.status_code == 402
    else:  # pragma: no cover
        raise AssertionError("quota enforcement should fail closed")

    prometheus = get_prometheus_metrics().decode()
    assert "hyba_billing_usage_units_total" in prometheus
    assert "hyba_billing_quota_rejections_total" in prometheus
    assert "hyba_billing_quota_remaining" in prometheus
