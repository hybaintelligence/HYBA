const metaEnv = (import.meta as any).env || {};

// All API requests should route through the Express secure bridge (Port 3000)
export const BACKEND_URL = "/api";
export const EXPRESS_URL = ""; 

/**
 * Robust Centralized Authentication Interceptor
 * Injects Authorization: Bearer <token> and defaults headers safely.
 */
export function authInterceptor(options: RequestInit = {}): RequestInit {
  const token = localStorage.getItem("quantum_token");
  
  // Construct headers cleanly supporting both Object and Headers formats
  const headers = new Headers(options.headers || {});
  
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  
  return {
    ...options,
    headers
  };
}

/**
 * Internal fetch with backoff wrapper utilizing the interceptor
 */
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

/**
 * Starts keep-alive ping intervals using the interceptor
 */
export function startKeepAlivePing(onPingResult?: (latency: number, success: boolean) => void) {
  return setInterval(async () => {
    const start = performance.now();
    try {
      const res = await fetch(`${BACKEND_URL}/health`, authInterceptor());
      const latency = performance.now() - start;
      if (onPingResult) {
        onPingResult(latency, res.ok);
      }
    } catch {
      if (onPingResult) {
        onPingResult(performance.now() - start, false);
      }
    }
  }, 30000);
}

export async function fetchTelemetryData() {
  try {
    const start = performance.now();
    const [healthRes, consciousnessRes, poolsRes, securityRes] = await Promise.all([
      fetchWithBackoff(`${BACKEND_URL}/health`),
      fetchWithBackoff(`${BACKEND_URL}/ai/consciousness`),
      fetchWithBackoff(`${BACKEND_URL}/mining/pools`),
      fetchWithBackoff(`${BACKEND_URL}/security/status`)
    ]);

    const latency = performance.now() - start;

    if (!healthRes.ok) throw new Error("Health check failed");

    const health = await healthRes.json();
    const consciousness = await consciousnessRes.json();
    const pools = await poolsRes.json();
    const security = await securityRes.json();

    return {
      status: "success",
      latency,
      health,
      consciousness,
      pools,
      security
    };
  } catch (err: any) {
    console.error("Telemetry fetch failed:", err);
    throw err;
  }
}

export async function executePulvini() {
  const response = await fetch(`${BACKEND_URL}/pulvini/execute`, authInterceptor({
    method: "POST"
  }));
  
  if (!response.ok) {
    throw new Error(`HYBA Backend HTTP Error: ${response.status}`);
  }
  
  return response.json();
}

export async function requestPrediction(payload: any) {
  const response = await fetch(`${BACKEND_URL}/predict`, authInterceptor({
    method: "POST",
    body: JSON.stringify(payload)
  }));
  if (!response.ok) throw new Error("Prediction request failed");
  return response.json();
}

export async function loginApi(credentials: any) {
  const response = await fetch(`${EXPRESS_URL}/api/auth/login`, authInterceptor({
    method: "POST",
    body: JSON.stringify(credentials)
  }));
  return response;
}

export async function registerApi(userData: any) {
  const response = await fetch(`${EXPRESS_URL}/api/auth/register`, authInterceptor({
    method: "POST",
    body: JSON.stringify(userData)
  }));
  return response;
}

export async function fetchProfileApi() {
  const response = await fetch(`${EXPRESS_URL}/api/auth/profile`, authInterceptor({
    method: "GET"
  }));
  return response;
}

export async function fetchProductsApi() {
  const response = await fetch(`${EXPRESS_URL}/api/products`, authInterceptor({
    method: "GET"
  }));
  return response;
}
