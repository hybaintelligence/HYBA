"""Frontend ↔ backend contract tests.

These tests are intentionally stricter than unit tests. They exercise the real
FastAPI app and compare the returned JSON shape against the frontend SDK contract
in ``src/apiClient.ts``.

Why this exists:
- unit/invariant tests can pass while the UI receives the wrong JSON shape;
- TypeScript interfaces do not protect runtime responses from FastAPI drift;
- backend-only routers must be explicitly documented as such, not accidentally
  absent from the frontend API client.

If any test in this file fails, do not paper over it by relaxing the assertion.
Either align the backend response, align the frontend type/function, or move the
route into the explicit backend-only allowlist with a reason.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from test_backend_api_helpers import bearer_headers, make_client


REPO_ROOT = Path(__file__).resolve().parents[1]
API_CLIENT_PATH = REPO_ROOT / "src" / "apiClient.ts"


def _api_client_source() -> str:
    return API_CLIENT_PATH.read_text(encoding="utf-8")


def _assert_required_keys(
    payload: dict[str, Any],
    required: dict[str, type | tuple[type, ...]],
    *,
    endpoint: str,
    frontend_type: str,
) -> None:
    missing = [key for key in required if key not in payload]
    wrong_type = [
        f"{key}: expected {expected}, got {type(payload.get(key)).__name__}"
        for key, expected in required.items()
        if key in payload and not isinstance(payload[key], expected)
    ]
    assert not missing and not wrong_type, (
        f"{endpoint} does not satisfy frontend contract {frontend_type}. "
        f"missing={missing}, wrong_type={wrong_type}, payload_keys={sorted(payload.keys())}"
    )


def test_health_readiness_runtime_shape_matches_frontend_contract() -> None:
    """GET /api/health/readiness must satisfy HealthReadinessResponse.

    The frontend type declares status, ready, subsystems, and boot_id. This test
    catches backend readiness responses that only expose substrate/pythia detail
    without the UI-facing readiness booleans and boot identity.
    """

    client = make_client()
    response = client.get("/api/health/readiness")
    assert response.status_code < 500, response.text
    payload = response.json()
    assert isinstance(payload, dict)
    _assert_required_keys(
        payload,
        {
            "status": str,
            "ready": bool,
            "subsystems": dict,
            "boot_id": str,
        },
        endpoint="GET /api/health/readiness",
        frontend_type="HealthReadinessResponse",
    )


def test_mining_status_runtime_shape_matches_frontend_contract() -> None:
    """GET /api/mining/status must satisfy MiningStatusResponse.

    The UI asks apiClient.getMiningStatus() for a top-level status string. A
    backend response that only exposes active/daemon_running/connection/shares
    is not compatible with that contract.
    """

    client = make_client()
    response = client.get(
        "/api/mining/status",
        headers=bearer_headers("ceo", "mining:read", "mining:operate"),
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert isinstance(payload, dict)
    _assert_required_keys(
        payload,
        {
            "status": str,
        },
        endpoint="GET /api/mining/status",
        frontend_type="MiningStatusResponse",
    )


def test_mining_job_search_accepts_frontend_optional_params_contract() -> None:
    """Frontend searchMiningJobs(params?) must not hit a required-job_id backend.

    apiClient.ts exposes searchMiningJobs(params?) where pool_id/worker/limit/offset
    are optional. Calling the endpoint without job_id should therefore be valid if
    the frontend contract is truthful.
    """

    client = make_client()
    response = client.get(
        "/api/mining/jobs/search?limit=10&offset=0",
        headers=bearer_headers("ceo", "mining:read", "mining:operate"),
    )
    assert response.status_code == 200, (
        "Frontend searchMiningJobs(params?) treats job_id as optional, but backend "
        f"rejected the call: status={response.status_code}, body={response.text}"
    )


def test_mining_job_search_runtime_shape_matches_frontend_contract() -> None:
    """GET /api/mining/jobs/search must return jobs + total for the frontend."""

    client = make_client()
    response = client.get(
        "/api/mining/jobs/search?job_id=contract-test-missing-job",
        headers=bearer_headers("ceo", "mining:read", "mining:operate"),
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert isinstance(payload, dict)
    _assert_required_keys(
        payload,
        {
            "jobs": list,
            "total": int,
        },
        endpoint="GET /api/mining/jobs/search",
        frontend_type="MiningJobsSearchResponse",
    )


@pytest.mark.parametrize(
    ("route_fragment", "owner"),
    [
        ("/organism/executive", "executive CNS API"),
        ("/organism", "organism CNS API"),
        ("/organism/regeneration", "regeneration API"),
        ("/v4/metabolism", "metabolism API"),
        ("/v1/streaming", "streaming sense API"),
        ("/security/event", "security event API"),
        ("/security/regeneration", "security regeneration API"),
        ("/security/swarm", "security swarm API"),
        ("/security/blockchain", "security blockchain API"),
        ("/security/autogenous", "security autogenous API"),
    ],
)
def test_public_backend_routes_are_represented_in_frontend_api_client(
    route_fragment: str,
    owner: str,
) -> None:
    """Public backend routers must be surfaced by apiClient.ts or made explicit.

    This test is intentionally static: it catches routes that exist in FastAPI but
    cannot be called through the production frontend SDK. If a route is genuinely
    backend-only, add an explicit backend-only allowlist with a reason rather than
    leaving the absence invisible.
    """

    source = _api_client_source()
    assert route_fragment in source, (
        f"{owner} route fragment {route_fragment!r} is not represented in src/apiClient.ts. "
        "Add a typed frontend function or explicitly classify the router as backend-only."
    )
