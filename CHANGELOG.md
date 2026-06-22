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

## 2026-06-22 — Agent D production closure documentation sprint

- Added developer onboarding, SDK quickstart, API reference, and system architecture documentation for Issue #134.
- Added incident response, customer onboarding, deployment, SLA template, FinOps controls, and unit-economics evidence boundaries.
- Added `scripts/finops_report.py` for AWS Cost Explorer reporting by service, customer tag, and API-surface tag.
- Archived `00_START_HERE_NEXT_STEPS.md` into `docs/strategy/` with a projection notice because its Series A and revenue assumptions are not yet production-evidenced.
- PR reference: pending (`docs: developer docs, runbooks, evidence pack`).
