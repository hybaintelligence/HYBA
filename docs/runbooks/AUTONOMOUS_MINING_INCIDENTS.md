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

## Stale State Lock Recovery

State writes use a cross-process `.lock` file. If a writer crashes, locks older than `HYBA_AUTONOMY_STATE_LOCK_STALE_SECONDS` (default `300`) are removed automatically and an audit event named `stale_state_lock_removed` is emitted. Prometheus also exports `hyba_stale_state_lock_recoveries_total`; alert on any increase because auto-recovery means a writer likely crashed or was killed. If lock contention continues after automatic stale-lock recovery, keep the controller in advisory mode, preserve the lock file as incident evidence, and inspect the PID/timestamp payload before manual removal.

## Metrics Scrape Protection

Prometheus endpoints should call `get_prometheus_metrics_text_cached()` rather than the raw exporter. The cache TTL is controlled by `HYBA_AUTONOMY_METRICS_CACHE_TTL_SECONDS` (default `5`) and prevents a misconfigured scraper from repeatedly forcing expensive φ-density recomputation. The cache is also invalidated immediately by decision, degradation, approval, rollback, stale-lock, and emergency-bypass audit events; constraint violations therefore surface on the next scrape even inside the TTL window. Set the TTL to `0` only for local diagnostics.

## Emergency Approval Bypass

Emergency approval is an explicit incident-command action, not an automatic fallback. Configure designated operators with `HYBA_EMERGENCY_OPERATOR_IDS`, require a non-empty incident reason, and preserve the `emergency_operator_bypass_approved` or `emergency_operator_bypass_rejected` audit event with the incident ticket. Missing approval callbacks still fail closed unless an authorized emergency operator deliberately records the bypass. Bypass scope is limited to autonomous optimisation/reflexive control; it must not relax SHA-256d validation, the verification firewall, live-share submission gates, or nonce-coverage/search submission paths.

## Rollback Dry Run

Before applying a rollback, validate the target state without writing it:

```bash
python scripts/autonomous_mining_rollback.py \
  --state artifacts/autonomous_mining/backups/reflexive_state_<timestamp>.json \
  --operator ops-team \
  --reason "phi_density_drift_incident" \
  --dry-run
```

Proceed without `--dry-run` only after the checksum validates and the reported epoch/history lengths match the intended recovery point. Schema behavior is explicit: v1 state restored into a v2 controller is migrated in memory (`schema_migration: v1_to_v2_in_memory`); future schema versions above the controller's supported version fail closed and require manual intervention.

## Capacity Guardrails Before Autonomous Mode

Autonomous mode remains gated by bounded proposal generation and operator-observable metrics. Keep `max_proposals_per_cycle` at a reviewed value, verify `hyba_consecutive_failures`, `hyba_degradation_events_total`, and `hyba_operator_overrides_total` are scraped, and run capacity/chaos rehearsal for disk-full, lock-stale, approval-timeout, and high-frequency proposal scenarios before unattended production use.
