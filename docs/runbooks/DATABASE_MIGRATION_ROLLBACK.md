# HYBA Database Migration and Rollback Runbook

**Scope:** PostgreSQL/SQLAlchemy/Alembic migration discipline for HYBA_FULLSTACK.

## Rules

1. Every schema change must have an explicit migration file.
2. Every migration must document downgrade/rollback behaviour.
3. Every production migration requires a pre-migration backup.
4. Migration status must be recorded in the local deployment transcript.
5. PYTHIA autonomy evidence and runtime evidence are application evidence, not schema migration scratch space.

## Pre-Migration Checklist

```bash
git rev-parse HEAD
python scripts/check_forensic_gap_closure.py
python scripts/validate_production_env.py
```

Then backup:

```bash
pg_dump "$DATABASE_URL" > backups/db/pre_migration_$(date -u +%Y%m%dT%H%M%SZ).sql
```

## Migration Execution

```bash
alembic current
alembic heads
alembic upgrade head
alembic current
```

If Alembic is not the active migration tool for a local database, record the exact schema command in `runtime/evidence/migrations/<timestamp>.md`.

## Post-Migration Smoke Checks

```bash
npm run backend:check
curl -s http://127.0.0.1:3001/api/health/readiness
python scripts/check_forensic_gap_closure.py
```

## Rollback

Preferred rollback:

```bash
alembic downgrade -1
```

Emergency rollback:

```bash
psql "$DATABASE_URL" < backups/db/<known-good>.sql
```

## Required Transcript Fields

- commit SHA before migration;
- migration revision before/after;
- backup path;
- command output;
- rollback command;
- operator name;
- date/time UTC;
- health/readiness result after migration.
