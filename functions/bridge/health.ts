interface CloudflareEnv {
  HYBA_BACKEND_URL?: string;
  CF_PAGES_COMMIT_SHA?: string;
  CF_PAGES_BRANCH?: string;
  JWT_SECRET?: string;
  HYBA_API_KEY_SECRET?: string;
  HYBA_CORS_ORIGINS?: string;
}

interface PagesContext<Env> {
  request: Request;
  env: Env;
}

export async function onRequest(context: PagesContext<CloudflareEnv>): Promise<Response> {
  const requiredEnvVars = ["HYBA_BACKEND_URL", "JWT_SECRET", "HYBA_API_KEY_SECRET", "HYBA_CORS_ORIGINS"];
  for (const envVar of requiredEnvVars) {
    if (!context.env[envVar]) {
      console.error(`Environment variable ${envVar} is not set`);
      return new Response(JSON.stringify({
        error: "environment_variable_not_set",
        message: `Set ${envVar} in Cloudflare Pages environment variables.`,
        path: new URL(context.request.url).pathname,
      }, null, 2), {
        status: 503,
        headers: { "content-type": "application/json" },
      });
    }
  }

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
