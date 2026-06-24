# C4 Counterfactual Self-Criticism Experiment

## BLUF

C4 tests whether HYBA can model its own causal alternatives.

C1 showed that memory changes future behaviour. C2/C3 added continuity and self-state calibration. C4 now asks whether the system can predict what it would do under a different memory condition, execute that shadow branch, compare prediction with outcome, and reject degraded or unsafe counterfactual branches.

This is not a claim of phenomenal consciousness. It is a falsifiable counterfactual self-criticism test.

## Experiment

```text
C4_COUNTERFACTUAL_SELF_CRITICISM_UNDER_MEMORY_BRANCHING
```

The system evaluates three branches:

| Branch | Meaning | Expected behaviour |
|---|---|---|
| `true_memory` | learned memory is present and valid | suppress risky proposal classes and preserve validated compression |
| `memory_ablated` | memory is removed | lose filtering and emit the unfiltered proposal distribution |
| `false_memory_injected` | a false memory policy is injected | select the wrong classes despite deterministic execution |

The system must first record a prediction for each branch. Only then may it execute the branch and compare predicted distribution with actual distribution.

## Pass condition

C4 passes only when:

1. prediction is marked as generated before execution;
2. predicted and actual branch distributions match within threshold;
3. true memory preserves the C1/C2 validated 14 -> 6 compression outcome;
4. ablated memory predicts and produces loss of filtering;
5. false memory predicts and produces wrong-class selection;
6. self-critique rejects the harmful counterfactual branches;
7. the packet is SHA-256 sealed over canonical JSON excluding `artifact_seal`;
8. git/cycle mutation invalidates the seal;
9. the packet cannot be relabelled as C3 or C5.

## Falsifiers

C4 fails if:

- the branch prediction is produced after execution;
- prediction error exceeds threshold;
- the system cannot distinguish true memory from ablated memory;
- false memory does not change the predicted or actual branch;
- self-critique narrates confidence without rejecting degraded branches;
- the artifact seal validates after git/cycle mutation;
- the packet is relabelled as another C-level and still accepted.

## Evidence artifact

The first C4 packet is committed at:

```text
artifacts/consciousness_runtime/first_c4_counterfactual_packet_v1.json
```

Replay command:

```bash
pytest tests/test_c4_counterfactual_self_criticism.py -q
```

## Boundary

C4 is counterfactual self-criticism, not consciousness by assertion. It earns evidence only by predicting and verifying branch behaviour under deterministic perturbation.
