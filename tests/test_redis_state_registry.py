"""
Test suite for Redis Quantum Substrate Registry

Validates distributed state management with mocked Redis client to ensure
test suite remains dependency-free while verifying production behavior.
"""

import json
import pytest
from unittest.mock import MagicMock, patch
from pythia_mining.redis_state_registry import (
    RedisQuantumSubstrateRegistry,
    get_redis_registry,
)


@pytest.fixture
def mock_redis_client():
    """Create mocked Redis client with common operation responses."""
    mock_client = MagicMock()
    mock_client.ping.return_value = True
    mock_client.set.return_value = True
    mock_client.setex.return_value = True
    mock_client.get.return_value = None
    mock_client.hgetall.return_value = {}
    mock_client.delete.return_value = 1
    mock_client.pipeline.return_value = mock_client
    mock_client.execute.return_value = [True, 1, 1]
    return mock_client


@pytest.fixture
def registry_with_mock_redis(mock_redis_client):
    """Create registry instance with mocked Redis client."""
    with patch("pythia_mining.redis_state_registry.RedisQuantumSubstrateRegistry._initialize_client"):
        registry = RedisQuantumSubstrateRegistry()
        registry._client = mock_redis_client
        registry._available = True
        yield registry


def test_redis_initialization_success(mock_redis_client):
    """Test successful Redis initialization with connection verification."""
    with patch("pythia_mining.redis_state_registry.RedisQuantumSubstrateRegistry._initialize_client"):
        registry = RedisQuantumSubstrateRegistry(host="localhost", port=6379)
        registry._client = mock_redis_client
        registry._available = True

        assert registry.available is True
        assert registry.host == "localhost"
        assert registry.port == 6379


def test_redis_initialization_failure():
    """Test graceful fallback when Redis is unavailable."""
    with patch("pythia_mining.redis_state_registry.RedisQuantumSubstrateRegistry._initialize_client") as mock_init:
        mock_init.side_effect = lambda: None
        registry = RedisQuantumSubstrateRegistry()
        registry._available = False
        registry._client = None

        assert registry.available is False
        assert registry._client is None


def test_serialize_instance_topology_success(registry_with_mock_redis, mock_redis_client):
    """Test successful instance topology serialization to Redis."""
    topology = {
        "instance_id": "qaas-test123",
        "code_distance": 7,
        "logical_qubits": 32,
        "owner": "customer-abc",
    }

    result = registry_with_mock_redis.serialize_instance_topology(
        "qaas-test123", topology
    )

    assert result is True
    mock_redis_client.setex.assert_called_once()
    call_args = mock_redis_client.setex.call_args
    assert call_args[0][0] == "quantum:instance:qaas-test123:metadata"
    assert call_args[0][1] == 86400  # 24h TTL
    serialized_data = json.loads(call_args[0][2])
    assert serialized_data["code_distance"] == 7


def test_serialize_instance_topology_redis_unavailable():
    """Test serialization returns False when Redis unavailable."""
    registry = RedisQuantumSubstrateRegistry()
    registry._available = False

    result = registry.serialize_instance_topology("test", {})

    assert result is False


def test_get_instance_topology_success(registry_with_mock_redis, mock_redis_client):
    """Test successful instance topology retrieval from Redis."""
    stored_topology = {
        "instance_id": "qaas-test123",
        "code_distance": 7,
        "logical_qubits": 32,
    }
    mock_redis_client.get.return_value = json.dumps(stored_topology)

    result = registry_with_mock_redis.get_instance_topology("qaas-test123")

    assert result is not None
    assert result["code_distance"] == 7
    assert result["logical_qubits"] == 32
    mock_redis_client.get.assert_called_once_with(
        "quantum:instance:qaas-test123:metadata"
    )


def test_get_instance_topology_not_found(registry_with_mock_redis, mock_redis_client):
    """Test topology retrieval returns None when instance not found."""
    mock_redis_client.get.return_value = None

    result = registry_with_mock_redis.get_instance_topology("nonexistent")

    assert result is None


def test_get_instance_topology_redis_unavailable():
    """Test topology retrieval returns None when Redis unavailable."""
    registry = RedisQuantumSubstrateRegistry()
    registry._available = False

    result = registry.get_instance_topology("test")

    assert result is None


def test_acquire_register_lock_success(registry_with_mock_redis, mock_redis_client):
    """Test successful distributed lock acquisition."""
    mock_redis_client.set.return_value = True

    result = registry_with_mock_redis.acquire_register_lock(
        "qaas-test123", "customer-abc"
    )

    assert result is True
    mock_redis_client.set.assert_called_once()
    call_args = mock_redis_client.set.call_args
    assert call_args[0][0] == "quantum:lock:register:qaas-test123"
    assert call_args[0][1] == "customer-abc"
    assert call_args[1]["px"] == 10000  # 10s lease
    assert call_args[1]["nx"] is True


def test_acquire_register_lock_already_held(registry_with_mock_redis, mock_redis_client):
    """Test lock acquisition fails when already held by another tenant."""
    mock_redis_client.set.return_value = False

    result = registry_with_mock_redis.acquire_register_lock(
        "qaas-test123", "customer-xyz"
    )

    assert result is False


def test_acquire_register_lock_redis_unavailable():
    """Test lock acquisition always succeeds in in-memory mode."""
    registry = RedisQuantumSubstrateRegistry()
    registry._available = False

    result = registry.acquire_register_lock("test", "customer")

    assert result is True


def test_release_register_lock_success(registry_with_mock_redis, mock_redis_client):
    """Test successful distributed lock release with Lua script."""
    mock_script = MagicMock()
    mock_script.return_value = 1  # 1 = lock deleted
    mock_redis_client.register_script.return_value = mock_script

    result = registry_with_mock_redis.release_register_lock(
        "qaas-test123", "customer-abc"
    )

    assert result is True
    mock_redis_client.register_script.assert_called_once()
    mock_script.assert_called_once()
    call_args = mock_script.call_args
    assert call_args[1]["keys"] == ["quantum:lock:register:qaas-test123"]
    assert call_args[1]["args"] == ["customer-abc"]


def test_release_register_lock_not_owner(registry_with_mock_redis, mock_redis_client):
    """Test lock release fails when tenant doesn't own the lock."""
    mock_script = MagicMock()
    mock_script.return_value = 0  # 0 = lock not deleted (not owner)
    mock_redis_client.register_script.return_value = mock_script

    result = registry_with_mock_redis.release_register_lock(
        "qaas-test123", "customer-xyz"
    )

    assert result is False


def test_record_resource_consumption_success(registry_with_mock_redis, mock_redis_client):
    """Test resource consumption recording with compute unit calculation."""
    metrics = {
        "defect_count": 5,
        "pairing_weight": 2.5,
        "circuit_depth": 10,
    }

    result = registry_with_mock_redis.record_resource_consumption(
        "qaas-test123", "customer-abc", metrics
    )

    assert result["status"] == "METERED_SUCCESS"
    assert result["tenant_id"] == "customer-abc"
    # Expected: ((5 * 2.5) + 1.0) * 10 = 135.0
    assert result["compute_units_drawn"] == 135.0

    mock_redis_client.pipeline.assert_called_once()
    mock_redis_client.hincrbyfloat.assert_called()
    mock_redis_client.hincrby.assert_called()
    mock_redis_client.execute.assert_called_once()


def test_record_resource_consumption_redis_unavailable():
    """Test resource metering returns in-memory status when Redis unavailable."""
    registry = RedisQuantumSubstrateRegistry()
    registry._available = False

    metrics = {"defect_count": 3, "pairing_weight": 1.5, "circuit_depth": 5}
    result = registry.record_resource_consumption("test", "customer", metrics)

    assert result["status"] == "METERED_IN_MEMORY"
    assert result["compute_units_drawn"] == 27.5  # ((3 * 1.5) + 1.0) * 5


def test_get_tenant_usage_success(registry_with_mock_redis, mock_redis_client):
    """Test tenant usage retrieval from Redis."""
    mock_redis_client.hgetall.return_value = {
        "total_compute_units": "1250.5",
        "total_execution_cycles": "42",
    }

    result = registry_with_mock_redis.get_tenant_usage("customer-abc")

    assert result["total_compute_units"] == 1250.5
    assert result["total_execution_cycles"] == 42
    mock_redis_client.hgetall.assert_called_once_with("tenant:customer-abc:metering")


def test_get_tenant_usage_redis_unavailable():
    """Test tenant usage returns zeros when Redis unavailable."""
    registry = RedisQuantumSubstrateRegistry()
    registry._available = False

    result = registry.get_tenant_usage("customer")

    assert result["total_compute_units"] == 0.0
    assert result["total_execution_cycles"] == 0


def test_delete_instance_success(registry_with_mock_redis, mock_redis_client):
    """Test instance deletion removes all associated keys."""
    result = registry_with_mock_redis.delete_instance("qaas-test123")

    assert result is True
    mock_redis_client.pipeline.assert_called_once()
    # Verify pipeline deletes all three keys
    assert mock_redis_client.delete.call_count == 3
    mock_redis_client.execute.assert_called_once()


def test_delete_instance_redis_unavailable():
    """Test instance deletion always succeeds in in-memory mode."""
    registry = RedisQuantumSubstrateRegistry()
    registry._available = False

    result = registry.delete_instance("test")

    assert result is True


def test_get_redis_registry_singleton():
    """Test global registry returns singleton instance."""
    registry1 = get_redis_registry()
    registry2 = get_redis_registry()

    assert registry1 is registry2


def test_compute_unit_formula_edge_cases(registry_with_mock_redis):
    """Test compute unit calculation with edge cases."""
    # Zero defects
    result1 = registry_with_mock_redis.record_resource_consumption(
        "test", "customer", {"defect_count": 0, "pairing_weight": 0, "circuit_depth": 5}
    )
    assert result1["compute_units_drawn"] == 5.0  # (0 + 1.0) * 5

    # Single defect, unit weight
    result2 = registry_with_mock_redis.record_resource_consumption(
        "test", "customer", {"defect_count": 1, "pairing_weight": 1.0, "circuit_depth": 1}
    )
    assert result2["compute_units_drawn"] == 2.0  # ((1 * 1.0) + 1.0) * 1

    # Missing metrics default to minimal cost
    result3 = registry_with_mock_redis.record_resource_consumption(
        "test", "customer", {}
    )
    assert result3["compute_units_drawn"] == 1.0  # (0 + 1.0) * 1


def test_lock_lease_expiration_configured():
    """Test lock lease duration is configured correctly."""
    registry = RedisQuantumSubstrateRegistry()
    assert registry.lock_lease_ms == 10000  # 10 seconds


def test_topology_ttl_configured(registry_with_mock_redis, mock_redis_client):
    """Test instance topology has 24h TTL configured."""
    registry_with_mock_redis.serialize_instance_topology("test", {"data": "value"})

    call_args = mock_redis_client.setex.call_args
    assert call_args[0][1] == 86400  # 24 hours in seconds
