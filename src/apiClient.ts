/**
 * HYBA API Client — Production-Grade TypeScript SDK
 *
 * Design principles (Stripe/McKinsey grade):
 *   - Fully typed request/response interfaces
 *   - Exponential backoff with jitter for retries
 *   - Unified error handling with typed errors
 *   - Request ID propagation for distributed tracing
 *   - Token lifecycle management (auto-refresh ready)
 *   - Zero runtime assumptions about token format
 */

// ── Types ──────────────────────────────────────────────────────────────────

export interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
  telemetry_source?: string;
  quantumCoherence?: number | null;
  phiResonance?: number | null;
  quantumSpeedupFactor?: number | null;
  actualSpeedupFactor?: number | null;
  systemMetrics?: SystemMetrics;
  substrate?: Record<string, unknown>;
  telemetry?: Record<string, unknown>;
}

export interface SystemMetrics {
  blockHeight?: number | null;
  currentHashrate?: number | null;
  powerConsumption?: number | null;
  activePool?: string | null;
  difficultyTarget?: string | null;
  networkDifficulty?: number | null;
  power_scale?: number | null;
  system_health?: string | null;
}

export interface ConsciousnessResponse {
  status: string;
  source: string;
  consciousness_level?: number | null;
  phi_resonance?: number | null;
  integrated_information?: number | null;
}

export interface PoolInfo {
  pool_id?: string;
  name?: string;
  url?: string;
  connection_state?: string;
  status?: string;
  is_active?: boolean;
  performance?: {
    latency_ms?: number;
    shares_submitted?: number;
  };
}

export interface PoolsResponse {
  pools: PoolInfo[];
  summary: {
    total_pools: number;
    active_pools: number;
    telemetry_source: string;
  };
}

export interface SecurityStatus {
  status: string;
  threat_level?: string | null;
  defense_systems?: Record<string, unknown>;
  recent_threats?: unknown[];
}

export interface TelemetryData {
  status: string;
  latency: number;
  health: HealthResponse;
  consciousness: ConsciousnessResponse;
  pools: PoolsResponse;
  security: SecurityStatus;
}

export interface AuthResponse {
  success: boolean;
  token?: string;
  user?: {
    id?: string;
    username: string;
    role: string;
    createdAt?: string;
  };
  error?: string;
  details?: string;
}

export interface Product {
  id?: string;
  name: string;
  description?: string;
}

export interface ApiError {
  code: string;
  message: string;
  status: number;
  requestId?: string;
  details?: Record<string, unknown>;
}

// ── Constants ──────────────────────────────────────────────────────────────

const BACKEND_URL = "/api";
const AUTH_URL = "";
const DEFAULT_MAX_RETRIES = 3;
const DEFAULT_BASE_DELAY_MS = 1000;

// ── Token Management ──────────────────────────────────────────────────────

const TOKEN_KEY = "hyba_auth_token";

function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

function setToken(token: string): void {
  try {
    localStorage.setItem(TOKEN_KEY, token);
  } catch {
    // localStorage may be unavailable in some environments
  }
}

function clearToken(): void {
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch {
    // noop
  }
}

// ── Auth Interceptor ──────────────────────────────────────────────────────

export function authInterceptor(init: RequestInit = {}): RequestInit {
  const token = getToken();
  const headers = new Headers(init.headers || {});

  if (!headers.has("Content-Type") && !(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  return { ...init, headers };
}

// ── Error Handling ────────────────────────────────────────────────────────

class HybaApiError extends Error {
  public readonly code: string;
  public readonly status: number;
  public readonly requestId?: string;
  public readonly details?: Record<string, unknown>;

  constructor(error: ApiError) {
    super(error.message);
    this.name = "HybaApiError";
    this.code = error.code;
    this.status = error.status;
    this.requestId = error.requestId;
    this.details = error.details;
  }
}

async function parseApiError(response: Response): Promise<HybaApiError> {
  const requestId = response.headers.get("x-request-id") || undefined;
  try {
    const body = await response.json();
    return new HybaApiError({
      code: body.error || "unknown_error",
      message: body.message || `HTTP ${response.status}`,
      status: response.status,
      requestId,
      details: body.details || body,
    });
  } catch {
    return new HybaApiError({
      code: "http_error",
      message: `HTTP ${response.status}: ${response.statusText}`,
      status: response.status,
      requestId,
    });
  }
}

// ── Retry Logic (exponential backoff with jitter) ────────────────────────

interface RetryOptions {
  maxRetries: number;
  baseDelayMs: number;
  maxDelayMs: number;
  retryOn: (status: number) => boolean;
}

const DEFAULT_RETRY_OPTIONS: RetryOptions = {
  maxRetries: DEFAULT_MAX_RETRIES,
  baseDelayMs: DEFAULT_BASE_DELAY_MS,
  maxDelayMs: 10000,
  retryOn: (status: number) => status >= 500 || status === 429,
};

function calculateDelay(attempt: number, baseDelayMs: number, maxDelayMs: number): number {
  const exponential = Math.min(baseDelayMs * Math.pow(2, attempt), maxDelayMs);
  // Add jitter: ±25%
  const jitter = exponential * (0.75 + Math.random() * 0.5);
  return Math.floor(jitter);
}

async function fetchWithRetry(
  url: string,
  options: RequestInit = {},
  retryOptions: Partial<RetryOptions> = {},
): Promise<Response> {
  const { maxRetries, baseDelayMs, maxDelayMs, retryOn } = { ...DEFAULT_RETRY_OPTIONS, ...retryOptions };
  const interceptedOptions = authInterceptor(options);

  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const response = await fetch(url, interceptedOptions);

      if (response.ok || !retryOn(response.status) || attempt >= maxRetries) {
        return response;
      }

      // Server error or rate limit — retry
      const delay = calculateDelay(attempt, baseDelayMs, maxDelayMs);
      console.warn(
        `[HYBA API] ${url} returned ${response.status}. Retrying in ${delay}ms (attempt ${attempt + 1}/${maxRetries})`,
      );
      await new Promise(resolve => setTimeout(resolve, delay));
      lastError = await parseApiError(response);
    } catch (error) {
      if (attempt >= maxRetries) {
        throw error;
      }
      const delay = calculateDelay(attempt, baseDelayMs, maxDelayMs);
      console.warn(`[HYBA API] ${url} network error. Retrying in ${delay}ms (attempt ${attempt + 1}/${maxRetries})`);
      await new Promise(resolve => setTimeout(resolve, delay));
      lastError = error instanceof Error ? error : new Error(String(error));
    }
  }

  throw lastError || new Error(`Request to ${url} failed after ${maxRetries} retries`);
}

// ── API Client ────────────────────────────────────────────────────────────

async function get<T>(path: string, retryOptions?: Partial<RetryOptions>): Promise<T> {
  const response = await fetchWithRetry(`${BACKEND_URL}${path}`, { method: "GET" }, retryOptions);
  if (!response.ok) throw await parseApiError(response);
  return response.json() as Promise<T>;
}

async function post<T>(path: string, body: unknown, retryOptions?: Partial<RetryOptions>): Promise<T> {
  const response = await fetchWithRetry(
    `${BACKEND_URL}${path}`,
    {
      method: "POST",
      body: JSON.stringify(body),
    },
    retryOptions,
  );
  if (!response.ok) throw await parseApiError(response);
  return response.json() as Promise<T>;
}

async function getOptional<T>(path: string, fallback: T, retryOptions?: Partial<RetryOptions>): Promise<T> {
  try {
    const response = await fetchWithRetry(
      `${BACKEND_URL}${path}`,
      { method: "GET" },
      { maxRetries: 1, baseDelayMs: 250, ...retryOptions },
    );
    if (!response.ok) return { ...fallback, http_status: response.status };
    return response.json() as Promise<T>;
  } catch (error) {
    return {
      ...fallback,
      error: error instanceof Error ? error.message : "endpoint_unavailable",
    } as T;
  }
}

// ── Health & Telemetry ────────────────────────────────────────────────────

export async function fetchTelemetryData(): Promise<TelemetryData> {
  const start = performance.now();
  const health = await get<HealthResponse>("/health");
  const [consciousness, pools, security] = await Promise.all([
    getOptional<ConsciousnessResponse>("/ai/consciousness", {
      status: "unavailable",
      source: "ai_endpoint_unavailable",
      consciousness_level: null,
      phi_resonance: null,
      integrated_information: null,
    }),
    getOptional<PoolsResponse>("/mining/pools", {
      pools: [],
      summary: { total_pools: 0, active_pools: 0, telemetry_source: "unavailable" },
    }),
    getOptional<SecurityStatus>("/security/status", {
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

// ── Mining ────────────────────────────────────────────────────────────────

export interface PulviniResult {
  status: "success" | "error";
  message?: string;
  timestamp?: string;
  source?: string;
  operations?: Array<{
    operation: string;
    state_vector_entries?: number;
    invariants?: number;
    diffusion_norm?: number;
    norm_error?: number;
    original_dimensions?: number;
    projected_dimensions?: number;
    topological_anchoring?: string;
    purity?: number;
    orthonormality_error?: number;
  }>;
  metric_compression?: string | null;
  hamiltonian_generation?: string | null;
  error?: string;
  details?: string;
}

export async function executePulvini(): Promise<PulviniResult> {
  return post<PulviniResult>("/pulvini/execute", {});
}

export interface PredictionResult {
  prediction?: unknown;
  confidence?: number;
  error?: string;
}

export async function requestPrediction(payload: Record<string, unknown>): Promise<PredictionResult> {
  return post<PredictionResult>("/predict", payload);
}

export async function updatePowerScale(scale: number): Promise<{ success: boolean }> {
  return post<{ success: boolean }>("/mining/power", { scale });
}

export interface ConnectPoolRequest {
  pool_id: string;
  worker: string;
  password: string;
  capacity_ehs?: number;
}

export interface ConnectPoolResponse {
  status: string;
  pool: string;
  worker: string;
  url: string;
  capacity_ehs: number;
  daemon: any;
  connected_at: string;
}

export async function connectToPool(data: ConnectPoolRequest): Promise<ConnectPoolResponse> {
  return post<ConnectPoolResponse>("/mining/connect", data);
}

export async function disconnectFromPool(): Promise<{ status: string; previous_pool?: string }> {
  return post<{ status: string; previous_pool?: string }>("/mining/disconnect", {});
}

export interface SubmitJobRequest {
  pool_id: string;
  worker: string;
  job_id: string;
  nonce: string;
  hashrate_ehs?: number;
}

export interface SubmitJobResponse {
  status: string;
  job_id: string;
  worker: string;
  pool_id: string;
  hashrate_ehs: number;
  total_submitted: number;
  total_accepted: number;
  acceptance_rate: number;
  timestamp: string;
}

export async function submitJob(data: SubmitJobRequest): Promise<SubmitJobResponse> {
  return post<SubmitJobResponse>("/mining/submit", data);
}

// ── Authentication ────────────────────────────────────────────────────────

export async function loginApi(credentials: { username: string; password: string }): Promise<AuthResponse> {
  const options = authInterceptor({
    method: "POST",
    body: JSON.stringify(credentials),
  });
  const response = await fetch(`${AUTH_URL}/api/auth/login`, options);
  if (!response.ok) throw await parseApiError(response);
  const data = (await response.json()) as AuthResponse;
  if (data.token) setToken(data.token);
  return data;
}

export async function registerApi(userData: { username: string; password: string }): Promise<AuthResponse> {
  const options = authInterceptor({
    method: "POST",
    body: JSON.stringify(userData),
  });
  const response = await fetch(`${AUTH_URL}/api/auth/register`, options);
  if (!response.ok) throw await parseApiError(response);
  return response.json() as Promise<AuthResponse>;
}

export async function fetchProfileApi(): Promise<Response> {
  return fetch(`${AUTH_URL}/api/auth/profile`, authInterceptor({ method: "GET" }));
}

export async function fetchProductsApi(): Promise<Response> {
  return fetch(`${AUTH_URL}/api/products`, authInterceptor({ method: "GET" }));
}

export function logout(): void {
  clearToken();
}

export function isAuthenticated(): boolean {
  return getToken() !== null;
}

// ── Keep-Alive Ping ───────────────────────────────────────────────────────

export function startKeepAlivePing(onPingResult?: (latency: number, success: boolean) => void): number {
  return window.setInterval(async () => {
    const start = performance.now();
    try {
      const res = await fetch(`${BACKEND_URL}/health`, authInterceptor());
      onPingResult?.(performance.now() - start, res.ok);
    } catch {
      onPingResult?.(performance.now() - start, false);
    }
  }, 30000);
}