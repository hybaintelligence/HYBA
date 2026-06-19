# HYBA Client Handover Readiness Index

**Date:** 2026-06-18  
**Audience:** Client executive sponsor, technical owner, security reviewer, and operations lead  
**Status:** Handover candidate with evidence-bound operating posture

## Handover Principle

The product surface must be credible under enterprise diligence: every runtime value shown to a client is either backend-attested telemetry, an explicit configuration state, or a clearly marked pending evidence item. The console must not infer revenue, accepted-share performance, thermal state, or pool performance from synthetic fixtures.

## Client-Facing Readiness Controls

| Control | Handover expectation | Evidence in this change |
| --- | --- | --- |
| Telemetry integrity | Client dashboards do not fabricate mining, revenue, share, thermal, or power data. | Analytics, jobs, and history panels now derive values from backend telemetry and render evidence-pending states when data is absent. |
| Claim discipline | Mining economics are not asserted without authenticated accounting or pool telemetry. | Analytics economics cards display “Not asserted” until backend telemetry supplies revenue and cost values. |
| Operational clarity | Empty states explain exactly why a panel is blank and what integration is required. | Jobs and historical data panels now use handover-safe empty states instead of demo records. |
| Executive posture | The interface communicates source provenance and client-safe caveats. | Analytics panel surfaces the telemetry source and states that fabricated values are prohibited. |

## Acceptance Checklist for Client Handover

1. Configure production secrets and pool credentials in the client environment.
2. Run the backend health and security endpoints with client-owned credentials.
3. Verify pool/job telemetry appears in the Mining Jobs panel.
4. Verify historical telemetry ingestion before enabling client trend review.
5. Connect accounting or pool payout telemetry before discussing revenue, cost, or profit.
6. Export the production readiness packet and share only evidence-backed claims.

## Executive Talking Points

- The platform is now safer for a Stripe/NVIDIA-grade review because client-visible operational panels no longer contain demo economics or randomized mining values.
- Revenue and profitability remain deliberately blank until backed by authenticated telemetry.
- The product posture is evidence-first: absence of telemetry is shown as an integration requirement, not hidden behind synthetic data.

## Residual Owner Actions

- Product owner: confirm final claim language for the client deck.
- Technical owner: map client telemetry fields to `health.systemMetrics`, pool records, and history records.
- Security owner: validate secrets, auth, and telemetry-source provenance in the target environment.
- Operations owner: perform a live runbook rehearsal and capture screenshots from the client deployment.
