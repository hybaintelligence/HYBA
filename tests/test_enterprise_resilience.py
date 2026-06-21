from __future__ import annotations

import asyncio

import pytest

from hyba_genesis_api.core.resilience import CircuitBreaker, CircuitOpenError, CircuitState


def test_circuit_breaker_opens_after_threshold_and_blocks() -> None:
    breaker = CircuitBreaker("dependency_x", failure_threshold=2, recovery_seconds=60.0)

    breaker.record_failure(RuntimeError("first failure"), now=10.0)
    assert breaker.state == CircuitState.CLOSED
    assert breaker.allow_request(now=11.0) is True

    breaker.record_failure(RuntimeError("second failure"), now=12.0)
    assert breaker.state == CircuitState.OPEN
    assert breaker.allow_request(now=20.0) is False


def test_circuit_breaker_half_open_trial_closes_on_success() -> None:
    breaker = CircuitBreaker("dependency_y", failure_threshold=1, recovery_seconds=5.0)
    breaker.record_failure(RuntimeError("dependency unavailable"), now=10.0)

    assert breaker.allow_request(now=16.0) is True
    assert breaker.state == CircuitState.HALF_OPEN
    breaker.record_success()

    assert breaker.state == CircuitState.CLOSED
    assert breaker.failure_count == 0
    assert breaker.last_error is None


def test_circuit_breaker_rejects_parallel_half_open_trial() -> None:
    breaker = CircuitBreaker("dependency_z", failure_threshold=1, recovery_seconds=1.0)
    breaker.record_failure(RuntimeError("dependency unavailable"), now=1.0)

    assert breaker.allow_request(now=2.1) is True
    assert breaker.allow_request(now=2.2) is False


def test_circuit_breaker_async_call_retries_then_succeeds() -> None:
    breaker = CircuitBreaker("flaky_service", failure_threshold=2, recovery_seconds=1.0)
    attempts = {"count": 0}

    async def flaky() -> str:
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise TimeoutError("temporary failure")
        return "ok"

    result = asyncio.run(breaker.call(flaky, retries=1, retry_backoff_seconds=0.0))

    assert result == "ok"
    assert attempts["count"] == 2
    assert breaker.state == CircuitState.CLOSED


def test_circuit_breaker_call_is_rejected_when_circuit_is_open() -> None:
    breaker = CircuitBreaker("open_service", failure_threshold=1, recovery_seconds=60.0)
    breaker.record_failure(RuntimeError("dependency unavailable"), now=100.0)

    async def operation() -> str:
        return "unexpected"

    with pytest.raises(CircuitOpenError):
        asyncio.run(breaker.call(operation))


def test_circuit_breaker_timeout_counts_as_failure() -> None:
    breaker = CircuitBreaker("slow_service", failure_threshold=1, recovery_seconds=1.0)

    async def slow() -> str:
        await asyncio.sleep(0.05)
        return "late"

    with pytest.raises(asyncio.TimeoutError):
        asyncio.run(breaker.call(slow, timeout_seconds=0.001))

    assert breaker.state == CircuitState.OPEN
    assert breaker.failure_count == 1
