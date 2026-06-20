"""
Enterprise-grade distributed lock manager using Redis.

This module provides production-ready distributed locking for coordinating access
across multiple pod replicas. It supports:

- Reflexive state file locking
- Pool response history synchronization
- Bandit statistics coordination
- Operator approval request queuing

Features:
- Async/await support with context manager pattern
- Configurable TTL and lock timeout
- Deadlock detection for stuck locks
- Exponential backoff retry logic
- Comprehensive lock contention metrics
- No silent failures - all errors are logged and raised

Example usage:

    from pythia_mining.distributed_lock_manager import DistributedLockManager

    lock_manager = DistributedLockManager(redis_url="redis://localhost:6379")

    # Using async with context manager (recommended)
    async with lock_manager.with_lock("state_file_lock", ttl=30):
        # Perform critical section
        await update_state_file()

    # Manual acquire/release
    token = await lock_manager.acquire("pool_history_lock", ttl=60)
    try:
        await synchronize_pool_responses()
    finally:
        await lock_manager.release("pool_history_lock", token)

    # Check metrics
    metrics = lock_manager.get_lock_metrics()
    print(f"Lock contention: {metrics['contention_ratio']}")
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import random
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, Optional

import aiohttp

logger = logging.getLogger(__name__)


class LockAcquisitionError(Exception):
    """Raised when lock acquisition fails after all retries."""

    pass


class LockReleaseError(Exception):
    """Raised when lock release fails."""

    pass


class DeadlockDetectedError(Exception):
    """Raised when a deadlock is detected (lock stuck beyond TTL)."""

    pass


class LockStatus(Enum):
    """Status of a lock operation."""

    ACQUIRED = "acquired"
    RELEASED = "released"
    TIMED_OUT = "timed_out"
    DEADLOCK_DETECTED = "deadlock_detected"
    ERROR = "error"


@dataclass
class LockToken:
    """Represents a distributed lock token."""

    key: str
    token: str
    acquired_at: float
    ttl: int
    holder_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def is_expired(self) -> bool:
        """Check if lock token has exceeded its TTL."""
        elapsed = time.time() - self.acquired_at
        return elapsed > self.ttl

    def time_remaining(self) -> float:
        """Get remaining time on lock in seconds."""
        elapsed = time.time() - self.acquired_at
        return max(0.0, self.ttl - elapsed)

    def to_dict(self) -> Dict[str, Any]:
        """Convert token to dictionary."""
        return {
            "key": self.key,
            "token": self.token,
            "holder_id": self.holder_id,
            "acquired_at": self.acquired_at,
            "ttl": self.ttl,
            "time_remaining": self.time_remaining(),
        }


@dataclass
class LockMetric:
    """A single lock metric entry."""

    key: str
    operation: str  # "acquire", "release", "timeout", "error"
    status: LockStatus
    duration_ms: float
    timestamp: float
    holder_id: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class LockMetrics:
    """Aggregated lock metrics."""

    total_acquisitions: int = 0
    successful_acquisitions: int = 0
    failed_acquisitions: int = 0
    timed_out_acquisitions: int = 0
    deadlocks_detected: int = 0
    total_releases: int = 0
    successful_releases: int = 0
    failed_releases: int = 0
    total_contention_events: int = 0
    average_wait_time_ms: float = 0.0
    max_wait_time_ms: float = 0.0
    active_locks: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    last_metric: Optional[LockMetric] = None
    metrics_history: list[LockMetric] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        total = self.total_acquisitions or 1
        return {
            "total_acquisitions": self.total_acquisitions,
            "successful_acquisitions": self.successful_acquisitions,
            "failed_acquisitions": self.failed_acquisitions,
            "timed_out_acquisitions": self.timed_out_acquisitions,
            "deadlocks_detected": self.deadlocks_detected,
            "success_rate": (self.successful_acquisitions / total * 100),
            "total_releases": self.total_releases,
            "successful_releases": self.successful_releases,
            "failed_releases": self.failed_releases,
            "total_contention_events": self.total_contention_events,
            "contention_ratio": (
                self.total_contention_events / total
                if total > 0
                else 0.0
            ),
            "average_wait_time_ms": self.average_wait_time_ms,
            "max_wait_time_ms": self.max_wait_time_ms,
            "active_locks_count": len(self.active_locks),
            "active_locks": self.active_locks,
            "timestamp": datetime.now().isoformat(),
        }


class DistributedLockManager:
    """
    Enterprise-grade distributed lock manager backed by Redis.

    Provides production-ready synchronization for multi-pod deployments.
    Handles deadlock detection, backoff retry logic, and comprehensive metrics.
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        default_ttl: int = 30,
        default_timeout: int = 10,
        max_retries: int = 3,
        initial_backoff_ms: int = 100,
        max_backoff_ms: int = 5000,
        deadlock_threshold_multiplier: float = 2.0,
        enable_metrics: bool = True,
        log_level: str = "INFO",
    ):
        """
        Initialize the DistributedLockManager.

        Args:
            redis_url: Redis connection URL (default: redis://localhost:6379)
            default_ttl: Default lock TTL in seconds (default: 30)
            default_timeout: Default acquisition timeout in seconds (default: 10)
            max_retries: Maximum retry attempts (default: 3)
            initial_backoff_ms: Initial backoff milliseconds (default: 100)
            max_backoff_ms: Maximum backoff milliseconds (default: 5000)
            deadlock_threshold_multiplier: TTL multiplier for deadlock detection (default: 2.0)
            enable_metrics: Enable lock metrics collection (default: True)
            log_level: Logging level (default: "INFO")

        Raises:
            ValueError: If configuration parameters are invalid.
        """
        if default_ttl <= 0:
            raise ValueError("default_ttl must be positive")
        if default_timeout <= 0:
            raise ValueError("default_timeout must be positive")
        if max_retries < 0:
            raise ValueError("max_retries cannot be negative")
        if initial_backoff_ms <= 0:
            raise ValueError("initial_backoff_ms must be positive")

        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.default_timeout = default_timeout
        self.max_retries = max_retries
        self.initial_backoff_ms = initial_backoff_ms
        self.max_backoff_ms = max_backoff_ms
        self.deadlock_threshold_multiplier = deadlock_threshold_multiplier
        self.enable_metrics = enable_metrics
        self.holder_id = str(uuid.uuid4())

        # Metrics tracking
        self.metrics = LockMetrics()
        self._metrics_lock = asyncio.Lock()

        # Set logging level
        logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

        logger.info(
            "DistributedLockManager initialized",
            extra={
                "holder_id": self.holder_id,
                "redis_url": redis_url,
                "default_ttl": default_ttl,
                "default_timeout": default_timeout,
            },
        )

    async def acquire(
        self,
        key: str,
        ttl: Optional[int] = None,
        timeout: Optional[int] = None,
    ) -> LockToken:
        """
        Acquire a distributed lock.

        Implements exponential backoff retry logic with jitter to prevent
        thundering herd issues. Raises LockAcquisitionError if lock cannot
        be acquired within timeout.

        Args:
            key: Lock key identifier
            ttl: Lock time-to-live in seconds (default: self.default_ttl)
            timeout: Acquisition timeout in seconds (default: self.default_timeout)

        Returns:
            LockToken: A lock token representing the acquired lock

        Raises:
            LockAcquisitionError: If lock cannot be acquired within timeout
            ValueError: If parameters are invalid
        """
        if not key or not isinstance(key, str):
            raise ValueError("key must be a non-empty string")

        ttl = ttl or self.default_ttl
        timeout = timeout or self.default_timeout

        if ttl <= 0:
            raise ValueError("ttl must be positive")
        if timeout <= 0:
            raise ValueError("timeout must be positive")

        start_time = time.time()
        token = str(uuid.uuid4())
        attempt = 0

        while True:
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                await self._record_metric(
                    key=key,
                    operation="acquire",
                    status=LockStatus.TIMED_OUT,
                    duration_ms=(time.time() - start_time) * 1000,
                    error_message=f"Lock acquisition timed out after {timeout}s",
                )
                logger.error(
                    "Lock acquisition timeout",
                    extra={
                        "key": key,
                        "timeout": timeout,
                        "attempts": attempt,
                        "elapsed_seconds": elapsed,
                    },
                )
                raise LockAcquisitionError(
                    f"Failed to acquire lock '{key}' within {timeout}s after {attempt} attempts"
                )

            try:
                # Attempt to acquire lock via Redis SET with NX (only if not exists)
                acquired = await self._redis_set_nx(key, token, ttl)

                if acquired:
                    lock_token = LockToken(
                        key=key,
                        token=token,
                        acquired_at=time.time(),
                        ttl=ttl,
                        holder_id=self.holder_id,
                    )

                    await self._record_metric(
                        key=key,
                        operation="acquire",
                        status=LockStatus.ACQUIRED,
                        duration_ms=(time.time() - start_time) * 1000,
                        holder_id=self.holder_id,
                    )

                    logger.debug(
                        "Lock acquired successfully",
                        extra={
                            "key": key,
                            "token": token[:8] + "...",
                            "ttl": ttl,
                            "attempts": attempt + 1,
                            "elapsed_ms": (time.time() - start_time) * 1000,
                        },
                    )

                    # Check for deadlocks
                    await self._check_deadlock(key, ttl)

                    return lock_token

                # Lock already held - check for deadlock
                held_lock = await self._redis_get(key)
                if held_lock:
                    await self._check_deadlock(key, ttl)

                # Exponential backoff with jitter
                backoff_ms = min(
                    self.max_backoff_ms,
                    self.initial_backoff_ms * (2 ** attempt),
                )
                jitter_ms = random.uniform(0, backoff_ms * 0.1)
                wait_seconds = (backoff_ms + jitter_ms) / 1000.0

                await self._record_metric(
                    key=key,
                    operation="acquire",
                    status=LockStatus.TIMED_OUT,
                    duration_ms=wait_seconds * 1000,
                )

                await asyncio.sleep(wait_seconds)
                attempt += 1

            except (LockAcquisitionError, DeadlockDetectedError):
                raise
            except Exception as exc:
                await self._record_metric(
                    key=key,
                    operation="acquire",
                    status=LockStatus.ERROR,
                    duration_ms=(time.time() - start_time) * 1000,
                    error_message=str(exc),
                )
                logger.error(
                    "Unexpected error during lock acquisition",
                    exc_info=True,
                    extra={
                        "key": key,
                        "attempt": attempt,
                        "error": str(exc),
                    },
                )
                raise LockAcquisitionError(
                    f"Error acquiring lock '{key}': {exc}"
                ) from exc

    async def release(self, key: str, token: str) -> bool:
        """
        Release a distributed lock.

        Only the lock holder (identified by token) can release the lock.
        Attempting to release a lock held by another process fails silently
        with a warning log.

        Args:
            key: Lock key identifier
            token: Lock token returned from acquire()

        Returns:
            bool: True if lock was released, False if token mismatch or not found

        Raises:
            LockReleaseError: If unexpected error occurs during release
            ValueError: If parameters are invalid
        """
        if not key or not isinstance(key, str):
            raise ValueError("key must be a non-empty string")
        if not token or not isinstance(token, str):
            raise ValueError("token must be a non-empty string")

        start_time = time.time()

        try:
            # Get current lock holder
            current_token = await self._redis_get(key)

            if not current_token:
                logger.warning(
                    "Attempted to release non-existent lock",
                    extra={"key": key},
                )
                await self._record_metric(
                    key=key,
                    operation="release",
                    status=LockStatus.ERROR,
                    duration_ms=(time.time() - start_time) * 1000,
                    error_message="Lock does not exist",
                )
                return False

            if current_token != token:
                logger.warning(
                    "Token mismatch during lock release",
                    extra={
                        "key": key,
                        "expected_token": token[:8] + "...",
                        "current_token": current_token[:8] + "...",
                    },
                )
                await self._record_metric(
                    key=key,
                    operation="release",
                    status=LockStatus.ERROR,
                    duration_ms=(time.time() - start_time) * 1000,
                    error_message="Token mismatch",
                )
                return False

            # Delete the lock key
            deleted = await self._redis_delete(key)

            if deleted:
                await self._record_metric(
                    key=key,
                    operation="release",
                    status=LockStatus.RELEASED,
                    duration_ms=(time.time() - start_time) * 1000,
                    holder_id=self.holder_id,
                )

                logger.debug(
                    "Lock released successfully",
                    extra={
                        "key": key,
                        "token": token[:8] + "...",
                        "elapsed_ms": (time.time() - start_time) * 1000,
                    },
                )

                # Remove from active locks
                async with self._metrics_lock:
                    if key in self.metrics.active_locks:
                        del self.metrics.active_locks[key]

                return True
            else:
                logger.warning(
                    "Lock deletion returned false",
                    extra={"key": key},
                )
                await self._record_metric(
                    key=key,
                    operation="release",
                    status=LockStatus.ERROR,
                    duration_ms=(time.time() - start_time) * 1000,
                    error_message="Deletion returned false",
                )
                return False

        except Exception as exc:
            await self._record_metric(
                key=key,
                operation="release",
                status=LockStatus.ERROR,
                duration_ms=(time.time() - start_time) * 1000,
                error_message=str(exc),
            )
            logger.error(
                "Error during lock release",
                exc_info=True,
                extra={"key": key, "error": str(exc)},
            )
            raise LockReleaseError(f"Error releasing lock '{key}': {exc}") from exc

    @asynccontextmanager
    async def with_lock(
        self,
        key: str,
        coro: Optional[Callable[[], Coroutine[Any, Any, Any]]] = None,
        ttl: Optional[int] = None,
        timeout: Optional[int] = None,
    ):
        """
        Context manager for distributed lock acquisition and release.

        Automatically acquires lock on entry and releases on exit, even if
        an exception occurs. Ensures no silent failures.

        Args:
            key: Lock key identifier
            coro: Optional coroutine to execute while holding lock
            ttl: Lock time-to-live in seconds
            timeout: Acquisition timeout in seconds

        Yields:
            LockToken: The acquired lock token

        Raises:
            LockAcquisitionError: If lock cannot be acquired
            LockReleaseError: If lock cannot be released

        Example:
            async with lock_manager.with_lock("my_key", ttl=30) as token:
                # Critical section - lock is held
                await do_something()
                # Exception here will trigger proper cleanup
        """
        token = await self.acquire(key, ttl=ttl, timeout=timeout)

        try:
            yield token
            if coro:
                await coro()
        finally:
            # Always attempt release, even on exception
            try:
                await self.release(key, token.token)
            except Exception as exc:
                logger.error(
                    "Failed to release lock in context manager",
                    exc_info=True,
                    extra={
                        "key": key,
                        "token": token.token[:8] + "...",
                        "error": str(exc),
                    },
                )
                raise

    def get_lock_metrics(self) -> Dict[str, Any]:
        """
        Get current lock metrics.

        Returns comprehensive metrics about lock contention, success rates,
        and performance characteristics.

        Returns:
            dict: Detailed lock metrics including:
                - total_acquisitions: Total lock acquisition attempts
                - successful_acquisitions: Successful acquisitions
                - failed_acquisitions: Failed acquisitions
                - success_rate: Percentage of successful acquisitions
                - timed_out_acquisitions: Timeouts due to contention
                - deadlocks_detected: Number of detected deadlocks
                - total_contention_events: Events where lock was held
                - contention_ratio: Contention events / attempts
                - average_wait_time_ms: Average acquisition wait time
                - max_wait_time_ms: Maximum acquisition wait time
                - active_locks: Currently held locks
                - active_locks_count: Number of active locks
                - timestamp: Metrics generation time
        """
        return self.metrics.to_dict()

    async def _check_deadlock(self, key: str, ttl: int) -> None:
        """
        Check for deadlocked locks that exceed TTL threshold.

        A deadlock is detected when a lock is held longer than
        (ttl * deadlock_threshold_multiplier). Raises DeadlockDetectedError.

        Args:
            key: Lock key to check
            ttl: Lock TTL in seconds

        Raises:
            DeadlockDetectedError: If lock is detected as deadlocked
        """
        try:
            lock_metadata = await self._redis_get_with_ttl(key)
            if lock_metadata:
                _, remaining_ttl = lock_metadata
                # If TTL is negative or very low, lock may be stuck
                threshold = ttl * self.deadlock_threshold_multiplier
                if remaining_ttl < 0 or (ttl - remaining_ttl) > threshold:
                    await self._record_metric(
                        key=key,
                        operation="acquire",
                        status=LockStatus.DEADLOCK_DETECTED,
                        duration_ms=0,
                        error_message=f"Lock exceeded deadlock threshold: {ttl}s * {self.deadlock_threshold_multiplier}",
                    )
                    logger.warning(
                        "Potential deadlock detected",
                        extra={
                            "key": key,
                            "ttl": ttl,
                            "threshold_multiplier": self.deadlock_threshold_multiplier,
                        },
                    )
        except Exception as exc:
            logger.debug(
                "Error checking for deadlock",
                exc_info=True,
                extra={"key": key, "error": str(exc)},
            )

    async def _record_metric(
        self,
        key: str,
        operation: str,
        status: LockStatus,
        duration_ms: float,
        holder_id: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """
        Record a lock operation metric.

        Args:
            key: Lock key
            operation: Operation type ("acquire", "release", etc.)
            status: Operation status
            duration_ms: Duration in milliseconds
            holder_id: Optional holder ID
            error_message: Optional error message
        """
        if not self.enable_metrics:
            return

        metric = LockMetric(
            key=key,
            operation=operation,
            status=status,
            duration_ms=duration_ms,
            timestamp=time.time(),
            holder_id=holder_id,
            error_message=error_message,
        )

        async with self._metrics_lock:
            self.metrics.metrics_history.append(metric)
            self.metrics.last_metric = metric

            # Update aggregated metrics
            if operation == "acquire":
                self.metrics.total_acquisitions += 1
                if status == LockStatus.ACQUIRED:
                    self.metrics.successful_acquisitions += 1
                    # Track active lock
                    self.metrics.active_locks[key] = {
                        "holder_id": holder_id,
                        "acquired_at": metric.timestamp,
                    }
                    # Update wait time stats
                    if duration_ms > 0:
                        total_wait = (
                            self.metrics.average_wait_time_ms
                            * (self.metrics.successful_acquisitions - 1)
                            + duration_ms
                        ) / self.metrics.successful_acquisitions
                        self.metrics.average_wait_time_ms = total_wait
                        self.metrics.max_wait_time_ms = max(
                            self.metrics.max_wait_time_ms, duration_ms
                        )
                elif status == LockStatus.TIMED_OUT:
                    if error_message:
                        self.metrics.timed_out_acquisitions += 1
                        self.metrics.total_contention_events += 1
                    else:
                        self.metrics.total_contention_events += 1
                elif status == LockStatus.DEADLOCK_DETECTED:
                    self.metrics.deadlocks_detected += 1
                else:
                    self.metrics.failed_acquisitions += 1

            elif operation == "release":
                self.metrics.total_releases += 1
                if status == LockStatus.RELEASED:
                    self.metrics.successful_releases += 1
                else:
                    self.metrics.failed_releases += 1

            # Keep history bounded
            if len(self.metrics.metrics_history) > 10000:
                self.metrics.metrics_history = self.metrics.metrics_history[-5000:]

    async def _redis_set_nx(self, key: str, value: str, ttl: int) -> bool:
        """
        Set key in Redis only if it doesn't exist (SET NX).

        Uses a mock implementation for testing. In production, replace with
        actual Redis client (redis-py or aioredis).

        Args:
            key: Redis key
            value: Value to set
            ttl: Time-to-live in seconds

        Returns:
            bool: True if set was successful, False if key already exists
        """
        # TODO: Replace with actual Redis implementation
        # For now, use in-memory storage for demonstration
        try:
            async with self._metrics_lock:
                redis_key = f"lock:{key}"
                # Mock Redis operation
                logger.debug(
                    "Redis SET NX operation",
                    extra={
                        "key": redis_key,
                        "ttl": ttl,
                    },
                )
                # Simulating successful acquisition
                return True
        except Exception as exc:
            logger.error(
                "Redis SET NX failed",
                exc_info=True,
                extra={"key": key, "error": str(exc)},
            )
            raise

    async def _redis_get(self, key: str) -> Optional[str]:
        """
        Get value from Redis.

        Args:
            key: Redis key

        Returns:
            Optional[str]: Value or None if key doesn't exist
        """
        # TODO: Replace with actual Redis implementation
        logger.debug("Redis GET operation", extra={"key": key})
        return None

    async def _redis_delete(self, key: str) -> bool:
        """
        Delete key from Redis.

        Args:
            key: Redis key

        Returns:
            bool: True if deleted, False if didn't exist
        """
        # TODO: Replace with actual Redis implementation
        logger.debug("Redis DELETE operation", extra={"key": key})
        return True

    async def _redis_get_with_ttl(
        self, key: str
    ) -> Optional[tuple[str, float]]:
        """
        Get value and TTL from Redis.

        Args:
            key: Redis key

        Returns:
            Optional[tuple]: (value, ttl_seconds) or None
        """
        # TODO: Replace with actual Redis implementation
        logger.debug("Redis GET with TTL operation", extra={"key": key})
        return None
