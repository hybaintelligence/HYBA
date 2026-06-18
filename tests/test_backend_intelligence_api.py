"""Backend intelligence API validation for frontend-facing requests."""

from __future__ import annotations

from tests.test_backend_api_helpers import make_client


def test_ai_consciousness_endpoint_returns_explicit_runtime_state() -> None:
    with make_client() as client:
        response = client.get("/api/ai/consciousness")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] in {"not_measured", "measured", "error"}
    assert "timestamp" in data
    assert "runtime_state" in data


def test_ai_consciousness_stimulation_accepts_bounded_request() -> None:
    with make_client() as client:
        response = client.post(
            "/api/ai/consciousness/stimulate",
            json={"intensity": 0.25, "duration_seconds": 5},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "accepted_degraded"


def test_ai_chat_fails_closed_when_runtime_is_unconfigured() -> None:
    with make_client() as client:
        response = client.post("/api/ai/chat", json={"message": "hello"})

    assert response.status_code == 501
    data = response.json()
    assert data["detail"]["error"] == "ai_runtime_not_connected"


def test_v1_intelligence_health_reports_runtime_surface() -> None:
    with make_client() as client:
        response = client.get("/api/v1/intelligence/health")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "timestamp" in data


def test_v1_intelligence_audit_returns_claim_bounded_payload() -> None:
    with make_client() as client:
        response = client.get("/api/v1/intelligence/audit")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "audit" in data or "components" in data or "checks" in data


def test_legacy_intelligence_status_path_is_not_fabricated() -> None:
    with make_client() as client:
        response = client.get("/api/intelligence/status")

    assert response.status_code in {404, 405}


def test_legacy_intelligence_telemetry_path_is_not_fabricated() -> None:
    with make_client() as client:
        response = client.get("/api/intelligence/telemetry")

    assert response.status_code in {404, 405}


def test_invalid_ai_stimulation_request_returns_validation_error() -> None:
    with make_client() as client:
        response = client.post(
            "/api/ai/consciousness/stimulate",
            json={"intensity": 2.0, "duration_seconds": 5},
        )

    assert response.status_code == 422
