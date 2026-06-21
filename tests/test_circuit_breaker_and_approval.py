"""Tests for circuit breaker failover and operator approval timeout fixes."""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock, MagicMock

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "python_backend"))

from pythia_mining.circuit_breaker_failover import (
    CircuitBreakerFailoverManager,
    PoolTier,
    CircuitBreakerStateEnum as CircuitBreakerState,
)
from pythia_mining.operator_approval_timeout import (
    OperatorApprovalTimeoutManager,
    ApprovalRequest,
    EscalationAction,
)


# ============================================================================
# TEST SUITE: Circuit Breaker Failover
# ============================================================================


class TestCircuitBreakerFailover:
    """Tests for circuit breaker failover recovery."""

    def test_initialization(self):
        """Test circuit breaker initializes with correct config."""
        manager = CircuitBreakerFailoverManager(
            primary_pool_id="pool_a",
            backup_pool_id="pool_b",
            max_failures_before_failover=10,
        )

        assert manager.current_tier == PoolTier.PRIMARY
        assert manager.current_state == CircuitBreakerState.CLOSED
        assert manager.get_current_pool_id() == "pool_a"

    def test_failure_tracking(self):
        """Test failure tracking and state transitions."""
        manager = CircuitBreakerFailoverManager(
            primary_pool_id="pool_a",
            backup_pool_id="pool_b",
            max_failures_before_failover=3,
        )

        # Record failures
        manager.record_failure("connection_refused")
        manager.record_failure("timeout")
        manager.record_failure("share_rejected")

        assert manager.failures_in_current_tier == 3
        assert manager.current_state == CircuitBreakerState.OPEN
        assert manager.should_failover()

    def test_failover_resets_heal_attempts(self):
        """Test that failover resets heal attempt window (critical bug fix)."""
        manager = CircuitBreakerFailoverManager(
            primary_pool_id="pool_a",
            backup_pool_id="pool_b",
            max_failures_before_failover=3,
        )

        # Record multiple failures
        for _ in range(3):
            manager.record_failure("test")

        # Verify heal window has 3 entries
        assert len(manager.heal_attempt_window) == 3

        # Failover
        success = manager.attempt_failover("exceeded_threshold")
        assert success
        assert manager.current_tier == PoolTier.BACKUP

        # CRITICAL: Heal window must be reset
        assert len(manager.heal_attempt_window) == 0
        assert manager.failures_in_current_tier == 0

    def test_failover_progression(self):
        """Test failover progression through tiers."""
        manager = CircuitBreakerFailoverManager(
            primary_pool_id="pool_a",
            backup_pool_id="pool_b",
            tertiary_pool_id="pool_c",
            max_failures_before_failover=2,
        )

        # Failover from primary to backup
        manager.failures_in_current_tier = 2
        assert manager.attempt_failover()
        assert manager.current_tier == PoolTier.BACKUP
        assert manager.get_current_pool_id() == "pool_b"

        # Failover from backup to tertiary
        manager.failures_in_current_tier = 2
        assert manager.attempt_failover()
        assert manager.current_tier == PoolTier.TERTIARY
        assert manager.get_current_pool_id() == "pool_c"

        # Try to failover from tertiary (no more tiers)
        manager.failures_in_current_tier = 2
        assert not manager.attempt_failover()
        assert manager.current_tier == PoolTier.MANUAL

    def test_success_recovery_from_half_open(self):
        """Test recovery from HALF_OPEN state on success."""
        manager = CircuitBreakerFailoverManager(
            primary_pool_id="pool_a",
            backup_pool_id="pool_b",
            max_failures_before_failover=2,
        )

        # Trigger circuit open
        manager.failures_in_current_tier = 2
        manager.current_state = CircuitBreakerState.OPEN

        # Try recovery
        assert manager.try_recovery()
        assert manager.current_state == CircuitBreakerState.HALF_OPEN

        # Record success
        manager.record_success()
        assert manager.current_state == CircuitBreakerState.CLOSED
        assert manager.failures_in_current_tier == 0

    def test_endless_retry_detection(self):
        """Test detection of endless retry loop."""
        manager = CircuitBreakerFailoverManager(
            primary_pool_id="pool_a",
            max_failures_before_failover=3,
        )

        # Simulate many heal attempts in window
        for i in range(25):
            manager.heal_attempt_window.append(time.time() - (i * 20))

        # Should detect endless retry
        assert manager.check_for_endless_retry()
        assert manager.metrics.endless_retry_preventions > 0

    def test_exponential_backoff_for_recovery(self):
        """Test exponential backoff when trying recovery."""
        manager = CircuitBreakerFailoverManager(
            primary_pool_id="pool_a",
            backup_pool_id="pool_b",
        )

        # Trigger circuit open
        manager.current_state = CircuitBreakerState.OPEN

        # First recovery attempt
        assert manager.try_recovery()
        assert manager.recovery_attempt_count == 1
        assert manager.current_state == CircuitBreakerState.HALF_OPEN

        # Immediately try again (should fail due to backoff)
        manager.current_state = CircuitBreakerState.OPEN
        assert not manager.try_recovery()
        assert manager.recovery_attempt_count == 1

        # Wait for backoff
        manager.last_recovery_attempt = time.time() - 31  # More than first backoff
        assert manager.try_recovery()
        assert manager.recovery_attempt_count == 2

    def test_failover_metrics_collection(self):
        """Test metrics collection during failovers."""
        manager = CircuitBreakerFailoverManager(
            primary_pool_id="pool_a",
            backup_pool_id="pool_b",
            max_failures_before_failover=1,
        )

        manager.record_failure("test")
        manager.attempt_failover()

        metrics = manager.get_metrics()
        assert metrics.total_failovers == 1
        assert metrics.successful_failovers == 1
        assert metrics.current_tier == "backup"

    def test_status_reporting(self):
        """Test comprehensive status reporting."""
        manager = CircuitBreakerFailoverManager(
            primary_pool_id="pool_a",
            backup_pool_id="pool_b",
        )

        status = manager.get_status()
        assert status["current_tier"] == "primary"
        assert status["current_state"] == "closed"
        assert status["pool_id"] == "pool_a"
        assert status["failures_in_tier"] == 0


# ============================================================================
# TEST SUITE: Operator Approval Timeout
# ============================================================================


class TestOperatorApprovalTimeout:
    """Tests for operator approval timeout management."""

    async def test_approval_request_creation(self):
        """Test approval request creation."""
        request = ApprovalRequest.create(
            decision_type="increase_search_depth",
            timeout_seconds=30,
            context={"current": 5, "proposed": 10},
        )

        assert request.decision_type == "increase_search_depth"
        assert request.timeout_seconds == 30
        assert request.status == "pending"
        assert request.context["current"] == 5

    async def test_approval_request_expiration(self):
        """Test approval request expiration checking."""
        request = ApprovalRequest.create(
            decision_type="test",
            timeout_seconds=1,
        )

        assert not request.is_expired()
        time.sleep(1.1)
        assert request.is_expired()

    async def test_approval_with_callback_approved(self):
        """Test approval callback returns approved."""
        async def mock_callback(req):
            return True

        manager = OperatorApprovalTimeoutManager(
            approval_callback=mock_callback,
            default_timeout_seconds=10,
        )

        result = await manager.request_approval(
            "test_decision",
            context={"value": 123},
        )

        assert result is True
        assert manager.metrics.approved_count == 1

    async def test_approval_with_callback_denied(self):
        """Test approval callback returns denied."""
        async def mock_callback(req):
            return False

        manager = OperatorApprovalTimeoutManager(
            approval_callback=mock_callback,
            default_timeout_seconds=10,
        )

        result = await manager.request_approval("test_decision")

        assert result is False
        assert manager.metrics.denied_count == 1

    async def test_approval_timeout_auto_approve(self):
        """Test timeout escalation to auto-approve."""
        async def slow_callback(req):
            await asyncio.sleep(5)
            return True

        manager = OperatorApprovalTimeoutManager(
            approval_callback=slow_callback,
            default_timeout_seconds=1,
            escalation_action=EscalationAction.AUTO_APPROVE,
        )

        result = await manager.request_approval("test_decision")

        assert result is True
        assert manager.metrics.timeout_count == 1
        assert manager.metrics.timeout_escalations == 1

    async def test_approval_timeout_auto_deny(self):
        """Test timeout escalation to auto-deny."""
        async def slow_callback(req):
            await asyncio.sleep(5)
            return True

        manager = OperatorApprovalTimeoutManager(
            approval_callback=slow_callback,
            default_timeout_seconds=1,
            escalation_action=EscalationAction.AUTO_DENY,
        )

        result = await manager.request_approval("test_decision")

        assert result is False
        assert manager.metrics.timeout_count == 1

    async def test_approval_timeout_manual_escalation(self):
        """Test timeout escalation to manual intervention."""
        async def slow_callback(req):
            await asyncio.sleep(5)
            return True

        manager = OperatorApprovalTimeoutManager(
            approval_callback=slow_callback,
            default_timeout_seconds=1,
            escalation_action=EscalationAction.ESCALATE_TO_MANUAL,
        )

        result = await manager.request_approval("test_decision")

        assert result is False
        assert manager.metrics.timeout_count == 1
        assert manager.metrics.timeout_escalations == 1

    async def test_approval_callback_error_handling(self):
        """Test error handling in approval callback."""
        async def error_callback(req):
            raise ValueError("Callback error")

        manager = OperatorApprovalTimeoutManager(
            approval_callback=error_callback,
            default_timeout_seconds=10,
            escalation_action=EscalationAction.AUTO_APPROVE,
        )

        result = await manager.request_approval("test_decision")

        assert result is True  # Auto-approve on error
        assert manager.metrics.error_count == 1

    async def test_no_callback_uses_escalation(self):
        """Test that missing callback uses escalation action."""
        manager = OperatorApprovalTimeoutManager(
            approval_callback=None,
            escalation_action=EscalationAction.AUTO_APPROVE,
        )

        result = await manager.request_approval("test_decision")

        assert result is True

    def test_sla_monitoring(self):
        """Test SLA compliance tracking."""
        manager = OperatorApprovalTimeoutManager()

        # Simulate response times
        manager.response_times = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]  # 4/6 < 5s = 67%
        manager.metrics.avg_response_time_seconds = 3.5
        manager.metrics.p95_response_time_seconds = 5.5

        sla = manager.get_sla_status()
        assert not sla["sla_compliant"]  # 67% < 95% target
        assert sla["compliance_rate"] < 0.95

    def test_pending_requests_tracking(self):
        """Test tracking of pending requests."""
        manager = OperatorApprovalTimeoutManager()

        req1 = ApprovalRequest.create("decision1", timeout_seconds=30)
        req2 = ApprovalRequest.create("decision2", timeout_seconds=30)

        manager.pending_requests[req1.request_id] = req1
        manager.pending_requests[req2.request_id] = req2

        pending = manager.get_pending_requests()
        assert len(pending) == 2

    def test_request_history(self):
        """Test request history retrieval."""
        manager = OperatorApprovalTimeoutManager()

        for i in range(10):
            req = ApprovalRequest.create(f"decision_{i}", timeout_seconds=30)
            manager.request_history.append(req)

        history = manager.get_request_history(limit=5)
        assert len(history) == 5

    def test_prometheus_metrics_emission(self):
        """Test Prometheus metrics emission."""
        manager = OperatorApprovalTimeoutManager()
        manager.metrics.total_requests = 100
        manager.metrics.approved_count = 80
        manager.metrics.denied_count = 20
        manager.response_times = [2.0, 3.0, 4.0]

        metrics = manager.emit_prometheus_metrics()
        assert isinstance(metrics, list)
        assert any("hyba_operator_approval_requests_total 100" in line for line in metrics)
        assert any("hyba_operator_approval_approved_total 80" in line for line in metrics)


# ============================================================================
# INTEGRATION TESTS: Realistic Scenarios
# ============================================================================


class TestRealisticScenarios:
    """Integration tests with realistic production scenarios."""

    def test_cascade_failover_under_stress(self):
        """Test cascading failover when all pools fail."""
        manager = CircuitBreakerFailoverManager(
            primary_pool_id="pool_a",
            backup_pool_id="pool_b",
            tertiary_pool_id="pool_c",
            max_failures_before_failover=2,
        )

        # Primary fails
        for _ in range(2):
            manager.record_failure("primary_down")
        assert manager.attempt_failover()
        assert manager.current_tier == PoolTier.BACKUP

        # Backup also fails
        for _ in range(2):
            manager.record_failure("backup_down")
        assert manager.attempt_failover()
        assert manager.current_tier == PoolTier.TERTIARY

        # Tertiary fails
        for _ in range(2):
            manager.record_failure("tertiary_down")
        assert not manager.attempt_failover()
        assert manager.current_tier == PoolTier.MANUAL

    async def test_approval_queue_fairness(self):
        """Test FIFO fairness of approval requests."""
        manager = OperatorApprovalTimeoutManager(
            approval_callback=None,
            escalation_action=EscalationAction.AUTO_APPROVE,
        )

        # Queue multiple requests
        results = []
        for i in range(5):
            result = await manager.request_approval(f"decision_{i}")
            results.append(result)

        # All should eventually be resolved
        assert len(results) == 5
        assert all(results)

    async def test_recovery_from_cascading_failures(self):
        """Test recovery after cascading failures."""
        manager = CircuitBreakerFailoverManager(
            primary_pool_id="pool_a",
            backup_pool_id="pool_b",
            max_failures_before_failover=2,
        )

        # Cascade to backup
        for _ in range(2):
            manager.record_failure("primary_fail")
        manager.attempt_failover()

        # Backup fails but then recovers
        manager.record_failure("backup_fail")
        manager.record_success()

        # Should be back online
        assert manager.current_state == CircuitBreakerState.CLOSED

    def test_no_endless_retry_after_failover(self):
        """Test that endless retry prevention works after failover."""
        manager = CircuitBreakerFailoverManager(
            primary_pool_id="pool_a",
            backup_pool_id="pool_b",
            max_failures_before_failover=3,
        )

        # Generate 3 failures in primary
        for _ in range(3):
            manager.record_failure("test")
            manager.heal_attempt_window.append(time.time())

        assert len(manager.heal_attempt_window) == 3

        # Failover
        manager.attempt_failover()

        # Window should be cleared
        assert len(manager.heal_attempt_window) == 0

        # Now backup can fail without being seen as endless retry
        manager.record_failure("backup_fail")
        assert not manager.check_for_endless_retry()


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
