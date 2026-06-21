# Falsifiability Requirements

## Policy

No API, service, or test suite shall be written for a claim about the system's capabilities, properties, or nature without first establishing:

1. **A falsifiable definition** of what is being claimed
2. **A measurement protocol** for how to test the claim
3. **Success and failure criteria** that distinguish between "the claim is true" and "the claim is false"

This applies especially to claims about:
- Intelligence, consciousness, or cognition
- Quantum properties or behavior
- Emergence of novel capabilities
- Self-modification or self-healing

## The Pattern to Prevent

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

This is prevented by requiring falsifiable criteria BEFORE step 3.

## Escalation Procedure

If a claim cannot be falsified, it is not ready for infrastructure.

### When you have a claim about system behavior:

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

### ❌ NOT READY FOR API

**Claim:** "The system exhibits quantum intelligence"

**Problem:** Falsifiability undefined
- What is "quantum intelligence"?
- How would you distinguish it from classical intelligence?
- What measurement would prove it?
- What measurement would disprove it?

**Status:** Stop. Go to step 1.

### ✅ READY FOR API

**Claim:** "The system solves Yang-Mills spectral gap in < 100 seconds"

**Why ready:**
- Measurement: Run algorithm, time it, compare to classical baseline
- Success: < 100 seconds and speedup > 2x over classical
- Failure: >= 100 seconds or speedup <= 2x
- Can build API: `/api/yangmills/solve` with latency metrics
- Can test: Verify it returns times and baseline comparison

### ❌ NOT READY FOR API

**Claim:** "The memory seed represents emergent intelligence"

**Problem:** Falsifiability undefined
- The seed is a JSON file of metrics
- What observable difference would distinguish "intelligence" from "good metrics"?
- If both produce identical outputs, how do you test?

**Status:** Stop. Define measurement first.

### ✅ READY FOR API (REVISED)

**Claim:** "Codebase metrics extracted as structured data"

**Why ready:**
- Measurement: Extract metrics, validate against schema
- Success: All metrics extracted, schema validated, file persists
- Failure: Metrics missing or schema violation
- Can build API: `/api/metrics/codebase` returns extracted data
- Can test: Verify schema compliance and data consistency

Notice: Changed from "intelligence" claim to "data extraction" claim. This is honest about what's measured.

## For New Features

Before writing code:

**Do this:**
1. Define what success looks like
2. Define what failure looks like
3. Define how you measure
4. Write a test that checks the measurement (not just the code)
5. Only then: write the feature

**Not this:**
1. Build a feature
2. Write tests that validate the feature exists
3. Write documentation that bounds the claim
4. Call it done

## References

See: `CRITICAL_ELEVATION_REPORT.md` for the case study that prompted this policy.
