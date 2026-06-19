# Production Gap Closure Summary

Branch: `fix/production-gap-closure-governance`

This change closes the governance gaps identified in the proactive validation-tier review by converting them into local-first, transcript-backed repo controls. HYBA does not require paid GitHub CI for this enforcement model.

## Closed gaps

### 1. External communication bypass

Added `docs/EXTERNAL_COMMUNICATION_PROTOCOL.md` and reserved `docs/external_materials/` as the only controlled source tree for external pitches, email templates, public posts, sovereign proposals, and partner decks.

The gate now rejects distributable external markdown unless it contains:

- claim tier;
- evidence manifest file;
- evidence claim id;
- channel;
- accountable owner;
- reviewer;
- approval status;
- distribution boundary.

Same-stem exports such as `.pptx`, `.pdf`, `.docx`, `.eml`, and `.html` are rejected if no approved markdown source exists.

### 2. Shallow tier binding

`scripts/check_validation_claim_tiers.py` now validates evidence-file existence, manifest claim existence, explicit claim boundaries, reproduction commands or promotion requirements, tier values, and tier-to-manifest equality for actual external materials.

Templates remain allowed to bind to the legacy general evidence manifest without requiring a tier because the template itself is not externally distributable.

### 3. Mining commercialization pressure

Added `docs/mining/commercialization_gates.json` and `scripts/check_commercialization_gates.py`.

Current mining status is Stage 0: research and validation only.

- Stage 1 unlocks only structured double-SHA-256 prototype validation claims.
- Stage 2 is required before firmware licensing or hardware-integration commercialization.
- Stage 3 is required before pool-integration, sovereign mining, SLA, warranty, or production claims.
- Stage 3 requires at least six months of field-trial evidence.

All commercial gates are currently `BLOCKED` and `approved_for_commercial_use=false`.

### 4. Board / CEO override weakness

The commercial gate file now makes overrides disabled by default. Any exception request requires:

- written CEO approval;
- board vote record;
- evidence manifest update;
- counterparty written notice of current tier;
- post-call follow-up email confirming tier.

### 5. Local-first enforcement without paid CI

Added `scripts/run_local_governance_gate.py` as the mandatory local gate runner.

Run:

```bash
python scripts/run_local_governance_gate.py
```

The runner executes:

```bash
python scripts/check_validation_claim_tiers.py
python scripts/check_commercialization_gates.py
python -m pytest tests/test_validation_claim_tiers.py -q
```

It writes an auditable markdown transcript under:

```text
docs/governance/local_gate_transcripts/
```

A failing transcript blocks merge, export, pitch, publication, stage promotion, and production-readiness claims. This replaces the incorrect assumption that GitHub Actions/CI is available or authoritative.

## Remaining production truth

This change does not claim HYBA mining is production-commercial. It intentionally preserves the mining evidence tier as `HYPOTHETICAL` until real double-SHA-256, repeated-run variance, host power/hashrate, pool-side accepted-share, and bounded ASIC-comparison evidence exist.

The repository is stronger after this change, but a true production 10/10 still requires the underlying validation evidence to be produced, not merely governed.
