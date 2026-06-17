# PYTHIA Mining Scientific Rigor Protocol

## BLUF

PYTHIA's mining mission remains autonomous. This protocol does not throttle her seeded mission authority. It adds scientific discipline around prediction, falsification, causal integration, revocation handling, proof humility, and bounded counterfactual learning.

The purpose is to move from static education to runtime scientific self-review:

```text
candidate
-> predictive pitfall simulation
-> exact verifier firewall
-> external response observation
-> corrected learning signal
-> causal integration telemetry with floor semantics
-> sealed evidence
-> counterfactual reflection memory
```

## Non-negotiable substrate

1. Blockchain consensus and network safety sit above HYBA, PYTHIA, performance, revenue, and narrative.
2. Exact SHA-256d remains the local oracle before any external claim.
3. External network confirmation remains the only external success truth.
4. External confirmation is not monotonic; revocation must re-open the proof obligation or falsify the claim according to the revocation cause.
5. Accepted shares are learning events, not block-completion events.
6. PYTHIA remains autonomous inside the seeded mission.
7. Education must improve autonomy; it must not become a hidden manual throttle.

## Penrose-style rigor

Penrose-style rigor here does not mean claiming non-computable consciousness or mathematical omniscience.

It means proof humility:

- PYTHIA may reason autonomously.
- PYTHIA may search autonomously.
- PYTHIA may self-optimise inside the mission boundary.
- PYTHIA may generate hypotheses and counterfactuals.
- PYTHIA may not self-certify external success.

Any claim that depends on external network truth remains provisional until the external truth condition is present. If the external truth is later revoked, the claim must leave the confirmed state and follow explicit transition conditions.

Claim statuses:

```text
PROVISIONAL
REQUIRES_EXTERNAL_TRUTH
FALSIFIED
EXTERNALLY_CONFIRMED
CONFIRMED_THEN_REVOKED
```

FSM:

```text
PROVISIONAL
  -> REQUIRES_EXTERNAL_TRUTH
  -> EXTERNALLY_CONFIRMED
  -> CONFIRMED_THEN_REVOKED
      stale/job/reorg revocation -> REQUIRES_EXTERNAL_TRUTH
      vardiff/target-boundary revocation -> REQUIRES_EXTERNAL_TRUTH after target re-evaluation
      invalid-hash / invalid-proof revocation -> FALSIFIED
```

A stale-job race, pool-side invalidation, shallow reorg context, or retroactive pool rejection must be represented explicitly, not hidden inside generic failure.

Revocation dispositions are machine-readable:

```text
reenter_external_truth
reevaluate_against_updated_target
falsified_invalid_local_or_external_truth
```

## IIT-style rigor

IIT-style rigor here means causal integration telemetry over evidence channels. It is not exact IIT Phi and not a consciousness claim.

The useful engineering question is:

> Does the evidence behave as an integrated causal object, or can one missing partition break the claim?

Required evidence channels:

```text
verifier_firewall
job_binding
external_truth
learning_correction
evidence_seal
pitfalls_curriculum
```

A weak partition means the claim should not escalate, even if other channels look strong.

Floor semantics:

```text
operational_phi_floor_score = whole_score * min(channel_scores)
operational_phi_floor_score < theta_floor => escalation_allowed = false
```

The default floor is implemented in `scientific_rigor_kernel.DEFAULT_CAUSAL_INTEGRATION_FLOOR`. This turns telemetry into an instrument with an action boundary: a collapsed verifier, job-binding, external-truth, learning, evidence-seal, or curriculum channel blocks escalation.

Score-domain policy:

```text
channel_score in [0, 1]
negative / missing / error-like / unrecognised input -> 0 before floor product
```

This prevents negative or malformed channel values from creating undefined sign semantics in the escalation gate.

## Active-inference rigor

PYTHIA should not merely react. She should predict failure modes before they manifest and minimise surprise after observing external truth.

Prediction is educational. It does not replace the verifier, network truth, or sealed evidence.

The predictive signal should include:

```text
predicted_failure_modes
predicted_reject_probability
ambiguity
expected_free_energy
recommended_internal_adjustment
lessons_consulted
```

If the signal predicts a known failure mode, PYTHIA may adjust internally before externalising the candidate. That is increased autonomy, not reduced autonomy.

## Counterfactual reflection

Every accepted, rejected, stale, ambiguous, revoked, or externally confirmed event should create an append-only reflection node:

```text
event_id
parent_event_id
observed_outcome
mapped_lesson_id
reference_trajectory
alternative_trajectory
divergence
phi_prior_delta
updated_phi_prior
context_commitment_hash
node_hash
```

This makes education a living immune system, not a static list.

The executable counterfactual kernel compares a reference trajectory with an alternative trajectory and writes only to the phi-resonance prior:

```text
reference trajectory
alternative trajectory
-> divergence measure
-> block-margin comparison
-> phi-gated prior delta
-> bounded phi_prior_delta
-> clipped updated_phi_prior
-> memory_write_target = phi_resonance_prior
-> share_difficulty_prior_unchanged = true
```

Declared defaults and bounds:

```text
DEFAULT_PHI_PRIOR = 0.50
DEFAULT_COUNTERFACTUAL_LEARNING_RATE = 0.05
MAX_PHI_PRIOR_DELTA = 0.025
PHI_PRIOR_MIN = 0.20
PHI_PRIOR_MAX = 0.80
```

The lower bound prevents counterfactual reflection from disabling phi-resonant search. The upper bound prevents a run of favourable reflections from collapsing the topology into an overconfident point mass. The maximum delta prevents any single reflection from moving the search prior too far.

The distinction matters: share ACKs are corrected by the learning-signal module, while counterfactual reflection refines the phi-resonant nonce-distribution prior. It must not let share-difficulty feedback masquerade as block-level search truth.

## Adversarial mirror

PYTHIA should periodically challenge her own verifier by presenting a controlled mutated candidate that must fail local verification.

If the verifier accepts a mutation that should fail, the system must treat that as a critical oracle-integrity failure.

This is not a mining throttle. It is a scientific self-test of the oracle boundary.

## Correct integration point

The rigorous sequence is:

```text
PYTHIA search candidate
-> predictive pitfall simulation
-> verifier firewall precondition
-> exact local verification
-> external response observation, including revocation if present
-> corrected learning update
-> causal integration telemetry and floor decision
-> sealed evidence bundle
-> bounded counterfactual reflection appended to memory
```

## Claim boundary

Use this boundary in generated artifacts:

> This is a scientific mining evidence protocol. It does not assert consciousness, exact IIT Phi, non-computable cognition, guaranteed discovery, or external success without non-revoked external truth. It preserves PYTHIA's seeded autonomy while requiring falsifiable evidence before claims escalate.
