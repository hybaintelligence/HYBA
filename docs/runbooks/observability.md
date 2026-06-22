# Observability Runbook

## Signals

HYBA FastAPI emits structured JSON logs, request trace headers, and Prometheus metrics.

## Operator checks

```bash
curl -i "$HYBA_STAGING_URL/api/health"
curl -s "$HYBA_STAGING_URL/metrics" | head
```

Expected results:

- `/api/health` returns HTTP 200 with `status`, `version`, and `timestamp`.
- Response headers include `x-request-id`, `x-correlation-id`, and `x-trace-id`.
- `/metrics` includes `request_total`, `request_duration_seconds`, and `active_requests`.

## Trace propagation

Pass an existing W3C `traceparent` header to continue a distributed trace. If no trace is supplied, HYBA creates one and returns it alongside `X-Trace-ID`.

## Circuit breaker response

Backend dependency failures must degrade as HTTP 503 with `Retry-After`, not unhandled 500s. Use this to distinguish transient dependency incidents from application defects.
