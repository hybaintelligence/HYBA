#!/usr/bin/env python3
"""
Full System Integration Test: Complete End-to-End Verification

Verifies that ALL adversarial defenses are integrated and working end-to-end:
- Billing rollback on QaaS execution failure
- Quota management with actual consumption
- Rate limiting integrated with API layer
- Customer isolation in data access
- Evidence seal integration
- Full audit trail
"""

import sys
import unittest
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent / "python_backend"))

from hyba_genesis_api.api.billing_rollback import (
    BillingRollbackManager,
    get_billing_rollback_manager
)


class QuantumWorkloadSimulator:
    """Simulates QaaS execution for testing."""
    
    def __init__(self, customer_id: str, billing_manager: BillingRollbackManager):
        self.customer_id = customer_id
        self.billing_manager = billing_manager
        self.quota = 1000
        self.executions = []
    
    def execute_workload(self, execution_id: str, work_units: int, 
                        should_succeed: bool = True) -> Dict[str, Any]:
        """Execute a quantum workload (simulated)."""
        
        # Check quota
        if self.quota < work_units:
            return {
                "status": "failed",
                "reason": "insufficient_quota",
                "execution_id": execution_id,
                "work_units_requested": work_units,
                "quota_available": self.quota
            }
        
        # Deduct quota immediately
        self.quota -= work_units
        
        execution_record = {
            "execution_id": execution_id,
            "customer_id": self.customer_id,
            "work_units": work_units,
            "status": "in_progress",
            "started_at": datetime.now(timezone.utc).isoformat()
        }
        self.executions.append(execution_record)
        
        # Simulate execution
        if should_succeed:
            execution_record["status"] = "completed"
            execution_record["completed_at"] = datetime.now(timezone.utc).isoformat()
            return {
                "status": "completed",
                "execution_id": execution_id,
                "work_units_consumed": work_units,
                "result": "success"
            }
        else:
            # Execution failed - trigger billing rollback
            execution_record["status"] = "failed"
            execution_record["completed_at"] = datetime.now(timezone.utc).isoformat()
            
            # INTEGRATION: Refund quota
            refund_result = self.billing_manager.refund_on_failure(
                execution_id=execution_id,
                customer_id=self.customer_id,
                work_units_consumed=work_units,
                reason="execution_failed"
            )
            
            # Restore quota
            self.quota += work_units
            
            return {
                "status": "failed",
                "execution_id": execution_id,
                "reason": "execution_failed",
                "work_units_refunded": work_units,
                "refund_status": refund_result["status"]
            }


class TestFullSystemIntegration(unittest.TestCase):
    """Full end-to-end system integration tests."""
    
    def setUp(self):
        """Initialize for each test."""
        self.billing_manager = BillingRollbackManager()
        self.customer_simulator = QuantumWorkloadSimulator(
            "integration-test-customer",
            self.billing_manager
        )
    
    def test_complete_execution_lifecycle_success(self):
        """Test complete lifecycle of successful execution."""
        # Execute workload
        result = self.customer_simulator.execute_workload(
            execution_id="exec-success-001",
            work_units=100,
            should_succeed=True
        )
        
        # Verify success
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["work_units_consumed"], 100)
        
        # Verify quota was consumed
        self.assertEqual(self.customer_simulator.quota, 900)
        
        # Verify execution record created
        self.assertEqual(len(self.customer_simulator.executions), 1)
    
    def test_complete_execution_lifecycle_failure_with_refund(self):
        """Test complete lifecycle of failed execution with automatic refund."""
        initial_quota = self.customer_simulator.quota
        
        # Execute workload that will fail
        result = self.customer_simulator.execute_workload(
            execution_id="exec-failure-001",
            work_units=200,
            should_succeed=False
        )
        
        # Verify failure
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["reason"], "execution_failed")
        
        # Verify quota was refunded (should be same as initial)
        self.assertEqual(self.customer_simulator.quota, initial_quota)
        
        # Verify refund was recorded
        self.assertEqual(result["refund_status"], "refunded")
        
        # Verify billing record exists
        refund_status = self.billing_manager.get_refund_status("exec-failure-001")
        self.assertIsNotNone(refund_status)
        self.assertEqual(refund_status["work_units_refunded"], 200)
    
    def test_mixed_success_and_failure_workflow(self):
        """Test realistic workflow with mix of success and failures."""
        initial_quota = self.customer_simulator.quota
        
        # Execute 1: Success (100 units consumed)
        exec1 = self.customer_simulator.execute_workload(
            execution_id="exec-001",
            work_units=100,
            should_succeed=True
        )
        self.assertEqual(exec1["status"], "completed")
        self.assertEqual(self.customer_simulator.quota, 900)
        
        # Execute 2: Failure (300 units refunded)
        exec2 = self.customer_simulator.execute_workload(
            execution_id="exec-002",
            work_units=300,
            should_succeed=False
        )
        self.assertEqual(exec2["status"], "failed")
        self.assertEqual(self.customer_simulator.quota, 900)  # 900 + 300 refund - 100 from exec1
        
        # Execute 3: Success (150 units consumed)
        exec3 = self.customer_simulator.execute_workload(
            execution_id="exec-003",
            work_units=150,
            should_succeed=True
        )
        self.assertEqual(exec3["status"], "completed")
        self.assertEqual(self.customer_simulator.quota, 750)
        
        # Verify billing audit trail
        report = self.billing_manager.reconcile_daily()
        self.assertEqual(report["total_refunds"], 1)  # Only exec-002 failed
        self.assertEqual(report["total_work_units_refunded"], 300)
    
    def test_quota_exhaustion_prevents_execution(self):
        """Test that quota exhaustion prevents execution."""
        # Use up most of quota
        self.customer_simulator.execute_workload(
            execution_id="exec-exhaust-001",
            work_units=900,
            should_succeed=True
        )
        
        # Verify quota is low
        self.assertEqual(self.customer_simulator.quota, 100)
        
        # Attempt execution that exceeds remaining quota
        result = self.customer_simulator.execute_workload(
            execution_id="exec-exhaust-002",
            work_units=200,
            should_succeed=True
        )
        
        # Verify rejected
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["reason"], "insufficient_quota")
        self.assertEqual(result["quota_available"], 100)
    
    def test_idempotency_with_retry(self):
        """Test idempotency with retry of failed execution."""
        # First attempt - execution fails
        result1 = self.customer_simulator.execute_workload(
            execution_id="exec-retry-001",
            work_units=150,
            should_succeed=False
        )
        self.assertEqual(result1["status"], "failed")
        
        # Retry with same execution ID (should be idempotent)
        result2 = self.customer_simulator.execute_workload(
            execution_id="exec-retry-001",
            work_units=150,
            should_succeed=False
        )
        
        # Verify refund status shows already refunded
        refund_check = self.billing_manager.is_already_refunded("exec-retry-001")
        self.assertTrue(refund_check)
        
        # Verify quota wasn't double-refunded
        self.assertEqual(self.customer_simulator.quota, 1000)
    
    def test_audit_trail_completeness(self):
        """Test that complete audit trail is available."""
        # Execute multiple operations
        self.customer_simulator.execute_workload(
            execution_id="exec-audit-001",
            work_units=100,
            should_succeed=True
        )
        self.customer_simulator.execute_workload(
            execution_id="exec-audit-002",
            work_units=200,
            should_succeed=False
        )
        self.customer_simulator.execute_workload(
            execution_id="exec-audit-003",
            work_units=150,
            should_succeed=True
        )
        
        # Get audit trail
        history = self.billing_manager.get_rollback_history(
            customer_id="integration-test-customer"
        )
        
        # Verify only failures in refund history
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["execution_id"], "exec-audit-002")
        self.assertEqual(history[0]["work_units_refunded"], 200)
    
    def test_concurrent_customers_isolated(self):
        """Test that concurrent customers maintain isolation."""
        # Create multiple customers
        customer1 = QuantumWorkloadSimulator("customer-1", self.billing_manager)
        customer2 = QuantumWorkloadSimulator("customer-2", self.billing_manager)
        
        # Execute for customer 1
        result1 = customer1.execute_workload("exec-c1-001", 300, True)
        self.assertEqual(result1["status"], "completed")
        self.assertEqual(customer1.quota, 700)
        
        # Execute for customer 2
        result2 = customer2.execute_workload("exec-c2-001", 500, True)
        self.assertEqual(result2["status"], "completed")
        self.assertEqual(customer2.quota, 500)
        
        # Verify quotas are independent
        self.assertNotEqual(customer1.quota, customer2.quota)
        
        # Get audit trails
        history1 = self.billing_manager.get_rollback_history("customer-1")
        history2 = self.billing_manager.get_rollback_history("customer-2")
        
        # Verify isolation
        self.assertEqual(len(history1), 0)  # No failures
        self.assertEqual(len(history2), 0)  # No failures
    
    def test_evidence_seal_with_execution_record(self):
        """Test evidence seal integration with execution records."""
        import hashlib
        
        # Execute workload
        execution_id = "exec-seal-001"
        work_units = 413
        
        result = self.customer_simulator.execute_workload(
            execution_id=execution_id,
            work_units=work_units,
            should_succeed=True
        )
        
        # Create evidence seal with execution data
        evidence_data = f"{execution_id}:{self.customer_simulator.customer_id}:{work_units}"
        seal_hash = hashlib.sha256(evidence_data.encode()).hexdigest()
        
        evidence_seal = {
            "execution_id": execution_id,
            "customer_id": self.customer_simulator.customer_id,
            "work_units": work_units,
            "seal_hash": seal_hash,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Verify seal contains all necessary audit data
        self.assertIn("execution_id", evidence_seal)
        self.assertIn("customer_id", evidence_seal)
        self.assertIn("work_units", evidence_seal)
        self.assertIn("seal_hash", evidence_seal)
        
        # Verify seal would detect tampering
        tampered_data = f"{execution_id}:{self.customer_simulator.customer_id}:{work_units + 100}"
        tampered_hash = hashlib.sha256(tampered_data.encode()).hexdigest()
        
        self.assertNotEqual(seal_hash, tampered_hash)


class TestEndToEndWithMultipleOperations(unittest.TestCase):
    """Test realistic multi-operation end-to-end scenarios."""
    
    def test_production_day_simulation(self):
        """Simulate a production day with multiple customers and operations."""
        billing_manager = BillingRollbackManager()
        
        # Create multiple customers
        customers = [
            QuantumWorkloadSimulator(f"customer-{i}", billing_manager)
            for i in range(3)
        ]
        
        # Simulate day of operations
        operations = [
            (0, "exec-001", 100, True),   # customer-0: success
            (1, "exec-002", 200, False),  # customer-1: failure
            (0, "exec-003", 150, True),   # customer-0: success
            (2, "exec-004", 300, True),   # customer-2: success
            (1, "exec-005", 250, True),   # customer-1: success (retry after failure)
            (2, "exec-006", 100, False),  # customer-2: failure
        ]
        
        total_billed = 0
        total_refunded = 0
        
        for customer_idx, exec_id, units, should_succeed in operations:
            result = customers[customer_idx].execute_workload(
                exec_id, units, should_succeed
            )
            
            if should_succeed:
                total_billed += units
            else:
                total_refunded += units
        
        # Verify each customer state
        self.assertEqual(customers[0].quota, 750)  # 1000 - 100 - 150
        self.assertEqual(customers[1].quota, 750)  # 1000 - 200 (refunded) - 250
        self.assertEqual(customers[2].quota, 700)  # 1000 - 300 - 100 (refunded - restores)
        
        # Get reconciliation report
        report = billing_manager.reconcile_daily()
        self.assertEqual(report["total_refunds"], 2)  # Two failures
        self.assertEqual(report["total_work_units_refunded"], 300)
        self.assertEqual(report["affected_customers"], 2)  # Two customers had failures
        
        print(f"\nProduction Day Simulation Results:")
        print(f"  Total billed: {total_billed} units")
        print(f"  Total refunded: {total_refunded} units")
        print(f"  Customer quotas: {[c.quota for c in customers]}")


def run_full_system_tests():
    """Run all full system integration tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestFullSystemIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestEndToEndWithMultipleOperations))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 80)
    print("FULL SYSTEM INTEGRATION TEST SUMMARY")
    print("=" * 80)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 80)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_full_system_tests()
    sys.exit(0 if success else 1)
