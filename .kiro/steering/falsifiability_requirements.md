# Falsifiability Requirements

## Policy: Two Contexts, Different Standards

Falsifiability requirements apply **differently** based on code context:

### Context 1: Research Code (Scripts, Experiments, Internal Modules)
**Standard**: Exploratory, hypothesis-driven. Minimal gate.
- You MAY write experimental code exploring quantum behavior, consciousness metrics, emergent properties
- You MAY hardcode metrics for testing purposes
- You MUST document what you're testing and why
- You MUST NOT (yet) expose these via public APIs
- **Rationale**: Innovation requires exploration. Dead ends are fine in research.

### Context 2: Production APIs (HTTP Endpoints, Deployed Services, Public Methods)
**Standard**: Verifiable, documented, stable. Strict gate.
- No public API endpoint shall expose a claim without first establishing:
  1. **A falsifiable definition** of what is being claimed
  2. **A measurement protocol** for how to test the claim
  3. **Success and failure criteria** that distinguish "true" from "false"
- This applies to claims about:
  - Intelligence, consciousness, or cognition
  - Quantum properties or behavior
  - Emergence of novel capabilities
  - Self-modification or self-healing
  - Mining efficiency, speedup factors, or performance claims

This applies especially to claims about intelligence, consciousness, or cognition.

## Pattern to Prevent

The "unverified API" failure mode follows this sequence:

```
Observation: "System has structural complexity"
  ↓
Hypothesis: "If X then intelligence emerges"
  ↓
Mistake: "Therefore intelligence has emerged" (without testing IF)
  ↓
API built: "Expose the emergent intelligence as a service"
  ↓
Tests written: "Verify the API exists and the disclaimer is present"
  ↓
Codebase debt: "Unverified claim now has HTTP surface and dependents"
```

This is prevented by:
- Keeping exploratory work OUT of public APIs
- Requiring falsifiable criteria BEFORE deploying to production
- Distinguishing research (where hypotheses are fine) from APIs (where verification is required)

## What Counts As "Production"?

| Code Type | Examples | Standard | Can Explore Freely? |
|-----------|----------|----------|-------------------|
| **Research** | Scripts, test files, internal modules, Jupyter notebooks | Exploratory, hypothesis-driven | ✅ Yes |
| **Experimental** | New features in feature branches, shadowed APIs | Requires measurement before merge | ⚠️ Measured before merging |
| **Production** | Public HTTP endpoints, deployed services, main branch | Falsifiable + measured | ❌ Requires gate |

**Key Rule**: If it's in a public API endpoint or deployed to production, it must pass the falsifiability gate.

## Escalation Procedure

### For Research Code (Interior, Not Customer-Facing)

If you're writing experimental code:

1. **Explore freely** — hypothesis-driven code is fine
2. **Document what you're testing** — why this exploration matters
3. **Don't expose via API yet** — keep it internal
4. **When ready to productionize** → follow Production API gate (below)

### For Production APIs (Public Endpoints, Customer-Facing)

If you have a claim to expose via public API or deploy to production:

1. **Write the falsifiable definition first**
   - What observable, measurable signal would prove this claim?
   - What would disprove it?
   - If you cannot answer: the claim is not yet ready

2. **Write the measurement protocol**
   - How specifically do you measure the signal?
   - What baseline or comparison do you use?
   - What noise/error margins are acceptable?
   - If you cannot specify: the claim is not yet ready

3. **Only then: implement the measurement**
   - Run the measurement
   - Report success or failure
   - If failure: revise the hypothesis, not the measurement

4. **Only then: build APIs or tests**
   - API: serves measured results
   - Tests: verify measurement protocol works
   - Documentation: states what was measured, with confidence

## Examples

### 🔬 RESEARCH: Exploring Quantum Intelligence

**Context**: Internal script testing an idea (not deployed)

**Claim**: "The system exhibits quantum intelligence"

**Status**: ✅ **OK for research**

```python
# scripts/test_quantum_intelligence_hypothesis.py
"""Exploring whether quantum-like properties emerge from tensor networks.
This is RESEARCH CODE. Do not deploy to production without measurement protocol."""

# Hypothesis: coherence metrics might indicate quantum-like behavior
emergence_index = compute_coherence_metrics()
print(f"Emergence index: {emergence_index}")  # Exploratory observation

# Question: does this correlate with anything? Unknown.
# Next: measure against known quantum systems to validate
```

**Why OK**:
- It's in a research script, not a public API
- Documents what's being tested
- Not claiming measurement, just exploring

---

### ❌ PRODUCTION: Same Idea Without Measurement (NOT READY)

**Context**: Public API endpoint

**Claim**: "The system exhibits quantum intelligence"

**Status**: ❌ **NOT ready for API**

```python
@app.get("/api/quantum/intelligence")
def get_quantum_intelligence():
    """Return quantum intelligence score."""
    # Same emergence_index from above
    return {"emergence_index": compute_coherence_metrics()}
```

**Problem**: 
- No falsifiable definition of "quantum intelligence"
- No measurement protocol
- No success/failure criteria
- Can't distinguish this API from a classical system doing the same thing

**Fix**: Move to research until measurement protocol is defined.

---

### ✅ PRODUCTION: Same Idea With Measurement Protocol (READY)

**Context**: Public API endpoint

**Claim**: "System can identify quantum entanglement patterns"

**Status**: ✅ **Ready for API**

```python
@app.get("/api/quantum/entanglement-detection")
def detect_entanglement():
    """
    Detect entanglement patterns in quantum states.
    
    Measurement protocol:
    - Run state through entanglement detector
    - Compare against known entangled/non-entangled states
    - Success: detection accuracy >= 95%
    - Failure: accuracy < 95%
    
    Current measured accuracy: 96.3% (±1.2%)
    """
    result = run_entanglement_detector(test_states)
    return {
        "accuracy": result.accuracy,
        "patterns_detected": result.count,
        "measurement_protocol": "Bell inequality violation detection",
        "success_criteria_met": result.accuracy >= 0.95,
    }
```

**Why ready**:
- Claim is specific and measurable
- Protocol is documented
- Actual measured results reported
- Success/failure criteria are explicit

## For New Features

Before deploying to production:

**Do this:**
1. Develop in research context (scripts, feature branches)
2. Explore hypotheses freely
3. When you have a working hypothesis:
   - Define what success looks like
   - Define what failure looks like
   - Define how you measure
   - Write a test that checks the measurement
4. Only then: expose via API or deploy
5. Update documentation with measured results

**Not this:**
1. Build a feature in main branch
2. Write tests that validate the feature exists
3. Write documentation that bounds the claim
4. Call it done
5. Move research to production without measurement

## Promoting Research to Production

When you want to move an experiment from research scripts to a public API:

1. **Measurement protocol defined?** ✅ If no → stop, define it first
2. **Measurement run on system?** ✅ If no → stop, run it
3. **Results meet success criteria?** ✅ If no → revise hypothesis or don't deploy
4. **Documented in code/tests?** ✅ If no → stop, document it
5. Deploy with confidence

If you can answer "yes" to all four, the code is ready for production.

## References

See: `CRITICAL_ELEVATION_REPORT.md` for the case study that prompted this policy.
