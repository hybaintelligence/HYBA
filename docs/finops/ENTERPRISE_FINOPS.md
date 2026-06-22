# Enterprise FinOps Controls

## Purpose

This document closes the repository-level financial-operations gap by defining cost telemetry, budget controls, and review cadence for production HYBA operation.

## Implemented repository signals

The telemetry layer includes billing and quota metrics:

- `hyba_billing_usage_units_total`
- `hyba_billing_estimated_charges_usd_total`
- `hyba_billing_quota_rejections_total`
- `hyba_billing_quota_remaining`

These metrics must use hashed or surrogate tenant identifiers only.

## Required production controls

- Monthly cloud budget per environment.
- Daily cost anomaly alert.
- Owner for each high-cost service.
- Customer or tenant usage dashboard.
- Quota rejection alert when production customers approach limits.
- Weekly cost review during launch phase.
- Monthly unit-economics review after stable launch.

## Cost-risk register

| Risk | Control |
|---|---|
| Autonomous workflow loops consume unexpected compute | Hard timeout, circuit breaker, quota metrics |
| Mining or heavy compute jobs exceed budget | Per-job quota, usage counter, environment budget alert |
| Logging or tracing cardinality explosion | Low-cardinality metric labels and bounded request fields |
| Customer usage exceeds plan | Quota remaining gauge and quota rejection counter |
| Cloud deployment left idle | Environment ownership and monthly review |

## Verification

```bash
PYTHONPATH=python_backend python -m pytest tests/test_enterprise_telemetry_posture.py -q
PYTHONPATH=python_backend python scripts/run_enterprise_gap_closure_gate.py
```

## Residual risk

Repository metrics are implemented. Actual budget alarms and cost dashboards must be attached to the chosen cloud billing account before production launch.
