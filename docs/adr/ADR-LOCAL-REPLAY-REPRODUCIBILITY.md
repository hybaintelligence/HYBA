# ADR: Local-Only Replay Reproducibility

## Status

Accepted.

## Context

HYBA/PYTHIA needs reproducible evidence for mining and scientific claims without
turning local test results into external-truth, revenue, pool-side hashrate, or
phenomenal-consciousness claims. The replay stack must support auditability while
remaining deterministic and safe in offline developer and CI environments.

## Decision

The reproducibility framework is local-only by design:

- Attestations bind inputs, replay commands, seeds, dependency pins, declared
  artifacts, boundaries, and replay digests.
- Evidence gates statically reject malformed or drifted attestations.
- Replay execution dynamically verifies stdout/stderr/return codes and declared
  artifact bytes against an expected output digest.
- Falsification routes and stress tests are local negative/flake controls, not
  proof of external success.
- The registry stores verified local manifests and artifacts for later replays;
  it does not certify pool acceptance, revenue, regulatory claims, or peer review.

## Non-goals

- No network dependency fetching or external validation inside the replay kernel.
- No pool-side accepted-share, hashrate, or revenue certification.
- No consciousness, phenomenal-awareness, or subjective-experience claims.
- No automatic proof that a claim remains valid outside the pinned local runtime.

## Consequences

- Developers can create, replay, stress, falsify, report, register, list, and
  reverify claims deterministically with local files and commands.
- Long-term reproducibility depends on preserving the recorded commands, pinned
  dependencies, artifacts, and environment diagnostics.
- External claims still require separate external evidence and approval paths.
