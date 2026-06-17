# HYBA Enterprise API Posture

## BLUF

HYBA Genesis now has an enterprise-grade API posture baseline at the application layer. The API already had a real FastAPI lifecycle, structured telemetry, substrate readiness, router separation, configurable CORS, JWT authentication, Argon2 operator credentials for production, and disabled self-service registration. This document records the enterprise controls now expected for production operation.

The application-layer posture complements cloud controls. It does not replace API Gateway, WAF/Cloud Armor, IAM, mTLS/service mesh policy, secret manager, central logging, or external SIEM.

## Existing production foundations

The backend entry point is a FastAPI application with:

- explicit app metadata and versioning;
- startup/shutdown lifespan management;
- substrate initialization and graceful shutdown;
- configurable CORS origins through `HYBA_CORS_ORIGINS`;
- explicit router registration for health, auth, intelligence, mining, products, memory, pool management, and unified mining;
- root health and substrate status endpoints;
- configurable host/port through `HYBA_BACKEND_HOST`, `HYBA_BACKEND_PORT`, and `PORT`.

Authentication posture includes:

- JWT access tokens;
- required `JWT_SECRET` in production;
- token expiry and issued-at claims;
- token IDs for revocation/blacklisting;
- production Argon2id operator credentials via `HYBA_OPERATOR_CREDENTIALS`;
- development-only fallback credentials disabled in production;
- self-service registration disabled.

Telemetry posture includes:

- structured JSON logging;
- request duration metrics;
- request IDs;
- request/error counters;
- health/readiness telemetry surfaces.

## Enterprise hardening layer

`hyba_genesis_api.core.api_posture` installs the following controls:

1. Request/correlation ID propagation.
2. Standard JSON error envelope.
3. Security headers:
   - `X-Content-Type-Options: nosniff`
   - `X-Frame-Options: DENY`
   - `Referrer-Policy: no-referrer`
   - `Permissions-Policy: camera=(), microphone=(), geolocation=()`
   - `Cache-Control: no-store`
   - production HSTS when enabled.
4. Body-size protection using `HYBA_API_MAX_BODY_BYTES`.
5. In-process fixed-window rate-limit backstop using `HYBA_API_RATE_LIMIT_PER_MINUTE`.
6. Validation-error envelope for client request failures.

## Environment variables

Required or expected for production:

```bash
NODE_ENV=production
HYBA_ENV=production
JWT_SECRET=<secret-manager-value>
HYBA_OPERATOR_CREDENTIALS='operator:$argon2id$...:operator'
HYBA_CORS_ORIGINS='https://app.hyba.ai,https://console.hyba.ai'
HYBA_API_RATE_LIMIT_ENABLED=true
HYBA_API_RATE_LIMIT_PER_MINUTE=120
HYBA_API_MAX_BODY_BYTES=2097152
HYBA_API_HSTS=true
HYBA_BACKEND_HOST=0.0.0.0
PORT=3001
```

## Production gates

The API is production-ready only when all of the following hold:

- `/health` returns HTTP 200 from the running service.
- `/api/health/ready` returns HTTP 200 only after substrate initialization completes.
- `JWT_SECRET` is configured in production.
- `HYBA_OPERATOR_CREDENTIALS` uses Argon2id hashes, not raw passwords or SHA-256 development fixtures.
- `HYBA_CORS_ORIGINS` contains explicit production origins, not `*`.
- security headers are present on successful and error responses.
- request IDs appear in logs and response headers.
- oversized bodies fail closed with HTTP 413.
- excessive calls fail closed with HTTP 429.
- gateway/WAF/IAM controls enforce the outer boundary.

## Verification commands

```bash
PYTHONPATH=python_backend python -m pytest tests/test_hyba_enterprise_api_posture.py -q
PYTHONPATH=python_backend python -m pytest tests/test_api_integration.py -q
```

Optional runtime smoke test:

```bash
curl -i http://localhost:3001/health
curl -i http://localhost:3001/api/health/ready
```

Expected enterprise headers include `X-Request-ID`, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, and `Cache-Control`.

## Residual production actions

Before an external enterprise launch, complete these infrastructure controls:

1. Put the API behind API Gateway or Cloud Run ingress with WAF/Cloud Armor.
2. Store `JWT_SECRET` and operator credentials in secret manager.
3. Configure explicit production CORS origins.
4. Add centralized Prometheus/OpenTelemetry export if not already enabled in the runtime stack.
5. Ensure Cloud Run or container deployment uses non-root runtime, resource limits, liveness/readiness probes, and least-privilege service account.
6. Keep OpenAPI exposed only where intended; otherwise gate `/docs` and `/openapi.json` at the gateway.

## Board-safe statement

HYBA Genesis exposes an enterprise API posture: authenticated operator access, production-only secret enforcement, structured telemetry, deterministic readiness, standard error envelopes, security headers, body-size limits, rate-limit backstop, and explicit production gates. The application is now hardened enough for Docker/local and ready for cloud perimeter controls before external enterprise exposure.
