# HYBA External Communication Protocol

This protocol turns evidence-tier governance into an operating rule for investor, sovereign, partner, media, recruitment, and public communications.

## Non-negotiable rule

No external claim leaves HYBA unless its source markdown lives in `docs/external_materials/`, contains claim-tier front matter, binds to an evidence manifest entry, and passes the local governance gate.

```bash
python scripts/run_local_governance_gate.py
```

Decks, PDFs, DOCX files, email templates, HTML exports, LinkedIn drafts, partner scripts, and sovereign-pilot proposals are treated as production artifacts. They must be generated from approved markdown source. A same-stem export without approved markdown is a failed gate.

## Required source location

Use this layout:

```text
docs/external_materials/
  <product>/
    <audience_or_counterparty>.md
    <audience_or_counterparty>.pptx   # optional export, same stem only
    <audience_or_counterparty>.pdf    # optional export, same stem only
```

Do not keep live Jamaica, Munera, DIFC, investor, LinkedIn, or partner materials outside this tree if they are meant to be sent.

## Required front matter

Every externally distributable `.md` file must include:

```yaml
---
claim: "One bounded claim only"
tier: HYPOTHETICAL
evidence_file: docs/evidence/claim_evidence_manifest.json
evidence_claim_id: pythia_validation_tier_guardrail
audience: investor_or_counterparty_name
channel: sovereign_pitch | investor_email | partner_deck | public_post | recruitment | media
owner: accountable_business_owner
last_reviewed: YYYY-MM-DD
review_status: approved_for_external_use
approved_by: named_reviewer_or_governance_role
external_distribution: true
distribution_boundary: "Exact audience, channel, and permitted reuse boundary"
---
```

The declared `tier` must exactly match the manifest claim tier. If the manifest says `HYPOTHETICAL`, the material may not say or imply `PROTOTYPE_VALIDATED`, `PRODUCTION_VALIDATED`, production-ready, revenue-ready, ASIC-superior, sovereign-ready, or field-proven.

## Approval workflow

1. Draft the material in `docs/external_materials/<product>/<audience>.md`.
2. Bind every claim to an evidence manifest entry.
3. Set `external_distribution: false` while drafting.
4. Run `python scripts/run_local_governance_gate.py` and fix failures.
5. Obtain accountable governance review.
6. Set `review_status: approved_for_external_use`, `approved_by`, `external_distribution: true`, and `distribution_boundary`.
7. Run the local governance gate again.
8. Archive or commit the passing transcript produced under `docs/governance/local_gate_transcripts/`.
9. Export to PPTX/PDF/DOCX/email only after the gate passes.

## Oral communication control

Verbal overclaims cannot be blocked by code, so every external call involving validation status must be followed by a written confirmation:

> To confirm the evidence boundary discussed today: `<product/claim>` is currently `<tier>`. The current validated evidence is `<manifest claim id>`. The claim does not prove `<boundaries>`. We will not market this as production-ready until the required stage gates pass.

The written confirmation must be committed or archived as an external material source before any follow-up deck or proposal is sent.

## Escalation

Escalate to CEO and board review when any of the following occurs:

- a deck, PDF, email, post, or script is sent without approved markdown source;
- a local governance gate transcript is missing, failed, or not archived for a sent claim;
- a `HYPOTHETICAL` claim is represented as prototype, production, revenue, or field validated;
- a mining claim asserts hashrate, accepted shares, revenue, ASIC superiority, or firmware readiness before the commercial stage gate unlocks;
- a counterparty receives a stronger claim orally than the written evidence tier allows.

## Mining-specific commercial rule

Mining commercialization is controlled by `docs/mining/commercialization_gates.json` and checked by the local governance gate:

```bash
python scripts/run_local_governance_gate.py
```

For focused debugging, the underlying commercial gate can be run directly:

```bash
python scripts/check_commercialization_gates.py
```

Current state is Stage 0: research and validation in progress only. Firmware licensing cannot unlock before Stage 2. Pool integration, sovereign mining, SLA, warranty, and production deployment claims cannot unlock before Stage 3 with at least six months of field-trial evidence.
