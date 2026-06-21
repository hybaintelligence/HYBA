# Changelog

## v1.0.0 - Local Replay Reproducibility Stack

### Added

- Deterministic reproducibility attestations for inputs, commands, seeds,
  dependency pins, artifacts, boundaries, and replay digests.
- Local replay executor with artifact hashing, stress testing, environment
  diagnostics, falsification probes, and full falsification-suite coverage.
- Mining auto-attester for zero-touch manifest emission from successful local
  mining/benchmark runs.
- Directory-based manifest registry for verified manifests and artifacts.
- CLI entry point (`pythia-replay`) plus compatibility script
  (`scripts/replay_claim.py`) for replay, stress, falsification, reporting,
  registration, listing, and re-verification workflows.
- JSON/HTML replay reporting and unified diff helpers.
- ADR, developer playbook, and bundled replay examples.
- Property-based test scaffolding for canonicalization, replay determinism,
  artifact hashing, and registry roundtrips.

### Boundaries

- Local deterministic replay only; no pool-side accepted-share, hashrate,
  revenue, external validation, regulatory, or consciousness claims.
