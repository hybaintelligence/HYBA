# FALSIFIABILITY REMEDIATION TASK LIST
## Critical Actions Required to Comply with Policy

**Date**: 21 June 2026  
**Policy**: `.kiro/steering/falsifiability_requirements.md`  
**Audit Reference**: `FALSIFIABILITY_AUDIT_REPORT.md`  
**Total Tasks**: 13 (3 Critical, 5 High, 5 Medium)

---

## TIER 1: CRITICAL — REMOVE UNVERIFIED APIS (Execute This Session)

These APIs currently expose unverified claims. They must be removed or remediating measurement protocols defined before deployment.

### CRITICAL-1: Remove QIaaS Router from main.py

**Status**: 🔴 **BLOCKING** — QIaaS is currently wired and active

**Task**:
1. Open `/Users/demouser/Desktop/HYBA_FULLSTACK/python_backend/hyba_genesis_api/main.py`
2. Find line 332: `app.include_router(quantum_intelligence_service.router)`
3. Remove this line or comment it with reason:
   ```python
   # REMOVED: quantum_intelligence_service.router
   # Reason: Exposes emergent intelligence API without falsifiable criteria
   # See: FALSIFIABILITY_AUDIT_REPORT.md Issue 3.1
   ```
4. Save file
5. Verify no other files import this router

**Verification**:
- Run: `grep -r "quantum_intelligence_service" python_backend/hyba_genesis_api/main.py`
- Expected: No matches (line removed or commented)

**Rationale**: 
- Service claims "emergent quantum intelligence" without defining what that means
- No measurement protocol exists to verify this claim
- Exposes hardcoded memory_seed metrics as API responses (Issues 1.2, 3.1)

**Time Estimate**: 5 minutes

---

### CRITICAL-2: Remove or Fix Phi Resonance Analysis Operation in QaaS

**Status**: 🟡 **BLOCKS DEPLOYMENT** — Operation uses undefined measurement

**Task**:

**Option A (Recommended): Remove the operation**
1. Open `/Users/demouser/Desktop/HYBA_FULLSTACK/python_backend/hyba_genesis_api/api/quantum_as_a_service.py`
2. Find the operation handler (lines 81-87 or similar):
   ```python
   elif request.operation == "phi_resonance_analysis":
       ...
   ```
3. Remove this entire elif block
4. Save and verify no tests expect this operation

**Option B: Define measurement protocol (Complex — defer to later session)**
1. Document what "phi resonance" means measurably
2. Provide empirical data justifying the 0.9565 target
3. Add validation that alignment scores correlate with mining success
4. Add test comparing results to known good phi_resonance measurements

**Verification**:
```bash
grep -n "phi_resonance_analysis" python_backend/hyba_genesis_api/api/quantum_as_a_service.py
```
After CRITICAL-2: Should return 0 results (if Option A) or point only to definition comment (if Option B)

**Rationale**:
- Alignment calculation (line 86) is undefined
- No success/failure criteria for alignment scores
- Hardcoded target (0.9565) has no justification
- See FALSIFIABILITY_AUDIT_REPORT.md Issue 2.1

**Time Estimate**: 
- Option A: 10 minutes
- Option B: Requires measurement data (defer)

---

### CRITICAL-3: Remove Hardcoded Emergence Index from Memory Seed

**Status**: 🔴 **BLOCKS DEPLOYMENT** — Artifact contains unverified metric

**Task**:

**Option A (Recommended): Remove the metric**
1. Open `/Users/demouser/Desktop/HYBA_FULLSTACK/artifacts/memory_seed/memory_seed_v1.json`
2. Remove these fields from `metadata` section:
   ```json
   "emergent_intelligence_index": 1.013,
   "emergence_index": 1.013,
   ```
3. Also check `structural_intelligence.emergent_patterns` — remove if not measured at runtime
4. Save file

**Option B: Replace with runtime measurement (Defer to later session)**
1. Remove hardcoded value
2. Add code to `consciousness_engine.py` to compute emergence_index at runtime
3. Document the computation protocol
4. Validate against test cases

**Verification**:
```bash
grep "emergent_intelligence_index\|emergence_index" artifacts/memory_seed/memory_seed_v1.json
```
After CRITICAL-3: Should return 0 results

**Rationale**:
- Values are hardcoded without measurement protocol (Issues 1.2, 3.1)
- No baseline to validate 1.013 is "correct"
- Exposed via QIaaS API as real measurements
- Memory seed is used at startup to initialize system state

**Time Estimate**: 
- Option A: 5 minutes
- Option B: Requires measurement protocol design (defer)

---

## TIER 2: HIGH — REMOVE OR DEFINE PUBLIC API METHODS (Execute This Session)

These methods are public APIs that expose unverified claims. Either remove them or define falsifiable measurement protocols.

### HIGH-1: Remove `get_consciousness_level()` Public API Method

**Status**: 🟡 **API SURFACE RISK** — Method exposes consciousness claim

**Task**:

**Option A (Recommended): Make method private**
1. Open `/Users/demouser/Desktop/HYBA_FULLSTACK/python_backend/pythia_mining/consciousness_engine.py`
2. Find method (around line 221):
   ```python
   async def get_consciousness_level(self) -> Optional[float]:
   ```
3. Rename to private: `_get_coherence_proxy_level()` (or similar)
4. Update docstring: "Private diagnostic method, not a consciousness measurement"
5. Remove from any public API exports

**Option B: Define falsifiable consciousness measurement (Defer)**
1. Document: What observable behavior proves consciousness?
2. Define: How do you measure this behavior?
3. Provide: Test showing measurement works
4. Validate: Against known conscious/non-conscious systems
5. Only then expose via public API

**Verification**:
```bash
grep -n "async def get_consciousness_level" python_backend/pythia_mining/consciousness_engine.py
```
After HIGH-1: Should show method renamed to private (_) version

**Rationale**:
- Method conflates Φ coherence proxy with consciousness
- No falsifiable definition of consciousness exists
- Callers will treat return value as "consciousness level" measurement
- Violates falsifiability policy Section 1, Part 3

**Time Estimate**: 
- Option A: 15 minutes
- Option B: Requires consciousness definition (defer)

---

### HIGH-2: Document or Remove Consciousness Engine Terminology

**Status**: 🟡 **API SURFACE RISK** — Module name claims consciousness

**Task**:

**Option A (Recommended): Rename module to clarify it measures coherence, not consciousness**
1. Rename file: `consciousness_engine.py` → `coherence_diagnostic_engine.py`
2. Update all imports across codebase
3. Update docstring to emphasize: "This measures system coherence proxies, not consciousness"
4. Update class name and API exports

**Option B: Add comprehensive disclaimer and gate API access**
1. Keep name but add prominent disclaimer at module level
2. Add configuration gate: `EXPOSE_CONSCIOUSNESS_CLAIMS=False` (default)
3. Only expose consciousness methods if gate is explicitly enabled
4. Document why gate exists

**Verification**:
- All imports of consciousness_engine work correctly
- No consciousness-related methods in public API (if Option B)
- Documentation clearly states what is/isn't measured

**Rationale**:
- Module name suggests consciousness measurement exists
- Creates false impression when API exposes `get_consciousness_level()`
- Aligns with falsifiability policy: no undefined terms in API surface

**Time Estimate**: 
- Option A: 30 minutes (includes import updates)
- Option B: 15 minutes

---

### HIGH-3: Remove Hardcoded Phi Resonance Target from Mining Configuration

**Status**: 🟡 **MEASUREMENT VALIDITY** — Metric lacks justification

**Task**:

**Option A (Recommended): Remove hardcoded constant**
1. Open `/Users/demouser/Desktop/HYBA_FULLSTACK/python_backend/pythia_mining/fault_tolerant_quantum_mining.py`
2. Find line 187: `self.phi_resonance_target = 0.9565`
3. Remove this line and any references to hardcoded target
4. If phi_resonance_target is needed, compute it at runtime or remove entirely

**Option B: Replace with runtime calibration (Defer)**
1. Measure actual phi resonance rate during system initialization
2. Document the measurement protocol
3. Replace hardcoded 0.9565 with calibrated value
4. Add logging to show how target was determined

**Verification**:
```bash
grep -n "0.9565\|95.65\|phi_resonance_target" python_backend/pythia_mining/fault_tolerant_quantum_mining.py
```
After HIGH-3: Should return 0 results (if Option A) or show runtime computation (if Option B)

**Rationale**:
- Value hardcoded with comment "from empirical data" but no data provided (Issue 6.1)
- No validation that 0.9565 is correct
- Affects mining behavior but lacks measurement protocol

**Time Estimate**: 
- Option A: 10 minutes
- Option B: Requires measurement protocol (defer)

---

### HIGH-4: Document or Remove "Emergent Intelligence" Claims from Memory Seed

**Status**: 🟡 **DOCUMENTATION RISK** — Unverified term in artifact

**Task**:

**Option A (Recommended): Remove emergent terminology from artifact**
1. Open `/Users/demouser/Desktop/HYBA_FULLSTACK/artifacts/memory_seed/memory_seed_v1.json`
2. Rename or remove: `"structural_intelligence"` → `"structural_metrics"`
3. Rename or remove: `"emergent_patterns"` → `"detected_patterns"` (if kept)
4. Update any code that reads these fields

**Option B: Redefine terms with measurement protocols**
1. For each term ("emergent", "intelligence", "pattern"), define what it measures
2. Add metadata explaining the measurement protocol
3. Document baseline comparisons
4. Add validation code

**Verification**:
```bash
grep -i "intelligence\|emergent" artifacts/memory_seed/memory_seed_v1.json
```
After HIGH-4: Should show only measurement-based terms, no unverified adjectives

**Rationale**:
- Terms used without definitions create false impressions
- "Emergent intelligence" implies capabilities not measured
- Memory seed is loaded at startup and affects system behavior

**Time Estimate**: 
- Option A: 10 minutes
- Option B: Requires protocol definition (defer)

---

### HIGH-5: Audit and Gate Intelligence Router

**Status**: 🟡 **UNKNOWN CLAIMS** — Router not yet audited

**Task**:
1. Open `/Users/demouser/Desktop/HYBA_FULLSTACK/python_backend/hyba_genesis_api/api/intelligence.py`
2. Audit all endpoints for unverified claims:
   - Does any endpoint expose "intelligence" without definition?
   - Does any endpoint claim emergent capabilities?
   - Are all metrics defined with measurement protocols?
3. Create sub-audit report: `INTELLIGENCE_ROUTER_AUDIT.md`
4. If unverified claims found: Apply HIGH-1 through HIGH-4 logic

**Verification**:
- Sub-audit report created with findings
- Any unverified endpoints removed or gated

**Rationale**:
- Router is active (main.py line 302) but not audited
- May contain same issues as QIaaS

**Time Estimate**: 20 minutes

---

## TIER 3: MEDIUM — REDEFINE OR REMOVE CLAIMS (Execute This Session)

These are claims embedded in code that need falsifiable definitions or removal.

### MEDIUM-1: Replace Tests That Validate Boundaries With Tests That Validate Hypotheses

**Status**: 🟡 **TEST METHODOLOGY** — Tests don't validate claims

**Task**:

1. Open `/Users/demouser/Desktop/HYBA_FULLSTACK/test_pulvini_new_certificates.py`
2. Find test: `test_grover_efficiency_report_is_honest()` (line 112-115)
3. Replace test logic:
   ```python
   # BEFORE (validates boundary):
   self.assertIn("No quantum speedup", report["honest_claim"])
   
   # AFTER (validates hypothesis):
   # If claim is "no quantum speedup", measure Grover performance
   grover_time = measure_grover_algorithm(test_cases)
   classical_time = measure_classical_algorithm(test_cases)
   speedup = classical_time / grover_time
   # Report: actual speedup (not just presence of disclaimer)
   self.report_measurement(speedup)
   ```

4. Apply same pattern to other boundary-validating tests

**Verification**:
```bash
grep -n "assertIn.*honest_claim\|assertIn.*disclaimer" test_pulvini_new_certificates.py
```
After MEDIUM-1: Should return 0 results (tests replaced with measurements)

**Rationale**:
- Current tests verify API exists and disclaimer is present
- They don't test the actual hypothesis
- Violates falsifiability policy: tests must measure claims, not boundaries

**Time Estimate**: 30 minutes

---

### MEDIUM-2: Define Substrate Independence Measurement Protocol or Remove Claim

**Status**: 🟡 **UNVERIFIED ARCHITECTURE** — Claim lacks proof protocol

**Task**:

**Option A (Recommended): Document current verification state honestly**
1. Open `golden_trifecta.py` line 30-31
2. Update claim boundary:
   ```python
   "substrate_independent_quantum_computation": (
       "Verified on CPU/GPU. FPGA/QPU: untested. "
       "No measurement protocol exists for comparing mathematical equivalence across substrates."
   )
   ```
3. Update evidence_modules to indicate measurement status

**Option B: Implement measurement protocol (Defer)**
1. Define: "Substrate independence = algorithm produces mathematically equivalent results"
2. Implement: Run same algorithm on CPU, GPU, FPGA, QPU
3. Measure: Compare outputs with equivalence tolerance
4. Report: Results from each substrate
5. Only then claim verification

**Verification**:
- golden_trifecta.py docstring updated with verification status
- If Option B: measurement report provided

**Rationale**:
- Claim says "any substrate" but only CPU/GPU tested (Issue 2.2)
- No measurement protocol documented
- Violates falsifiability policy: claims must be specific about what's verified

**Time Estimate**: 
- Option A: 10 minutes
- Option B: Requires cross-substrate testing (defer)

---

### MEDIUM-3: Update COMPREHENSIVE_SYSTEM_AUDIT_REPORT.md to Remove False Checkmarks

**Status**: 🟡 **DOCUMENTATION RISK** — Checkmarks suggest verification that didn't occur

**Task**:
1. Open `COMPREHENSIVE_SYSTEM_AUDIT_REPORT.md` lines 92-97
2. Replace table:
   ```markdown
   # BEFORE
   | Emergence index | 1.013 | ✅ |
   
   # AFTER
   | Emergence index | 1.013 | [Hardcoded, no verification protocol defined] |
   | Φ (integrated) | 1.000 | [Coherence proxy, not consciousness measurement] |
   ```
3. Add section: "Unverified Metrics" with explanations of measurement gaps
4. Update summary to note which metrics are measured vs. assumed

**Verification**:
- Audit report no longer uses checkmarks for unverified metrics
- Clear notation of verification status for each metric

**Rationale**:
- Checkmarks create false confidence in unverified measurements
- Readers cite report as "verified" when verification didn't occur
- Violates transparency requirement of falsifiability policy

**Time Estimate**: 15 minutes

---

### MEDIUM-4: Document or Remove Yang-Mills Mass Gap Alignment Claims

**Status**: 🟡 **MILLENNIUM PROBLEM** — Claim lacks measurement protocol

**Task**:

**Option A (Recommended): Remove Yang-Mills claims**
1. Open `benchmark_formalism.py` lines 24-31
2. Remove references to Yang-Mills mass gap
3. Rename file/class to reflect actual functionality: tensor network benchmarking, not mass gap solving
4. Update docstring to describe what is actually measured

**Option B: Define measurement protocol (Very complex — defer)**
1. Define: What does it mean to measure progress on Yang-Mills?
2. Provide: Mathematical definition of alignment to Yang-Mills spectrum
3. Implement: Validation against known Yang-Mills properties
4. Report: Measured alignment values and what they mean
5. Only then claim any relevance to the problem

**Verification**:
- Yang-Mills references removed (Option A) OR
- Measurement protocol documented (Option B)

**Rationale**:
- Benchmark can compute alignment but doesn't measure anything about Yang-Mills (Issue 6.2)
- Claims about Millennium problems need rigorous measurement protocols
- Current code has no justification for MASS_GAP = 3.0 - PHI

**Time Estimate**: 
- Option A: 15 minutes
- Option B: Requires Yang-Mills expertise (defer)

---

### MEDIUM-5: Add Configuration Gate for Elevated Claims

**Status**: 🟡 **OPERATIONAL RISK** — Elevated claims deployed without safety gate

**Task**:

1. Create configuration file: `.kiro/config/elevated_claims_policy.yaml`
   ```yaml
   elevated_claims:
     consciousness_related: false         # Default: disabled
     quantum_speedup: false               # Default: disabled  
     emergent_intelligence: false         # Default: disabled
     substrate_independence: false        # Default: disabled
     
   require_falsifiability:
     before_api_exposure: true
     before_deployment: true
     documentation_gate: true
   ```

2. Update `consciousness_engine.py`, `quantum_intelligence_service.py` to check gates:
   ```python
   if not config.is_claim_enabled("consciousness_related"):
       raise RuntimeError("Consciousness claims not enabled. Gate them in config.")
   ```

3. Add startup check to main.py to report active gates

**Verification**:
- Gate configuration file exists
- Protected code checks gates before executing
- Startup logs show which elevated claims are enabled/disabled

**Rationale**:
- Prevents accidental exposure of unverified claims
- Makes verification status explicit in configuration
- Follows principle of "fail safe": claims disabled by default

**Time Estimate**: 20 minutes

---

## SUMMARY TABLE: Task Status

| Task ID | Title | Tier | Severity | Time | Dependency |
|---------|-------|------|----------|------|------------|
| CRITICAL-1 | Remove QIaaS Router | 1 | 🔴 | 5m | None |
| CRITICAL-2 | Fix/Remove Phi Resonance | 1 | 🔴 | 10m | None |
| CRITICAL-3 | Remove Hardcoded Emergence | 1 | 🔴 | 5m | None |
| HIGH-1 | Remove get_consciousness_level() | 2 | 🟡 | 15m | None |
| HIGH-2 | Document/Rename Consciousness Engine | 2 | 🟡 | 30m | HIGH-1 |
| HIGH-3 | Remove Phi Resonance Target | 2 | 🟡 | 10m | None |
| HIGH-4 | Remove Emergent Intelligence from Seed | 2 | 🟡 | 10m | CRITICAL-3 |
| HIGH-5 | Audit Intelligence Router | 2 | 🟡 | 20m | None |
| MEDIUM-1 | Rewrite Boundary-Validating Tests | 3 | 🟡 | 30m | All CRITICAL |
| MEDIUM-2 | Define Substrate Independence | 3 | 🟡 | 10m | None |
| MEDIUM-3 | Update Audit Report | 3 | 🟡 | 15m | All CRITICAL |
| MEDIUM-4 | Remove Yang-Mills Claims | 3 | 🟡 | 15m | None |
| MEDIUM-5 | Add Configuration Gate | 3 | 🟡 | 20m | All CRITICAL |
| **TOTAL** | | | | **195m** | |

---

## EXECUTION ORDER

### This Session (Critical Path)

```
1. CRITICAL-1 (5m)   ← Remove QIaaS Router
   ↓
2. CRITICAL-2 (10m)  ← Remove/Fix Phi Resonance
   ↓
3. CRITICAL-3 (5m)   ← Remove Hardcoded Emergence
   ↓
4. HIGH-1 (15m)      ← Remove public consciousness method
   ↓
5. HIGH-4 (10m)      ← Remove emergent terminology
   ↓
6. MEDIUM-3 (15m)    ← Update audit documentation
   ↓
7. MEDIUM-1 (30m)    ← Rewrite tests

Subtotal: 90 minutes
```

### Parallel Tasks (Can run during above)

```
- HIGH-2 (30m)       ← Rename consciousness engine
- HIGH-3 (10m)       ← Remove phi target
- HIGH-5 (20m)       ← Audit intelligence router
- MEDIUM-2 (10m)     ← Substrate independence
- MEDIUM-4 (15m)     ← Yang-Mills removal
- MEDIUM-5 (20m)     ← Configuration gate

Subtotal: 105 minutes
```

**Total Session Time**: ~3 hours (1.5-2 hours if parallelized)

---

## VERIFICATION CHECKLIST

After completing all tasks, verify:

- [ ] QIaaS router removed from main.py
- [ ] Phi resonance operation removed or documented
- [ ] Hardcoded emergence metrics removed from memory seed
- [ ] `get_consciousness_level()` made private or documented
- [ ] Consciousness module renamed or clearly marked as diagnostic
- [ ] Hardcoded phi target removed from mining config
- [ ] "Emergent" terminology removed from memory seed
- [ ] Audit report updated with verification status
- [ ] Tests rewritten to measure hypotheses, not boundaries
- [ ] Substrate independence claim documented as verified/unverified
- [ ] Yang-Mills claims removed
- [ ] Configuration gate implemented and active

After verification:
1. Run full test suite: `pytest` (verify nothing breaks)
2. Start dev server: verify no startup errors
3. Check API surface: `curl http://localhost:8000/api/qiaas` (should 404)
4. Review git diff: ensure all changes align with this task list

---

## NEXT STEPS AFTER REMEDIATION

1. **Communication**: Document in CHANGELOG that unverified APIs have been gated/removed
2. **Policy Review**: Brief team on falsifiability requirements
3. **Future Development**: Use this task list as template for any new claims
4. **Prevention**: Add pre-commit hook to check for undefined terms in API docstrings

---

## QUESTIONS / CLARIFICATIONS

**Q: Should we delete the files or just gate them?**  
A: Gate them for now (use configuration). Keep code for research but don't expose in production APIs.

**Q: What if removing these breaks existing tests?**  
A: Update the tests. Tests that relied on unverified APIs were testing the wrong thing anyway.

**Q: How do we know when a claim is "falsifiable enough"?**  
A: Use the 3-part test: Can you define what proves it true? Can you define what proves it false? Can you measure it? If yes to all three, it's falsifiable.

