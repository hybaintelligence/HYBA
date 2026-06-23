"""Backend mining API validation for frontend-facing requests."""

from __future__ import annotations

from tests.test_backend_api_helpers import bearer_headers, make_client


def test_get_mining_pools_returns_summary_and_pool_list() -> None:
    with make_client() as client:
        response = client.get(
            "/api/mining/pools", headers=bearer_headers("mining:read")
        )

    assert response.status_code == 200
    data = response.json()
    assert "pools" in data
    assert "summary" in data
    assert isinstance(data["pools"], list)
    assert data["summary"]["total_pools"] == len(data["pools"])
    assert data["summary"]["telemetry_source"] == "live_api"


def test_get_pool_config_exposes_configured_pool_records() -> None:
    with make_client() as client:
        response = client.get(
            "/api/mining/pool-config", headers=bearer_headers("mining:read")
        )

    assert response.status_code == 200
    data = response.json()
    assert "pools" in data
    assert "active_pool_id" in data
    assert all("required_fields" in pool for pool in data["pools"])


def test_mining_status_is_readable_without_active_connection() -> None:
    with make_client() as client:
        response = client.get(
            "/api/mining/status", headers=bearer_headers("mining:read")
        )

    assert response.status_code == 200
    data = response.json()
    assert data["telemetry_source"] == "live_api"
    assert "midas" in data
    assert "shares" in data


def test_mining_health_reports_structured_checks() -> None:
    with make_client() as client:
        response = client.get(
            "/api/mining/health", headers=bearer_headers("mining:read")
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] in {"healthy", "degraded", "unhealthy"}
    assert {"daemon", "connection", "activity", "midas"}.issubset(data["checks"])


def test_connect_rejects_unknown_pool_with_validation_error() -> None:
    payload = {
        "pool_id": "test-pool",
        "worker": "test-worker",
        "password": "test",
        "capacity_ehs": 0.5,
    }
    with make_client() as client:
        response = client.post(
            "/api/mining/connect",
            json=payload,
            headers=bearer_headers("mining:operate"),
        )

    assert response.status_code == 422
    assert response.status_code < 500


def test_connect_enforces_capacity_hashrate_cap() -> None:
    payload = {"pool_id": "viabtc", "capacity_ehs": 1.5}
    with make_client() as client:
        response = client.post(
            "/api/mining/connect",
            json=payload,
            headers=bearer_headers("mining:operate"),
        )

    assert response.status_code == 422
    assert response.status_code < 500


def test_pause_without_connection_returns_controlled_conflict() -> None:
    with make_client() as client:
        response = client.post(
            "/api/mining/pause", json={}, headers=bearer_headers("mining:operate")
        )

    assert response.status_code in {409, 429}
    assert response.status_code < 500


def test_resume_without_connection_returns_controlled_conflict() -> None:
    with make_client() as client:
        response = client.post(
            "/api/mining/resume", json={}, headers=bearer_headers("mining:operate")
        )

    assert response.status_code in {409, 429}
    assert response.status_code < 500


def test_submit_without_active_connection_fails_closed() -> None:
    payload = {
        "pool_id": "viabtc",
        "worker": "test-worker",
        "job_id": "job-1",
        "nonce": "0x1a2b",
        "hashrate_ehs": 0.5,
    }
    with make_client() as client:
        response = client.post(
            "/api/mining/submit", json=payload, headers=bearer_headers("mining:operate")
        )

    assert response.status_code in {400, 429}
    assert response.status_code < 500


def test_mining_read_endpoints_require_authorization() -> None:
    with make_client() as client:
        response = client.get("/api/mining/pools")

    assert response.status_code == 401
