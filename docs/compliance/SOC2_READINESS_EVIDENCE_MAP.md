# SOC2 Readiness Evidence Map

## Position

This document is a readiness map, not a certification statement. HYBA must not claim SOC2 certification until an accredited external audit is completed.

## Evidence map

| Control area | Repository evidence | Status |
|---|---|---|
| Security monitoring | `hyba_audit_events_total`, structured JSON logs, request/correlation IDs | Repository evidence implemented |
| Change management | Pull requests, tests, governance gates, evidence pack | Repository evidence implemented |
| Availability monitoring | `/health`, `/metrics`, resilience circuit state metrics | Repository evidence implemented |
| Confidentiality | API security headers, CORS configuration, secret-store requirement | Application controls plus external dependency |
| Incident response | `docs/runbooks/OBSERVABILITY_AND_RELIABILITY.md`, support escalation workflow | Operational control documented |
| Risk assessment | `docs/ENTERPRISE_GAP_CLOSURE_EVIDENCE_PACK.md` and residual-risk fields | Operational control documented |
| Vendor/cloud controls | Cloud IAM, SIEM, managed secrets, backup policy, WAF | External deployment dependency |

## Mandatory external actions

- Engage SOC2 auditor.
- Define audit period and trust-service criteria.
- Export CI/CD, incident, access-control, and monitoring evidence.
- Attach cloud IAM, secret-store, log-retention, and backup evidence.
- Complete management assertion and auditor testing.

## Allowed claim

HYBA has a repository-level SOC2 readiness evidence map and application-layer controls that support future SOC2 preparation.

## Disallowed claim

HYBA is SOC2 certified or SOC2 compliant.
