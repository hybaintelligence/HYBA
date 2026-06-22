# Deployment Runbook

## Pre-deploy checklist

```bash
git status --short
python scripts/run_local_governance_gate.py
pytest tests/ -q
docker build -f Dockerfile.prod .
```

Expected output: clean worktree except intended release commit, zero governance failures, pytest passes with at least the baseline test count, and Docker build exits 0.

## Deploy

```bash
export HYBA_ENV=staging
export HYBA_IMAGE_TAG="$(git rev-parse --short HEAD)"
bash scripts/deploy-multi-cloud.sh staging
```

Expected output: deployment script completes without errors and prints the staging endpoint.

## Verify health and public surfaces

```bash
bash scripts/smoke_test.sh "$HYBA_BASE_URL"
```

Expected output: HTTP 200 for `/api/health`, `/api/v1/fault-tolerant-computers`, `/api/qiaas`, and `/api/quantum-finance/capability-map` according to the current smoke-test implementation.

## Rollback

```bash
helm rollback hyba-platform -n hyba
bash scripts/smoke_test.sh "$HYBA_BASE_URL"
```

Expected output: previous release restored and smoke checks pass.
