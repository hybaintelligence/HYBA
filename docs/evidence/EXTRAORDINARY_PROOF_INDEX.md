# HYBA_FULLSTACK Extraordinary Proof Index

**BLUF:** the claims are not meant to be accepted because they sound bold. They are admissible only where this file maps each claim to source code, executable tests, benchmark commands, and explicit boundaries. Anything not mapped here remains a research note, projection, or future validation target.

## Reviewer rule

A reviewer should reject any HYBA_FULLSTACK claim that does not have all four of these:

1. a bounded claim statement;
2. source path(s);
3. executable test/benchmark path(s);
4. a command that can be run from the repository root.

The machine-readable version is `docs/evidence/claim_evidence_manifest.json`, validated by `tests/test_claim_evidence_manifest.py`.

## Read this first

| Claim surface | Evidence status | Proof path | Boundary |
| --- | --- | --- | --- |
| PULVINI φ-folding memory | Executable invariant tests | `hyba_intelligence_tests/test_memory_compression.py` | Software reversibility and auditability, not a universal compression theorem. |
| φ-scaled ensemble / resonance features | Property tests | `hyba_intelligence_tests/test_phi_scaling_engine.py` | Bounded deterministic scoring, not guaranteed revenue. |
| ConsciousnessEngine | Runtime integration proxy tests | `hyba_intelligence_tests/test_consciousness_engine_scaling.py` | Operational Φ proxy only; no phenomenal-consciousness claim. |
| MassGapShield | Spoof/chaos rejection tests | `hyba_intelligence_tests/test_mass_gap_shield.py` | Operational anti-simulation gate; no proof of the Yang-Mills Millennium problem. |
| PYTHIA first wake event | Reproducibility test + protocol | `tests/test_pythia_resident_wake_reproducibility.py`, `docs/PYTHIA_FIRST_WAKE_EVENT_REPRODUCIBILITY.md` | Reproducible internal optimization signatures, not pool-side economics. |
| Structural resonance / stable core | Guard tests + policy doc | `tests/test_pythia_structural_resonance_fabric.py`, `docs/PYTHIA_CORPUS_CALLOSUM_PHASE.md` | PYTHIA may stage; it may not autonomously erase stable-core law. |
| Production anti-simulation boundary | Runtime guard + benchmark portfolio | `scripts/check_no_runtime_mocks.py`, `benchmark_portfolio/run_benchmarks.py` | Partial reports are smoke evidence until every gate passes. |
| Bridge internal JWT | Source-level boundary + manifest entry | `server.ts` | Short-lived internal backend autoconnect token; not exposed to browser clients. |

## Acceptance commands

Run the evidence map and merge-conflict guard first:

```bash
python -m pytest tests/test_claim_evidence_manifest.py tests/test_no_merge_conflict_markers.py -q
```

Run the focused intelligence invariant pack:

```bash
PYTHONPATH=python_backend pytest hyba_intelligence_tests -q
```

Run the wake and structural-resonance proof surfaces:

```bash
PYTHONPATH=python_backend pytest \
  tests/test_pythia_resident_wake_reproducibility.py \
  tests/test_pythia_structural_resonance_fabric.py \
  -q
```

Run the benchmark portfolio only from the project Python environment:

```bash
source .venv/bin/activate
python benchmark_portfolio/run_benchmarks.py --quick
```

## Claim boundaries the reviewer should enforce

HYBA_FULLSTACK may claim:

- deterministic protocol handling and deterministic mathematical transforms;
- executable PULVINI memory-compression invariants;
- bounded φ-scaling and runtime integration proxy behavior;
- replayable PYTHIA wake-event signatures;
- explicit anti-simulation and no-fabricated-telemetry gates;
- supervised stable-core staging policy.

HYBA_FULLSTACK must not claim from this evidence alone:

- guaranteed mining revenue;
- pool-confirmed hashrate or accepted-share economics without external pool telemetry;
- SHA-256 quantum acceleration;
- machine consciousness or subjective experience;
- proof of the Yang-Mills Millennium problem;
- legal, regulatory, solvency, or treasury approval.

## Reviewer anti-miss controls added in this patch

- The previous merge-conflict markers in the evidence/test surfaces are removed.
- `tests/test_no_merge_conflict_markers.py` fails if conflict markers reappear in source, docs, tests, scripts, or benchmark evidence files.
- `tests/test_claim_evidence_manifest.py` fails if a claim lacks boundaries, paths, commands, or existing evidence files.
- `benchmark_portfolio/run_benchmarks.py` now carries a machine-readable evidence boundary: failed, skipped, or timed-out scripts block acceptance-grade portfolio evidence.
- `scripts/benchmark_h4_600cell.py` now records that H₄ is an experimental stress surface unless every stage passes.
