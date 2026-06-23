"""Behavioral API contract tests for the mining operations surface.

These tests intentionally exercise FastAPI through TestClient instead of checking
that documentation agrees with itself. They cover auth boundaries, validation,
response-shape commitments, redaction, idempotency, and body-size posture for the
PYTHIA-adjacent mining API domain.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from test_backend_api_helpers import bearer_headers, make_client


@pytest.fixture()
def mining_api_sandbox(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> dict[str, Path]:
    """Redirect mutable mining files away from the repository checkout."""

    from hyba_genesis_api.api import mining

    state_path = tmp_path / "pythia_state.json"
    config_path = tmp_path / "mining_config.json"
    pool_config_path = tmp_path / "mining_pools_config.json"

    monkeypatch.setenv("HYBA_POOL_CONFIG_PATH", str(pool_config_path))
    monkeypatch.setattr(mining, "_state_path", lambda: str(state_path))
    monkeypatch.setattr(mining, "_config_path", lambda: str(config_path))
    monkeypatch.setattr(
        mining,
        "start_pythia_daemon",
        lambda capacity_ehs=None: {
            "status": "started",
            "pid": 4242,
            "capacity_ehs": capacity_ehs,
            "hashrate_cap_ehs": mining.PULVINI_HASHRATE_CAP_EHS,
        },
    )
    monkeypatch.setattr(mining, "stop_pythia_daemon", lambda: {"status": "stopped"})
    return {
        "state": state_path,
        "config": config_path,
        "pool_config": pool_config_path,
    }


def _assert_enterprise_error(
    payload: dict[str, Any], *, code: str, status_code: int
) -> None:
    assert payload["success"] is False
    assert payload["error"]["code"] == code
    assert payload["error"]["status_code"] == status_code
    assert payload["error"]["request_id"]


def test_mining_status_requires_authentication(
    mining_api_sandbox: dict[str, Path],
) -> None:
    client = make_client()

    response = client.get("/api/mining/status")

    assert response.status_code == 401
    _assert_enterprise_error(response.json(), code="http_error", status_code=401)
    assert response.headers["X-Request-ID"]
    assert response.headers["Cache-Control"] == "no-store"


def test_mining_control_rejects_read_only_role(
    mining_api_sandbox: dict[str, Path],
) -> None:
    client = make_client()

    response = client.post(
        "/api/mining/pool-config",
        headers=bearer_headers("treasury_viewer", "mining:read"),
        json={"pool_id": "viabtc", "username": "operator", "password": "x"},
    )

    assert response.status_code == 403
    _assert_enterprise_error(response.json(), code="http_error", status_code=403)


@pytest.mark.parametrize(
    ("payload", "expected_fragment"),
    [
        ({"pool_id": "unknown", "username": "operator", "password": "x"}, "pool_id"),
        (
            {"pool_id": "viabtc", "username": "bad worker!", "password": "x"},
            "identifier",
        ),
        ({"pool_id": "ckpool", "btc_address": "short"}, "BTC address"),
    ],
)
def test_pool_config_payload_validation_fails_closed(
    mining_api_sandbox: dict[str, Path], payload: dict[str, Any], expected_fragment: str
) -> None:
    client = make_client()

    response = client.post(
        "/api/mining/pool-config",
        headers=bearer_headers("ceo", "mining:operate"),
        json=payload,
    )

    assert response.status_code == 422
    body = response.json()
    _assert_enterprise_error(body, code="validation_error", status_code=422)
    assert expected_fragment in response.text


def test_pool_config_write_redacts_credentials_and_supports_idempotency(
    mining_api_sandbox: dict[str, Path],
) -> None:
    client = make_client()
    headers = {
        **bearer_headers("ceo", "mining:operate", "mining:read"),
        "Idempotency-Key": "pool-config-redaction-contract",
    }
    payload = {
        "pool_id": "viabtc",
        "username": "hyba.operator",
        "password": "super-secret-token",
        "url": "stratum+tcp://btc.viabtc.io:3333",
    }

    first = client.post("/api/mining/pool-config", headers=headers, json=payload)
    second = client.post("/api/mining/pool-config", headers=headers, json=payload)

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json() == second.json()
    pool = first.json()["pool"]
    assert pool["username"] == "<configured>"
    assert pool["password"] == "<configured>"
    assert "super-secret-token" not in first.text
    persisted = mining_api_sandbox["pool_config"].read_text(encoding="utf-8")
    assert (
        "super-secret-token" in persisted
    ), "secret may persist only in the private runtime file"


def test_mining_status_and_job_search_return_frontend_contract_shapes(
    mining_api_sandbox: dict[str, Path],
) -> None:
    mining_api_sandbox["state"].write_text(
        json.dumps(
            {
                "hashrate_ehs": 99.0,
                "total_shares": 4,
                "accepted_shares": 3,
                "rejected_shares": 1,
                "current_job": {"job_id": "job-current", "target": 1},
                "last_job": {"job_id": "job-last", "status": "rejected"},
            }
        ),
        encoding="utf-8",
    )
    client = make_client()
    headers = bearer_headers("ceo", "mining:read")

    status_response = client.get("/api/mining/status", headers=headers)
    jobs_response = client.get(
        "/api/mining/jobs/search?limit=10&offset=0", headers=headers
    )

    assert status_response.status_code == 200, status_response.text
    status_body = status_response.json()
    assert status_body["status"] in {"running", "stopped"}
    assert status_body["hashrate_ehs"] == 1.0
    assert status_body["hashrate_cap_ehs"] == 1.0
    assert status_body["shares"] == {"submitted": 4, "accepted": 3, "rejected": 1}
    assert status_body["telemetry_source"] == "live_api"

    assert jobs_response.status_code == 200, jobs_response.text
    jobs_body = jobs_response.json()
    assert jobs_body["total"] == 2
    assert [job["job_id"] for job in jobs_body["jobs"]] == ["job-current", "job-last"]


def test_oversized_api_payload_is_rejected_before_route_handler(
    mining_api_sandbox: dict[str, Path],
) -> None:
    client = make_client()

    response = client.post(
        "/api/mining/pool-config",
        headers={
            **bearer_headers("ceo", "mining:operate"),
            "Content-Length": str(3 * 1024 * 1024),
            "Content-Type": "application/json",
        },
        content=b"{}",
    )

    assert response.status_code == 413
    _assert_enterprise_error(
        response.json(), code="request_body_too_large", status_code=413
    )
