# HYBA Cloudflare Production Deployment

This repo is now prepared for a Cloudflare Pages deployment from Git while preserving the existing Docker/Express production path.

## Recommended Cloudflare Pages settings

| Setting | Value |
| --- | --- |
| Build command | `npm run build` |
| Build output directory | `dist` |
| Runtime | Cloudflare Pages Functions |
| Required environment variable | `HYBA_BACKEND_URL=https://<your-fastapi-origin>` |

`wrangler.toml` pins the Pages output directory to `dist`. Cloudflare's build-command field must still be set to `npm run build`; `npm build` is not a valid npm CLI command and will fail before Vite starts. The Pages Functions under `functions/` proxy `/api/*` and `/health/*` to `HYBA_BACKEND_URL`, so the SPA can continue to call same-origin API routes after deployment.

## Build Configuration Verification

Before deploying to Cloudflare Pages, verify the dashboard settings match the recommended configuration above:

- **Build command**: `npm run build` ✓ (NOT `npm build`)
- **Build output directory**: `dist` ✓
- **Root directory**: `/` (default)
- **Build system version**: 3 (Cloudflare's latest)

You can validate the repository-side build configuration with:

```bash
node scripts/assert_cloudflare_pages_build_config.mjs
```

## Production gates

Run these before connecting the production branch to Cloudflare or after changing Pages dashboard settings:

```bash
npm run cloudflare:check
npm run lint
npm run build
npm run test:backend
npm run test:e2e:backend
```

`npm run prod:check` runs the full gate sequence in one command.

## Security and caching controls

Cloudflare will publish `public/_headers` and `public/_redirects` into the built asset bundle. These files provide:

- HSTS, frame denial, MIME sniffing protection, strict referrer policy, and a locked-down permissions policy.
- Immutable caching for fingerprinted assets.
- No-store caching for `index.html`.
- SPA fallback routing while preserving `/api/*`, `/health/*`, and `/bridge/health` routes for Functions.

## Health checks

After deployment, validate:

- `https://<app-domain>/bridge/health` returns the Cloudflare edge bridge status and backend reachability.
- `https://<app-domain>/api/health/readiness` proxies to the FastAPI backend readiness endpoint.
- The UI header latency pill reports a connected state after the first successful telemetry poll.

## Rollback plan

1. Revert the Cloudflare Pages deployment to the previous successful build in the Cloudflare dashboard.
2. Verify `/bridge/health` and `/api/health/readiness` on the rolled-back build.
3. Keep the Docker path available for environments that require the Express bridge and colocated FastAPI runtime.
