from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from hyba_genesis_api.core.api_posture import (
    EnterpriseAPIConfig,
    InMemoryRateLimiter,
    install_enterprise_api_posture,
)


def _config(**overrides):
    base = {
        "environment": "production",
        "request_limit_per_minute": 100,
        "max_body_bytes": 1024,
        "hsts_enabled": True,
        "rate_limit_enabled": True,
    }
    base.update(overrides)
    return EnterpriseAPIConfig(**base)


def test_enterprise_posture_adds_security_and_trace_headers():
    app = FastAPI()
    install_enterprise_api_posture(app, _config())

    @app.get("/ok")
    async def ok():
        return {"ok": True}

    response = TestClient(app).get("/ok", headers={"x-request-id": "req-enterprise-1"})

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "req-enterprise-1"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["permissions-policy"] == "camera=(), microphone=(), geolocation=()"
    assert response.headers["strict-transport-security"] == "max-age=31536000; includeSubDomains"


def test_standard_http_error_envelope_is_returned():
    app = FastAPI()
    install_enterprise_api_posture(app, _config())

    @app.get("/forbidden")
    async def forbidden():
        raise HTTPException(status_code=403, detail={"error": "forbidden", "message": "No."})

    response = TestClient(app).get("/forbidden", headers={"x-request-id": "req-denied"})

    assert response.status_code == 403
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "forbidden"
    assert payload["error"]["message"] == "No."
    assert payload["error"]["request_id"] == "req-denied"


def test_request_body_size_guard_fails_closed():
    app = FastAPI()
    install_enterprise_api_posture(app, _config(max_body_bytes=4))

    @app.post("/payload")
    async def payload():
        return {"ok": True}

    response = TestClient(app).post("/payload", content="12345", headers={"x-request-id": "req-large"})

    assert response.status_code == 413
    body = response.json()
    assert body["error"]["code"] == "request_body_too_large"
    assert body["error"]["request_id"] == "req-large"


def test_rate_limiter_blocks_after_configured_limit():
    app = FastAPI()
    install_enterprise_api_posture(app, _config(request_limit_per_minute=1))

    @app.get("/limited")
    async def limited():
        return {"ok": True}

    client = TestClient(app)
    first = client.get("/limited", headers={"x-request-id": "req-1"})
    second = client.get("/limited", headers={"x-request-id": "req-2"})

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.headers["retry-after"] == "60"
    assert second.json()["error"]["code"] == "rate_limit_exceeded"


def test_in_memory_rate_limiter_is_deterministic_by_minute_window():
    limiter = InMemoryRateLimiter(limit_per_minute=2)

    assert limiter.allow("client-a", now=60.0) is True
    assert limiter.allow("client-a", now=61.0) is True
    assert limiter.allow("client-a", now=62.0) is False
    assert limiter.allow("client-a", now=120.0) is True
