# Local Governance PR Posture

This branch should be reviewed as local-first governance closure, not CI-dependent closure.

## Summary

This closes the production-readiness governance gaps identified in the proactive validation-tier review using HYBA's actual operating model: local validation, local transcripts, and local merge discipline.

## Mandatory local command

```bash
python scripts/run_local_governance_gate.py
```

## Operating rule

No merge, external deck/export/email/public post/partner script/sovereign proposal, mining stage promotion, or production-readiness claim may proceed without a passing local governance transcript.

## Boundary

This does not claim HYBA mining is production-commercial. It keeps revenue, hashrate, ASIC, firmware, sovereign, SLA, warranty, accepted-share, and production claims blocked until evidence stage gates pass.
