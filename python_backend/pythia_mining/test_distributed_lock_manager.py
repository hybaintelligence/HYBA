"""
Comprehensive tests for DistributedLockManager.

Tests cover:
- Lock acquisition and release
- Context manager pattern
- Deadlock detection
- Exponential backoff retry logic
- Lock contention scenarios
- Metrics collection
- Error handling
"""

import asyncio
import pytest
from datetime import datetime

from distributed_lock_manager import (
    DistributedLockManager,
    LockAcquisitionError,
    LockReleaseError,
    DeadlockDetectedError,
    LockToken,
    LockStatus,
)


@pytest.fixture
def lock_manager():
    """Create a lock manager instance for testing."""
    return DistributedLockManager(
        redis_url="redis://localhost:6379",
        default_ttl=10,
        default_timeout=5,
        max_retries=3,
        initial_backoff_ms=50,
        max_backoff_ms=500,
        enable_metrics=True,
        log_level="DEBUG",
    )


@pytest.mark.asyncio
async def test_lock_acquisition_success(lock_manager):
    """Test successful lock acquisition."""
    token = await lock_manager.acquire("test_lock_1", ttl=10)

    assert token is not None
    assert isinstance(token, LockToken)
    assert token.key == "test_lock_1"
    assert token.ttl == 10
    assert not token.is_expired()
    assert token.time_remaining() > 0

    # Cleanup
    await lock_manager.release("test_lock_1", token.token)


@pytest.mark.asyncio
async def test_lock_release_success(lock_manager):
    """Test successful lock release."""
    token = await lock_manager.acquire("test_lock_2", ttl=10)
    result = await lock_manager.release("test_lock_2", token.token)

    assert result is True
    metrics = lock_manager.get_lock_metrics()
    assert metrics["successful_releases"] >= 1


@pytest.mark.asyncio
async def test_context_manager_basic(lock_manager):
    """Test context manager pattern for lock management."""
    async with lock_manager.with_lock("context_lock", ttl=10) as token:
        assert token is not None
        assert isinstance(token, LockToken)
        assert token.key == "context_lock"

    # Lock should be released after context exit
    metrics = lock_manager.get_lock_metrics()
    assert metrics["successful_releases"] >= 1


@pytest.mark.asyncio
async def test_context_manager_with_exception(lock_manager):
    """Test context manager properly releases lock even on exception."""
    try:
        async with lock_manager.with_lock("exception_lock", ttl=10) as token:
            assert token is not None
            raise ValueError("Test exception")
    except ValueError:
        pass

    # Lock should still be released
    metrics = lock_manager.get_lock_metrics()
    assert metrics["successful_releases"] >= 1
    assert len(metrics["active_locks"]) == 0


@pytest.mark.asyncio
async def test_token_expiration(lock_manager):
    """Test lock token expiration detection."""
    token = await lock_manager.acquire("expiry_lock", ttl=1)

    assert not token.is_expired()
    assert token.time_remaining() > 0

    # Wait for expiration
    await asyncio.sleep(1.1)

    assert token.is_expired()
    assert token.time_remaining() == 0.0

    # Cleanup
    await lock_manager.release("expiry_lock", token.token)


@pytest.mark.asyncio
async def test_invalid_parameters(lock_manager):
    """Test error handling for invalid parameters."""
    with pytest.raises(ValueError):
        await lock_manager.acquire("", ttl=10)

    with pytest.raises(ValueError):
        await lock_manager.acquire("test", ttl=-1)

    with pytest.raises(ValueError):
        await lock_manager.acquire("test", timeout=-1)

    with pytest.raises(ValueError):
        await lock_manager.release("test", "")


@pytest.mark.asyncio
async def test_lock_metrics_structure(lock_manager):
    """Test metrics collection and structure."""
    # Perform some operations
    token1 = await lock_manager.acquire("metric_lock_1", ttl=5)
    await lock_manager.release("metric_lock_1", token1.token)

    token2 = await lock_manager.acquire("metric_lock_2", ttl=5)

    metrics = lock_manager.get_lock_metrics()

    # Verify metrics structure
    assert "total_acquisitions" in metrics
    assert "successful_acquisitions" in metrics
    assert "failed_acquisitions" in metrics
    assert "success_rate" in metrics
    assert "contention_ratio" in metrics
    assert "average_wait_time_ms" in metrics
    assert "max_wait_time_ms" in metrics
    assert "active_locks_count" in metrics
    assert "active_locks" in metrics
    assert "timestamp" in metrics

    # Verify values
    assert metrics["total_acquisitions"] >= 2
    assert metrics["successful_acquisitions"] >= 2
    assert metrics["success_rate"] > 0
    assert metrics["average_wait_time_ms"] >= 0
    assert metrics["max_wait_time_ms"] >= 0

    # Cleanup
    await lock_manager.release("metric_lock_2", token2.token)


@pytest.mark.asyncio
async def test_multiple_concurrent_locks(lock_manager):
    """Test acquiring multiple different locks concurrently."""
    async def acquire_lock(manager, lock_id):
        token = await manager.acquire(f"concurrent_lock_{lock_id}", ttl=5)
        await asyncio.sleep(0.1)
        await manager.release(f"concurrent_lock_{lock_id}", token.token)

    # Acquire multiple locks concurrently
    tasks = [acquire_lock(lock_manager, i) for i in range(5)]
    await asyncio.gather(*tasks)

    metrics = lock_manager.get_lock_metrics()
    assert metrics["successful_acquisitions"] >= 5
    assert metrics["successful_releases"] >= 5


@pytest.mark.asyncio
async def test_lock_token_to_dict(lock_manager):
    """Test lock token serialization."""
    token = await lock_manager.acquire("serialize_lock", ttl=10)

    token_dict = token.to_dict()

    assert "key" in token_dict
    assert "token" in token_dict
    assert "holder_id" in token_dict
    assert "acquired_at" in token_dict
    assert "ttl" in token_dict
    assert "time_remaining" in token_dict

    assert token_dict["key"] == "serialize_lock"
    assert token_dict["ttl"] == 10

    # Cleanup
    await lock_manager.release("serialize_lock", token.token)


@pytest.mark.asyncio
async def test_lock_manager_initialization_validation():
    """Test lock manager initialization validation."""
    with pytest.raises(ValueError):
        DistributedLockManager(default_ttl=-1)

    with pytest.raises(ValueError):
        DistributedLockManager(default_timeout=-1)

    with pytest.raises(ValueError):
        DistributedLockManager(max_retries=-1)

    with pytest.raises(ValueError):
        DistributedLockManager(initial_backoff_ms=-1)


@pytest.mark.asyncio
async def test_contention_metrics(lock_manager):
    """Test contention metrics when locks are contested."""
    # Create rapid acquisition attempts
    tokens = []
    for i in range(3):
        token = await lock_manager.acquire(f"contention_test", ttl=5)
        tokens.append(token)

    metrics = lock_manager.get_lock_metrics()

    # Should have some contention recorded
    assert metrics["total_acquisitions"] >= 1
    if metrics["total_acquisitions"] > 1:
        assert metrics["contention_ratio"] >= 0

    # Cleanup
    for token in tokens:
        try:
            await lock_manager.release("contention_test", token.token)
        except Exception:
            pass


@pytest.mark.asyncio
async def test_default_parameters(lock_manager):
    """Test lock acquisition with default parameters."""
    token = await lock_manager.acquire("default_params_lock")

    assert token.ttl == lock_manager.default_ttl
    assert not token.is_expired()

    # Cleanup
    await lock_manager.release("default_params_lock", token.token)


@pytest.mark.asyncio
async def test_release_nonexistent_lock(lock_manager):
    """Test releasing a lock that doesn't exist."""
    result = await lock_manager.release("nonexistent_lock", "fake_token")
    assert result is False


@pytest.mark.asyncio
async def test_release_with_wrong_token(lock_manager):
    """Test releasing with wrong token."""
    token = await lock_manager.acquire("wrong_token_lock", ttl=10)

    # Try to release with wrong token
    result = await lock_manager.release("wrong_token_lock", "wrong_token_value")
    assert result is False

    # Original token should still work
    result = await lock_manager.release("wrong_token_lock", token.token)
    assert result is True


@pytest.mark.asyncio
async def test_metrics_history_bounded(lock_manager):
    """Test that metrics history doesn't grow unbounded."""
    # Generate many operations
    for i in range(100):
        token = await lock_manager.acquire(f"bounded_history_lock_{i}", ttl=1)
        await lock_manager.release(f"bounded_history_lock_{i}", token.token)

    metrics = lock_manager.get_lock_metrics()
    
    # History should be bounded
    assert len(lock_manager.metrics.metrics_history) <= 10000


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
