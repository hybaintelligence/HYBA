# PYTHIA DIFC / AAOIFI Sukuk Audit Demonstration

**Protocol:** `PYTHIA_DIFC_AAOIFI_SUKUK_AUDIT_V1`  
**Lift-out package:** `python_backend/pythia_finance_audit/`  
**Bridge:** `python_backend/pythia_finance_audit/difc_aaiofi_bridge.py`  
**Tests:** `tests/test_pythia_difc_aaiofi_sukuk_bridge.py`  
**Generator:** `scripts/generate_difc_sukuk_audit_packet.py`

---

## BLUF

The DIFC / AAOIFI Sukuk layer is a jurisdiction/product overlay for the existing PYTHIA Finance Sovereign Audit core. It is intentionally packaged outside `pythia_mining` so it can be lifted out later as a standalone regulated-finance evidence product.

The system may:

- receive a Sukuk candidate;
- apply DIFC/AAOIFI-tagged review screens;
- generate synthetic criticism;
- route through the existing PYTHIA audit bridge and guard boundary;
- emit a sealed JSON evidence packet;
- stage the result for human Shariah Supervisory Board, compliance, trustee, auditor, or regulator-authorised review.

The system must not:

- issue a fatwa or Shariah ruling;
- issue legal, regulatory, capital, investment, credit, or trading advice;
- approve, issue, book, trade, submit, route, file, or execute a transaction;
- replace a Shariah Supervisory Board, trustee, compliance officer, senior management, regulator, or external Shariah auditor.

---

## Why this module exists

The previous finance sovereign audit module proved the generic pattern:

```text
candidate -> invariant screens -> synthetic criticism -> immutable guard -> sealed evidence -> sovereign human authority
```

The DIFC / AAOIFI Sukuk bridge adds the missing institutional artifact: a Sukuk-specific evidence packet with review tags for AAOIFI GS 1, GS 12, and SS 17 concepts, while preserving the non-executing PYTHIA boundary.

---

## Modularity and lift-out boundary

The repo now has a dedicated package:

```text
python_backend/pythia_finance_audit/
  __init__.py
  difc_aaiofi_bridge.py
```

This package is the product boundary. It is allowed to import the current PYTHIA core adapter today, but product and jurisdiction logic must stay here.

### Dependency rule

Allowed direction:

```text
pythia_finance_audit -> pythia_mining.finance_sovereign_audit -> auditable_decision_bridge -> ImmutableInvariantGuard
```

Forbidden direction:

```text
pythia_mining -> pythia_finance_audit
```

That means the finance product can be extracted later by replacing one adapter function instead of untangling mining internals.

---

## DIFC / AAOIFI overlay screens

The bridge currently emits findings for:

| Finding | Purpose | Review tag |
|---|---|---|
| `DIFC_AAOIFI_SUBSTANCE_OVER_FORM` | Detect economic-substance drift against contractual form | GS 1 / SS 17 review tag |
| `DIFC_AAOIFI_ASSET_BACKING_OWNERSHIP` | Require asset-backing and ownership evidence | GS 12 / SS 17 review tag |
| `DIFC_AAOIFI_SPV_TRUSTEE_GOVERNANCE` | Screen SPV independence and trustee oversight | GS 12 review tag |
| `DIFC_AAOIFI_RISK_SHARING_DEBT_MIMICRY` | Generate criticism where risk-sharing looks debt-like | GS 1 / GS 12 review tag |
| `DIFC_AAOIFI_GHARAR_UNCERTAINTY` | Detect excessive uncertainty | GS 1 / SS 17 review tag |
| `DIFC_AAOIFI_SSSB_HUMAN_AUTHORITY` | Preserve human SSSB authority | GS 1 / GS 12 review tag |
| `DIFC_AAOIFI_DISCLOSURE_TRACEABILITY` | Require traceable disclosure and replay hashes | GS 1 / GS 12 review tag |
| `DIFC_AAOIFI_NO_AUTOMATIC_ACTION` | Prevent approval, issuance, trading, booking, filing, or execution | HYBA sovereign-human boundary |

`standard_reference` fields are review tags only. They are not automated clause-level legal or Shariah determinations. Exact applicability must be calibrated by counsel, a qualified Shariah authority, and authorised compliance owners.

---

## Commands

Run the DIFC / AAOIFI bridge tests:

```bash
PYTHONPATH=python_backend python -m pytest tests/test_pythia_difc_aaiofi_sukuk_bridge.py -q
```

Generate a staged Sukuk packet:

```bash
PYTHONPATH=python_backend python scripts/generate_difc_sukuk_audit_packet.py \
  --output artifacts/difc_audit/latest/sukuk_staged_packet.json
```

Generate a drifting Sukuk packet:

```bash
PYTHONPATH=python_backend python scripts/generate_difc_sukuk_audit_packet.py \
  --drift \
  --output artifacts/difc_audit/latest/sukuk_drift_report.json
```

Run both finance gates together:

```bash
PYTHONPATH=python_backend python -m pytest \
  tests/test_pythia_finance_sovereign_audit.py \
  tests/test_pythia_difc_aaiofi_sukuk_bridge.py \
  -q
```

---

## Client-safe phrasing

Use this wording:

> PYTHIA is an invariant-governed Sukuk audit evidence layer. It receives a candidate structure, applies AAOIFI-tagged criticism and traceability screens, routes the packet through a protected guard boundary, and stages sealed evidence for human SSSB/compliance review. It does not issue fatwas, legal opinions, capital determinations, approvals, transaction instructions, filings, or execution.

For a Shariah scholar:

> The system is designed to strengthen human review by surfacing substance, ownership, SPV/trustee, uncertainty, and evidence-lineage questions before a human SSSB decision. It does not replace the SSSB.

For a regulator/compliance reviewer:

> The output is replayable JSON evidence: candidate facts, overlay findings, core finance audit packet, guard decision, verdict, human-review requirement, no-action flag, and stable hash.

---

## Missing before pilot

Before any external pilot, add:

1. client-approved thresholds and evidence schema;
2. legal/Shariah review of every `standard_reference` tag;
3. independent packet verifier for `difc_aaiofi_packet_hash`;
4. sequence simulation for lifecycle drift from pre-issuance to continuity monitoring;
5. UI read-only criticism ledger for non-technical SSSB/compliance users;
6. packaging tests proving `pythia_finance_audit` can be imported without frontend or mining runtime services beyond the declared adapter.

---

## Claim boundary

This is a screening and evidence-packet prototype. It is not legal advice, regulatory advice, religious advice, investment advice, capital advice, credit advice, trading advice, or an operational transaction system.
