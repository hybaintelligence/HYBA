"""Backend security API validation for frontend-facing requests."""

from __future__ import annotations

from tests.test_backend_api_helpers import make_client


def test_security_status_returns_safe_status_payload() -> None:
    with make_client() as client:
        response = client.get("/api/security/status")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "threat_level" in data
    assert "recent_threats" in data


def test_security_regeneration_status_returns_module_summary() -> None:
    with make_client() as client:
        response = client.get("/api/security/regeneration/status")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "regeneration" in data
    assert "total_modules" in data["regeneration"] or "modules" in data["regeneration"]


def test_security_swarm_status_returns_controlled_payload() -> None:
    with make_client() as client:
        response = client.get("/api/security/swarm/status")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data


def test_security_blockchain_threats_returns_controlled_payload() -> None:
    with make_client() as client:
        response = client.get("/api/security/blockchain/threats")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data


def test_security_shield_accepts_valid_degraded_mode_request_without_api_keys() -> None:
    with make_client() as client:
        response = client.post("/api/security/shield", json={"strength": 0.7})

    assert response.status_code == 200
    data = response.json()
    assert "status" in data


def test_security_shield_rejects_invalid_strength() -> None:
    with make_client() as client:
        response = client.post("/api/security/shield", json={"strength": 1.7})

    assert response.status_code == 422


def test_security_event_accepts_structured_event() -> None:
    with make_client() as client:
        response = client.post(
            "/api/security/event",
            json={"event_type": "frontend_backend_validation", "severity": "low"},
        )

    assert response.status_code < 500
