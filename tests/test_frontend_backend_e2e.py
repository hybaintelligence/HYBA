"""Frontend/backend E2E bootstrap tests.

These tests exercise the FastAPI app the way the frontend operator dashboard does:
start from process health, read readiness, load mining status, and perform a job
search without requiring a specific job id. Contract tests check individual JSON
shapes; this file checks that the route sequence works together as a runtime path.
"""

from __future__ import annotations

from test_backend_api_helpers import bearer_headers, make_client


def test_e2e_operator_dashboard_bootstrap_sequence() -> None:
    """The core dashboard bootstrap route sequence must work against the real app."""

    client = make_client()
    headers = bearer_headers("ceo", "mining:read", "mining:operate")

    health = client.get("/api/health")
    assert health.status_code == 200, health.text
    health_payload = health.json()
    assert isinstance(health_payload, dict)
    assert isinstance(health_payload.get("status"), str)

    readiness = client.get("/api/health/readiness")
    assert readiness.status_code == 200, readiness.text
    readiness_payload = readiness.json()
    assert isinstance(readiness_payload, dict)
    assert isinstance(readiness_payload.get("status"), str)
    assert isinstance(readiness_payload.get("ready"), bool)
    assert isinstance(readiness_payload.get("subsystems"), dict)
    assert isinstance(readiness_payload.get("boot_id"), str)

    mining_status = client.get("/api/mining/status", headers=headers)
    assert mining_status.status_code == 200, mining_status.text
    mining_payload = mining_status.json()
    assert isinstance(mining_payload, dict)
    assert isinstance(mining_payload.get("status"), str)
    assert "active" in mining_payload
    assert "connection" in mining_payload

    job_search = client.get(
        "/api/mining/jobs/search?limit=5&offset=0",
        headers=headers,
    )
    assert job_search.status_code == 200, job_search.text
    job_payload = job_search.json()
    assert isinstance(job_payload, dict)
    assert isinstance(job_payload.get("jobs"), list)
    assert isinstance(job_payload.get("total"), int)


def test_e2e_operator_dashboard_optional_job_search_does_not_422() -> None:
    """The dashboard may search jobs without a selected job id during initial load."""

    client = make_client()
    headers = bearer_headers("ceo", "mining:read", "mining:operate")

    response = client.get("/api/mining/jobs/search", headers=headers)

    assert response.status_code == 200, response.text
    payload = response.json()
    assert isinstance(payload, dict)
    assert isinstance(payload.get("jobs"), list)
    assert isinstance(payload.get("total"), int)
