"""Tests for Autonomous QaaS/CIaaS Self-Healing and Self-Optimizing Controller"""

import json
import time
from pathlib import Path

import pytest

from pythia_mining.autonomous_qaas_controller import (
    AutonomousQaaSController,
    HealAttempt,
    OptimizationProposal,
    ServiceHealthMetrics,
    create_autonomous_controller,
)


@pytest.fixture
def temp_persistence_dir(tmp_path):
    """Provide temporary persistence directory for tests."""
    return tmp_path / "autonomous_qaas_test"


@pytest.fixture
def qaas_controller(temp_persistence_dir):
    """Create QaaS autonomous controller for testing."""
    return create_autonomous_controller(
        service_id="test-qaas-001",
        service_kind="qaas",
        persistence_dir=temp_persistence_dir,
    )


@pytest.fixture
def ciaas_controller(temp_persistence_dir):
    """Create CIaaS autonomous controller for testing."""
    return create_autonomous_controller(
        service_id="test-ciaas-001",
        service_kind="ciaas",
        persistence_dir=temp_persistence_dir,
    )


def test_controller_initialization(qaas_controller):
    """Test autonomous controller initializes with correct defaults."""
    assert qaas_controller.service_id == "test-qaas-001"
    assert qaas_controller.service_kind == "qaas"
    assert qaas_controller._active is False
    assert qaas_controller._consecutive_failures == 0
    assert qaas_controller._optimization_epochs == 0


def test_controller_start_stop(qaas_controller):
    """Test controller start and stop lifecycle."""
    # Start controller
    start_result = qaas_controller.start()
    assert start_result["status"] == "autonomous_controller_active"
    assert start_result["service_id"] == "test-qaas-001"
    assert qaas_controller._active is True
    
    # Stop controller
    stop_result = qaas_controller.stop()
    assert stop_result["status"] == "autonomous_controller_stopped"
    assert qaas_controller._active is False


def test_health_metrics_computation(qaas_controller):
    """Test health metrics are computed correctly from execution history."""
    qaas_controller.start()
    
    # Record successful executions
    for _ in range(10):
        qaas_controller.record_execution(
            execution_time_ms=50.0,
            logical_error_rate=0.001,
            correction_success=True,
        )
    
    metrics = qaas_controller.get_health_metrics()
    assert metrics.workload_count == 10
    assert metrics.logical_error_rate == pytest.approx(0.001)
    assert metrics.correction_success_rate == 1.0
    assert metrics.consecutive_failures == 0
    assert metrics.health_score > 0.8


def test_health_score_degradation_detection(qaas_controller):
    """Test health score degrades when error rates increase."""
    qaas_controller.start()
    
    # Record failing executions
    for _ in range(10):
        qaas_controller.record_execution(
            execution_time_ms=50.0,
            logical_error_rate=0.008,  # High error rate
            correction_success=False,
        )
    
    metrics = qaas_controller.get_health_metrics()
    assert metrics.health_score < 0.5
    assert metrics.consecutive_failures == 10


def test_healing_trigger_on_health_degradation(qaas_controller):
    """Test healing triggers automatically when health score drops."""
    qaas_controller.start()
    
    # Degrade health
    for _ in range(5):
        qaas_controller.record_execution(
            execution_time_ms=50.0,
            logical_error_rate=0.009,
            correction_success=False,
        )
    
    metrics = qaas_controller.get_health_metrics()
    trigger = qaas_controller.should_trigger_healing(metrics)
    
    assert trigger is not None
    assert trigger in ("health_score_below_threshold", "consecutive_correction_failures", "error_rate_spike")


def test_autonomous_soft_reset_healing(qaas_controller):
    """Test autonomous soft reset clears transient failures."""
    qaas_controller.start()
    qaas_controller._consecutive_failures = 5
    
    heal_result = qaas_controller.heal("health_score_below_threshold")
    
    assert heal_result.action == "soft_reset"
    assert heal_result.success is True
    assert qaas_controller._consecutive_failures == 0


def test_autonomous_recalibration_healing(qaas_controller):
    """Test autonomous recalibration on correction failures."""
    qaas_controller.start()
    qaas_controller._consecutive_failures = 3
    
    heal_result = qaas_controller.heal("consecutive_correction_failures")
    
    assert heal_result.action == "recalibrate_error_model"
    assert heal_result.success is True
    assert qaas_controller._consecutive_failures == 0


def test_circuit_breaker_on_excessive_heal_attempts(qaas_controller):
    """Test circuit breaker triggers failover after excessive heal attempts."""
    qaas_controller.start()
    
    # Trigger 6 heal attempts in short window
    for i in range(6):
        qaas_controller.heal(f"test_trigger_{i}")
    
    # Next heal should trigger circuit breaker
    heal_result = qaas_controller.heal("error_rate_spike")
    
    assert heal_result.action == "failover_to_backup"
    assert heal_result.success is False


def test_optimization_proposal_generation(qaas_controller):
    """Test self-optimization proposals are generated based on metrics."""
    qaas_controller.start()
    
    # Record successful executions with high correction rate
    for _ in range(20):
        qaas_controller.record_execution(
            execution_time_ms=50.0,
            logical_error_rate=0.001,
            correction_success=True,
        )
    
    metrics = qaas_controller.get_health_metrics()
    proposal = qaas_controller.propose_optimization(
        current_code_distance=7,
        current_error_rate=0.001,
        metrics=metrics,
    )
    
    # High success rate should propose reducing code distance
    assert proposal is not None
    assert proposal.parameter == "code_distance"
    assert proposal.proposed_value < proposal.current_value


def test_optimization_proposal_increase_code_distance(qaas_controller):
    """Test proposals increase code distance when error rate is high."""
    qaas_controller.start()
    
    # Record executions with high error rate
    for _ in range(20):
        qaas_controller.record_execution(
            execution_time_ms=50.0,
            logical_error_rate=0.004,
            correction_success=True,
        )
    
    metrics = qaas_controller.get_health_metrics()
    proposal = qaas_controller.propose_optimization(
        current_code_distance=7,
        current_error_rate=0.004,
        metrics=metrics,
    )
    
    # High error rate should propose increasing code distance
    assert proposal is not None
    assert proposal.parameter == "code_distance"
    assert proposal.proposed_value > proposal.current_value


def test_optimization_not_proposed_when_unhealthy(qaas_controller):
    """Test optimization proposals are not generated when health is poor."""
    qaas_controller.start()
    
    # Record failing executions
    for _ in range(10):
        qaas_controller.record_execution(
            execution_time_ms=50.0,
            logical_error_rate=0.009,
            correction_success=False,
        )
    
    metrics = qaas_controller.get_health_metrics()
    proposal = qaas_controller.propose_optimization(
        current_code_distance=7,
        current_error_rate=0.001,
        metrics=metrics,
    )
    
    # No proposals when unhealthy
    assert proposal is None


def test_optimization_cooldown_period(qaas_controller):
    """Test optimization respects cooldown period between proposals."""
    qaas_controller.start()
    
    # Record successful executions
    for _ in range(20):
        qaas_controller.record_execution(
            execution_time_ms=50.0,
            logical_error_rate=0.001,
            correction_success=True,
        )
    
    metrics = qaas_controller.get_health_metrics()
    
    # First proposal should succeed
    proposal1 = qaas_controller.propose_optimization(
        current_code_distance=7,
        current_error_rate=0.001,
        metrics=metrics,
    )
    assert proposal1 is not None
    
    # Second proposal should be blocked by cooldown
    proposal2 = qaas_controller.propose_optimization(
        current_code_distance=7,
        current_error_rate=0.001,
        metrics=metrics,
    )
    assert proposal2 is None


def test_apply_optimization_proposal(qaas_controller):
    """Test optimization proposals are applied and tracked."""
    qaas_controller.start()
    
    proposal = OptimizationProposal(
        proposal_id="test_opt_001",
        timestamp=time.time(),
        parameter="code_distance",
        current_value=7.0,
        proposed_value=5.0,
        expected_improvement=0.15,
        confidence=0.8,
    )
    
    success = qaas_controller.apply_optimization(proposal)
    
    assert success is True
    assert proposal.applied is True
    assert qaas_controller._optimization_epochs == 1
    assert len(qaas_controller._proposals) == 1


def test_state_persistence(qaas_controller, temp_persistence_dir):
    """Test autonomous controller state persists across restarts."""
    qaas_controller.start()
    
    # Record execution history
    for _ in range(5):
        qaas_controller.record_execution(
            execution_time_ms=50.0,
            logical_error_rate=0.001,
            correction_success=True,
        )
    
    # Generate proposals
    metrics = qaas_controller.get_health_metrics()
    proposal = qaas_controller.propose_optimization(
        current_code_distance=7,
        current_error_rate=0.001,
        metrics=metrics,
    )
    if proposal:
        qaas_controller.apply_optimization(proposal)
    
    qaas_controller.stop()
    
    # Verify state file exists
    state_file = temp_persistence_dir / "test-qaas-001_autonomous_state.json"
    assert state_file.exists()
    
    # Load state and verify
    state = json.loads(state_file.read_text())
    assert state["service_id"] == "test-qaas-001"
    assert state["service_kind"] == "qaas"
    assert len(state["error_rates"]) == 5


def test_state_restoration(temp_persistence_dir):
    """Test controller restores state on initialization."""
    # Create controller and save state
    controller1 = create_autonomous_controller(
        service_id="test-restore-001",
        service_kind="qaas",
        persistence_dir=temp_persistence_dir,
    )
    controller1.start()
    controller1._optimization_epochs = 10
    controller1._save_state()
    controller1.stop()
    
    # Create new controller instance
    controller2 = create_autonomous_controller(
        service_id="test-restore-001",
        service_kind="qaas",
        persistence_dir=temp_persistence_dir,
    )
    
    # Verify state was restored
    assert controller2._optimization_epochs == 10


def test_get_status_comprehensive(qaas_controller):
    """Test get_status returns comprehensive autonomous state."""
    qaas_controller.start()
    
    # Record some activity
    for _ in range(5):
        qaas_controller.record_execution(
            execution_time_ms=50.0,
            logical_error_rate=0.001,
            correction_success=True,
        )
    
    status = qaas_controller.get_status()
    
    assert status["service_id"] == "test-qaas-001"
    assert status["service_kind"] == "qaas"
    assert status["active"] is True
    assert "health_score" in status
    assert "health_metrics" in status
    assert "optimization" in status
    assert "healing" in status
    assert "claim_boundary" in status


def test_ciaas_controller_behavior(ciaas_controller):
    """Test CIaaS controller behaves identically to QaaS."""
    ciaas_controller.start()
    
    # Record executions
    for _ in range(10):
        ciaas_controller.record_execution(
            execution_time_ms=100.0,
            logical_error_rate=0.002,
            correction_success=True,
        )
    
    metrics = ciaas_controller.get_health_metrics()
    assert metrics.workload_count == 10
    assert metrics.health_score > 0.7
    
    status = ciaas_controller.get_status()
    assert status["service_kind"] == "ciaas"


def test_sliding_window_bounded_memory(qaas_controller):
    """Test execution history maintains bounded sliding window."""
    qaas_controller.start()
    
    # Record more than window size
    for _ in range(150):
        qaas_controller.record_execution(
            execution_time_ms=50.0,
            logical_error_rate=0.001,
            correction_success=True,
        )
    
    # Verify bounded
    assert len(qaas_controller._execution_times) == 100
    assert len(qaas_controller._error_rates) == 100


def test_heal_attempt_sliding_window(qaas_controller):
    """Test heal attempts respect sliding window for circuit breaker."""
    qaas_controller.start()
    
    # Create old heal attempts (outside window)
    old_time = time.time() - 700.0  # 11+ minutes ago
    for i in range(5):
        qaas_controller._heal_attempts.append(
            HealAttempt(
                attempt_id=f"old_{i}",
                timestamp=old_time,
                trigger="test",
                action="soft_reset",
                success=True,
            )
        )
    
    # Recent attempts should not include old ones
    recent = qaas_controller._recent_heal_attempts()
    assert recent == 0


def test_factory_function(temp_persistence_dir):
    """Test factory function creates controllers correctly."""
    qaas = create_autonomous_controller("svc-001", "qaas", temp_persistence_dir)
    ciaas = create_autonomous_controller("svc-002", "ciaas", temp_persistence_dir)
    
    assert qaas.service_kind == "qaas"
    assert ciaas.service_kind == "ciaas"
    assert qaas.service_id != ciaas.service_id
