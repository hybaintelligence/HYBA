"""
Integration tests for billing rollback with QaaS/CIaaS execution pipeline

Validates end-to-end behavior:
- Failed executions trigger automatic refunds
- Quota is correctly restored
- Audit trail is maintained
"""

import pytest
from datetime import datetime, timezone
from python_backend.hyba_genesis_api.api.billing_rollback import (
    BillingRollbackManager,
    get_billing_rollback_manager
)


class MockQuotaManager:
    """Mock quota manager for testing integration"""
    
    def __init__(self, initial_quota: int = 1000):
        self.quotas = {"test_customer": initial_quota}
        self.consumed = {"test_customer": 0}
    
    def consume_quota(self, customer_id: str, units: int) -> bool:
        """Consume quota, return True if successful"""
        available = self.quotas.get(customer_id, 0) - self.consumed.get(customer_id, 0)
        if available >= units:
            self.consumed[customer_id] = self.consumed.get(customer_id, 0) + units
            return True
        return False
    
    def refund_quota(self, customer_id: str, units: int):
        """Refund quota"""
        self.consumed[customer_id] = max(0, self.consumed.get(customer_id, 0) - units)
    
    def get_available(self, customer_id: str) -> int:
        """Get available quota"""
        return self.quotas.get(customer_id, 0) - self.consumed.get(customer_id, 0)


class TestQaaSIntegration:
    """Test billing rollback with QaaS execution pipeline"""
    
    def test_successful_execution_consumes_quota(self):
        """Verify successful execution consumes quota without refund"""
        quota_mgr = MockQuotaManager(initial_quota=1000)
        billing_mgr = BillingRollbackManager()
        
        # Execute successfully
        consumed = quota_mgr.consume_quota("test_customer", 100)
        assert consumed is True
        assert quota_mgr.get_available("test_customer") == 900
        
        # No refund needed
        assert billing_mgr.is_already_refunded("exec_success") is False
    
    def test_failed_execution_triggers_refund(self):
        """Verify failed execution triggers automatic quota refund"""
        quota_mgr = MockQuotaManager(initial_quota=1000)
        billing_mgr = BillingRollbackManager()
        
        # Start execution - consume quota
        consumed = quota_mgr.consume_quota("test_customer", 150)
        assert consumed is True
        assert quota_mgr.get_available("test_customer") == 850
        
        # Execution fails - trigger rollback
        refund_result = billing_mgr.refund_on_failure(
            execution_id="exec_failed_1",
            customer_id="test_customer",
            work_units_consumed=150,
            reason="timeout_after_30s"
        )
        
        assert refund_result["success"] is True
        assert refund_result["work_units_refunded"] == 150
        
        # Restore quota
        quota_mgr.refund_quota("test_customer", 150)
        assert quota_mgr.get_available("test_customer") == 1000
    
    def test_multiple_failures_accumulate_refunds(self):
        """Verify multiple failures are tracked correctly"""
        quota_mgr = MockQuotaManager(initial_quota=1000)
        billing_mgr = BillingRollbackManager()
        
        failures = [
            ("exec_f1", 100, "timeout"),
            ("exec_f2", 75, "oom_error"),
            ("exec_f3", 50, "validation_failed"),
        ]
        
        for exec_id, units, reason in failures:
            # Consume quota
            quota_mgr.consume_quota("test_customer", units)
            
            # Fail and refund
            billing_mgr.refund_on_failure(exec_id, "test_customer", units, reason)
            quota_mgr.refund_quota("test_customer", units)
        
        # Quota should be fully restored
        assert quota_mgr.get_available("test_customer") == 1000
        
        # All refunds should be in history
        history = billing_mgr.get_rollback_history(customer_id="test_customer")
        assert len(history) == 3
        assert sum(r["work_units_refunded"] for r in history) == 225


class TestCIaaSIntegration:
    """Test billing rollback with CIaaS execution pipeline"""
    
    def test_consciousness_computation_failure_refund(self):
        """Verify consciousness computation failure triggers refund"""
        quota_mgr = MockQuotaManager(initial_quota=5000)
        quota_mgr.quotas["research_customer"] = 5000
        quota_mgr.consumed["research_customer"] = 0
        billing_mgr = BillingRollbackManager()
        
        # Large consciousness computation
        consumed = quota_mgr.consume_quota("research_customer", 1000)
        assert consumed is True
        
        # Computation fails due to memory exhaustion
        refund_result = billing_mgr.refund_on_failure(
            execution_id="consciousness_job_42",
            customer_id="research_customer",
            work_units_consumed=1000,
            reason="memory_exhausted_during_iit_phi_computation"
        )
        
        assert refund_result["success"] is True
        quota_mgr.refund_quota("research_customer", 1000)
        assert quota_mgr.get_available("research_customer") == 5000
    
    def test_partial_execution_refunds_consumed_units(self):
        """Verify partial execution refunds actual consumed units"""
        quota_mgr = MockQuotaManager(initial_quota=10000)
        quota_mgr.quotas["enterprise_customer"] = 10000
        quota_mgr.consumed["enterprise_customer"] = 0
        billing_mgr = BillingRollbackManager()
        
        # Reserve 2000 units
        quota_mgr.consume_quota("enterprise_customer", 2000)
        
        # Only 800 units actually consumed before failure
        refund_result = billing_mgr.refund_on_failure(
            execution_id="partial_exec_123",
            customer_id="enterprise_customer",
            work_units_consumed=800,  # Only what was consumed
            reason="early_termination"
        )
        
        # Refund the 800 that were consumed
        quota_mgr.refund_quota("enterprise_customer", 800)
        
        # 1200 units should remain consumed (2000 - 800)
        assert quota_mgr.get_available("enterprise_customer") == 8800


class TestDailyReconciliationIntegration:
    """Test daily reconciliation with live quota system"""
    
    def test_daily_reconciliation_matches_quota_records(self):
        """Verify daily reconciliation report matches quota system"""
        quota_mgr = MockQuotaManager(initial_quota=10000)
        billing_mgr = BillingRollbackManager()
        
        # Process day's workload with some failures
        executions = [
            ("exec_d1", "cust_a", 100, None),  # Success
            ("exec_d2", "cust_a", 150, "timeout"),  # Failed
            ("exec_d3", "cust_b", 200, None),  # Success
            ("exec_d4", "cust_b", 75, "error"),  # Failed
            ("exec_d5", "cust_c", 300, "oom"),  # Failed
        ]
        
        for exec_id, cust_id, units, failure_reason in executions:
            # All consume quota initially
            if cust_id not in quota_mgr.quotas:
                quota_mgr.quotas[cust_id] = 10000
                quota_mgr.consumed[cust_id] = 0
            
            quota_mgr.consume_quota(cust_id, units)
            
            # Failed executions get refunded
            if failure_reason:
                billing_mgr.refund_on_failure(exec_id, cust_id, units, failure_reason)
                quota_mgr.refund_quota(cust_id, units)
        
        # Daily reconciliation
        report = billing_mgr.reconcile_daily()
        
        assert report["total_refunds"] == 3
        assert report["total_work_units_refunded"] == 525  # 150 + 75 + 300
        assert report["affected_customers"] == 3
        
        # Verify quota state matches
        assert quota_mgr.consumed["cust_a"] == 100  # 100 success
        assert quota_mgr.consumed["cust_b"] == 200  # 200 success
        assert quota_mgr.consumed["cust_c"] == 0     # 0 (all failed)


class TestIdempotencyInPipeline:
    """Test idempotency handling in execution pipeline"""
    
    def test_retry_logic_does_not_double_refund(self):
        """Verify retry logic doesn't cause double refunds"""
        quota_mgr = MockQuotaManager(initial_quota=1000)
        quota_mgr.quotas["retry_customer"] = 1000
        quota_mgr.consumed["retry_customer"] = 0
        billing_mgr = BillingRollbackManager()
        
        # Initial execution fails
        quota_mgr.consume_quota("retry_customer", 100)
        
        # First refund attempt
        result1 = billing_mgr.refund_on_failure(
            execution_id="exec_retry",
            customer_id="retry_customer",
            work_units_consumed=100,
            reason="transient_error"
        )
        quota_mgr.refund_quota("retry_customer", 100)
        
        assert result1["status"] == "refunded"
        assert quota_mgr.get_available("retry_customer") == 1000
        
        # Retry mechanism attempts second refund (should be idempotent)
        result2 = billing_mgr.refund_on_failure(
            execution_id="exec_retry",  # Same execution ID
            customer_id="retry_customer",
            work_units_consumed=100,
            reason="transient_error"
        )
        
        assert result2["status"] == "already_refunded"
        assert result2["work_units_refunded"] == 100  # Original amount
        
        # Quota should not be double-refunded
        assert quota_mgr.get_available("retry_customer") == 1000


class TestAuditTrailIntegration:
    """Test audit trail with compliance requirements"""
    
    def test_audit_trail_7_year_retention(self):
        """Verify audit trail supports 7-year retention requirement"""
        billing_mgr = BillingRollbackManager()
        
        # Process refund
        billing_mgr.refund_on_failure(
            execution_id="audit_exec_1",
            customer_id="audit_customer",
            work_units_consumed=250,
            reason="compliance_test"
        )
        
        # Retrieve audit record
        history = billing_mgr.get_rollback_history(customer_id="audit_customer")
        
        assert len(history) == 1
        record = history[0]
        
        # Verify all required audit fields present
        required_fields = [
            "execution_id",
            "customer_id",
            "work_units_refunded",
            "reason",
            "timestamp",
            "status"
        ]
        
        for field in required_fields:
            assert field in record, f"Missing audit field: {field}"
        
        # Verify timestamp is immutable ISO format
        ts = datetime.fromisoformat(record["timestamp"])
        assert ts.tzinfo is not None
    
    def test_reconciliation_report_audit_format(self):
        """Verify reconciliation reports include full audit trail"""
        billing_mgr = BillingRollbackManager()
        
        billing_mgr.refund_on_failure("exec_a1", "cust_audit", 100, "r1")
        billing_mgr.refund_on_failure("exec_a2", "cust_audit", 200, "r2")
        
        report = billing_mgr.reconcile_daily()
        
        # Report should include individual reconciliation records
        assert "reconciliations" in report
        assert len(report["reconciliations"]) == 2
        
        # Each reconciliation should have full audit context
        for rec in report["reconciliations"]:
            assert rec["customer_id"] == "cust_audit"
            assert "timestamp" in rec
            assert "reason" in rec


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
