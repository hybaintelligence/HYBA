from fastapi import HTTPException

from hyba_genesis_api.api.billing_integration import (
    execute_with_billing,
    get_billing_audit_log,
    get_generated_invoices,
    reset_billing_evidence,
)
from hyba_genesis_api.api.customer_access import (
    CustomerApiKeyIssueRequest,
    customer_access,
)
from hyba_genesis_api.api.quota_manager import get_quota_manager


def _customer(customer_id="tenant-billing"):
    response = customer_access.issue_key(
        CustomerApiKeyIssueRequest(
            customer_id=customer_id,
            customer_name="Billing Test",
            tier="developer",
            monthly_compute_units=100,
            monthly_requests=100,
        )
    )
    return customer_access.get_customer_by_api_key(response.api_key)


def test_billing_wrapper_deducts_refunds_audits_and_invoices():
    reset_billing_evidence()
    principal = _customer()
    quota = get_quota_manager()
    quota.provision_quota(
        principal.customer_id, principal.quota_compute_units_per_month
    )

    result, usage, invoice = execute_with_billing(
        principal=principal,
        product="qaas.execute",
        endpoint="/api/v1/fault-tolerant-computers/test/execute",
        units=10,
        execution_id="success-exec",
        execute=lambda: {"ok": True},
    )

    assert result == {"ok": True}
    assert usage["units"] == 10
    assert quota.get_status(principal.customer_id)["consumed"] == 10
    assert invoice in get_generated_invoices()
    assert invoice["customer_id"] == principal.customer_id

    try:
        execute_with_billing(
            principal=principal,
            product="qaas.execute",
            endpoint="/api/v1/fault-tolerant-computers/test/execute",
            units=5,
            execution_id="failed-exec",
            execute=lambda: (_ for _ in ()).throw(
                HTTPException(status_code=503, detail="backend failed")
            ),
        )
    except HTTPException:
        pass

    assert quota.get_status(principal.customer_id)["consumed"] == 10
    assert any(entry["outcome"] == "failure" for entry in get_billing_audit_log())
    assert any(entry["outcome"] == "success" for entry in get_billing_audit_log())


def test_audit_log_schema_contains_required_fields():
    reset_billing_evidence()
    principal = _customer("tenant-audit")
    execute_with_billing(
        principal=principal,
        product="qaas.execute",
        endpoint="/api/v1/fault-tolerant-computers/test/execute",
        units=1,
        execution_id="audit-schema-exec",
        execute=lambda: {"ok": True},
    )
    entry = get_billing_audit_log()[-1]
    assert set(entry) == {
        "customer_id",
        "endpoint",
        "timestamp_iso8601",
        "request_id",
        "quota_deducted",
        "outcome",
    }
    assert entry["outcome"] in {"success", "failure"}
