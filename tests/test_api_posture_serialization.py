from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

fastapi = pytest.importorskip(
    "fastapi", reason="FastAPI backend dependencies are not installed"
)
from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from hyba_genesis_api.core.api_posture import (  # noqa: E402
    EnterpriseAPIConfig,
    install_enterprise_api_posture,
)


class Payload(BaseModel):
    value: int = Field(gt=0)


def _client() -> TestClient:
    app = FastAPI()
    install_enterprise_api_posture(
        app,
        EnterpriseAPIConfig(
            environment="test",
            request_limit_per_minute=100,
            max_body_bytes=1024,
            hsts_enabled=False,
            rate_limit_enabled=False,
            csp_enabled=False,
            sanitize_production_errors=False,
        ),
    )

    @app.post("/validate")
    async def validate(payload: Payload) -> dict[str, int]:
        return {"value": payload.value}

    @app.get("/http-error")
    async def http_error() -> None:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "pool_profile_validation_failed",
                "message": ValueError("unsupported pool id"),
            },
        )

    return TestClient(app)


def test_request_validation_error_is_json_serializable() -> None:
    response = _client().post("/validate", json={"value": 0})

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert isinstance(body["details"], list)
    assert body["details"][0]["ctx"]
    assert all(
        isinstance(value, str) for value in body["details"][0].get("ctx", {}).values()
    )


def test_http_exception_detail_with_value_error_is_json_serializable() -> None:
    response = _client().get("/http-error")

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "pool_profile_validation_failed"
    assert "unsupported pool id" in body["error"]["message"]
    assert response.headers["X-Request-ID"]
