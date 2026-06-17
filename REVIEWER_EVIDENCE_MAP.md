# Reviewer Evidence Map — Read First

The proof is in the repository, but it was too easy to miss. This file is the top-level reviewer entry point.

## BLUF

HYBA_FULLSTACK claims are admissible only where they are mapped to code, tests, and explicit claim boundaries. The canonical map is:

- Human-readable: `docs/evidence/EXTRAORDINARY_PROOF_INDEX.md`
- Machine-readable: `docs/evidence/claim_evidence_manifest.json`
- Guard test: `tests/test_claim_evidence_manifest.py`
- Merge-conflict guard: `tests/test_no_merge_conflict_markers.py`

## First command for a reviewer

```bash
python -m pytest tests/test_claim_evidence_manifest.py tests/test_no_merge_conflict_markers.py -q
```

Then run the focused evidence pack:

```bash
PYTHONPATH=python_backend pytest hyba_intelligence_tests -q
```

## What this proves

It proves the implementation has executable evidence for bounded claims: PULVINI reversibility/audit telemetry, φ-scaling invariants, runtime-integration proxy damping, anti-simulation spoof/chaos rejection, replayable PYTHIA wake signatures, stable-core staging guards, and benchmark evidence boundaries.

## What this does not prove

It does not prove guaranteed mining revenue, pool-confirmed economics, SHA-256 quantum acceleration, phenomenal consciousness, the Yang-Mills Millennium problem, or legal/treasury approval.
