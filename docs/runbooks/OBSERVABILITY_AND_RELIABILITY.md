# Observability and Reliability Runbook

## Purpose

This runbook closes the operational gap for production troubleshooting and runtime resilience. It is paired with code in:

- `python_backend/hyba_genesis_api/core/telemetry.py`
- `python_backend/hyba_genesis_api/core/api_posture.py`
- `python_backend/hyba_genesis_api/core/resilience.py`
- `tests/test_enterprise_telemetry_posture.py`
- `tests/test_enterprise_resilience.py`

## Runtime signals

The backend exposes `/metrics` in Prometheus format and `/health` for compatibility health checks. The telemetry layer emits:

- `hyba_requests_total`
- `hyba_request_duration_seconds`
- `hyba_errors_total`
- `hyba_governance_gate_status`
- `hyba_enterprise_readiness_gap_status`
- `hyba_workflow_status`
- `hyba_reliability_circuit_state`
- `hyba_audit_events_total`
- billing quota and usage counters

Every request should carry or receive:

- `X-Request-ID`
- `X-Correlation-ID`
- optional `traceparent` propagation when present

## Local verification

Run:

```bash
npm run python:env:check
PYTHONPATH=python_backend python -m pytest tests/test_enterprise_telemetry_posture.py tests/test_enterprise_resilience.py -q
PYTHONPATH=python_backend python scripts/run_enterprise_gap_closure_gate.py
```

Then start the backend and inspect metrics:

```bash
npm run backend:start
curl -s http://127.0.0.1:3001/health
curl -s http://127.0.0.1:3001/metrics | grep hyba_
```

## Production collector setup

Set the following at deployment time:

```bash
OTEL_SERVICE_NAME=hyba-genesis-api
OTEL_EXPORTER_OTLP_ENDPOINT=<collector-url>
HYBA_CORS_ORIGINS=https://<frontend-origin>
HYBA_API_RATE_LIMIT_ENABLED=true
HYBA_API_RATE_LIMIT_PER_MINUTE=120
HYBA_API_MAX_BODY_BYTES=2097152
```

The OpenTelemetry path remains optional for local tests. The Prometheus metrics endpoint is the minimum required runtime signal.

## Incident triage

1. Confirm `/health` responds.
2. Check `hyba_errors_total` and `hyba_request_duration_seconds`.
3. Filter logs by `request_id` or `correlation_id`.
4. Check `hyba_reliability_circuit_state` for dependency protection events.
5. Check `hyba_governance_gate_status` for failing gates.
6. If customer-facing impact exists, update the status page using `docs/support/ENTERPRISE_CUSTOMER_EXPERIENCE.md`.
7. Capture evidence in `docs/governance/` after the incident.

## Reliability controls

Use `CircuitBreaker` for dependency calls that can fail repeatedly, including remote model calls, mining pool calls, external billing, and governance evidence upload steps. Required pattern:

```python
breaker = CircuitBreaker("pool_profile_sync", failure_threshold=3, recovery_seconds=30)
result = await breaker.call(sync_pool_profile, timeout_seconds=5.0, retries=1)
```

Do not loop indefinitely around external calls. Every production dependency call must have one of:

- timeout
- retry bound
- circuit breaker
- fail-closed policy
- documented degraded mode

## Closure status

Repository-level observability and application reliability are closed by code and tests. External paging, managed dashboards, and multi-region failover remain environment provisioning tasks and are not claimed as completed by this runbook alone.
