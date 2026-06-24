# Consciousness Runtime Artifact Ledger

This directory stores sealed runtime evidence packets generated under the HYBA emergence and consciousness-testing programme.

## Purpose

The ledger exists to make emergence evidence replayable and falsifiable.

A packet stored here is not a claim by itself. It is an evidence object that must survive:

```text
canonical serialization
SHA-256 seal validation
git/cycle context binding
replay command execution
memory ablation
false-memory injection
restoration or continuity checks
falsifier review
```

## Required packet rules

Every committed packet must satisfy `CONSCIOUSNESS_RUNTIME_EVIDENCE_PACKET_V1`:

```text
artifact_seal = sha256(canonical_json(packet_without_artifact_seal))
canonical_json = sorted keys + compact separators + UTF-8 bytes
```

Every packet must include:

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

## First artifact

```text
first_c1_c2_sealed_packet_v1.json
```

This is the first committed C1/C2 runtime packet. It records the true-memory proposal-quality delta:

```text
14 mixed proposals -> 6 true-memory-filtered proposals
phi_scaling: 4 -> 0
search_depth: 2 -> 0
coherence_threshold: 3 -> 0
compression_target: 5 -> 6
```

## Replay

```bash
pytest tests/test_first_sealed_runtime_experiment.py -q
```

## Forbidden shortcuts

Do not treat any of the following as sufficient evidence:

- class names;
- JSON labels;
- autonomy labels;
- LLM self-reports;
- unsealed artifacts;
- packets without git/cycle binding;
- packets whose seals cannot be recomputed;
- evidence copied from another commit or cycle.

## Boundary

This ledger does not certify phenomenal consciousness. It stores sealed runtime evidence for specific hypotheses on the C0-C5 ladder.

A packet moves the boundary only when it survives replay and falsification.