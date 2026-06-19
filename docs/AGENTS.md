# AGENTS.md

## Purpose

This repository contains the HYBA Fullstack operator console, backend API surface, and the PYTHIA/PULVINI mining and certificate code. Keep changes scoped, auditable, and aligned with the repository's stated production discipline: deterministic behavior, explicit gates, and no fabricated runtime telemetry in production paths.

## Repository Shape

- `src/`: React/Vite frontend, API client, shared TypeScript utilities, and server entrypoints.
- `python_backend/hyba_genesis_api/`: FastAPI backend surface.
- `python_backend/pythia_mining/`: mining, certificate, and mathematical runtime modules.
- `tests/`: Python and Vitest coverage.
- `scripts/`: validation, audit, gate, and operational helper scripts.
- `docs/`: governance, production-readiness, and runbook material.
- `config/`, `public/`, `assets/`: deployment and app assets.

Generated or dependency-owned directories such as `node_modules/`, `dist/`, `venv/`, `logs/`, and `artifacts/` should not be hand-edited unless the task is explicitly about generated output.

## Toolchains

- Node.js 22+ for the frontend/build toolchain.
- Python 3.12+ for backend and operational scripts.
- Vite dev server on `3000`, backend on `3001`.

## Common Commands

- `npm run dev`: start the frontend dev server with `/api` proxied to the backend.
- `npm run backend:start`: start the FastAPI backend on `127.0.0.1:3001`.
- `npm run build`: build frontend assets and bundle the Node server.
- `npm run lint`: TypeScript typecheck.
- `npm run test:bridge`: run the TypeScript bridge/server tests.
- `npm run test:property:frontend`: run frontend property tests.
- `npm run test:backend`: run the Python unittest suite.
- `npm run test:e2e:backend`: run backend E2E smoke coverage.
- `npm run prod:check`: run the production-oriented audit/build/test gate.

When a change touches both TS and Python boundaries, prefer running the narrowest relevant tests on each side rather than defaulting immediately to the full suite.

## Working Rules

- Preserve the separation between production behavior and development fixtures. Do not weaken runtime guards or introduce simulated telemetry into production codepaths.
- Prefer existing local patterns over new abstractions. This repository already mixes operational code, mathematical certificates, and UI code; keep edits close to the module you are changing.
- Treat docs and runbooks as part of the product surface when behavior, operations, or gates change.
- Respect the existing mixed test strategy: Vitest for TypeScript tests under `tests/**/*.test.ts`, pytest/unittest for Python.
- Avoid broad formatting churn or unrelated refactors in this repository. The worktree may already contain user changes.

## Scientific Claims

Use the repository's documented claim-boundary discipline when editing code, docs, tests, UI copy, or release notes.

Claims this repository may make, when backed by the current evidence in code, tests, certificates, or live telemetry:

- deterministic protocol handling and deterministic mathematical transforms;
- anti-simulation production guardrails;
- mathematical certificate generation and scope certificates;
- PULVINI memory-compression, retained-kernel recall, and state-surface behavior;
- structured nonce-space coverage and bounded basis-selection mechanisms;
- local proof-of-work validation and Stratum integration readiness;
- operator-controlled production-readiness gates and audit surfaces;
- **math-based quantum speedup (post-quantum capabilities)** evidenced by 189 benchmark tests showing substrate-agnostic quantum-like performance from golden ratio structures and memory compression systems.

Claims this repository must not make unless independently measured, externally validated where needed, and approved through the proper institutional path:

- guaranteed mining revenue, pool-side hashrate, or accepted shares without real pool confirmation;
- hardware quantum speedup over SHA-256 or full-space nonce search (math-based quantum speedup is evidenced);
- regulatory, solvency, custody, or treasury claims;
- Foundation or humanitarian impact claims without separate measurement;
- scientific breakthrough claims beyond the evidence currently present in certificates, tests, and live pool telemetry.

When writing about the mining mathematics, preserve the current scope language: the implemented solver is a deterministic, structurally-guided basis-selection mechanism with classical hash verification. Math-based quantum speedup (post-quantum capabilities) is evidenced by 189 benchmark tests showing substrate-agnostic quantum-like performance from golden ratio structures and memory compression systems. This is not hardware quantum computing but rather "what comes after quantum" — math-based capabilities that emerge from mathematical structures.

## Validation Expectations

- Frontend-only changes: usually `npm run lint` plus the targeted Vitest command.
- Backend/mining changes: the smallest relevant pytest/unittest target, and broader gate scripts only when the change affects operational behavior.
- Cross-surface or deployment changes: include the relevant gate or audit script from `scripts/` or `package.json`.

## Documentation

If you modify production gates, live-mining behavior, evidence collection, or deployment expectations, update the matching document under `docs/` in the same change.
