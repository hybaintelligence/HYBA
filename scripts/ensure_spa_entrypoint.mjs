#!/usr/bin/env node
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { resolve } from 'node:path';

const distServerPath = resolve(process.cwd(), 'dist/server.mjs');

const productionRootRoutePattern = /app\.get\("\/",\s*async\s*\([^)]*\)\s*=>\s*\{\s*if\s*\(!CONFIG\.isProduction\)\s*return\s*next\(\);\s*noStore\(res\);\s*res\.json\(\{\s*status:\s*"online",\s*service:\s*"HYBA Secure Bridge",\s*version:\s*"2\.1\.0",\s*backendReachable:\s*await isBackendReachable\(\),\s*timestamp:\s*(?:\(\/\*\s*@__PURE__\s*\*\/\s*new Date\(\)\)|new Date\(\))\.toISOString\(\)\s*\}\);\s*\}\);/s;

const replacement = `app.get("/bridge/status", async (_req, res) => {
    noStore(res);
    res.json({
      status: "online",
      service: "HYBA Secure Bridge",
      version: "2.1.0",
      backendReachable: await isBackendReachable(),
      timestamp: new Date().toISOString()
    });
  });`;

if (!existsSync(distServerPath)) {
  console.error(`[spa-entrypoint] ${distServerPath} does not exist. Run the server bundle build first.`);
  process.exit(1);
}

const bundledServer = readFileSync(distServerPath, 'utf8');

if (bundledServer.includes('app.get("/bridge/status"') && !bundledServer.includes('app.get("/", async (_req, res, next)')) {
  console.log('[spa-entrypoint] production SPA entrypoint already hardened.');
  process.exit(0);
}

if (!productionRootRoutePattern.test(bundledServer)) {
  console.error('[spa-entrypoint] expected production root JSON route was not found; refusing an unsafe build.');
  process.exit(1);
}

const hardenedServer = bundledServer.replace(productionRootRoutePattern, replacement);

if (hardenedServer.includes('app.get("/", async (_req, res, next)')) {
  console.error('[spa-entrypoint] production root route still intercepts the SPA after patching.');
  process.exit(1);
}

writeFileSync(distServerPath, hardenedServer);
console.log('[spa-entrypoint] moved bridge status JSON from / to /bridge/status; / now serves the SPA.');
