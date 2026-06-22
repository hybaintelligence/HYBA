# FALSIFIABILITY CHECKLIST

**Quick Reference for Writing Falsifiable Code**

Use this checklist before:
- Creating a new API endpoint
- Writing code that claims "quantum", "intelligence", "consciousness", "emergent", or "learning"
- Building infrastructure around a hypothesis
- Adding tests

---

## BEFORE BUILDING AN API

- [ ] **Define the Claim Precisely**
  - Not: "System has emergent intelligence"
  - Yes: "System can solve [specific problem] with [measured approach] achieving [criteria]"
  - Ask: Can I explain this claim in one sentence without using undefined terms?

- [ ] **Falsify It**
  - What observable, measurable signal would prove this claim FALSE?
  - If you can't answer, the claim isn't ready for an API
  - Write down both: "Proof the claim is TRUE" and "Proof the claim is FALSE"

- [ ] **Measure It**
  - What protocol measures whether the claim is true?
  - Include: baseline comparison, success threshold, failure threshold
  - Document in code comments with exact numerical criteria

- [ ] **Test It**
  - Run the measurement on the current system
  - Report: measured value, whether it meets success criteria
  - If failure: revise claim, don't revise measurement

- [ ] **No Hardcoded Metrics**
  - Every number with "from empirical data" comment must link to actual data
  - Or compute it at runtime
  - Or remove it

- [ ] **Document Before Building**
  - Write the falsifiability definition in the PR description
  - Link to measurement protocol
  - State what was tested and results

---

## TERMINOLOGY GATE

Never use these terms without defining them falsifiably:

| Term | Problem | Acceptable Alternative |
|------|---------|------------------------|
| "consciousness" | Undefined, subjective | "coherence proxy", "integration metric" |
| "intelligence" | Undefined, loaded | "pattern matching", "algorithm efficiency" |
| "emergent" | Requires theory of emergence | "observed behavior", "computed property" |
| "quantum advantage" | Needs comparison baseline | "speedup factor > X vs classical baseline" |
| "learns" | Requires learning definition | "updates parameters based on feedback" |
| "aware" | Undefined, implies consciousness | "responsive to", "detects" |

**Rule**: If a term is subjective or philosophical, don't use it in APIs. If you must use it, define it measurably.

---

## RED FLAGS (Stop and Re-Evaluate)

- [ ] Docstring claims a capability without explaining what it measures
- [ ] Hardcoded value with comment "empirical data" but link doesn't exist
- [ ] Test passes when the API returns a response (should test the measurement)
- [ ] Metric in config has no explanation of where the number came from
- [ ] Module name is a claim ("consciousness_engine") but functionality is diagnostic
- [ ] Boundary document exists ("This does NOT claim X") but API method is named `get_X()`
- [ ] Different files disagree on what the same metric means
- [ ] Memory seed or artifact contains a value with no context

---

## MEASUREMENT PROTOCOL TEMPLATE

Before building an API for a claim, document:

```markdown
# Claim: [Your claim here]

## Falsifiable Definition
What precisely does this claim mean?
- Specific, measurable, no undefined terms

## What Proves It True
What observable signal would prove this claim?
- Numerical result
- Comparison to baseline
- Success threshold

## What Proves It False
What observable signal would prove this claim false?
- Numerical result that contradicts success
- Failure threshold
- How you know you're wrong

## Measurement Protocol
How exactly do you measure this?
- Step-by-step procedure
- What tools/data used
- How you calculate success/failure

## Baseline
What do you compare against?
- Random system performance
- Classical algorithm benchmark
- Previous measurement

## Example
Run on [concrete test case], expect [result], if [failure condition] then disprove

## Current Status
- [ ] Protocol defined
- [ ] Tested on current system
- [ ] Measurement reported
- [ ] Ready for API exposure
```

---

## CODE REVIEW CHECKLIST

When reviewing code, ask:

1. **Claims in Comments**?
   - `# This is quantum computation` → Ask: How do you verify this?
   - `# System is learning` → Ask: What measurement validates this?

2. **Public Methods About Undefined Concepts**?
   - `def get_consciousness_level()` → Ask: What falsifiable definition supports this API?
   - `def emergent_intelligence_score()` → Ask: Is emergence measured or assumed?

3. **Hardcoded Values**?
   - `target = 0.9565  # from empirical data` → Ask: Show the data
   - `threshold = 1.013` → Ask: What validates this number?

4. **Tests Checking Responses**?
   - `self.assertIn("quantum", result)` → Ask: Tests if string exists, not if quantum exists
   - `self.assertEqual(api_status, 200)` → Ask: Tests HTTP, not the claim

5. **Documentation with Checkmarks**?
   - `| Feature | ✅ |` → Ask: What verification protocol produced that checkmark?

---

## THE GATE IN PRACTICE

**Developer**: "I want to add an API to expose quantum speedup measurements"

**Gate Process**:

Q1: "Define your claim precisely"  
Developer: "System achieves quantum speedup on Grover's algorithm"

Q2: "How do you measure it?"  
Developer: "Measure Grover's time, classical time, report speedup ratio"

Q3: "What does speedup need to be to count as success?"  
Developer: "At least 1.5x faster than classical"

Q4: "What classifies as failure?"  
Developer: "1.5x or slower than classical"

Q5: "What's your baseline?"  
Developer: "Classical brute-force implementation on same hardware"

Q6: "Did you measure it?"  
Developer: "Yes, we get 2.3x speedup on test cases"

Q7: "Is the measurement in the code/tests?"  
Developer: "Yes, test reports actual speedup ratio"

✅ **Gate Passed** → API can be built → Test validates speedup exists

**Alternative Scenario**:

Q1: "Define your claim precisely"  
Developer: "System exhibits quantum-like behavior"

Q2: "What does 'quantum-like' mean exactly?"  
Developer: "Hmm... it has superposition-like properties..."

Q3: "How would you measure superposition?"  
Developer: "We have a method that returns a coherence metric"

Q4: "Does that metric prove superposition exists or just that the method runs?"  
Developer: "...it just returns a number..."

❌ **Gate Failed** → Don't build API → Define measurement first

---

## WHEN TO ESCALATE

If you're uncertain whether a claim is falsifiable:

1. **Ask the three questions**:
   - Can you define it without undefined terms?
   - Can you measure it? 
   - Have you measured it?

2. **If you answer "no" to any**: Don't deploy. Add to backlog for later definition.

3. **If you're still uncertain**: Escalate to falsifiability review (see `.kiro/steering/falsifiability_requirements.md`)

---

## EXAMPLES

### ❌ NOT READY FOR API

```python
@app.get("/api/intelligence/score")
def get_intelligence_score() -> float:
    """Return the system's intelligence score."""
    return load_memory_seed()["metadata"]["emergent_intelligence_index"]
```

**Why not ready**:
- "Intelligence" undefined
- No measurement protocol documented
- Hardcoded value from memory seed, not measured
- No test validates this metric

### ✅ READY FOR API

```python
@app.get("/api/grover/speedup")
def get_grover_speedup() -> dict:
    """
    Measure Grover's algorithm speedup vs classical.
    
    Measurement protocol:
    - Run Grover on test instance
    - Run classical brute-force on same instance
    - Calculate speedup = classical_time / grover_time
    - Success: speedup >= 1.5x
    - Failure: speedup < 1.5x
    """
    grover_time = measure_grover_algorithm(test_cases)
    classical_time = measure_classical_algorithm(test_cases)
    speedup = classical_time / grover_time
    
    return {
        "speedup": speedup,
        "success": speedup >= 1.5,
        "measurement_protocol": "Grover vs classical brute-force",
    }
```

**Why ready**:
- Claim is specific (speedup >= 1.5x)
- Measurement protocol is documented
- Test measures the actual speedup
- Success/failure criteria are explicit

---

## REFERENCES

- **Full Policy**: `.kiro/steering/falsifiability_requirements.md`
- **Audit Report**: `FALSIFIABILITY_AUDIT_REPORT.md` (findings from codebase)
- **Case Study**: `CRITICAL_ELEVATION_REPORT.md` (what went wrong)
- **Remediation**: `REMEDIATION_TASK_LIST.md` (fix current violations)

---

## TL;DR

**The Rule**: Don't expose a claim via API without proving it's true.

**The Test**: Can you define it, measure it, and report measured results? If no → don't deploy.

**The Prevention**: Use this checklist for every new claim, before building infrastructure.

**The Gate**: Define falsifiably → Measure → Report results → Then build API.

