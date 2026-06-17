# Autonomous Mining Incident Runbook

## High Constraint Violation Rate

1. Inspect `get_metrics_snapshot()` or `get_prometheus_metrics_text()` and grouped audit events by constraint name.
2. For `energy_conservation`, investigate power caps and recent search-depth changes.
3. For `information_integrity`, inspect compression-ratio proposals and rollback if drift persists.
4. Degrade to advisory mode through the operator control surface.
5. Capture the current state and audit log into `artifacts/autonomous_mining/incident_<timestamp>.json`.

## Repeated Failures and Degradation

1. Verify `consecutive_failures >= 3` and confirm the degradation audit event.
2. Review the correlated decision chain for the failing action.
3. If phi density is below `0.3`, stop autonomous execution and restore the last known-good state.
4. Require human review before re-enabling reflexive cycles.

## Operator Approval Timeout

1. Treat missing approval as automatic rejection.
2. Confirm `operator_approval_completed` is logged with `rejected`, the timeout reason, and any operator ID supplied by the approval service.
3. Escalate to the on-call operator if repeated timeouts occur in one hour.
4. Continue operation with conservative advisory defaults.

## Rollback

Use the rollback CLI with an operator identity and reason:

```bash
python scripts/autonomous_mining_rollback.py \
  --state artifacts/autonomous_mining/backups/reflexive_state_<timestamp>.json \
  --operator ops-team \
  --reason "phi_density_drift_incident"
```

Validate the checksum file when present and keep the rollback audit event with the incident ticket.
