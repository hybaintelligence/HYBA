from __future__ import annotations

import importlib
import os
from pathlib import Path

import pytest

fastapi = pytest.importorskip("fastapi", reason="FastAPI backend dependencies are not installed")
from fastapi.testclient import TestClient


def _client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("HYBA_CUSTOMER_PORTAL_STORE", str(tmp_path / "portal.json"))
    monkeypatch.delenv("HYBA_PORTAL_DEMO_FIXTURES", raising=False)
    import hyba_genesis_api.api.customer_portal as customer_portal

    customer_portal = importlib.reload(customer_portal)
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(customer_portal.router)
    return TestClient(app)


def test_customer_portal_empty_tenant_is_evidence_first(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client(tmp_path, monkeypatch)

    response = client.get("/api/customer/acme/dashboard")

    assert response.status_code == 200
    payload = response.json()
    assert payload["instances"] == []
    assert payload["monthly_usage"]["compute_units"] == 0
    assert payload["billing_summary"]["current_month_usd"] == 0
    assert payload["data_provenance"]["demo_fixtures_enabled"] is False


def test_api_key_lifecycle_persists_hmac_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client(tmp_path, monkeypatch)

    create_response = client.post(
        "/api/customer/acme/api-keys",
        json={"label": "production rotation", "rotation_days": 30},
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["api_key"].startswith("hyba_live_")
    assert created["key_hash"] != created["api_key"]
    dashboard = client.get("/api/customer/acme/dashboard").json()
    assert dashboard["api_keys"][0]["label"] == "production rotation"
    assert "api_key" not in dashboard["api_keys"][0]

    revoke_response = client.delete(f"/api/customer/acme/api-keys/{created['key_id']}")

    assert revoke_response.status_code == 200
    assert client.get("/api/customer/acme/dashboard").json()["api_keys"] == []


def test_payment_method_requires_tokenized_last4(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client(tmp_path, monkeypatch)

    invalid = client.post(
        "/api/customer/acme/payment-methods",
        json={"provider": "stripe", "token": "tok_enterprise", "last4": "12ab", "card_type": "visa"},
    )
    valid = client.post(
        "/api/customer/acme/payment-methods",
        json={"provider": "stripe", "token": "tok_enterprise", "last4": "4242", "card_type": "visa"},
    )

    assert invalid.status_code == 422
    assert valid.status_code == 201
    assert valid.json()["last4"] == "4242"
    assert "token" not in valid.json()
