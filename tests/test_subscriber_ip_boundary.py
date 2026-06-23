from __future__ import annotations

import importlib

import pytest

fastapi = pytest.importorskip(
    "fastapi", reason="FastAPI backend dependencies are not installed"
)
from fastapi import FastAPI
from fastapi.testclient import TestClient


def _client(monkeypatch: pytest.MonkeyPatch, production: bool = True) -> TestClient:
    monkeypatch.setenv("NODE_ENV", "production" if production else "development")
    monkeypatch.setenv("HYBA_API_KEYS", "operator-test-key")
    import hyba_genesis_api.core.api_posture as api_posture

    api_posture = importlib.reload(api_posture)
    app = FastAPI()
    api_posture.install_enterprise_api_posture(app)

    @app.get("/api/security/status")
    async def leaked_status() -> dict[str, object]:
        return {
            "status": "integrated",
            "intelligence_integration": {"phi_integrated": 0.99},
            "defense_systems": {"stabilizer_swarm": "active"},
            "source": "multi_intelligence_security_runtime",
        }

    @app.post("/api/security/regeneration/trigger")
    async def regeneration_trigger() -> dict[str, object]:
        return {"status": "would_have_triggered", "clifford_index": 7}

    return TestClient(app)


def test_security_status_is_subscriber_safe_and_redacted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _client(monkeypatch)

    response = client.get("/api/security/status?observer_pressure=1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "protected"
    assert payload["source"] == "subscriber_safe_security_boundary"
    assert payload["defense_systems"]["intelligence_runtime"] == "internal_only"
    serialized = str(payload).lower()
    assert "phi_integrated" not in serialized
    assert "stabilizer_swarm" not in serialized
    assert "clifford" not in serialized
    assert "observer_pressure" not in serialized


def test_security_operator_routes_are_hidden_from_subscribers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _client(monkeypatch)

    response = client.post("/api/security/regeneration/trigger")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_security_operator_routes_allow_configured_operator_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _client(monkeypatch)

    response = client.post(
        "/api/security/regeneration/trigger",
        headers={"X-API-Key": "operator-test-key"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "would_have_triggered"
