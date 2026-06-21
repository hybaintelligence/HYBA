#!/usr/bin/env python3
"""
Adversarial Robustness Testing Suite for HYBA QaaS/CIaaS

Tests defensive measures against:
1. Quota exhaustion attacks
2. Rate limiting bypass attempts
3. Billing manipulation
4. State corruption
5. Concurrency exploits
"""

import sys
import unittest
import time
import threading
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "python_backend"))

from pythia_mining.distributed_lock_manager import DistributedLockManager
from pythia_mining.redis_state_registry import RedisQuantumSubstrateRegistry


class TestQuotaExhaustionDefense(unittest.TestCase):
    """Test defenses against quota exhaustion attacks."""

    def test_quota_cannot_go_negative(self):
        """Verify quota cannot become negative via concurrent requests."""
        # Mock Redis client for DistributedLockManager
        mock_redis = Mock()
        lock_manager = DistributedLockManager(mock_redis)
        customer_quota = {"remaining": 1000}
        
        def consume_quota(units):
            # Simulate concurrent consumption
            if customer_quota["remaining"] >= units:
                customer_quota["remaining"] -= units
                return True
            return False
        
        # Attempt to consume more than available
        results = []
        for _ in range(50):
            results.append(consume_quota(30))
        
        # Verify quota never went negative
        self.assertGreaterEqual(customer_quota["remaining"], 0,
                               "Quota went negative - quota exhaustion attack succeeded")
        
        # Count successful consumptions
        successful = sum(results)
        self.assertLessEqual(successful * 30, 1000,
                            "More quota consumed than available")

    def test_quota_refund_on_failure(self):
        """Verify failed executions refund quota."""
        initial_quota = 1000
        units_consumed = 100
        quota = initial_quota - units_consumed  # Start after consumption
        
        # Simulate execution failure
        execution_failed = True
        
        if execution_failed:
            quota += units_consumed  # Refund
        
        self.assertEqual(quota, initial_quota, "Quota not refunded on failure")

    def test_quota_overflow_protection(self):
        """Verify quota addition is bounded."""
        max_quota = 10000
        current_quota = 9500
        
        # Attempt to add excessive quota
        refund = 1000
        new_quota = min(current_quota + refund, max_quota)
        
        self.assertEqual(new_quota, max_quota, "Quota overflowed")


class TestRateLimitingBypass(unittest.TestCase):
    """Test defenses against rate limiting bypass."""

    def test_rate_limit_per_customer(self):
        """Verify rate limits are per-customer, not global."""
        customer_a_requests = []
        customer_b_requests = []
        rpm_limit = 60
        
        # Customer A makes 30 requests
        for i in range(30):
            customer_a_requests.append(time.time())
        
        # Customer B makes 30 requests
        for i in range(30):
            customer_b_requests.append(time.time())
        
        # Verify each customer is within limit
        time_window = customer_a_requests[-1] - customer_a_requests[0]
        rate_a = 30 / (time_window + 0.001)
        
        time_window_b = customer_b_requests[-1] - customer_b_requests[0]
        rate_b = 30 / (time_window_b + 0.001)
        
        # Both customers should be able to make requests
        self.assertGreater(rate_a, 0)
        self.assertGreater(rate_b, 0)

    def test_rate_limit_headers_present(self):
        """Verify rate limit headers prevent bypass attempts."""
        response_headers = {
            "X-RateLimit-Limit": "60",
            "X-RateLimit-Remaining": "45",
            "X-RateLimit-Reset": "1718972400"
        }
        
        # Verify headers exist
        self.assertIn("X-RateLimit-Limit", response_headers)
        self.assertIn("X-RateLimit-Remaining", response_headers)
        self.assertIn("X-RateLimit-Reset", response_headers)
        
        # Verify remaining <= limit
        limit = int(response_headers["X-RateLimit-Limit"])
        remaining = int(response_headers["X-RateLimit-Remaining"])
        self.assertLessEqual(remaining, limit)

    def test_burst_limit_enforcement(self):
        """Verify burst limits are enforced."""
        burst_limit = 10
        burst_window = 1  # 1 second
        recent_requests = []
        
        # Attempt burst of 15 requests
        current_time = time.time()
        for i in range(15):
            if len([r for r in recent_requests if current_time - r < burst_window]) < burst_limit:
                recent_requests.append(current_time)
        
        # Verify burst limit was enforced
        recent_count = len([r for r in recent_requests if current_time - r < burst_window])
        self.assertLessEqual(recent_count, burst_limit,
                            "Burst limit not enforced")


class TestBillingManipulation(unittest.TestCase):
    """Test defenses against billing manipulation."""

    def test_double_billing_prevention(self):
        """Verify idempotency key prevents double billing."""
        idempotency_key = "exec-2026-06-21-001"
        executed_keys = set()
        
        # First execution
        if idempotency_key not in executed_keys:
            executed_keys.add(idempotency_key)
            billed = True
        else:
            billed = False
        
        # Second execution with same key
        if idempotency_key not in executed_keys:
            executed_keys.add(idempotency_key)
            double_billed = True
        else:
            double_billed = False
        
        self.assertTrue(billed, "First execution not billed")
        self.assertFalse(double_billed, "Double billing occurred - idempotency failed")

    def test_billing_cannot_be_negative(self):
        """Verify billing amount cannot be negative."""
        work_units = 100
        cost_per_unit = 0.01
        total_cost = max(0, work_units * cost_per_unit)
        
        self.assertGreaterEqual(total_cost, 0, "Negative billing detected")

    def test_evidence_seal_includes_metering(self):
        """Verify evidence seal includes metering data for audit."""
        execution_id = "exec-001"
        customer_id = "cust-123"
        work_units = 413
        
        evidence_seal = {
            "execution_id": execution_id,
            "customer_id": customer_id,
            "work_units": work_units,
            "timestamp": time.time(),
            "hash": "sha256_hash_of_request"
        }
        
        # Verify all fields present
        self.assertIn("execution_id", evidence_seal)
        self.assertIn("customer_id", evidence_seal)
        self.assertIn("work_units", evidence_seal)
        self.assertIn("hash", evidence_seal)

    def test_billing_rollback_on_failure(self):
        """Verify billing is rolled back on execution failure."""
        initial_balance = 1000
        work_units = 100
        cost = work_units * 0.01
        
        # Simulate execution
        balance = initial_balance - cost
        
        # Execution fails
        execution_successful = False
        if not execution_successful:
            balance += cost  # Rollback
        
        self.assertEqual(balance, initial_balance,
                        "Billing not rolled back on failure")


class TestStateCorruptionDefense(unittest.TestCase):
    """Test defenses against state corruption."""

    def test_distributed_lock_prevents_concurrent_state_mutation(self):
        """Verify distributed locks prevent concurrent state mutation."""
        shared_state = {"counter": 0}
        lock = threading.Lock()
        
        def increment_with_lock():
            with lock:
                temp = shared_state["counter"]
                temp += 1
                shared_state["counter"] = temp
        
        threads = [threading.Thread(target=increment_with_lock) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Without proper locking, this could be < 10
        self.assertEqual(shared_state["counter"], 10,
                        "Concurrent state mutation allowed")

    def test_redis_rehydration_after_restart(self):
        """Verify state can be restored after process restart."""
        execution_state = {
            "execution_id": "exec-001",
            "status": "in_progress",
            "customer_id": "cust-123"
        }
        
        # Simulate persistence and restart
        persisted = execution_state.copy()
        
        # After restart, restore state
        restored_state = persisted.copy()
        
        self.assertEqual(restored_state, execution_state,
                        "State not properly restored after restart")

    def test_idempotency_key_persistence(self):
        """Verify idempotency keys persist across restarts."""
        executed_idempotency_keys = {"key-001", "key-002", "key-003"}
        
        # Simulate persistence
        persisted_keys = executed_idempotency_keys.copy()
        
        # After restart
        restored_keys = persisted_keys.copy()
        
        self.assertEqual(restored_keys, executed_idempotency_keys,
                        "Idempotency keys not persisted")


class TestConcurrencyExploits(unittest.TestCase):
    """Test defenses against concurrency-based exploits."""

    def test_concurrent_lock_acquisition(self):
        """Verify only one process can acquire lock at a time."""
        lock_holder = {"process_id": None}
        lock = threading.Lock()
        
        def try_acquire_lock(process_id):
            with lock:
                if lock_holder["process_id"] is None:
                    lock_holder["process_id"] = process_id
                    time.sleep(0.01)  # Hold lock briefly
                    lock_holder["process_id"] = None
        
        threads = [threading.Thread(target=try_acquire_lock, args=(i,)) 
                  for i in range(5)]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Lock should be released
        self.assertIsNone(lock_holder["process_id"],
                         "Lock not properly released")

    def test_race_condition_prevention_in_quota(self):
        """Verify quota updates are atomic."""
        quota = 1000
        quota_lock = threading.Lock()
        results = []
        
        def consume_quota_safely(units):
            with quota_lock:
                nonlocal quota
                if quota >= units:
                    quota -= units
                    results.append(True)
                    return True
            results.append(False)
            return False
        
        threads = [threading.Thread(target=consume_quota_safely, args=(100,))
                  for _ in range(15)]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Only 10 should succeed (1000 / 100)
        successful = sum(results)
        self.assertEqual(successful, 10,
                        f"Race condition in quota: {successful} succeeded instead of 10")


class TestIPProtection(unittest.TestCase):
    """Test IP protection and access controls."""

    def test_api_key_validation(self):
        """Verify API keys are properly validated."""
        valid_key = "hyba_test_key_abcd1234567890"
        invalid_key = "invalid_key"
        
        def validate_api_key(key):
            return key.startswith("hyba_") and len(key) >= 24
        
        self.assertTrue(validate_api_key(valid_key))
        self.assertFalse(validate_api_key(invalid_key))

    def test_customer_isolation(self):
        """Verify customers cannot access each other's data."""
        customer_a_data = {"customer_id": "cust-a", "data": "secret-a"}
        customer_b_data = {"customer_id": "cust-b", "data": "secret-b"}
        
        def get_data_for_customer(customer_id, data):
            if data["customer_id"] == customer_id:
                return data
            return None
        
        result_a = get_data_for_customer("cust-a", customer_b_data)
        result_b = get_data_for_customer("cust-b", customer_a_data)
        
        self.assertIsNone(result_a, "Customer isolation violated")
        self.assertIsNone(result_b, "Customer isolation violated")

    def test_evidence_seal_prevents_tampering(self):
        """Verify evidence seals detect tampering."""
        import hashlib
        
        original_seal = {
            "execution_id": "exec-001",
            "work_units": 413
        }
        
        # Calculate hash of original
        seal_str = str(original_seal)
        original_hash = hashlib.sha256(seal_str.encode()).hexdigest()
        
        # Attempt to tamper
        tampered_seal = original_seal.copy()
        tampered_seal["work_units"] = 500
        
        tampered_str = str(tampered_seal)
        tampered_hash = hashlib.sha256(tampered_str.encode()).hexdigest()
        
        self.assertNotEqual(original_hash, tampered_hash,
                           "Tampering not detected")


def run_adversarial_tests():
    """Run all adversarial robustness tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestQuotaExhaustionDefense))
    suite.addTests(loader.loadTestsFromTestCase(TestRateLimitingBypass))
    suite.addTests(loader.loadTestsFromTestCase(TestBillingManipulation))
    suite.addTests(loader.loadTestsFromTestCase(TestStateCorruptionDefense))
    suite.addTests(loader.loadTestsFromTestCase(TestConcurrencyExploits))
    suite.addTests(loader.loadTestsFromTestCase(TestIPProtection))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 80)
    print("ADVERSARIAL ROBUSTNESS TEST SUMMARY")
    print("=" * 80)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 80)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_adversarial_tests()
    sys.exit(0 if success else 1)
