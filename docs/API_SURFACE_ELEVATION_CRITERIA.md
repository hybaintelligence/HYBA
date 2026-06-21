# API Surface Elevation Criteria - Falsifiable Definitions

This document defines "elevation" in falsifiable, testable terms for the HYBA API surface across all five domains. Each criterion maps to specific automated behavioral tests, not prose.

## Elevation Definition

An API endpoint is "elevated" when it passes **all** of the following behavioral tests:

### 1. Authentication & Authorization Boundaries
- **Test**: Endpoint returns 401 when called without valid authentication
- **Test**: Endpoint returns 403 when called with insufficient role permissions
- **Test**: Endpoint accepts requests with valid authentication and sufficient roles
- **Falsifiable**: `pytest tests/test_*_auth.py::test_endpoint_requires_auth -v`

### 2. Input Validation (Closed Schema)
- **Test**: Endpoint returns 422 for malformed payloads (missing required fields, wrong types, constraint violations)
- **Test**: Endpoint returns 422 for out-of-bounds values (negative where positive required, strings exceeding max length)
- **Test**: Endpoint accepts valid payloads and processes them correctly
- **Falsifiable**: `pytest tests/test_*_validation.py::test_invalid_payload_rejected -v`

### 3. Error Handling & Response Shape
- **Test**: Error responses include structured error payload with code, message, request_id, status_code
- **Test**: Error responses include enterprise security headers (X-Request-ID, Cache-Control)
- **Test**: Success responses match documented frontend contract shape
- **Falsifiable**: `pytest tests/test_*_contracts.py::test_error_response_shape -v`

### 4. Credential Redaction
- **Test**: Secrets (passwords, API keys, tokens) are never returned in API responses
- **Test**: Secrets are redacted to `<configured>` or similar placeholder in responses
- **Test**: Secrets persist only in private runtime files, not in response bodies
- **Falsifiable**: `pytest tests/test_*_redaction.py::test_credentials_redacted -v`

### 5. Idempotency
- **Test**: Repeated requests with same idempotency key return identical responses
- **Test**: Idempotency key reuse with different payload returns 409 conflict
- **Test**: Idempotency cache respects TTL (24h default)
- **Falsifiable**: `pytest tests/test_*_idempotency.py::test_idempotent_requests -v`

### 6. Rate Limiting & Posture
- **Test**: Requests exceeding rate limit return 429 with retry-after header
- **Test**: Oversized request bodies (exceeding max_body_bytes) return 413 before route handler
- **Test**: Rate limiting is per-client (identified by API key or JWT subject)
- **Falsifiable**: `pytest tests/test_*_posture.py::test_rate_limiting -v`

### 7. Negative Path Coverage
- **Test**: Endpoint handles missing resources (404) correctly
- **Test**: Endpoint handles concurrent operations (409 conflict) correctly
- **Test**: Endpoint handles service unavailability (503) with degraded mode if applicable
- **Falsifiable**: `pytest tests/test_*_negative_paths.py::test_404_handling -v`

## Domain-Specific Criteria

### Mining Operations Domain
- **Endpoints**: `/api/mining/*`
- **Additional Criteria**:
  - Pool configuration validation against known pool IDs (viabtc, ckpool, etc.)
  - BTC address format validation (base58check, checksum verification)
  - Hashrate cap enforcement (PULVINI_HASHRATE_CAP_EHS)
  - Job search pagination (limit/offset validation)
  - Telemetry source attribution (live_api vs cached)
- **Current Status**: ✅ 8/8 behavioral tests passing in `test_mining_operations_api_contracts.py`

### Command Room Domain
- **Endpoints**: `/api/admin/*`, `/api/executive/*`
- **Additional Criteria**:
  - Admin-only endpoints reject non-admin roles (403)
  - Executive endpoints require CEO or executive-level roles
  - Audit trail logging for all administrative actions
  - Configuration changes require confirmation/review
- **Current Status**: ⚠️ No behavioral tests exist

### Intelligence/Mathematics Domain
- **Endpoints**: `/api/admin/millennium-mathematics/*`, `/api/v1/fault-tolerant-computers/*`
- **Additional Criteria**:
  - Quantum workload validation (circuit_depth bounds, logical_qubits limits)
  - PHI resonance analysis returns mathematical alignment score (0-1)
  - Surface code cycles return syndrome statistics
  - Evidence seals include request hash and metadata
- **Current Status**: ⚠️ No behavioral tests exist

### Customer/Commercial Domain
- **Endpoints**: `/api/v1/computational-intelligence-services/*`, `/api/customer/*`
- **Additional Criteria**:
  - API key authentication (X-API-Key header validation)
  - Tenant isolation (customers cannot access other customers' resources)
  - Quota enforcement (compute units, request limits)
  - Usage metering recorded per workload
  - Billing events generated on successful operations
- **Current Status**: ⚠️ No behavioral tests exist

### Security/Regeneration Domain
- **Endpoints**: `/api/security/*`, `/api/regeneration/*`
- **Additional Criteria**:
  - Security event logging (authentication failures, authorization failures)
  - Regeneration operations require elevated permissions
  - Swarm operations validate swarm membership
  - Blockchain operations validate chain state
  - Autogenous operations validate system state
- **Current Status**: ⚠️ No behavioral tests exist

## Maturity Scorecard (Falsifiable)

An API domain achieves a maturity level when **all** endpoints in that domain pass the corresponding test suite:

| Level | Criteria | Test Command |
|-------|----------|--------------|
| **Level 1: Authenticated** | All endpoints require authentication and return 401 without it | `pytest tests/test_*_auth.py -v` |
| **Level 2: Authorized** | All endpoints enforce role-based access control (403 for insufficient roles) | `pytest tests/test_*_authz.py -v` |
| **Level 3: Validated** | All endpoints reject invalid payloads with 422 | `pytest tests/test_*_validation.py -v` |
| **Level 4: Contract-Compliant** | All endpoints return documented response shapes | `pytest tests/test_*_contracts.py -v` |
| **Level 5: Secure** | All endpoints redact credentials and enforce rate limiting | `pytest tests/test_*_security.py -v` |
| **Level 6: Production-Ready** | All endpoints pass negative path, idempotency, and error handling tests | `pytest tests/test_*_production.py -v` |

## Current State

- **Mining Operations**: Level 6 (Production-Ready) - 8/8 behavioral tests passing
- **Command Room**: Level 0 (No tests)
- **Intelligence/Mathematics**: Level 0 (No tests)
- **Customer/Commercial**: Level 0 (No tests)
- **Security/Regeneration**: Level 0 (No tests)

## Next Steps

1. Create behavioral contract tests for Command Room domain (`test_command_room_api_contracts.py`)
2. Create behavioral contract tests for Intelligence/Mathematics domain (`test_intelligence_math_api_contracts.py`)
3. Create behavioral contract tests for Customer/Commercial domain (`test_customer_commercial_api_contracts.py`)
4. Create behavioral contract tests for Security/Regeneration domain (`test_security_regeneration_api_contracts.py`)
5. Run full test suite: `pytest tests/test_*_api_contracts.py -v`
6. Achieve Level 6 maturity across all five domains

## Separation of Concerns

- **Executive Narrative Documentation**: `docs/API_SURFACE_EXECUTIVE_REVIEW.md` - Stakeholder communication, roadmap, governance
- **Behavioral Testing**: `tests/test_*_api_contracts.py` - Actual API verification, contract enforcement
- **This Document**: `docs/API_SURFACE_ELEVATION_CRITERIA.md` - Falsifiable definitions, maturity scorecard

**Rule**: A PR claiming "API surface elevation" must include passing behavioral tests. Documentation-only PRs should be titled "API surface documentation" and must not claim testing or elevation.
