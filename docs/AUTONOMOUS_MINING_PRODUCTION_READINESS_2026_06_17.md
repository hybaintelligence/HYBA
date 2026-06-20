# PYTHIA Autonomous Mining Production Readiness Review — 2026-06-17

## Decision

**Conditional GO** for advisory and command-room observed operation only. Unattended `supervised` or `autonomous` operation remains gated on bounded operator approval, monitoring, incident response, secret handling, rollback rehearsal, and chaos testing.

## Implemented Controls

- Guarded decisions now fail closed when an operator approval callback is absent, erroring, or slower than the configured approval timeout. Approval services may return either a boolean or a structured decision with operator ID and reason.
- Autonomy audit events include correlation IDs, decision IDs, checked constraints, violated constraints, operator action, outcome, and state diffs.
- Runtime metrics are available through `get_metrics_snapshot()`, `get_prometheus_metrics_text()`, and the scrape-protected `get_prometheus_metrics_text_cached()` using low-cardinality Prometheus names aligned with the table below. Metrics cache invalidation is event-driven for decision, degradation, approval, rollback, stale-lock, and emergency-bypass events; constraint-violation decisions invalidate immediately rather than waiting for TTL expiry.
- Reflexive state persistence uses deterministic JSON, atomic replace, SHA-256 checksum files, schema versioning, bounded backup rotation, and an in-process plus lock-file write guard to reduce state contention. Stale lock files are recovered after `HYBA_AUTONOMY_STATE_LOCK_STALE_SECONDS` seconds (default `300`) and emit both a structured audit event and `hyba_stale_state_lock_recoveries_total` for alerting.
- State recovery is exposed through `scripts/autonomous_mining_rollback.py` with operator ID and reason capture. Dry-run rollback reports whether a v1 backup will be migrated in memory on a v2 controller before any write occurs.
- Emergency bypass authority is explicitly scoped to the autonomous optimisation/reflexive layer. It does not relax SHA-256d verification, verification firewall, live-share submission gates, or nonce-coverage/search submission paths.
- Manual autonomous-circuit resets are audited with `manual_reset_within_cooldown`; repeated resets inside `HYBA_AUTONOMY_MANUAL_RESET_COOLDOWN_SECONDS` (default `300`) warn but do not block incident commanders.
- Reflexive target selection now uses bounded posterior target statistics with deterministic Thompson-style exploration. Actual pool/testnet accept/reject observations can be ingested with `record_pool_response(...)`; those observations exponentially strengthen or weaken the corresponding target evidence without bypassing local SHA-256d verification.
- Virtual mining proposal scoring is anchored to actual double-SHA-256 avalanche samples derived from deterministic proposal payloads, then damped or boosted by recent real pool/testnet response evidence. This closes the prior gap where the virtual landscape could be too idealized for live-response learning.
- Loadable Prometheus alert rules live in `alerts/pythia_mining.yaml`, and the Grafana import template lives in `dashboards/pythia_mining.json`; the markdown dashboard is explanatory only.

## Required Metrics

| Metric | Type | Alert |
| --- | --- | --- |
| `hyba_phi_density` | Gauge | warn below `0.5` |
| `hyba_constraint_violations_total` | Counter | critical above `10/hour` |
| `hyba_consecutive_failures` / `hyba_autonomous_consecutive_failures` | Gauge | critical at `>= 3` |
| `hyba_autonomous_circuit_open` | Gauge | critical at `1` |
| `hyba_autonomous_circuit_breaker_trips_total` | Counter | critical above `3/hour` |
| `hyba_degradation_events_total` | Counter | warn above `0` |
| `hyba_reflexive_cycle_duration_ms` | Histogram | warn when P99 exceeds `5000` |
| `hyba_operator_overrides_total` | Counter | warn above `5/hour` |
| `hyba_stale_state_lock_recoveries_total` | Counter | critical above `0`; a recovered lock means a writer likely crashed or was killed |

## Rollout Plan

1. Run advisory mode with `HYBA_OPERATOR_APPROVAL_REQUIRED=true` and reflexive learning disabled for the first observed window.
2. Enable reflexive learning at a conservative interval after baseline logs and metrics are stable.
3. Enter supervised mode only after approval handling, dashboard alerts, and rollback have been exercised.
4. Enter autonomous mode only after chaos scenarios have passed and operator escalation is staffed.

## Command-Room Game Day Gate

Before moving from observed command-room operation to unattended autonomous operation, run:

```bash
npm run prod:game-day
```

The rehearsal is deterministic and local-only: it does not connect to pools and submits zero shares. It intentionally triggers three circuit-breaker cascades against the autonomous controller, verifies that Prometheus text includes the degradation metrics, and confirms the autonomy level degrades to `manual` for operator escalation. Archive the JSON evidence with the incident-response notes and follow `docs/runbooks/AUTONOMOUS_MINING_INCIDENTS.md` if any assertion fails.

Also run the boundary-observability rehearsal before unattended operation:

```bash
PYTHONPATH=python_backend python scripts/command_room_game_day.py --scenario boundary_chaos --json
```

That scenario validates silent-degradation observability by forcing boundary-threshold proposal pressure, confirming proposal acceptance decays, reflexive-loop duration rises, and Prometheus text exposes both signals.

## Incident Response

See `docs/runbooks/AUTONOMOUS_MINING_INCIDENTS.md` for constraint-violation, degradation, approval-timeout, and rollback procedures.
