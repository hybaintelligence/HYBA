# PYTHIA Auditable Decision Bridge

## BLUF

The first external-domain push should be an audit bridge, not an action engine.
PYTHIA may inspect, criticize, reject, or stage an external recommendation, but it
must not perform the external action. The bridge creates a sealed report for
human review and keeps the Stable Core boundary intact.

## Why this is the right first domain move

Mining gave PYTHIA a deterministic training substrate. The next commercial
substrate should keep the same discipline: clear invariants, replayable evidence,
and no hidden runtime authority. The auditable decision bridge lets HYBA present
PYTHIA as a sovereign review layer over external model outputs.

This is safer and more procurement-ready than positioning PYTHIA as a tactical or
operational decision-maker. The product claim becomes:

> PYTHIA does not ask you to trust an AI recommendation. PYTHIA shows you how the
> recommendation survived criticism, invariant checks, and Stable Core guard
> review before any human signs off.

## Invariants

The initial bridge enforces five human-owned invariants:

1. `TRACEABLE_EVIDENCE` — the candidate must include traceable evidence.
2. `REVIEW_CONTROL_PRIORITY` — review controls remain senior to optimization.
3. `INFORMATION_INTEGRITY` — lineage and output hashes must be present.
4. `HUMAN_APPROVAL_FOR_MATERIAL_ACTION` — material action requires human approval.
5. `NO_AUTOMATIC_ACTION` — the bridge may reject or stage; it cannot perform the action.

These are implemented in `python_backend/pythia_mining/auditable_decision_bridge.py`.

## Guard boundary

The bridge also passes any proposed Stable Core touchpoint through
`ImmutableInvariantGuard`. If a candidate attempts to target a protected symbol
such as `validate_constraints`, the packet is rejected before staging.

## Verification commands

Run the new bridge tests:

```bash
PYTHONPATH=python_backend python -m pytest tests/test_pythia_auditable_decision_bridge.py -q
```

Run the full PYTHIA Phase IV gate:

```bash
PYTHONPATH=python_backend python -m pytest \
  tests/test_pythia_resident_wake_reproducibility.py \
  tests/test_pythia_structural_resonance_fabric.py \
  tests/test_pythia_stable_core_evidence_packet.py \
  tests/test_pythia_auditable_decision_bridge.py \
  -q
```

Generate the first staged report:

```bash
PYTHONPATH=python_backend python scripts/generate_auditable_decision_report.py \
  --output artifacts/pythia_audit_bridge/latest/review_report.json
```

Generate the adversarial rejection report:

```bash
PYTHONPATH=python_backend python scripts/generate_auditable_decision_report.py \
  --adversarial \
  --output artifacts/pythia_audit_bridge/latest/adversarial_report.json
```

## Handling rule

For external-domain recommendations:

```text
Permission granted to inspect.
Permission granted to criticize.
Permission granted to stage a sealed report.
Permission denied for automatic action.
Human review required.
```

## What this proves

The bridge proves that PYTHIA's Stable Core doctrine generalizes beyond mining:

- external recommendations are treated as candidates, not commands;
- evidence lineage is required;
- missing review evidence triggers rejection;
- protected Stable Core symbols remain immutable to self-change;
- a stable report hash supports replay and audit.
