# HYBA FULLSTACK - Test Gap Analysis Report
**Generated:** 2026-06-19  
**Test Suite Status:** 979 passed / 50 failed (Backend) | 201 passed / 9 failed (Frontend)

---

## Executive Summary

The test suite reveals **3 critical bug categories** that need immediate attention:

1. **CRITICAL: dodecahedral_solver.py NameError** - `job` variable undefined (affects 15+ tests)
2. **CRITICAL: IIT 4.0 Φ computation failures** - Integration metrics returning 0.0 or inverted values
3. **MEDIUM: API validation errors** - JSON serialization and authentication issues

---

## Backend Test Failures (50 failed, 979 passed)

### 🔴 Category 1: Quantum Solver Critical Bug (15+ failures)

**Root Cause:** `python_backend/pythia_mining/dodecahedral_solver.py:404` - undefined variable `job`

```python
# Line 404 in dodecahedral_solver.py
if job is not None:  # ❌ NameError: name 'job' is not defined
```

**Affected Tests:**
- `test_agent3_quantum_solvers.py::test_classical_fallback_activation_when_no_marked_states`
- `test_agent3_quantum_solvers.py::test_classical_brute_force_correctness_sets_solution_metadata`
- `test_agent3_quantum_solvers.py::test_fallback_determinism_for_fresh_solvers`
- `test_agent3_quantum_solvers.py::test_first_hit_latency_is_recorded_for_solve`
- `test_agent3_quantum_solvers.py::test_solver_throughput_under_small_load_completes_quickly`
- `test_backend_workflows.py::MiningPropertyAndIntegrationTests::test_configured_solver_projects_nonce_inside_declared_ranges`
- `test_backend_workflows.py::MiningPropertyAndIntegrationTests::test_connect_search_submit_smoke_uses_validation_before_accounting`
- `test_backend_workflows.py::MiningPropertyAndIntegrationTests::test_solve_updates_telemetry_and_projects_nonce_inside_range`
- `test_e2e_pulvini_workflow.py::PulviniProductionWorkflowTests::test_full_workflow_pool_arrival_to_share_acceptance`
- `test_funding_engine_deployment_gate.py::test_deterministic_search_repeats_nonce`
- `test_gap_local_pow_validation.py::test_solver_finds_nonce_within_regtest_target_in_bounded_time`
- `test_gap_phi_search_vs_random.py` (7 tests)
- `test_hendrix_phi_performance_benchmark.py::test_hendrix_phi_finds_valid_on_regtest`
- `test_mining_capability_benchmarks.py::test_capability_async_benchmark_suite`
- `test_mining_innovation_properties.py::test_property_pythia_search_is_deterministic_for_same_target_and_range`

**Impact:** HIGH - Core mining solver cannot execute, blocking production deployment

---

### 🔴 Category 2: HENDRIX-Φ Solver API Changes (6 failures)

**Root Cause:** `hendrix_phi_solver.py` - `phi_gradient_proposal()` method signature changed

```python
# Tests expect:
hendrix.phi_gradient_proposal(start_nonce=X, ...)

# But method signature doesn't accept start_nonce
TypeError: phi_gradient_proposal() got an unexpected keyword argument 'start_nonce'
```

**Affected Tests:**
- `test_hendrix_phi_performance_benchmark.py::test_hendrix_phi_vs_random_easy_target`
- `test_hendrix_phi_performance_benchmark.py::test_hendrix_phi_vs_random_medium_target`
- `test_hendrix_phi_performance_benchmark.py::test_hendrix_phi_vs_random_hard_target`
- `test_hendrix_phi_performance_benchmark.py::test_hendrix_phi_deterministic_within_target`
- `test_hendrix_phi_performance_benchmark.py::test_hendrix_phi_top_percentile_placement`

**Additional Performance Issue:**
```
test_hendrix_phi_performance_benchmark.py::test_hendrix_phi_batch_throughput
AssertionError: HENDRIX-Φ throughput too low: 34224/sec
assert 34223.861686218166 >= 100000
```

**Impact:** MEDIUM - Performance benchmarks fail, φ-guided search slower than expected

---

### 🔴 Category 3: IIT 4.0 Φ Computation Failures (4 failures)

**Root Cause:** Integrated Information (Φ) metric returning 0.0 or incorrect values

```python
# test_iit_4_complete.py::test_phi_max_exceeds_local_phi
AssertionError: 0.0 not greater than or equal to np.float64(0.9)
Φ_max (best partition): 0.0000  # ❌ Should be > 0
Φ_local (full system): 1.0000

# test_iit_phi_mining_correlation.py::test_phi_multivariate_health_assessment
AssertionError: all_healthy Φ should exceed mixed: 0.0000 vs 0.4043
assert 0.0 > 0.4042866535636551  # ❌ Inverted

# test_iit_phi_mining_correlation.py::test_phi_density_vs_share_acceptance_correlation
AssertionError: Expected positive correlation, got -0.3609  # ❌ Negative correlation
```

**Affected Tests:**
- `test_iit_4_complete.py::TestIIT4Complete::test_phi_max_exceeds_local_phi`
- `test_iit_phi_mining_correlation.py::test_consciousness_engine_regime_transitions`
- `test_iit_phi_mining_correlation.py::test_phi_density_vs_share_acceptance_correlation`
- `test_iit_phi_mining_correlation.py::test_iit_analyzer_phi_consistency_across_health_states`
- `test_iit_phi_mining_correlation.py::test_phi_multivariate_health_assessment`

**Impact:** MEDIUM - Consciousness Engine metrics unreliable, regime transitions not detected

---

### 🟡 Category 4: API Validation & Serialization (5 failures)

**Issue 1: JSON Serialization Error**
```python
# test_backend_mining_api.py::test_connect_rejects_unknown_pool_with_validation_error
TypeError: Object of type ValueError is not JSON serializable
# In: python_backend/hyba_genesis_api/core/api_posture.py:188
```

**Issue 2: Pydantic v2 Deprecation Warnings**
```python
# python_backend/hyba_genesis_api/api/admin.py:98,422,461
PydanticDeprecatedSince20: Support for class-based `config` is deprecated, 
use ConfigDict instead.
```

**Affected Tests:**
- `test_backend_mining_api.py::test_connect_rejects_unknown_pool_with_validation_error`
- `test_backend_intelligence_api.py::test_ai_chat_fails_closed_when_runtime_is_unconfigured`
- `test_backend_intelligence_api.py::test_v1_intelligence_health_reports_runtime_surface`
- `test_backend_intelligence_api.py::test_v1_intelligence_audit_returns_claim_bounded_payload`
- `test_backend_security_api.py::test_security_regeneration_status_returns_module_summary`

**Impact:** LOW - Error handling broken, API returns 500 instead of proper validation errors

---

### 🟡 Category 5: Capability Registry & Evidence Manifest (6 failures)

**Root Cause:** Missing or outdated capability registry validation

**Affected Tests:**
- `test_adaptive_capability_registry.py::test_registry_has_expected_capability_ids`
- `test_adaptive_capability_registry.py::test_each_capability_has_required_evidence_fields`
- `test_adaptive_capability_registry.py::test_registry_referenced_tests_exist`
- `test_adaptive_capability_registry.py::test_registry_preserves_claim_boundary_language`
- `test_adaptive_capability_registry.py::test_status_values_are_from_declared_vocabulary`
- `test_claim_evidence_manifest.py::test_claim_evidence_manifest_is_complete_and_points_to_existing_files`

**Impact:** LOW - Documentation/governance layer, not runtime-critical

---

### 🟡 Category 6: Additional Isolated Failures (9 tests)

1. **test_adaptive_science_claim_gate.py::test_controlled_science_program_preserves_proof_ladder**
2. **test_agent4_data_storage_knowledge.py::TestAgent4Proofs::test_proof_mathematical_soundness_verifies_inverse**
3. **test_autonomous_mining_controller.py** (2 tests - self-optimization)
4. **test_backend_workflows.py::SubstrateUnitTests::test_substrate_initialization_is_deterministic_and_json_serializable**
5. **test_backend_workflows.py::AdversarialValidationTests::test_production_requires_external_pool_configuration_and_blocks_fixtures**
6. **test_great_minds_integration.py::TestFourierHarmonicAnalysis::test_wavelet_analysis**

---

## Frontend Test Failures (9 failed, 201 passed)

### 🟡 Category 1: API Client Authentication (1 failure)

**Root Cause:** Authorization header not set in mining API calls

```typescript
// test_apiClient_mining.test.ts
expect(headers.get("Authorization")).toBe("Bearer mining-token");
// Actual: null ❌
```

**Impact:** MEDIUM - Mining API calls will fail authentication in production

---

### 🟡 Category 2: Security Swarm Routes (3 failures)

**Issue:** Syndrome bits exposed in HTTP responses (should be filtered)

```typescript
// test_security_swarm_routes.test.ts
expect(body.defense_systems.stabilizer_monitor).not.toHaveProperty("syndrome");
// Actual: syndrome array present ❌

// Missing endpoint: POST /api/security/swarm/respond
expected 202, received 404
```

**Impact:** LOW - Security implementation incomplete, syndrome bits leak

---

### 🟡 Category 3: Unhandled Promise Rejections (2 errors)

**Issue:** Test cleanup not awaiting async operations

```typescript
// test_apiClient_error_retry.test.ts
Unhandled Rejection: HybaApiError: nope (code: 'still_unavailable')
Unhandled Rejection: TypeError: network offline
```

**Impact:** LOW - Test infrastructure issue, not production bug

---

## Priority Fixes

### P0 - Critical (Blocks Production)

1. **Fix dodecahedral_solver.py NameError**
   - File: `python_backend/pythia_mining/dodecahedral_solver.py:404`
   - Fix: Pass `job` parameter to `_classical_fallback()` method
   - Tests Fixed: 15+

2. **Fix HENDRIX-Φ API signature**
   - File: `python_backend/pythia_mining/hendrix_phi_solver.py`
   - Fix: Add `start_nonce` parameter to `phi_gradient_proposal()`
   - Tests Fixed: 6

### P1 - High (Affects Core Functionality)

3. **Fix IIT 4.0 Φ computation**
   - Files: `python_backend/pythia_mining/iit_4_analyzer.py`, `consciousness_engine.py`
   - Fix: Debug partition algorithm returning Φ_max = 0.0
   - Tests Fixed: 4

4. **Fix HENDRIX-Φ throughput**
   - Current: 34K nonces/sec
   - Target: 100K nonces/sec
   - Fix: Profile and optimize φ-resonance scoring path

### P2 - Medium (Error Handling & Documentation)

5. **Fix API JSON serialization**
   - File: `python_backend/hyba_genesis_api/core/api_posture.py:188`
   - Fix: Convert ValueError to dict before JSONResponse
   - Tests Fixed: 5

6. **Add Authorization header to mining API**
   - File: `src/apiClient.ts`
   - Fix: Include auth token in mining endpoint calls
   - Tests Fixed: 1

### P3 - Low (Documentation & Test Infrastructure)

7. **Update capability registry**
   - Tests Fixed: 6

8. **Filter syndrome bits from HTTP responses**
   - Tests Fixed: 2

9. **Fix test cleanup (unhandled rejections)**
   - Tests Fixed: 2

---

## Test Coverage Summary

| Suite | Passed | Failed | Skip | Total | Pass Rate |
|-------|--------|--------|------|-------|-----------|
| Backend | 979 | 50 | 36 | 1065 | 95.1% |
| Frontend | 201 | 9 | 0 | 210 | 95.7% |
| **Total** | **1180** | **59** | **36** | **1275** | **95.4%** |

---

## Recommendations

1. **Immediate Action**: Fix P0 dodecahedral_solver.py bug (blocking 15+ tests)
2. **Code Review**: HENDRIX-Φ API changes broke 6 benchmarks - requires interface stability
3. **IIT 4.0 Investigation**: Φ computation algorithm needs mathematical review
4. **API Hardening**: JSON serialization and auth headers need production-grade error handling
5. **Performance Profiling**: HENDRIX-Φ throughput 66% below target (34K vs 100K nonces/sec)

---

## Next Steps

```bash
# 1. Fix dodecahedral_solver.py
vim python_backend/pythia_mining/dodecahedral_solver.py +404

# 2. Fix HENDRIX-Φ API
vim python_backend/pythia_mining/hendrix_phi_solver.py

# 3. Re-run affected tests
npm run test:backend -- tests/test_agent3_quantum_solvers.py -v
npm run test:backend -- tests/test_hendrix_phi_performance_benchmark.py -v

# 4. Full regression test
npm run test:all
```

---

**Report End**
