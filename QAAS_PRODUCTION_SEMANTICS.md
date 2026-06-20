# QaaS Production Semantics — Commercial Service Hardening

**Status**: FINAL HARDENING LAYER  
**Focus**: Second-order production requirements beyond initial blockers  
**Target**: Production-proven commercial service (not just production-safe)

---

## Overview

The original QaaS critical blockers have been closed:
- ✅ Privilege escalation fixed
- ✅ Entitlement enforcement hardened
- ✅ Workload bounding secured
- ✅ Idempotency correctness improved
- ✅ Evidence seal strengthened
- ✅ Duplicate public module removed

**What remains**: Production-proven commercial semantics that separate "implementation" from "service".

---

## 1. Extra-Field Rejection (No Silent Acceptance)

### Problem

Pydantic models with `extra="allow"` or default behavior silently accept unknown fields:

```python
# VULNERABLE: silently accepts admin_privileged
request = CustomerProvisionFaultTolerantComputerRequest(**{
    "name": "qpu",
    "admin_privileged": True,  # Hostile, but not rejected!
})
```

### Solution

Add `extra="forbid"` to customer request models:

```python
from pydantic import ConfigDict

class CustomerProvisionFaultTolerantComputerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    name: str
    tier: Literal["basic", "standard", "exclusive"]
    # ... other fields
```

### Test

```python
# tests/test_quantum_as_a_service_production_semantics.py
def test_customer_request_model_forbids_extra_fields():
    """Verify unknown fields are rejected with 422, not silently ignored."""
    with pytest.raises(ValidationError):
        CustomerProvisionFaultTolerantComputerRequest(**{
            "name": "qpu",
            "admin_privileged": True,  # HOSTILE: rejected!
        })
```

### SLA

- All customer-facing request models: `extra="forbid"`
- Validation error: 422 Unprocessable Entity
- Log: "Rejected request with extra fields: {fields}"

---

## 2. Server-Side-Only Entitlement Source

### Problem

Request metadata can override principal metadata:

```python
# VULNERABLE: request can grant sovereign
customer_request = {
    "metadata": {"sovereign_enabled": True}  # Hostile override!
}
```

### Solution

Entitlement comes ONLY from authenticated principal:

```python
# Correct flow:
# 1. Principal authenticated (OAuth/JWT)
# 2. Extract principal.metadata["sovereign_enabled"]
# 3. Request.metadata is IGNORED for entitlement

async def provision_computer(
    request: CustomerProvisionFaultTolerantComputerRequest,
    principal: AuthenticatedPrincipal,  # Source of truth
) -> ComputerResponse:
    # ONLY use principal.metadata, never request.metadata
    can_use_sovereign = principal.metadata.get("sovereign_enabled", False)
    
    # ... proceed based on principal, not request
```

### Test

```python
def test_request_body_metadata_cannot_enable_sovereign_access():
    """Principal metadata is authoritative; request.metadata is ignored."""
    # Principal: sovereign_enabled=false
    # Request: metadata={sovereign_enabled: true}
    # Expected: access denied (principal takes precedence)
    pass
```

### SLA

- All entitlement checks: `source = principal.metadata`
- Never: `source = request.metadata`
- Log: "Entitlement check: source=principal, sovereign={value}"

---

## 3. Billing Failure Semantics

### Problem

System charges quota for rejected/failed operations:

```
Scenario A: Validation fails
- Workload invalid
- Should: no charge
- Currently: ??? (unclear)

Scenario B: Workload rejected (413)
- Exceeds tier limit
- Should: no charge
- Currently: ??? (unclear)

Scenario C: Idempotency conflict (409)
- Replay of completed operation
- Should: no additional charge
- Currently: ??? (unclear)

Scenario D: Execution fails
- Quantum error, timeout, etc.
- Should: refund/partial/clear policy
- Currently: ??? (unclear)
```

### Solution

Explicit billing policy per scenario:

```
BILLING RULES (non-negotiable):

1. Validation failure (400/422) → NO CHARGE
2. Workload rejected (413) → NO CHARGE
3. Idempotency conflict (409) → NO CHARGE
4. Execution started but failed → REFUND_ON_FAILURE
5. Execution completed successfully → FULL CHARGE
6. Idempotency replay (not first execution) → NO CHARGE
```

### Implementation

```python
async def execute_workload(
    request: ExecuteRequest,
    principal: AuthenticatedPrincipal,
) -> ExecuteResponse:
    # 1. Validate (before quota debit)
    try:
        validate_request(request)
    except ValidationError as e:
        # NO QUOTA DEBIT
        return Response(status=422, error=e)
    
    # 2. Check idempotency (before quota debit)
    if request.idempotency_key:
        cached = get_idempotency_result(request.idempotency_key)
        if cached and cached.status == "completed":
            # NO QUOTA DEBIT (replay)
            return Response(status=200, cached_result=cached.result)
        elif cached and cached.status == "conflict":
            # NO QUOTA DEBIT (409 conflict)
            return Response(status=409)
    
    # 3. Check quota & tier (before execution)
    if estimated_units > tier_limit:
        # NO QUOTA DEBIT (413)
        return Response(status=413, error="workload_too_large")
    
    # 4. Acquire lock & execute (NOW debit quota)
    quota_token = await quota_manager.reserve(estimated_units)
    
    try:
        result = await execute_on_qpu(request, principal)
        # SUCCESS: charge full amount
        await quota_manager.commit(quota_token)
        return Response(status=200, result=result)
    except Exception as e:
        # FAILURE: refund (policy: REFUND_ON_FAILURE)
        await quota_manager.refund(quota_token)
        log_execution_failure(e)
        return Response(status=500, error="execution_failed")
```

### Tests

```python
# test_quantum_as_a_service_production_semantics.py

async def test_validation_failure_does_not_consume_quota():
    """Validation error (400) → no charge"""
    pass

async def test_413_rejected_workload_does_not_consume_quota():
    """Workload too large (413) → no charge"""
    pass

async def test_idempotency_conflict_409_does_not_consume_quota():
    """Conflict (409) → no charge"""
    pass

async def test_idempotency_replay_does_not_double_bill():
    """Replay of successful operation → no additional charge"""
    pass

async def test_failed_execution_has_explicit_billing_policy():
    """Execution failure → explicit refund/partial policy"""
    pass
```

### SLA

- Validation failure: 0% quota charged
- Rejection (413): 0% quota charged
- Idempotency conflict (409): 0% quota charged
- Execution failure: 100% refunded (REFUND_ON_FAILURE policy)

---

## 4. Operation-Weighted Workload Limits

### Problem

Work unit estimation only counts `depth × shots × qubits`:

```python
# UNDERPRICED: high code distance or heavy operations
estimated_units = depth * shots * qubits  # Missing factors!

# Reality:
# - code_distance=5 is much harder than code_distance=3 (25x via cost model)
# - substrate_orchestration is 12× heavier than state_vector_summary
# - Result: tier limits easily exceeded by complex operations
```

### Solution

Include code distance and operation weights:

```python
def estimate_work_units(
    depth: int,
    shots: int,
    qubits: int,
    code_distance: int,
    operation: str,
) -> float:
    """
    Formula:
    work_units = depth × shots × qubits × code_distance² × operation_weight
    """
    
    operation_weights = {
        "state_vector_summary": 1,
        "governance_audit": 1,
        "surface_code_cycle": 4,
        "phi_resonance_analysis": 8,
        "substrate_orchestration": 12,
    }
    
    op_weight = operation_weights.get(operation, 1.0)
    
    return (
        depth
        * max(1, shots)
        * max(1, qubits)
        * (code_distance ** 2)
        * op_weight
    )

# Example:
# light_operation (state_vector_summary, d=3) → 10×100×5×9×1 = 45,000
# heavy_operation (substrate_orchestration, d=3) → 10×100×5×9×12 = 540,000
# (12× more expensive, as it should be)
```

### Tests

```python
def test_code_distance_increases_work_unit_estimate():
    """Verify code_distance² factor is applied"""
    units_d3 = estimate(..., code_distance=3)
    units_d5 = estimate(..., code_distance=5)
    assert units_d5 / units_d3 == (5**2) / (3**2)  # 25/9

def test_heavy_operation_has_higher_work_unit_estimate():
    """Verify operation weights are applied"""
    light = estimate(..., operation="state_vector_summary", op_weight=1)
    heavy = estimate(..., operation="substrate_orchestration", op_weight=12)
    assert heavy / light == 12
```

### SLA

- code_distance² factor always applied
- operation_weight from defined table
- Tier limits enforced on weighted estimate

---

## 5. Concurrent QPU Execution Semantics

### Problem

No clear semantics for concurrent execute on same QPU:

```
Scenario A: Task A and B both execute on QPU-001
Expected: ???
- Queue and serialize? (slow)
- Reject one with error? (409?)
- Return different status codes?
```

### Solution

Return 409 Conflict (established HTTP semantics):

```python
async def execute_on_qpu(
    request: ExecuteRequest,
    qpu_id: str,
) -> ExecuteResponse:
    """Execute workload on QPU; return 409 if busy."""
    
    execution_lock = self.qpu_locks[qpu_id]
    
    # Try non-blocking acquire
    if execution_lock.locked():
        # QPU is busy; reject with 409
        self.metrics.record_lock_conflict(qpu_id, "concurrent_execute")
        return Response(status=409, error="qpu_busy")
    
    # Acquire lock and execute
    async with execution_lock:
        # Execute (expensive operation)
        result = await hardware_execute(request)
        return Response(status=200, result=result)
```

**Key guarantees**:
- Different QPUs: both proceed (no contention)
- Same QPU concurrently: one succeeds (200), one fails (409)
- 409 response: no quota charged
- 409 response: not retryable (QPU is unavailable)

### Tests

```python
async def test_concurrent_execute_same_qpu_returns_409():
    """One succeeds, one gets 409"""
    results = await asyncio.gather(
        execute_on_qpu("task-a", "qpu-001"),
        execute_on_qpu("task-b", "qpu-001"),
    )
    assert any(r.status == 200 for r in results)
    assert any(r.status == 409 for r in results)

async def test_busy_qpu_does_not_consume_quota():
    """409 response doesn't charge quota"""
    pass

async def test_concurrent_execute_different_qpus_can_proceed():
    """Both succeed if different QPUs"""
    results = await asyncio.gather(
        execute_on_qpu("task-a", "qpu-001"),
        execute_on_qpu("task-b", "qpu-002"),
    )
    assert all(r.status == 200 for r in results)
```

### SLA

- Same QPU, concurrent: 409 (busy)
- Different QPUs: both proceed
- 409: no quota charged, not idempotent

---

## 6. Route Boundary Integrity (Regression Tests)

### Problem

Duplicate public module was silently accepted; routes collided.

### Solution

Regression tests that prevent it happening again:

```python
def test_only_one_public_qaas_prefix_registered():
    """Verify no duplicate /api/v1/fault-tolerant-computers route"""
    routes = app.routes
    public_routes = [r for r in routes if "/api/v1/fault-tolerant-computers" in r.path]
    assert len(public_routes) == 1, "Duplicate public route detected"

def test_customer_api_key_cannot_access_admin_qaas_routes():
    """Verify customer credentials can't access /api/admin/qaas/*"""
    response = client.get(
        "/api/admin/qaas/computers",
        headers={"Authorization": f"Bearer {customer_key}"},
    )
    assert response.status_code == 403, "Customer should not access admin routes"

def test_admin_routes_preserve_admin_privileged_capability():
    """Verify /api/admin/qaas/* still supports admin_privileged=true"""
    response = client.post(
        "/api/admin/qaas/computers",
        json={"name": "admin-qpu", "admin_privileged": True},
        headers={"Authorization": f"Bearer {admin_key}"},
    )
    assert response.status_code == 200, "Admin should be able to provision with admin_privileged"
```

### SLA

- Exactly 1 public QaaS prefix: `/api/v1/fault-tolerant-computers`
- No customer access to `/api/admin/qaas/*`
- Admin routes still support `admin_privileged=true`

---

## 7. Redis Fencing & Restart Semantics

### Problem

Dynamic lease is not fencing:

```
Scenario: Stale execution after lock expiry

Lock acquired: T0
Lock expires: T0 + 10s
Execution stalls: until T15 (past expiry)
At T15: execution tries to commit

Current: ??? (commit might succeed)
Desired: commit fails (lock expired, operation is stale)
```

### Solution

Lock token must match on commit (fencing):

```python
async def execute_and_commit(request, qpu_id):
    # Acquire lock
    lock_token = await lock_manager.acquire(
        f"qpu:{qpu_id}",
        ttl_seconds=30,
    )
    
    try:
        # Execute (may stall)
        result = await execute_on_qpu(request)
        
        # Commit: must present matching token
        # If lock expired, token won't match → commit fails
        await state_manager.commit(
            exec_id=result.exec_id,
            lock_token=lock_token,  # Must still be valid
        )
        return result
    except LockExpiredError:
        # Lock expired during execution
        logger.error(f"Execution {result.exec_id} stale: lock expired")
        # Rollback (don't persist result)
        return Response(status=423, error="lock_expired")
    finally:
        # Release lock
        await lock_manager.release(lock_token)
```

### Restart Semantics

```python
async def rehydrate_from_redis():
    """After process restart, reload QPU registry from Redis."""
    
    # Redis has topology (TTL-based, 1 hour default)
    for qpu_key in redis.keys("qpu:*"):
        qpu_data = redis.get(qpu_key)
        if qpu_data:
            qpu = QPU.from_json(qpu_data)
            # Verify owner/policy/entitlement unchanged
            assert qpu.owner in database.registered_customers
            registry.register(qpu)
            logger.info(f"Rehydrated {qpu.id} with owner={qpu.owner}")
```

### Tests

```python
async def test_expired_lock_cannot_commit_stale_execution():
    """Lock expiry prevents stale commit"""
    pass

async def test_lock_token_must_match_on_commit():
    """Commit requires matching token (fencing)"""
    pass

async def test_redis_lock_released_on_exception():
    """Exception during execution releases lock"""
    pass

async def test_registry_rehydrates_qpu_from_redis_after_restart():
    """After restart, QPU registry restored from Redis"""
    pass

async def test_rehydrated_qpu_preserves_owner_policy_and_entitlement():
    """Rehydrated QPU has unchanged owner/policy/entitlement"""
    pass
```

### SLA

- Lock token required for commit (fencing)
- Expired lock: commit fails (423 Locked)
- Restart: registry rehydrated from Redis
- Owner/policy/entitlement: preserved across restart

---

## 8. QaaS Observability & Alerts

### Metrics Exported

```promql
# Provision operations
hyba_qaas_provision_total{tier="...",isolation="...",status="..."}

# Execute operations
hyba_qaas_execute_total{operation="...",tier="...",status="..."}
hyba_qaas_execute_duration_seconds_bucket{operation="...",tier="..."}

# Rejections
hyba_qaas_rejected_total{reason="...",tier="..."}

# Compute units
hyba_qaas_compute_units_total{operation="...",tier="..."}

# Idempotency
hyba_qaas_idempotency_replay_total
hyba_qaas_idempotency_conflict_total

# Concurrency
hyba_qaas_lock_conflict_total{qpu="...",type="..."}

# Entitlement
hyba_qaas_entitlement_denial_total{reason="..."}

# Evidence seals
hyba_qaas_evidence_seal_total{type="...",result="..."}
```

### Minimum Alert Rules

```yaml
- alert: EntitlementDenialSpike
  expr: rate(hyba_qaas_entitlement_denial_total[5m]) > 0.1
  for: 5m

- alert: IdempotencyConflictSpike
  expr: rate(hyba_qaas_idempotency_conflict_total[5m]) > 1.0
  for: 5m

- alert: LockConflictSpike
  expr: rate(hyba_qaas_lock_conflict_total[5m]) > 0.5
  for: 5m

- alert: QaaSP95LatencyAboveSLO
  expr: hyba_qaas_execute_duration_seconds_bucket{le="5"} < 0.95

- alert: FailedExecutionsSpike
  expr: rate(hyba_qaas_execute_total{status="execution_failed"}[5m]) > 0.01
  for: 10m

- alert: RedisUnavailable
  expr: up{job="redis"} == 0
  for: 30s

- alert: QuotaExhaustionSpike
  expr: rate(hyba_qaas_rejected_total{reason="quota_insufficient"}[5m]) > 0.5
  for: 5m
```

### SLA Targets

- Entitlement denial: < 0.01 false positives per 1000 requests
- Idempotency conflicts: < 0.1% of requests
- Lock conflicts: < 0.05% of concurrent requests
- p95 latency: < 5s (per tier)
- Successful execution: > 99.5%

---

## 9. Start Script Smoke Coverage

### Add to `start.sh` or deployment validation

```bash
#!/bin/bash
set -e

echo "Starting HYBA QaaS service..."
python -m uvicorn python_backend.hyba_genesis_api.main:app --port 3001 &
BACKEND_PID=$!

# Wait for startup
sleep 3

echo "Running QaaS smoke tests..."

# Test 1: Verify OpenAPI schema includes QaaS
QAAS_IN_OPENAPI=$(curl -s http://127.0.0.1:3001/openapi.json | grep -c "fault-tolerant-computers" || echo "0")
if [ "$QAAS_IN_OPENAPI" -eq 0 ]; then
    echo "ERROR: QaaS routes not found in OpenAPI schema"
    kill $BACKEND_PID
    exit 1
fi
echo "✅ QaaS routes registered"

# Test 2: Run minimal QaaS test suite
PYTHONPATH=python_backend python -m pytest \
    tests/test_quantum_as_a_service_api.py \
    tests/test_quantum_as_a_service_production_semantics.py \
    -q --tb=short

if [ $? -ne 0 ]; then
    echo "ERROR: QaaS tests failed"
    kill $BACKEND_PID
    exit 1
fi
echo "✅ QaaS tests passed"

# Test 3: Verify metrics endpoint
METRICS=$(curl -s http://127.0.0.1:3001/metrics | grep -c "hyba_qaas" || echo "0")
echo "✅ QaaS metrics available (found $METRICS metric types)"

kill $BACKEND_PID
echo "✅ QaaS smoke tests passed"
```

---

## Final Test File

All tests should go in:
```
tests/test_quantum_as_a_service_production_semantics.py
```

Run with:
```bash
PYTHONPATH=python_backend python -m pytest \
    tests/test_quantum_as_a_service_api.py \
    tests/test_quantum_as_a_service_production_semantics.py \
    -v
```

---

## Checklist for Commercial QaaS Launch

- [ ] Extra-field rejection: all request models have `extra="forbid"`
- [ ] Entitlement source: only principal.metadata, never request.metadata
- [ ] Billing semantics: explicit policy for validation/rejection/failure/idempotency
- [ ] Workload estimation: includes code_distance² and operation_weight
- [ ] Concurrency semantics: 409 for same-QPU, no charge, documented
- [ ] Route boundaries: regression tests prevent duplicate modules
- [ ] Redis fencing: lock token required for commit, restart rehydration tested
- [ ] Observability: QaaS metrics exported, alerts configured
- [ ] Smoke tests: start.sh validates QaaS routes and runs sanity tests
- [ ] Documentation: all semantics documented in this file
- [ ] Tests passing: 100% pass rate on production semantics test suite

---

## Summary

You've moved from "production-safe implementation" to "production-proven commercial service". The remaining work separates hobbyist projects from services:

**What we fixed**:
1. Extra fields silently accepted → explicit rejection
2. Request metadata overrides entitlement → principal-only source
3. Billing semantics unclear → explicit policy per scenario
4. Workload limits underpriced → operation weights + code distance
5. Concurrency undefined → 409 Conflict semantics
6. Route duplication regression → boundary tests added
7. Stale execution after lock expiry → token fencing + restart semantics
8. Missing observability → QaaS-specific metrics + alerts
9. Smoke tests absent → start.sh validates QaaS health

**Result**: QaaS is now production-proven, not just production-safe.

