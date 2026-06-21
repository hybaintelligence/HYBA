"""
Comprehensive tests for BillingRollbackManager

Validates:
- Refund semantics on execution failures
- Idempotency (no double-refunds)
- Daily reconciliation
- Thread safety
- Audit trail integrity
"""

import pytest
from datetime import datetime, timezone, timedelta
from threading import Thread
from python_backend.hyba_genesis_api.api.billing_rollback import (
    BillingRollbackManager,
    get_billing_rollback_manager
)


class TestBillingRollbackBasics:
    """Test core refund functionality"""
    
    def test_refund_on_failure_records_correctly(self):
        """Verify failed execution triggers quota refund"""
        manager = BillingRollbackManager()
        
        result = manager.refund_on_failure(
            execution_id="exec_123",
            customer_id="cust_abc",
            work_units_consumed=100,
            reason="timeout"
        )
        
        assert result["success"] is True
        assert result["status"] == "refunded"
        assert result["work_units_refunded"] == 100
        assert "timestamp" in result
    
    def test_idempotency_prevents_double_refunds(self):
        """Verify same execution cannot be refunded twice"""
        manager = BillingRollbackManager()
        
        # First refund
        result1 = manager.refund_on_failure(
            execution_id="exec_456",
            customer_id="cust_xyz",
            work_units_consumed=50,
            reason="error"
        )
        assert result1["status"] == "refunded"
        
        # Second refund (duplicate)
        result2 = manager.refund_on_failure(
            execution_id="exec_456",
            customer_id="cust_xyz",
            work_units_consumed=50,
            reason="error"
        )
        assert result2["status"] == "already_refunded"
        assert result2["work_units_refunded"] == 50  # Original amount
    
    def test_is_already_refunded_check(self):
        """Verify refund status check"""
        manager = BillingRollbackManager()
        
        assert manager.is_already_refunded("exec_999") is False
        
        manager.refund_on_failure(
            execution_id="exec_999",
            customer_id="cust_test",
            work_units_consumed=10,
            reason="test"
        )
        
        assert manager.is_already_refunded("exec_999") is True
    
    def test_get_refund_status(self):
        """Verify refund status retrieval"""
        manager = BillingRollbackManager()
        
        assert manager.get_refund_status("exec_missing") is None
        
        manager.refund_on_failure(
            execution_id="exec_status",
            customer_id="cust_status",
            work_units_consumed=25,
            reason="validation_error"
        )
        
        status = manager.get_refund_status("exec_status")
        assert status is not None
        assert status["work_units_refunded"] == 25
        assert status["reason"] == "validation_error"


class TestDailyReconciliation:
    """Test daily reconciliation functionality"""
    
    def test_reconcile_daily_aggregates_refunds(self):
        """Verify daily reconciliation sums all refunds"""
        manager = BillingRollbackManager()
        
        # Process multiple refunds
        manager.refund_on_failure("exec_1", "cust_a", 100, "timeout")
        manager.refund_on_failure("exec_2", "cust_b", 50, "error")
        manager.refund_on_failure("exec_3", "cust_a", 75, "timeout")
        
        report = manager.reconcile_daily()
        
        assert report["total_refunds"] == 3
        assert report["total_work_units_refunded"] == 225
        assert report["affected_customers"] == 2
        assert report["refunds_by_reason"]["timeout"] == 175
        assert report["refunds_by_reason"]["error"] == 50
    
    def test_reconcile_daily_with_specific_date(self):
        """Verify reconciliation can query specific date"""
        manager = BillingRollbackManager()
        
        # Current date should have no refunds initially
        today = datetime.now(timezone.utc).date().isoformat()
        report = manager.reconcile_daily(date=today)
        
        # After adding refund
        manager.refund_on_failure("exec_today", "cust_x", 30, "test")
        report = manager.reconcile_daily(date=today)
        
        assert report["total_refunds"] == 1
        assert report["date"] == today
    
    def test_reconcile_empty_date(self):
        """Verify reconciliation handles dates with no refunds"""
        manager = BillingRollbackManager()
        
        future_date = (datetime.now(timezone.utc) + timedelta(days=30)).date().isoformat()
        report = manager.reconcile_daily(date=future_date)
        
        assert report["total_refunds"] == 0
        assert report["total_work_units_refunded"] == 0
        assert report["affected_customers"] == 0


class TestRollbackHistory:
    """Test audit trail and history retrieval"""
    
    def test_get_rollback_history_all(self):
        """Verify full rollback history retrieval"""
        manager = BillingRollbackManager()
        
        manager.refund_on_failure("exec_h1", "cust_1", 10, "r1")
        manager.refund_on_failure("exec_h2", "cust_2", 20, "r2")
        manager.refund_on_failure("exec_h3", "cust_3", 30, "r3")
        
        history = manager.get_rollback_history()
        
        assert len(history) == 3
        # Most recent first
        assert history[0]["execution_id"] == "exec_h3"
        assert history[2]["execution_id"] == "exec_h1"
    
    def test_get_rollback_history_filtered_by_customer(self):
        """Verify customer-specific history filtering"""
        manager = BillingRollbackManager()
        
        manager.refund_on_failure("exec_f1", "cust_alpha", 10, "r1")
        manager.refund_on_failure("exec_f2", "cust_beta", 20, "r2")
        manager.refund_on_failure("exec_f3", "cust_alpha", 30, "r3")
        
        history = manager.get_rollback_history(customer_id="cust_alpha")
        
        assert len(history) == 2
        assert all(r["customer_id"] == "cust_alpha" for r in history)
    
    def test_get_rollback_history_respects_limit(self):
        """Verify history limit parameter works"""
        manager = BillingRollbackManager()
        
        for i in range(10):
            manager.refund_on_failure(f"exec_{i}", "cust_limit", 1, "test")
        
        history = manager.get_rollback_history(limit=5)
        assert len(history) == 5


class TestThreadSafety:
    """Test concurrent access patterns"""
    
    def test_concurrent_refunds_no_race_conditions(self):
        """Verify thread-safe refund processing"""
        manager = BillingRollbackManager()
        results = []
        
        def refund_worker(exec_id, cust_id, units):
            result = manager.refund_on_failure(exec_id, cust_id, units, "concurrent")
            results.append(result)
        
        threads = []
        for i in range(10):
            t = Thread(target=refund_worker, args=(f"exec_t{i}", f"cust_{i}", i * 10))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        assert len(results) == 10
        assert all(r["success"] for r in results)
    
    def test_concurrent_idempotency_checks(self):
        """Verify thread-safe idempotency under concurrent duplicate requests"""
        manager = BillingRollbackManager()
        results = []
        
        def duplicate_refund_worker():
            result = manager.refund_on_failure("exec_dup", "cust_dup", 100, "test")
            results.append(result)
        
        threads = [Thread(target=duplicate_refund_worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # One should be refunded, rest should be already_refunded
        refunded_count = sum(1 for r in results if r["status"] == "refunded")
        already_refunded_count = sum(1 for r in results if r["status"] == "already_refunded")
        
        assert refunded_count == 1
        assert already_refunded_count == 4
        assert all(r["work_units_refunded"] == 100 for r in results)


class TestGlobalSingleton:
    """Test global manager singleton"""
    
    def test_get_billing_rollback_manager_singleton(self):
        """Verify singleton returns same instance"""
        manager1 = get_billing_rollback_manager()
        manager2 = get_billing_rollback_manager()
        
        assert manager1 is manager2
        
        # State should persist
        manager1.refund_on_failure("exec_singleton", "cust_singleton", 42, "test")
        assert manager2.is_already_refunded("exec_singleton")


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_zero_work_units_refund(self):
        """Verify zero work unit refunds are handled"""
        manager = BillingRollbackManager()
        
        result = manager.refund_on_failure("exec_zero", "cust_zero", 0, "no_charge")
        assert result["success"] is True
        assert result["work_units_refunded"] == 0
    
    def test_large_work_units_refund(self):
        """Verify large work unit refunds are handled"""
        manager = BillingRollbackManager()
        
        result = manager.refund_on_failure("exec_large", "cust_large", 1_000_000, "big_job")
        assert result["success"] is True
        assert result["work_units_refunded"] == 1_000_000
    
    def test_empty_reason_string(self):
        """Verify empty reason strings are handled"""
        manager = BillingRollbackManager()
        
        result = manager.refund_on_failure("exec_noreason", "cust_noreason", 10, "")
        assert result["success"] is True
        assert result["reason"] == ""
    
    def test_special_characters_in_ids(self):
        """Verify special characters in IDs are handled"""
        manager = BillingRollbackManager()
        
        result = manager.refund_on_failure(
            "exec_special-123_v2.0",
            "cust@example.com",
            50,
            "timeout: connection refused"
        )
        assert result["success"] is True


class TestAuditTrail:
    """Test audit trail integrity"""
    
    def test_refund_timestamps_are_valid(self):
        """Verify all refunds have valid ISO timestamps"""
        manager = BillingRollbackManager()
        
        manager.refund_on_failure("exec_ts1", "cust_ts", 10, "test")
        manager.refund_on_failure("exec_ts2", "cust_ts", 20, "test")
        
        history = manager.get_rollback_history()
        
        for record in history:
            # Verify timestamp can be parsed
            ts = datetime.fromisoformat(record["timestamp"])
            assert ts.tzinfo is not None  # Has timezone
            assert ts <= datetime.now(timezone.utc)  # Not in future
    
    def test_reconciliation_preserves_all_fields(self):
        """Verify reconciliation includes all refund record fields"""
        manager = BillingRollbackManager()
        
        manager.refund_on_failure("exec_rec", "cust_rec", 100, "preserved")
        report = manager.reconcile_daily()
        
        assert len(report["reconciliations"]) == 1
        rec = report["reconciliations"][0]
        
        assert rec["execution_id"] == "exec_rec"
        assert rec["customer_id"] == "cust_rec"
        assert rec["work_units_refunded"] == 100
        assert rec["reason"] == "preserved"
        assert rec["status"] == "refunded"
        assert "timestamp" in rec


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
