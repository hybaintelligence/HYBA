# HYBA Performance Tuning Runbook

## Uvicorn workers

Run production API workers with `WEB_CONCURRENCY=$((2 * CPU_CORES + 1))` and `uvicorn hyba_genesis_api.main:app --app-dir python_backend --workers "$WEB_CONCURRENCY"`.

Expected output includes one parent process and `$WEB_CONCURRENCY` worker processes. For a 2 vCPU pod, set `WEB_CONCURRENCY=5`.

## Redis and cache pools

Static capability responses use Redis when `REDIS_URL` is configured and fall back to process memory only for local development. Configure `HYBA_REDIS_MAX_CONNECTIONS` or the deployment chart equivalent to at least `100` for staging and production.

## Load validation

Run:

```bash
HYBA_STAGING_URL=https://<staging-endpoint> python load_testing/run_load_test.py
```

Expected artifact: `load_testing/results/baseline.json` containing p50, p95, p99 latency and error rate. Thresholds are documented in `load_testing/THRESHOLDS.md`.
