from __future__ import annotations

import asyncio
from types import SimpleNamespace

from starlette.responses import Response

from hyba_genesis_api.core import telemetry
from hyba_genesis_api.core.api_posture import (
    EnterpriseAPIConfig,
    InMemoryRateLimiter,
    apply_enterprise_security_headers,
    enterprise_error_payload,
)


def _fake_request(headers: dict[str, str] | None = None):
    return SimpleNamespace(
        headers=headers or {},
        method="GET",
        url=SimpleNamespace(path="/enterprise-test"),
        state=SimpleNamespace(),
    )


def test_enterprise_metrics_publish_gap_gate_workflow_and_audit_signals() -> None:
    telemetry.init_metrics()
    telemetry.record_governance_gate_status("enterprise_gap_closure", True)
    telemetry.set_enterprise_readiness_gap_status("observability_monitoring", "closed_by_code")
    telemetry.set_workflow_status("mining_operations", "healthy", True)
    telemetry.record_audit_event("security.auth_boundary", "allowed", request_id="req-test")

    metrics = telemetry.get_prometheus_metrics().decode("utf-8")

    assert "hyba_governance_gate_status" in metrics
    assert "enterprise_gap_closure" in metrics
    assert "hyba_enterprise_readiness_gap_status" in metrics
    assert "observability_monitoring" in metrics
    assert "hyba_workflow_status" in metrics
    assert "mining_operations" in metrics
    assert "hyba_audit_events_total" in metrics


def test_telemetry_middleware_propagates_request_correlation_and_trace_headers() -> None:
    request = _fake_request(
        {
            "x-request-id": "req-123",
            "x-correlation-id": "corr-456",
            "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-00",
        }
    )

    async def call_next(_request):
        return Response(status_code=204)

    response = asyncio.run(telemetry.telemetry_middleware(request, call_next))

    assert response.headers["x-request-id"] == "req-123"
    assert response.headers["x-correlation-id"] == "corr-456"
    assert response.headers["traceparent"].startswith("00-")
    assert telemetry.get_metrics()["last_request"]["correlation_id"] == "corr-456"


def test_enterprise_api_posture_headers_include_security_and_correlation() -> None:
    config = EnterpriseAPIConfig(
        environment="production",
        request_limit_per_minute=10,
        max_body_bytes=1024,
        hsts_enabled=True,
        rate_limit_enabled=True,
        csp_enabled=True,
        sanitize_production_errors=True,
    )
    response = Response()

    apply_enterprise_security_headers(response, "req-a", config, "corr-b")

    assert response.headers["X-Request-ID"] == "req-a"
    assert response.headers["X-Correlation-ID"] == "corr-b"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Strict-Transport-Security"].startswith("max-age=")
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]


def test_enterprise_error_payload_is_standardized() -> None:
    payload = enterprise_error_payload(
        code="rate_limit_exceeded",
        message="Request rate limit exceeded.",
        request_id="req-x",
        status_code=429,
    )

    assert payload == {
        "success": False,
        "error": {
            "code": "rate_limit_exceeded",
            "message": "Request rate limit exceeded.",
            "status_code": 429,
            "request_id": "req-x",
        },
    }


def test_in_memory_rate_limiter_prunes_and_blocks_after_limit() -> None:
    limiter = InMemoryRateLimiter(limit_per_minute=2)

    assert limiter.allow("client-a", now=60.0) is True
    assert limiter.allow("client-a", now=60.1) is True
    assert limiter.allow("client-a", now=60.2) is False
    assert limiter.allow("client-a", now=120.0) is True
