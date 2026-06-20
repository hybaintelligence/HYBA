# HYBA Monitoring and Alerting Baseline

**Scope:** backend API, frontend reachability, mining pool connectivity, security posture, PYTHIA evidence visibility, and local-first operations.

## Required Signals

| Domain | Signal | Alert Condition |
|---|---|---|
| Backend | `/api/health/readiness` | non-200 or `status` not ready |
| Backend | request error rate | sustained 5xx or validation spike |
| Auth | failed login count | repeated failures by source/operator |
| Security | `scripts/check_forensic_gap_closure.py` | any failure |
| Secrets | `scripts/check_secret_hygiene.py` | any failure |
| PYTHIA evidence | newest `runtime/evidence/pythia_autonomy/*.json` | missing after backend boot |
| Mining | pool connectivity | no active configured pool when live mode expected |
| Mining | accepted/rejected share telemetry | rejection spike or accepted-share stall |
| Database | connection errors | any repeated connection failure |
| Frontend | build/start smoke | Vite build/start failure |

## Local Baseline Commands

```bash
python scripts/check_forensic_gap_closure.py
python scripts/check_secret_hygiene.py
python scripts/run_local_security_scan.py
curl -s http://127.0.0.1:3001/api/health/readiness
curl -s http://127.0.0.1:3001/api/health/startup-self-healing
```

## Prometheus/Metric Expectations

When Prometheus is enabled, export at minimum:

- HTTP request count by method/path/status.
- HTTP latency histogram.
- backend readiness gauge.
- auth failure counter.
- pool connection state gauge.
- share submitted/accepted/rejected counters.
- PYTHIA startup self-healing completed gauge.
- PYTHIA latest evidence timestamp.
- security gate last-run status.

## Alert Severity

| Severity | Example |
|---|---|
| SEV-1 | exposed credential, backend unavailable, unauthorized admin access |
| SEV-2 | repeated auth failures, mining pool outage, evidence persistence failure |
| SEV-3 | optional scanner missing, non-critical telemetry lag |

## Operator Rule

If a signal cannot be monitored automatically in the current local deployment, it must be checked manually and recorded in `runtime/evidence/operator_checks/<timestamp>.md`.
