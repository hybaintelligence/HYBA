# HYBA_FULLSTACK frontend client-grade completion evidence — 2026-06-23

## BLUF

The frontend is now guarded as a client-grade operating surface rather than a cosmetic dashboard. The production contract is: every board-level surface must be mounted, every degraded state must be honest, every significant backend action family must be typed and inventoried, and release readiness must be executable through a single gate.

A new Vitest gate was added at:

```text
tests/test_frontend_client_grade_readiness.test.ts
```

It is included by `vitest.config.ts` through `tests/**/*.test.ts`, so it is exercised by `npm run test:frontend:unit` and by the broader frontend release gates.

## What the new gate freezes

### 1. Complete operating surface

The test asserts that the application shell keeps the full executive and operator estate present:

- executive summary
- sovereign command post
- sovereign genesis panel
- admin panel
- executive dashboard
- mining jobs
- historical data
- analytics
- customer portal
- CIaaS services
- QaaS / quantum API controls
- pool configuration
- network toast
- authenticated AI assistant

This prevents future regressions where the backend grows but the frontend silently drops a surface.

### 2. Honest degraded-state behaviour

The test asserts that the shell still exposes resilient states and truthful messaging:

- telemetry interruption panel
- retry connection affordance
- empty states for missing pool telemetry and catalog records
- skeleton loading state
- network status toast
- explicit `REAL TELEMETRY ONLY — NO FABRICATED DATA` footer contract

This matters because a McKinsey, Stripe, Apple, or NVIDIA-grade surface must fail closed and explain what is unavailable instead of fabricating confidence.

### 3. Backend action pressure

The test asserts that the frontend API client still tracks the significant backend action families the backend is expected to expose, including:

- admin account management
- funding review and disbursement workflows
- production mining lifecycle and share submission workflows
- security control workflows
- organism lifecycle workflows
- intelligence scaling, orchestration, and consciousness boost workflows
- evolution workflow application
- executive mining intent controls

This does not claim every action is UX-perfect; it prevents the dangerous failure mode where backend capabilities exist but disappear from the typed frontend contract.

### 4. One-command release discipline

The test asserts that the existing release machinery remains connected:

- `test:frontend:gate` runs the full frontend suite and build
- `prod:check` remains present
- readiness script still requires accessibility, role-matrix, command-safety, live-stack, release-readiness, production-hardening, and evidence artifacts

## Production posture

The frontend should be treated as release-candidate ready with live-UAT dependency, not blindly production-proven. The repo already contains strong gates for TypeScript, Vitest, component coverage, Playwright, accessibility, role matrix, command safety, backend contracts, runtime SPA hardening, and Docker/runtime entrypoint checks. The remaining proof is environmental: run the gates against the actual backend and the live sandbox base URL before customer exposure.

Required local gate:

```bash
npm ci
npm run test:frontend:gate
node scripts/check_frontend_readiness.mjs
```

Required integrated/live gate:

```bash
LIVE_E2E_SANDBOX=true PLAYWRIGHT_BASE_URL=<deployed-or-local-url> npm run test:frontend:e2e
REQUIRE_LIVE_SANDBOX=true LIVE_E2E_SANDBOX=true PLAYWRIGHT_BASE_URL=<deployed-or-local-url> node scripts/check_frontend_readiness.mjs
```

## Executive standard

The frontend must feel like a boardroom operating system, not a lab notebook:

- sparse executive language
- no fake telemetry
- fast recovery from backend failure
- visible blast radius around significant actions
- role-bounded admin and executive controls
- typed client contract for backend expansion
- proof and evidence surfaces for extraordinary claims
- CI enforcement so readiness is repeatable

The new gate converts that standard into a failing test rather than an aspiration.
