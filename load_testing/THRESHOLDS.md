# HYBA Load Test Thresholds

* QaaS execute p95 latency: `< 500ms` at 50 concurrent users.
* Health check p95 latency: `< 200ms`.
* Error rate: `< 1%` at 50 concurrent users.

Run with `HYBA_STAGING_URL=https://<staging> python load_testing/run_load_test.py`. Without `HYBA_STAGING_URL`, the harness writes a dry-run baseline that records the missing staging dependency without fabricating latency.
