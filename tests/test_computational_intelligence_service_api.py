"""API tests for admin-provisioned Computational Intelligence as a Service."""

from __future__ import annotations

from fastapi.testclient import TestClient

from hyba_genesis_api.api.admin import require_admin
from hyba_genesis_api.api.computational_intelligence_service import registry
from hyba_genesis_api.auth.jwt_handler import TokenPayload
from hyba_genesis_api.main import app


def _admin_payload() -> TokenPayload:
    return TokenPayload(sub="1", username="root-admin", roles=["admin"], exp=9999999999, iat=1)


def test_admin_can_provision_start_execute_and_stop_ciaas_without_mining_job_shape():
    app.dependency_overrides[require_admin] = _admin_payload
    registry._services.clear()
    try:
        client = TestClient(app)
        provision = client.post(
            "/api/admin/computational-intelligence-services",
            json={
                "name": "commercial-ciaas-01",
                "service_tier": "production",
                "tenancy": "dedicated-control-plane",
                "code_distance": 5,
                "logical_compute_units": 4,
                "physical_error_rate": 0.0001,
                "admin_privileged": True,
                "allowed_workloads": ["orchestrate", "counterfactual", "governance_audit"],
            },
        )
        assert provision.status_code == 201
        body = provision.json()
        assert body["state"] == "provisioned"
        assert body["service_tier"] == "production"
        assert body["tenancy"] == "dedicated-control-plane"
        assert body["fault_tolerance"]["fault_tolerant"] is True
        assert len(body["evidence_seal"]) == 64

        service_id = body["service_id"]
        started = client.post(f"/api/admin/computational-intelligence-services/{service_id}/start")
        assert started.status_code == 200
        assert started.json()["state"] == "running"

        workload = client.post(
            f"/api/admin/computational-intelligence-services/{service_id}/workloads",
            json={
                "workload_type": "orchestrate",
                "context": {
                    "objective": "route high-stakes operational decision",
                    "constraints": ["fault-tolerant", "auditable", "commercial-slo"],
                },
                "idempotency_key": "same-workload-1",
            },
        )
        assert workload.status_code == 200
        result = workload.json()
        assert result["workload_type"] == "orchestrate"
        assert result["fault_tolerance"]["logical_error_rate"] < 0.0001
        assert result["commercial_policy"]["workloads_executed"] == 1
        assert "job_id" not in result["result"]

        replay = client.post(
            f"/api/admin/computational-intelligence-services/{service_id}/workloads",
            json={
                "workload_type": "orchestrate",
                "context": {"objective": "changed but idempotent"},
                "idempotency_key": "same-workload-1",
            },
        )
        assert replay.status_code == 200
        assert replay.json()["executed_at"] == result["executed_at"]

        stopped = client.post(f"/api/admin/computational-intelligence-services/{service_id}/stop")
        assert stopped.status_code == 200
        assert stopped.json()["state"] == "stopped"
    finally:
        app.dependency_overrides.clear()
        registry._services.clear()


def test_ciaas_rejects_invalid_surface_code_distance_and_disallowed_workload():
    app.dependency_overrides[require_admin] = _admin_payload
    registry._services.clear()
    try:
        client = TestClient(app)
        bad = client.post(
            "/api/admin/computational-intelligence-services",
            json={"name": "bad-ciaas", "code_distance": 4},
        )
        assert bad.status_code == 422
        assert "code_distance must be odd" in bad.text

        provision = client.post(
            "/api/admin/computational-intelligence-services",
            json={"name": "audit-only", "allowed_workloads": ["governance_audit"]},
        )
        service_id = provision.json()["service_id"]
        client.post(f"/api/admin/computational-intelligence-services/{service_id}/start")
        denied = client.post(
            f"/api/admin/computational-intelligence-services/{service_id}/workloads",
            json={"workload_type": "orchestrate", "context": {"x": 1}},
        )
        assert denied.status_code == 403
    finally:
        app.dependency_overrides.clear()
        registry._services.clear()
