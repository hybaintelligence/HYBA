"""Memory-routed meta-controller with Hebbian reinforcement learning.

This module implements the autonomous meta-controller that uses:
- Non-Markovian memory kernel for learning from past failures
- Hebbian reinforcement for route probability updates
- Causal attribution for explainable routing decisions
- Circuit-breaker bounds for autonomous safety
- Universal passport system for audit logging

The controller learns from NACK (negative acknowledgment) events to avoid
repeating mistakes, and reinforces successful routes via ACK events.

Mathematical properties:
- Route probabilities are normalized to sum to 1.0
- Hebbian weights decay exponentially over time
- Circuit-breaker trips are deterministic given state
- Memory kernel provides non-Markovian context
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Mapping, Sequence

# Schema version for compatibility
MEMORY_ROUTER_SCHEMA_VERSION = "MEMORY_ROUTER_V1"


class RouteDecision(str, Enum):
    """Possible routing decisions."""

    EXECUTE = "execute"
    HALT = "halt"
    FALLBACK = "fallback"
    RETRY = "retry"


class CircuitBreakerState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit broken, blocking requests
    HALF_OPEN = "half_open"  # Testing if circuit should close


@dataclass(frozen=True)
class RouteResult:
    """Result of a routing decision."""

    decision: RouteDecision
    route: str
    explanation: Mapping[str, Any]
    confidence: float
    circuit_breaker_tripped: bool
    passport: Mapping[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    schema_version: str = MEMORY_ROUTER_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "decision": self.decision.value,
            "route": self.route,
            "explanation": dict(self.explanation),
            "confidence": self.confidence,
            "circuit_breaker_tripped": self.circuit_breaker_tripped,
            "passport": dict(self.passport),
            "timestamp": self.timestamp,
            "schema_version": self.schema_version,
        }


class CircuitBreaker:
    """Circuit breaker for autonomous safety bounds.

    The circuit breaker trips when failure rate exceeds threshold,
    preventing cascading failures.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_seconds: float = 60.0,
    ):
        """Initialize the circuit breaker.

        Args:
            failure_threshold: Number of failures before tripping
            timeout_seconds: Seconds before attempting to reset from OPEN to HALF_OPEN
        """
        self.failure_threshold = int(failure_threshold)
        self.timeout_seconds = float(timeout_seconds)
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.success_count = 0

    def would_trip(self, route: str, signal: Mapping[str, Any]) -> bool:
        """Check if circuit breaker would trip for this route/signal.

        Args:
            route: The route being considered
            signal: The signal to route

        Returns:
            True if circuit breaker would trip
        """
        if self.state == CircuitBreakerState.OPEN:
            # Check if timeout has elapsed
            if time.time() - self.last_failure_time > self.timeout_seconds:
                self.state = CircuitBreakerState.HALF_OPEN
                return False
            return True

        return False

    def record_success(self) -> None:
        """Record a successful operation."""
        if self.state == CircuitBreakerState.HALF_OPEN:
            # Reset to closed on success in half-open state
            self.state = CircuitBreakerState.CLOSED
            self.failure_count = 0

        self.success_count += 1
        # Decay failure count on success
        self.failure_count = max(0, self.failure_count - 1)

    def record_failure(self) -> None:
        """Record a failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN

    def reset(self) -> None:
        """Reset the circuit breaker to closed state."""
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0


class HebbianMemoryKernel:
    """Hebbian memory kernel for route learning.

    This implements non-Markovian memory by maintaining a history of
    NACK/ACK events and updating route probabilities via Hebbian reinforcement.

    Mathematical model:
    - Weight update: Δw = η * (reward - baseline)
    - Weight decay: w(t+1) = w(t) * decay_rate
    - Probability normalization: p_i = exp(w_i) / Σ_j exp(w_j)
    """

    def __init__(
        self,
        learning_rate: float = 0.1,
        decay_rate: float = 0.99,
        window_size: int = 100,
    ):
        """Initialize the Hebbian memory kernel.

        Args:
            learning_rate: Rate at which weights are updated
            decay_rate: Exponential decay rate for weights
            window_size: Number of historical events to maintain
        """
        self.learning_rate = float(learning_rate)
        self.decay_rate = float(decay_rate)
        self.window_size = int(window_size)
        self.weights: dict[str, float] = {}
        self.history: list[tuple[str, bool, float]] = []  # (route, success, timestamp)

    def current_route_weights(self) -> dict[str, float]:
        """Get current route weights with decay applied."""
        # Apply exponential decay
        decayed_weights = {}
        for route, weight in self.weights.items():
            decayed_weights[route] = weight * (self.decay_rate ** len(self.history))

        return decayed_weights

    def current_route_probabilities(self) -> dict[str, float]:
        """Get current route probabilities (softmax of weights)."""
        weights = self.current_route_weights()

        if not weights:
            return {}

        # Softmax normalization
        exp_weights = {route: 2.0 ** weight for route, weight in weights.items()}
        total = sum(exp_weights.values())

        if total == 0:
            return {route: 1.0 / len(weights) for route in weights}

        return {route: exp_weight / total for route, exp_weight in exp_weights.items()}

    def record_ack(self, signal: Mapping[str, Any], route: str) -> None:
        """Record a successful ACK event.

        Args:
            signal: The signal that was routed
            route: The route that succeeded
        """
        self._record_event(route, success=True)
        self._update_weights(route, success=True)

    def record_nack(self, signal: Mapping[str, Any], route: str) -> None:
        """Record a failed NACK event.

        Args:
            signal: The signal that failed to route
            route: The route that failed
        """
        self._record_event(route, success=False)
        self._update_weights(route, success=False)

    def _record_event(self, route: str, success: bool) -> None:
        """Record an event in history."""
        self.history.append((route, success, time.time()))

        # Maintain window size
        if len(self.history) > self.window_size:
            self.history.pop(0)

    def _update_weights(self, route: str, success: bool) -> None:
        """Update Hebbian weights based on success/failure."""
        if route not in self.weights:
            self.weights[route] = 0.0

        # Hebbian update: positive reinforcement for success, negative for failure
        reward = 1.0 if success else -1.0
        self.weights[route] += self.learning_rate * reward

        # Ensure weights don't grow unbounded
        self.weights[route] = max(-10.0, min(10.0, self.weights[route]))

    def add_route(self, route: str, initial_weight: float = 0.0) -> None:
        """Add a new route with optional initial weight."""
        self.weights[route] = float(initial_weight)

    def get_memory_certificate(self) -> dict[str, Any]:
        """Get a certificate describing the memory state."""
        return {
            "learning_rate": self.learning_rate,
            "decay_rate": self.decay_rate,
            "window_size": self.window_size,
            "num_routes": len(self.weights),
            "history_length": len(self.history),
            "recent_success_rate": self._recent_success_rate(),
            "weights": dict(self.weights),
        }

    def _recent_success_rate(self) -> float:
        """Calculate success rate over recent history."""
        if not self.history:
            return 0.0

        recent = self.history[-min(20, len(self.history)) :]
        successes = sum(1 for _, success, _ in recent if success)
        return successes / len(recent)


class MemoryRoutedController:
    """Meta-controller with memory-based routing and Hebbian learning.

    This controller integrates:
    - Hebbian memory kernel for learning from past routing decisions
    - Circuit breaker for autonomous safety bounds
    - Causal attribution for explainable decisions
    - Universal passport system for audit logging

    The controller routes signals based on learned probabilities, avoiding
    routes that have historically failed and reinforcing successful routes.
    """

    def __init__(
        self,
        memory_kernel: HebbianMemoryKernel,
        circuit_breaker: CircuitBreaker,
        causal_router: Any,  # CausalAttributionEngine from attribution module
        audit_log: Any,  # SharedAuditLog from audit module
        fallback_route: str = "fallback_safe",
    ):
        """Initialize the memory-routed controller.

        Args:
            memory_kernel: Hebbian memory kernel for learning
            circuit_breaker: Circuit breaker for safety bounds
            causal_router: Causal attribution engine for explanations
            audit_log: Shared audit log for passport logging
            fallback_route: Safe fallback route when primary routes fail
        """
        self.memory = memory_kernel
        self.breaker = circuit_breaker
        self.causal_router = causal_router
        self.audit = audit_log
        self.fallback_route = str(fallback_route)

    def route(self, signal: Mapping[str, Any]) -> RouteResult:
        """Route a signal using memory-based decision making.

        Args:
            signal: The signal to route

        Returns:
            RouteResult with decision, explanation, and audit passport
        """
        # Get current route probabilities from memory
        route_probs = self.memory.current_route_probabilities()

        # Select route based on probabilities
        candidate_route = self._select_route(route_probs, signal)

        # Get causal explanation for this routing decision
        explanation = self._get_causal_explanation(signal, candidate_route)

        # Check if circuit breaker would trip
        would_trip = self.breaker.would_trip(candidate_route, signal)

        if would_trip:
            # Circuit breaker tripped - halt and log
            return self._handle_circuit_breaker_trip(signal, candidate_route, explanation)

        # Execute the route
        return self._execute_route(signal, candidate_route, explanation)

    def _select_route(
        self,
        route_probs: dict[str, float],
        signal: Mapping[str, Any],
    ) -> str:
        """Select a route based on probabilities.

        Args:
            route_probs: Dictionary of route -> probability
            signal: The signal being routed

        Returns:
            Selected route
        """
        if not route_probs:
            # No learned routes, use fallback
            return self.fallback_route

        # Select route with highest probability
        # (could be stochastic with proper seeding)
        return max(route_probs.items(), key=lambda kv: kv[1])[0]

    def _get_causal_explanation(
        self,
        signal: Mapping[str, Any],
        route: str,
    ) -> Mapping[str, Any]:
        """Get causal explanation for routing decision.

        Args:
            signal: The signal being routed
            route: The selected route

        Returns:
            Causal explanation dictionary
        """
        try:
            # Use causal router if available
            explanation = self.causal_router.explain(
                event=signal,
                claim={"route": route, "type": "routing_decision"},
            )
            return explanation.to_dict()
        except Exception:
            # Fallback to simple explanation if causal router fails
            return {
                "route": route,
                "confidence": 0.5,
                "reason": "causal_analysis_unavailable",
            }

    def _handle_circuit_breaker_trip(
        self,
        signal: Mapping[str, Any],
        route: str,
        explanation: Mapping[str, Any],
    ) -> RouteResult:
        """Handle circuit breaker trip by halting and logging.

        Args:
            signal: The signal that triggered the trip
            route: The route that would have been taken
            explanation: Causal explanation for the decision

        Returns:
            RouteResult with HALT decision
        """
        # Create passport for circuit breaker trip
        from python_backend.core.audit.universal_passport import (
            EpistemicBound,
            make_circuit_breaker_passport,
        )

        passport = make_circuit_breaker_passport(
            signal=signal,
            route=route,
            explanation=explanation,
        )

        # Log to audit log
        try:
            self.audit.append(passport)
        except Exception:
            # Continue even if audit logging fails
            pass

        # Record NACK in memory
        self.memory.record_nack(signal, route)

        return RouteResult(
            decision=RouteDecision.HALT,
            route=route,
            explanation=explanation,
            confidence=0.0,
            circuit_breaker_tripped=True,
            passport=passport.to_dict(),
        )

    def _execute_route(
        self,
        signal: Mapping[str, Any],
        route: str,
        explanation: Mapping[str, Any],
    ) -> RouteResult:
        """Execute a route and record the result.

        Args:
            signal: The signal to route
            route: The selected route
            explanation: Causal explanation

        Returns:
            RouteResult with EXECUTE decision
        """
        # In a real implementation, this would actually execute the route
        # For now, we simulate success/failure based on route quality

        # Simulate execution (would be actual route execution in production)
        route_probs = self.memory.current_route_probabilities()
        route_quality = route_probs.get(route, 0.5)

        # Simulate success based on route quality
        success = route_quality > 0.3 or (route == self.fallback_route)

        if success:
            # Record ACK in memory
            self.memory.record_ack(signal, route)
            self.breaker.record_success()

            confidence = route_quality
            decision = RouteDecision.EXECUTE
        else:
            # Record NACK in memory
            self.memory.record_nack(signal, route)
            self.breaker.record_failure()

            confidence = 0.0
            decision = RouteDecision.FALLBACK

        # Create passport for routing decision
        from python_backend.core.audit.universal_passport import (
            EpistemicBound,
            make_passport,
        )

        passport = make_passport(
            subsystem="meta_controller",
            claim_type="routing_decision",
            payload={
                "signal": signal,
                "route": route,
                "success": success,
                "explanation": explanation,
            },
            epistemic_bounds=[
                EpistemicBound.NO_GUARANTEE_CORRECTNESS.value,
                EpistemicBound.NO_DETERMINISTIC_OUTCOME.value,
            ],
        )

        # Log to audit log
        try:
            self.audit.append(passport)
        except Exception:
            # Continue even if audit logging fails
            pass

        return RouteResult(
            decision=decision,
            route=route,
            explanation=explanation,
            confidence=confidence,
            circuit_breaker_tripped=False,
            passport=passport.to_dict(),
        )

    def get_memory_state(self) -> dict[str, Any]:
        """Get the current memory state."""
        return self.memory.get_memory_certificate()

    def get_circuit_breaker_state(self) -> dict[str, Any]:
        """Get the current circuit breaker state."""
        return {
            "state": self.breaker.state.value,
            "failure_count": self.breaker.failure_count,
            "success_count": self.breaker.success_count,
            "last_failure_time": self.breaker.last_failure_time,
            "failure_threshold": self.breaker.failure_threshold,
            "timeout_seconds": self.breaker.timeout_seconds,
        }

    def reset_circuit_breaker(self) -> None:
        """Reset the circuit breaker to closed state."""
        self.breaker.reset()


__all__ = [
    "MEMORY_ROUTER_SCHEMA_VERSION",
    "RouteDecision",
    "CircuitBreakerState",
    "RouteResult",
    "CircuitBreaker",
    "HebbianMemoryKernel",
    "MemoryRoutedController",
]
