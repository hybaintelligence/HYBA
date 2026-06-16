# HYBA Fullstack Local-to-Multicloud Deployment Plan

Status: working deployment plan  
Scope: this repository only  
Applies to: local Docker now, single-cloud next, Azure/GCP/AWS availability later

## Objective

Use the existing container path in this repository for low-cost local validation first, then promote the same image and runtime assumptions into managed cloud environments once the service behavior is stable and worth paying for.

This repository is already structured for that path:

- `Dockerfile` builds the application image.
- `docker-compose.production.yml` defines the three production-facing services:
  - `hyba-backend`
  - `hyba-runtime`
  - `hyba-bridge`
- `docs/CLOUDFLARE_DEPLOYMENT.md` already covers the optional Cloudflare Pages frontend path.

## Phase 1: Local Docker Now

Use local containers for a few hours at a time while validating basic behavior and keeping cost at zero.

### Minimum local goals

1. Build the image successfully.
2. Bring up the three-service stack from `docker-compose.production.yml`.
3. Verify health endpoints.
4. Verify required environment variables and secrets loading.
5. Confirm logs, restarts, and shutdown behavior.
6. Confirm the app comes back cleanly after a full stop/start cycle.

### Local commands

```bash
docker compose -f docker-compose.production.yml build
docker compose -f docker-compose.production.yml up
```

In a separate shell:

```bash
curl http://127.0.0.1:3000/bridge/health
curl http://127.0.0.1:3000/api/health/readiness
docker compose -f docker-compose.production.yml ps
docker compose -f docker-compose.production.yml logs --tail=200
```

### Local exit criteria

Do not pay for cloud until the following are true locally:

- image builds repeatably;
- health checks go green without manual patching;
- secrets are injected only through environment or secret storage;
- containers restart cleanly;
- no required state is lost unexpectedly;
- operational checks pass at the correct scope.

### Local gates

Run the narrowest relevant checks first, then the broader gates:

```bash
npm run build
npm run prod:env:check
npm run runtime:guard
npm run test:backend
npm run test:e2e:backend
```

Use `npm run prod:check` when you want the broader production-oriented gate in one pass.

## Phase 2: First Paid Cloud Deployment

Do not start with three clouds. Start with one.

The first paid target should prove:

- image registry push/pull;
- secret injection in the cloud platform;
- stable ingress and TLS;
- logs and metrics in a managed control plane;
- restart behavior under real network conditions;
- rollback discipline.

### Recommended first-cloud shape

Run this repository as three services, matching the existing compose split:

1. `hyba-bridge`: public HTTP entrypoint
2. `hyba-backend`: internal API service
3. `hyba-runtime`: internal runtime/worker service

Keep the first deployment simple:

- one region;
- one environment;
- no active-active failover yet;
- managed secrets;
- managed logs;
- health checks wired to the platform;
- image tags pinned to deployable builds.

### Why this shape

This repo already expresses separate responsibilities in Compose. Preserving that boundary makes failures easier to understand and avoids hiding cross-service issues inside one oversized container.

## Phase 3: Multicloud Availability

Once one cloud is stable, add Azure, Google Cloud, and AWS as parallel deployment targets for availability.

Do this as active-passive first, not active-active. Active-active across three clouds is expensive operationally and creates more failure modes than it removes if you do it too early.

### Recommended multicloud sequence

1. Primary cloud: live production target.
2. Secondary cloud: warm standby with validated deployment path.
3. Third cloud: cold standby or periodic validation deployment.
4. Only then consider traffic steering or cross-cloud failover automation.

### Cross-cloud rules

- Keep the container image behavior identical across providers.
- Keep environment variable names identical across providers.
- Keep health checks identical across providers.
- Keep one canonical release process.
- Keep rollback simple: previous image tag plus previous config revision.
- Do not couple failover to speculative performance claims or mining-state assumptions.

## Provider Mapping

These are the cleanest managed targets for this repo's container model.

### Azure

Use Azure Container Apps for the first managed Azure target.

Why:

- managed container platform;
- HTTPS/TCP ingress support;
- secrets support;
- revision-based deployment model;
- jobs support if later needed for isolated runtime work.

Official reference: [learn.microsoft.com](https://learn.microsoft.com/en-us/azure/container-apps/overview)

Suggested mapping:

- `hyba-bridge`: public container app
- `hyba-backend`: internal container app
- `hyba-runtime`: internal container app or job, depending on runtime behavior

### Google Cloud

Use Cloud Run for the first managed Google Cloud target.

Why:

- deploys container images directly;
- supports continuous deployment from git;
- supports custom domains, multi-region traffic patterns, and health checks;
- supports jobs separately if the runtime later needs a stronger worker model.

Official reference: [cloud.google.com](https://cloud.google.com/run/docs/overview/what-is-cloud-run)

Suggested mapping:

- `hyba-bridge`: public Cloud Run service
- `hyba-backend`: private/internal Cloud Run service
- `hyba-runtime`: Cloud Run service or Cloud Run job based on runtime lifecycle

### AWS

Use Amazon ECS on AWS Fargate for the first managed AWS target.

Why:

- runs containers without managing EC2 clusters;
- lets you define CPU, memory, networking, and IAM at the task level;
- works cleanly with load balancers for HTTP ingress.

Official reference: [docs.aws.amazon.com](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate.html)

Suggested mapping:

- `hyba-bridge`: ECS service behind an Application Load Balancer
- `hyba-backend`: internal ECS service
- `hyba-runtime`: ECS service or scheduled/on-demand task

## Frontend Delivery Options

This repo already has a Cloudflare Pages path for the frontend and edge proxying.

There are two valid patterns:

1. Keep the whole stack together behind the `hyba-bridge` container.
2. Serve the frontend from Cloudflare Pages and route API traffic to the backend origin described in `docs/CLOUDFLARE_DEPLOYMENT.md`.

Start with option 1 unless there is a real need to separate frontend delivery from the runtime stack.

## Secrets and Configuration

Before any paid deployment:

- keep `JWT_SECRET` in managed secret storage;
- keep `HYBA_OPERATOR_CREDENTIALS` in managed secret storage;
- do not commit pool credentials;
- keep `HYBA_ALLOW_DEV_FIXTURES=false`;
- keep `HYBA_ENABLE_LIVE_SHARE_SUBMIT=false` until explicit approval exists;
- record which environment variables differ between local, staging, and production.

## Release Discipline

Use the same release shape across clouds:

1. Build immutable image.
2. Run repo gates.
3. Push tagged image.
4. Deploy to staging or standby target.
5. Verify health endpoints.
6. Promote to primary.
7. Keep the previous image tag available for rollback.

## Practical Recommendation

For this repository:

1. Use local Docker now for repeated short sessions.
2. Move to one paid cloud only after local behavior is stable.
3. Add Azure, Google Cloud, and AWS as managed replicas only after the first cloud is boring.
4. Keep the mining repository on the same operational pattern, but do not assume the same runtime, scaling, or failover profile until it is validated independently.
