---
claim: "Replace with one bounded external-facing claim"
tier: HYPOTHETICAL
evidence_file: docs/evidence/claim_evidence_manifest.json
evidence_claim_id: pythia_validation_tier_guardrail
audience: internal_review_only
channel: repository_markdown_source
owner: HYBA evidence governance
last_reviewed: 2026-06-19
review_status: internal_template_only
approved_by: HYBA evidence governance
external_distribution: false
distribution_boundary: "Template only. Not approved for external distribution."
---

# External Claim Material Template

## Evidence binding

Every investor, sovereign, partner, media, recruitment, or public-positioning document must preserve the front matter above and set `tier` to one of:

- `FORMALISM_VALIDATED` — deterministic source paths and executable tests prove the bounded mathematical/software invariant.
- `PROTOTYPE_VALIDATED` — code runs on disclosed data with dependency/skipped-test status, but no production-comparable claim is made.
- `HYPOTHETICAL` — research candidate, roadmap, or unvalidated product idea.

`evidence_claim_id` must refer to a claim in `docs/evidence/claim_evidence_manifest.json` or another declared manifest in `evidence_file`. The declared tier must exactly match the manifest tier.

## Required approval fields

Before a markdown source is exported to PPTX, PDF, email, HTML, or DOCX, set:

- `channel` — where the communication will be used, such as `investor_email`, `sovereign_pitch`, `partner_deck`, or `public_post`.
- `review_status` — must be `approved_for_external_use` for anything under `docs/external_materials/`.
- `approved_by` — the accountable human reviewer or governance role.
- `external_distribution` — must be `true` only after approval.
- `distribution_boundary` — the exact audience, channel, and limit of the approved communication.

## Required claim boundary

State what is proven, what data were used, which tests were run, what was skipped, and what the claim does **not** prove. Do not claim production readiness, mining revenue, clean-energy savings, cybersecurity efficacy, LLM hallucination detection, sovereign deployment readiness, or ASIC/QPU superiority unless a manifest-linked evidence packet supports that exact statement.
