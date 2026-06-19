# Board Tier Gate Override Policy

HYBA evidence tiers are not marketing preferences. They are operating controls.

## Default position

Overrides are disabled by default.

A claim marked `HYPOTHETICAL` may not be presented as `PROTOTYPE_VALIDATED`, `PRODUCTION_VALIDATED`, production-ready, revenue-ready, sovereign-ready, field-proven, ASIC-superior, or deployment-certified.

HYBA does not rely on paid GitHub CI for this control. The mandatory enforcement artifact is a passing local governance gate transcript produced by:

```bash
python scripts/run_local_governance_gate.py
```

## Exception request requirements

Any exception request must include all of the following before the communication is sent:

1. written CEO approval;
2. board vote record;
3. evidence manifest update;
4. counterparty written notice of the current tier;
5. post-call or post-meeting written follow-up confirming the evidence boundary;
6. legal/commercial risk note;
7. named accountable owner;
8. passing local governance gate transcript, archived or linked from the deal room.

## Automatic escalation

Escalate to CEO and board review when:

- an external deck, email, PDF, script, post, or proposal bypasses `docs/external_materials/`;
- a same-stem exported artifact has no approved markdown source;
- the local governance gate transcript is missing, failed, stale, or inconsistent with the external claim;
- a `HYPOTHETICAL` claim is verbally or textually represented as validated;
- a mining claim asserts hashrate, accepted shares, revenue, firmware licensing readiness, ASIC superiority, SLA, warranty, or sovereign production readiness before the matching stage gate unlocks.

## Consequence

The communication must be withdrawn or corrected in writing. The corrected written statement must cite the actual evidence tier and the current manifest boundary.
