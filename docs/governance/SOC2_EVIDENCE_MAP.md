# SOC2 Evidence Map (Not a Certification Claim)

| Criterion | Control description | Implementation file | Test file | Status |
|---|---|---|---|---|
| CC6 | API access is gated by customer API keys or admin JWTs. | `python_backend/hyba_genesis_api/api/customer_access.py`, `python_backend/hyba_genesis_api/auth/jwt_handler.py` | `tests/test_auth_boundaries.py` | implemented |
| CC6 | Security headers and CORS allowlist reduce browser/API abuse. | `python_backend/hyba_genesis_api/core/api_posture.py`, `python_backend/hyba_genesis_api/main.py` | `tests/test_security_headers.py` | implemented |
| CC7 | Billing/audit events are emitted with fixed schema for execution outcomes. | `python_backend/hyba_genesis_api/api/billing_integration.py` | `tests/test_billing_integration.py` | implemented |
| CC8 | Changes are validated through automated tests and governance gates. | `scripts/run_local_governance_gate.py` | `tests/` | partially_implemented |
| CC9 | Quota controls limit metered customer consumption and produce invoices. | `python_backend/hyba_genesis_api/api/customer_access.py`, `python_backend/hyba_genesis_api/api/billing_integration.py` | `tests/test_billing_integration.py` | implemented |
| A1 | Availability controls include health checks and graceful error boundaries. | `python_backend/hyba_genesis_api/api/health.py`, `python_backend/hyba_genesis_api/core/api_posture.py` | `tests/test_backend_health_api.py` | partially_implemented |

HYBA has not claimed SOC2 certification. This map identifies implementation evidence for future audit readiness.
