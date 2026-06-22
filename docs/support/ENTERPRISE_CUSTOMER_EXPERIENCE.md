# Enterprise Customer Experience Operating Model

## Purpose

This document closes the repository-level customer-experience gap by defining how enterprise customers are supported, updated, and escalated during production operation.

## Customer-facing artifacts

Minimum customer pack:

- Service description and supported APIs.
- Status page URL or internal incident broadcast channel.
- Support contact and escalation path.
- SLA/SLO statement tied to measured evidence.
- Maintenance-window notice process.
- Security and privacy contact.

## Support severity matrix

| Severity | Definition | Response target | Required action |
|---|---|---:|---|
| SEV1 | Customer-facing outage or data-risk event | 15 minutes | War room, status update, owner assigned |
| SEV2 | Major feature degraded or repeated workflow failure | 1 hour | Incident owner, customer update, mitigation plan |
| SEV3 | Non-critical defect or delayed workflow | 1 business day | Ticket, triage, release target |
| SEV4 | Question, documentation request, enhancement | 3 business days | Backlog or documentation update |

## Status updates

For SEV1/SEV2, publish updates with:

- Current state.
- Customer impact.
- Workaround if available.
- Next update time.
- Reference request/correlation IDs where relevant.

## Repository evidence

- Runtime request IDs and correlation IDs: `python_backend/hyba_genesis_api/core/telemetry.py`.
- Operational runbook: `docs/runbooks/OBSERVABILITY_AND_RELIABILITY.md`.
- Security baseline: `docs/security/ENTERPRISE_SECURITY_BASELINE.md`.
- Gap closure evidence pack: `docs/ENTERPRISE_GAP_CLOSURE_EVIDENCE_PACK.md`.

## External setup required

- Provision public or customer-specific status page.
- Provision support inbox or ticket system.
- Assign on-call ownership and escalation contacts.
- Connect incident updates to customer account ownership.

## Claim guardrail

Do not promise a contractual uptime percentage until the production telemetry, incident process, cloud topology, and support rota are live and evidenced.
