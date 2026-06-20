"""Standalone validation for Autonomous QaaS/CIaaS Controller

Validates core functionality without pytest dependency.
"""

import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "python_backend"))

from pythia_mining.autonomous_qaas_controller import (
    create_autonomous_controller,
    ServiceHealthMetrics,
)


def test_initialization():
    """Test controller initialization."""
    print("✓ Test 1: Controller initialization")
    controller = create_autonomous_controller("test-001", "qaas", Path("/tmp/test_autonomous"))
    assert controller.service_id == "test-001"
    assert controller.service_kind == "qaas"
    assert not controller._active
    print("  ✓ Initialized successfully")


def test_start_stop():
    """Test start/stop lifecycle."""
    print("✓ Test 2: Start/stop lifecycle")
    controller = create_autonomous_controller("test-002", "qaas", Path("/tmp/test_autonomous"))
    
    start_result = controller.start()
    assert start_result["status"] == "autonomous_controller_active"
    assert controller._active
    print("  ✓ Started successfully")
    
    stop_result = controller.stop()
    assert stop_result["status"] == "autonomous_controller_stopped"
    assert not controller._active
    print("  ✓ Stopped successfully")


def test_health_metrics():
    """Test health metrics computation."""
    print("✓ Test 3: Health metrics computation")
    controller = create_autonomous_controller("test-003", "qaas", Path("/tmp/test_autonomous"))
    controller.start()
    
    # Record successful executions
    for _ in range(10):
        controller.record_execution(
            execution_time_ms=50.0,
            logical_error_rate=0.001,
            correction_success=True,
        )
    
    metrics = controller.get_health_metrics()
    assert metrics.workload_count == 10, f"Expected 10 workloads, got {metrics.workload_count}"
    assert abs(metrics.logical_error_rate - 0.001) < 1e-9, f"Expected error rate 0.001, got {metrics.logical_error_rate}"
    assert metrics.correction_success_rate == 1.0, f"Expected 100% success, got {metrics.correction_success_rate}"
    assert metrics.consecutive_failures == 0, f"Expected 0 failures, got {metrics.consecutive_failures}"
    assert metrics.health_score > 0.5, f"Expected health_score > 0.5, got {metrics.health_score}"
    print(f"  ✓ Health score: {metrics.health_score:.3f}")


def test_healing_trigger():
    """Test healing triggers on degradation."""
    print("✓ Test 4: Healing trigger detection")
    controller = create_autonomous_controller("test-004", "qaas", Path("/tmp/test_autonomous"))
    controller.start()
    
    # Degrade health
    for _ in range(5):
        controller.record_execution(
            execution_time_ms=50.0,
            logical_error_rate=0.009,
            correction_success=False,
        )
    
    metrics = controller.get_health_metrics()
    trigger = controller.should_trigger_healing(metrics)
    assert trigger is not None
    print(f"  ✓ Trigger detected: {trigger}")


def test_autonomous_healing():
    """Test autonomous healing execution."""
    print("✓ Test 5: Autonomous healing")
    import uuid
    unique_id = f"test-heal-{uuid.uuid4().hex[:8]}"
    controller = create_autonomous_controller(unique_id, "qaas", Path("/tmp/test_autonomous"))
    controller.start()
    controller._consecutive_failures = 3
    
    heal_result = controller.heal("consecutive_correction_failures")
    assert heal_result.success, f"Expected healing success, got {heal_result.success}"
    assert controller._consecutive_failures == 0, f"Expected 0 failures after heal, got {controller._consecutive_failures}"
    print(f"  ✓ Healing action: {heal_result.action}")


def test_circuit_breaker():
    """Test circuit breaker failover."""
    print("✓ Test 6: Circuit breaker protection")
    controller = create_autonomous_controller("test-006", "qaas", Path("/tmp/test_autonomous"))
    controller.start()
    
    # Trigger multiple heal attempts
    for i in range(6):
        controller.heal(f"test_trigger_{i}")
    
    # Next heal should trigger circuit breaker
    heal_result = controller.heal("error_rate_spike")
    assert heal_result.action == "failover_to_backup"
    assert not heal_result.success
    print("  ✓ Circuit breaker triggered failover")


def test_optimization_proposal():
    """Test self-optimization proposal generation."""
    print("✓ Test 7: Self-optimization proposals")
    controller = create_autonomous_controller("test-007", "qaas", Path("/tmp/test_autonomous"))
    controller.start()
    
    # Record successful executions
    for _ in range(20):
        controller.record_execution(
            execution_time_ms=50.0,
            logical_error_rate=0.001,
            correction_success=True,
        )
    
    metrics = controller.get_health_metrics()
    proposal = controller.propose_optimization(
        current_code_distance=7,
        current_error_rate=0.001,
        metrics=metrics,
    )
    
    assert proposal is not None
    assert proposal.parameter == "code_distance"
    print(f"  ✓ Proposal: {proposal.parameter} {proposal.current_value} → {proposal.proposed_value}")


def test_state_persistence():
    """Test state persistence across restarts."""
    print("✓ Test 8: State persistence")
    temp_dir = Path("/tmp/test_autonomous_persist")
    
    # Create and use controller
    controller1 = create_autonomous_controller("test-persist-001", "qaas", temp_dir)
    controller1.start()
    controller1._optimization_epochs = 10
    controller1._save_state()
    controller1.stop()
    
    # Create new instance and verify restoration
    controller2 = create_autonomous_controller("test-persist-001", "qaas", temp_dir)
    assert controller2._optimization_epochs == 10
    print(f"  ✓ Restored optimization epochs: {controller2._optimization_epochs}")


def test_comprehensive_status():
    """Test comprehensive status reporting."""
    print("✓ Test 9: Comprehensive status")
    controller = create_autonomous_controller("test-009", "qaas", Path("/tmp/test_autonomous"))
    controller.start()
    
    # Record activity
    for _ in range(5):
        controller.record_execution(
            execution_time_ms=50.0,
            logical_error_rate=0.001,
            correction_success=True,
        )
    
    status = controller.get_status()
    assert status["service_id"] == "test-009"
    assert status["service_kind"] == "qaas"
    assert status["active"] is True
    assert "health_score" in status
    assert "health_metrics" in status
    assert "optimization" in status
    assert "healing" in status
    print("  ✓ Status includes all required fields")


def main():
    """Run all validation tests."""
    print("\n" + "=" * 70)
    print("AUTONOMOUS QAAS/CIAAS CONTROLLER VALIDATION")
    print("=" * 70 + "\n")
    
    tests = [
        test_initialization,
        test_start_stop,
        test_health_metrics,
        test_healing_trigger,
        test_autonomous_healing,
        test_circuit_breaker,
        test_optimization_proposal,
        test_state_persistence,
        test_comprehensive_status,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"  ✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"RESULTS: {passed}/{len(tests)} tests passed")
    if failed == 0:
        print("✓ All tests passed - Autonomous controller validated")
    else:
        print(f"✗ {failed} test(s) failed")
    print("=" * 70 + "\n")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
