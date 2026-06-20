"""API tests for the commercial Quantum-as-a-Service fault-tolerant computer."""

from __future__ import annotations

from fastapi.testclient import TestClient

from hyba_genesis_api.api.admin import require_admin
from hyba_genesis_api.api.quantum_as_a_service import registry
from hyba_genesis_api.auth.jwt_handler import TokenPayload
from hyba_genesis_api.main import app


def _admin_payload() -> TokenPayload:
    return TokenPayload(sub="1", username="root-admin", roles=["admin"], exp=9999999999, iat=1)


def test_admin_provisions_virtual_fault_tolerant_quantum_computer_and_executes_surface_code_cycle():
    app.dependency_overrides[require_admin] = _admin_payload
    registry._computers.clear()
    try:
        client = TestClient(app)
        provision = client.post(
            "/api/admin/fault-tolerant-computers",
            json={
                "name": "market-qpu-01",
                "tier": "production",
                "isolation": "dedicated-control-plane",
                "code_distance": 5,
                "logical_qubits": 4,
                "physical_error_rate": 0.0001,
                "phi_resonance_target": 0.9565,
                "max_circuit_depth": 2,
                "admin_privileged": True,
            },
        )
        assert provision.status_code == 201
        body = provision.json()
        assert body["state"] == "provisioned"
        assert body["tier"] == "production"
        assert body["fault_tolerance"]["fault_tolerant"] is True
        assert body["quantum_parameters"]["logical_qubits"] == 4
        assert "mining" in body["claim_boundary"]
        assert len(body["evidence_seal"]) == 64

        computer_id = body["computer_id"]
        started = client.post(f"/api/admin/fault-tolerant-computers/{computer_id}/start")
        assert started.status_code == 200
        assert started.json()["state"] == "running"

        executed = client.post(
            f"/api/admin/fault-tolerant-computers/{computer_id}/execute",
            json={
                "operation": "surface_code_cycle",
                "logical_qubits": [0, 1],
                "circuit_depth": 2,
                "shots": 8,
                "idempotency_key": "surface-code-cycle-1",
            },
        )
        assert executed.status_code == 200
        result = executed.json()
        assert result["operation"] == "surface_code_cycle"
        assert result["result"]["syndrome_rounds"] >= 4
        assert result["fault_tolerance"]["logical_error_rate"] < 0.0001
        assert "job_id" not in result["result"]

        replay = client.post(
            f"/api/admin/fault-tolerant-computers/{computer_id}/execute",
            json={
                "operation": "surface_code_cycle",
                "logical_qubits": [2],
                "circuit_depth": 1,
                "idempotency_key": "surface-code-cycle-1",
            },
        )
        assert replay.status_code == 200
        assert replay.json()["executed_at"] == result["executed_at"]

        stopped = client.post(f"/api/admin/fault-tolerant-computers/{computer_id}/stop")
        assert stopped.status_code == 200
        assert stopped.json()["state"] == "stopped"
    finally:
        app.dependency_overrides.clear()
        registry._computers.clear()


def test_qaas_rejects_invalid_topology_and_policy_violations():
    app.dependency_overrides[require_admin] = _admin_payload
    registry._computers.clear()
    try:
        client = TestClient(app)
        bad_topology = client.post(
            "/api/admin/fault-tolerant-computers",
            json={"name": "bad-qpu", "code_distance": 4},
        )
        assert bad_topology.status_code == 422
        assert "code_distance must be odd" in bad_topology.text

        provision = client.post(
            "/api/admin/fault-tolerant-computers",
            json={
                "name": "audit-only-qpu",
                "allowed_operations": ["governance_audit"],
                "max_circuit_depth": 1,
            },
        )
        computer_id = provision.json()["computer_id"]
        client.post(f"/api/admin/fault-tolerant-computers/{computer_id}/start")

        denied = client.post(
            f"/api/admin/fault-tolerant-computers/{computer_id}/execute",
            json={"operation": "surface_code_cycle", "circuit_depth": 1},
        )
        assert denied.status_code == 403

        too_deep = client.post(
            f"/api/admin/fault-tolerant-computers/{computer_id}/execute",
            json={"operation": "governance_audit", "circuit_depth": 2},
        )
        assert too_deep.status_code == 413
    finally:
        app.dependency_overrides.clear()
        registry._computers.clear()
