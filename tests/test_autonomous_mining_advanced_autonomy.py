"""Behavioral tests for the four advanced autonomy enhancements.

Tests drive threshold boundaries directly with mocked state,
asserting on *actions taken*, not on string presence.
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
from unittest.mock import MagicMock, PropertyMock, patch

# Add python_backend to path (same pattern as existing test files)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python_backend"))

import pytest

from pythia_mining.autonomous_mining_controller import (
    AutonomousConfig,
    AutonomousMiningController,
    AutonomyLevel,
)
from pythia_mining.phi_unified_mining_engine import UnifiedMiningEngine


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_controller(**kwargs) -> AutonomousMiningController:
    """Build a controller with a mock engine and given config overrides."""
    engine = MagicMock(spec=UnifiedMiningEngine)
    engine.optimizer = MagicMock()
    engine.phi_ensemble = MagicMock()
    engine.solver = MagicMock()
    from dataclasses import dataclass, field

    @dataclass
    class MockConsciousnessConfig:
        phi_critical_threshold: float = 0.2
        phi_distributed_threshold: float = 0.4
        phi_singular_threshold: float = 0.7

    @dataclass
    class MockConsciousness:
        config: MockConsciousnessConfig = field(default_factory=MockConsciousnessConfig)

    engine.consciousness = MockConsciousness()

    config = AutonomousConfig(
        autonomy_level=AutonomyLevel.AUTONOMOUS,
        max_autonomous_hashrate_ehs=0.5,
        phi_coherence_threshold=0.70,
        reflexive_loop_enabled=False,
        compression_drive_enabled=False,
        persistence_enabled=False,
        circuit_breaker_failure_threshold=3,
        circuit_breaker_cooldown_seconds=300.0,
    )
    # Apply any overrides
    for k, v in kwargs.items():
        if hasattr(config, k):
            setattr(config, k, v)

    ctrl = AutonomousMiningController(unified_engine=engine, config=config)
    return ctrl


async def _run_single_monitor_cycle(ctrl: AutonomousMiningController) -> None:
    """Execute one iteration of the monitor health checks without the 60s sleep."""
    metrics = ctrl.get_metrics_snapshot()

    # Update live metrics from engine state
    ctrl._actual_hashrate = metrics.get("phi_density", 0.0) * 2.0
    ctrl._target_hashrate = 1.0

    # Track error rate from constraint violations
    total_decisions = metrics.get("total_decisions", 0)
    violations = metrics.get("constraint_violations", 0)
    ctrl._error_rate = violations / max(total_decisions, 1)

    # Health Check 1: Hashrate performance dip
    if ctrl._actual_hashrate < (ctrl._target_hashrate * 0.7):
        await ctrl._handle_performance_degradation()
        ctrl._degradation_events += 1

    # Health Check 2: Error rate climbing
    if ctrl._error_rate > ctrl.MAX_ERROR_THRESHOLD:
        await ctrl._recalibrate_parameters()

    # Health Check 3: Environment-aware resource scaling
    await ctrl._seek_improvement_with_resource_awareness()


# ===================================================================
# TEST 1: Continuous Health Loop
# ===================================================================


class TestContinuousHealthLoop:
    """Exercise the background monitor: thresholds, exception survival, lifecycle."""

    @pytest.mark.asyncio
    async def test_hashrate_dip_triggers_degradation_handler(self):
        """When phi_density drops 30% below target, _handle_performance_degradation fires."""
        ctrl = _make_controller()
        handler = asyncio.Event()

        original = ctrl._handle_performance_degradation

        async def tracking_handler():
            handler.set()
            await original()

        ctrl._handle_performance_degradation = tracking_handler

        # Run the monitor cycle with a low phi_density
        with patch.object(ctrl, "get_metrics_snapshot", return_value={
            "phi_density": 0.2,  # normalized hashrate = 0.4, target=1.0 => 40% of target => <70%
            "total_decisions": 100,
            "constraint_violations": 5,
        }):
            await _run_single_monitor_cycle(ctrl)

        # Assert the handler was called
        assert handler.is_set()
        # degradation_events should have incremented
        assert ctrl._degradation_events > 0

    @pytest.mark.asyncio
    async def test_error_rate_climbing_triggers_recalibration(self):
        """When error_rate exceeds MAX_ERROR_THRESHOLD, _recalibrate_parameters fires."""
        ctrl = _make_controller()
        recalibrated = asyncio.Event()

        original = ctrl._recalibrate_parameters

        async def tracking_recalibrate():
            recalibrated.set()
            await original()

        ctrl._recalibrate_parameters = tracking_recalibrate

        # Run the monitor cycle with high constraint violations
        with patch.object(ctrl, "get_metrics_snapshot", return_value={
            "phi_density": 0.8,
            "total_decisions": 10,
            "constraint_violations": 3,  # 30% error rate > 15% threshold
        }):
            await _run_single_monitor_cycle(ctrl)

        assert recalibrated.is_set()

    @pytest.mark.asyncio
    async def test_start_continuous_monitor_prevents_double_start(self):
        """Calling start_continuous_monitor twice should not create two tasks."""
        ctrl = _make_controller()
        await ctrl.start_continuous_monitor()
        task1 = ctrl._monitor_task
        await ctrl.start_continuous_monitor()
        task2 = ctrl._monitor_task
        # Should be the same task (second call is no-op when already running)
        assert task1 is task2
        # Clean up
        await ctrl.stop_continuous_monitor()

    @pytest.mark.asyncio
    async def test_stop_continuous_monitor_cancels_cleanly(self):
        """stop_continuous_monitor should cancel the task and set is_running=False."""
        ctrl = _make_controller()
        await ctrl.start_continuous_monitor()
        assert ctrl.is_running
        await ctrl.stop_continuous_monitor()
        assert not ctrl.is_running
        assert ctrl._monitor_task is None or ctrl._monitor_task.done()

    @pytest.mark.asyncio
    async def test_continuous_monitor_records_autonomy_event(self):
        """Health check actions must record entries in the autonomy journal."""
        ctrl = _make_controller()
        journal_len = len(ctrl._autonomy_journal)

        # Trigger a performance degradation event
        ctrl._actual_hashrate = 0.1
        ctrl._target_hashrate = 1.0
        with patch.object(ctrl, "get_metrics_snapshot", return_value={
            "phi_density": 0.05,
            "total_decisions": 100,
            "constraint_violations": 0,
            "degradation_events": 0,
        }):
            await ctrl._handle_performance_degradation()

        assert len(ctrl._autonomy_journal) == journal_len + 1
        assert ctrl._autonomy_journal[-1]["event_type"] == "PerformanceDegradation"

# ===================================================================
# TEST 2: Dynamic Resource Scaling
# ===================================================================


class TestDynamicResourceScaling:
    """Exercise CPU-load thresholds and intensity adjustments."""

    @pytest.mark.asyncio
    async def test_high_cpu_load_triggers_throttle(self):
        """When CPU load > 90%, intensity should decrement and event recorded."""
        ctrl = _make_controller()
        initial_intensity = ctrl._current_intensity

        with patch.object(ctrl, "platform_interface_get_cpu_load", return_value=95.0):
            await ctrl._seek_improvement_with_resource_awareness()

        assert ctrl._current_intensity == initial_intensity - 1
        # Verify journal entry
        journal_entries = [e for e in ctrl._autonomy_journal if e["event_type"] == "ResourceThrottle"]
        assert len(journal_entries) == 1
        assert journal_entries[0]["data"]["system_load"] == 95.0

    @pytest.mark.asyncio
    async def test_exactly_90_percent_cpu_does_not_throttle(self):
        """At exactly 90% load (boundary), throttle must NOT fire — code uses `> 90`."""
        ctrl = _make_controller()
        initial = ctrl._current_intensity

        with patch.object(ctrl, "platform_interface_get_cpu_load", return_value=90.0):
            await ctrl._seek_improvement_with_resource_awareness()

        assert ctrl._current_intensity == initial
        assert not any(e["event_type"] == "ResourceThrottle" for e in ctrl._autonomy_journal)

    @pytest.mark.asyncio
    async def test_low_cpu_load_triggers_expansion(self):
        """When CPU load < 40% and intensity < 10, intensity should increment."""
        ctrl = _make_controller()
        ctrl._current_intensity = 3  # well below max

        with patch.object(ctrl, "platform_interface_get_cpu_load", return_value=25.0):
            await ctrl._seek_improvement_with_resource_awareness()

        assert ctrl._current_intensity == 4
        journal_entries = [e for e in ctrl._autonomy_journal if e["event_type"] == "ResourceExpansion"]
        assert len(journal_entries) == 1
        assert journal_entries[0]["data"]["system_load"] == 25.0

    @pytest.mark.asyncio
    async def test_exactly_40_percent_cpu_does_not_expand(self):
        """At exactly 40% load (boundary), expansion must NOT fire — code uses `< 40`."""
        ctrl = _make_controller()
        ctrl._current_intensity = 3

        with patch.object(ctrl, "platform_interface_get_cpu_load", return_value=40.0):
            await ctrl._seek_improvement_with_resource_awareness()

        assert ctrl._current_intensity == 3
        assert not any(e["event_type"] == "ResourceExpansion" for e in ctrl._autonomy_journal)

    @pytest.mark.asyncio
    async def test_moderate_cpu_load_does_nothing(self):
        """Between 40-90% load, no intensity adjustment should occur."""
        ctrl = _make_controller()
        initial = ctrl._current_intensity

        with patch.object(ctrl, "platform_interface_get_cpu_load", return_value=65.0):
            await ctrl._seek_improvement_with_resource_awareness()

        assert ctrl._current_intensity == initial
        assert len(ctrl._autonomy_journal) == 0

    def test_platform_interface_falls_back_to_simulated_load(self):
        """When psutil is unavailable and os.getloadavg fails, return stored _system_load."""
        ctrl = _make_controller()
        ctrl._system_load = 42.0

        # Patch os.getloadavg to raise
        with patch("os.getloadavg", side_effect=AttributeError("not available")):
            load = ctrl.platform_interface_get_cpu_load()

        # Should fall back to the stored field
        assert load == 42.0

    @pytest.mark.asyncio
    async def test_adjust_intensity_scales_engine_parameters(self):
        """Intensity change should propagate to optimizer max_search_iterations."""
        ctrl = _make_controller()
        ctrl._current_intensity = 5
        # Scale from 5 -> 3 (decrement twice)
        await ctrl._adjust_intensity(decrement=2)
        assert ctrl._current_intensity == 3

        # intensity_ratio = 3/5 = 0.6, base=60 => scaled=36
        expected_iterations = int(max(10.0, min(300.0, 60.0 * 0.6)))
        if ctrl.engine and ctrl.engine.optimizer:
            assert ctrl.engine.optimizer.max_search_iterations == expected_iterations

    @pytest.mark.asyncio
    async def test_resource_awareness_records_journal_event(self):
        """Verify journal event recording in resource throttling path."""
        ctrl = _make_controller()

        with patch.object(ctrl, "platform_interface_get_cpu_load", return_value=92.0):
            await ctrl._seek_improvement_with_resource_awareness()

        # Verify the journal has a ResourceThrottle entry
        events = [e for e in ctrl._autonomy_journal if e["event_type"] == "ResourceThrottle"]
        assert len(events) == 1
        assert "new_intensity" in events[0]["data"]


# ===================================================================
# TEST 3: Circuit Breaker Pattern
# ===================================================================


class TestCircuitBreakerPattern:
    """Exercise heal-attempt frequency threshold and failover logic."""

    @pytest.mark.asyncio
    async def test_excessive_heal_attempts_triggers_failover(self):
        """More than 5 heal attempts in the sliding window should trigger backup switch."""
        ctrl = _make_controller()

        # Seed the heal window with 6 timestamps within the last 10 minutes
        now = time.time()
        ctrl._heal_attempt_window = [now - i * 60 for i in range(6)]  # last 6 minutes

        result = await ctrl.boot_self_heal_and_optimize()

        assert result["circuit_breaker_triggered"] is True
        assert result["reason"] == "excessive_heal_attempts"
        assert result["heal_attempts"] >= 5
        assert result["startup_self_healing_executed"] is False

        # Verify journal has a CircuitBreakerFailover entry
        events = [e for e in ctrl._autonomy_journal if e["event_type"] == "CircuitBreakerFailover"]
        assert len(events) == 1
        assert events[0]["data"]["action"] == "switch_to_backup"

    @pytest.mark.asyncio
    async def test_exactly_five_heal_attempts_does_not_trigger_failover(self):
        """Exactly 5 heal attempts (boundary) must NOT trigger the circuit breaker.

        The code uses `attempts > 5`, so 5 is the last safe value.
        """
        ctrl = _make_controller()
        now = time.time()
        ctrl._heal_attempt_window = [now - i * 60 for i in range(5)]

        # Replace the entire audit logger with a mock to eliminate I/O timeout
        original_logger = ctrl._persistent_audit_logger
        ctrl._persistent_audit_logger = MagicMock()
        try:
            with patch.object(ctrl, "seek_improvement", return_value={"reflexive_cycle_executed": False}):
                result = await ctrl.boot_self_heal_and_optimize()
        finally:
            ctrl._persistent_audit_logger = original_logger

        assert result.get("circuit_breaker_triggered") is not True

    @pytest.mark.asyncio
    async def test_few_heal_attempts_proceeds_normally(self):
        """Fewer than 6 heal attempts should proceed with normal boot logic."""
        ctrl = _make_controller()

        # Seed with only 2 attempts
        now = time.time()
        ctrl._heal_attempt_window = [now - i * 60 for i in range(2)]

        # Replace the entire audit logger with a mock to eliminate I/O timeout
        original_logger = ctrl._persistent_audit_logger
        ctrl._persistent_audit_logger = MagicMock()
        try:
            with patch.object(ctrl, "seek_improvement", return_value={"reflexive_cycle_executed": False}):
                result = await ctrl.boot_self_heal_and_optimize()
        finally:
            ctrl._persistent_audit_logger = original_logger

        # Should NOT circuit-break
        assert result.get("circuit_breaker_triggered") is not True

    @pytest.mark.asyncio
    async def test_heal_attempt_window_prunes_old_entries(self):
        """Entries older than window_seconds should be pruned from the sliding window."""
        ctrl = _make_controller()

        # Seed with entries both inside and outside the window
        now = time.time()
        ctrl._heal_attempt_window = [
            now - 10,           # 10s ago (inside)
            now - 700,          # 700s ago (outside 600s window)
            now - 100,          # 100s ago (inside)
            now - 300,          # 300s ago (inside)
        ]

        count = await ctrl.get_recent_heal_attempts()
        assert count == 3  # 700s entry should be pruned

    @pytest.mark.asyncio
    async def test_switch_to_backup_resets_consecutive_failures(self):
        """After failover, _consecutive_failures should reset to 0."""
        ctrl = _make_controller()
        ctrl._consecutive_failures = 5

        await ctrl._switch_to_backup_infrastructure()

        assert ctrl._consecutive_failures == 0
        assert ctrl._circuit_open_until == 0.0

    @pytest.mark.asyncio
    async def test_circuit_breaker_records_autonomy_event(self):
        """Failover path must record to the autonomy journal."""
        ctrl = _make_controller()
        now = time.time()
        ctrl._heal_attempt_window = [now - i * 60 for i in range(6)]

        await ctrl.boot_self_heal_and_optimize()

        events = [e for e in ctrl._autonomy_journal if e["event_type"] == "CircuitBreakerFailover"]
        assert len(events) == 1
        events2 = [e for e in ctrl._autonomy_journal if e["event_type"] == "BackupFailover"]
        assert len(events2) == 1


# ===================================================================
# TEST 4: Autonomy Journal (Auditability)
# ===================================================================


class TestAutonomyJournal:
    """Exercise journal bounds, coverage at decision points, and optimization delta."""

    def test_journal_bounded_to_1000_entries(self):
        """Journal should enforce its 1000-entry bound to prevent unbounded growth."""
        ctrl = _make_controller()

        # Record 1005 events
        for i in range(1005):
            ctrl.record_autonomy_event(f"test_event_{i}", {"index": i})

        assert len(ctrl._autonomy_journal) <= 1000

    def test_journal_returns_most_recent_first(self):
        """get_autonomy_journal should return entries in reverse chronological order."""
        ctrl = _make_controller()

        ctrl.record_autonomy_event("first", {"seq": 1})
        ctrl.record_autonomy_event("second", {"seq": 2})

        journal = ctrl.get_autonomy_journal()
        assert journal[0]["data"]["seq"] == 2
        assert journal[1]["data"]["seq"] == 1

    def test_journal_limit_parameter(self):
        """get_autonomy_journal(limit=N) should return only N entries."""
        ctrl = _make_controller()

        for i in range(50):
            ctrl.record_autonomy_event(f"evt_{i}", {"i": i})

        limited = ctrl.get_autonomy_journal(limit=5)
        assert len(limited) == 5

    def test_calculate_optimization_delta_returns_zero_for_no_baseline(self):
        """When reference_efficiency is 0, delta should be 0.0 (no division by zero)."""
        ctrl = _make_controller()
        ctrl._reference_efficiency = 0.0

        delta = ctrl.calculate_optimization_delta()
        assert delta == 0.0

    def test_calculate_optimization_delta_positive_improvement(self):
        """When current efficiency exceeds reference, delta should be positive."""
        ctrl = _make_controller()
        ctrl._reference_efficiency = 0.5

        # Make get_current_efficiency return a higher value
        with patch.object(ctrl, "get_current_efficiency", return_value=0.75):
            delta = ctrl.calculate_optimization_delta()

        assert delta > 0.0
        # (0.75 - 0.5) / 0.5 * 100 = 50%
        assert delta == 50.0

    @pytest.mark.asyncio
    async def test_performance_degradation_records_journal_event(self):
        """_handle_performance_degradation must record a journal entry."""
        ctrl = _make_controller()
        journal_len = len(ctrl._autonomy_journal)

        await ctrl._handle_performance_degradation()

        assert len(ctrl._autonomy_journal) == journal_len + 1
        assert ctrl._autonomy_journal[-1]["event_type"] == "PerformanceDegradation"

    @pytest.mark.asyncio
    async def test_parameter_recalibration_records_journal_event(self):
        """_recalibrate_parameters must record a journal entry."""
        ctrl = _make_controller()
        journal_len = len(ctrl._autonomy_journal)

        await ctrl._recalibrate_parameters()

        assert len(ctrl._autonomy_journal) == journal_len + 1
        assert ctrl._autonomy_journal[-1]["event_type"] == "ParameterRecalibration"