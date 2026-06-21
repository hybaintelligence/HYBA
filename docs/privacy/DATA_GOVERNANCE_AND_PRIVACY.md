# Data Governance and Privacy

## Purpose

This document closes the repository-level privacy and governance gap for enterprise readiness. It defines the minimum data controls that must be maintained before production customer data is processed.

## Data classes

| Class | Examples | Required controls |
|---|---|---|
| Operational telemetry | request IDs, correlation IDs, status codes, latency | No raw secrets; bounded retention; dashboard access controls |
| Audit events | auth boundary results, API posture rejections, governance gates | Central log sink in production; incident review retention |
| Customer account data | tenant identifiers, contact metadata, subscription state | Hash or surrogate keys in metrics; least-privilege storage access |
| Compute and mining workflow data | pool profile, job state, proof and evidence packets | Separate operational evidence from customer secrets |
| Sensitive configuration | API keys, JWT secrets, database URLs | Managed secret store only; never commit to repo |

## Repository controls implemented

- Metrics use tenant hashes rather than raw customer identifiers.
- Request and correlation IDs are propagated for traceability.
- Audit events are structured and low-cardinality.
- Security baseline requires managed secrets and log-retention controls.
- Enterprise gap closure gate blocks unsupported certification claims.

## Production requirements

Before live enterprise data processing:

1. Confirm data processors and subprocessors.
2. Record retention periods for logs, audit events, and customer records.
3. Define deletion and export procedure for customer data.
4. Confirm database backup encryption and restore tests.
5. Confirm region and data-residency commitments per customer contract.
6. Confirm customer-notification workflow with legal and compliance owner.

## Verification

```bash
PYTHONPATH=python_backend python scripts/run_enterprise_gap_closure_gate.py
```

## Residual risk

This repository establishes the governance baseline. Final privacy closure depends on live data inventory, customer contracts, deployment region, and selected processors.
