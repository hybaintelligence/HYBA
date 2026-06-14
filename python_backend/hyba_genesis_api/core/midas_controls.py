"""Production MIDAS controls for HYBA_FULLSTACK mining operations.

This module keeps mining runtime safety local to HYBA_FULLSTACK while preserving
regulatory separation from HYBA_Unified_Backend.  It intentionally has no
external dependencies so FastAPI routes, tests, and future worker contracts can
exercise the same production invariants.
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from threading import RLock
from typing import Any, Optional


class MiningState(Enum):
    """Canonical production mining states plus compatibility aliases."""

    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"

    # Backward-compatible aliases must resolve to canonical states.
    INITIALIZING = "starting"
    MINING = "running"


class StateTransitionError(Exception):
    """Raised when an invalid production state transition is attempted."""


@dataclass(frozen=True)
class StateTransition:
    transition_id: str
    from_state: MiningState
    to_state: MiningState
    timestamp: datetime
    reason: str
    request_id: str
    duration_in_previous_state_ms: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class StateMachineConfig:
    require_request_id: bool = True
    allowed_transitions: dict[MiningState, set[MiningState]] = field(
        default_factory=lambda: {
            MiningState.IDLE: {MiningState.STARTING},
            MiningState.STARTING: {MiningState.RUNNING},
            MiningState.RUNNING: {MiningState.STOPPING},
            MiningState.STOPPING: {MiningState.STOPPED},
            MiningState.STOPPED: {MiningState.STARTING},
        }
    )


class MIDASStateMachine:
    """Strict production state machine for mining runtime control."""

    def __init__(self, config: StateMachineConfig | None = None):
        self.config = config or StateMachineConfig()
        self.current_state = MiningState.IDLE
        self.previous_state: MiningState | None = None
        self.transition_history: list[StateTransition] = []
        self.state_entry_time = time.monotonic()
        self._lock = RLock()
        self.metrics: dict[str, int] = {
            "transitions_total": 0,
            "invalid_transitions_total": 0,
        }

    def transition(
        self,
        to_state: MiningState,
        *,
        request_id: str | None = None,
        reason: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> StateTransition:
        metadata = dict(metadata or {})
        request_id = request_id or metadata.get("request_id")
        with self._lock:
            if self.config.require_request_id and not request_id:
                self.metrics["invalid_transitions_total"] += 1
                raise StateTransitionError(
                    "MIDAS state transitions require a request_id"
                )

            if to_state not in self.config.allowed_transitions.get(
                self.current_state, set()
            ):
                self.metrics["invalid_transitions_total"] += 1
                valid = [
                    s.value
                    for s in self.config.allowed_transitions.get(
                        self.current_state, set()
                    )
                ]
                raise StateTransitionError(
                    f"Invalid state transition from {self.current_state.value} to {to_state.value}. "
                    f"Valid transitions from {self.current_state.value}: {valid}"
                )

            now = time.monotonic()
            transition = StateTransition(
                transition_id=str(uuid.uuid4()),
                from_state=self.current_state,
                to_state=to_state,
                timestamp=datetime.now(UTC),
                reason=reason,
                request_id=str(request_id),
                duration_in_previous_state_ms=(now - self.state_entry_time) * 1000,
                metadata=metadata,
            )
            self.previous_state = self.current_state
            self.current_state = to_state
            self.state_entry_time = time.monotonic()
            self.transition_history.append(transition)
            self.metrics["transitions_total"] += 1
            metric_name = f"transition_{transition.from_state.value}_to_{transition.to_state.value}_total"
            self.metrics[metric_name] = self.metrics.get(metric_name, 0) + 1
            return transition

    def force_transition(
        self,
        to_state: MiningState,
        *,
        request_id: str | None = None,
        reason: str = "forced",
    ) -> StateTransition:
        with self._lock:
            self.metrics["invalid_transitions_total"] += 1
        raise StateTransitionError(
            f"Forced transition to {to_state.value} is disabled in production: {reason}; request_id={request_id}"
        )

    def get_state(self) -> MiningState:
        with self._lock:
            return self.current_state

    def get_transition_history(self, limit: int = 100) -> list[StateTransition]:
        with self._lock:
            return list(self.transition_history[-limit:])

    def validate_state_machine(self) -> dict[str, Any]:
        canonical = [
            MiningState.IDLE,
            MiningState.STARTING,
            MiningState.RUNNING,
            MiningState.STOPPING,
            MiningState.STOPPED,
        ]
        errors: list[str] = []
        with self._lock:
            current_state = self.current_state
            history = list(self.transition_history)
            metrics = dict(self.metrics)
        if current_state not in canonical:
            errors.append(f"non-canonical state: {current_state.value}")
        for transition in history:
            if transition.to_state not in self.config.allowed_transitions.get(
                transition.from_state, set()
            ):
                errors.append(
                    f"invalid historical transition: {transition.from_state.value}->{transition.to_state.value}"
                )
            if not transition.request_id:
                errors.append(
                    f"transition {transition.transition_id} missing request_id"
                )
        return {
            "valid": not errors,
            "current_state": current_state.value,
            "canonical_path": [state.value for state in canonical],
            "errors": errors,
            "transition_count": len(history),
            "metrics": metrics,
        }


class RateLimitExceededError(Exception):
    def __init__(self, retry_after_seconds: float, request_id: str | None = None):
        self.retry_after_seconds = max(retry_after_seconds, 0.0)
        self.request_id = request_id
        super().__init__(
            f"MIDAS rate limit exceeded; retry after {self.retry_after_seconds:.3f}s"
        )

    def to_response_body(self) -> dict[str, Any]:
        return {
            "error": "rate_limited",
            "retryable": True,
            "retry_after_seconds": self.retry_after_seconds,
            "request_id": self.request_id,
        }


class BackpressureError(Exception):
    def __init__(self, message: str, request_id: str | None = None):
        self.request_id = request_id
        super().__init__(message)

    def to_response_body(self) -> dict[str, Any]:
        return {
            "error": "backpressure_active",
            "retryable": True,
            "request_id": self.request_id,
            "detail": str(self),
        }


@dataclass
class TokenBucketRateLimiter:
    rate_per_second: float = 10.0
    burst_capacity: int = 10
    tokens: float = field(init=False)
    updated_at: float = field(default_factory=time.monotonic)
    allowed_total: int = 0
    rejected_total: int = 0
    _lock: RLock = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.rate_per_second <= 0:
            raise ValueError("rate_per_second must be positive")
        if self.burst_capacity <= 0:
            raise ValueError("burst_capacity must be positive")
        self.tokens = float(self.burst_capacity)
        object.__setattr__(self, "_lock", RLock())

    def allow(self, request_id: str | None = None) -> bool:
        with self._lock:
            now = time.monotonic()
            elapsed = max(now - self.updated_at, 0.0)
            self.tokens = min(
                self.burst_capacity, self.tokens + elapsed * self.rate_per_second
            )
            self.updated_at = now
            if self.tokens >= 1.0:
                self.tokens -= 1.0
                self.allowed_total += 1
                return True
            self.rejected_total += 1
            retry_after = (1.0 - self.tokens) / self.rate_per_second
        raise RateLimitExceededError(retry_after, request_id=request_id)

    def metrics(self) -> dict[str, Any]:
        with self._lock:
            return {
                "scope": "process",
                "rate_per_second": self.rate_per_second,
                "burst_capacity": self.burst_capacity,
                "tokens_available": round(self.tokens, 6),
                "allowed_total": self.allowed_total,
                "rejected_total": self.rejected_total,
            }


@dataclass
class BackpressureGuard:
    max_inflight: int = 25
    max_queue_depth: int = 100
    inflight: int = 0
    queue_depth: int = 0
    rejected_total: int = 0

    def admit(self, request_id: Optional[str] = None) -> None:
        if (
            self.inflight >= self.max_inflight
            or self.queue_depth >= self.max_queue_depth
        ):
            self.rejected_total += 1
            raise BackpressureError(
                f"MIDAS backpressure active: inflight={self.inflight}/{self.max_inflight}, "
                f"queue_depth={self.queue_depth}/{self.max_queue_depth}",
                request_id=request_id,
            )
        self.inflight += 1

    def release(self) -> None:
        self.inflight = max(self.inflight - 1, 0)

    def metrics(self) -> dict[str, Any]:
        return {
            "scope": "process",
            "max_inflight": self.max_inflight,
            "max_queue_depth": self.max_queue_depth,
            "inflight": self.inflight,
            "queue_depth": self.queue_depth,
            "rejected_total": self.rejected_total,
        }


class RequestStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


TERMINAL_STATUSES = {
    RequestStatus.COMPLETED,
    RequestStatus.FAILED,
    RequestStatus.CANCELLED,
}


@dataclass
class MiningRequest:
    request_id: str
    operation_type: str
    parameters: dict[str, Any]
    status: RequestStatus
    created_at: datetime
    updated_at: datetime
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    idempotency_key: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        return data


class MiningRequestTracker:
    """Thread-safe request tracker with idempotency support."""

    def __init__(self, request_ttl_seconds: int = 3600):
        if request_ttl_seconds <= 0:
            raise ValueError("request_ttl_seconds must be positive")
        self.requests: dict[str, MiningRequest] = {}
        self.idempotency_keys: dict[str, str] = {}
        self.request_ttl_seconds = request_ttl_seconds
        self.last_cleanup = time.time()
        self._lock = RLock()

    def generate_request_id(self) -> str:
        return f"mining_req_{int(time.time())}_{uuid.uuid4().hex[:16]}"

    def generate_idempotency_key(
        self, operation_type: str, parameters: dict[str, Any]
    ) -> str:
        try:
            params_str = json.dumps(
                parameters, sort_keys=True, separators=(",", ":"), default=str
            )
        except TypeError:
            params_str = repr(sorted(parameters.items()))
        return hashlib.sha256(
            f"{operation_type}:{params_str}".encode("utf-8")
        ).hexdigest()

    def create_request(
        self,
        operation_type: str,
        parameters: dict[str, Any],
        idempotency_key: Optional[str] = None,
    ) -> MiningRequest:
        with self._lock:
            idempotency_key = idempotency_key or self.generate_idempotency_key(
                operation_type, parameters
            )
            existing_id = self.idempotency_keys.get(idempotency_key)
            if existing_id:
                existing = self.requests.get(existing_id)
                if existing and existing.status != RequestStatus.FAILED:
                    return existing
            now = datetime.now(UTC)
            request = MiningRequest(
                request_id=self.generate_request_id(),
                operation_type=operation_type,
                parameters=dict(parameters),
                status=RequestStatus.PENDING,
                created_at=now,
                updated_at=now,
                idempotency_key=idempotency_key,
            )
            self.requests[request.request_id] = request
            self.idempotency_keys[idempotency_key] = request.request_id
            return request

    def update_request_status(
        self,
        request_id: str,
        status: RequestStatus,
        *,
        result: Optional[dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> bool:
        with self._lock:
            request = self.requests.get(request_id)
            if request is None:
                return False
            request.status = status
            request.updated_at = datetime.now(UTC)
            if result is not None:
                request.result = result
            if error is not None:
                request.error = error
            return True

    def cleanup_expired_requests(self) -> int:
        with self._lock:
            cutoff = datetime.now(UTC) - timedelta(seconds=self.request_ttl_seconds)
            expired_ids = [
                rid for rid, req in self.requests.items() if req.created_at < cutoff
            ]
            for request_id in expired_ids:
                request = self.requests.pop(request_id)
                if (
                    request.idempotency_key
                    and self.idempotency_keys.get(request.idempotency_key) == request_id
                ):
                    del self.idempotency_keys[request.idempotency_key]
            self.last_cleanup = time.time()
            return len(expired_ids)

    def get_stats(self) -> dict[str, Any]:
        with self._lock:
            status_counts: dict[str, int] = {}
            for request in self.requests.values():
                status_counts[request.status.value] = (
                    status_counts.get(request.status.value, 0) + 1
                )
            return {
                "total_requests": len(self.requests),
                "status_breakdown": status_counts,
                "idempotency_keys_tracked": len(self.idempotency_keys),
                "request_ttl_seconds": self.request_ttl_seconds,
                "last_cleanup": datetime.fromtimestamp(
                    self.last_cleanup, tz=UTC
                ).isoformat(),
            }


midas_state_machine = MIDASStateMachine()
midas_rate_limiter = TokenBucketRateLimiter()
midas_backpressure_guard = BackpressureGuard()
mining_request_tracker = MiningRequestTracker()
