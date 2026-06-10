const metaEnv = (import.meta as any).env || {};
void metaEnv;

// All API requests route through the Express secure bridge.
export const BACKEND_URL = "/api";
export const EXPRESS_URL = "";

/**
 * Robust centralized authentication interceptor.
 */
export function authInterceptor(options: RequestInit = {}): RequestInit {
  const token = localStorage.getItem("quantum_token");
  const headers = new Headers(options.headers || {});

  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  return {
    ...options,
    headers,
  };
}

async function fetchWithBackoff(url: string, options: RequestInit = {}, maxRetries = 3, baseDelayMs = 1000): Promise<Response> {
  let retries = 0;
  const interceptedOptions = authInterceptor(options);
  while (true) {
    try {
      const response = await fetch(url, interceptedOptions);
      if (!response.ok && response.status >= 500 && retries < maxRetries) {
        throw new Error(`Server error: ${response.status}`);
      }
      return response;
    } catch (error) {
      if (retries >= maxRetries) {
        throw error;
      }
      const delay = baseDelayMs * Math.pow(2, retries);
      console.warn(`Fetch failed for ${url}. Retrying in ${delay}ms... (Attempt ${retries + 1}/${maxRetries})`);
      await new Promise(resolve => setTimeout(resolve, delay));
      retries++;
    }
  }
}

async function fetchRequiredJson(path: string) {
  const response = await fetchWithBackoff(`${BACKEND_URL}${path}`);
  if (!response.ok) {
    throw new Error(`Required backend endpoint failed: ${path} (${response.status})`);
  }
  return response.json();
}

async function fetchOptionalJson(path: string, unavailablePayload: Record<string, unknown>) {
  try {
    const response = await fetchWithBackoff(`${BACKEND_URL}${path}`, {}, 1, 250);
    if (!response.ok) {
      return {
        ...unavailablePayload,
        http_status: response.status,
      };
    }
    return response.json();
  } catch (error: any) {
    return {
      ...unavailablePayload,
      error: error?.message || "endpoint_unavailable",
    };
  }
}

export function startKeepAlivePing(onPingResult?: (latency: number, success: boolean) => void) {
  return setInterval(async () => {
    const start = performance.now();
    try {
      const res = await fetch(`${BACKEND_URL}/health`, authInterceptor());
      onPingResult?.(performance.now() - start, res.ok);
    } catch {
      onPingResult?.(performance.now() - start, false);
    }
  }, 30000);
}

export async function fetchTelemetryData() {
  const start = performance.now();
  const health = await fetchRequiredJson("/health");
  const [consciousness, pools, security] = await Promise.all([
    fetchOptionalJson("/ai/consciousness", {
      status: "unavailable",
      source: "ai_endpoint_unavailable",
      consciousness_level: null,
      phi_resonance: null,
      integrated_information: null,
    }),
    fetchOptionalJson("/mining/pools", {
      pools: [],
      summary: {
        total_pools: 0,
        active_pools: 0,
        telemetry_source: "unavailable",
      },
    }),
    fetchOptionalJson("/security/status", {
      status: "unavailable",
      threat_level: null,
      defense_systems: {},
      recent_threats: [],
    }),
  ]);

  return {
    status: "success",
    latency: performance.now() - start,
    health,
    consciousness,
    pools,
    security,
  };
}

export async function executePulvini() {
  const response = await fetch(`${BACKEND_URL}/pulvini/execute`, authInterceptor({
    method: "POST",
  }));

  if (!response.ok) {
    throw new Error(`HYBA Backend HTTP Error: ${response.status}`);
  }

  return response.json();
}

export async function requestPrediction(payload: any) {
  const response = await fetch(`${BACKEND_URL}/predict`, authInterceptor({
    method: "POST",
    body: JSON.stringify(payload),
  }));
  if (!response.ok) throw new Error("Prediction runtime is not available");
  return response.json();
}

export async function loginApi(credentials: any) {
  return fetch(`${EXPRESS_URL}/api/auth/login`, authInterceptor({
    method: "POST",
    body: JSON.stringify(credentials),
  }));
}

export async function registerApi(userData: any) {
  return fetch(`${EXPRESS_URL}/api/auth/register`, authInterceptor({
    method: "POST",
    body: JSON.stringify(userData),
  }));
}

export async function fetchProfileApi() {
  return fetch(`${EXPRESS_URL}/api/auth/profile`, authInterceptor({
    method: "GET",
  }));
}

export async function fetchProductsApi() {
  return fetch(`${EXPRESS_URL}/api/products`, authInterceptor({
    method: "GET",
  }));
}

export async function updatePowerScale(scale: number) {
  const response = await fetch(`${BACKEND_URL}/mining/power`, authInterceptor({
    method: "POST",
    body: JSON.stringify({ scale }),
  }));
  if (!response.ok) throw new Error("Power scale update failed");
  return response.json();
}
