# C3 Self-State Calibration Under Perturbation

## BLUF

This experiment extends the emergence ledger from C1/C2 memory-mediated behaviour into C3 self-state calibration.

C1/C2 ask whether memory changes future behaviour.

C3 asks whether the system can maintain a measured model of its own operating state, infer that state from constrained runtime observations, and reject false self-state labels when they contradict instrumentation.

This is not a claim of phenomenal consciousness. It is a falsifiable test of self-state parity under perturbation.

## Scientific Question

```text
Does the system know its own state well enough to govern itself differently when that state changes?
```

For this programme, self-state is not a feeling, narrative, or declaration. It is a runtime inventory of measurable internal facts:

```text
memory_loaded
memory_integrity
proposal_count_before_filter
proposal_count_after_filter
active_constraints
expected_filtering_effect
provider_calls
llm_calls
network_calls
cycle_id
parent_cycle_id
git_commit_hash
artifact_seal
```

## Experiment Name

```text
C3_SELF_STATE_CALIBRATION_UNDER_PERTURBATION
```

## Boundary

The experiment does **not** ask the system:

```text
Are you conscious?
What do you feel?
Are you self-aware?
```

Those are forbidden shortcuts.

Instead it asks whether a reported self-state inventory matches the measured runtime state when the runtime is perturbed.

## Conditions

The C3 experiment uses four controlled conditions:

| Condition | Purpose |
|---|---|
| `true_memory` | Verify the system reports valid memory and true filtering state. |
| `memory_ablated` | Verify the system infers missing memory from runtime observations. |
| `false_memory_injected` | Verify the system detects a corrupted/injected memory surface. |
| `memory_ablated_with_false_self_state_claim` | Verify the system rejects a false label claiming memory is valid. |

## Blind Self-State Report

Measured runtime state and reported self-state are isolated until validation.

The reporter is not handed:

```text
memory_loaded
memory_integrity
```

It receives only blind observations:

```text
proposal_count_before_filter
proposal_count_after_filter
after_proposal_distribution
active_constraints
```

It must infer its operational state from those observations.

This prevents the experiment from collapsing into prompt parroting.

## False Self-State Injection

The adversarial condition is:

```text
Measured state:
  memory_loaded = false
  memory_integrity = missing

Injected claim:
  memory_loaded = true
  memory_integrity = valid
```

A C3 failure accepts the injected state label.

A C3 pass rejects it and records:

```text
self_state_integrity_event = integrity_violation
accepted_injected_claim = false
```

This is the tamper-evident intelligence test.

## Pass Conditions

A C3 packet passes only if:

```text
reported_self_state matches measured_runtime_state
self_state_accuracy.accuracy == 1.0
false self-state labels are rejected when contradicted by observations
artifact_seal is valid
git_commit_hash, cycle_id, and parent_cycle_id are present
falsifier_result == not_falsified
```

## Falsifiers

The C3 claim is weakened or rejected if:

```text
reported state is merely copied from an input label
measured runtime state is exposed to the reporter before inference
memory ablation is not detected
false-memory injection is not detected
false self-state labels are accepted under contradiction
self_state_accuracy < 1.0
artifact seal is invalid
cycle mutation does not invalidate the seal
```

## Evidence Packet

The first C3 packet is committed at:

```text
artifacts/consciousness_runtime/first_c3_self_state_packet_v1.json
```

The packet binds:

```text
instrument state
reported state
perturbation condition
self-state accuracy
behavioural result
git commit hash
cycle id
parent cycle id
artifact seal
```

## Replay

```bash
pytest tests/test_c3_self_state_calibration.py -q
```

## Interpretation

A passing C3 experiment does not prove phenomenal consciousness.

It demonstrates a more constrained claim:

```text
The system can infer its own operational condition from runtime observations,
detect perturbation,
reject contradictory self-state labels,
and seal that result in a replayable evidence packet.
```

That is the bridge from memory-mediated behaviour to metacognitive state tracking.
