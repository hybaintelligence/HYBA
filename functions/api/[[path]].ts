interface CloudflareEnv {
  HYBA_BACKEND_URL?: string;
  HYBA_EDGE_PROXY_TIMEOUT_MS?: string;
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

function requestId(): string {
  return `edge_${crypto.randomUUID()}`;
}

function timeoutMs(env: CloudflareEnv): number {
  const parsed = Number(env.HYBA_EDGE_PROXY_TIMEOUT_MS || 30000);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 30000;
}

function json(body: Record<string, unknown>, status = 200, id = requestId()): Response {
  return new Response(JSON.stringify({ ...body, requestId: id }, null, 2), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      "x-request-id": id,
      "x-hyba-edge": "cloudflare-pages",
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

function copyHeaders(request: Request, id: string): Headers {
  const headers = new Headers();
  request.headers.forEach((value, key) => {
    if (!HOP_BY_HOP_HEADERS.has(key.toLowerCase())) headers.set(key, value);
  });
  headers.set("x-hyba-edge", "cloudflare-pages");
  headers.set("x-request-id", id);
  return headers;
}

export async function onRequest(context: PagesContext<CloudflareEnv>): Promise<Response> {
  const id = context.request.headers.get("x-request-id") || requestId();
  const backendUrl = getBackendUrl(context.env);
  if (!backendUrl) {
    return json({
      error: "backend_not_configured",
      message: "Set HYBA_BACKEND_URL in Cloudflare Pages environment variables to enable /api proxying.",
    }, 503, id);
  }

  const request = context.request;
  const target = buildTargetUrl(request, backendUrl);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs(context.env));
  const init: RequestInit = {
    method: request.method,
    headers: copyHeaders(request, id),
    body: ["GET", "HEAD"].includes(request.method.toUpperCase()) ? undefined : request.body,
    redirect: "manual",
    signal: controller.signal,
  };

  try {
    const response = await fetch(target, init);
    const responseHeaders = new Headers(response.headers);
    responseHeaders.set("x-hyba-edge", "cloudflare-pages");
    responseHeaders.set("x-request-id", id);
    responseHeaders.set("cache-control", responseHeaders.get("cache-control") || "no-store");
    responseHeaders.delete("content-encoding");
    responseHeaders.delete("content-length");

    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
    });
  } catch (error: unknown) {
    const aborted = error instanceof DOMException && error.name === "AbortError";
    return json({
      error: aborted ? "backend_timeout" : "backend_unavailable",
      message: aborted ? "HYBA backend request timed out" : "HYBA backend is not reachable from Cloudflare Pages",
      path: new URL(request.url).pathname,
    }, 503, id);
  } finally {
    clearTimeout(timeout);
  }
}
