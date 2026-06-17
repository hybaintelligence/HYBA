# PYTHIA Finance Audit Lift-Out Manifest

## BLUF

`python_backend/pythia_finance_audit/` is the regulated-finance evidence product boundary. It may currently adapt to `pythia_mining.finance_sovereign_audit`, but all jurisdiction, product, Sukuk, DIFC, DFSA, AAOIFI, GS 12, SS 17, scholar-facing, and client-demo logic must remain inside the finance audit package or in scripts/docs that consume that package.

The product must remain an evidence generator and criticism ledger. It must not become a Shariah ruling engine, legal-opinion engine, regulatory approval engine, capital engine, trading system, booking system, issuance system, or external filing system.

## Current lift-out seams

Portable product package:

```text
python_backend/pythia_finance_audit/
```

Current narrow adapter into PYTHIA core:

```text
pythia_finance_audit.difc_aaiofi_bridge
  -> pythia_mining.finance_sovereign_audit.audit_finance_candidate
```

Canonical caller import surface:

```python
from pythia_finance_audit.difc_aaoifi_bridge import generate_difc_sukuk_audit_packet
```

Legacy-compatible implementation path:

```python
from pythia_finance_audit.difc_aaiofi_bridge import generate_difc_sukuk_audit_packet
```

## Dependency rule

Allowed today:

```text
scripts/*
  -> pythia_finance_audit
  -> pythia_mining.finance_sovereign_audit
  -> AuditableDecisionBridge / ImmutableInvariantGuard
```

Forbidden:

```text
pythia_mining -> pythia_finance_audit
frontend/product UI -> pythia_mining direct imports
DIFC/AAOIFI/Sukuk screens inside pythia_mining
external execution clients inside pythia_finance_audit
```

## What belongs in `pythia_finance_audit`

- Portable candidate dataclasses.
- DIFC/DFSA jurisdiction context.
- AAOIFI GS 1 / GS 12 / SS 17 review tags.
- Sukuk lifecycle and governance screens.
- Human SSSB/compliance escalation fields.
- Evidence packet shape.
- Stable packet hash logic.
- Product-specific criticism vocabulary.

## What must remain outside `pythia_finance_audit`

- Live trading, booking, order routing, issuance, external filing, or bank integrations.
- Legal, regulatory, or Shariah determinations.
- Clause-level automated standard interpretation without qualified human calibration.
- Secrets, client data, bank credentials, or production deployment keys.
- Mining-specific orchestration unrelated to the current adapter.

## Next extraction step

When ready to lift out, create a new repository or package with:

```text
pythia_finance_audit/
scripts/generate_difc_sukuk_audit_packet.py
scripts/verify_difc_sukuk_audit_packet.py
scripts/show_difc_sukuk_criticism_ledger.py
scripts/simulate_difc_sukuk_lifecycle_drift.py
docs/PYTHIA_DIFC_AAOIFI_SUKUK_AUDIT.md
docs/PYTHIA_FINANCE_AUDIT_LIFT_OUT_MANIFEST.md
tests/test_pythia_difc_aaiofi_sukuk_bridge.py
tests/test_pythia_difc_aaoifi_import_surface.py
tests/test_pythia_difc_sukuk_demo_scripts.py
```

Then replace the current adapter call:

```python
from pythia_mining.finance_sovereign_audit import audit_finance_candidate
```

with a standalone interface such as:

```python
class EvidenceCoreAdapter:
    def audit(self, candidate: Mapping[str, object]) -> Mapping[str, object]:
        ...
```

That keeps the product portable while still allowing the HYBA/PYTHIA core to provide stronger guard evidence when available.

## Client-safe demo path

1. Generate a staged packet.
2. Generate a drift/challenge packet.
3. Verify the packet hash and no-action boundary.
4. Render the criticism ledger for human reviewers.
5. Run the lifecycle simulation to show progressive drift detection.
6. Keep every output framed as evidence for authorised human review.

## Commands

```bash
PYTHONPATH=python_backend python scripts/generate_difc_sukuk_audit_packet.py \
  --output artifacts/difc_audit/latest/sukuk_staged_packet.json

PYTHONPATH=python_backend python scripts/generate_difc_sukuk_audit_packet.py \
  --drift \
  --output artifacts/difc_audit/latest/sukuk_drift_report.json

PYTHONPATH=python_backend python scripts/verify_difc_sukuk_audit_packet.py \
  artifacts/difc_audit/latest/sukuk_drift_report.json

PYTHONPATH=python_backend python scripts/show_difc_sukuk_criticism_ledger.py \
  artifacts/difc_audit/latest/sukuk_drift_report.json \
  --output artifacts/difc_audit/latest/sukuk_criticism_ledger.txt

PYTHONPATH=python_backend python scripts/simulate_difc_sukuk_lifecycle_drift.py \
  --output-dir artifacts/difc_audit/lifecycle
```

## Non-negotiable boundary language

Use this language externally:

> PYTHIA Finance Audit is an invariant-governed evidence layer. It receives candidate structures, applies adversarial criticism against human-owned governance boundaries, generates cryptographically sealed evidence packets, and stages the result exclusively for authorised Shariah Supervisory Board, compliance, legal, or regulatory review. It does not issue fatwas, legal opinions, regulatory approvals, capital determinations, investment recommendations, trade instructions, booking instructions, issuance approvals, or external filings.
