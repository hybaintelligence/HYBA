# Local-First Governance Closure

HYBA does not depend on paid GitHub CI for the claim-tier and commercialization controls in this branch.

The closure model is:

1. local scripts enforce the rules;
2. the local runner writes a timestamped transcript;
3. the transcript becomes the operating evidence for merge, export, pitch, publication, stage promotion, and production-readiness review;
4. the evidence manifest and mining commercialization gates remain authoritative for what may actually be claimed.

## Mandatory command

```bash
python scripts/run_local_governance_gate.py
```

## Gate semantics

- `PASS`: the local claim-tier and commercialization-stage controls passed at the time of execution.
- `FAIL`: no merge, no external distribution, no publication, no mining commercialization promotion, and no production-readiness claim.

## What this closes

- External decks/emails/posts cannot bypass the repo source-of-truth rule.
- Same-stem exports are blocked unless an approved markdown source exists.
- HYPOTHETICAL claims cannot be textually promoted to prototype, production, revenue, field, SLA, ASIC, or sovereign-ready status without manifest evidence.
- Mining commercialization remains blocked at Stage 0 until the required real-world validation evidence exists.
- Governance does not rely on hosted CI availability.

## What this does not close

This does not make mining production-commercial. It prevents premature claims while the real validation evidence is produced.
