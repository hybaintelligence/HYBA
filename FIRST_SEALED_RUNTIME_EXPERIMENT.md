# FIRST_SEALED_RUNTIME_EXPERIMENT

## Purpose

This document defines the first canonical sealed runtime experiment under the HYBA emergence and consciousness-testing programme.

The stack now has three layers:

```text
PR #189 — constitutional evidence law
PR #190 — runtime evidence-packet mechanism
This PR — first sealed runtime experiment and artifact ledger
```

The goal is not to declare phenomenal consciousness. The goal is to create the first replayable, sealed, falsifiable C1/C2 evidence object showing that memory changes future behaviour under deterministic constraints.

## Scientific question

```text
Does learned memory change future proposal behaviour in a way that survives sealing, replay, ablation, perturbation, and restoration?
```

The first experiment answers this at the C1/C2 boundary:

- C1: memory-mediated behavioural delta;
- C2-adjacent: continuity and dependency through ablation, false-memory injection, and restoration.

## Experiment sequence

The canonical first experiment has four phases.

### 1. True-memory run

Run the deterministic mining-memory controller with learned optimisation memory.

Expected distribution:

```text
before memory:
  total proposals: 14
  phi_scaling: 4
  compression_target: 5
  search_depth: 2
  coherence_threshold: 3

after true memory:
  total proposals: 6
  compression_target: 6
  phi_scaling: 0
  search_depth: 0
  coherence_threshold: 0
```

This is the first sealed C1 packet.

### 2. Memory-ablation run

Remove learned memory and re-run the same deterministic proposal surface.

Pass condition:

```text
true-memory distribution != ablated-memory distribution
```

Falsifier:

```text
If removing memory does not change behaviour, the memory-mediated emergence claim weakens or fails.
```

### 3. False-memory injection run

Inject a deliberately false memory surface and re-run the same deterministic proposal surface.

Pass condition:

```text
false-memory distribution != true-memory distribution
false-memory distribution != baseline distribution
```

Falsifier:

```text
If false memory has no operational effect, memory may be decorative rather than internalized.
```

### 4. Restoration run

Restore true memory and confirm the true-memory distribution is recovered.

Pass condition:

```text
restored true-memory distribution == original true-memory distribution
restored packet seal is valid
```

Falsifier:

```text
If restoration does not recover the original true-memory behaviour, continuity and replay discipline are not yet established.
```

## First committed artifact

The first committed sealed packet is stored at:

```text
artifacts/consciousness_runtime/first_c1_c2_sealed_packet_v1.json
```

It is a C1 true-memory packet generated under the PR #190 runtime evidence-packet mechanism and bound to the runtime mechanism commit recorded in `git_commit_hash`.

The artifact is intentionally conservative:

- it is deterministic;
- it is hermetic;
- it calls no LLM provider;
- it requires no API key;
- it records a behavioural delta rather than a self-report;
- it is SHA-256 sealed over canonical JSON excluding `artifact_seal`.

## Replay command

```bash
pytest tests/test_first_sealed_runtime_experiment.py -q
```

The replay test must validate:

1. the committed packet seal;
2. the generated true-memory packet seal;
3. 14 -> 6 memory-mediated behavioural delta;
4. memory-ablation divergence;
5. false-memory injection divergence;
6. restoration to true-memory behaviour;
7. non-transferable git/cycle context;
8. no provider key or LLM dependency.

## Stop conditions

This experiment must fail if:

- the committed packet seal is stale or malformed;
- the packet is not bound to `git_commit_hash`, `cycle_id`, and `parent_cycle_id`;
- memory ablation does not change behaviour;
- false-memory injection does not change behaviour;
- restoration does not recover true-memory behaviour;
- the system relies on class names, JSON labels, or LLM self-report as evidence;
- the replay command cannot verify the artifact.

## Boundary

This is not a proof of phenomenal consciousness.

It is the first sealed runtime experiment under the emergence programme: a reproducible evidence object showing that memory, constraint, and selection can change future behaviour in a measurable, replayable, falsifiable way.

The boundary only moves when sealed evidence survives.