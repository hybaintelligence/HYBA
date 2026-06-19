# Adaptive Systems Capability Registry

Current as of: 2026-06-19  
Owner: HYBA Chairman  
Repository: HYBA_FULLSTACK  
Status: Canonical capability registry for controlled adaptive-systems programme

## Bottom line

This canonical registry converts the controlled adaptive-systems investigation into capability IDs that can be tested, documented, preserved, and reviewed.

Each capability must name evidence files, a local test command, a current supported claim, a known gap, a claim boundary, and a status. No capability should advance from observation to institutional claim unless the registry entry, test command, artifact, supported claim, known gap, and claim boundary are present.

## Capability status levels

| Status | Meaning |
| --- | --- |
| `implemented` | Code or test instrument exists. |
| `tested` | Test command exists and is expected to exercise the capability. |
| `artifact-backed` | A generated or preserved artifact records the measurement. |
| `baseline-needed` | More negative controls or baseline comparisons are required. |
| `runtime-needed` | Static/proxy evidence exists, but runtime measurement is still required. |
| `external-review-needed` | Internal evidence exists, but independent review is required before broad use. |

## Registry

### ADAPT-FEEDBACK-001 — Feedback-loop detection

**Capability:** Detect controlled feedback patterns in Python systems, including state feedback, update methods, and accumulation loops.

**Evidence files:**

- `tests/test_adaptive_behavior_deep_analysis.py`
- `tests/test_adaptive_science_claim_gate.py`
- `artifacts/adaptive_behavior_analysis.json` when generated

**Test command:**

```bash
python -m pytest tests/test_adaptive_behavior_deep_analysis.py tests/test_adaptive_science_claim_gate.py -q
```

**Current supported claim:**

HYBA_FULLSTACK has an instrument that can detect controlled feedback/update patterns in source files and synthetic controls.

**Known gap:**

Feedback detection alone does not prove learning or open-ended improvement. Runtime probes and baseline comparisons are still required.

**Claim boundary:**

Use as evidence of feedback instrumentation and feedback-pattern presence only.

**Status:** `implemented`, `tested`, `artifact-backed`, `baseline-needed`, `runtime-needed`

---

### ADAPT-MEMORY-002 — Memory and state accumulation detection

**Capability:** Detect memory-like structures, append/update patterns, state histories, and retained state surfaces.

**Evidence files:**

- `tests/test_adaptive_behavior_deep_analysis.py`
- `tests/test_adaptive_science_claim_gate.py`
- `artifacts/adaptive_behavior_analysis.json` when generated

**Test command:**

```bash
python -m pytest tests/test_adaptive_behavior_deep_analysis.py tests/test_adaptive_science_claim_gate.py -q
```

**Current supported claim:**

HYBA_FULLSTACK has an instrument that can detect memory/state accumulation patterns and distinguish them from threshold/optimisation patterns in controlled examples.

**Known gap:**

State accumulation is not the same as semantic memory, learning, or understanding. Longitudinal runtime tests are required.

**Claim boundary:**

Use as evidence of retained state and memory-pattern instrumentation only.

**Status:** `implemented`, `tested`, `artifact-backed`, `runtime-needed`

---

### ADAPT-OPTIMISE-003 — Parameter and threshold optimisation detection

**Capability:** Detect threshold, parameter, and configuration update patterns that may indicate adaptive control.

**Evidence files:**

- `tests/test_adaptive_behavior_deep_analysis.py`
- `tests/test_adaptive_science_claim_gate.py`
- `artifacts/adaptive_behavior_analysis.json` when generated

**Test command:**

```bash
python -m pytest tests/test_adaptive_behavior_deep_analysis.py tests/test_adaptive_science_claim_gate.py -q
```

**Current supported claim:**

HYBA_FULLSTACK has an instrument that can detect parameter or threshold update patterns in source files and synthetic controls.

**Known gap:**

Parameter updates must be compared against no-op, random, and fixed-threshold baselines before being treated as effective adaptation.

**Claim boundary:**

Use as evidence of optimisation-pattern instrumentation only.

**Status:** `implemented`, `tested`, `baseline-needed`, `runtime-needed`

---

### ADAPT-RUNTIME-004 — PULVINI autonomic recovery and redistribution

**Capability:** Exercise runtime recovery / redistribution behaviour under controlled failure conditions.

**Evidence files:**

- `tests/test_pulvini_autonomics.py`

**Test command:**

```bash
python -m pytest tests/test_pulvini_autonomics.py -q
```

**Current supported claim:**

HYBA_FULLSTACK contains tests for controlled runtime recovery, redistribution, and invariant preservation in the PULVINI autonomic surface.

**Known gap:**

The tests must be preserved with runtime telemetry, repeated-session artifacts, and negative controls before external use.

**Claim boundary:**

Use as evidence of controlled autonomic recovery testing within the declared software surface.

**Status:** `implemented`, `tested`, `runtime-needed`, `external-review-needed`

---

### ADAPT-INTEGRATION-005 — Integration proxy measurement

**Capability:** Measure software integration proxies and compare them across structures.

**Evidence files:**

- `tests/test_emergent_complexity_iit.py`
- `artifacts/emergent_complexity_analysis.json` when generated

**Test command:**

```bash
python -m pytest tests/test_emergent_complexity_iit.py -q
```

**Current supported claim:**

HYBA_FULLSTACK has integration-style proxy tests and artifact outputs that can be preserved for before/after comparison.

**Known gap:**

Proxy measures must be explicitly labelled, formula-defined, baseline-compared, and separated from runtime causal behaviour.

**Claim boundary:**

Use as evidence of software integration proxy measurement only.

**Status:** `implemented`, `tested`, `artifact-backed`, `baseline-needed`, `external-review-needed`

---

### ADAPT-CLAIM-GATE-006 — Evidence and claim-boundary gate

**Capability:** Ensure adaptive-system artifacts and programme documents preserve proof-ladder and claim-boundary metadata.

**Evidence files:**

- `tests/test_adaptive_science_claim_gate.py`
- `docs/governance/CONTROLLED_ADAPTIVE_SYSTEMS_SCIENCE_PROGRAM.md`
- `docs/ADAPTIVE_SYSTEMS_CAPABILITY_REGISTRY.md`
- `docs/technical-reports/ADAPTIVE_SYSTEMS_CAPABILITY_REGISTRY.md`

**Test command:**

```bash
python -m pytest tests/test_adaptive_science_claim_gate.py -q
```

**Current supported claim:**

HYBA_FULLSTACK has a proof-gate test surface that checks the scientific programme and adaptive artifacts for evidence-boundary discipline.

**Known gap:**

The gate should be expanded to validate generated scientific packets once those artifacts exist.

**Claim boundary:**

Use as evidence of internal claim-control instrumentation only.

**Status:** `implemented`, `tested`, `external-review-needed`

## Capability-to-proof ladder

| Capability ID | Current ladder position | Next required movement |
| --- | --- | --- |
| ADAPT-FEEDBACK-001 | instrument -> test | replicate, baseline, runtime probe |
| ADAPT-MEMORY-002 | instrument -> test | repeated runtime sessions |
| ADAPT-OPTIMISE-003 | instrument -> test | fixed/random/no-op baselines |
| ADAPT-RUNTIME-004 | test | artifact preservation and negative controls |
| ADAPT-INTEGRATION-005 | instrument -> test | formula definition and baseline comparison |
| ADAPT-CLAIM-GATE-006 | govern | extend to scientific packet artifacts |

## Capability documentation rule

Each new adaptive-system capability must add or update:

1. this registry;
2. at least one test;
3. an artifact or planned artifact;
4. an explicit supported claim;
5. an explicit known gap;
6. an explicit claim boundary;
7. a command that can be run locally.

## Canonical formulation

> HYBA_FULLSTACK capabilities are not advanced by assertion. They advance by registry entry, test command, artifact, supported claim, known gap, and claim boundary. The registry is the bridge between discovery and reviewable science.
