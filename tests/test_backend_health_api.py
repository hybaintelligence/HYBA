"""Backend health and readiness API validation."""

from __future__ import annotations

from tests.test_backend_api_helpers import make_client


def test_root_health_endpoint_returns_ok() -> None:
    with make_client() as client:
        response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "substrate" in data
    assert "telemetry" in data


def test_api_health_endpoint_returns_backend_health_payload() -> None:
    with make_client() as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] in {"healthy", "degraded"}
    assert data["version"] == "2.0.1"
    assert "systemMetrics" in data


def test_liveness_probe_returns_alive() -> None:
    with make_client() as client:
        response = client.get("/api/health/live")

    assert response.status_code == 200
    assert response.json()["status"] == "alive"


def test_readiness_probe_returns_ready_or_initializing() -> None:
    with make_client() as client:
        response = client.get("/api/health/ready")

    assert response.status_code in {200, 503}
    data = response.json()
    assert data["status"] in {"ready", "initializing"}
    assert "substrate" in data


def test_detailed_readiness_endpoint_returns_substrate_and_pythia() -> None:
    with make_client() as client:
        response = client.get("/api/health/readiness")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] in {"ready", "initializing"}
    assert "substrate" in data
    assert "pythia" in data


def test_substrate_endpoint_reports_ready_flag() -> None:
    with make_client() as client:
        response = client.get("/api/substrate")

    assert response.status_code == 200
    data = response.json()
    assert "ready" in data
    assert isinstance(data["ready"], bool)
