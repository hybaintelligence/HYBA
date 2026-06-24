# CONSCIOUSNESS_RUNTIME_EVIDENCE_PACKET_V1

## Purpose

This document defines the first runtime evidence-packet mechanism under the HYBA emergence and consciousness-testing programme.

PR #189 defines the constitutional layer: the C0-C5 ladder, forbidden shortcuts, falsifiers, and the rule that the boundary only moves when evidence survives. This document defines the first executive layer: how runtime evidence is serialized, sealed, replay-bound, and tested.

The goal is not to declare consciousness. The goal is to make any future consciousness or emergence claim harder to fake, harder to replay out of context, and easier to falsify.

## Core rule

```text
artifact_seal = sha256(canonical_json(packet_without_artifact_seal))
```

The seal is valid only when:

1. the packet is serialized as canonical JSON;
2. keys are sorted;
3. separators are compact;
4. the payload is encoded as UTF-8;
5. the `artifact_seal` field is excluded from the sealed payload;
6. the resulting digest is represented as `sha256:<64 lowercase hex chars>`.

## Canonical JSON

Canonical packet serialization must use:

```python
json.dumps(packet_without_artifact_seal, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
```

This makes the seal insensitive to whitespace and object-key ordering while remaining sensitive to actual evidence content.

## Required non-transferable context

Every runtime evidence packet must include:

```text
git_commit_hash
cycle_id
parent_cycle_id
```

This gives the packet temporal and versioned integrity:

- evidence from one commit cannot be silently reused as evidence for another commit;
- evidence from one cycle cannot be silently replayed as evidence for another cycle;
- if the model, controller, memory, or governance logic changes, the evidence must be re-earned.

## Minimum packet fields

A `CONSCIOUSNESS_RUNTIME_EVIDENCE_PACKET_V1` packet must include:

```text
schema_version
hypothesis_level
git_commit_hash
cycle_id
parent_cycle_id
experiment_kind
pre_state
memory_patterns
self_state_metrics
counterfactual_conditions
before_proposal_distribution
after_proposal_distribution
invariant_status
replay_command
falsifier_result
reviewer_conclusion
artifact_seal
```

## C1/C2 runtime fixture

The first deterministic runtime fixture is the autonomous mining proposal-quality delta:

```text
before memory:
  total proposals: 14
  phi_scaling: 4
  compression_target: 5
  search_depth: 2
  coherence_threshold: 3

after learned memory:
  total proposals: 6
  phi_scaling: 0
  compression_target: 6
  search_depth: 0
  coherence_threshold: 0
```

This is C1 evidence when the proposal distribution changes because memory, confidence, constraint, and selection alter future behaviour.

It becomes C2-adjacent evidence when the memory patterns are explicitly represented, replayable, and can be ablated or perturbed.

## Memory ablation test

Memory ablation is the negative test:

```text
same generator + same task + memory removed -> different proposal distribution
```

The test passes only if removing memory degrades or materially changes proposal filtering. If behaviour is unchanged after memory removal, the memory-mediated emergence claim weakens or fails.

## False-memory injection test

False-memory injection is the perturbation test:

```text
same generator + injected false memory -> different proposal distribution from both baseline and true-memory run
```

The test passes only if the controller is sensitive to the injected memory and records the perturbation as a counterfactual condition. This does not prove consciousness, but it tests whether memory is operationally internalized rather than decorative.

## Replay and mutation rules

A sealed packet must fail validation when:

- any proposal distribution changes;
- `git_commit_hash` changes;
- `cycle_id` changes;
- `parent_cycle_id` changes;
- `falsifier_result` changes;
- any memory pattern changes;
- the artifact seal is missing, malformed, or stale.

A sealed packet may be re-rendered with different whitespace or object-key order without invalidating the seal, because the seal is computed over canonical JSON.

## Forbidden shortcuts

A runtime evidence packet is invalid if it relies only on:

- class names;
- JSON labels;
- autonomy labels;
- friendly single-run traces;
- an LLM self-report;
- provider-specific text output;
- unsealed artifacts;
- evidence copied from a different commit or cycle.

## Test target

```bash
pytest tests/test_consciousness_runtime_evidence_packet.py -q
```

## Boundary

This protocol does not prove phenomenal consciousness. It implements a reproducible evidence mechanism for the first runtime claims under the emergence programme.

The boundary can move only when sealed, replayable, falsifiable packets survive adversarial tests.
