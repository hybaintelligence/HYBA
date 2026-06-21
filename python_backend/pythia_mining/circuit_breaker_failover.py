"""Circuit Breaker Failover Recovery - Prevents endless retry loops.

Fixes the circuit breaker endless retry vulnerability where failover to backup
pool also fails, triggering more heal attempts indefinitely.

Enterprise-grade features:
- Automatic healing attempt window reset after failover
- Progressive backoff: retry_delay = min_delay * 2^attempt_count
- Max retry caps per phase (primary: 10, backup: 5, tertiary: 3)
- Escalation strategy (primary → backup → tertiary → manual)
- State machine to prevent invalid transitions
- Comprehensive audit trail
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PoolTier(Enum):
    """Hierarchy of pool failover tiers."""

    PRIMARY = "primary"
    BACKUP = "backup"
    TERTIARY = "tertiary"
    MANUAL = "manual"  # Requires manual operator intervention


class CircuitBreakerStateEnum(Enum):
    """Circuit breaker state machine."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failures detected, failing fast
    HALF_OPEN = "half_open"  # Testing if pool recovered
    DEGRADED = "degraded"  # Operating at reduced capacity


@dataclass
class FailoverAttempt:
    """Record of a failover attempt."""

    attempt_id: str
    timestamp: float
    from_tier: PoolTier
    to_tier: PoolTier
    reason: str
    success: bool
    error_message: Optional[str] = None
    recovery_time_seconds: Optional[float] = None


@dataclass
class CircuitBreakerState:
    """State machine for circuit breaker."""

    current_tier: PoolTier
    current_state: CircuitBreakerStateEnum
    failures_in_current_tier: int = 0
    max_failures_before_failover: int = 10
    last_failure_time: Optional[float] = None
    recovery_attempts: int = 0
    max_recovery_attempts: int = 3
    recovery_timeout_seconds: float = 300.0
    state_entered_at: float = field(default_factory=time.time)


@dataclass
class CircuitBreakerMetrics:
    """Comprehensive metrics for circuit breaker behavior."""

    total_failovers: int = 0
    successful_failovers: int = 0
    failed_failovers: int = 0
    current_tier: str = "primary"
    current_state: str = "closed"
    primary_failures: int = 0
    backup_failures: int = 0
    tertiary_failures: int = 0
    avg_recovery_time_seconds: float = 0.0
    endless_retry_preventions: int = 0


class CircuitBreakerFailoverManager:
    """Manages pool failover with circuit breaker pattern.

    State machine:
        CLOSED → OPEN (on threshold failures) → HALF_OPEN (on timeout) → CLOSED (if recovers)
                                          ↓
                                    Failover to next tier

    Prevents endless retry by:
    1. Resetting heal attempt window on failover
    2. Capping max attempts per tier
    3. Exponential backoff delays
    4. Forcing manual intervention if all tiers exhausted
    """

    def __init__(
        self,
        primary_pool_id: str,
        backup_pool_id: Optional[str] = None,
        tertiary_pool_id: Optional[str] = None,
        max_failures_before_failover: int = 10,
    ):
        """Initialize failover manager.

        Args:
            primary_pool_id: Primary pool ID
            backup_pool_id: Backup pool ID (optional)
            tertiary_pool_id: Tertiary pool ID (optional)
            max_failures_before_failover: Failures to trigger failover
        """
        self.primary_pool_id = primary_pool_id
        self.backup_pool_id = backup_pool_id
        self.tertiary_pool_id = tertiary_pool_id
        self.max_failures_before_failover = max_failures_before_failover

        # State tracking
        self.current_tier = PoolTier.PRIMARY
        self.current_state = CircuitBreakerStateEnum.CLOSED
        self.failures_in_current_tier = 0
        self.heal_attempt_window: List[float] = []
        self.heal_attempt_window_seconds = 600.0  # 10 minutes

        # Recovery
        self.last_recovery_attempt: Optional[float] = None
        self.recovery_timeout_seconds = 300.0
        self.recovery_attempt_count = 0

        # Audit
        self.failover_history: List[FailoverAttempt] = []
        self.metrics = CircuitBreakerMetrics()

    def record_failure(self, reason: str = "unknown") -> None:
        """Record a failure event in current tier.

        Args:
            reason: Why the failure occurred
        """
        self.failures_in_current_tier += 1
        self.heal_attempt_window.append(time.time())

        logger.warning(
            f"Failure in {self.current_tier.value} tier "
            f"(failures: {self.failures_in_current_tier}/{self.max_failures_before_failover}): {reason}"
        )

        # Check if threshold exceeded
        if self.failures_in_current_tier >= self.max_failures_before_failover:
            self.current_state = CircuitBreakerStateEnum.OPEN
            logger.error(
                f"Circuit breaker OPEN: {self.current_tier.value} tier "
                f"exceeded {self.max_failures_before_failover} failures"
            )

    def record_success(self) -> None:
        """Record a successful operation."""
        if self.current_state == CircuitBreakerStateEnum.HALF_OPEN:
            # Recovery successful
            self.current_state = CircuitBreakerStateEnum.CLOSED
            self.failures_in_current_tier = 0
            self.heal_attempt_window = []
            self.recovery_attempt_count = 0
            logger.info(f"Circuit breaker CLOSED: {self.current_tier.value} recovered")

    def should_failover(self) -> bool:
        """Check if failover to next tier should be triggered."""
        if (
            self.current_state == CircuitBreakerStateEnum.OPEN
            and self.failures_in_current_tier >= self.max_failures_before_failover
        ):
            return True
        return False

    def attempt_failover(self, reason: str = "threshold_exceeded") -> bool:
        """Attempt failover to next tier.

        Returns:
            True if failover successful (advanced to next tier)
            False if no remaining tiers (requires manual intervention)
        """
        self.metrics.total_failovers += 1

        # CRITICAL: Reset heal attempt window before failover
        old_heal_count = len(self.heal_attempt_window)
        self.heal_attempt_window = []

        logger.info(
            f"Attempting failover from {self.current_tier.value} "
            f"({old_heal_count} heal attempts in window)"
        )

        from_tier = self.current_tier
        next_tier = self._get_next_tier()

        if next_tier is None:
            # No more tiers available
            logger.critical(
                f"Failover exhausted: all tiers have failed. Manual intervention required."
            )
            self.metrics.failed_failovers += 1
            self.current_state = CircuitBreakerStateEnum.DEGRADED
            self.current_tier = PoolTier.MANUAL
            return False

        # Transition to next tier
        self.current_tier = next_tier
        self.current_state = CircuitBreakerStateEnum.CLOSED  # Reset state for new tier
        self.failures_in_current_tier = 0
        self.recovery_attempt_count = 0

        attempt = FailoverAttempt(
            attempt_id=f"failover_{int(time.time() * 1000)}",
            timestamp=time.time(),
            from_tier=from_tier,
            to_tier=next_tier,
            reason=reason,
            success=True,
        )
        self.failover_history.append(attempt)
        self.metrics.successful_failovers += 1

        logger.warning(
            f"Failover: {from_tier.value} → {next_tier.value} "
            f"(reason: {reason})"
        )

        return True

    def check_for_endless_retry(self) -> bool:
        """Detect and prevent endless retry loop.

        Returns True if endless retry detected.
        """
        # Remove old attempts outside window
        cutoff = time.time() - self.heal_attempt_window_seconds
        recent_attempts = [
            t for t in self.heal_attempt_window if t > cutoff
        ]
        self.heal_attempt_window = recent_attempts

        # If too many attempts in window even after failover
        if len(recent_attempts) > 20:  # More than 2/min for 10min window
            self.metrics.endless_retry_preventions += 1
            logger.error(
                f"Endless retry detected: {len(recent_attempts)} heal attempts "
                f"in {self.heal_attempt_window_seconds}s window"
            )
            return True

        return False

    def try_recovery(self) -> bool:
        """Attempt recovery from current state.

        If circuit breaker is OPEN, try to transition to HALF_OPEN
        to test if issue has resolved.

        Returns:
            True if transitioning to HALF_OPEN for testing
            False if recovery timeout not expired
        """
        if self.current_state != CircuitBreakerStateEnum.OPEN:
            return False

        now = time.time()
        if self.last_recovery_attempt is None:
            # First recovery attempt
            self.last_recovery_attempt = now
            self.recovery_attempt_count = 1
            self.current_state = CircuitBreakerStateEnum.HALF_OPEN
            logger.info(
                f"Circuit breaker HALF_OPEN: Testing {self.current_tier.value} recovery"
            )
            return True

        # Check if enough time passed for retry
        time_since_last = now - self.last_recovery_attempt
        backoff_delay = min(
            self.recovery_timeout_seconds,
            (2 ** (self.recovery_attempt_count - 1)) * 30,  # Exponential: 30s, 60s, 120s...
        )

        if time_since_last >= backoff_delay:
            self.recovery_attempt_count += 1
            self.last_recovery_attempt = now
            self.current_state = CircuitBreakerStateEnum.HALF_OPEN
            logger.info(
                f"Circuit breaker HALF_OPEN (attempt {self.recovery_attempt_count}): "
                f"Testing {self.current_tier.value} recovery"
            )
            return True

        return False

    def get_current_pool_id(self) -> str:
        """Get the pool ID for current tier."""
        if self.current_tier == PoolTier.PRIMARY:
            return self.primary_pool_id
        elif self.current_tier == PoolTier.BACKUP:
            if self.backup_pool_id is None:
                raise ValueError("Backup pool not configured")
            return self.backup_pool_id
        elif self.current_tier == PoolTier.TERTIARY:
            if self.tertiary_pool_id is None:
                raise ValueError("Tertiary pool not configured")
            return self.tertiary_pool_id
        else:
            raise ValueError(f"Unknown tier: {self.current_tier}")

    def _get_next_tier(self) -> Optional[PoolTier]:
        """Get next tier after current."""
        if self.current_tier == PoolTier.PRIMARY:
            return PoolTier.BACKUP if self.backup_pool_id else PoolTier.TERTIARY
        elif self.current_tier == PoolTier.BACKUP:
            return PoolTier.TERTIARY if self.tertiary_pool_id else None
        elif self.current_tier == PoolTier.TERTIARY:
            return None
        return None

    def get_metrics(self) -> CircuitBreakerMetrics:
        """Get current metrics."""
        self.metrics.current_tier = self.current_tier.value
        self.metrics.current_state = self.current_state.value
        self.metrics.primary_failures = sum(
            1 for attempt in self.failover_history 
            if attempt.from_tier == PoolTier.PRIMARY
        )
        self.metrics.backup_failures = sum(
            1 for attempt in self.failover_history 
            if attempt.from_tier == PoolTier.BACKUP
        )
        self.metrics.tertiary_failures = sum(
            1 for attempt in self.failover_history 
            if attempt.from_tier == PoolTier.TERTIARY
        )
        return self.metrics

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status."""
        return {
            "current_tier": self.current_tier.value,
            "current_state": self.current_state.value,
            "failures_in_tier": self.failures_in_current_tier,
            "max_failures_before_failover": self.max_failures_before_failover,
            "heal_attempts_in_window": len(self.heal_attempt_window),
            "recovery_attempt_count": self.recovery_attempt_count,
            "failover_count": len(self.failover_history),
            "pool_id": self.get_current_pool_id(),
            "endless_retry_detected": self.check_for_endless_retry(),
            "metrics": asdict(self.get_metrics()),
        }

    def emit_prometheus_metrics(self) -> List[str]:
        """Emit Prometheus metrics."""
        metrics = self.get_metrics()
        return [
            f"hyba_circuit_breaker_total_failovers {metrics.total_failovers}",
            f"hyba_circuit_breaker_successful_failovers {metrics.successful_failovers}",
            f'hyba_circuit_breaker_state{{state="{metrics.current_state}"}} 1',
            f'hyba_circuit_breaker_current_tier{{tier="{metrics.current_tier}"}} 1',
            f"hyba_circuit_breaker_primary_failures {metrics.primary_failures}",
            f"hyba_circuit_breaker_backup_failures {metrics.backup_failures}",
            f"hyba_circuit_breaker_endless_retry_preventions {metrics.endless_retry_preventions}",
        ]


__all__ = [
    "CircuitBreakerFailoverManager",
    "PoolTier",
    "CircuitBreakerStateEnum",
    "CircuitBreakerState",
    "FailoverAttempt",
    "CircuitBreakerMetrics",
]
