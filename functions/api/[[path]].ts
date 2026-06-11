interface CloudflareEnv {
  HYBA_BACKEND_URL?: string;
}

interface PagesContext<Env> {
  request: Request;
  env: Env;
  params: Record<string, string | string[]>;
  waitUntil(promise: Promise<unknown>): void;
  next(input?: Request | string, init?: RequestInit): Promise<Response>;
  data: Record<string, unknown>;
}

const HOP_BY_HOP_HEADERS = new Set([
  "connection",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailer",
  "transfer-encoding",
  "upgrade",
  "host",
]);

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

function buildTargetUrl(request: Request, backendUrl: URL): URL {
  const incoming = new URL(request.url);
  const target = new URL(backendUrl.toString());
  target.pathname = `/api${incoming.pathname.replace(/^\/api/, "")}`;
  target.search = incoming.search;
  return target;
}

function copyHeaders(request: Request): Headers {
  const headers = new Headers();
  request.headers.forEach((value, key) => {
    if (!HOP_BY_HOP_HEADERS.has(key.toLowerCase())) headers.set(key, value);
  });
  headers.set("x-hyba-edge", "cloudflare-pages");
  return headers;
}

export async function onRequest(context: PagesContext<CloudflareEnv>): Promise<Response> {
  const backendUrl = getBackendUrl(context.env);
  if (!backendUrl) {
    return json({
      error: "backend_not_configured",
      message: "Set HYBA_BACKEND_URL in Cloudflare Pages environment variables to enable /api proxying.",
    }, 503);
  }

  const request = context.request;
  const target = buildTargetUrl(request, backendUrl);
  const init: RequestInit = {
    method: request.method,
    headers: copyHeaders(request),
    body: ["GET", "HEAD"].includes(request.method.toUpperCase()) ? undefined : request.body,
    redirect: "manual",
  };

  const response = await fetch(target, init);
  const responseHeaders = new Headers(response.headers);
  responseHeaders.set("x-hyba-edge", "cloudflare-pages");
  responseHeaders.delete("content-encoding");
  responseHeaders.delete("content-length");

  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: responseHeaders,
  });
}
