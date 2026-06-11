interface CloudflareEnv {
  HYBA_BACKEND_URL?: string;
}

interface PagesContext<Env> {
  request: Request;
  env: Env;
}

function json(body: Record<string, unknown>, status = 200): Response {
  return new Response(JSON.stringify(body, null, 2), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
    },
  });
}

function getBackendUrl(env: CloudflareEnv): URL | null {
  if (!env.HYBA_BACKEND_URL) return null;
  try {
    const url = new URL(env.HYBA_BACKEND_URL);
    if (!["https:", "http:"].includes(url.protocol)) return null;
    return url;
  } catch {
    return null;
  }
}

export async function onRequest(context: PagesContext<CloudflareEnv>): Promise<Response> {
  const backendUrl = getBackendUrl(context.env);
  if (!backendUrl) {
    return json({
      error: "backend_not_configured",
      message: "Set HYBA_BACKEND_URL in Cloudflare Pages environment variables to enable /health proxying.",
    }, 503);
  }

  const incoming = new URL(context.request.url);
  const target = new URL(backendUrl.toString());
  target.pathname = `/api/health${incoming.pathname.replace(/^\/health/, "")}`;
  target.search = incoming.search;

  const response = await fetch(target, {
    method: context.request.method,
    headers: context.request.headers,
    body: ["GET", "HEAD"].includes(context.request.method.toUpperCase()) ? undefined : context.request.body,
    redirect: "manual",
  });

  const headers = new Headers(response.headers);
  headers.set("x-hyba-edge", "cloudflare-pages");
  headers.delete("content-encoding");
  headers.delete("content-length");

  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers,
  });
}
