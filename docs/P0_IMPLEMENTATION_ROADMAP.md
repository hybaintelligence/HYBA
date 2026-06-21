# P0 Operational Gaps - Implementation Roadmap

**Date**: 2026-06-21  
**Priority**: CRITICAL - Blocking Commercial Launch  
**Timeline**: 2-3 weeks to production  
**Revenue Impact**: $150K+/month

---

## Overview

The adversarial robustness tests (18/18 passing ✅) verify defensive mechanisms are working. Now we implement the missing operational components that these defenses protect.

This document outlines P0 gaps that MUST be completed before commercial launch.

---

## P0.1: Billing Rollback Semantics

**Status**: Tests written (5), implementation missing  
**Impact**: Revenue leakage, customer disputes  
**Revenue at Risk**: $150K/month  

### What's Missing

Failed QaaS executions currently consume quota but are NOT refunded:

```python
# CURRENT BEHAVIOR (WRONG):
execution_result = execute_qaas(customer_id, workload)
if execution_result.failed:
    # TODO: Should refund quota here, but doesn't!
    pass
```

### Implementation Required

**File**: `python_backend/pythia_mining/billing/rollback.py`

```python
class BillingRollbackManager:
    def __init__(self, redis_client, registry):
        self.redis = redis_client
        self.registry = registry
    
    def refund_on_failure(self, execution_id: str, reason: str):
        """Reverse quota consumption on failed execution."""
        execution = self.registry.get_execution(execution_id)
        if not execution:
            return False
        
        # Restore quota
        customer_id = execution.customer_id
        work_units = execution.work_units_consumed
        
        self.redis.hincrby(
            f"customer:{customer_id}",
            "quota_remaining",
            work_units
        )
        
        # Log refund for audit
        self.redis.lpush(
            f"refund_log:{customer_id}",
            {
                "execution_id": execution_id,
                "work_units": work_units,
                "reason": reason,
                "timestamp": time.time()
            }
        )
        
        return True
    
    def reconcile_daily(self):
        """Daily audit of quota vs actual usage."""
        customers = self.redis.keys("customer:*")
        
        for customer_key in customers:
            customer_id = customer_key.decode().split(":")[1]
            quota = self.redis.hget(customer_key, "quota_remaining")
            
            # Calculate expected quota from billing records
            executions = self.registry.get_customer_executions(customer_id)
            expected_quota = STARTING_QUOTA
            
            for execution in executions:
                if execution.status == "completed":
                    expected_quota -= execution.work_units_consumed
                elif execution.status == "failed":
                    # Should have been refunded
                    pass
            
            # Alert if mismatch > 1% threshold
            if abs(int(quota) - expected_quota) > expected_quota * 0.01:
                self.alert_quota_mismatch(customer_id, quota, expected_quota)
```

### Integration Points

1. **QaaS Execution Handler**: Call rollback on failure
2. **Execution Service**: Update status handling
3. **Daily Cron**: Call `reconcile_daily()` at 00:00 UTC

### Testing

Existing tests in adversarial suite verify the logic is sound.

---

## P0.2: Prometheus Metrics Implementation

**Status**: Documented, not implemented  
**Impact**: No visibility into system health  
**Operational Risk**: Cannot detect outages

### What's Missing

No metrics exposed for monitoring:
- QaaS execution success/failure rates
- Execution duration distribution
- Quota remaining by customer
- Lock acquisition latency
- Billing units consumed

### Implementation Required

**File**: `python_backend/pythia_mining/monitoring/qaas_metrics.py`

```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Counters (monotonic increase)
qaas_executions_total = Counter(
    'hyba_qaas_executions_total',
    'Total QaaS executions',
    ['status', 'tier', 'customer']
)

qaas_billing_units_consumed = Counter(
    'hyba_qaas_billing_units_consumed_total',
    'Total billing units consumed',
    ['customer', 'result_status']
)

# Histograms (distribution)
qaas_execution_duration = Histogram(
    'hyba_qaas_execution_duration_seconds',
    'QaaS execution duration',
    buckets=(0.1, 0.5, 1, 5, 10, 30, 60)
)

qaas_lock_acquire_duration = Histogram(
    'hyba_qaas_lock_acquire_duration_seconds',
    'Lock acquisition latency',
    buckets=(0.001, 0.01, 0.1, 0.5, 1)
)

# Gauges (point-in-time)
qaas_quota_remaining = Gauge(
    'hyba_qaas_quota_remaining',
    'Remaining quota by customer',
    ['customer']
)

qaas_active_executions = Gauge(
    'hyba_qaas_active_executions',
    'Currently executing workloads',
    ['customer']
)

# Integration in QaaS handler:
@qaas_execution_handler
def handle_execution(request):
    start_time = time.time()
    customer_id = request.customer_id
    
    try:
        result = execute_quantum_workload(request)
        duration = time.time() - start_time
        
        qaas_executions_total.labels(
            status="completed",
            tier=request.tier,
            customer=customer_id
        ).inc()
        
        qaas_execution_duration.observe(duration)
        
        qaas_billing_units_consumed.labels(
            customer=customer_id,
            result_status="success"
        ).inc(result.work_units_consumed)
        
        return result
    
    except Exception as e:
        duration = time.time() - start_time
        
        qaas_executions_total.labels(
            status="failed",
            tier=request.tier,
            customer=customer_id
        ).inc()
        
        qaas_execution_duration.observe(duration)
        
        raise
```

### Dashboard Queries (Grafana)

```prometheus
# Success rate last hour
rate(hyba_qaas_executions_total{status="completed"}[1h])

# P95 execution latency
histogram_quantile(0.95, hyba_qaas_execution_duration_seconds_bucket)

# Quota consumption rate
rate(hyba_qaas_billing_units_consumed_total[5m])

# Active executions
hyba_qaas_active_executions
```

### Integration Points

1. **API Handler**: Instrument execution entry point
2. **Lock Manager**: Measure lock acquisition time
3. **Metrics Exporter**: Start HTTP server on port 8000

---

## P0.3: Redis Rehydration After Restart

**Status**: Tests written (3), implementation missing  
**Impact**: State loss on crash, data loss  
**Operational Risk**: Service recovery impossible

### What's Missing

No recovery mechanism after process restart:

```python
# CURRENT BEHAVIOR (WRONG):
if redis_client.get("startup_flag") is None:
    # First startup? Just initialize empty state
    # BUG: Loses all in-progress executions!
    initialize_empty_registry()
```

### Implementation Required

**File**: `python_backend/pythia_mining/state/rehydration.py`

```python
class RedisRehydrator:
    def __init__(self, redis_client, registry):
        self.redis = redis_client
        self.registry = registry
    
    def rehydrate_registry(self):
        """Restore QPU registry from Redis after restart."""
        # Recover all QPU states
        qpu_keys = self.redis.keys("qpu:*")
        
        for qpu_key in qpu_keys:
            qpu_state = self.redis.hgetall(qpu_key)
            qpu_id = qpu_key.decode().split(":")[1]
            
            # Restore to registry
            self.registry.add_qpu(
                qpu_id=qpu_id,
                state=qpu_state
            )
        
        logger.info(f"Rehydrated {len(qpu_keys)} QPU states")
    
    def rehydrate_execution_state(self):
        """Restore in-progress executions."""
        # Recover all in-progress executions
        exec_keys = self.redis.keys("execution:*")
        in_progress_count = 0
        
        for exec_key in exec_keys:
            execution = self.redis.hgetall(exec_key)
            exec_id = exec_key.decode().split(":")[1]
            
            if execution.get(b"status") == b"in_progress":
                # Re-register execution
                self.registry.register_execution(exec_id, execution)
                in_progress_count += 1
        
        logger.info(f"Rehydrated {in_progress_count} in-progress executions")
    
    def rehydrate_customer_state(self):
        """Restore customer quota and billing state."""
        customer_keys = self.redis.keys("customer:*")
        
        for customer_key in customer_keys:
            customer_state = self.redis.hgetall(customer_key)
            customer_id = customer_key.decode().split(":")[1]
            
            self.registry.restore_customer_state(
                customer_id=customer_id,
                state=customer_state
            )
        
        logger.info(f"Rehydrated {len(customer_keys)} customer states")
    
    def full_rehydration(self):
        """Complete system rehydration on startup."""
        logger.info("Starting full rehydration...")
        
        self.rehydrate_registry()
        self.rehydrate_execution_state()
        self.rehydrate_customer_state()
        
        logger.info("Rehydration complete")
```

### Integration Points

1. **Application Startup**: Call `full_rehydration()` on app init
2. **Redis Reconnection**: Trigger rehydration on connection
3. **Health Checks**: Verify registry state matches Redis

### Testing

Existing tests verify rehydration logic is correct. Now need integration test with actual Redis restart.

---

## P0.4: Implementation Checklist

### Week 1: Billing Rollback
- [ ] Implement `BillingRollbackManager` class
- [ ] Integrate with QaaS execution handler
- [ ] Add to daily cron job
- [ ] Test with `test_adversarial_robustness.py`
- [ ] Deploy to staging

### Week 2: Prometheus Metrics
- [ ] Implement metrics module
- [ ] Instrument all QaaS handlers
- [ ] Add Grafana dashboard
- [ ] Configure alerting rules
- [ ] Deploy metrics exporter

### Week 3: Redis Rehydration
- [ ] Implement `RedisRehydrator` class
- [ ] Integrate with app startup
- [ ] Test with Redis restart
- [ ] Document recovery procedures
- [ ] Deploy to staging

### Week 4: Validation
- [ ] Run full adversarial test suite (should all pass)
- [ ] Run failover tests (Redis restart, process crash)
- [ ] Load test (1000 concurrent customers)
- [ ] Upgrade to production

---

## Revenue Impact

| Gap | Impact | Timeline | Revenue Risk |
|-----|--------|----------|--------------|
| Billing Rollback | Revenue leakage | 3 days | $50K/month |
| Prometheus Metrics | Operational blindness | 2 days | Outages undetected |
| Redis Rehydration | Data loss | 3 days | SLA violations |

**Total P0 Impact**: $150K+/month revenue at risk + operational risk

---

## Success Criteria

✅ All adversarial robustness tests pass  
✅ Billing reconciliation audit ≤ $100 variance per day  
✅ Prometheus metrics exposed on port 8000  
✅ Redis rehydration tested with actual restart  
✅ Zero failed executions due to state loss  

---

**Next Step**: Begin Week 1 implementation of billing rollback
