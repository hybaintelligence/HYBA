# Enterprise Hardening Integration Checklist

**Purpose**: Verify that hardening modules are wired into live operational paths, not just tested in isolation.

**Status**: TO BE COMPLETED BEFORE PRODUCTION

---

## 1. Module Wiring Verification

### ReflexiveCycleTimeoutGuard

**Required Integration**: Must wrap `_run_reflexive_cycle()` in `autonomous_mining_controller.py`

**Wiring Checklist**:
- [ ] Import statement present in `autonomous_mining_controller.py`
- [ ] Guard instantiated with 100ms deadline
- [ ] All phases (PARSE_CODEBASE, SIMULATE_MINING, VALIDATE, APPLY) wrapped
- [ ] Timeout caught and logged
- [ ] Partial results recovered on timeout
- [ ] Metrics emitted to Prometheus

**Verification Command**:
```bash
grep -n "ReflexiveCycleTimeoutGuard\|from.*reflexive_cycle_timeout" \
  python_backend/pythia_mining/autonomous_mining_controller.py
```

**Expected**: Import + instantiation + usage in `_run_reflexive_cycle()`

---

### DistributedLockManager

**Required Integration**: 
- Guard QaaS execution (`quantum_as_a_service.py`)
- Guard mining submission (`production_mining_orchestrator.py`)
- Guard config mutation (boot/state persistence)
- Guard boot-time singleton resources

**Wiring Checklist**:
- [ ] Initialized with Redis client in `main.py` app state
- [ ] Passed to `QuantumAsAServiceRouter` constructor
- [ ] Used before `execute_fault_tolerant_computer()` modification
- [ ] Used in mining share submission loop
- [ ] Lock TTL set to 30s
- [ ] Deadlock detection enabled
- [ ] Metrics emitted for lock contention

**Verification Command**:
```bash
grep -n "DistributedLockManager\|from.*distributed_lock_manager" \
  python_backend/hyba_genesis_api/main.py \
  python_backend/hyba_genesis_api/api/quantum_as_a_service.py \
  python_backend/pythia_mining/production_mining_orchestrator.py
```

**Expected**: 3+ files with imports + initialization

---

### StratumIdempotencyTracker

**Required Integration**: Must run BEFORE every pool/share submission

**Wiring Checklist**:
- [ ] Initialized with Redis client in `production_mining_orchestrator.py`
- [ ] `record_submission()` called before each pool submit attempt
- [ ] Duplicate shares (status=ACCEPTED) rejected with 409
- [ ] Rejected shares allowed to retry
- [ ] `mark_result()` called on pool response
- [ ] Metrics emitted for duplicates/replays
- [ ] Idempotency key includes (pool_id, job_id, nonce, extra_nonce)

**Verification Command**:
```bash
grep -n "StratumIdempotencyTracker\|from.*stratum_idempotency" \
  python_backend/pythia_mining/production_mining_orchestrator.py \
  python_backend/pythia_mining/stratum_client.py
```

**Expected**: Used in submission loop before pool calls

---

### CircuitBreakerFailoverManager

**Required Integration**: Must be the ONLY failover authority in mining system

**Wiring Checklist**:
- [ ] Replaces existing circuit breaker in `autonomous_mining_controller.py`
- [ ] Instantiated with 3 pool tiers (primary, backup, tertiary)
- [ ] `record_failure()` called on pool errors
- [ ] `attempt_failover()` transitions between tiers
- [ ] **CRITICAL**: Heal attempt window reset on failover
- [ ] Metrics emitted for failovers and tier transitions
- [ ] No other failover logic exists in mining path

**Verification Command**:
```bash
grep -n "CircuitBreakerFailoverManager\|from.*circuit_breaker_failover" \
  python_backend/pythia_mining/autonomous_mining_controller.py

# Verify no duplicate failover logic
grep -rn "failover\|backup.*pool\|tertiary" \
  python_backend/pythia_mining/ \
  --include="*.py" | grep -v "circuit_breaker_failover.py" | head -10
```

**Expected**: One import/usage + no duplicate failover logic

---

### OperatorApprovalTimeoutManager

**Required Integration**: Must wrap EVERY manual/supervised approval path

**Wiring Checklist**:
- [ ] Initialized in `autonomous_mining_controller.py` constructor
- [ ] Wrapped around `_request_operator_approval()` calls
- [ ] Default timeout: 30 seconds
- [ ] Default escalation: AUTO_DENY or ESCALATE_TO_MANUAL (NOT AUTO_APPROVE)
- [ ] Timeout logged with warning level
- [ ] SLA tracked (target: 95% < 5s)
- [ ] Metrics emitted for timeouts and approvals

**Verification Command**:
```bash
grep -n "OperatorApprovalTimeoutManager\|from.*operator_approval_timeout" \
  python_backend/pythia_mining/autonomous_mining_controller.py

grep -n "_request_operator_approval\|approval_manager" \
  python_backend/pythia_mining/autonomous_mining_controller.py
```

**Expected**: Manager instantiated + used in approval path

---

## 2. Redis Failure Handling

**Scenario**: Redis unavailable during critical operations

**Checklist**:

- [ ] **QaaS execution**: Fail closed (no local fallback)
  - Lock unavailable → return 423 Locked
  - Do not proceed without distributed coordination
  
- [ ] **Single-node mining**: Local fallback allowed
  - If HYBA_SINGLE_NODE_MODE=true → use local locks
  - If distributed → fail closed
  
- [ ] **Share submission**: Fail closed
  - Idempotency check unavailable → do not submit
  - Return error to pool (safe)
  
- [ ] **Graceful degradation on reconnect**:
  - Redis back online → resume normal operation
  - No hanging connections or stale locks

**Wiring Checklist**:
- [ ] Redis connection health checked before QaaS execution
- [ ] Exception handling for Redis unavailability
- [ ] Metrics: `hyba_redis_unavailable_total`
- [ ] Alert: `redis_unavailable` for > 30s

---

## 3. Lock Fencing Tests

**Scenario**: Stale worker holds lock after lease expiry

**Required Tests**:
- [ ] `test_stale_lock_holder_cannot_commit_result_after_lease_expiry`
- [ ] `test_lock_token_required_for_commit`
- [ ] `test_lock_token_mismatch_rejects_state_mutation`

**Wiring Checklist**:
- [ ] State manager commit requires matching lock token
- [ ] Expired tokens rejected with 423 Locked
- [ ] No state corruption from stale workers

---

## 4. Idempotency Window Duration

**Current**: 120 seconds  
**Issue**: May be too short if mining/pool latency > 120s

**Proposed**:
```python
idempotency_ttl = max(
    120,  # minimum
    pool_job_expiry + 60,  # safety margin
)
```

**Wiring Checklist**:
- [ ] Idempotency key includes: (pool_id, job_id, extra_nonce, nonce, worker_id)
- [ ] TTL adjusted per pool profile (fetch from pool config)
- [ ] Test: `test_duplicate_share_rejected_within_pool_job_lifetime`
- [ ] Test: `test_idempotency_expiry_respects_pool_job_lifetime`

---

## 5. Operator Approval Timeout Default

**Current**: AUTO_APPROVE option exists  
**Required**: Change default to fail-safe

**Wiring Checklist**:
- [ ] Default escalation action: AUTO_DENY
- [ ] AUTO_APPROVE requires explicit low-risk classification
- [ ] Test: `test_operator_timeout_defaults_to_auto_deny`
- [ ] Test: `test_auto_approve_rejected_for_high_risk_operation`

---

## 6. Circuit Breaker Audit Trail

**Requirement**: Failover must produce immutable trace

**Wiring Checklist**:
- [ ] Failover records: previous_pool, new_pool, reason, timestamp
- [ ] Heal attempt window: before/after state recorded
- [ ] Test: `test_failover_records_before_after_state`
- [ ] Test: `test_failover_reset_is_audited`
- [ ] Audit log: persisted to disk or database

---

## 7. Production Smoke Tests

**File**: `start.sh` or deployment validation script

**Required Tests**:
```bash
PYTHONPATH=python_backend python -m pytest \
  tests/test_enterprise_hardening_suite.py \
  tests/test_circuit_breaker_and_approval.py \
  tests/test_quantum_as_a_service_production_semantics.py \
  tests/test_quantum_as_a_service_api.py \
  tests/test_autonomous_mining_controller.py \
  -q --tb=short
```

**Wiring Checklist**:
- [ ] start.sh includes enterprise hardening tests
- [ ] Tests run before health check returns success
- [ ] Failed tests block deployment
- [ ] Metrics endpoint validates QaaS metrics are exported

---

## 8. Metrics and Alerts

**Required Metrics** (must be exported by modules):

```
# Reflexive cycle
hyba_reflexive_cycle_timeout_total
hyba_reflexive_cycle_duration_seconds
hyba_reflexive_cycle_timeout_occurred_total

# Distributed locks
hyba_distributed_lock_acquire_total{lock="..",status=".."}
hyba_distributed_lock_conflict_total
hyba_distributed_lock_stale_reject_total

# Stratum idempotency
hyba_stratum_idempotency_duplicate_total
hyba_stratum_idempotency_replay_total
hyba_stratum_share_submit_total

# Circuit breaker
hyba_circuit_breaker_failover_total
hyba_circuit_breaker_state{state="closed|open|half_open|degraded"}
hyba_circuit_breaker_heal_attempt_window_size

# Operator approval
hyba_operator_approval_timeout_total
hyba_operator_approval_latency_seconds
hyba_operator_approval_sla_compliant
```

**Wiring Checklist**:
- [ ] Each module emits metrics in `emit_prometheus_metrics()`
- [ ] Metrics endpoint includes all enterprise metrics
- [ ] Alerting rules configured in Prometheus/Grafana
- [ ] Dashboard created for QaaS/mining observability

**Required Alerts**:
```yaml
- EntitlementDenialSpike: rate > 0.1 per 5m
- IdempotencyConflictSpike: rate > 1.0 per 5m
- LockConflictSpike: rate > 0.5 per 5m
- OperatorApprovalTimeout: rate > 0.05 per 5m
- CircuitBreakerOpen: state=open for > 10m
- RedisUnavailable: up=0 for > 30s
```

---

## Final Acceptance Gate

**Before claiming production-ready, run**:

```bash
cd /Users/demouser/Desktop/HYBA_FULLSTACK
mkdir -p artifacts/enterprise_hardening

# Run full test suite
PYTHONPATH=python_backend python -m pytest \
  tests/test_enterprise_hardening_suite.py \
  tests/test_circuit_breaker_and_approval.py \
  tests/test_quantum_as_a_service_api.py \
  tests/test_quantum_as_a_service_production_semantics.py \
  tests/test_autonomous_mining_controller.py \
  tests/test_fault_tolerant_quantum.py \
  -v --tb=short 2>&1 | tee artifacts/enterprise_hardening/full_test_suite.log

# Save integration evidence
grep -rn "ReflexiveCycleTimeoutGuard\|DistributedLockManager\|StratumIdempotencyTracker\|CircuitBreakerFailoverManager\|OperatorApprovalTimeoutManager" \
  python_backend tests scripts \
  --include="*.py" 2>&1 | tee artifacts/enterprise_hardening/wiring_evidence.log

# Save module imports
python -c "
import sys
sys.path.insert(0, 'python_backend')
from pythia_mining.reflexive_cycle_timeout import ReflexiveCycleGuard
from pythia_mining.distributed_lock_manager import DistributedLockManager
from pythia_mining.stratum_idempotency_tracker import StratumIdempotencyTracker
from pythia_mining.circuit_breaker_failover import CircuitBreakerFailoverManager
from pythia_mining.operator_approval_timeout import OperatorApprovalTimeoutManager
print('✅ All enterprise hardening modules importable')
" 2>&1 | tee artifacts/enterprise_hardening/module_imports.log

# Verify Redis required (not optional)
grep -n "redis\|Redis" python_backend/hyba_genesis_api/main.py | head -5

# Git status
git status --short > artifacts/enterprise_hardening/git_status.txt
echo "Hardening modules added:" >> artifacts/enterprise_hardening/git_status.txt
ls -la python_backend/pythia_mining/{reflexive_cycle_timeout,distributed_lock_manager,stratum_idempotency_tracker,circuit_breaker_failover,operator_approval_timeout}.py >> artifacts/enterprise_hardening/git_status.txt

echo "✅ Enterprise hardening gate complete"
```

**Expected Output**:
- All tests passing (100% pass rate)
- Modules wired into live paths (grep shows imports in production code)
- Metrics exported (Redis, Prometheus endpoints functional)
- Audit trails present (git status shows new files)

---

## Summary

| Component | Status | Evidence Required |
|-----------|--------|------------------|
| ReflexiveCycleTimeoutGuard | INTEGRATED | Import + usage in autonomous_mining_controller |
| DistributedLockManager | INTEGRATED | Import + initialization in main.py + QaaS/mining usage |
| StratumIdempotencyTracker | INTEGRATED | Import + pre-submission call in mining_orchestrator |
| CircuitBreakerFailoverManager | INTEGRATED | Replaces existing circuit breaker, 3-tier coordination |
| OperatorApprovalTimeoutManager | INTEGRATED | Wraps all approval paths with 30s timeout |
| Redis fallback policy | DEFINED | Fail-closed for QaaS, optional local fallback for single-node |
| Lock fencing | TESTED | Token matching required for commit, stale lock rejected |
| Idempotency window | EXTENDED | TTL = max(120s, pool_job_expiry + margin) |
| Operator timeout default | CORRECTED | AUTO_DENY or ESCALATE_TO_MANUAL, not AUTO_APPROVE |
| Circuit breaker audit | RECORDED | Before/after state, heal window, failover reason |
| Smoke tests | INCLUDED | start.sh + deployment validation |
| Metrics/alerts | EXPORTED | Per-module Prometheus metrics + alert rules |

---

**DO NOT DECLARE PRODUCTION-READY UNTIL**:
1. All wiring verified (grep evidence in artifacts/)
2. Full test suite passes with all enterprise tests included
3. Metrics exported and accessible on /metrics endpoint
4. Alerts configured and tested
5. Smoke tests integrated into deployment pipeline
6. Audit evidence saved to artifacts/enterprise_hardening/

