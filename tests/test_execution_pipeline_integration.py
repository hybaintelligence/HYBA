"""
Integration Tests for Full Execution Pipeline

Tests end-to-end integration of:
- QuotaManager
- BillingRollbackManager
- ExecutionCoordinator
- AutonomousQaaSController
"""

import pytest
import time
from pathlib import Path

from python_backend.hyba_genesis_api.api.quota_manager import QuotaManager
from python_backend.hyba_genesis_api.api.billing_rollback import BillingRollbackManager
from python_backend.hyba_genesis_api.api.execution_coordinator import ExecutionCoordinator
from python_backend.pythia_mining.autonomous_qaas_controller import AutonomousQaaSController


class TestExecutionPipelineIntegration:
    """Test full execution pipeline with all components"""
    
    def test_successful_execution_full_pipeline(self, tmp_path):
        """Verify successful execution through full pipeline"""
        quota_mgr = QuotaManager()
        billing_mgr = BillingRollbackManager()
        quota_mgr.provision_quota("test_customer", 1000)
        
        autonomous = AutonomousQaaSController(
            service_id="test_service",
            service_kind="qaas",
            persistence_dir=tmp_path
        )
        autonomous.start()
        
        coordinator = ExecutionCoordinator(
            autonomous_controller=autonomous,
            quota_manager=quota_mgr,
            billing_manager=billing_mgr
        )
        
        def successful_workload():
            return {"status": "completed", "error_rate": 0.001}
        
        result = coordinator.execute_with_protection(
            customer_id="test_customer",
            work_units=100,
            execution_fn=successful_workload
        )
        
        assert result["success"] is True
        assert result["work_units_charged"] == 100
        assert result["quota_remaining"] == 900
        assert quota_mgr.get_available("test_customer") == 900
        
        history = billing_mgr.get_rollback_history(customer_id="test_customer")
        assert len(history) == 0
    
    def test_failed_execution_triggers_rollback(self, tmp_path):
        """Verify failed execution triggers automatic rollback"""
        quota_mgr = QuotaManager()
        billing_mgr = BillingRollbackManager()
        quota_mgr.provision_quota("fail_customer", 1000)
        
        autonomous = AutonomousQaaSController(
            service_id="fail_service",
            service_kind="qaas",
            persistence_dir=tmp_path
        )
        autonomous.start()
        
        coordinator = ExecutionCoordinator(
            autonomous_controller=autonomous,
            quota_manager=quota_mgr,
            billing_manager=billing_mgr
        )
        
        def failing_workload():
            raise RuntimeError("Quantum decoherence detected")
        
        result = coordinator.execute_with_protection(
            customer_id="fail_customer",
            work_units=150,
            execution_fn=failing_workload
        )
        
        assert result["success"] is False
        assert "RuntimeError" in result["error"]
        assert result["work_units_refunded"] == 150
        assert result["refund_status"] == "refunded"
        assert result["quota_restored"] is True
        assert result["quota_remaining"] == 1000
        assert quota_mgr.get_available("fail_customer") == 1000
        
        history = billing_mgr.get_rollback_history(customer_id="fail_customer")
        assert len(history) == 1
        assert history[0]["work_units_refunded"] == 150
        assert "RuntimeError" in history[0]["reason"]
    
    def test_insufficient_quota_blocks_execution(self):
        """Verify insufficient quota prevents execution"""
        quota_mgr = QuotaManager()
        billing_mgr = BillingRollbackManager()
        quota_mgr.provision_quota("poor_customer", 50)
        
        coordinator = ExecutionCoordinator(
            quota_manager=quota_mgr,
            billing_manager=billing_mgr
        )
        
        def expensive_workload():
            return {"status": "completed"}
        
        result = coordinator.execute_with_protection(
            customer_id="poor_customer",
            work_units=100,
            execution_fn=expensive_workload
        )
        
        assert result["success"] is False
        assert result["error"] == "insufficient_quota"
        assert result["requested_units"] == 100
        assert result["available_units"] == 50
        assert quota_mgr.get_available("poor_customer") == 50
    
    def test_multiple_executions_track_correctly(self, tmp_path):
        """Verify multiple executions track quota and billing correctly"""
        quota_mgr = QuotaManager()
        billing_mgr = BillingRollbackManager()
        quota_mgr.provision_quota("multi_customer", 1000)
        
        autonomous = AutonomousQaaSController(
            service_id="multi_service",
            service_kind="qaas",
            persistence_dir=tmp_path
        )
        autonomous.start()
        
        coordinator = ExecutionCoordinator(
            autonomous_controller=autonomous,
            quota_manager=quota_mgr,
            billing_manager=billing_mgr
        )
        
        executions = [
            (lambda: {"status": "ok"}, 100, True),
            (lambda: {"status": "ok"}, 150, True),
            (lambda: (_ for _ in ()).throw(ValueError("Error 1")), 75, False),
            (lambda: {"status": "ok"}, 200, True),
            (lambda: (_ for _ in ()).throw(TimeoutError("Error 2")), 125, False),
        ]
        
        for exec_fn, units, should_succeed in executions:
            result = coordinator.execute_with_protection(
                customer_id="multi_customer",
                work_units=units,
                execution_fn=exec_fn
            )
            assert result["success"] == should_succeed
        
        assert quota_mgr.get_available("multi_customer") == 550
        
        history = billing_mgr.get_rollback_history(customer_id="multi_customer")
        assert len(history) == 2
        total_refunded = sum(h["work_units_refunded"] for h in history)
        assert total_refunded == 200
        
        status = quota_mgr.get_status("multi_customer")
        assert status["total_quota"] == 1000
        assert status["consumed"] == 450
        assert status["available"] == 550


class TestAutonomousControllerIntegration:
    """Test autonomous controller integration with execution pipeline"""
    
    def test_autonomous_records_successful_executions(self, tmp_path):
        """Verify autonomous controller records successful executions"""
        quota_mgr = QuotaManager()
        billing_mgr = BillingRollbackManager()
        quota_mgr.provision_quota("auto_customer", 1000)
        
        autonomous = AutonomousQaaSController(
            service_id="auto_service",
            service_kind="qaas",
            persistence_dir=tmp_path
        )
        autonomous.start()
        
        coordinator = ExecutionCoordinator(
            autonomous_controller=autonomous,
            quota_manager=quota_mgr,
            billing_manager=billing_mgr
        )
        
        for i in range(10):
            result = coordinator.execute_with_protection(
                customer_id="auto_customer",
                work_units=10,
                execution_fn=lambda: {"status": "ok", "error_rate": 0.001}
            )
            assert result["success"] is True
        
        metrics = autonomous.get_health_metrics()
        assert metrics.workload_count == 10
        assert metrics.consecutive_failures == 0
        assert metrics.health_score > 0.9
    
    def test_autonomous_triggers_healing_on_failures(self, tmp_path):
        """Verify autonomous controller triggers healing after failures"""
        quota_mgr = QuotaManager()
        billing_mgr = BillingRollbackManager()
        quota_mgr.provision_quota("heal_customer", 1000)
        
        autonomous = AutonomousQaaSController(
            service_id="heal_service",
            service_kind="qaas",
            persistence_dir=tmp_path
        )
        autonomous.start()
        
        coordinator = ExecutionCoordinator(
            autonomous_controller=autonomous,
            quota_manager=quota_mgr,
            billing_manager=billing_mgr
        )
        
        for i in range(3):
            result = coordinator.execute_with_protection(
                customer_id="heal_customer",
                work_units=10,
                execution_fn=lambda: (_ for _ in ()).throw(RuntimeError("Fail"))
            )
            assert result["success"] is False
        
        metrics = autonomous.get_health_metrics()
        trigger = autonomous.should_trigger_healing(metrics)
        
        assert trigger is not None
        assert metrics.consecutive_failures >= 3
        
        heal_result = autonomous.heal(trigger)
        assert heal_result.success is True


class TestDailyReconciliationIntegration:
    """Test daily reconciliation with full pipeline"""
    
    def test_daily_reconciliation_aggregates_all_refunds(self, tmp_path):
        """Verify daily reconciliation captures all pipeline refunds"""
        quota_mgr = QuotaManager()
        billing_mgr = BillingRollbackManager()
        
        autonomous = AutonomousQaaSController(
            service_id="recon_service",
            service_kind="qaas",
            persistence_dir=tmp_path
        )
        autonomous.start()
        
        coordinator = ExecutionCoordinator(
            autonomous_controller=autonomous,
            quota_manager=quota_mgr,
            billing_manager=billing_mgr
        )
        
        customers = ["cust_a", "cust_b", "cust_c"]
        for cust in customers:
            quota_mgr.provision_quota(cust, 1000)
        
        failures = [
            ("cust_a", 100, RuntimeError("Error 1")),
            ("cust_b", 75, TimeoutError("Timeout")),
            ("cust_a", 50, ValueError("Error 2")),
            ("cust_c", 150, RuntimeError("Error 3")),
        ]
        
        for customer, units, error in failures:
            coordinator.execute_with_protection(
                customer_id=customer,
                work_units=units,
                execution_fn=lambda e=error: (_ for _ in ()).throw(e)
            )
        
        report = billing_mgr.reconcile_daily()
        
        assert report["total_refunds"] == 4
        assert report["total_work_units_refunded"] == 375
        assert report["affected_customers"] == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
