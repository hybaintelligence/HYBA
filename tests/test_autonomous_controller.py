"""
Comprehensive Test Suite for Autonomous Controller
Testing autonomous meta-controller with healing, optimizing, and mining subsystems
"""

import pytest
import time

# Add python_backend to path
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "python_backend"))

from pythia_mining.autonomous_controller import (
    AutonomousMetaController,
    AutonomousHealer,
    AutonomousOptimizer,
    AutonomousMiner,
    MiningCircuitBreaker,
    AuditLog,
    MiningActionClass,
    MiningDecision,
    OptimizationTarget,
    CircuitBreakerTripped,
    BreakerState,
)

from pythia_mining.quantum_regeneration import (
    ContextSignal,
    Role,
)


class TestAuditLog:
    """Test audit log infrastructure."""

    def test_audit_log_initialization(self):
        """Test audit log initialization."""
        audit = AuditLog()
        assert len(audit._entries) == 0

    def test_audit_record(self):
        """Test recording audit entries."""
        audit = AuditLog()
        entry = audit.record(
            subsystem="test", action="test_action", detail={"key": "value"}, reversible=True
        )
        assert entry.subsystem == "test"
        assert entry.action == "test_action"
        assert entry.reversible
        assert len(audit._entries) == 1

    def test_audit_recent(self):
        """Test retrieving recent audit entries."""
        audit = AuditLog()
        for i in range(10):
            audit.record("subsystem", f"action_{i}", {"i": i}, True)

        recent = audit.recent(n=5)
        assert len(recent) == 5
        assert recent[0].action == "action_5"

    def test_audit_recent_filtered(self):
        """Test retrieving recent entries filtered by subsystem."""
        audit = AuditLog()
        for i in range(10):
            subsystem = "healing" if i % 2 == 0 else "optimizing"
            audit.record(subsystem, f"action_{i}", {"i": i}, True)

        healing_recent = audit.recent(subsystem="healing", n=5)
        assert all(e.subsystem == "healing" for e in healing_recent)

    def test_audit_count_by_subsystem(self):
        """Test counting entries by subsystem."""
        audit = AuditLog()
        for i in range(10):
            subsystem = "healing" if i % 2 == 0 else "optimizing"
            audit.record(subsystem, f"action_{i}", {"i": i}, True)

        counts = audit.count_by_subsystem()
        assert counts["healing"] == 5
        assert counts["optimizing"] == 5


class TestAutonomousHealer:
    """Test autonomous healing subsystem."""

    def test_healer_initialization(self):
        """Test healer initialization."""
        audit = AuditLog()
        healer = AutonomousHealer(audit, entropy_fault_threshold=0.3)
        assert healer.entropy_fault_threshold == 0.3
        assert len(healer.module_states) == 0

    def test_healer_register_module(self):
        """Test registering modules for healing."""
        audit = AuditLog()
        healer = AutonomousHealer(audit)
        healer.register_module("test_module")
        assert "test_module" in healer.module_states

    def test_healer_monitor_tick(self):
        """Test healing monitor tick."""
        audit = AuditLog()
        healer = AutonomousHealer(audit)
        healer.register_module("test_module")

        context = ContextSignal(
            clifford_index=0, target_role=Role.HEALTHY_SPECIALIZED, confidence=0.9
        )

        trace = healer.monitor_tick(module_id="test_module", observed_severity=0.5, context=context)

        assert "module_id" in trace
        assert "status" in trace
        assert len(audit._entries) > 0

    def test_healer_innervation_failure(self):
        """Test innervation failure handling."""
        audit = AuditLog()
        healer = AutonomousHealer(audit)
        healer.register_module("test_module")

        # No context signal should trigger innervation failure
        trace = healer.monitor_tick(module_id="test_module", observed_severity=0.5, context=None)

        assert trace["status"] == "innervation_failure"


class TestAutonomousOptimizer:
    """Test autonomous optimizing subsystem."""

    def test_optimizer_initialization(self):
        """Test optimizer initialization."""
        audit = AuditLog()
        optimizer = AutonomousOptimizer(audit)
        assert len(optimizer.targets) == 0

    def test_optimizer_register_target(self):
        """Test registering optimization targets."""
        audit = AuditLog()
        optimizer = AutonomousOptimizer(audit)

        target = OptimizationTarget(
            name="test_param",
            current_value=0.5,
            bounds=(0.0, 1.0),
            step_size=0.1,
            objective_fn=lambda x: -((x - 0.7) ** 2),  # Peak at 0.7
        )

        optimizer.register_target(target)
        assert "test_param" in optimizer.targets
        assert "test_param" in optimizer.history

    def test_optimizer_tick(self):
        """Test optimization tick."""
        audit = AuditLog()
        optimizer = AutonomousOptimizer(audit)

        target = OptimizationTarget(
            name="test_param",
            current_value=0.5,
            bounds=(0.0, 1.0),
            step_size=0.1,
            objective_fn=lambda x: -((x - 0.7) ** 2),  # Peak at 0.7
        )

        optimizer.register_target(target)

        # Should move toward 0.7
        new_value = optimizer.optimize_tick("test_param")
        assert new_value >= 0.5  # Should increase toward 0.7

    def test_optimizer_bounds_clamp(self):
        """Test that parameters stay within bounds."""
        audit = AuditLog()
        optimizer = AutonomousOptimizer(audit)

        target = OptimizationTarget(
            name="test_param",
            current_value=0.1,
            bounds=(0.0, 1.0),
            step_size=0.2,
            objective_fn=lambda x: x,  # Always increase
        )

        optimizer.register_target(target)

        # Try to optimize beyond bounds
        for _ in range(10):
            optimizer.optimize_tick("test_param")

        assert 0.0 <= optimizer.targets["test_param"].current_value <= 1.0

    def test_optimizer_rollback(self):
        """Test parameter rollback."""
        audit = AuditLog()
        optimizer = AutonomousOptimizer(audit)

        target = OptimizationTarget(
            name="test_param",
            current_value=0.5,
            bounds=(0.0, 1.0),
            step_size=0.1,
            objective_fn=lambda x: -((x - 0.7) ** 2),
        )

        optimizer.register_target(target)

        initial_value = target.current_value
        optimizer.optimize_tick("test_param")

        # Rollback
        restored = optimizer.rollback("test_param", steps=1)
        assert restored == initial_value
        assert target.current_value == initial_value

    def test_optimizer_get_history(self):
        """Test retrieving optimization history."""
        audit = AuditLog()
        optimizer = AutonomousOptimizer(audit)

        target = OptimizationTarget(
            name="test_param",
            current_value=0.5,
            bounds=(0.0, 1.0),
            step_size=0.1,
            objective_fn=lambda x: -((x - 0.7) ** 2),
        )

        optimizer.register_target(target)

        for _ in range(5):
            optimizer.optimize_tick("test_param")

        history = optimizer.get_history("test_param")
        assert len(history) == 5


class TestMiningCircuitBreaker:
    """Test mining circuit breaker."""

    def test_breaker_initialization(self):
        """Test circuit breaker initialization."""
        breaker = MiningCircuitBreaker()
        assert MiningActionClass.POOL_SWITCH in breaker.breakers
        assert MiningActionClass.PAYOUT_ADDRESS_CHANGE in breaker.breakers
        assert MiningActionClass.SPEND_PAST_BUDGET in breaker.breakers

    def test_breaker_gate_ungated_action(self):
        """Test that ungated actions pass through."""
        breaker = MiningCircuitBreaker()
        # INTERNAL_TUNING is not gated
        breaker.gate(MiningActionClass.INTERNAL_TUNING)
        # Should not raise

    def test_breaker_gate_gated_action(self):
        """Test that gated actions are rate-limited."""
        breaker = MiningCircuitBreaker()

        # First action should pass
        breaker.gate(MiningActionClass.POOL_SWITCH)

        # Second action should pass
        breaker.gate(MiningActionClass.POOL_SWITCH)

        # Third action should pass
        breaker.gate(MiningActionClass.POOL_SWITCH)

        # Fourth action should trigger cooldown
        with pytest.raises(CircuitBreakerTripped):
            breaker.gate(MiningActionClass.POOL_SWITCH)

    def test_breaker_cooldown(self):
        """Test cooldown mechanism."""
        breaker = MiningCircuitBreaker()

        # Exhaust rate limit
        for _ in range(3):
            breaker.gate(MiningActionClass.POOL_SWITCH)

        # Should be in cooldown
        with pytest.raises(CircuitBreakerTripped):
            breaker.gate(MiningActionClass.POOL_SWITCH)

        # Manually set cooldown to past to test cooldown expiration
        breaker.breakers[MiningActionClass.POOL_SWITCH]._cooldown_until = time.time() - 1.0

        # Clear timestamps to allow new actions
        breaker.breakers[MiningActionClass.POOL_SWITCH]._timestamps.clear()

        # Should now pass
        breaker.gate(MiningActionClass.POOL_SWITCH)

    def test_breaker_status(self):
        """Test getting breaker status."""
        breaker = MiningCircuitBreaker()

        status = breaker.get_breaker_status(MiningActionClass.POOL_SWITCH)
        assert status["gated"]
        assert "max_actions" in status
        assert "window_seconds" in status

    def test_breaker_ungated_status(self):
        """Test status for ungated action."""
        breaker = MiningCircuitBreaker()

        status = breaker.get_breaker_status(MiningActionClass.INTERNAL_TUNING)
        assert not status["gated"]


class TestAutonomousMiner:
    """Test autonomous mining subsystem."""

    def test_miner_initialization(self):
        """Test miner initialization."""
        audit = AuditLog()
        breaker = MiningCircuitBreaker()

        def dummy_policy(telemetry):
            return MiningDecision(
                action_class=MiningActionClass.INTERNAL_TUNING,
                payload={"param": "value"},
                reversible=True,
            )

        miner = AutonomousMiner(audit, breaker, dummy_policy)
        assert miner.decision_policy == dummy_policy

    def test_miner_tick_ungated(self):
        """Test miner tick with ungated action."""
        audit = AuditLog()
        breaker = MiningCircuitBreaker()

        def dummy_policy(telemetry):
            return MiningDecision(
                action_class=MiningActionClass.INTERNAL_TUNING,
                payload={"param": "value"},
                reversible=True,
            )

        miner = AutonomousMiner(audit, breaker, dummy_policy)

        # Mock execute_action to avoid NotImplementedError
        miner._execute_action = lambda decision: {"success": True}

        result = miner.tick({"telemetry": "data"})
        assert result["status"] == "executed"

    def test_miner_tick_gated_blocked(self):
        """Test miner tick with gated action blocked by breaker."""
        audit = AuditLog()
        breaker = MiningCircuitBreaker()

        def dummy_policy(telemetry):
            return MiningDecision(
                action_class=MiningActionClass.POOL_SWITCH,
                payload={"pool": "new_pool"},
                reversible=True,
            )

        miner = AutonomousMiner(audit, breaker, dummy_policy)

        # Exhaust rate limit
        for _ in range(3):
            breaker.gate(MiningActionClass.POOL_SWITCH)

        result = miner.tick({"telemetry": "data"})
        assert result["status"] == "blocked"
        assert "reason" in result

    def test_miner_execute_action_not_implemented(self):
        """Test that execute_action raises NotImplementedError by default."""
        audit = AuditLog()
        breaker = MiningCircuitBreaker()

        def dummy_policy(telemetry):
            return MiningDecision(
                action_class=MiningActionClass.INTERNAL_TUNING,
                payload={"param": "value"},
                reversible=True,
            )

        miner = AutonomousMiner(audit, breaker, dummy_policy)

        with pytest.raises(NotImplementedError):
            miner._execute_action(
                MiningDecision(
                    action_class=MiningActionClass.INTERNAL_TUNING,
                    payload={"param": "value"},
                    reversible=True,
                )
            )


class TestAutonomousMetaController:
    """Test autonomous meta-controller."""

    def test_meta_controller_initialization(self):
        """Test meta-controller initialization."""
        controller = AutonomousMetaController()
        assert controller.audit is not None
        assert controller.healer is not None
        assert controller.optimizer is not None
        assert controller.breaker is not None
        assert controller.miner is None

    def test_meta_controller_attach_miner(self):
        """Test attaching miner to meta-controller."""
        controller = AutonomousMetaController()

        def dummy_policy(telemetry):
            return MiningDecision(
                action_class=MiningActionClass.INTERNAL_TUNING,
                payload={"param": "value"},
                reversible=True,
            )

        controller.attach_miner(dummy_policy)
        assert controller.miner is not None

    def test_meta_controller_tick_all(self):
        """Test full control loop tick."""
        controller = AutonomousMetaController()

        # Register modules for healing
        controller.healer.register_module("module_1")
        controller.healer.register_module("module_2")

        # Register optimization targets
        target = OptimizationTarget(
            name="test_param",
            current_value=0.5,
            bounds=(0.0, 1.0),
            step_size=0.1,
            objective_fn=lambda x: -((x - 0.7) ** 2),
        )
        controller.optimizer.register_target(target)

        # Attach miner
        def dummy_policy(telemetry):
            return MiningDecision(
                action_class=MiningActionClass.INTERNAL_TUNING,
                payload={"param": "value"},
                reversible=True,
            )

        controller.attach_miner(dummy_policy)
        controller.miner._execute_action = lambda decision: {"success": True}

        # Execute tick
        healing_inputs = [
            {"module_id": "module_1", "severity": 0.5, "context": None},
            {"module_id": "module_2", "severity": 0.3, "context": None},
        ]
        optimization_targets = ["test_param"]
        mining_telemetry = {"hashrate": 100.0}

        results = controller.tick_all(healing_inputs, optimization_targets, mining_telemetry)

        assert "healing" in results
        assert "optimizing" in results
        assert "mining" in results
        assert len(results["healing"]) == 2
        assert len(results["optimizing"]) == 1

    def test_meta_controller_get_audit_summary(self):
        """Test getting audit summary."""
        controller = AutonomousMetaController()

        # Record some actions
        controller.audit.record("healing", "action1", {}, True)
        controller.audit.record("optimizing", "action2", {}, True)
        controller.audit.record("mining", "action3", {}, True)

        summary = controller.get_audit_summary()
        assert summary["total_entries"] == 3
        assert summary["by_subsystem"]["healing"] == 1
        assert summary["by_subsystem"]["optimizing"] == 1
        assert summary["by_subsystem"]["mining"] == 1

    def test_meta_controller_get_breaker_status(self):
        """Test getting breaker status."""
        controller = AutonomousMetaController()

        status = controller.get_breaker_status()
        assert "pool_switch" in status
        assert "payout_address_change" in status
        assert "spend_past_budget" in status

    def test_meta_controller_without_miner(self):
        """Test tick without miner attached."""
        controller = AutonomousMetaController()

        # Register modules for healing
        controller.healer.register_module("module_1")

        # Register optimization targets
        target = OptimizationTarget(
            name="test_param",
            current_value=0.5,
            bounds=(0.0, 1.0),
            step_size=0.1,
            objective_fn=lambda x: -((x - 0.7) ** 2),
        )
        controller.optimizer.register_target(target)

        # Execute tick without miner
        healing_inputs = [{"module_id": "module_1", "severity": 0.5, "context": None}]
        optimization_targets = ["test_param"]

        results = controller.tick_all(healing_inputs, optimization_targets, None)

        assert results["mining"] is None
        assert len(results["healing"]) == 1
        assert len(results["optimizing"]) == 1


class TestBreakerState:
    """Test breaker state."""

    def test_breaker_state_initialization(self):
        """Test breaker state initialization."""
        state = BreakerState(
            action_class=MiningActionClass.POOL_SWITCH,
            max_actions=3,
            window_seconds=3600,
            cooldown_seconds=1800,
        )
        assert state.action_class == MiningActionClass.POOL_SWITCH
        assert state.max_actions == 3
        assert len(state._timestamps) == 0

    def test_breaker_state_check_and_record(self):
        """Test check and record mechanism."""
        state = BreakerState(
            action_class=MiningActionClass.POOL_SWITCH,
            max_actions=3,
            window_seconds=3600,
            cooldown_seconds=1800,
        )

        # First action should pass
        state.check_and_record(time.time())
        assert len(state._timestamps) == 1

    def test_breaker_state_rate_limit(self):
        """Test rate limiting."""
        state = BreakerState(
            action_class=MiningActionClass.POOL_SWITCH,
            max_actions=2,
            window_seconds=3600,
            cooldown_seconds=1800,
        )

        now = time.time()

        # First two actions should pass
        state.check_and_record(now)
        state.check_and_record(now)

        # Third should trigger cooldown
        with pytest.raises(CircuitBreakerTripped):
            state.check_and_record(now)

    def test_breaker_state_window_expiration(self):
        """Test that timestamps expire after window."""
        state = BreakerState(
            action_class=MiningActionClass.POOL_SWITCH,
            max_actions=2,
            window_seconds=1.0,
            cooldown_seconds=10.0,
        )

        now = time.time()

        # First action at t=0
        state.check_and_record(now)

        # Second action at t=0.5 (within window)
        state.check_and_record(now + 0.5)

        # Third action at t=2.0 (outside window, first should expire)
        state.check_and_record(now + 2.0)

        # Should have 2 timestamps (first expired, second and third remain)
        # Actually, the second at 0.5 is also outside the 1.0 window from 2.0
        # So only the third should remain
        assert len(state._timestamps) == 1

    def test_breaker_state_remaining_cooldown(self):
        """Test getting remaining cooldown."""
        state = BreakerState(
            action_class=MiningActionClass.POOL_SWITCH,
            max_actions=1,
            window_seconds=3600,
            cooldown_seconds=10.0,
        )

        now = time.time()

        # Manually set cooldown to future
        state._cooldown_until = now + 5.0

        remaining = state.get_remaining_cooldown(now)
        assert remaining > 0
        assert remaining <= 5.0

    def test_breaker_state_window_count(self):
        """Test getting window count."""
        state = BreakerState(
            action_class=MiningActionClass.POOL_SWITCH,
            max_actions=5,
            window_seconds=3600,
            cooldown_seconds=1800,
        )

        now = time.time()

        for i in range(3):
            state.check_and_record(now)

        count = state.get_window_count(now)
        assert count == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
