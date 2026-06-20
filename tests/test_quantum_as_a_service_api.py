"""API tests for the commercial Quantum-as-a-Service fault-tolerant computer."""

from __future__ import annotations

from fastapi.testclient import TestClient

from hyba_genesis_api.api.admin import require_admin
from hyba_genesis_api.api.customer_access import CustomerPrincipal
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


def _customer_principal(tier: str = "developer", sovereign_enabled: bool = False) -> CustomerPrincipal:
    """Create a test customer principal with specified tier."""
    metadata = {}
    if sovereign_enabled:
        metadata["sovereign_enabled"] = True
    return CustomerPrincipal(
        customer_id="test-customer",
        tier=tier,
        metadata=metadata,
    )


def _override_customer_auth(principal: CustomerPrincipal):
    """Override customer auth dependency for testing."""
    from hyba_genesis_api.api.customer_access import require_customer_api_key

    def _mock_require():
        return principal

    app.dependency_overrides[require_customer_api_key] = _mock_require


def test_public_qaas_cannot_set_admin_privileged():
    """Test that public customers cannot set admin_privileged=True."""
    registry._computers.clear()
    principal = _customer_principal(tier="developer")
    _override_customer_auth(principal)
    try:
        client = TestClient(app)
        # Try to provision with admin_privileged=True (should be ignored)
        provision = client.post(
            "/api/v1/fault-tolerant-computers",
            json={
                "name": "customer-qpu",
                "tier": "developer",
                "isolation": "single-tenant",
                "code_distance": 7,
                "logical_qubits": 32,
            },
        )
        assert provision.status_code == 201
        body = provision.json()
        # Verify admin_privileged is always False for customer requests
        assert body["admin_privileged"] is False
    finally:
        app.dependency_overrides.clear()
        registry._computers.clear()


def test_public_developer_key_cannot_request_production_qpu():
    """Test that developer API key cannot request production tier QaaS."""
    registry._computers.clear()
    principal = _customer_principal(tier="developer")
    _override_customer_auth(principal)
    try:
        client = TestClient(app)
        # Try to provision production tier with developer key
        provision = client.post(
            "/api/v1/fault-tolerant-computers",
            json={
                "name": "customer-qpu",
                "tier": "production",
                "isolation": "single-tenant",
                "code_distance": 7,
                "logical_qubits": 32,
            },
        )
        assert provision.status_code == 403
        assert "Developer API key can only provision developer tier" in provision.text
    finally:
        app.dependency_overrides.clear()
        registry._computers.clear()


def test_public_developer_key_cannot_request_dedicated_isolation():
    """Test that developer API key cannot request dedicated-control-plane isolation."""
    registry._computers.clear()
    principal = _customer_principal(tier="developer")
    _override_customer_auth(principal)
    try:
        client = TestClient(app)
        # Try to provision with dedicated-control-plane isolation
        provision = client.post(
            "/api/v1/fault-tolerant-computers",
            json={
                "name": "customer-qpu",
                "tier": "developer",
                "isolation": "dedicated-control-plane",
                "code_distance": 7,
                "logical_qubits": 32,
            },
        )
        assert provision.status_code == 403
        assert "Developer API key can only use single-tenant isolation" in provision.text
    finally:
        app.dependency_overrides.clear()
        registry._computers.clear()


def test_public_production_key_cannot_request_sovereign_isolation():
    """Test that production API key cannot request sovereign-isolated isolation."""
    registry._computers.clear()
    principal = _customer_principal(tier="production")
    _override_customer_auth(principal)
    try:
        client = TestClient(app)
        # Try to provision with sovereign-isolated isolation
        provision = client.post(
            "/api/v1/fault-tolerant-computers",
            json={
                "name": "customer-qpu",
                "tier": "production",
                "isolation": "sovereign-isolated",
                "code_distance": 7,
                "logical_qubits": 32,
            },
        )
        assert provision.status_code == 403
        assert "Production API key can only use single-tenant or dedicated-control-plane" in provision.text
    finally:
        app.dependency_overrides.clear()
        registry._computers.clear()


def test_public_enterprise_requires_sovereign_entitlement():
    """Test that enterprise API key requires sovereign_enabled=true for sovereign tier."""
    registry._computers.clear()
    principal = _customer_principal(tier="enterprise", sovereign_enabled=False)
    _override_customer_auth(principal)
    try:
        client = TestClient(app)
        # Try to provision sovereign tier without entitlement
        provision = client.post(
            "/api/v1/fault-tolerant-computers",
            json={
                "name": "customer-qpu",
                "tier": "sovereign",
                "isolation": "single-tenant",
                "code_distance": 7,
                "logical_qubits": 32,
            },
        )
        assert provision.status_code == 403
        assert "requires sovereign_enabled=true metadata" in provision.text
    finally:
        app.dependency_overrides.clear()
        registry._computers.clear()


def test_public_enterprise_with_sovereign_entitlement_can_request_sovereign():
    """Test that enterprise API key with sovereign_enabled=true can request sovereign tier."""
    registry._computers.clear()
    principal = _customer_principal(tier="enterprise", sovereign_enabled=True)
    _override_customer_auth(principal)
    try:
        client = TestClient(app)
        # Provision sovereign tier with proper entitlement
        provision = client.post(
            "/api/v1/fault-tolerant-computers",
            json={
                "name": "customer-qpu",
                "tier": "sovereign",
                "isolation": "sovereign-isolated",
                "code_distance": 7,
                "logical_qubits": 32,
            },
        )
        assert provision.status_code == 201
        body = provision.json()
        assert body["tier"] == "sovereign"
        assert body["isolation"] == "sovereign-isolated"
    finally:
        app.dependency_overrides.clear()
        registry._computers.clear()


def test_public_qaas_rejects_excessive_estimated_units():
    """Test that QaaS rejects workloads exceeding tier sync limits."""
    registry._computers.clear()
    principal = _customer_principal(tier="developer")
    _override_customer_auth(principal)
    try:
        client = TestClient(app)
        # Provision a computer
        provision = client.post(
            "/api/v1/fault-tolerant-computers",
            json={
                "name": "customer-qpu",
                "tier": "developer",
                "isolation": "single-tenant",
                "code_distance": 7,
                "logical_qubits": 32,
            },
        )
        computer_id = provision.json()["computer_id"]
        
        # Start the computer
        client.post(f"/api/v1/fault-tolerant-computers/{computer_id}/start")
        
        # Try to execute workload exceeding developer tier limits (10,000 units)
        # circuit_depth=1000, shots=10, logical_qubits=2 = 20,000 units > 10,000 limit
        execute = client.post(
            f"/api/v1/fault-tolerant-computers/{computer_id}/execute",
            json={
                "operation": "surface_code_cycle",
                "logical_qubits": [0, 1],
                "circuit_depth": 1000,
                "shots": 10,
            },
        )
        assert execute.status_code == 413
        assert "exceed tier sync limit" in execute.text
    finally:
        app.dependency_overrides.clear()
        registry._computers.clear()


def test_public_qaas_rejects_excessive_logical_qubits():
    """Test that QaaS rejects workloads exceeding tier logical qubit limits."""
    registry._computers.clear()
    principal = _customer_principal(tier="developer")
    _override_customer_auth(principal)
    try:
        client = TestClient(app)
        # Provision a computer
        provision = client.post(
            "/api/v1/fault-tolerant-computers",
            json={
                "name": "customer-qpu",
                "tier": "developer",
                "isolation": "single-tenant",
                "code_distance": 7,
                "logical_qubits": 32,
            },
        )
        computer_id = provision.json()["computer_id"]
        
        # Start the computer
        client.post(f"/api/v1/fault-tolerant-computers/{computer_id}/start")
        
        # Try to execute workload exceeding developer tier qubit limit (32 qubits)
        execute = client.post(
            f"/api/v1/fault-tolerant-computers/{computer_id}/execute",
            json={
                "operation": "surface_code_cycle",
                "logical_qubits": list(range(50)),  # 50 qubits > 32 limit
                "circuit_depth": 10,
                "shots": 1,
            },
        )
        assert execute.status_code == 413
        assert "exceeds tier sync limit" in execute.text
    finally:
        app.dependency_overrides.clear()
        registry._computers.clear()


def test_idempotency_rejects_mismatched_request():
    """Test that idempotency key with different request payload is rejected."""
    app.dependency_overrides[require_admin] = _admin_payload
    registry._computers.clear()
    try:
        client = TestClient(app)
        provision = client.post(
            "/api/admin/fault-tolerant-computers",
            json={"name": "idempotency-qpu", "code_distance": 5, "logical_qubits": 4},
        )
        computer_id = provision.json()["computer_id"]
        client.post(f"/api/admin/fault-tolerant-computers/{computer_id}/start")

        # First execution with idempotency key
        first = client.post(
            f"/api/admin/fault-tolerant-computers/{computer_id}/execute",
            json={
                "operation": "surface_code_cycle",
                "logical_qubits": [0, 1],
                "circuit_depth": 2,
                "shots": 8,
                "idempotency_key": "test-key-1",
            },
        )
        assert first.status_code == 200

        # Replay with same key but different request (should be rejected)
        replay = client.post(
            f"/api/admin/fault-tolerant-computers/{computer_id}/execute",
            json={
                "operation": "surface_code_cycle",
                "logical_qubits": [2, 3],  # Different qubits
                "circuit_depth": 2,
                "shots": 8,
                "idempotency_key": "test-key-1",  # Same key
            },
        )
        assert replay.status_code == 409
        assert "Idempotency key reused with different request payload" in replay.text
    finally:
        app.dependency_overrides.clear()
        registry._computers.clear()
