# Backend API Validation Status

This document records the backend API validation coverage added for frontend integration and deployment readiness.

## Coverage Added

- Health and readiness endpoints: `/health`, `/api/health`, `/api/health/live`, `/api/health/ready`, `/api/health/readiness`, and `/api/substrate`.
- Mining API endpoints: pool discovery, pool configuration, status, health, connect validation, pause/resume conflict handling, submit fail-closed behavior, and authorization enforcement.
- Intelligence API endpoints: AI consciousness status, stimulation validation, fail-closed chat behavior, v1 intelligence health/audit, and legacy path non-fabrication checks.
- Security API endpoints: security status, regeneration, swarm, blockchain threat, shield validation, and event submission behavior.

## Validation Notes

The tests use FastAPI `TestClient` through a shared helper and generate a scoped JWT for mining read/control endpoints. This keeps endpoint verification deterministic and avoids depending on an externally running server while still exercising the actual FastAPI routes, middleware, validation, and authentication dependencies.

The API suite intentionally accepts explicit degraded or unavailable states for optional runtime integrations. That preserves the repository rule that production paths must not fabricate telemetry when live mining, intelligence, or security runtimes are unavailable.
