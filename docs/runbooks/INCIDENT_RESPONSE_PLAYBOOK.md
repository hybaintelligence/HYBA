# HYBA Incident Response Playbook

**Scope:** HYBA_FULLSTACK security, frontend/backend operations, pool configuration, credentials, production API posture, and operator response.

**PYTHIA autonomy:** PYTHIA self-healing/autonomy internals are not disabled by this playbook. Incident response controls the surrounding operational envelope: credentials, network exposure, API access, logs, and rollback.

## Severity Levels

| Severity | Trigger | Initial Action |
|---|---|---|
| SEV-1 | active credential exposure, unauthorized admin access, live pool abuse, data exfiltration | isolate service, rotate secrets, preserve evidence |
| SEV-2 | auth bypass, repeated 5xx failure, suspicious pool traffic, failed production gate | restrict access, capture logs, run local forensic gate |
| SEV-3 | degraded telemetry, scanner warning, failed optional dependency scan | triage during same operating day |

## First 15 Minutes

1. Preserve local evidence under `runtime/evidence/incidents/<timestamp>/`.
2. Capture command transcript, backend logs, frontend console output, and relevant JSON evidence.
3. Rotate affected secrets if any token, pool password, Firebase credential, admin password, or API key is suspected.
4. Run:

```bash
python scripts/check_secret_hygiene.py
python scripts/check_forensic_gap_closure.py
python scripts/run_local_security_scan.py
```

5. If auth is affected, force logout by rotating `JWT_SECRET` and restarting the backend.
6. If mining pool credentials are affected, rotate the worker/password at the pool provider and update only local secret storage.

## Evidence To Preserve

- Git commit SHA.
- Backend startup/shutdown logs.
- `runtime/evidence/pythia_autonomy/*.json` relevant to the incident window.
- `runtime/evidence/security_scans/*.json`.
- Pool connection and accepted/rejected-share telemetry.
- Operator commands executed.

## Recovery Criteria

- Root cause identified or bounded.
- Affected secrets rotated.
- `check_secret_hygiene.py` passes.
- `check_forensic_gap_closure.py` passes.
- Production config validator passes for production deployments.
- Backend health and readiness endpoints return expected state.
- PYTHIA autonomy evidence remains intact and auditable.

## Post-Incident Review

Produce a short review with:

- What happened.
- What was affected.
- What PYTHIA did autonomously, if relevant.
- What operator action was taken.
- What code/config/docs changed.
- Which local gates now prevent recurrence.
