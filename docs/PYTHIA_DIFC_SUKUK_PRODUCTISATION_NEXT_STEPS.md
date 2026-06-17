# PYTHIA DIFC / AAOIFI Sukuk Productisation Pass

**Status:** implemented as a lift-out extension under `python_backend/pythia_finance_audit/`  
**Boundary:** read-only criticism, lifecycle simulation, sealed evidence, and human sovereign review only.

---

## BLUF

The DIFC / AAOIFI Sukuk module has moved from a single packet generator into a small productisation surface:

1. a multi-step Sukuk lifecycle drift simulator;
2. a read-only Markdown criticism ledger for Shariah scholar / SSSB / trustee / compliance review;
3. CLI scripts for generating and rendering those artifacts;
4. tests locking the no-action and human-review boundaries.

This preserves the prior architecture:

```text
candidate -> invariant screens -> synthetic criticism -> immutable guard -> sealed evidence -> sovereign human authority
```

The product surface remains outside `pythia_mining`, which keeps future extraction feasible.

---

## New files

```text
python_backend/pythia_finance_audit/sukuk_lifecycle_simulation.py
python_backend/pythia_finance_audit/criticism_ledger.py
scripts/simulate_difc_sukuk_lifecycle.py
scripts/render_difc_sukuk_criticism_ledger.py
tests/test_pythia_difc_sukuk_lifecycle_simulation.py
tests/test_pythia_difc_sukuk_criticism_ledger.py
```

---

## Lifecycle simulation

The simulator creates a deterministic five-step Sukuk lifecycle:

| Step | Stage | Purpose |
|---:|---|---|
| 01 | `pre_issuance_structuring` | Clean pre-issuance structure with ownership, SPV, trustee, SSSB, and traceability evidence. |
| 02 | `issuance_closing_review` | Closing review with asset evidence and trustee confirmation. |
| 03 | `continuity_monitoring_warning` | First warning where risk-sharing begins to resemble debt-like fixed-return behaviour. |
| 04 | `asset_drift_restructuring_trigger` | First blocker state with substance, asset-backing, SPV, and uncertainty drift. |
| 05 | `maturity_or_remediation_review` | Remediation state that remains blocked until evidence and structure are restored. |

Every step preserves:

```text
human_review_required = true
automatic_action_allowed = false
action = ESCALATE_TO_SOVEREIGN_HUMAN
```

---

## Read-only criticism ledger

The ledger renderer accepts either:

1. a single DIFC / AAOIFI Sukuk packet; or
2. a lifecycle simulation bundle.

It renders a Markdown view that is suitable for non-technical review:

- candidate ID and lifecycle stage;
- verdict;
- no-action boundary;
- packet hash;
- finding table;
- failed/warning counts;
- human owner and review tag;
- per-finding reasoning;
- recommended next action.

The ledger is presentation-only and does not perform any external action.

---

## Commands

Run the complete finance/Sukuk productisation test gate:

```bash
PYTHONPATH=python_backend python -m pytest \
  tests/test_pythia_finance_sovereign_audit.py \
  tests/test_pythia_difc_aaiofi_sukuk_bridge.py \
  tests/test_pythia_difc_aaoifi_import_surface.py \
  tests/test_pythia_difc_sukuk_lifecycle_simulation.py \
  tests/test_pythia_difc_sukuk_criticism_ledger.py \
  -q
```

Generate a lifecycle simulation artifact:

```bash
PYTHONPATH=python_backend python scripts/simulate_difc_sukuk_lifecycle.py \
  --output artifacts/difc_audit/latest/sukuk_lifecycle_simulation.json
```

Generate a compact lifecycle summary:

```bash
PYTHONPATH=python_backend python scripts/simulate_difc_sukuk_lifecycle.py \
  --compact \
  --output artifacts/difc_audit/latest/sukuk_lifecycle_summary.json
```

Render a lifecycle criticism ledger:

```bash
PYTHONPATH=python_backend python scripts/render_difc_sukuk_criticism_ledger.py \
  artifacts/difc_audit/latest/sukuk_lifecycle_summary.json \
  --output artifacts/difc_audit/latest/sukuk_lifecycle_criticism_ledger.md
```

Render a single-packet criticism ledger:

```bash
PYTHONPATH=python_backend python scripts/generate_difc_sukuk_audit_packet.py \
  --drift \
  --output artifacts/difc_audit/latest/sukuk_drift_report.json

PYTHONPATH=python_backend python scripts/render_difc_sukuk_criticism_ledger.py \
  artifacts/difc_audit/latest/sukuk_drift_report.json \
  --output artifacts/difc_audit/latest/sukuk_drift_criticism_ledger.md
```

Verify the single packet:

```bash
PYTHONPATH=python_backend python scripts/verify_difc_sukuk_audit_packet.py \
  artifacts/difc_audit/latest/sukuk_drift_report.json
```

---

## Demo narrative for Pinsent Masons / DIFC / bank pilots

Use this sequence:

1. Show the clean staged Sukuk packet.
2. Show the lifecycle simulation and point to step 03 as the first warning.
3. Show step 04 as the first blocker state.
4. Render the Markdown criticism ledger for a Shariah scholar / trustee / compliance audience.
5. Verify the packet hash using the independent verifier.
6. Emphasise that the system never makes the human decision.

Client-safe phrasing:

> PYTHIA provides a read-only Sukuk criticism ledger. It receives evidence, applies AAOIFI-tagged review screens, surfaces warnings and blockers, seals the packet, and escalates to human SSSB/compliance owners. It does not issue rulings, opinions, approvals, filings, or operational instructions.

---

## Remaining before a pilot

Before an external pilot, the engineering/product checklist is now narrower:

1. client-approved threshold configuration;
2. counsel and Shariah scholar review of review tags;
3. client evidence schema mapping;
4. external replay pack with sample input data;
5. optional read-only web UI over the Markdown ledger;
6. standalone packaging exercise that replaces the current `pythia_mining.finance_sovereign_audit` adapter with a product-neutral adapter.

---

## Claim boundary

This remains a screening and evidence-packet prototype. It is not legal advice, regulatory advice, religious advice, investment advice, capital advice, credit advice, trading advice, or an operational transaction system.
