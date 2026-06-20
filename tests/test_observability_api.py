"""
Test suite for Admin Observability Router

Validates Redis-backed telemetry aggregation and monitoring endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from hyba_genesis_api.main import app

client = TestClient(app)


@pytest.fixture
def admin_token():
    """Get admin JWT token for authenticated requests."""
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin"},
    )
    return response.json()["access_token"]


@pytest.fixture
def mock_redis_registry():
    """Create mocked Redis registry for observability tests."""
    mock_registry = MagicMock()
    mock_registry.available = True
    mock_registry.host = "localhost"
    mock_registry.port = 6379
    mock_registry.get_tenant_usage.return_value = {
        "total_compute_units": 1250.5,
        "total_execution_cycles": 42,
    }
    mock_registry.get_instance_topology.return_value = {
        "instance_id": "qaas-test123",
        "executions": 15,
        "updated_at": "2026-06-20T12:00:00Z",
    }
    mock_registry.delete_instance.return_value = True
    return mock_registry


def test_get_tenant_resource_usage_success(admin_token, mock_redis_registry):
    """Test tenant usage retrieval with Redis available."""
    with patch("hyba_genesis_api.api.observability.get_redis_registry", return_value=mock_redis_registry):
        response = client.get(
            "/api/admin/observability/tenants/customer-abc/usage",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["tenant_id"] == "customer-abc"
        assert data["total_compute_units"] == 1250.5
        assert data["total_execution_cycles"] == 42
        assert data["instances_count"] == 0


def test_get_tenant_resource_usage_redis_unavailable(admin_token):
    """Test tenant usage endpoint returns 503 when Redis unavailable."""
    mock_registry = MagicMock()
    mock_registry.available = False

    with patch("hyba_genesis_api.api.observability.get_redis_registry", return_value=mock_registry):
        response = client.get(
            "/api/admin/observability/tenants/customer-abc/usage",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 503
        assert "Redis telemetry backend unavailable" in response.json()["detail"]


def test_get_system_health_redis_available(admin_token, mock_redis_registry):
    """Test system health endpoint with Redis connected."""
    with patch("hyba_genesis_api.api.observability.get_redis_registry", return_value=mock_redis_registry):
        response = client.get(
            "/api/admin/observability/system/health",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["redis_available"] is True
        assert data["redis_host"] == "localhost"
        assert data["redis_port"] == 6379


def test_get_instance_telemetry_success(admin_token, mock_redis_registry):
    """Test instance telemetry retrieval with Redis backing."""
    with patch("hyba_genesis_api.api.observability.get_redis_registry", return_value=mock_redis_registry):
        response = client.get(
            "/api/admin/observability/instances/qaas-test123/telemetry",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["instance_id"] == "qaas-test123"
        assert data["total_execution_cycles"] == 15
        assert data["last_updated"] == "2026-06-20T12:00:00Z"
        assert data["redis_backed"] is True


def test_delete_instance_state_success(admin_token, mock_redis_registry):
    """Test instance state deletion from Redis."""
    with patch("hyba_genesis_api.api.observability.get_redis_registry", return_value=mock_registry):
        response = client.delete(
            "/api/admin/observability/instances/qaas-test123",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deleted"
        assert data["instance_id"] == "qaas-test123"
