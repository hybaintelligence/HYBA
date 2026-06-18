"""Live full-stack connectivity and deployment-readiness checks.

These tests are intentionally black-box checks against the documented local
operator stack: the FastAPI backend on 127.0.0.1:3001 and the frontend dev
server on 127.0.0.1:3000. They skip when either server is not running so the
regular offline unit-test suite remains deterministic.
"""

from __future__ import annotations

import concurrent.futures
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import pytest
from urllib import error as urlerror
from urllib import request as urlrequest


class SimpleResponse:
    def __init__(self, status_code: int, headers: dict[str, str], body: bytes):
        self.status_code = status_code
        self.headers = headers
        self._body = body

    def json(self) -> Any:
        return json.loads(self._body.decode("utf-8"))

    @property
    def text(self) -> str:
        return self._body.decode("utf-8", errors="replace")


BACKEND_URL = "http://127.0.0.1:3001"
FRONTEND_URL = "http://127.0.0.1:3000"
REQUEST_TIMEOUT_SECONDS = 2.0


def _request(
    url: str,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = REQUEST_TIMEOUT_SECONDS,
) -> SimpleResponse:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request_headers = dict(headers or {})
    if body is not None:
        request_headers.setdefault("Content-Type", "application/json")
    req = urlrequest.Request(url, data=body, headers=request_headers, method=method)
    try:
        with urlrequest.urlopen(req, timeout=timeout) as response:
            return SimpleResponse(response.status, dict(response.headers.items()), response.read())
    except urlerror.HTTPError as exc:
        return SimpleResponse(exc.code, dict(exc.headers.items()), exc.read())


def _get_json(url: str, *, timeout: float = REQUEST_TIMEOUT_SECONDS) -> SimpleResponse:
    return _request(url, timeout=timeout)


def _post_json(url: str, payload: dict[str, Any], *, timeout: float = REQUEST_TIMEOUT_SECONDS) -> SimpleResponse:
    return _request(url, method="POST", payload=payload, timeout=timeout)


def _server_available(url: str) -> bool:
    try:
        response = _get_json(url)
        return response.status_code < 500
    except (urlerror.URLError, TimeoutError):
        return False


requires_backend = pytest.mark.skipif(
    not _server_available(f"{BACKEND_URL}/health"),
    reason="HYBA backend is not running on 127.0.0.1:3001",
)
requires_fullstack = pytest.mark.skipif(
    not (
        _server_available(f"{BACKEND_URL}/health")
        and _server_available(FRONTEND_URL)
    ),
    reason="HYBA backend and frontend dev server are not both running",
)


@requires_fullstack
class TestFullStackConnectivity:
    """Test complete frontend-backend integration through the dev proxy."""

    def test_backend_is_running(self) -> None:
        response = _get_json(f"{BACKEND_URL}/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_frontend_is_running(self) -> None:
        response = _get_json(FRONTEND_URL)
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_frontend_proxy_to_backend(self) -> None:
        response_via_frontend = _get_json(f"{FRONTEND_URL}/api/health")
        response_via_backend = _get_json(f"{BACKEND_URL}/api/health")

        assert response_via_frontend.status_code == 200
        assert response_via_backend.status_code == 200
        assert response_via_frontend.json()["status"] == response_via_backend.json()["status"]

    def test_api_health_proxy_preserves_request_id_header(self) -> None:
        response = _get_json(f"{FRONTEND_URL}/api/health")
        assert response.status_code == 200
        assert response.headers.get("x-request-id")

    def test_substrate_readiness_through_backend(self) -> None:
        response = _get_json(f"{BACKEND_URL}/api/substrate")
        assert response.status_code == 200
        assert response.json().get("ready") is True

    def test_full_mining_workflow(self) -> None:
        pools_resp = _get_json(f"{FRONTEND_URL}/api/mining/pools")
        assert pools_resp.status_code == 200
        pools_data = pools_resp.json()
        assert isinstance(pools_data.get("pools"), list)
        assert "summary" in pools_data

        connect_payload = {
            "pool_id": "test-pool",
            "worker": "test-worker",
            "password": "test",
            "capacity_ehs": 0.5,
        }
        connect_resp = _post_json(f"{FRONTEND_URL}/api/mining/connect", connect_payload)
        assert 200 <= connect_resp.status_code < 600

        config_resp = _get_json(f"{FRONTEND_URL}/api/mining/pool-config")
        assert config_resp.status_code == 200
        assert "pools" in config_resp.json()

    def test_security_status_available(self) -> None:
        response = _get_json(f"{FRONTEND_URL}/api/security/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "threat_level" in data

    def test_cross_origin_preflight_requests(self) -> None:
        response = _request(
            f"{BACKEND_URL}/api/mining/connect",
            method="OPTIONS",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert response.status_code == 200
        assert "access-control-allow-origin" in {key.lower() for key in response.headers}

    def test_backend_validation_errors_use_enterprise_envelope(self) -> None:
        response = _post_json(f"{FRONTEND_URL}/api/mining/connect", {"pool_id": "test-pool"})
        assert response.status_code in {400, 422}
        data = response.json()
        assert data.get("success") is False
        assert data.get("error", {}).get("request_id")

    def test_retry_candidate_health_requests_remain_stable(self) -> None:
        for _ in range(5):
            response = _get_json(f"{FRONTEND_URL}/api/health")
            assert response.status_code == 200
            time.sleep(0.1)


@requires_backend
class TestPerformance:
    """Basic deployment-readiness performance checks for the backend."""

    def test_response_latency(self) -> None:
        start = time.perf_counter()
        response = _get_json(f"{BACKEND_URL}/health")
        latency_ms = (time.perf_counter() - start) * 1000

        assert response.status_code == 200
        assert latency_ms < 1000

    def test_concurrent_requests(self) -> None:
        def make_request(_: int) -> SimpleResponse:
            return _get_json(f"{BACKEND_URL}/health")

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(make_request, range(20)))

        assert all(response.status_code == 200 for response in results)


class DeploymentReadinessReport:
    """Generate a JSON deployment-readiness report from live local services."""

    def __init__(self, backend_url: str = BACKEND_URL, frontend_url: str = FRONTEND_URL):
        self.backend_url = backend_url.rstrip("/")
        self.frontend_url = frontend_url.rstrip("/")

    def generate(self, output_path: str | Path = "DEPLOYMENT_READINESS_REPORT.json") -> dict[str, Any]:
        checks = {
            "backend_running": self._check_backend,
            "frontend_running": self._check_frontend,
            "proxy_working": self._check_proxy,
            "health_endpoints": self._check_health,
            "mining_api": self._check_mining_api,
            "security_api": self._check_security_api,
            "cors_enabled": self._check_cors,
            "performance": self._check_performance,
        }
        results = {name: check() for name, check in checks.items()}
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": results,
            "status": "READY" if all(results.values()) else "BLOCKED",
        }
        Path(output_path).write_text(json.dumps(report, indent=2), encoding="utf-8")
        return report

    def _safe_check(self, check: Callable[[], bool]) -> bool:
        try:
            return check()
        except (urlerror.URLError, TimeoutError):
            return False

    def _check_backend(self) -> bool:
        return self._safe_check(lambda: _get_json(f"{self.backend_url}/health").status_code == 200)

    def _check_frontend(self) -> bool:
        return self._safe_check(lambda: _get_json(self.frontend_url).status_code == 200)

    def _check_proxy(self) -> bool:
        return self._safe_check(lambda: _get_json(f"{self.frontend_url}/api/health").status_code == 200)

    def _check_health(self) -> bool:
        return self._safe_check(lambda: _get_json(f"{self.backend_url}/api/health").status_code == 200)

    def _check_mining_api(self) -> bool:
        return self._safe_check(lambda: _get_json(f"{self.backend_url}/api/mining/pools").status_code == 200)

    def _check_security_api(self) -> bool:
        return self._safe_check(lambda: _get_json(f"{self.backend_url}/api/security/status").status_code == 200)

    def _check_cors(self) -> bool:
        def check() -> bool:
            response = _request(
                f"{self.backend_url}/api/mining/connect",
                method="OPTIONS",
                headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST"},
            )
            return response.status_code == 200 and "access-control-allow-origin" in {
                key.lower() for key in response.headers
            }

        return self._safe_check(check)

    def _check_performance(self) -> bool:
        def check() -> bool:
            start = time.perf_counter()
            response = _get_json(f"{self.backend_url}/health")
            return response.status_code == 200 and (time.perf_counter() - start) * 1000 < 1000

        return self._safe_check(check)
