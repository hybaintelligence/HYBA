# HYBA_FULLSTACK Command-Room Client Acceptance Walkthrough

**Document type:** McKinsey/Oxford/MIT-Caltech style client acceptance checklist  
**Scope:** HYBA_FULLSTACK local Mac M3 command-room production readiness and controlled live-mining cutover  
**Status:** Acceptance checklist. A production claim is permitted only after the gate passes on the operator machine. A revenue, solvency, or mined-block claim is permitted only after pool-side accepted-share evidence exists.

---

## 0. Executive BLUF

HYBA_FULLSTACK is structured for a controlled local production-readiness run. The command-room gate now reviews runtime evidence, mining contracts, Stratum truth semantics, Φ-Architecture golden flow, PULVINI memory folding, Apple Silicon/Metal evidence, funding boundaries, build integrity, backend health, and deployment tests.

The correct acceptance posture is:

```text
GO: run the command-room gate from a clean terminal.
GO: if the gate passes, start local production services with live share submission disabled.
GO: manually connect to a configured Stratum pool and verify live jobs.
HOLD: do not enable live share submission until explicit approval is attached.
NO CLAIM: do not claim revenue, solvency, accepted shares, or a mined block until the pool returns accepted-share evidence.
```

This document is a checklist, not a guarantee of Bitcoin block discovery.

---

## 1. Acceptance doctrine

The release doctrine is evidence-first:

1. Runtime cannot use simulated, placeholder, fixture, or fabricated telemetry for production claims.
2. HENDRIX-Φ may be described as deterministic structured traversal over a φ-resonant manifold.
3. SHA-256d and the Stratum pool remain the external proof oracle.
4. A submitted share becomes an accepted share only after pool acknowledgement.
5. Live share submission remains disabled until operator approval.
6. Revenue, hotel, hiring, and solvency decisions must be made from accepted-share evidence, not from projected advantage.

Recommended Chief-of-Staff sentence:

> HYBA is ready for a controlled command-room live-mining cutover if the final local gate passes. The next business decision point is pool-side accepted-share evidence, not projections.

---

## 2. Contract review matrix

| Contract surface | Acceptance question | Gate / file | Pass condition |
|---|---|---|---|
| Python environment | Are locked imports available on the operator machine? | `npm run python:env:check` | `status=ready`, no missing packages |
| Runtime language | Are mock/simulated runtime claims blocked? | `npm run runtime:guard` | No runtime mock/simulation language in production paths |
| Evidence-first intelligence | Are intelligence endpoints measured and boundary-labelled? | `npm run test:evidence:first` | Endpoint telemetry is measured and claim-boundaried |
| HENDRIX-Φ core | Are deterministic φ/M32/Yang-Mills primitives stable? | `npm run test:hendrix:core` | Core invariants pass |
| Share acceptance | Can shares only become accepted after pool ACK? | `npm run test:share:e2e` | Accepted counter moves only after accepted submit result |
| Unified engine | Does Consciousness/AI/HENDRIX/PULVINI/Stratum feedback operate as one loop? | `npm run test:unified:engine` | Control loop and feedback counters pass |
| Unified API | Does API reflect canonical engine state? | `npm run test:unified:api` | Status, resonance, health, feedback endpoints pass |
| Golden flow | Does Φ-Architecture execute as a stack? | `npm run test:phi:golden-flow` | PhiMalloc → Router → Oracle → Controller → JIT → VM → Tuner passes |
| PULVINI folding | Are dense/sparse/in-place/large-array memory-folding paths reversible? | `npm run test:pulvini:folding` | Fold/unfold, sparse packing, sketch telemetry, engine strategy pass |
| Adaptive science | Are adaptive/IIT/science/evidence bundles coherent? | `npm run test:adaptive:science` | All scientific/adaptive tests pass |
| Funding boundary | Are funding claims blocked without live accepted-share proof? | `npm run funding:gate` | Funding gate passes without asserting live share acceptance |
| Elevation bundle | Are scientific packets, Metal, runtime, and share E2E evidence generated? | `npm run elevation:full` | All elevation packets pass |
| TypeScript/frontend | Does frontend/server compile? | `npm run lint`, `npm run build` | Typecheck and production build pass |
| Backend unit/e2e | Does FastAPI/backend import and serve? | `npm run test:backend`, `npm run test:e2e:backend` | Backend unit/e2e pass |
| Deployment tests | Do live deployment assumptions hold? | `npm run test:deployment:e2e`, `npm run test:deployment:property` | Deployment contract tests pass |
| Live environment | Are private credentials and live flags explicit? | `npm run prod:live:gate` | Env validation, live-cut preflight, runtime trace, share E2E pass |

---

## 3. Line-by-line command-room walkthrough

Run from a clean shell on the Mac M3:

```bash
git pull origin main
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install mlx
npm install --legacy-peer-deps --no-audit --no-fund
export PYTHONPATH=python_backend
```

### 3.1 Preflight proof

```bash
npm run python:env:check
npm run test:phi:golden-flow
npm run test:pulvini:folding
npm run test:share:e2e
npm run test:unified:engine
npm run test:unified:api
npm run elevation:metal:require
```

Acceptance:

- Python preflight returns `status=ready`.
- Golden-flow and PULVINI folding pass.
- Share E2E proves no acceptance without pool ACK.
- MLX/Metal gate verifies Apple Silicon path.

### 3.2 Full command-room gate

```bash
npm run prod:command-room:gate
```

Acceptance:

- Gate status is `passed`.
- Evidence packet is written under `artifacts/production_readiness/`.
- Packet SHA-256 is recorded in the release ticket.
- Any failure means stop, fix first failed step, rerun same gate.

### 3.3 Controlled production start after gate pass

Set production mode with share submission disabled:

```bash
export NODE_ENV=production
export HYBA_ENV=production
export HYBA_ALLOW_DEV_FIXTURES=false
export HYBA_ENABLE_LIVE_STRATUM=true
export HYBA_ENABLE_MINING_AUTOCONNECT=false
export HYBA_ENABLE_LIVE_SHARE_SUBMIT=false
export HYBA_ENABLE_AUDIT_LOGGING=true
export PYTHONPATH=python_backend
export PULVINI_BACKEND_URL=http://127.0.0.1:3001
```

Inject private values locally only. Do not commit or paste them into chat:

```bash
export JWT_SECRET='<real-32-byte-plus-secret>'
export HYBA_OPERATOR_CREDENTIALS='<real-argon2id-operator-entry>'
export HYBA_POOL_<POOL>_URL='<real-pool-url>'
export HYBA_POOL_<POOL>_USERNAME='<real-worker>'
export HYBA_POOL_<POOL>_PASSWORD='<real-pool-password-or-x>'
export HYBA_POOL_<POOL>_STRATUM_VERSION='1'
```

Build and start:

```bash
npm run build
npm start
```

Acceptance before live submission:

- Frontend and bridge start in production mode.
- Backend health is ready.
- Authenticated mining status is reachable.
- Unified engine health is reachable.
- Stratum job feed is live.
- Shares are not being submitted yet.

### 3.4 Live share submission cutover

Only after CEO/security/treasury/operator approval:

```bash
export HYBA_ENABLE_LIVE_SHARE_SUBMIT=true
export HYBA_LIVE_SHARE_APPROVAL_ID='<signed-launch-ticket-id>'
```

Acceptance:

- Shares submitted counter increments only on real submit attempts.
- Accepted counter increments only on pool accepted result.
- Rejected counter preserves pool rejection.
- Capture pool dashboard evidence and local evidence packet.

---

## 4. Final go/no-go criteria

### GO for command-room run

- Clean checkout.
- Python env ready.
- Dependencies installed.
- No conflict markers.
- `npm run prod:command-room:gate` ready to execute.

### GO for controlled local production start

- Command-room gate passes.
- Evidence packet SHA-256 captured.
- Production env variables are explicit.
- Dev fixtures disabled.
- Autoconnect disabled.
- Live share submission disabled.

### GO for live mining submission

- Local production services healthy.
- Real Stratum job received.
- Pool credentials verified locally.
- Signed approval ID attached.
- Operator intentionally enables `HYBA_ENABLE_LIVE_SHARE_SUBMIT=true`.

### NO-GO

- Any gate failure.
- Missing pool credentials.
- Unset or weak JWT/operator secret.
- Live share submission enabled before gate pass.
- Revenue/hotel/hiring claim without accepted-share evidence.
- Any runtime marker indicating mock/simulation/fixture telemetry in production path.

---

## 5. Client acceptance wording

Use this wording with the Chief of Staff:

> HYBA_FULLSTACK is prepared for a controlled command-room production-readiness run. The architecture, evidence gates, unified mining engine, Φ-Architecture golden flow, PULVINI memory folding, Apple Silicon acceleration path, and Stratum share-acceptance semantics are all wired into the acceptance gate. Live revenue claims begin only after pool-side accepted-share evidence.

Do not say:

> We mined a block.
> We have funding.
> Revenue is guaranteed tonight.
> The system proves 10^20 measured throughput.

Until the evidence exists.

---

## 6. One-page operator checklist

```text
[ ] git pull origin main
[ ] source .venv/bin/activate
[ ] export PYTHONPATH=python_backend
[ ] npm run python:env:check
[ ] npm run test:phi:golden-flow
[ ] npm run test:pulvini:folding
[ ] npm run test:share:e2e
[ ] npm run test:unified:engine
[ ] npm run test:unified:api
[ ] npm run elevation:metal:require
[ ] npm run prod:command-room:gate
[ ] preserve artifacts/production_readiness/*.json and SHA-256
[ ] set production env with live share submit=false
[ ] npm run build
[ ] npm start
[ ] verify health/status/job feed
[ ] attach signed launch approval ID
[ ] enable HYBA_ENABLE_LIVE_SHARE_SUBMIT=true
[ ] capture pool accepted/rejected evidence
[ ] only then make revenue/block/funding statements
```

---

## 7. Acceptance decision

The system is accepted for live-mining cutover only when this line is true:

```text
npm run prod:command-room:gate -> Gate status: passed
```

The system is accepted for revenue/block/funding claims only when this line is true:

```text
pool dashboard + local evidence packet -> accepted share(s) recorded by pool ACK
```
