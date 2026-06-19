import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const dockerfile = readFileSync('Dockerfile', 'utf8');
const hardener = readFileSync('scripts/ensure_spa_entrypoint.mjs', 'utf8');
const serverSource = readFileSync('src/server.ts', 'utf8');

describe('production SPA entrypoint', () => {
  it('keeps the Docker production image serving the SPA at /', () => {
    expect(dockerfile).toContain('RUN npm run build');
    expect(dockerfile).toContain('RUN node scripts/ensure_spa_entrypoint.mjs');
    expect(dockerfile.indexOf('RUN node scripts/ensure_spa_entrypoint.mjs')).toBeGreaterThan(
      dockerfile.indexOf('RUN npm run build'),
    );
  });

  it('uses a Node-capable runtime before installing production npm dependencies', () => {
    expect(dockerfile).toContain('FROM node:22.15.0-bookworm-slim AS runtime');
    expect(dockerfile).toContain('RUN npm install --omit=dev');
    expect(dockerfile.indexOf('FROM node:22.15.0-bookworm-slim AS runtime')).toBeLessThan(
      dockerfile.indexOf('RUN npm install --omit=dev'),
    );
  });

  it('moves public bridge status away from the SPA root in the bundled server', () => {
    expect(hardener).toContain('app.get("/bridge/status"');
    expect(hardener).toContain('productionRootRoutePattern');
    expect(hardener).toContain('production root route still intercepts the SPA');
  });

  it('protects against the current server source root-route interception until source is simplified', () => {
    expect(serverSource).toContain('app.get("/", async (_req: Request, res: Response, next: NextFunction)');
    expect(hardener).toContain('moved bridge status JSON from / to /bridge/status');
  });
});
