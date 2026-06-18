"""Shared helpers for backend API surface tests."""

from __future__ import annotations

import os

os.environ.setdefault("JWT_SECRET", "backend-api-test-secret")
os.environ.setdefault("HYBA_ENV", "test")
os.environ.setdefault("NODE_ENV", "test")

import pytest

fastapi = pytest.importorskip("fastapi", reason="FastAPI backend dependencies are not installed")
from fastapi.testclient import TestClient

from hyba_genesis_api.auth.jwt_handler import get_jwt_manager
from hyba_genesis_api.main import app


def make_client() -> TestClient:
    return TestClient(app)


def bearer_headers(*roles: str) -> dict[str, str]:
    selected_roles = list(roles) or ["ceo", "mining:read", "mining:operate"]
    token = get_jwt_manager().create_access_token(
        user_id="backend-api-test-user",
        username="backend-api-test-user",
        roles=selected_roles,
    )
    return {
        "Authorization": f"Bearer {token}",
        "X-Request-ID": "backend-api-test-request",
    }
