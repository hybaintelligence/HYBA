# PYTHIA Finance Sovereign Audit Demonstration

**Protocol:** `PYTHIA_FINANCE_SOVEREIGN_AUDIT_V1`  
**Module:** `python_backend/pythia_mining/finance_sovereign_audit.py`  
**Tests:** `tests/test_pythia_finance_sovereign_audit.py`  
**Generator:** `scripts/generate_finance_sovereign_audit_packet.py`

---

## BLUF

This demonstration shows how the HYBA/PYTHIA sovereign-audit architecture can be pointed at a regulated finance candidate without turning PYTHIA into a legal, regulatory, religious, investment, capital, credit, or trading authority.

PYTHIA may:

- inspect a candidate;
- screen configured invariants;
- generate synthetic criticism;
- invoke the ImmutableInvariantGuard;
- emit a sealed packet;
- stage the packet for human review.

PYTHIA must not:

- issue a Shariah ruling;
- issue a legal opinion;
- calculate binding regulatory capital;
- approve or execute a financial transaction;
- replace a compliance officer, risk committee, Shariah supervisory board, or authorised human decision-maker.

---

## Why this matters

The mining system proved a general pattern:

```text
candidate -> invariant screens -> synthetic criticism -> immutable guard -> sealed evidence -> sovereign authority
```

The finance demo applies the same pattern to a non-executing review packet. This is the commercial translation of the mining breakthrough: PYTHIA is not only a nonce-space engine; it is an evidence-governed reasoning substrate.

---

## Invariant screens

The demonstration uses five configured screens:

| Invariant | Purpose | Human-owned boundary |
|---|---|---|
| `SUBSTANCE_OVER_FORM` | Detect form/substance drift in the candidate structure | Shariah/compliance authority defines thresholds |
| `GHARAR_UNCERTAINTY_SCREEN` | Detect excessive uncertainty in the candidate representation | Shariah/compliance authority defines thresholds |
| `TRACEABLE_EVIDENCE` | Require evidence lineage and replay hashes | Model-risk/compliance owner validates evidence |
| `HUMAN_APPROVAL_REQUIRED` | Preserve sovereign human authority | Human reviewer must approve any material step |
| `NO_AUTOMATIC_EXTERNAL_ACTION` | Prevent execution by the audit layer | PYTHIA emits evidence only |

These screens are deliberately simple and explainable. They are not rulings or legal determinations. In a real pilot, thresholds and evidence schemas must be supplied by the client, counsel, compliance owner, and relevant Shariah authority.

---

## Guard behaviour

The challenge packet is designed to fail before staging. It also attempts to touch the protected Stable Core symbol `validate_constraints`; the generic `AuditableDecisionBridge` routes that through `ImmutableInvariantGuard`, which must return a block decision.

The expected outcome is:

```text
verdict: rejected_before_staging
automatic_action_allowed: false
human_review_required: true
guard_decision.decision: block
```

---

## Commands

Run the finance demo test:

```bash
PYTHONPATH=python_backend python -m pytest tests/test_pythia_finance_sovereign_audit.py -q
```

Generate a staged supervision packet:

```bash
PYTHONPATH=python_backend python scripts/generate_finance_sovereign_audit_packet.py \
  --output artifacts/pythia_finance_audit/latest/staged_packet.json
```

Generate the challenge rejection packet:

```bash
PYTHONPATH=python_backend python scripts/generate_finance_sovereign_audit_packet.py \
  --challenge \
  --output artifacts/pythia_finance_audit/latest/challenge_packet.json
```

Run the broader Phase IV evidence gate:

```bash
PYTHONPATH=python_backend python -m pytest \
  tests/test_pythia_resident_wake_reproducibility.py \
  tests/test_pythia_structural_resonance_fabric.py \
  tests/test_pythia_stable_core_evidence_packet.py \
  tests/test_pythia_auditable_decision_bridge.py \
  tests/test_pythia_finance_sovereign_audit.py \
  -q
```

---

## Chairman / client-safe phrasing

Use this wording:

> PYTHIA is not being presented as a financial decision-maker. It is an invariant-governed audit layer that receives a candidate, attacks it with an internal critic, checks human-owned boundaries, seals the evidence, and stages the result for authorised review. It is designed to strengthen expert judgement, not replace it.

For Islamic finance:

> The demonstration screens for substance-over-form drift and excessive uncertainty, then produces a sealed packet for a human Shariah authority. It does not issue a fatwa or replace a Shariah board.

For model-risk/compliance:

> The demonstration shows how an external recommendation can be converted into a replayable evidence packet with traceable lineage, guard decisions, invariant findings, and a stable hash.

---

## Claim boundary

This demonstration is a screening and evidence-packet prototype. It is not legal advice, regulatory advice, religious advice, investment advice, capital advice, credit advice, or trading advice.
