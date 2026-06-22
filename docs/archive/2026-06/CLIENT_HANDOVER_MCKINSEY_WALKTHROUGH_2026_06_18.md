# HYBA_FULLSTACK Client Handover Walkthrough — 2026-06-18

**Document type:** executive handover, acceptance walkthrough, and end-to-end operating proof plan  
**Audience:** client sponsor, chief of staff, operator, security reviewer, and delivery owner  
**Posture:** evidence-first. This walkthrough certifies the handover process and the gates that must pass; it does not claim revenue, accepted shares, or mined blocks without pool-side evidence.

---

## 1. Executive answer

HYBA_FULLSTACK is designed as a three-layer operating system:

1. **Operator console and bridge** — React/Vite frontend plus Node server and Cloudflare adapters.
2. **FastAPI control plane** — health, auth, intelligence, mining, unified-mining, pool-management, and administration APIs.
3. **PYTHIA/PULVINI runtime** — deterministic mining, certificate, Stratum, memory, and evidence modules.

For client handover, the system is accepted only when the following chain works end to end:

```text
operator login / API authorization
  → dashboard bootstrap
  → backend health/readiness
  → mining status and job contract
  → unified runtime status
  → Stratum handshake/share semantics
  → production guardrails
  → build/typecheck
  → evidence packet or gate transcript retained
```

The key handover decision is therefore not “does the demo look good?” but “does the same command set prove the console, backend, runtime, and production guardrails together?”

---

## 2. Handover go/no-go scorecard

| Workstream | Client question | Acceptance command | Decision rule |
|---|---|---|---|
| Package registry | Can the command-room host reach the exact Python dependency pins? | `npm run python:registry:check` | Must reach PyPI or an approved mirror before dependency installation. |
| Environment | Are runtime dependencies declared and preflighted? | `npm run python:env:check` | Must fail fast with exact missing packages or return `status=ready`. |
| Frontend seed data | Does the product panel have deterministic handover records? | `PYTHONPATH=python_backend python -m pytest tests/test_products_seed_catalog.py -q` | Must return a frontend array contract populated from the seed catalog. |
| Frontend/server | Does the TypeScript surface compile? | `npm run lint` | Must pass after Node dependencies are installed. |
| Production bundle | Can the runnable web app be built? | `npm run build` | Must emit `dist/` assets and server bundle. |
| API contract | Does dashboard bootstrap hit backend contracts without 422/500 drift? | `npm run test:integration-fence` | Must pass health, readiness, mining status, job search, pool handshake, and runtime flow tests. |
| Backend smoke | Can FastAPI import and run the E2E workflow? | `npm run test:e2e:backend` | Must pass using `PYTHONPATH=python_backend`. |
| Production guardrails | Are production paths free of mock/simulated telemetry claims? | `npm run runtime:guard` | Must pass before production claims. |
| Command-room gate | Does the operator runbook pass as one controlled cutover? | `npm run prod:command-room:gate` | Must pass before controlled local production start. |

---

## 3. McKinsey-style walkthrough narrative

### 3.1 What the client sees

The operator opens the HYBA console, verifies system health, reviews intelligence and mining panels, checks pool configuration posture, and confirms that mining controls are gated by authentication and operational approval.

### 3.2 What the delivery team proves behind the scenes

Each visible console step maps to a testable control:

- Health cards map to `/api/health` and readiness checks.
- Mining status maps to authenticated mining endpoints and canonical runtime state.
- Pool configuration maps to explicit Stratum profile and handshake contracts.
- Share acceptance maps to pool acknowledgement semantics; local counters cannot fabricate accepted shares.
- Production-readiness claims map to scripts and tests, not slideware.

### 3.3 What is intentionally not claimed

The handover must not claim guaranteed Bitcoin revenue, guaranteed pool hashrate, accepted shares, mined blocks, treasury solvency, or regulatory outcomes unless separate live evidence exists. The accepted wording is:

> HYBA_FULLSTACK is ready for a controlled command-room acceptance run when the documented gates pass on the operator machine. Live revenue claims begin only after pool-side accepted-share evidence.

---

## 4. Live pool job-flow finding closed in this handover

The live pool profile gate must represent the job flow that the current daemon can actually execute. ViaBTC remains the default Stratum v1 handover profile for worker `PYTHIA.001`; the Braiins Stratum v2 profile is retained in configuration but disabled until Stratum v2 channel/job-flow support is implemented. This keeps the live profile gate focused on job-capable Stratum v1 profiles and prevents a disabled future profile from blocking ViaBTC acceptance.

## 5. Dependency hardening finding closed in this handover

During handover validation, the Python environment preflight was narrower than the backend import surface. Admin and database modules import SQLAlchemy, Alembic migration support, and Pydantic email validation support, but these packages were not declared in the canonical backend requirements lock or preflight list.

The handover fix is:

- Add `email-validator` for `EmailStr` models.
- Add `SQLAlchemy` for database sessions, ORM models, and admin/auth APIs.
- Add `alembic` for the migration surface already present in the repository.
- Add these imports to the preflight script so client acceptance fails fast before backend tests collect.

This changes the acceptance behavior from late pytest import errors to an actionable environment gate.

---

## 6. Operator runbook for handover day

Run from a clean terminal:

```bash
python -m pip install --upgrade pip
npm run python:registry:check
python -m pip install -r python_backend/requirements.txt
npm install --legacy-peer-deps --no-audit --no-fund
export PYTHONPATH=python_backend
npm run python:env:check
set -a; source .env.local; set +a
PYTHONPATH=python_backend python scripts/check_pool_profile_job_flow.py --mode live
PYTHONPATH=python_backend python -m pytest tests/test_products_seed_catalog.py -q
npm run lint
npm run build
npm run test:integration-fence
npm run test:e2e:backend
npm run runtime:guard
npm run prod:command-room:gate
```

If any command fails, stop the walkthrough, capture the transcript, fix the first failing control, and rerun the same command. Do not skip forward.

---

## 7. Client acceptance closeout

A handover is complete only when the client receives:

1. The passing command transcript or evidence packet.
2. The Git commit hash for the accepted build.
3. The environment file template with private values redacted.
4. The go/no-go decision and any open risks.
5. A written statement that no revenue or accepted-share claim is made without pool-side evidence.
