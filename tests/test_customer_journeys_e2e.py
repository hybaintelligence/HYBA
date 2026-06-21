"""
End-to-End Customer Journey Tests

Maps complete customer workflows through the integrated system:
- Developer trial journey
- Enterprise customer journey  
- Research institution journey
- Failure recovery journey
"""

import pytest
import time
from pathlib import Path

from python_backend.hyba_genesis_api.api.quota_manager import QuotaManager
from python_backend.hyba_genesis_api.api.billing_rollback import BillingRollbackManager
from python_backend.hyba_genesis_api.api.execution_coordinator import ExecutionCoordinator
from python_backend.pythia_mining.autonomous_qaas_controller import AutonomousQaaSController


class TestDeveloperTrialJourney:
    """
    Customer Journey: Developer Trial
    
    Flow:
    1. Sign up with $100 trial credit (1000 work units)
    2. Execute first quantum circuit (successful)
    3. Execute batch of test circuits (mix of success/failure)
    4. Monitor quota consumption
    5. Receive automatic refunds on failures
    6. Review usage and billing history
    """
    
    def test_complete_developer_trial_journey(self, tmp_path):
        """Map complete developer trial journey"""
        # Step 1: Sign up with trial credit
        quota_mgr = QuotaManager()
        billing_mgr = BillingRollbackManager()
        customer_id = "dev_alice_trial"
        
        trial_result = quota_mgr.provision_quota(customer_id, 1000)
        assert trial_result["success"] is True
        assert trial_result["total_quota"] == 1000
        
        # Setup autonomous controller and coordinator
        autonomous = AutonomousQaaSController(
            service_id=f"qaas_{customer_id}",
            service_kind="qaas",
            persistence_dir=tmp_path
        )
        autonomous.start()
        
        coordinator = ExecutionCoordinator(
            autonomous_controller=autonomous,
            quota_manager=quota_mgr,
            billing_manager=billing_mgr
        )
        
        # Step 2: First quantum circuit (successful)
        first_circuit = coordinator.execute_with_protection(
            customer_id=customer_id,
            work_units=50,
            execution_fn=lambda: {
                "circuit_type": "grover_search",
                "qubits": 5,
                "depth": 10,
                "error_rate": 0.001,
                "fidelity": 0.99
            }
        )
        
        assert first_circuit["success"] is True
        assert first_circuit["work_units_charged"] == 50
        assert first_circuit["quota_remaining"] == 950
        
        # Step 3: Batch of test circuits (mix of success/failure)
        batch_circuits = [
            (lambda: {"circuit": "bell_state", "error_rate": 0.0005}, 25, "bell_state_test"),
            (lambda: (_ for _ in ()).throw(RuntimeError("Decoherence")), 30, "failed_entanglement"),
            (lambda: {"circuit": "qft", "error_rate": 0.002}, 40, "qft_test"),
            (lambda: (_ for _ in ()).throw(ValueError("Invalid gate")), 35, "failed_circuit"),
            (lambda: {"circuit": "vqe", "error_rate": 0.0015}, 60, "vqe_optimization"),
        ]
        
        results = []
        for exec_fn, units, exec_id in batch_circuits:
            result = coordinator.execute_with_protection(
                customer_id=customer_id,
                work_units=units,
                execution_fn=exec_fn,
                execution_id=exec_id
            )
            results.append((exec_id, result))
        
        # Step 4: Monitor quota consumption
        status = quota_mgr.get_status(customer_id)
        
        # Successful: 50 + 25 + 40 + 60 = 175
        # Failed (refunded): 30 + 35 = 65
        # Remaining: 1000 - 175 = 825
        assert status["consumed"] == 175
        assert status["available"] == 825
        assert status["statistics"]["total_executions"] == 6  # 5 batch + 1 first
        assert status["statistics"]["total_refunds"] == 2
        
        # Step 5: Verify automatic refunds on failures
        refund_history = billing_mgr.get_rollback_history(customer_id=customer_id)
        assert len(refund_history) == 2
        
        failed_refunds = sum(r["work_units_refunded"] for r in refund_history)
        assert failed_refunds == 65
        
        # Step 6: Review complete usage history
        usage_history = quota_mgr.get_usage_history(customer_id)
        assert len(usage_history) == 8  # 6 consumptions + 2 refunds
        
        consumptions = [h for h in usage_history if h["type"] == "consumption"]
        refunds = [h for h in usage_history if h["type"] == "refund"]
        assert len(consumptions) == 6
        assert len(refunds) == 2
        
        # Verify developer has 825 units remaining for continued experimentation
        final_status = quota_mgr.get_status(customer_id)
        assert final_status["available"] == 825
        assert final_status["utilization_percent"] == 17.5  # 175/1000


class TestEnterpriseCustomerJourney:
    """
    Customer Journey: Enterprise Customer
    
    Flow:
    1. Provision 10,000 work units ($1,000/month subscription)
    2. Run production quantum optimization workload
    3. Experience infrastructure failure (automatic recovery)
    4. Autonomous controller detects and heals
    5. Continue with optimized parameters
    6. Daily reconciliation report for accounting
    """
    
    def test_complete_enterprise_customer_journey(self, tmp_path):
        """Map complete enterprise customer journey"""
        # Step 1: Enterprise provisioning
        quota_mgr = QuotaManager()
        billing_mgr = BillingRollbackManager()
        customer_id = "enterprise_acme_corp"
        
        provision_result = quota_mgr.provision_quota(customer_id, 10000)
        assert provision_result["total_quota"] == 10000
        
        # Setup with autonomous controller
        autonomous = AutonomousQaaSController(
            service_id=f"qaas_enterprise_{customer_id}",
            service_kind="qaas",
            persistence_dir=tmp_path
        )
        autonomous.start()
        
        coordinator = ExecutionCoordinator(
            autonomous_controller=autonomous,
            quota_manager=quota_mgr,
            billing_manager=billing_mgr
        )
        
        # Step 2: Production quantum optimization workload
        production_results = []
        for i in range(10):
            result = coordinator.execute_with_protection(
                customer_id=customer_id,
                work_units=200,
                execution_fn=lambda: {
                    "optimization": "portfolio_optimization",
                    "qubits": 20,
                    "depth": 50,
                    "error_rate": 0.0008,
                    "convergence": 0.95
                },
                execution_id=f"prod_optimization_{i}"
            )
            production_results.append(result)
            assert result["success"] is True
        
        # Step 3: Infrastructure failure simulation
        infrastructure_failure = coordinator.execute_with_protection(
            customer_id=customer_id,
            work_units=250,
            execution_fn=lambda: (_ for _ in ()).throw(RuntimeError("Qubit coherence lost")),
            execution_id="infrastructure_failure"
        )
        
        assert infrastructure_failure["success"] is False
        assert infrastructure_failure["work_units_refunded"] == 250
        assert infrastructure_failure["refund_status"] == "refunded"
        
        # Step 4: Autonomous controller detects and heals
        metrics = autonomous.get_health_metrics()
        trigger = autonomous.should_trigger_healing(metrics)
        
        if trigger:
            heal_result = autonomous.heal(trigger)
            assert heal_result.success is True
        
        # Step 5: Continue with optimized parameters
        post_healing_result = coordinator.execute_with_protection(
            customer_id=customer_id,
            work_units=200,
            execution_fn=lambda: {
                "optimization": "portfolio_optimization",
                "qubits": 20,
                "depth": 50,
                "error_rate": 0.0005,  # Improved after healing
                "convergence": 0.97
            },
            execution_id="post_healing_optimization"
        )
        
        assert post_healing_result["success"] is True
        
        # Step 6: Daily reconciliation for accounting
        reconciliation = billing_mgr.reconcile_daily()
        
        # Verify enterprise usage
        status = quota_mgr.get_status(customer_id)
        # 11 successful * 200 = 2200 units consumed
        assert status["consumed"] == 2200
        assert status["available"] == 7800
        assert status["utilization_percent"] == 22.0
        
        # Verify 1 refund recorded
        assert reconciliation["total_refunds"] >= 1
        assert reconciliation["total_work_units_refunded"] >= 250


class TestResearchInstitutionJourney:
    """
    Customer Journey: Research Institution
    
    Flow:
    1. Academic grant allocation (5000 units)
    2. Run exploratory quantum chemistry simulations
    3. Multiple researchers share the quota
    4. Some experiments fail (automatic refunds)
    5. Track refund rate for grant reporting
    6. Export usage history for grant compliance
    """
    
    def test_complete_research_institution_journey(self, tmp_path):
        """Map complete research institution journey"""
        # Step 1: Grant allocation
        quota_mgr = QuotaManager()
        billing_mgr = BillingRollbackManager()
        institution_id = "university_quantum_lab"
        
        grant_result = quota_mgr.provision_quota(institution_id, 5000)
        assert grant_result["total_quota"] == 5000
        
        autonomous = AutonomousQaaSController(
            service_id=f"qaas_research_{institution_id}",
            service_kind="qaas",
            persistence_dir=tmp_path
        )
        autonomous.start()
        
        coordinator = ExecutionCoordinator(
            autonomous_controller=autonomous,
            quota_manager=quota_mgr,
            billing_manager=billing_mgr
        )
        
        # Step 2 & 3: Multiple researchers running simulations
        research_experiments = [
            # Researcher A: Molecular simulations
            (lambda: {"experiment": "h2_molecule", "error_rate": 0.001}, 150, "researcher_a_h2"),
            (lambda: {"experiment": "lih_molecule", "error_rate": 0.0012}, 200, "researcher_a_lih"),
            
            # Researcher B: Quantum chemistry (some failures)
            (lambda: {"experiment": "benzene_ring", "error_rate": 0.0015}, 300, "researcher_b_benzene"),
            (lambda: (_ for _ in ()).throw(ValueError("Basis set error")), 180, "researcher_b_failed"),
            
            # Researcher C: Material science
            (lambda: {"experiment": "graphene_lattice", "error_rate": 0.0011}, 250, "researcher_c_graphene"),
            (lambda: (_ for _ in ()).throw(RuntimeError("Convergence failure")), 220, "researcher_c_failed"),
            
            # Researcher A: Follow-up experiments
            (lambda: {"experiment": "h2o_molecule", "error_rate": 0.0009}, 175, "researcher_a_h2o"),
        ]
        
        for exec_fn, units, exec_id in research_experiments:
            coordinator.execute_with_protection(
                customer_id=institution_id,
                work_units=units,
                execution_fn=exec_fn,
                execution_id=exec_id
            )
        
        # Step 4 & 5: Track refund rate for grant reporting
        status = quota_mgr.get_status(institution_id)
        
        # Successful: 150 + 200 + 300 + 250 + 175 = 1075
        # Failed (refunded): 180 + 220 = 400
        assert status["consumed"] == 1075
        assert status["available"] == 3925
        assert status["statistics"]["total_refunds"] == 2
        assert status["statistics"]["refund_rate"] > 0  # ~28.6%
        
        # Step 6: Export usage history for grant compliance
        usage_history = quota_mgr.get_usage_history(institution_id, limit=100)
        
        # Generate compliance report
        compliance_report = {
            "institution": institution_id,
            "grant_allocation": 5000,
            "units_consumed": status["consumed"],
            "units_remaining": status["available"],
            "total_experiments": status["statistics"]["total_executions"],
            "successful_experiments": status["statistics"]["total_executions"] - status["statistics"]["total_refunds"],
            "failed_experiments": status["statistics"]["total_refunds"],
            "refund_rate": status["statistics"]["refund_rate"],
            "usage_history": usage_history
        }
        
        assert compliance_report["units_consumed"] == 1075
        assert compliance_report["successful_experiments"] == 5
        assert compliance_report["failed_experiments"] == 2


class TestFailureRecoveryJourney:
    """
    Customer Journey: Failure Recovery & Reliability
    
    Flow:
    1. Customer starts with quota
    2. Experiences consecutive failures
    3. Autonomous controller triggers healing
    4. All failures result in automatic refunds
    5. Customer retries after healing
    6. Success - no lost quota from failures
    """
    
    def test_complete_failure_recovery_journey(self, tmp_path):
        """Map complete failure recovery journey"""
        quota_mgr = QuotaManager()
        billing_mgr = BillingRollbackManager()
        customer_id = "customer_recovery_test"
        
        # Step 1: Initial quota
        quota_mgr.provision_quota(customer_id, 1000)
        initial_quota = quota_mgr.get_available(customer_id)
        assert initial_quota == 1000
        
        autonomous = AutonomousQaaSController(
            service_id=f"qaas_recovery_{customer_id}",
            service_kind="qaas",
            persistence_dir=tmp_path
        )
        autonomous.start()
        
        coordinator = ExecutionCoordinator(
            autonomous_controller=autonomous,
            quota_manager=quota_mgr,
            billing_manager=billing_mgr
        )
        
        # Step 2: Consecutive failures
        failures = [
            RuntimeError("Qubit decoherence"),
            TimeoutError("Circuit execution timeout"),
            ValueError("Invalid quantum state"),
        ]
        
        for i, error in enumerate(failures):
            result = coordinator.execute_with_protection(
                customer_id=customer_id,
                work_units=100,
                execution_fn=lambda e=error: (_ for _ in ()).throw(e),
                execution_id=f"failure_{i}"
            )
            assert result["success"] is False
            assert result["work_units_refunded"] == 100
        
        # Step 3: Autonomous controller triggers healing
        metrics = autonomous.get_health_metrics()
        assert metrics.consecutive_failures >= 3
        
        trigger = autonomous.should_trigger_healing(metrics)
        assert trigger is not None
        
        heal_result = autonomous.heal(trigger)
        assert heal_result.success is True
        
        # Step 4: Verify all failures refunded
        refund_history = billing_mgr.get_rollback_history(customer_id=customer_id)
        assert len(refund_history) == 3
        total_refunded = sum(r["work_units_refunded"] for r in refund_history)
        assert total_refunded == 300
        
        # Verify quota fully restored
        quota_after_failures = quota_mgr.get_available(customer_id)
        assert quota_after_failures == 1000  # Fully restored
        
        # Step 5: Customer retries after healing
        retry_result = coordinator.execute_with_protection(
            customer_id=customer_id,
            work_units=100,
            execution_fn=lambda: {
                "circuit": "successful_after_healing",
                "error_rate": 0.0005,
                "fidelity": 0.995
            },
            execution_id="successful_retry"
        )
        
        # Step 6: Success - no lost quota
        assert retry_result["success"] is True
        assert retry_result["work_units_charged"] == 100
        
        final_quota = quota_mgr.get_available(customer_id)
        assert final_quota == 900  # Only successful execution consumed
        
        # Verify customer experience
        status = quota_mgr.get_status(customer_id)
        assert status["consumed"] == 100  # Only 1 successful
        assert status["available"] == 900
        assert status["statistics"]["total_executions"] == 4  # 3 failed + 1 success
        assert status["statistics"]["total_refunds"] == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
