# HYBA_FULLSTACK Production Readiness Runbook

This runbook defines the minimum gates for deploying HYBA_FULLSTACK as the separated product-facing application boundary. It intentionally keeps HYBA_Unified_Backend out of the deployment path except for contract/reference alignment.

## Target runtime

HYBA_FULLSTACK runs as:

1. React/Vite static application.
2. Express secure bridge on `PORT`, default `3000`.
3. FastAPI backend on `127.0.0.1:3001` inside the container/runtime or as a separately managed private service.
4. PYTHIA mining daemon controlled only through MIDAS mining operations.

The Express bridge is not the source of mining truth. It is the HTTP boundary, proxy, security header layer, request-ID propagator, and static asset server.

## Required deployment gates

A production deployment must not proceed unless all of these pass:

```bash
npm ci
npm run lint
npm run build
PYTHONPATH=python_backend python3 -m unittest discover -s tests -p "test_*.py"
python3 scripts/validate_production_env.py
docker build -t hyba-fullstack:release .
```

The GitHub Actions workflow `Production Readiness` runs these same categories:

- Runtime mock/static telemetry guardrails.
- Backend regression and mining validation.
- MIDAS production-control tests.
- Frontend typecheck and build.
- Production config guardrails.
- Docker image build.

## Required production environment

Required:

- `NODE_ENV=production`
- `HYBA_ENV=production`
- `JWT_SECRET`
- `HYBA_OPERATOR_CREDENTIALS` using Argon2id hashes
- `PULVINI_BACKEND_URL=http://127.0.0.1:3001` unless using a separately managed backend service
- At least one production pool URL, username, and password before live mining is enabled

Recommended:

- `HOST=0.0.0.0`
- `PORT=3000`
- `BACKEND_PROXY_TIMEOUT_MS=30000`
- `RATE_LIMIT_WINDOW_MS=60000`
- `RATE_LIMIT_MAX=100`
- `LOG_LEVEL=info`
- `HYBA_ALLOW_DEV_FIXTURES=false`
- `HYBA_ENABLE_LIVE_STRATUM=true`
- `HYBA_ENABLE_MINING_AUTOCONNECT=false`
- `HYBA_ENABLE_LIVE_SHARE_SUBMIT=false` until explicit launch approval
- `HYBA_LIVE_SHARE_APPROVAL_ID=<approval/change-control id>` when live share submission is enabled
- `HYBA_INTERNAL_HEALTH_TOKEN=<secret internal diagnostics token>` when scraping `/bridge/metrics` or `/bridge/internal/health`
- `HYBA_ENABLE_AUDIT_LOGGING=true`
- `HYBA_SECRET_MANAGER_URI=<your secret manager URI>`
- `HYBA_METRICS_ENDPOINT=<metrics scraping endpoint>`

## Operator credential standard

Production operator credentials must use Argon2id, not raw SHA-256.

```text
HYBA_OPERATOR_CREDENTIALS='operator:$argon2id$v=19$m=65536,t=3,p=4$...:mining_operator'
```

Multiple operator entries are separated with semicolons because Argon2id hashes contain commas:

```text
HYBA_OPERATOR_CREDENTIALS='ceo:$argon2id$...:ceo;miner:$argon2id$...:mining_operator'
```

Generate hashes offline or through the deployment secret-management workflow:

```bash
python3 - <<'PY'
from argon2 import PasswordHasher
print(PasswordHasher().hash("replace-with-strong-password"))
PY
```

## Mining control boundary

All mutating mining operations must pass through:

- `MIDASStateMachine`
- `MiningRequestTracker`
- `TokenBucketRateLimiter`
- `BackpressureGuard`

Mutating endpoints must include or derive:

- `X-Request-ID` or `X-Correlation-ID`
- `Idempotency-Key`

The canonical lifecycle is:

```text
IDLE -> STARTING -> RUNNING -> STOPPING -> STOPPED
```

Forced transitions are disabled in production. Missing request IDs, invalid transitions, duplicate active requests, exhausted token buckets, and active backpressure must fail closed.

Mining auto-connect is default-disabled. Pool credentials being present means the runtime is capable of connecting; it must not connect until an explicit operator/MIDAS action is issued. `HYBA_ENABLE_MINING_AUTOCONNECT=true` is an exceptional control-plane override and must not be the default launch posture.

## Regulatory separation

HYBA_FULLSTACK is the product-facing runtime boundary:

- Application UI
- Express bridge
- FastAPI application APIs
- PYTHIA mining runtime adapter
- MIDAS production controls for mining operations

HYBA_Unified_Backend remains the broader backend/research/substrate boundary:

- Metis
- Euclid
- Research substrate
- Institutional backend contracts

Do not migrate the entire Unified backend into FULLSTACK. Only migrate or clone narrowly scoped control contracts that FULLSTACK must enforce locally.

## Institutional governance boundary

HYBA_FULLSTACK is HYBA's self-financing operating substrate. It sits inside HYBA Group / Company and must not be confused with HYBA Foundation or HYBA Research.

Deployment approval must preserve these boundaries:

- HYBA Group / Company owns production operation, revenue execution, security, and runtime accountability.
- HYBA Foundation may benefit from mission funding, but it does not operate production mining runtime.
- HYBA Research owns scientific claim discipline and research-grade proof publication, but it does not become the production operations team.
- THEMIS governs compliance, evidence, allowed claims, enforcement, and regulator-ready packets.
- PULVINI provides memory compression at scale and mathematical/state certificates; it is not the governance authority.

The canonical governance note is `docs/HYBA_FULLSTACK_GOVERNANCE.md` and must be reviewed before release-candidate tagging.

## Treasury boundary

Mining operations are not treasury allocation.

Mining operation roles/scopes:

- `mining:read`
- `mining:operate`
- `ceo`
- `treasury_admin`
- `mining_operator`
- `treasury_viewer` for read-only status

Treasury allocation, custody, payroll, tax, creditor, regulatory, and solvency decisions must remain separate from mining runtime controls.

## Self-financing claim boundary

HYBA_FULLSTACK may be described as the self-financing operating substrate of HYBA only when the release posture is evidence-bound.

Allowed language:

- self-financing operating substrate;
- production runtime for PYTHIA/PYTHAGORAS mining controls;
- PULVINI memory-compression and certificate surface;
- anti-simulation guarded mining runtime;
- operator-controlled treasury-capacity engine.

Disallowed language unless separately measured, legally reviewed, and approved:

- guaranteed mining revenue;
- guaranteed hashrate;
- guaranteed solvency;
- quantum speedup over SHA-256;
- accepted shares without live pool confirmation;
- Foundation impact without Foundation measurement;
- scientific breakthrough without HYBA Research approval.

## Health checks and diagnostics

Public container/load-balancer health check:

```bash
curl -fsS http://127.0.0.1:3000/bridge/health
```

Protected detailed bridge health:

```bash
curl -fsS -H "X-HYBA-Internal-Token: <token>" http://127.0.0.1:3000/bridge/internal/health
```

Protected Prometheus metrics:

```bash
curl -fsS -H "X-HYBA-Internal-Token: <token>" http://127.0.0.1:3000/bridge/metrics
```

Backend readiness check:

```bash
curl -fsS http://127.0.0.1:3001/api/health/readiness
```

Mining status check:

```bash
curl -fsS -H "Authorization: Bearer <token>" http://127.0.0.1:3000/api/mining/status
```

## Deployment steps

1. Confirm CI is green on `main` or release branch.
2. Build the production image.
3. Inject production secrets from the deployment secret store.
4. Start the container with no dev fixtures enabled.
5. Check bridge health.
6. Check backend readiness.
7. Log in as an authorized operator.
8. Check mining status; it should be inactive before an explicit connect operation.
9. Confirm the institutional governance boundary and self-financing claim boundary are accepted.
10. Connect to a pool only after legal, treasury, security, and operational approvals are complete.
11. Monitor protected bridge metrics and MIDAS mining metrics.

## Rollback

A rollback is required if any of these happen after deployment:

- `/bridge/health` fails repeatedly.
- `/api/health/readiness` fails repeatedly.
- MIDAS state validation returns `valid=false`.
- Backpressure rejections persist beyond normal transient load.
- Invalid state transition counts increase unexpectedly.
- Pool connection attempts fail repeatedly in production.
- Share validation produces unexpected internal errors.
- Governance or self-financing claim boundaries are violated in production-facing material.

Rollback by redeploying the last green image and revoking any newly introduced operator/pool credentials if compromise or leak is suspected.

## Production readiness status

A release is production-ready only when:

- CI is green.
- Docker image builds.
- Production secrets are present outside source control.
- Operator credentials use Argon2id hashes.
- Dev fixtures are disabled.
- Mining auto-connect is disabled unless explicitly approved.
- At least one live pool credential set is valid if mining is to be activated.
- Regulatory separation is accepted by the accountable operator.
- Institutional governance boundary is accepted by the accountable operator.
- Self-financing claim boundary is accepted by the accountable operator.
- Monitoring and rollback ownership are assigned.
