# HYBA Docker Deployment Checklist

Use this checklist before promoting any HYBA frontend, backend, substrate, mining, or autonomics service image to production. Treat unchecked boxes as release blockers unless the deployment notes document an explicit, approved exception.

## 1. Pre-deployment validation

- [ ] Confirm the repository has no merge markers, orphaned generated directories, or untracked deployment artifacts.
- [ ] Confirm `.dockerignore` excludes dependency, cache, build, secret, and large artifact paths: `node_modules/`, `.venv/`, `__pycache__/`, `.pytest_cache/`, `dist/`, `build/`, `.env`, logs, benchmark outputs, and research artifacts.
- [ ] Confirm secrets are injected through environment variables or the deployment secret manager, never copied into the image.
- [ ] Confirm Python dependencies are pinned through `python_backend/requirements.txt` and backend service lock files.
- [ ] Confirm frontend dependencies are locked by `package-lock.json`.
- [ ] Confirm production claim language remains evidence-bound and does not promise pool revenue, accepted shares, or external impact without telemetry.

## 2. Dockerfile review

### Fullstack image

- [ ] Use pinned, supported base images for Node.js and Python.
- [ ] Build frontend dependencies in a Node dependency stage.
- [ ] Run `npm run lint` and `npm run build` in the image build, with no fallback artifact generation.
- [ ] Build Python dependencies in a dedicated Python dependency stage and install with `pip install --no-cache-dir`.
- [ ] Copy only runtime artifacts into the final image.
- [ ] Run as a non-root user.
- [ ] Use `tini` or equivalent signal handling for multi-process runtime supervision.
- [ ] Define a healthcheck for the public bridge readiness surface.
- [ ] Start FastAPI with explicit host, port, worker, and log-level settings.

### Frontend/static surface

- [ ] Ensure Vite resolves the production `index.html` entrypoint deterministically.
- [ ] Ensure the generated SPA entrypoint is patched/hardened before runtime.
- [ ] Confirm asset cache headers and CSP/reverse-proxy headers are supplied by the deployment proxy when the image is not serving through nginx.

## 3. Local build validation

- [ ] Run `docker build -t hyba-fullstack:local .`.
- [ ] Confirm the build performs dependency installation, TypeScript linting, frontend bundling, server bundling, and Python dependency resolution successfully.
- [ ] Confirm there are no deprecated Dockerfile instruction warnings.
- [ ] Record the final image size and investigate unexpected growth.
- [ ] Save or link the build transcript in release evidence when required by the deployment gate.

## 4. Local runtime validation

- [ ] Run `docker run --rm -p 3000:3000 -p 3001:3001 hyba-fullstack:local`.
- [ ] Confirm `GET /bridge/health` returns healthy bridge status.
- [ ] Confirm the SPA root loads without server-side JSON intercepting `/`.
- [ ] Confirm frontend-to-backend proxy requests reach FastAPI.
- [ ] Confirm logs show startup, health, and shutdown events without stack traces.
- [ ] Confirm CORS and proxy behavior match the target environment.

## 5. Compose integration

- [ ] Define frontend/bridge, backend runtime, database, Redis/queue, and telemetry services as needed.
- [ ] Define explicit networks for public bridge traffic and backend/private dependencies.
- [ ] Inject environment variables via deployment `.env` or platform secrets.
- [ ] Define persistent volumes for stateful services only.
- [ ] Add healthchecks and `restart: unless-stopped` for long-lived services.
- [ ] Add resource limits appropriate for the deployment tier.

## 6. Production hardening

- [ ] Ensure no secrets, private keys, local databases, or `.env` files are baked into the image.
- [ ] Add reverse proxy HTTPS termination through Traefik, nginx, Caddy, or the cloud platform edge.
- [ ] Configure CSP, HSTS, and cache headers at the edge/proxy layer.
- [ ] Configure structured logging and retention.
- [ ] Add monitoring labels and metrics scrape configuration.
- [ ] Confirm rollback image tags and rollback commands are documented.

## 7. Registry push

- [ ] Tag the image with immutable release/version metadata and, if used, a `latest` alias.
- [ ] Push to the target registry.
- [ ] Confirm the registry digest matches the locally built digest.
- [ ] Record image digest in deployment notes.

## 8. Server/cloud deployment

- [ ] Pull the exact approved image digest.
- [ ] Run `docker compose up -d --pull always` or the platform-equivalent deployment command.
- [ ] Confirm all containers start cleanly.
- [ ] Confirm healthchecks pass after the configured start period.
- [ ] Confirm logs are free of stack traces and dependency resolver errors.
- [ ] Confirm API, UI, substrate telemetry, and mining readiness surfaces connect as expected.

## 9. Post-deployment validation

- [ ] Run synthetic API smoke tests.
- [ ] Run frontend smoke tests.
- [ ] Validate mining substrate connectivity without claiming accepted shares unless confirmed by the pool.
- [ ] Validate Salamander/autonomic endpoints used by the deployment.
- [ ] Validate QAOA/audit-chain telemetry ingestion where enabled.
- [ ] Validate dashboard ingestion and operator status panels.
- [ ] Validate SLO/error-budget dashboards and alert delivery.

## 10. Operational readiness

- [ ] Monitoring dashboards are active.
- [ ] Alerts are configured and routed.
- [ ] Log retention policy is active.
- [ ] Backup policy is active for stateful dependencies.
- [ ] Rollback plan is documented and tested.
- [ ] Deployment notes, image digest, and gate outputs are committed or attached to the release evidence.
