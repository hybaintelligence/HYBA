# PYTHIA Autonomous Mining Production Readiness Review — 2026-06-17

## Decision

**Conditional GO** for advisory and command-room observed operation only. Unattended `supervised` or `autonomous` operation remains gated on bounded operator approval, monitoring, incident response, secret handling, rollback rehearsal, and chaos testing.

## Implemented Controls

- Guarded decisions now fail closed when an operator approval callback is absent, erroring, or slower than the configured approval timeout. Approval services may return either a boolean or a structured decision with operator ID and reason.
- Autonomy audit events include correlation IDs, decision IDs, checked constraints, violated constraints, operator action, outcome, and state diffs.
- Runtime metrics are available through `get_metrics_snapshot()` and `get_prometheus_metrics_text()` using low-cardinality Prometheus names aligned with the table below.
- Reflexive state persistence uses deterministic JSON, atomic replace, SHA-256 checksum files, schema versioning, bounded backup rotation, and an in-process plus lock-file write guard to reduce state contention.
- State recovery is exposed through `scripts/autonomous_mining_rollback.py` with operator ID and reason capture.

## Required Metrics

| Metric | Type | Alert |
| --- | --- | --- |
| `hyba_phi_density` | Gauge | warn below `0.5` |
| `hyba_constraint_violations_total` | Counter | critical above `10/hour` |
| `hyba_consecutive_failures` | Gauge | critical at `>= 3` |
| `hyba_degradation_events_total` | Counter | warn above `0` |
| `hyba_reflexive_cycle_duration_ms` | Histogram | warn when P99 exceeds `5000` |
| `hyba_operator_overrides_total` | Counter | warn above `5/hour` |

## Rollout Plan

1. Run advisory mode with `HYBA_OPERATOR_APPROVAL_REQUIRED=true` and reflexive learning disabled for the first observed window.
2. Enable reflexive learning at a conservative interval after baseline logs and metrics are stable.
3. Enter supervised mode only after approval handling, dashboard alerts, and rollback have been exercised.
4. Enter autonomous mode only after chaos scenarios have passed and operator escalation is staffed.

## Incident Response

See `docs/runbooks/AUTONOMOUS_MINING_INCIDENTS.md` for constraint-violation, degradation, approval-timeout, and rollback procedures.
