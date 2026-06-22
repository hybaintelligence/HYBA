"""Reliability helpers for graceful dependency degradation."""

from __future__ import annotations

import logging
from typing import Awaitable, Callable, TypeVar

from fastapi import HTTPException

from hyba_genesis_api.core.telemetry import set_reliability_circuit_state

T = TypeVar("T")


class BackendDependencyError(RuntimeError):
    """Raised when a mandatory backend dependency is unavailable."""


async def execute_with_circuit_breaker(
    circuit_name: str,
    operation: Callable[[], Awaitable[T]],
    *,
    retry_after_seconds: int = 30,
) -> T:
    """Run an async dependency operation and return HTTP 503 on dependency failure."""

    try:
        set_reliability_circuit_state(circuit_name, "closed")
        return await operation()
    except (BackendDependencyError, ConnectionError, TimeoutError) as exc:
        set_reliability_circuit_state(circuit_name, "open")
        logging.warning(
            "Backend dependency degraded",
            extra={"circuit": circuit_name, "error": str(exc)},
        )
        raise HTTPException(
            status_code=503,
            detail={"status": "degraded", "dependency": circuit_name},
            headers={"Retry-After": str(retry_after_seconds)},
        ) from exc
