"""Stress tests for autonomous mining controller.

These tests validate system behavior under extreme load conditions:
- High-frequency pool responses
- Rapid proposal generation
- Circuit breaker saturation
- Memory pressure
- State persistence under load
"""

from __future__ import annotations

import asyncio
import tempfile
import time
from pathlib import Path
from typing import List

import pytest

from pythia_mining.autonomous_mining_controller import (
    AutonomousConfig,
    AutonomousMiningController,
    AutonomyLevel,
)


class _FakeEngine:
    """Minimal duck-type stand-in for UnifiedMiningEngine."""

    phi_density: float = 0.75
    current_job = None
    stratum_client = None
    phi_ensemble = None
    optimizer = None
    solver = None
    consciousness = None

    def get_hashrate(self) -> float:
        return 0.0

    def get_phi_density(self) -> float:
        return self.phi_density

    def get_state(self) -> dict:
        return {"status": "idle"}

    class _PhiScaling:
        phi_scaling = 1.5
        search_depth = 60
        coherence_threshold = 0.45
        compression_target = 1.86

    phi_scaling_engine = _PhiScaling()


def _make_controller(tmp_dir: str) -> AutonomousMiningController:
    """Create controller for testing."""
    config = AutonomousConfig(
        autonomy_level=AutonomyLevel.AUTONOMOUS,
        persistence_enabled=True,
        persistence_dir=tmp_dir,
        reflexive_loop_enabled=True,
        compression_drive_enabled=False,
        max_proposals_per_cycle=3,
        virtual_session_horizon=0.01,
    )
    return AutonomousMiningController(_FakeEngine(), config=config)


# =============================================================================
# STRESS TEST: High-Frequency Pool Responses
# =============================================================================


@pytest.mark.stress
def test_stress_high_frequency_pool_responses():
    """System should handle 10,000 pool responses without degradation."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)

        start_time = time.monotonic()

        # Simulate 10,000 rapid pool responses
        for i in range(10_000):
            ctrl.record_pool_response(
                share_accepted=(i % 3 == 0),  # 33% accept rate
                error_code=None if i % 3 == 0 else "low-diff",
                job_difficulty=1000.0 + (i % 100),  # Varying difficulty
                response_time_ms=50.0 + (i % 50),
            )

        elapsed = time.monotonic() - start_time

        # Performance assertions
        assert elapsed < 10.0, f"10k responses took {elapsed:.2f}s, should be <10s"

        # Memory assertions
        assert (
            len(ctrl._pool_response_history) == 1000
        ), "History should be capped at 1000 samples"

        # State assertions
        assert ctrl._consecutive_failures == 0, "No failures should accumulate"
        assert not ctrl.is_circuit_open(), "Circuit should remain closed"

        # Metrics generation should still be fast
        metrics_start = time.monotonic()
        metrics = ctrl.get_prometheus_metrics_text_cached()
        metrics_elapsed = time.monotonic() - metrics_start

        assert (
            metrics_elapsed < 0.1
        ), f"Metrics generation took {metrics_elapsed:.3f}s after 10k responses"
        assert "hyba_phi_density" in metrics


# =============================================================================
# STRESS TEST: Rapid Reflexive Cycles
# =============================================================================


@pytest.mark.stress
@pytest.mark.asyncio
async def test_stress_rapid_reflexive_cycles():
    """System should handle 100 consecutive reflexive cycles."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)

        start_time = time.monotonic()

        # Run 100 reflexive optimization cycles
        for i in range(100):
            result = await ctrl.seek_improvement()

            # Verify each cycle completes successfully
            assert result.get("reflexive_cycle_executed") is True

            # Verify proposals generated
            assert result.get("proposals_generated", 0) > 0

        elapsed = time.monotonic() - start_time

        # Should complete in reasonable time
        assert (
            elapsed < 60.0
        ), f"100 reflexive cycles took {elapsed:.2f}s, should be <60s"

        # Verify state integrity
        metrics = ctrl.get_metrics_snapshot()
        assert metrics["reflexive_cycle_count"] >= 100
        assert metrics["consecutive_failures"] == 0


# =============================================================================
# STRESS TEST: Circuit Breaker Saturation
# =============================================================================


@pytest.mark.stress
def test_stress_circuit_breaker_saturation():
    """System should handle repeated circuit breaker trips."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)

        trip_count = 0

        # Trigger 20 circuit breaker trips
        for cycle in range(20):
            # Reset circuit if needed
            if ctrl.is_circuit_open():
                ctrl.reset_circuit_breaker(
                    operator_id="stress_test", operator_reason=f"stress_cycle_{cycle}"
                )

            # Trigger 3 consecutive failures to trip circuit
            for _ in range(3):
                ctrl.record_autonomy_failure("stress_test_failure")

            # Verify circuit opened
            if ctrl.is_circuit_open():
                trip_count += 1

        # Should have tripped circuit multiple times
        assert (
            trip_count >= 15
        ), f"Only {trip_count}/20 trips registered, circuit breaker may be stuck"

        # System should still be responsive
        metrics = ctrl.get_prometheus_metrics_text()
        assert "hyba_autonomous_circuit_breaker_trips_total" in metrics


# =============================================================================
# STRESS TEST: State Persistence Under Load
# =============================================================================


@pytest.mark.stress
def test_stress_state_persistence_rapid_saves():
    """System should handle rapid state saves without corruption."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)

        # Rapidly save state 1000 times with pool responses
        for i in range(1000):
            ctrl.record_pool_response(
                share_accepted=(i % 2 == 0),
                error_code=None,
                job_difficulty=1000.0,
                target=f"target_{i % 5}",
            )
            ctrl._save_reflexive_state()

        # Verify final state file exists and is valid
        state_file = Path(tmp) / "reflexive_state.json"
        assert state_file.exists(), "State file should exist"

        # Verify checksum file exists
        checksum_file = Path(tmp) / "reflexive_state.json.sha256"
        assert checksum_file.exists(), "Checksum file should exist"

        # Load state and verify integrity
        ctrl2 = _make_controller(tmp)
        ctrl2._load_reflexive_state()

        # Should load successfully without corruption
        assert len(ctrl2._reflexive_target_bandits) > 0


# =============================================================================
# STRESS TEST: Memory Pressure
# =============================================================================


@pytest.mark.stress
def test_stress_memory_bounded_growth():
    """System should not exhibit unbounded memory growth."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)

        # Simulate long-running operation with many events
        for i in range(10_000):
            # Record pool responses
            ctrl.record_pool_response(
                share_accepted=(i % 2 == 0),
                error_code=None,
                job_difficulty=1000.0,
            )

            # Record autonomy events
            if i % 100 == 0:
                ctrl.record_autonomy_success()

        # Verify bounded structures
        assert (
            len(ctrl._pool_response_history) <= 1000
        ), "Pool history should be bounded at 1000"

        # Decision history is accessed via get_decision_history()
        decision_history = ctrl.get_decision_history()
        assert len(decision_history) <= 1000, "Decision history should be bounded"

        # State file should not be enormous
        ctrl._save_reflexive_state()
        state_file = Path(tmp) / "reflexive_state.json"
        state_size = state_file.stat().st_size

        assert (
            state_size < 1_000_000
        ), f"State file is {state_size} bytes, should be <1MB"


# =============================================================================
# STRESS TEST: Concurrent Operations
# =============================================================================


@pytest.mark.stress
@pytest.mark.asyncio
async def test_stress_concurrent_operations():
    """System should handle concurrent pool responses and reflexive cycles."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)

        async def record_responses():
            """Simulate pool responses."""
            for i in range(100):
                ctrl.record_pool_response(
                    share_accepted=(i % 2 == 0),
                    error_code=None,
                    job_difficulty=1000.0,
                )
                await asyncio.sleep(0.001)

        async def run_reflexive_cycles():
            """Run reflexive optimization cycles."""
            for _ in range(10):
                await ctrl.seek_improvement()
                await asyncio.sleep(0.01)

        # Run both concurrently
        await asyncio.gather(
            record_responses(),
            run_reflexive_cycles(),
        )

        # System should remain consistent
        assert not ctrl.is_circuit_open()
        assert ctrl._consecutive_failures == 0


# =============================================================================
# STRESS TEST: Prometheus Metrics Under Load
# =============================================================================


@pytest.mark.stress
def test_stress_prometheus_metrics_high_cardinality():
    """Prometheus metrics should remain low-cardinality under stress."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)

        # Generate many events with different IDs
        for i in range(1000):
            ctrl.record_pool_response(
                share_accepted=(i % 2 == 0),
                error_code=f"error_{i % 10}",  # 10 unique error codes
                job_difficulty=1000.0 + i,
                proposal_id=f"proposal_{i}",
                decision_id=f"decision_{i}",
            )

        # Get metrics
        metrics = ctrl.get_prometheus_metrics_text()

        # Verify no high-cardinality labels leaked
        assert (
            "proposal_id=" not in metrics
        ), "High-cardinality proposal_id should not be in metrics"

        assert (
            "decision_id=" not in metrics
        ), "High-cardinality decision_id should not be in metrics"

        # Verify error_code is aggregated, not per-error
        error_lines = [l for l in metrics.split("\n") if "error_code=" in l]
        assert len(error_lines) < 20, f"Too many error_code labels: {len(error_lines)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "stress"])
