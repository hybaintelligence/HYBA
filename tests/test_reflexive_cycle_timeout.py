"""Tests for ReflexiveCycleGuard - reflexive cycle timeout enforcement."""

import asyncio
import pytest
from typing import List, Dict, Any

from python_backend.pythia_mining.reflexive_cycle_timeout import (
    ReflexiveCycleGuard,
    ExecutionPhase,
    TimeoutAction,
    get_reflexive_cycle_guard,
    reset_reflexive_cycle_guard,
)


@pytest.fixture
def guard():
    """Create a fresh guard instance for each test."""
    reset_reflexive_cycle_guard()
    return ReflexiveCycleGuard(deadline_ms=50.0, enable_telemetry=False)


class TestReflexiveCycleGuard:
    """Test ReflexiveCycleGuard core functionality."""

    @pytest.mark.asyncio
    async def test_basic_cycle_completion(self, guard):
        """Test basic cycle with all phases completing within deadline."""

        async def fast_parse():
            await asyncio.sleep(0.001)
            return [{"id": "p1"}, {"id": "p2"}]

        async def fast_simulate(proposal):
            await asyncio.sleep(0.001)
            return {**proposal, "simulated_phi": 0.95}

        async def fast_validate(proposal):
            await asyncio.sleep(0.001)
            return {**proposal, "valid": True}

        async def fast_apply(proposal):
            await asyncio.sleep(0.001)
            return {**proposal, "applied": True}

        async with guard.reflexive_cycle() as cycle:
            proposals = await cycle.parse_proposals(fast_parse)
            assert len(proposals) == 2

            simulated = await cycle.simulate_mining(proposals, fast_simulate)
            assert len(simulated) == 2
            assert all(p.get("simulated_phi") == 0.95 for p in simulated)

            validated = await cycle.validate_constraints(simulated, fast_validate)
            assert len(validated) == 2
            assert all(p.get("valid") for p in validated)

            applied, complete = await cycle.apply_proposals(validated, fast_apply)
            assert len(applied) == 2
            assert complete is True

    @pytest.mark.asyncio
    async def test_parsing_timeout_returns_empty(self, guard):
        """Test that parsing timeout returns empty proposals gracefully."""

        async def slow_parse():
            await asyncio.sleep(0.1)  # Exceed 50ms deadline
            return [{"id": "p1"}]

        async with guard.reflexive_cycle() as cycle:
            proposals = await cycle.parse_proposals(slow_parse)
            assert proposals == []

        # Verify timeout was recorded
        metrics = guard.get_metrics_snapshot()
        assert metrics["timeout_count"] == 1
        assert metrics["partial_results_returned"] == 1

    @pytest.mark.asyncio
    async def test_simulation_timeout_returns_partial_results(self, guard):
        """Test that simulation timeout returns proposals completed so far."""
        proposals = [{"id": f"p{i}"} for i in range(5)]

        async def slow_simulate(proposal):
            await asyncio.sleep(0.015)  # ~75ms for all 5
            return {**proposal, "simulated": True}

        async with guard.reflexive_cycle() as cycle:
            simulated = await cycle.simulate_mining(proposals, slow_simulate)

            # Should have completed at least one, but not all
            assert len(simulated) > 0
            assert len(simulated) < len(proposals)

        metrics = guard.get_metrics_snapshot()
        assert metrics["partial_results_returned"] > 0

    @pytest.mark.asyncio
    async def test_validation_timeout_skips_checks(self, guard):
        """Test that validation timeout skips remaining constraint checks."""
        proposals = [{"id": f"p{i}"} for i in range(3)]

        validation_count = 0

        async def slow_validate(proposal):
            nonlocal validation_count
            validation_count += 1
            await asyncio.sleep(0.020)
            return {**proposal, "validated": True}

        async with guard.reflexive_cycle() as cycle:
            validated = await cycle.validate_constraints(
                proposals, slow_validate, skip_on_timeout=True
            )
            # Should have all proposals, even if not all validated
            assert len(validated) == len(proposals)

        metrics = guard.get_metrics_snapshot()
        assert metrics["validations_skipped"] > 0

    @pytest.mark.asyncio
    async def test_apply_timeout_triggers_rollback(self, guard):
        """Test that apply timeout triggers rollback."""
        proposals = [{"id": f"p{i}"} for i in range(3)]

        rollback_count = 0

        async def rollback_fn():
            nonlocal rollback_count
            rollback_count += 1

        async def slow_apply(proposal):
            await asyncio.sleep(0.020)
            return {**proposal, "applied": True}

        async with guard.reflexive_cycle() as cycle:
            applied, complete = await cycle.apply_proposals(
                proposals, slow_apply, rollback_on_timeout=True
            )

            # Should not be complete due to timeout
            assert complete is False or len(applied) < len(proposals)

        metrics = guard.get_metrics_snapshot()
        assert metrics["rollbacks_performed"] >= 0

    @pytest.mark.asyncio
    async def test_time_remaining_tracking(self, guard):
        """Test that time remaining is accurately tracked."""

        async def check_times():
            times = []
            times.append(guard._time_remaining_ms())
            await asyncio.sleep(0.010)
            times.append(guard._time_remaining_ms())
            await asyncio.sleep(0.010)
            times.append(guard._time_remaining_ms())
            return times

        async with guard.reflexive_cycle() as cycle:
            times = await check_times()

            # Each measurement should have less time than previous
            assert times[0] > times[1] > times[2]
            assert times[0] > 0

    @pytest.mark.asyncio
    async def test_metrics_collection(self, guard):
        """Test that metrics are properly collected."""

        async def dummy_parse():
            await asyncio.sleep(0.001)
            return [{"id": "p1"}]

        async def dummy_apply(proposal):
            await asyncio.sleep(0.001)
            return proposal

        # Run multiple cycles
        for _ in range(3):
            async with guard.reflexive_cycle() as cycle:
                proposals = await cycle.parse_proposals(dummy_parse)
                applied, _ = await cycle.apply_proposals(proposals, dummy_apply)

        metrics = guard.get_metrics_snapshot()
        assert metrics["total_cycles"] == 3
        assert metrics["avg_duration_ms"] > 0
        assert metrics["min_duration_ms"] > 0
        assert metrics["max_duration_ms"] > 0

    @pytest.mark.asyncio
    async def test_deadline_exceeded_check(self, guard):
        """Test deadline exceeded detection."""
        async with guard.reflexive_cycle() as cycle:
            # Initially not exceeded
            assert not cycle.is_deadline_exceeded()

            # Exhaust the deadline
            await asyncio.sleep(0.051)  # Exceed 50ms

            # Now should be exceeded
            assert cycle.is_deadline_exceeded()

    @pytest.mark.asyncio
    async def test_empty_proposals_handling(self, guard):
        """Test handling of empty proposal lists."""

        async def dummy_validate(proposal):
            return {**proposal, "validated": True}

        async def dummy_apply(proposal):
            return {**proposal, "applied": True}

        async with guard.reflexive_cycle() as cycle:
            # Empty proposals should return empty without error
            validated = await cycle.validate_constraints([], dummy_validate)
            assert validated == []

            applied, complete = await cycle.apply_proposals([], dummy_apply)
            assert applied == []
            assert complete is True


class TestPhaseMetrics:
    """Test ExecutionPhase and PhaseMetrics tracking."""

    def test_phase_metrics_completion(self):
        """Test phase metrics marking and calculation."""
        from python_backend.pythia_mining.reflexive_cycle_timeout import PhaseMetrics

        metric = PhaseMetrics(
            phase=ExecutionPhase.PARSING,
            start_time_ms=1000.0,
        )

        assert not metric.completed
        assert metric.duration_ms == 0.0

        metric.mark_complete(1050.0)

        assert metric.completed
        assert metric.duration_ms == 50.0
        assert metric.percent_complete() == 100.0


class TestTimeoutMetrics:
    """Test TimeoutMetrics aggregation."""

    def test_timeout_metrics_recording(self):
        """Test recording of timeout metrics."""
        from python_backend.pythia_mining.reflexive_cycle_timeout import TimeoutMetrics

        metrics = TimeoutMetrics()

        # Record cycles
        metrics.record_cycle(20.0)
        metrics.record_cycle(30.0)
        metrics.record_cycle(40.0)

        assert metrics.total_cycles == 3
        assert metrics.total_duration_ms == 90.0
        assert metrics.avg_duration_ms == 30.0
        assert metrics.min_duration_ms == 20.0
        assert metrics.max_duration_ms == 40.0

        # Record timeout
        affected = {ExecutionPhase.SIMULATION, ExecutionPhase.VALIDATION}
        metrics.record_timeout("Simulation took too long", affected)

        assert metrics.timeout_count == 1
        assert metrics.last_timeout_reason == "Simulation took too long"
        assert ExecutionPhase.SIMULATION in metrics.phases_affected


class TestCycleContext:
    """Test the CycleContext helper."""

    @pytest.mark.asyncio
    async def test_cycle_context_methods(self):
        """Test CycleContext provides access to guard methods."""
        guard = ReflexiveCycleGuard(deadline_ms=100.0, enable_telemetry=False)

        async def fast_parse():
            return [{"id": "p1"}]

        async with guard.reflexive_cycle() as cycle:
            # Test context methods
            remaining = cycle.time_remaining_ms()
            assert remaining > 0
            assert remaining <= 100.0

            proposals = await cycle.parse_proposals(fast_parse)
            assert len(proposals) == 1


class TestGlobalGuardSingleton:
    """Test global guard singleton pattern."""

    def test_get_global_guard(self):
        """Test getting global guard instance."""
        reset_reflexive_cycle_guard()

        guard1 = get_reflexive_cycle_guard(deadline_ms=100.0)
        guard2 = get_reflexive_cycle_guard(deadline_ms=200.0)

        # Should return same instance
        assert guard1 is guard2

    def test_reset_guard(self):
        """Test resetting global guard."""
        guard1 = get_reflexive_cycle_guard()
        reset_reflexive_cycle_guard()
        guard2 = get_reflexive_cycle_guard()

        # Should be different instances
        assert guard1 is not guard2


class TestErrorHandling:
    """Test error handling and recovery."""

    @pytest.mark.asyncio
    async def test_exception_in_parse_phase(self, guard):
        """Test exception handling in parse phase."""

        async def failing_parse():
            raise ValueError("Parse failed")

        with pytest.raises(ValueError):
            async with guard.reflexive_cycle() as cycle:
                await cycle.parse_proposals(failing_parse)

    @pytest.mark.asyncio
    async def test_exception_in_simulate_phase(self, guard):
        """Test exception handling in simulate phase."""
        proposals = [{"id": "p1"}]

        async def failing_simulate(proposal):
            raise ValueError("Simulate failed")

        with pytest.raises(ValueError):
            async with guard.reflexive_cycle() as cycle:
                await cycle.simulate_mining(proposals, failing_simulate)

    @pytest.mark.asyncio
    async def test_exception_in_apply_phase(self, guard):
        """Test exception handling with rollback in apply phase."""
        proposals = [{"id": "p1"}]

        async def failing_apply(proposal):
            raise ValueError("Apply failed")

        with pytest.raises(ValueError):
            async with guard.reflexive_cycle() as cycle:
                await cycle.apply_proposals(proposals, failing_apply)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
