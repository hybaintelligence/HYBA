import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from hyba_genesis_api.core.api_posture import EnterpriseAPIConfig, install_enterprise_api_posture
from hyba_genesis_api.main import validate_required_secrets


def test_security_headers_present():
    app = FastAPI()
    install_enterprise_api_posture(app, EnterpriseAPIConfig(
        environment="production", request_limit_per_minute=100, max_body_bytes=1024,
        hsts_enabled=True, rate_limit_enabled=False, csp_enabled=True,
        sanitize_production_errors=True,
    ))

    @app.get("/ping")
    def ping():
        return {"ok": True}

    response = TestClient(app).get("/ping")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Strict-Transport-Security"].startswith("max-age=31536000")
    assert "Content-Security-Policy" in response.headers
    assert "X-Request-ID" in response.headers


def test_startup_secret_guard_rejects_missing_production_secrets(monkeypatch):
    monkeypatch.setenv("HYBA_ENV", "production")
    monkeypatch.delenv("HYBA_API_KEY_SECRET", raising=False)
    monkeypatch.delenv("JWT_SECRET", raising=False)
    with pytest.raises(RuntimeError):
        validate_required_secrets()


def test_startup_secret_guard_rejects_placeholder_secrets(monkeypatch):
    monkeypatch.setenv("HYBA_ENV", "production")
    monkeypatch.setenv("HYBA_API_KEY_SECRET", "change-me")
    monkeypatch.setenv("JWT_SECRET", "your-secret-here")
    with pytest.raises(RuntimeError):
        validate_required_secrets()
