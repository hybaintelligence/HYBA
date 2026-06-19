# Canonical Documentation Map

This file is the documentation source-of-truth map for HYBA Fullstack. Use it before adding or restoring documentation so the repository does not accumulate one-off status notes, duplicate summaries, or legacy handoff files.

## Canonical Entry Points

| Need | Canonical document |
| --- | --- |
| Repository overview and documentation taxonomy | [`docs/README.md`](README.md) |
| Production readiness summary | [`docs/executive-summary/PRODUCTION_READINESS_SUMMARY.md`](executive-summary/PRODUCTION_READINESS_SUMMARY.md) |
| Production readiness evidence | [`docs/evidence/PRODUCTION_READINESS.md`](evidence/PRODUCTION_READINESS.md) |
| Production deployment quickstart | [`docs/PRODUCTION_DEPLOYMENT_QUICKSTART.md`](PRODUCTION_DEPLOYMENT_QUICKSTART.md) |
| Deployment procedures | [`docs/runbooks/deployment_procedures.md`](runbooks/deployment_procedures.md) |
| Live Stratum rollout | [`docs/runbooks/live_stratum_rollout.md`](runbooks/live_stratum_rollout.md) |
| Mining operations | [`docs/MINING_OPERATIONS.md`](MINING_OPERATIONS.md) |
| Testing guide | [`docs/TESTING_GUIDE.md`](TESTING_GUIDE.md) |
| Governance | [`docs/governance/HYBA_FULLSTACK_GOVERNANCE.md`](governance/HYBA_FULLSTACK_GOVERNANCE.md) |
| Integration fence release gate | [`docs/governance/INTEGRATION_FENCE_RELEASE_GATE.md`](governance/INTEGRATION_FENCE_RELEASE_GATE.md) |
| Controlled adaptive systems program | [`docs/governance/CONTROLLED_ADAPTIVE_SYSTEMS_SCIENCE_PROGRAM.md`](governance/CONTROLLED_ADAPTIVE_SYSTEMS_SCIENCE_PROGRAM.md) |
| Scientific innovation index | [`docs/scientific/SCIENTIFIC_INNOVATION_README.md`](scientific/SCIENTIFIC_INNOVATION_README.md) |
| Capability registry | [`docs/technical-reports/ADAPTIVE_SYSTEMS_CAPABILITY_REGISTRY.md`](technical-reports/ADAPTIVE_SYSTEMS_CAPABILITY_REGISTRY.md) |
| Research vindication evidence | [`docs/research/RESEARCH_VINDICATION_EMERGENT_COHERENCE.md`](research/RESEARCH_VINDICATION_EMERGENT_COHERENCE.md) |
| Security and secrets management | [`docs/security/secrets_management.md`](security/secrets_management.md) |
| Operational escalation and rollback | [`docs/operations/escalation_and_rollback.md`](operations/escalation_and_rollback.md) |
| Metrics and alerts | [`docs/observability/metrics_and_alerts.md`](observability/metrics_and_alerts.md) |

## Canonicalization Rules

- Prefer updating an existing canonical document over creating a new summary, status, handoff, or completion file.
- Keep transient logs, validation output, and one-time evidence in `artifacts/` or `logs/`; do not promote them into `docs/` unless they become a maintained runbook, reference, or evidence packet.
- Do not add `*_SUMMARY.md`, `*_STATUS.md`, `FINAL_*`, `SESSION_*`, or `TEST_PUSH*` files under `docs/` without first updating this map and explaining why an existing canonical document is insufficient.
- Keep duplicate topic documents in their domain directory (`governance/`, `scientific/`, `technical-reports/`, `research/`, `runbooks/`, or `deployment/`) instead of the `docs/` root.
- Preserve the repository claim boundary: deterministic structurally guided basis-selection with classical hash verification; no implication of SHA-256 quantum acceleration or unverified production telemetry.

## Legacy Documents Removed

The following root-level `docs/` files were removed because they were transient status/completion notes or duplicates of maintained domain documents:

- `docs/README_TEST_PUSH.md`
- `docs/TEST_PUSH_SUMMARY.md`
- `docs/SESSION_SUMMARY.md`
- `docs/DOCUMENT_COMPLETION_SUMMARY.md`
- `docs/INSTALL_STATUS.md`
- `docs/DEPLOYMENT_STATUS_SUMMARY.md`
- `docs/LIVE_MINING_SETUP_STATUS.md`
- `docs/SYSTEM_READY_TO_RUN.md`
- `docs/NODUS_SOLUTUS_COMPLETION_SUMMARY.md`
- `docs/FINAL_VERIFICATION_REPORT.md`
- `docs/ADAPTIVE_SYSTEMS_CAPABILITY_REGISTRY.md`
- `docs/CONTROLLED_ADAPTIVE_SYSTEMS_SCIENCE_PROGRAM.md`
- `docs/RESEARCH_VINDICATIONS.md`
- `docs/SCIENTIFIC_INNOVATION_README.md`
