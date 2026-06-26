# Docker Cloud deployment checklist

This repo builds a single production image that serves the Vite frontend through the Node bridge and starts the FastAPI backend in the same container. The bridge proxies browser `/api/*` calls to `PULVINI_BACKEND_URL` (`http://127.0.0.1:3001` inside the image), so the frontend and backend stay connected without exposing a separate browser-facing backend URL.

## Required GitHub repository secrets

Create these in **Settings → Secrets and variables → Actions → Repository secrets** or with `scripts/configure_github_docker_secrets.sh`.

| Secret | Required | Purpose |
| --- | --- | --- |
| `DOCKERHUB_USERNAME` | yes | Docker Hub account/organization used by the deploy workflow. |
| `DOCKERHUB_TOKEN` | yes | Docker Hub access token with push permission. |
| `DOCKERHUB_REPOSITORY` | yes | Image repository, for example `your-org/hyba-fullstack`. |
| `JWT_SECRET` | yes | Production JWT signing secret, at least 32 characters. Generate with `openssl rand -base64 32`. |
| `HYBA_INTERNAL_HEALTH_TOKEN` | yes | Token for `/bridge/internal/*` diagnostics. Generate with `openssl rand -base64 32`. |
| `HYBA_OPERATOR_CREDENTIALS` | yes | Semicolon-separated `username:$argon2id$...:role` entries. Use a `mining_operator` role for the mining operator account. |
| `HYBA_POOL_VIABTC_URL` | if using ViaBTC | ViaBTC Stratum URL, for example `stratum+ssl://btc.viabtc.com:3333`. |
| `HYBA_POOL_VIABTC_USERNAME` | if using ViaBTC | ViaBTC worker or account username. |
| `HYBA_POOL_VIABTC_PASSWORD` | if using ViaBTC | ViaBTC Stratum password. |
| `HYBA_POOL_NICEHASH_URL` | if using NiceHash | NiceHash Stratum URL, for example `stratum+ssl://sha256.auto.nicehash.com:443`. |
| `HYBA_POOL_NICEHASH_WORKER` | if using NiceHash | NiceHash worker name. |
| `HYBA_POOL_NICEHASH_NH_POOL_ID` | if using NiceHash | NiceHash pool id/routing value. |
| `HYBA_POOL_NICEHASH_PASSWORD` | if using NiceHash | Usually `x` unless your provider requires another value. |
| `HYBA_POOL_BRAIINS_URL` | if using Braiins | Braiins Stratum URL. |
| `HYBA_POOL_BRAIINS_USERNAME` | if using Braiins | Braiins username. |
| `HYBA_POOL_BRAIINS_PASSWORD` | if using Braiins | Braiins password. |
| `HYBA_POOL_CKPOOL_URL` | if using CKPool | CKPool Stratum URL. |
| `HYBA_POOL_CKPOOL_BTC_ADDRESS` | if using CKPool | BTC payout address. |
| `HYBA_POOL_CKPOOL_PASSWORD` | if using CKPool | Usually `x`. |
| `HYBA_MINING_AUTO_POOL_ID` | optional | Pool to auto-connect on startup: `viabtc`, `nicehash`, `braiins`, or `ckpool`. If omitted, the bridge chooses the first configured pool. |
| `HYBA_QUANTUM_CAPACITY_EHS` | optional | Startup capacity request, capped by the backend at `1.0` EH/s. |
| `HYBA_LIVE_SHARE_APPROVAL_ID` | only if live share submission is enabled | Required approval identifier when `HYBA_ENABLE_LIVE_SHARE_SUBMIT=true`. |

At least one pool profile is required before live mining deployment. Keep `HYBA_ENABLE_LIVE_SHARE_SUBMIT=false` for first production bring-up, then enable it only after an operator approval is recorded.

## CLI setup

If GitHub CLI is installed and authenticated, run:

```bash
scripts/configure_github_docker_secrets.sh
```

The script creates generated app secrets automatically and prompts for deployment and pool values. It does not print secret values after entry.

## Docker Cloud workflow

`.github/workflows/docker-cloud-deploy.yml` validates the production environment contract, builds the frontend/server bundle, builds the Docker image, smoke-starts the container, verifies `/bridge/health`, verifies backend readiness through `/api/health/readiness`, and pushes `latest` plus the commit SHA tag to Docker Hub on `main` or manual dispatch.

## Runtime flags for first bring-up

Use these defaults for a safe first deploy:

```env
NODE_ENV=production
HYBA_ENV=production
PULVINI_BACKEND_URL=http://127.0.0.1:3001
HYBA_SPAWN_BACKEND=false
HYBA_ENABLE_LIVE_STRATUM=true
HYBA_ENABLE_MINING_AUTOCONNECT=true
HYBA_ENABLE_LIVE_SHARE_SUBMIT=false
HYBA_ENABLE_AUDIT_LOGGING=true
HYBA_ALLOW_DEV_FIXTURES=false
```
