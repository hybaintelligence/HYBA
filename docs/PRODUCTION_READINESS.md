# HYBA_FULLSTACK Production Readiness Runbook

This runbook defines the minimum gates for deploying HYBA_FULLSTACK as the separated product-facing application boundary. It intentionally keeps HYBA_Unified_Backend out of the deployment path except for contract/reference alignment.

## Target runtime

HYBA_FULLSTACK runs as:

1. React/Vite static application.
2. Express secure bridge on `PORT`, default `3000`.
3. FastAPI backend on `127.0.0.1:3001` inside the container/runtime.
4. PYTHIA mining daemon controlled only through MIDAS mining operations.

The Express bridge is not the source of mining truth. It is the HTTP boundary, proxy, security header layer, request-ID propagator, and static asset server.

## Required deployment gates

A production deployment must not proceed unless all of these pass:

```bash
npm ci
npm run lint
npm run build
PYTHONPATH=python_backend python3 -m unittest discover -s tests -p "test_*.py"
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
- `HYBA_OPERATOR_CREDENTIALS`
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
- `HYBA_ENABLE_LIVE_STRATUM=false` outside production or controlled staging smoke tests

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

## Health checks

Container health check:

```bash
curl -fsS http://127.0.0.1:3000/bridge/health
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
9. Connect to a pool only after legal, treasury, security, and operational approvals are complete.
10. Monitor bridge metrics and MIDAS mining metrics.

## Rollback

A rollback is required if any of these happen after deployment:

- `/bridge/health` fails repeatedly.
- `/api/health/readiness` fails repeatedly.
- MIDAS state validation returns `valid=false`.
- Backpressure rejections persist beyond normal transient load.
- Invalid state transition counts increase unexpectedly.
- Pool connection attempts fail repeatedly in production.
- Share validation produces unexpected internal errors.

Rollback by redeploying the last green image and revoking any newly introduced operator/pool credentials if compromise or leak is suspected.

## Production readiness status

A release is production-ready only when:

- CI is green.
- Docker image builds.
- Production secrets are present outside source control.
- Dev fixtures are disabled.
- At least one live pool credential set is valid if mining is to be activated.
- Regulatory separation is accepted by the accountable operator.
- Monitoring and rollback ownership are assigned.
