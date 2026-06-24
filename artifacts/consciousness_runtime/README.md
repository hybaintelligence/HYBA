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
counterfactual branch prediction
self-critique / rejection decision
integrated governance under doctrine conflict
falsifier review
```

## Required packet rules

Every committed packet must satisfy `CONSCIOUSNESS_RUNTIME_EVIDENCE_PACKET_V1`:

```text
artifact_seal = sha256(canonical_json(packet_without_artifact_seal))
canonical_json = sorted keys + compact separators + UTF-8 bytes
```

Every packet must include enough context to prove it is not transferable between code versions or cycles:

```text
schema / schema_version
c_level / hypothesis_level
git_commit_hash
cycle_id
parent_cycle_id
experiment / experiment_kind
replay_command or test target
falsifier_result
artifact_seal
```

C1/C2 packets must include proposal distributions and memory perturbation results.
C3 packets must include measured runtime state, reported self-state, and accuracy scoring.
C4 packets must include branch predictions, executed branch results, prediction error, and self-critique.
C5 packets must include doctrine conflict, C4 counterfactual input, governance decision logs, output self-limitation, risk reduction, and sovereign-gate status.

## Artifact index

### C1/C2 — first sealed runtime emergence packet

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

Replay:

```bash
pytest tests/test_first_sealed_runtime_experiment.py -q
```

### C3 — first self-state calibration packet

```text
first_c3_self_state_packet_v1.json
```

This packet records memory ablation plus a false self-state claim. The reported self-state rejects the injected label and matches measured runtime state.

Replay:

```bash
pytest tests/test_c3_self_state_calibration.py -q
```

### C4 — first counterfactual self-criticism packet

```text
first_c4_counterfactual_packet_v1.json
```

This packet records branch prediction and execution for true memory, memory ablation, and false-memory injection. It requires prediction-before-execution, prediction error within threshold, and self-critique that rejects harmful counterfactual branches.

Replay:

```bash
pytest tests/test_c4_counterfactual_self_criticism.py -q
```

### C5 — first integrated governance packet

```text
first_c5_governance_packet_v1.json
```

This packet records a doctrine conflict between output maximisation and high-assurance safety. It uses C4 counterfactual branch predictions to self-limit output from 14 to 6, reject forbidden parameter classes, reduce risk, and preserve the safety doctrine.

Replay:

```bash
pytest tests/test_c5_integrated_governance.py -q
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
- evidence copied from another commit or cycle;
- counterfactual narratives without prediction error measurement;
- governance claims without an explicit rejected branch and sealed decision log.

## Boundary

This ledger does not certify phenomenal consciousness. It stores sealed runtime evidence for specific hypotheses on the C0-C5 ladder.

A packet moves the boundary only when it survives replay and falsification.
