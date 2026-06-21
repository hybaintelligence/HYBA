"""Reliability controls for production-facing HYBA workflows.

This module provides a deterministic, dependency-light circuit breaker and retry
wrapper for API, mining, governance, and autonomous workflow calls. It is not a
replacement for cloud load balancers or service meshes; it is the application
layer safety net that keeps local, Docker, and single-region cloud deployments
from repeatedly hammering known-bad dependencies.
"""

from __future__ import annotations

import asyncio
import inspect
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable, TypeVar

T = TypeVar("T")


class CircuitState(str, Enum):
    CLOSED = "closed"
    HALF_OPEN = "half_open"
    OPEN = "open"


class CircuitOpenError(RuntimeError):
    """Raised when a call is blocked because the circuit is open."""


@dataclass
class CircuitBreaker:
    """Small circuit breaker with timeout and retry support.

    The breaker opens after ``failure_threshold`` consecutive failures. Once the
    cooldown expires, it allows one half-open trial. A successful trial closes the
    circuit; a failed trial re-opens it.
    """

    name: str
    failure_threshold: int = 3
    recovery_seconds: float = 30.0
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    opened_at: float | None = None
    last_error: str | None = None
    _half_open_trial_inflight: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.failure_threshold < 1:
            raise ValueError("failure_threshold must be >= 1")
        if self.recovery_seconds <= 0:
            raise ValueError("recovery_seconds must be > 0")
        self._publish_state()

    def allow_request(self, now: float | None = None) -> bool:
        now = time.monotonic() if now is None else now
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if self.opened_at is not None and now - self.opened_at >= self.recovery_seconds:
                self.state = CircuitState.HALF_OPEN
                self._half_open_trial_inflight = False
                self._publish_state()
            else:
                return False
        if self.state == CircuitState.HALF_OPEN:
            if self._half_open_trial_inflight:
                return False
            self._half_open_trial_inflight = True
            return True
        return False

    def record_success(self) -> None:
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.opened_at = None
        self.last_error = None
        self._half_open_trial_inflight = False
        self._publish_state()

    def record_failure(self, exc: BaseException, now: float | None = None) -> None:
        self.failure_count += 1
        self.last_error = f"{exc.__class__.__name__}: {exc}"
        self._half_open_trial_inflight = False
        if self.state == CircuitState.HALF_OPEN or self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.opened_at = time.monotonic() if now is None else now
        self._publish_state()

    async def call(
        self,
        operation: Callable[..., T | Awaitable[T]],
        *args: Any,
        timeout_seconds: float | None = None,
        retries: int = 0,
        retry_backoff_seconds: float = 0.05,
        **kwargs: Any,
    ) -> T:
        """Run ``operation`` behind the circuit breaker.

        ``retries`` counts additional attempts after the first failure. Timeout
        applies per attempt. The final failure is recorded against the circuit.
        """

        if retries < 0:
            raise ValueError("retries must be >= 0")
        if retry_backoff_seconds < 0:
            raise ValueError("retry_backoff_seconds must be >= 0")
        if not self.allow_request():
            raise CircuitOpenError(f"Circuit {self.name!r} is open")

        attempts = retries + 1
        last_error: BaseException | None = None
        for attempt in range(attempts):
            try:
                result = operation(*args, **kwargs)
                if inspect.isawaitable(result):
                    if timeout_seconds is None:
                        value = await result  # type: ignore[misc]
                    else:
                        value = await asyncio.wait_for(result, timeout=timeout_seconds)  # type: ignore[arg-type]
                else:
                    value = result
                self.record_success()
                return value  # type: ignore[return-value]
            except Exception as exc:  # noqa: BLE001 - final failure must trip the breaker
                last_error = exc
                if attempt + 1 < attempts:
                    await asyncio.sleep(retry_backoff_seconds * (attempt + 1))
                    continue
                self.record_failure(exc)
                raise
        assert last_error is not None
        self.record_failure(last_error)
        raise last_error

    def snapshot(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "opened_at": self.opened_at,
            "last_error": self.last_error,
        }

    def _publish_state(self) -> None:
        try:
            from hyba_genesis_api.core.telemetry import set_reliability_circuit_state

            set_reliability_circuit_state(self.name, self.state.value)
        except Exception:
            # Resilience controls must remain available even if telemetry is not
            # configured in a local test process.
            return
