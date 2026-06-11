interface CloudflareEnv {
  HYBA_BACKEND_URL?: string;
  CF_PAGES_COMMIT_SHA?: string;
  CF_PAGES_BRANCH?: string;
}

interface PagesContext<Env> {
  request: Request;
  env: Env;
}

export async function onRequest(context: PagesContext<CloudflareEnv>): Promise<Response> {
  const started = Date.now();
  const backend = context.env.HYBA_BACKEND_URL || null;
  let backendReachable = false;
  let backendStatus: number | null = null;

  if (backend) {
    try {
      const healthUrl = new URL("/api/health/readiness", backend);
      const response = await fetch(healthUrl, { method: "GET", headers: { "x-hyba-edge": "cloudflare-pages" } });
      backendStatus = response.status;
      backendReachable = response.ok;
    } catch {
      backendReachable = false;
    }
  }

  const status = backendReachable ? 200 : 503;
  return new Response(JSON.stringify({
    status: backendReachable ? "ok" : "degraded",
    service: "HYBA Cloudflare Edge Bridge",
    backendConfigured: Boolean(backend),
    backendReachable,
    backendStatus,
    branch: context.env.CF_PAGES_BRANCH || null,
    commit: context.env.CF_PAGES_COMMIT_SHA || null,
    latencyMs: Date.now() - started,
    timestamp: new Date().toISOString(),
  }, null, 2), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
    },
  });
}
