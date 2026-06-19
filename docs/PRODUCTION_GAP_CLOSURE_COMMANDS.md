# Production Gap Closure Commands

HYBA does not rely on paid GitHub CI for these controls. The production-gap closure is local-first and transcript-backed.

## Mandatory local gate

Run this before merging, exporting external material, sending investor/sovereign/partner claims, or advancing a mining commercialization stage:

```bash
python scripts/run_local_governance_gate.py
```

The runner executes:

```bash
python scripts/check_validation_claim_tiers.py
python scripts/check_commercialization_gates.py
python -m pytest tests/test_validation_claim_tiers.py -q
```

It writes a markdown transcript under:

```text
docs/governance/local_gate_transcripts/
```

A failing transcript blocks merge, export, pitch, publication, commercial-stage promotion, and production-readiness claims until fixed and re-run.

## Fast manual commands

For focused local debugging, run the underlying gates directly:

```bash
python scripts/check_validation_claim_tiers.py
python scripts/check_commercialization_gates.py
python -m pytest tests/test_validation_claim_tiers.py -q
```

The existing npm alias still runs the strengthened claim-tier guard:

```bash
npm run review:claim-tiers
```

## Operating discipline

- No deck, PDF, DOCX, email template, public post, partner script, or sovereign-pilot proposal may leave HYBA without a passing local gate transcript.
- No mining firmware, pool, sovereign, SLA, warranty, revenue, hashrate, accepted-share, or ASIC-superiority claim may be made unless the commercial gate file unlocks it and the local gate passes.
- A passing gate is necessary but not sufficient for production claims. The evidence manifest must still contain the required real-world validation evidence.
