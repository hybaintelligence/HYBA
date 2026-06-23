"""Shared helpers for backend API surface tests."""

from __future__ import annotations

import os
import time

os.environ.setdefault("JWT_SECRET", "backend-api-test-secret")
os.environ.setdefault("HYBA_ENV", "test")
os.environ.setdefault("NODE_ENV", "test")

import pytest

fastapi = pytest.importorskip(
    "fastapi", reason="FastAPI backend dependencies are not installed"
)
from fastapi.testclient import TestClient

from hyba_genesis_api.auth.jwt_handler import get_jwt_manager
from hyba_genesis_api.core.midas_controls import MiningState
from hyba_genesis_api.main import app


def reset_backend_api_test_state() -> None:
    """Reset process-global mining control-plane state between API tests.

    The mining API intentionally owns durable process globals for active pool state,
    MIDAS transition state, request idempotency, and backpressure. Unit tests must
    start from a deterministic command-room state or later tests inherit prior
    control-plane decisions and fail for the wrong reason.
    """

    from hyba_genesis_api.api import mining
    from hyba_genesis_api.core import midas_controls

    mining._ACTIVE_CONNECTION = None  # noqa: SLF001
    mining._JOBS_SUBMITTED = 0  # noqa: SLF001
    mining._SHARES_ACCEPTED = 0  # noqa: SLF001
    mining._SHARES_REJECTED = 0  # noqa: SLF001
    mining._DAEMON_STARTED = False  # noqa: SLF001
    mining._PYTHIA_PROCESS = None  # noqa: SLF001

    state_machine = midas_controls.midas_state_machine
    with state_machine._lock:  # noqa: SLF001
        state_machine.current_state = MiningState.IDLE
        state_machine.previous_state = None
        state_machine.transition_history.clear()
        state_machine.state_entry_time = time.monotonic()
        state_machine.metrics = {
            "transitions_total": 0,
            "invalid_transitions_total": 0,
        }

    limiter = midas_controls.midas_rate_limiter
    with limiter._lock:  # noqa: SLF001
        limiter.tokens = float(limiter.burst_capacity)
        limiter.updated_at = time.monotonic()
        limiter.allowed_total = 0
        limiter.rejected_total = 0

    guard = midas_controls.midas_backpressure_guard
    guard.inflight = 0
    guard.queue_depth = 0
    guard.rejected_total = 0

    tracker = midas_controls.mining_request_tracker
    with tracker._lock:  # noqa: SLF001
        tracker.requests.clear()
        tracker.idempotency_keys.clear()
        tracker.last_cleanup = time.time()


def make_client() -> TestClient:
    reset_backend_api_test_state()
    return TestClient(app)


def bearer_headers(*roles: str) -> dict[str, str]:
    selected_roles = list(roles) or ["ceo", "mining:read", "mining:operate"]
    token = get_jwt_manager().create_access_token(
        user_id="backend-api-test-user",
        username="backend-api-test-user",
        roles=selected_roles,
    )
    return {
        "Authorization": f"Bearer {token}",
        "X-Request-ID": "backend-api-test-request",
    }
