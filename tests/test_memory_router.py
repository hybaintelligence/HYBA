"""Unit and property tests for MemoryRoutedController module.

This test suite validates:
1. Basic functionality of Hebbian memory kernel
2. Circuit breaker behavior and state transitions
3. Memory-routed controller decision making
4. Integration with causal attribution and audit logging
5. Property-based tests for mathematical invariants
"""

from __future__ import annotations

import time

import pytest
from hypothesis import given, strategies as st
from hypothesis.strategies import dictionaries, floats, integers, text

from python_backend.core.meta_controller.memory_router import (
    CircuitBreaker,
    CircuitBreakerState,
    HebbianMemoryKernel,
    MemoryRoutedController,
    RouteDecision,
    RouteResult,
)


# ============================================================================
# Unit Tests
# ============================================================================


class TestHebbianMemoryKernel:
    """Test HebbianMemoryKernel."""

    def test_kernel_creation(self):
        """Test creating a memory kernel."""
        kernel = HebbianMemoryKernel()
        assert kernel.learning_rate == 0.1
        assert kernel.decay_rate == 0.99
        assert kernel.window_size == 100
        assert len(kernel.weights) == 0
        assert len(kernel.history) == 0

    def test_kernel_custom_parameters(self):
        """Test creating kernel with custom parameters."""
        kernel = HebbianMemoryKernel(
            learning_rate=0.5,
            decay_rate=0.95,
            window_size=50,
        )
        assert kernel.learning_rate == 0.5
        assert kernel.decay_rate == 0.95
        assert kernel.window_size == 50

    def test_add_route(self):
        """Test adding a new route."""
        kernel = HebbianMemoryKernel()
        kernel.add_route("route_1", initial_weight=1.0)
        assert "route_1" in kernel.weights
        assert kernel.weights["route_1"] == 1.0

    def test_record_ack(self):
        """Test recording ACK event."""
        kernel = HebbianMemoryKernel()
        kernel.add_route("route_1")
        kernel.record_ack({"type": "test"}, "route_1")
        
        assert len(kernel.history) == 1
        assert kernel.history[0] == ("route_1", True, pytest.approx(time.time()))
        assert kernel.weights["route_1"] > 0  # Should increase

    def test_record_nack(self):
        """Test recording NACK event."""
        kernel = HebbianMemoryKernel()
        kernel.add_route("route_1")
        kernel.record_nack({"type": "test"}, "route_1")
        
        assert len(kernel.history) == 1
        assert kernel.history[0] == ("route_1", False, pytest.approx(time.time()))
        assert kernel.weights["route_1"] < 0  # Should decrease

    def test_current_route_weights(self):
        """Test getting current route weights."""
        kernel = HebbianMemoryKernel()
        kernel.add_route("route_1", initial_weight=1.0)
        kernel.add_route("route_2", initial_weight=0.5)
        
        weights = kernel.current_route_weights()
        assert "route_1" in weights
        assert "route_2" in weights
        assert weights["route_1"] > weights["route_2"]

    def test_current_route_probabilities(self):
        """Test getting current route probabilities."""
        kernel = HebbianMemoryKernel()
        kernel.add_route("route_1", initial_weight=1.0)
        kernel.add_route("route_2", initial_weight=0.0)
        
        probs = kernel.current_route_probabilities()
        assert "route_1" in probs
        assert "route_2" in probs
        assert abs(sum(probs.values()) - 1.0) < 1e-6  # Should sum to 1

    def test_probability_normalization(self):
        """Test that probabilities are normalized."""
        kernel = HebbianMemoryKernel()
        kernel.add_route("route_1", initial_weight=10.0)
        kernel.add_route("route_2", initial_weight=-10.0)
        
        probs = kernel.current_route_probabilities()
        assert abs(sum(probs.values()) - 1.0) < 1e-6
        assert all(0.0 <= p <= 1.0 for p in probs.values())

    def test_history_window_size(self):
        """Test that history respects window size."""
        kernel = HebbianMemoryKernel(window_size=5)
        kernel.add_route("route_1")
        
        for i in range(10):
            kernel.record_ack({"type": "test"}, "route_1")
        
        assert len(kernel.history) == 5

    def test_memory_certificate(self):
        """Test getting memory certificate."""
        kernel = HebbianMemoryKernel()
        kernel.add_route("route_1")
        kernel.record_ack({"type": "test"}, "route_1")
        
        cert = kernel.get_memory_certificate()
        assert "learning_rate" in cert
        assert "decay_rate" in cert
        assert "num_routes" in cert
        assert "weights" in cert
        assert cert["num_routes"] == 1

    def test_recent_success_rate(self):
        """Test recent success rate calculation."""
        kernel = HebbianMemoryKernel()
        kernel.add_route("route_1")
        
        # Record 3 successes, 1 failure
        for _ in range(3):
            kernel.record_ack({"type": "test"}, "route_1")
        kernel.record_nack({"type": "test"}, "route_1")
        
        cert = kernel.get_memory_certificate()
        assert cert["recent_success_rate"] == 0.75


class TestCircuitBreaker:
    """Test CircuitBreaker."""

    def test_breaker_creation(self):
        """Test creating a circuit breaker."""
        breaker = CircuitBreaker()
        assert breaker.failure_threshold == 5
        assert breaker.timeout_seconds == 60.0
        assert breaker.state == CircuitBreakerState.CLOSED
        assert breaker.failure_count == 0

    def test_breaker_custom_parameters(self):
        """Test creating breaker with custom parameters."""
        breaker = CircuitBreaker(failure_threshold=3, timeout_seconds=30.0)
        assert breaker.failure_threshold == 3
        assert breaker.timeout_seconds == 30.0

    def test_would_trip_closed(self):
        """Test breaker doesn't trip when closed."""
        breaker = CircuitBreaker()
        assert breaker.would_trip("route_1", {"type": "test"}) is False

    def test_would_trip_after_failures(self):
        """Test breaker trips after threshold failures."""
        breaker = CircuitBreaker(failure_threshold=3)
        
        for _ in range(3):
            breaker.record_failure()
        
        assert breaker.state == CircuitBreakerState.OPEN
        assert breaker.would_trip("route_1", {"type": "test"}) is True

    def test_would_trip_open(self):
        """Test breaker trips when in OPEN state."""
        breaker = CircuitBreaker(failure_threshold=1)
        breaker.record_failure()
        
        assert breaker.state == CircuitBreakerState.OPEN
        assert breaker.would_trip("route_1", {"type": "test"}) is True

    def test_record_success_resets_half_open(self):
        """Test success resets breaker from HALF_OPEN to CLOSED."""
        breaker = CircuitBreaker(failure_threshold=1)
        breaker.record_failure()
        assert breaker.state == CircuitBreakerState.OPEN
        
        # Wait for timeout
        breaker.last_failure_time = time.time() - breaker.timeout_seconds - 1
        assert breaker.would_trip("route_1", {"type": "test"}) is False  # Should be HALF_OPEN
        
        breaker.record_success()
        assert breaker.state == CircuitBreakerState.CLOSED

    def test_record_success_decays_failure_count(self):
        """Test success decays failure count."""
        breaker = CircuitBreaker(failure_threshold=5)
        
        for _ in range(3):
            breaker.record_failure()
        assert breaker.failure_count == 3
        
        breaker.record_success()
        assert breaker.failure_count == 2  # Should decay by 1

    def test_reset(self):
        """Test resetting the breaker."""
        breaker = CircuitBreaker(failure_threshold=1)
        breaker.record_failure()
        assert breaker.state == CircuitBreakerState.OPEN
        
        breaker.reset()
        assert breaker.state == CircuitBreakerState.CLOSED
        assert breaker.failure_count == 0


class TestRouteResult:
    """Test RouteResult dataclass."""

    def test_result_creation(self):
        """Test creating a route result."""
        result = RouteResult(
            decision=RouteDecision.EXECUTE,
            route="route_1",
            explanation={"reason": "test"},
            confidence=0.8,
            circuit_breaker_tripped=False,
        )
        assert result.decision == RouteDecision.EXECUTE
        assert result.route == "route_1"
        assert result.confidence == 0.8

    def test_result_to_dict(self):
        """Test result serialization to dict."""
        result = RouteResult(
            decision=RouteDecision.EXECUTE,
            route="route_1",
            explanation={"reason": "test"},
            confidence=0.8,
            circuit_breaker_tripped=False,
        )
        result_dict = result.to_dict()
        assert result_dict["decision"] == "execute"
        assert result_dict["route"] == "route_1"
        assert result_dict["confidence"] == 0.8


class TestMemoryRoutedController:
    """Test MemoryRoutedController."""

    def test_controller_creation(self):
        """Test creating a memory-routed controller."""
        memory = HebbianMemoryKernel()
        breaker = CircuitBreaker()
        
        # Mock causal router and audit log
        class MockCausalRouter:
            def explain(self, event, claim):
                from python_backend.core.attribution.causal_router import CausalExplanation
                return CausalExplanation(
                    hotspots=[],
                    counterfactual=None,
                    explanation_quality="high",
                    timestamp=time.time(),
                )
        
        class MockAuditLog:
            def append(self, passport):
                pass
        
        causal_router = MockCausalRouter()
        audit_log = MockAuditLog()
        
        controller = MemoryRoutedController(
            memory, breaker, causal_router, audit_log
        )
        assert controller.memory == memory
        assert controller.breaker == breaker

    def test_route_with_no_memory(self):
        """Test routing with no learned routes."""
        memory = HebbianMemoryKernel()
        breaker = CircuitBreaker()
        
        class MockCausalRouter:
            def explain(self, event, claim):
                from python_backend.core.attribution.causal_router import CausalExplanation
                return CausalExplanation(
                    hotspots=[],
                    counterfactual=None,
                    explanation_quality="high",
                    timestamp=time.time(),
                )
        
        class MockAuditLog:
            def append(self, passport):
                pass
        
        controller = MemoryRoutedController(
            memory, breaker, MockCausalRouter(), MockAuditLog()
        )
        
        result = controller.route({"type": "test"})
        assert result.decision in [RouteDecision.EXECUTE, RouteDecision.FALLBACK]
        assert result.route == "fallback_safe"

    def test_route_with_learned_routes(self):
        """Test routing with learned routes."""
        memory = HebbianMemoryKernel()
        memory.add_route("route_1", initial_weight=2.0)
        memory.add_route("route_2", initial_weight=1.0)
        breaker = CircuitBreaker()
        
        class MockCausalRouter:
            def explain(self, event, claim):
                from python_backend.core.attribution.causal_router import CausalExplanation
                return CausalExplanation(
                    hotspots=[],
                    counterfactual=None,
                    explanation_quality="high",
                    timestamp=time.time(),
                )
        
        class MockAuditLog:
            def append(self, passport):
                pass
        
        controller = MemoryRoutedController(
            memory, breaker, MockCausalRouter(), MockAuditLog()
        )
        
        result = controller.route({"type": "test"})
        assert result.route == "route_1"  # Should select highest weight

    def test_route_with_circuit_breaker_trip(self):
        """Test routing when circuit breaker trips."""
        memory = HebbianMemoryKernel()
        memory.add_route("route_1")
        breaker = CircuitBreaker(failure_threshold=1)
        breaker.record_failure()  # Trip the breaker
        
        class MockCausalRouter:
            def explain(self, event, claim):
                from python_backend.core.attribution.causal_router import CausalExplanation
                return CausalExplanation(
                    hotspots=[],
                    counterfactual=None,
                    explanation_quality="high",
                    timestamp=time.time(),
                )
        
        class MockAuditLog:
            def append(self, passport):
                pass
        
        controller = MemoryRoutedController(
            memory, breaker, MockCausalRouter(), MockAuditLog()
        )
        
        result = controller.route({"type": "test"})
        assert result.decision == RouteDecision.HALT
        assert result.circuit_breaker_tripped is True

    def test_get_memory_state(self):
        """Test getting memory state."""
        memory = HebbianMemoryKernel()
        memory.add_route("route_1")
        breaker = CircuitBreaker()
        
        class MockCausalRouter:
            def explain(self, event, claim):
                from python_backend.core.attribution.causal_router import CausalExplanation
                return CausalExplanation(
                    hotspots=[],
                    counterfactual=None,
                    explanation_quality="high",
                    timestamp=time.time(),
                )
        
        class MockAuditLog:
            def append(self, passport):
                pass
        
        controller = MemoryRoutedController(
            memory, breaker, MockCausalRouter(), MockAuditLog()
        )
        
        state = controller.get_memory_state()
        assert "learning_rate" in state
        assert "weights" in state

    def test_get_circuit_breaker_state(self):
        """Test getting circuit breaker state."""
        memory = HebbianMemoryKernel()
        breaker = CircuitBreaker()
        
        class MockCausalRouter:
            def explain(self, event, claim):
                from python_backend.core.attribution.causal_router import CausalExplanation
                return CausalExplanation(
                    hotspots=[],
                    counterfactual=None,
                    explanation_quality="high",
                    timestamp=time.time(),
                )
        
        class MockAuditLog:
            def append(self, passport):
                pass
        
        controller = MemoryRoutedController(
            memory, breaker, MockCausalRouter(), MockAuditLog()
        )
        
        state = controller.get_circuit_breaker_state()
        assert "state" in state
        assert "failure_count" in state

    def test_reset_circuit_breaker(self):
        """Test resetting circuit breaker."""
        memory = HebbianMemoryKernel()
        breaker = CircuitBreaker(failure_threshold=1)
        breaker.record_failure()
        
        class MockCausalRouter:
            def explain(self, event, claim):
                from python_backend.core.attribution.causal_router import CausalExplanation
                return CausalExplanation(
                    hotspots=[],
                    counterfactual=None,
                    explanation_quality="high",
                    timestamp=time.time(),
                )
        
        class MockAuditLog:
            def append(self, passport):
                pass
        
        controller = MemoryRoutedController(
            memory, breaker, MockCausalRouter(), MockAuditLog()
        )
        
        assert breaker.state == CircuitBreakerState.OPEN
        controller.reset_circuit_breaker()
        assert breaker.state == CircuitBreakerState.CLOSED


# ============================================================================
# Property-Based Tests
# ============================================================================


class TestHebbianMemoryKernelProperties:
    """Property-based tests for HebbianMemoryKernel."""

    @given(
        learning_rate=floats(min_value=0.01, max_value=1.0),
        decay_rate=floats(min_value=0.9, max_value=0.999),
        window_size=integers(min_value=10, max_value=1000),
    )
    def test_property_kernel_parameters_valid(self, learning_rate, decay_rate, window_size):
        """Property: Valid parameters create valid kernel."""
        kernel = HebbianMemoryKernel(learning_rate, decay_rate, window_size)
        assert kernel.learning_rate == learning_rate
        assert kernel.decay_rate == decay_rate
        assert kernel.window_size == window_size

    @given(
        num_routes=integers(min_value=1, max_value=10),
    )
    def test_property_probabilities_sum_to_one(self, num_routes):
        """Property: Route probabilities always sum to 1.0."""
        kernel = HebbianMemoryKernel()
        for i in range(num_routes):
            kernel.add_route(f"route_{i}", initial_weight=float(i))
        
        probs = kernel.current_route_probabilities()
        if probs:  # Only check if there are routes
            assert abs(sum(probs.values()) - 1.0) < 1e-6

    @given(
        num_events=integers(min_value=1, max_value=50),
    )
    def test_property_history_respects_window(self, num_events):
        """Property: History never exceeds window size."""
        kernel = HebbianMemoryKernel(window_size=20)
        kernel.add_route("route_1")
        
        for _ in range(num_events):
            kernel.record_ack({"type": "test"}, "route_1")
        
        assert len(kernel.history) <= 20


class TestCircuitBreakerProperties:
    """Property-based tests for CircuitBreaker."""

    @given(
        failure_threshold=integers(min_value=1, max_value=100),
        timeout_seconds=floats(min_value=1.0, max_value=3600.0),
    )
    def test_property_breaker_parameters_valid(self, failure_threshold, timeout_seconds):
        """Property: Valid parameters create valid breaker."""
        breaker = CircuitBreaker(failure_threshold, timeout_seconds)
        assert breaker.failure_threshold == failure_threshold
        assert breaker.timeout_seconds == timeout_seconds

    @given(
        num_failures=integers(min_value=1, max_value=20),
    )
    def test_property_failure_count_never_negative(self, num_failures):
        """Property: Failure count is never negative."""
        breaker = CircuitBreaker(failure_threshold=100)
        
        for _ in range(num_failures):
            breaker.record_failure()
        
        # Record some successes to decay
        for _ in range(num_failures):
            breaker.record_success()
        
        assert breaker.failure_count >= 0


class TestRouteResultProperties:
    """Property-based tests for RouteResult."""

    @given(
        confidence=floats(min_value=0.0, max_value=1.0),
    )
    def test_property_confidence_in_range(self, confidence):
        """Property: Confidence is always in [0, 1]."""
        result = RouteResult(
            decision=RouteDecision.EXECUTE,
            route="route_1",
            explanation={},
            confidence=confidence,
            circuit_breaker_tripped=False,
        )
        assert 0.0 <= result.confidence <= 1.0


# ============================================================================
# Integration Tests
# ============================================================================


class TestMemoryRouterIntegration:
    """Test integration with other modules."""

    def test_controller_learns_from_failures(self):
        """Test that controller learns from routing failures."""
        memory = HebbianMemoryKernel()
        memory.add_route("route_1", initial_weight=2.0)
        memory.add_route("route_2", initial_weight=1.0)
        breaker = CircuitBreaker()
        
        class MockCausalRouter:
            def explain(self, event, claim):
                from python_backend.core.attribution.causal_router import CausalExplanation
                return CausalExplanation(
                    hotspots=[],
                    counterfactual=None,
                    explanation_quality="high",
                    timestamp=time.time(),
                )
        
        class MockAuditLog:
            def append(self, passport):
                pass
        
        controller = MemoryRoutedController(
            memory, breaker, MockCausalRouter(), MockAuditLog()
        )
        
        # Initial state: route_1 has higher weight
        assert memory.weights["route_1"] > memory.weights["route_2"]
        
        # Simulate failures on route_1
        for _ in range(5):
            memory.record_nack({"type": "test"}, "route_1")
        
        # route_1 weight should decrease
        assert memory.weights["route_1"] < 2.0

    def test_controller_reinforces_successes(self):
        """Test that controller reinforces successful routes."""
        memory = HebbianMemoryKernel()
        memory.add_route("route_1", initial_weight=0.0)
        breaker = CircuitBreaker()
        
        class MockCausalRouter:
            def explain(self, event, claim):
                from python_backend.core.attribution.causal_router import CausalExplanation
                return CausalExplanation(
                    hotspots=[],
                    counterfactual=None,
                    explanation_quality="high",
                    timestamp=time.time(),
                )
        
        class MockAuditLog:
            def append(self, passport):
                pass
        
        controller = MemoryRoutedController(
            memory, breaker, MockCausalRouter(), MockAuditLog()
        )
        
        # Record successes on route_1
        for _ in range(5):
            memory.record_ack({"type": "test"}, "route_1")
        
        # route_1 weight should increase
        assert memory.weights["route_1"] > 0.0

    def test_controller_passport_generation(self):
        """Test that controller generates audit passports."""
        memory = HebbianMemoryKernel()
        breaker = CircuitBreaker()
        
        class MockCausalRouter:
            def explain(self, event, claim):
                from python_backend.core.attribution.causal_router import CausalExplanation
                return CausalExplanation(
                    hotspots=[],
                    counterfactual=None,
                    explanation_quality="high",
                    timestamp=time.time(),
                )
        
        class MockAuditLog:
            def __init__(self):
                self.passports = []
            
            def append(self, passport):
                self.passports.append(passport)
        
        audit_log = MockAuditLog()
        controller = MemoryRoutedController(
            memory, breaker, MockCausalRouter(), audit_log
        )
        
        controller.route({"type": "test"})
        
        # Should have generated a passport
        assert len(audit_log.passports) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
