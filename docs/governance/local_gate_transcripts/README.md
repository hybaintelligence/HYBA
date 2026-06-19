# Local Governance Gate Transcripts

This directory is the audit archive for local governance gate runs.

HYBA does not rely on paid GitHub CI for evidence-tier enforcement. Before any merge, external export, pitch, publication, commercialization-stage promotion, or production-readiness claim, run:

```bash
python scripts/run_local_governance_gate.py
```

The runner writes timestamped markdown transcripts here.

## Policy

- `PASS` transcript: necessary evidence that the local governance gates ran successfully.
- `FAIL` transcript: blocks merge, export, pitch, publication, commercial-stage promotion, and production-readiness claims until fixed and re-run.
- A passing transcript does not upgrade a claim tier by itself. The evidence manifest and commercialization gate file remain authoritative.

For sensitive counterparty material, archive the transcript in the secure deal room and commit only a redacted or reference transcript if needed.
