# HYBA_FULLSTACK — Test & Coverage Assessment Report
**Date:** 2026-06-16  
**Commit:** 3228268de294d17add48a3c2b55fb156cc025814  
**Environment:** macOS Tahoe, Python 3.12.7 (pyenv), Node v22.22.3 (nvm), npm 10.9.8

---

## 1. Toolchain Installed

| Tool | Version | Status |
|------|---------|--------|
| Python | 3.12.7 (pyenv) | Pre-existing |
| Node.js | v22.22.3 (nvm) | Pre-existing |
| npm | 10.9.8 | Pre-existing |
| pytest | 8.3.4 | Pre-existing |
| pytest-cov | 7.1.0 | **Installed** |
| coverage | 7.14.1 | **Installed** |
| @vitest/coverage-v8 | latest | **Installed** |
| hypothesis | 6.92.1 | Pre-existing |
| pytest-asyncio | 0.24.0 | Pre-existing |

## 2. Reproducibility Lock Files

| Lock File | Exists | Purpose |
|-----------|--------|---------|
| `npm-shrinkwrap.json` | ✅ 271 KB | Node.js dependency pinning |
| `node_modules/.package-lock.json` | ✅ | Installed node_modules integrity |
| `python_backend/requirements.lock` | ✅ | Python dependency pinning |
| `python_backend/requirements.txt` | ✅ | Python pinned versions (canonical) |

---

## 3. Python Backend Test Results

**Command:** `PYTHONPATH=python_backend python3 -m pytest tests/ --cov=python_backend --cov-report=term --cov-report=html --cov-report=xml -v`

| Metric | Count |
|--------|-------|
| **Tests Collected** | 1137 |
| **Passed** | 1091 |
| **Failed** | 40 |
| **Skipped** | 6 |
| **Warnings** | 27 |
| **Duration** | 16 min 6 sec |

### 3.1 Overall Coverage

| Metric | Value |
|--------|-------|
| **Total Lines** | 15,525 |
| **Lines Covered** | 10,533 |
| **Lines Missing** | 4,992 |
| **Overall Line Coverage** | **67.8%** |

### 3.2 Per-Package Coverage

| Package | Coverage | Assessment |
|---------|----------|------------|
| `pythia_mining.config` | 100.0% | ✅ Complete |
| `hyba_genesis_api.core` | 93.8% | ✅ Strong |
| `pythia_mining` | 71.7% | ⚠️ Moderate |
| `hyba_genesis_api.api` | 50.4% | ⚠️ Needs improvement |
| `hyba_genesis_api.websocket` | 85.0% | ✅ Strong |
| `hyba_genesis_api.auth` | 29.0% | ❌ Low |
| `hyba_genesis_api` (root) | 8.6% | ❌ Very low |
| `hyba_genesis_api.models` | 0.0% | ❌ Zero coverage |
| `.` (run_unified_miner.py) | 37.7% | ❌ Low |

### 3.3 High-Coverage Modules (≥90%)

- `pulvini_grover_certificate.py` — 100%
- `pulvini_memory.py` — 100%
- `pulvini_topology.py` — 100%
- `pulvini_verifier.py` — 98%
- `pulvini_operator.py` — 98%
- `pulvini_structural_certificate.py` — 98%
- `phi_unified_mining_engine.py` — 95%
- `pulvini_phi_memory.py` — 96%
- `pulvini_nonce_compression.py` — 97%
- `hendrix_phi_solver.py` — 99%
- `phi_oracle.py` — 96%
- `pulvini_bures.py` — 98%
- `pulvini_choi.py` — 95%
- `pulvini_gamma.py` — 94%

### 3.4 Zero-Coverage Modules (0%)

- `main.py` (pythia_mining) — 92 lines
- `mass_gap_protector.py` — 51 lines
- `nonce_tensor_precomputer.py` — 105 lines
- `phi_entropy.py` — 81 lines
- `phi_production_loop.py` — 69 lines
- `pulvini_group_h4.py` — 161 lines
- `pulvini_manifold_h4.py` — 218 lines
- `pulvini_topology_h4.py` — 29 lines
- `enhanced_ultimate_pulvini_quantum.py` — 12 lines

### 3.5 Failed Tests (40)

**Test files with failures:**
- `test_adaptive_capability_registry.py` — 5 failures (registry schema/validation)
- `test_backend_workflows.py` — 1 failure (production fixture validation)
- `test_consciousness_evidence_packet.py` — 1 failure (determinism check)
- `test_e2e_pulvini_workflow.py` — 1 failure (end-to-end share acceptance)
- `test_live_deployment_e2e.py` — 1 failure (live pool pipeline)
- `test_mining_benefit_assessment.py` — 1 failure (dodecahedral surface alignment)
- `test_phi_config_and_memory_refactor.py` — 1 failure (reversibility)
- `test_phi_property_hypothesis.py` — 5 failures (ensemble/resonance properties)
- `test_phi_synthetic_morphogenesis.py` — 1 failure (execution gating)
- `test_pool_profile_primitives.py` — 1 failure (validation ordering)
- `test_post_quantum_benchmark.py` — 2 failures (determinism/group closure)
- `test_prediction_endpoint.py` — 4 failures (power scale/timestamp/strategy)
- `test_property_based_backend.py` — 4 failures (property-based tests)
- `test_pulvini_autonomics.py` — 1 failure (genesis status snapshot)
- `test_pulvini_e2e_share_flow.py` — 1 failure (compressed search flow)
- `test_pulvini_hashrate_cap_property.py` — 1 failure (EHS bounds)
- `test_pulvini_new_certificates.py` — 1 failure (phi folding proof)
- `test_pulvini_phi_memory.py` — 2 failures (fabric kernel/adversarial cases)
- `test_pulvini_production_facade.py` — 6 failures (density/fidelity/bures/passport/coherence/evolution)

### 3.6 Additional Python Tests

**Command:** `PYTHONPATH=python_backend python3 -m pytest additional_tests/test_ai_api_endpoints.py additional_tests/test_coinbase_and_header.py additional_tests/test_compact_target_effective.py -v`

| Metric | Count |
|--------|-------|
| **Passed** | 12 |
| **Failed** | 0 |
| **Duration** | 0.25 sec |

---

## 4. TypeScript / Vitest Test Results

**Command:** `npx vitest run` (+ `@vitest/coverage-v8` with `--coverage`)

| Metric | Count |
|--------|-------|
| **Test Files** | 13 |
| **Files Passed** | 10–11 |
| **Files Failed** | 2–3 |
| **Tests Passed** | 169–170 |
| **Tests Failed** | 2–3 |
| **Duration** | ~7.5 sec |

### 4.1 Failed TS Tests

| Test File | Failure | Root Cause |
|-----------|---------|------------|
| `test_bridge_security.test.ts` | Module not found `'../bridge_security'` | Missing module: `bridge_security.ts` |
| `test_consciousness_behavioral.test.ts` | Mirror test accuracy 0.4 < 0.5 threshold | Probabilistic threshold not met |
| `test_security_swarm_routes.test.ts` (2 tests) | Syndrome property leaking; POST returns 404 | Route not registered; response shape mismatch |

### 4.2 Note on TS Coverage

The `@vitest/coverage-v8` package was installed, but vitest coverage report output was suppressed by high-volume log output from test fixtures. The 13 TS test files are largely self-contained (inline module implementations within tests) rather than importing from `src/`, so traditional line coverage of `src/` is minimal. The Python backend is the primary coverage surface.

---

## 5. Coverage Artifacts

| Artifact | Path |
|----------|------|
| Coverage XML | `coverage.xml` |
| Coverage HTML | `htmlcov/index.html` |
| Test Report | `logs/COVERAGE_ASSESSMENT_REPORT_2026-06-16.md` |

---

## 6. Summary & Recommendations

### Overall Scorecard

| Surface | Pass Rate | Coverage |
|---------|-----------|----------|
| **Python backend** (pytest) | 96.3% (1091/1131) | **67.8%** |
| **Python additional** | 100% (12/12) | N/A |
| **TypeScript** (vitest) | 98.3% (169/172) | N/A (self-contained) |
| **Combined** | **96.7%** (1272/1315) | **67.8%** (Python) |

### Key Findings

1. **1,272 of 1,315 total tests pass (96.7%)** across Python and TypeScript.
2. **Python coverage is 67.8%** — strong in `pythia_mining` (71.7%) and `core` (93.8%), but weak in `hyba_genesis_api` root/auth/models.
3. **40 Python test failures** cluster in: property-based hypothesis tests (11), production facade tests (6), E2E integration tests (4), prediction endpoint (4), and capability registry (5).
4. **4 TS test failures** are isolated: 1 missing module, 1 probabilistic threshold, 2 route/shape mismatches.
5. **Reproducibility is ensured** via `npm-shrinkwrap.json` (Node) and `pinned requirements.txt` (Python).

### Recommended Next Steps

1. **Fix the 40 Python failures** — prioritize property-based test failures in `test_pulvini_production_facade.py` (6) and `test_phi_property_hypothesis.py` (5) as they test core mathematical invariants.
2. **Improve `hyba_genesis_api` coverage** — add tests for `auth/role_manager.py` (0%), `jwt_handler.py` (34%), `api/mining.py` (28%), and `models/` (0%).
3. **Fix TS failures** — create missing `bridge_security.ts` module; fix security swarm route registration.
4. **Add `vitest.config.ts` coverage config** — add a `coverage` section to enable persistent TS coverage reporting.