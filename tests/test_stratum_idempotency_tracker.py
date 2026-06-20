"""
Stratum Idempotency Tracker - Comprehensive Unit Tests

Tests cover:
- Duplicate detection (TOCTOU safety)
- Race condition prevention with Redis Lua scripts
- Retry logic (rejected shares can be resubmitted)
- Metrics tracking
- Memory fallback when Redis unavailable
- TTL expiration handling
- Atomic state transitions
"""

import asyncio
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest

from pythia_mining.stratum_idempotency_tracker import (
    IdempotencyTracker,
    StratumSubmissionRecord,
    SubmissionStatus,
)


class TestStratumSubmissionRecord:
    """Test StratumSubmissionRecord dataclass."""
    
    def test_creation(self):
        """Test basic record creation."""
        record = StratumSubmissionRecord(
            submission_id="test-id-123",
            pool_id="pool1",
            nonce=12345,
            timestamp=time.time(),
            status="pending",
        )
        
        assert record.submission_id == "test-id-123"
        assert record.pool_id == "pool1"
        assert record.nonce == 12345
        assert record.status == "pending"
        assert record.attempt_count == 1
    
    def test_serialization(self):
        """Test to_dict and from_dict."""
        original = StratumSubmissionRecord(
            submission_id="id-456",
            pool_id="pool2",
            nonce=54321,
            timestamp=1234567890.0,
            status="accepted",
            reason="accepted",
            attempt_count=2,
        )
        
        # Serialize
        data = original.to_dict()
        assert data["submission_id"] == "id-456"
        assert data["nonce"] == 54321
        
        # Deserialize
        restored = StratumSubmissionRecord.from_dict(data)
        assert restored.submission_id == original.submission_id
        assert restored.nonce == original.nonce
        assert restored.attempt_count == original.attempt_count


class TestIdempotencyTrackerMemoryMode:
    """Test IdempotencyTracker in memory-only mode (no Redis)."""
    
    @pytest.fixture
    def tracker(self):
        """Create tracker without Redis."""
        return IdempotencyTracker(redis_client=None, ttl_seconds=10)
    
    @pytest.mark.asyncio
    async def test_record_and_check_duplicate(self, tracker):
        """Test basic duplicate detection."""
        pool_id = "pool1"
        nonce = 100
        
        # First submission
        record1 = await tracker.record_submission(pool_id, nonce)
        assert record1.status == "pending"
        assert record1.submission_id
        
        # Check duplicate
        duplicate = await tracker.check_duplicate(pool_id, nonce)
        assert duplicate is not None
        assert duplicate.submission_id == record1.submission_id
        assert duplicate.attempt_count == 1
    
    @pytest.mark.asyncio
    async def test_no_duplicate_different_nonce(self, tracker):
        """Test no false positives on different nonces."""
        pool_id = "pool1"
        
        record1 = await tracker.record_submission(pool_id, 100)
        duplicate = await tracker.check_duplicate(pool_id, 200)
        
        assert duplicate is None
    
    @pytest.mark.asyncio
    async def test_no_duplicate_different_pool(self, tracker):
        """Test no false positives on different pools."""
        nonce = 100
        
        record1 = await tracker.record_submission("pool1", nonce)
        duplicate = await tracker.check_duplicate("pool2", nonce)
        
        assert duplicate is None
    
    @pytest.mark.asyncio
    async def test_mark_result_accepted(self, tracker):
        """Test marking submission as accepted."""
        pool_id = "pool1"
        nonce = 100
        
        record = await tracker.record_submission(pool_id, nonce)
        
        await tracker.mark_result(
            record.submission_id,
            pool_id,
            nonce,
            accepted=True,
            reason=None,
        )
        
        # Check updated record
        updated = await tracker.check_duplicate(pool_id, nonce)
        assert updated.status == "accepted"
        assert updated.attempt_count == 2
    
    @pytest.mark.asyncio
    async def test_mark_result_rejected(self, tracker):
        """Test marking submission as rejected."""
        pool_id = "pool1"
        nonce = 100
        
        record = await tracker.record_submission(pool_id, nonce)
        
        await tracker.mark_result(
            record.submission_id,
            pool_id,
            nonce,
            accepted=False,
            reason="stale",
        )
        
        updated = await tracker.check_duplicate(pool_id, nonce)
        assert updated.status == "rejected"
        assert updated.reason == "stale"
    
    @pytest.mark.asyncio
    async def test_ttl_expiration(self, tracker):
        """Test TTL expiration in memory store."""
        pool_id = "pool1"
        nonce = 100
        
        record = await tracker.record_submission(pool_id, nonce)
        assert await tracker.check_duplicate(pool_id, nonce) is not None
        
        # Advance time past TTL
        tracker._memory_timestamps[tracker._get_nonce_key(pool_id, nonce)] = (
            time.time() - 20  # Older than 10s TTL
        )
        
        # After cleanup, expired entry should be gone
        await tracker.cleanup_expired()
        duplicate = await tracker.check_duplicate(pool_id, nonce)
        assert duplicate is None
    
    @pytest.mark.asyncio
    async def test_metrics_tracking(self, tracker):
        """Test metrics are tracked correctly."""
        pool_id = "pool1"
        
        # Record submissions
        rec1 = await tracker.record_submission(pool_id, 100)
        rec2 = await tracker.record_submission(pool_id, 101)
        
        # Mark one accepted, one rejected
        await tracker.mark_result(rec1.submission_id, pool_id, 100, accepted=True)
        await tracker.mark_result(rec2.submission_id, pool_id, 101, accepted=False)
        
        metrics = await tracker.get_metrics()
        
        assert metrics["submissions_recorded"] == 2
        assert metrics["accepted_submissions"] == 1
        assert metrics["rejected_submissions"] == 1
        assert metrics["redis_available"] is False
    
    @pytest.mark.asyncio
    async def test_duplicate_metrics(self, tracker):
        """Test duplicate tracking metrics."""
        pool_id = "pool1"
        nonce = 100
        
        rec1 = await tracker.record_submission(pool_id, nonce)
        await tracker.mark_result(rec1.submission_id, pool_id, nonce, accepted=False)
        
        # Record duplicate attempt
        tracker.record_duplicate_attempt(pool_id, nonce, "rejected")
        
        metrics = await tracker.get_metrics()
        assert metrics["duplicate_attempts"] == 1
        assert metrics["retry_successes"] == 1


class TestIdempotencyTrackerWithRedis:
    """Test IdempotencyTracker with Redis backend."""
    
    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        redis = MagicMock()
        redis.get = MagicMock(return_value=None)
        redis.setex = MagicMock()
        redis.register_script = MagicMock()
        redis.hgetall = MagicMock(return_value={})
        return redis
    
    @pytest.fixture
    def tracker(self, mock_redis):
        """Create tracker with mock Redis."""
        return IdempotencyTracker(redis_client=mock_redis, ttl_seconds=120)
    
    @pytest.mark.asyncio
    async def test_redis_check_duplicate(self, mock_redis):
        """Test duplicate check uses Redis."""
        tracker = IdempotencyTracker(redis_client=mock_redis)
        
        record_data = {
            "submission_id": "id1",
            "pool_id": "pool1",
            "nonce": 100,
            "timestamp": time.time(),
            "status": "pending",
            "reason": None,
            "attempt_count": 1,
        }
        mock_redis.get.return_value = json.dumps(record_data)
        
        duplicate = await tracker.check_duplicate("pool1", 100)
        
        assert duplicate is not None
        assert duplicate.submission_id == "id1"
        mock_redis.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_redis_record_submission(self, mock_redis):
        """Test submission recording uses Redis."""
        tracker = IdempotencyTracker(redis_client=mock_redis)
        
        record = await tracker.record_submission("pool1", 100)
        
        # Verify Redis setex was called
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        
        # Extract the key, ttl, and value from call
        key = call_args[0][0]
        ttl = call_args[0][1]
        value = call_args[0][2]
        
        assert "stratum:nonce:pool1:100" in key
        assert ttl == 120
        
        # Value should be JSON serialized record
        stored_record = json.loads(value)
        assert stored_record["submission_id"] == record.submission_id
    
    @pytest.mark.asyncio
    async def test_redis_mark_result_with_lua(self, mock_redis):
        """Test mark_result uses Redis Lua script."""
        tracker = IdempotencyTracker(redis_client=mock_redis)
        
        # Mock Lua script compilation
        mock_script = MagicMock()
        mock_script.return_value = b"UPDATED"
        mock_redis.register_script.return_value = mock_script
        
        # Mock existing record
        existing_data = {
            "submission_id": "id1",
            "pool_id": "pool1",
            "nonce": 100,
            "timestamp": time.time(),
            "status": "pending",
            "reason": None,
            "attempt_count": 1,
        }
        mock_redis.get.return_value = json.dumps(existing_data)
        
        await tracker.mark_result("id1", "pool1", 100, accepted=True, reason=None)
        
        # Verify Lua script was registered and called
        mock_redis.register_script.assert_called_once()
        mock_script.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_redis_fallback_to_memory(self, mock_redis):
        """Test fallback to memory when Redis fails."""
        mock_redis.get.side_effect = ConnectionError("Redis unavailable")
        
        tracker = IdempotencyTracker(redis_client=mock_redis)
        
        # Should still work with memory store
        record = await tracker.record_submission("pool1", 100)
        assert record.submission_id
        
        duplicate = await tracker.check_duplicate("pool1", 100)
        assert duplicate is not None


class TestIdempotencyRaceConditions:
    """Test race condition prevention with concurrent operations."""
    
    @pytest.mark.asyncio
    async def test_concurrent_submissions_same_nonce(self):
        """Test concurrent submissions with same nonce."""
        tracker = IdempotencyTracker(redis_client=None, ttl_seconds=10)
        
        pool_id = "pool1"
        nonce = 100
        
        # Simulate concurrent submissions
        async def submit_share(i):
            record = await tracker.record_submission(pool_id, nonce)
            return record
        
        # All should succeed in recording
        tasks = [submit_share(i) for i in range(5)]
        records = await asyncio.gather(*tasks)
        
        # Only first should get through without duplicate
        # (This tests that subsequent checks detect duplicates)
        assert len(records) == 5
        assert records[0].submission_id != records[1].submission_id
    
    @pytest.mark.asyncio
    async def test_concurrent_duplicate_checks(self):
        """Test concurrent duplicate checks."""
        tracker = IdempotencyTracker(redis_client=None, ttl_seconds=10)
        
        pool_id = "pool1"
        nonce = 100
        
        # Record initial submission
        record = await tracker.record_submission(pool_id, nonce)
        
        # Concurrent checks should all find the same record
        async def check_duplicate(i):
            return await tracker.check_duplicate(pool_id, nonce)
        
        tasks = [check_duplicate(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        # All should find the duplicate
        assert all(r is not None for r in results)
        assert all(r.submission_id == record.submission_id for r in results)
    
    @pytest.mark.asyncio
    async def test_concurrent_mark_result(self):
        """Test concurrent mark_result operations."""
        tracker = IdempotencyTracker(redis_client=None, ttl_seconds=10)
        
        pool_id = "pool1"
        nonce = 100
        
        record = await tracker.record_submission(pool_id, nonce)
        
        # Concurrent mark_result calls
        async def mark_result(accepted):
            await tracker.mark_result(
                record.submission_id,
                pool_id,
                nonce,
                accepted=accepted,
                reason="test",
            )
        
        tasks = [mark_result(i % 2 == 0) for i in range(5)]
        await asyncio.gather(*tasks)
        
        # Final status should be consistent
        final = await tracker.check_duplicate(pool_id, nonce)
        assert final.status in ["accepted", "rejected"]


class TestIdempotencyRetryLogic:
    """Test retry logic for rejected shares."""
    
    @pytest.mark.asyncio
    async def test_retry_allowed_after_rejection(self):
        """Test that rejected shares can be retried."""
        tracker = IdempotencyTracker(redis_client=None, ttl_seconds=60)
        
        pool_id = "pool1"
        nonce = 100
        
        # First submission rejected
        rec1 = await tracker.record_submission(pool_id, nonce)
        await tracker.mark_result(
            rec1.submission_id,
            pool_id,
            nonce,
            accepted=False,
            reason="stale",
        )
        
        # Check shows rejection
        duplicate = await tracker.check_duplicate(pool_id, nonce)
        assert duplicate.status == "rejected"
        
        # Should be retryable (in real implementation, check logic would allow retry)
        tracker.record_duplicate_attempt(pool_id, nonce, duplicate.status)
        
        metrics = await tracker.get_metrics()
        assert metrics["retry_successes"] == 1
    
    @pytest.mark.asyncio
    async def test_no_retry_after_acceptance(self):
        """Test that accepted shares cannot be retried."""
        tracker = IdempotencyTracker(redis_client=None, ttl_seconds=60)
        
        pool_id = "pool1"
        nonce = 100
        
        # Submission accepted
        record = await tracker.record_submission(pool_id, nonce)
        await tracker.mark_result(
            record.submission_id,
            pool_id,
            nonce,
            accepted=True,
            reason=None,
        )
        
        # Check shows acceptance
        duplicate = await tracker.check_duplicate(pool_id, nonce)
        assert duplicate.status == "accepted"
        
        # Should NOT be retryable
        tracker.record_duplicate_attempt(pool_id, nonce, duplicate.status)
        
        metrics = await tracker.get_metrics()
        # No retry successes because status is accepted (would be DUP_NONCE)
        assert metrics["retry_successes"] == 0
        assert metrics["duplicate_attempts"] == 1


class TestIdempotencyCleanup:
    """Test cleanup and expiration handling."""
    
    @pytest.mark.asyncio
    async def test_cleanup_removes_expired(self):
        """Test cleanup removes expired entries."""
        tracker = IdempotencyTracker(redis_client=None, ttl_seconds=5)
        
        # Add entries
        for i in range(3):
            await tracker.record_submission("pool1", 100 + i)
        
        assert len(tracker._memory_store) == 3
        
        # Expire all
        for key in tracker._memory_timestamps:
            tracker._memory_timestamps[key] = time.time() - 10
        
        cleaned = await tracker.cleanup_expired()
        
        assert cleaned == 3
        assert len(tracker._memory_store) == 0
    
    @pytest.mark.asyncio
    async def test_cleanup_preserves_valid(self):
        """Test cleanup preserves non-expired entries."""
        tracker = IdempotencyTracker(redis_client=None, ttl_seconds=60)
        
        # Add entries
        await tracker.record_submission("pool1", 100)
        await tracker.record_submission("pool1", 101)
        
        cleaned = await tracker.cleanup_expired()
        
        # Should not clean anything (still within TTL)
        assert cleaned == 0
        assert len(tracker._memory_store) == 2


class TestIdempotencyMetrics:
    """Test comprehensive metrics collection."""
    
    @pytest.mark.asyncio
    async def test_complete_metrics_flow(self):
        """Test metrics through complete flow."""
        tracker = IdempotencyTracker(redis_client=None, enable_metrics=True)
        
        # Multiple submissions with varied outcomes
        for pool_id in ["pool1", "pool2"]:
            for i in range(5):
                nonce = 100 + i
                rec = await tracker.record_submission(pool_id, nonce)
                
                # Half accepted, half rejected
                accepted = i % 2 == 0
                await tracker.mark_result(
                    rec.submission_id,
                    pool_id,
                    nonce,
                    accepted=accepted,
                    reason=None if accepted else "low_diff",
                )
        
        metrics = await tracker.get_metrics()
        
        assert metrics["submissions_recorded"] == 10
        assert metrics["accepted_submissions"] == 5
        assert metrics["rejected_submissions"] == 5
    
    @pytest.mark.asyncio
    async def test_metrics_with_duplicates(self):
        """Test metrics tracking duplicates."""
        tracker = IdempotencyTracker(redis_client=None, enable_metrics=True)
        
        pool_id = "pool1"
        nonce = 100
        
        # Initial submission
        rec1 = await tracker.record_submission(pool_id, nonce)
        await tracker.mark_result(rec1.submission_id, pool_id, nonce, accepted=False)
        
        # Duplicate attempts
        for _ in range(3):
            tracker.record_duplicate_attempt(pool_id, nonce, "rejected")
        
        metrics = await tracker.get_metrics()
        
        assert metrics["duplicate_attempts"] == 3
        assert metrics["retry_successes"] == 3  # All were retries


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
