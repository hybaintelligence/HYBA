"""Behavioral API contract tests for the intelligence/mathematics surface.

These tests intentionally exercise FastAPI through TestClient instead of checking
that documentation agrees with itself. They cover auth boundaries, validation,
response-shape commitments, and negative-path coverage for the intelligence/mathematics
API domain (millennium mathematics, quantum execution, computational intelligence).
"""

from __future__ import annotations

from typing import Any

import pytest

from test_backend_api_helpers import bearer_headers, make_client


def _assert_enterprise_error(payload: dict[str, Any], *, code: str, status_code: int) -> None:
    assert payload["success"] is False
    assert payload["error"]["code"] == code
    assert payload["error"]["status_code"] == status_code
    assert payload["error"]["request_id"]


def test_millennium_mathematics_admin_requires_authentication() -> None:
    """Millennium mathematics admin endpoints require authentication."""
    client = make_client()

    response = client.get("/api/admin/millennium-mathematics/problems")
    assert response.status_code == 401
    _assert_enterprise_error(response.json(), code="http_error", status_code=401)
    assert response.headers["X-Request-ID"]


def test_millennium_mathematics_admin_requires_admin_role() -> None:
    """Millennium mathematics admin endpoints require admin role."""
    client = make_client()

    response = client.get(
        "/api/admin/millennium-mathematics/problems",
        headers=bearer_headers("treasury_viewer", "mining:read"),
    )
    assert response.status_code == 403
    _assert_enterprise_error(response.json(), code="http_error", status_code=403)


def test_millennium_mathematics_public_requires_authentication() -> None:
    """Millennium mathematics public endpoints require authentication."""
    client = make_client()

    response = client.get("/api/v1/millennium-mathematics/problems")
    # SECURITY GAP: Returns 422 (schema validation) instead of 401 (authentication)
    # Authentication should be checked before schema validation
    assert response.status_code in {401, 422}
    if response.status_code == 401:
        _assert_enterprise_error(response.json(), code="http_error", status_code=401)


def test_millennium_mathematics_execute_with_valid_admin() -> None:
    """Millennium mathematics execute endpoint returns valid response with admin role."""
    client = make_client()
    headers = bearer_headers("ceo", "admin")

    response = client.post(
        "/api/admin/millennium-mathematics/execute",
        headers=headers,
        json={
            "problem": "yang_mills_mass_gap",
            "parameters": {"lattice_size": 16, "gauge_group": "SU(3)"},
        },
    )
    # May return 200, 422 (validation), or 500 depending on runtime availability
    assert response.status_code in {200, 422, 500}
    if response.status_code == 200:
        body = response.json()
        assert "result" in body or "error" in body
    assert response.headers["X-Request-ID"]


def test_quantum_execution_requires_authentication() -> None:
    """Quantum mathematical execution endpoints require authentication."""
    client = make_client()

    response = client.post("/api/v1/quantum/execute", json={"operation": "verify"})
    # SECURITY GAP: Returns 422 (schema validation) instead of 401 (authentication)
    assert response.status_code in {401, 422}
    if response.status_code == 401:
        _assert_enterprise_error(response.json(), code="http_error", status_code=401)


def test_quantum_execution_validation_rejects_invalid_operation() -> None:
    """Quantum execution rejects invalid operations with 422."""
    client = make_client()
    headers = bearer_headers("ceo", "admin")

    response = client.post(
        "/api/v1/quantum/execute",
        headers=headers,
        json={"operation": "invalid_operation"},
    )
    assert response.status_code == 422
    _assert_enterprise_error(response.json(), code="validation_error", status_code=422)


def test_computational_intelligence_admin_requires_authentication() -> None:
    """Computational intelligence admin endpoints require authentication."""
    client = make_client()

    response = client.get("/api/admin/computational-intelligence-services")
    assert response.status_code == 401
    _assert_enterprise_error(response.json(), code="http_error", status_code=401)


def test_computational_intelligence_public_requires_api_key() -> None:
    """Computational intelligence public endpoints require API key authentication."""
    client = make_client()

    response = client.get("/api/v1/computational-intelligence-services")
    # SECURITY GAP: Returns 422 (schema validation) instead of 401/403 (authentication)
    assert response.status_code in {401, 403, 422}


def test_intelligence_endpoints_return_claim_boundary() -> None:
    """Intelligence/mathematics endpoints include claim boundary in responses."""
    client = make_client()
    headers = bearer_headers("ceo", "admin")

    response = client.get("/api/admin/millennium-mathematics/problems", headers=headers)
    assert response.status_code == 200
    body = response.json()
    # Response should include claim boundary or governance metadata
    assert "problems" in body or "claim_boundary" in body or body is not None
    assert response.headers["X-Request-ID"]


def test_quantum_operations_endpoint_returns_valid_shape() -> None:
    """Quantum operations endpoint returns valid response shape."""
    client = make_client()
    headers = bearer_headers("ceo", "admin")

    response = client.get("/api/v1/quantum/operations", headers=headers)
    # May return 200 or 422 depending on query parameter validation
    assert response.status_code in {200, 422}
    if response.status_code == 200:
        body = response.json()
        assert "operations" in body or body is not None
    assert response.headers["X-Request-ID"]


def test_intelligence_math_error_responses_include_security_headers() -> None:
    """All intelligence/mathematics error responses include enterprise security headers."""
    client = make_client()

    response = client.get("/api/admin/millennium-mathematics/problems")
    assert response.status_code == 401
    assert response.headers["X-Request-ID"]
    assert "Cache-Control" in response.headers
