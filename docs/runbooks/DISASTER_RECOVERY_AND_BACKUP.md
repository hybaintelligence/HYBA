# HYBA Disaster Recovery and Backup Runbook

**Scope:** local-first backend/frontend operations, database state, runtime evidence, autonomy evidence, pool config, and deployment rollback.

**PYTHIA autonomy:** preserve autonomy evidence during backup and restore. Do not delete or rewrite `runtime/evidence/pythia_autonomy/` as part of routine cleanup.

## Recovery Objectives

| Asset | RPO | RTO | Notes |
|---|---:|---:|---|
| Source repository | last commit | 30 min | recover from Git remote |
| Database | last validated backup | 2 h | PostgreSQL dump or SQLite snapshot |
| Runtime evidence | last local backup | 2 h | includes PYTHIA/security/mining evidence |
| Pool local config | latest secret store backup | 30 min | never commit live secrets |

## Backup Checklist

1. Capture Git SHA:

```bash
git rev-parse HEAD
```

2. Backup database:

```bash
# PostgreSQL example
pg_dump "$DATABASE_URL" > backups/db/hyba_$(date -u +%Y%m%dT%H%M%SZ).sql

# SQLite/local example
cp -a data/*.db backups/db/ 2>/dev/null || true
```

3. Backup evidence:

```bash
mkdir -p backups/evidence
rsync -a runtime/evidence/ backups/evidence/runtime-evidence/
```

4. Backup local-only config from your secret store/export location, not from git.

5. Run local integrity gates:

```bash
python scripts/check_secret_hygiene.py
python scripts/check_forensic_gap_closure.py
```

## Restore Checklist

1. Restore source checkout at the target commit.
2. Restore environment/secret values from the secret manager.
3. Restore database snapshot.
4. Restore evidence directory if continuity is required.
5. Start backend locally:

```bash
npm run backend:start
```

6. Verify:

```bash
curl -s http://127.0.0.1:3001/api/health/readiness
curl -s http://127.0.0.1:3001/api/health/startup-self-healing
python scripts/check_forensic_gap_closure.py
```

## Rollback Criteria

Rollback when any of the following occur:

- Auth cookies fail for operator sessions.
- Production config validator fails.
- Mining pool credentials resolve incorrectly.
- Backend readiness fails after restart.
- Evidence persistence stops writing JSON reports.

## Evidence Retention

Keep at minimum:

- 30 days of security scan transcripts.
- 30 days of PYTHIA startup autonomy evidence.
- 30 days of mining pool handshake/share telemetry.
- All incident evidence bundles until manually closed.
