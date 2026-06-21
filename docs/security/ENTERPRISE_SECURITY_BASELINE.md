# Enterprise Security Baseline

## Scope

This baseline turns the security portion of the production-readiness assessment into enforceable application controls and explicit infrastructure requirements.

## Implemented in repository

Application-layer controls:

- Standard error envelope with `request_id`.
- `X-Request-ID` and `X-Correlation-ID` propagation.
- Security response headers: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, `Cache-Control`, `Cross-Origin-Opener-Policy`, `Cross-Origin-Resource-Policy`, and CSP.
- HSTS in production mode.
- Request body size rejection via `HYBA_API_MAX_BODY_BYTES`.
- In-process rate-limit backstop.
- Structured audit events for rejected API-posture paths.
- Prometheus audit counter: `hyba_audit_events_total`.

Primary files:

- `python_backend/hyba_genesis_api/core/api_posture.py`
- `python_backend/hyba_genesis_api/core/telemetry.py`
- `tests/test_enterprise_telemetry_posture.py`

## Required environment controls

These must be configured in the deployment platform before enterprise customer claims are made:

- Managed secret store for production credentials.
- Least-privilege service accounts.
- CI secret scanning and dependency audit.
- WAF or API gateway rate limits.
- Private network paths for databases and state stores.
- Central log sink with retention policy.
- SIEM integration for audit events.
- SSO/IAM integration where customers require enterprise identity.

## Verification commands

```bash
PYTHONPATH=python_backend python -m pytest tests/test_enterprise_telemetry_posture.py -q
PYTHONPATH=python_backend python scripts/run_enterprise_gap_closure_gate.py
```

## Claims policy

Allowed after this branch passes:

- HYBA has application-layer API posture controls.
- HYBA emits structured audit events for selected security-relevant paths.
- HYBA has repository evidence for security-readiness work.

Not allowed without external evidence:

- SOC2 certified.
- External penetration test completed.
- Production SIEM fully integrated.
- Enterprise SSO deployed for all tenants.
- Zero-trust architecture fully implemented across cloud infrastructure.

## Residual risks

Security/compliance remains `documented_but_external_dependency` in the closure manifest because certification, penetration testing, and cloud IAM provisioning cannot be proven from repository changes alone.
