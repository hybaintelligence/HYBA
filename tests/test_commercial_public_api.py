"""Customer-facing QaaS/CIaaS commercial API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from hyba_genesis_api.api.admin import require_admin
from hyba_genesis_api.api.computational_intelligence_service import registry as ciaas_registry
from hyba_genesis_api.api.customer_access import CustomerApiKeyIssueRequest, customer_access
from hyba_genesis_api.api.quantum_as_a_service import registry as qaas_registry
from hyba_genesis_api.auth.jwt_handler import TokenPayload
from hyba_genesis_api.main import app


def _admin_payload() -> TokenPayload:
    return TokenPayload(sub="1", username="root-admin", roles=["admin"], exp=9999999999, iat=1)


def _issue_key(customer_id: str = "customer-acme", **quota_overrides: int) -> str:
    issued = customer_access.issue_key(
        CustomerApiKeyIssueRequest(
            customer_id=customer_id,
            tier="production",
            **quota_overrides,
        )
    )
    return issued.api_key


def test_public_qaas_customer_api_key_provisions_meters_and_isolates_tenant():
    qaas_registry._computers.clear()
    customer_access._local_counters.clear()
    try:
        api_key = _issue_key("qaas-customer")
        other_key = _issue_key("other-customer")
        client = TestClient(app)

        provision = client.post(
            "/api/v1/fault-tolerant-computers",
            headers={"X-API-Key": api_key},
            json={
                "name": "public-qpu",
                "code_distance": 5,
                "logical_qubits": 3,
                "max_circuit_depth": 2,
            },
        )
        assert provision.status_code == 201
        computer_id = provision.json()["computer_id"]
        assert provision.json()["owner"] == "qaas-customer"

        started = client.post(
            f"/api/v1/fault-tolerant-computers/{computer_id}/start",
            headers={"X-API-Key": api_key},
        )
        assert started.status_code == 200
        execute = client.post(
            f"/api/v1/fault-tolerant-computers/{computer_id}/execute",
            headers={"X-API-Key": api_key},
            json={
                "operation": "surface_code_cycle",
                "logical_qubits": [0],
                "circuit_depth": 1,
                "shots": 2,
            },
        )
        assert execute.status_code == 200
        assert execute.json()["usage_meter"]["product"] == "qaas.execute"
        assert execute.json()["usage_meter"]["units"] == 2

        hidden = client.post(
            f"/api/v1/fault-tolerant-computers/{computer_id}/start",
            headers={"X-API-Key": other_key},
        )
        assert hidden.status_code == 404
    finally:
        qaas_registry._computers.clear()
        customer_access._local_counters.clear()


def test_public_ciaas_quota_enforcement_and_admin_key_issuance():
    app.dependency_overrides[require_admin] = _admin_payload
    ciaas_registry._services.clear()
    customer_access._local_counters.clear()
    try:
        client = TestClient(app)
        issued = client.post(
            "/api/admin/customer-api-keys",
            json={
                "customer_id": "ciaas-customer",
                "tier": "developer",
                "monthly_compute_units": 4,
            },
        )
        assert issued.status_code == 201
        api_key = issued.json()["api_key"]
        assert api_key.startswith("hyba_live_")

        provision = client.post(
            "/api/v1/computational-intelligence-services",
            headers={"X-API-Key": api_key},
            json={
                "name": "public-ciaas",
                "logical_compute_units": 2,
                "allowed_workloads": ["governance_audit"],
            },
        )
        assert provision.status_code == 201
        service_id = provision.json()["service_id"]
        client.post(
            f"/api/v1/computational-intelligence-services/{service_id}/start",
            headers={"X-API-Key": api_key},
        )
        workload = client.post(
            f"/api/v1/computational-intelligence-services/{service_id}/workloads",
            headers={"X-API-Key": api_key},
            json={"workload_type": "governance_audit", "context": {"case": "quota"}},
        )
        assert workload.status_code == 200
        assert workload.json()["usage_meter"]["product"] == "ciaas.execute"

        over_quota = client.post(
            f"/api/v1/computational-intelligence-services/{service_id}/workloads",
            headers={"X-API-Key": api_key},
            json={"workload_type": "governance_audit", "context": {"payload": "x" * 5000}},
        )
        assert over_quota.status_code == 402
    finally:
        app.dependency_overrides.clear()
        ciaas_registry._services.clear()
        customer_access._local_counters.clear()
