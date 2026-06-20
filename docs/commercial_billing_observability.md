# Commercial Billing and Observability Runbook

## Scope

This runbook covers the production controls for customer-facing QaaS and CIaaS APIs:

- per-tenant monthly request quota enforcement;
- per-tenant monthly compute-unit quota enforcement;
- tiered and customer-overridable unit pricing;
- Prometheus metrics and Grafana panels for billing and incident visibility.

## Billing controls

Customer API keys carry a tier (`developer`, `production`, or `enterprise`), monthly request limits, monthly compute-unit limits, and an optional `metadata.pricing_usd_per_unit` map. Pricing overrides can target a full product key such as `qaas.execute`, a product family such as `qaas`, or the `default` fallback.

Metering is fail-closed: quota is checked before accepted QaaS/CIaaS work is executed. If a request would exceed monthly request or compute-unit quota, the API returns HTTP 402 and records a quota-rejection metric. Accepted work returns a usage meter with units, unit price, estimated charge, currency, and quota-enforcement status.

## Prometheus metrics

Load `/metrics` into Prometheus and alert on these low-cardinality series:

- `hyba_billing_usage_units_total{tenant_hash,product,tier}` — accepted billable units;
- `hyba_billing_estimated_charges_usd_total{tenant_hash,product,tier}` — accepted estimated usage charges;
- `hyba_billing_quota_rejections_total{tenant_hash,quota,tier}` — fail-closed quota denials;
- `hyba_billing_quota_remaining{tenant_hash,quota,tier}` — remaining monthly request and compute-unit quota;
- existing `hyba_requests_total`, `hyba_request_duration_seconds`, and `hyba_errors_total` for API health.

Tenant labels are one-way hashes to avoid exposing raw tenant identifiers in monitoring infrastructure.

## Grafana and alerts

- Import `dashboards/hyba_commercial_observability.json` for the commercial API dashboard.
- Load `alerts/hyba_billing_observability.yaml` into Prometheus Alertmanager-compatible rule management.
- During an incident, correlate quota rejections with customer plan limits before raising runtime-severity incidents.

## Operational response

1. For quota rejection spikes, verify whether the tenant is intentionally exceeding plan limits or whether an integration loop is generating unexpected traffic.
2. For commercial endpoint 5xx alerts, pause any automated billing exports until reconciliation confirms which requests were accepted.
3. Compare usage meters in API responses with Prometheus totals before invoicing disputed periods.
4. If Redis is configured and degraded, use in-process metrics for immediate customer protection and reconcile distributed counters from structured logs.
