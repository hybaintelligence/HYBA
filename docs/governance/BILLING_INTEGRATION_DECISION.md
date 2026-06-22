# Billing Integration Decision

Date: 2026-06-22
Owner: Agent B

## Decision

HYBA uses Option 2: direct wrapping of metered execution calls. Customer-facing QaaS, QIaaS, and CIaaS execution paths call `execute_with_billing(...)`, which meters quota before the workload and automatically records a rollback/refund if execution raises.

## Evidence

- Implementation: `python_backend/hyba_genesis_api/api/billing_integration.py`
- QaaS wiring: `python_backend/hyba_genesis_api/api/quantum_as_a_service.py`
- QIaaS wiring: `python_backend/hyba_genesis_api/api/quantum_intelligence_service.py`
- CIaaS wiring: `python_backend/hyba_genesis_api/api/computational_intelligence_service.py`
- Tests: `tests/test_billing_integration.py`

## Rationale

Direct wrapping is the lowest-risk path because it preserves existing service business logic and constrains billing changes to the customer-facing metered boundaries. The wrapper emits fixed audit fields and draft invoice evidence for successful executions, while failed executions refund quota and add rollback records through `BillingRollbackManager`.
