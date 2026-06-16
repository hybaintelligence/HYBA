/**
 * HYBA API Client — Production-Grade TypeScript SDK
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
  phi_tier?: number | null;
  phi_tier_composition?: {
    label?: string;
    phi_exponent?: number;
    scale_factor?: number;
    hashrate_cap_ehs?: number;
  } | null;
  memory_compression_contract?: string | null;
  system_health?: string | null;
}

export interface ConsciousnessResponse {
  status: string;
  source: string;
  consciousness_level?: number | null;
  phi_resonance?: number | null;
  integrated_information?: number | null;
}

export type PoolCredentialMode = "username_password" | "btc_address" | "nicehash_worker_pool_id";

export interface PoolInfo {
  pool_id?: string;
  name?: string;
  url?: string;
  credential_mode?: PoolCredentialMode;
  required_fields?: string[];
  configured?: boolean;
  enabled?: boolean;
  source?: string;
  connection_state?: string;
  status?: string;
  is_active?: boolean;
  performance?: {
    latency_ms?: number | null;
    shares_submitted?: number;
    shares_accepted?: number;
    shares_rejected?: number;
    acceptance_rate?: number;
  };
}

export interface PoolsResponse {
  pools: PoolInfo[];
  summary: {
    total_pools: number;
    configured_pools?: number;
    active_pools: number;
    telemetry_source: string;
  };
}

export interface PoolConfigResponse {
  pools: PoolInfo[];
  active_pool_id?: string | null;
  timestamp: string;
}

export interface ConfigurePoolRequest {
  pool_id: string;
  url?: string;
  username?: string;
  password?: string;
  btc_address?: string;
  worker?: string;
  nicehash_pool_id?: string;
  priority?: number;
  enabled?: boolean;
}

export interface ConfigurePoolResponse {
  status: string;
  pool: PoolInfo;
  request_id?: string;
  tracked_request_id?: string;
  idempotency_key?: string;
}

export interface MetacognitiveStateTelemetry {
  phi_integrated?: number | null;
  syndrome_pressure?: number | null;
  shard_entropy?: number | null;
  confidence_delta?: number | null;
  resource_exhaustion?: number | null;
}

export interface MetacognitiveTelemetry {
  self_awareness?: number | null;
  metacognitive_depth?: number | null;
  is_predicting_disturbance?: boolean | null;
  prediction_accuracy?: number | null;
  events?: string[] | null;
  strategy_weights?: Record<string, number> | null;
  predicted_state?: MetacognitiveStateTelemetry | null;
  current_state?: MetacognitiveStateTelemetry | null;
}

export interface StabilizerMonitorTelemetry {
  syndrome_weight?: number | null;
  confidence?: number | null;
  confidence_threshold?: number | null;
  syndrome_width?: number | null;
  sampled_ancillas?: number | null;
  operating_mode?: string | null;
  syndrome_check_stride?: number | null;
  check_frequency?: number | null;
  syndrome_rotation_index?: number | null;
  pool_permutation_checksum?: number | null;
  sanitized?: boolean | null;
  cause?: string | null;
  metacognitive?: MetacognitiveTelemetry | null;
}

export interface AncillaTrapPoolTelemetry {
  agents_total?: number | null;
  agents_active?: number | null;
  logical_agents?: number | null;
  reserved_ancillas?: number | null;
  active_ancillas?: number | null;
  max_ancilla_pool?: number | null;
  reserved_traps?: number | null;
  active_traps?: number | null;
  disturbed_traps?: number | null;
  retired_traps?: number | null;
}

export interface SecurityDefenseSystems extends Record<string, unknown> {
  stabilizer_monitor?: StabilizerMonitorTelemetry;
  preallocated_ancilla_trap_pool?: AncillaTrapPoolTelemetry;
}

export interface SecurityStatus {
  status: string;
  threat_level?: string | null;
  defense_systems?: SecurityDefenseSystems;
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
const TOKEN_KEY = "hyba_auth_token";
export const PULVINI_HASHRATE_CAP_EHS = 1;

function assertPulviniHashrateCap(value: number | undefined, field: string): void {
  if (value === undefined) return;
  if (!Number.isFinite(value) || value < 0 || value > PULVINI_HASHRATE_CAP_EHS) {
    throw new Error(`${field} must be between 0 and ${PULVINI_HASHRATE_CAP_EHS} EH/s`);
  }
}

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
    // noop
  }
}

function clearToken(): void {
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch {
    // noop
  }
}

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
      code: body.error || body.detail?.error || "unknown_error",
      message:
        body.message ||
        body.detail?.message ||
        body.detail?.detail ||
        body.detail ||
        `HTTP ${response.status}`,
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

function secureUnitInterval(): number {
  if (typeof crypto !== "undefined" && typeof crypto.getRandomValues === "function") {
    const values = new Uint32Array(1);
    crypto.getRandomValues(values);
    return values[0] / 0xffffffff;
  }
  return 0.5;
}

function calculateDelay(attempt: number, baseDelayMs: number, maxDelayMs: number): number {
  return Math.floor(Math.min(baseDelayMs * Math.pow(2, attempt), maxDelayMs));
}

async function fetchWithRetry(
  url: string,
  options: RequestInit = {},
  retryOptions: Partial<RetryOptions> = {},
): Promise<Response> {
  const { maxRetries, baseDelayMs, maxDelayMs, retryOn } = {
    ...DEFAULT_RETRY_OPTIONS,
    ...retryOptions,
  };
  const interceptedOptions = authInterceptor(options);
  let lastError: Error | null = null;
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const response = await fetch(url, interceptedOptions);
      if (response.ok || !retryOn(response.status) || attempt >= maxRetries) {
        return response;
      }
      const delay = calculateDelay(attempt, baseDelayMs, maxDelayMs);
      await new Promise((resolve) => setTimeout(resolve, delay));
      lastError = await parseApiError(response);
    } catch (error) {
      if (attempt >= maxRetries) throw error;
      const delay = calculateDelay(attempt, baseDelayMs, maxDelayMs);
      await new Promise((resolve) => setTimeout(resolve, delay));
      lastError = error instanceof Error ? error : new Error(String(error));
    }
  }
  throw lastError || new Error(`Request to ${url} failed after ${maxRetries} retries`);
}

async function get<T>(path: string, retryOptions?: Partial<RetryOptions>): Promise<T> {
  const response = await fetchWithRetry(`${BACKEND_URL}${path}`, { method: "GET" }, retryOptions);
  if (!response.ok) throw await parseApiError(response);
  return response.json() as Promise<T>;
}

async function post<T>(
  path: string,
  body: unknown,
  retryOptions?: Partial<RetryOptions>,
): Promise<T> {
  const response = await fetchWithRetry(
    `${BACKEND_URL}${path}`,
    { method: "POST", body: JSON.stringify(body) },
    retryOptions,
  );
  if (!response.ok) throw await parseApiError(response);
  return response.json() as Promise<T>;
}

async function getOptional<T>(
  path: string,
  fallback: T,
  retryOptions?: Partial<RetryOptions>,
): Promise<T> {
  try {
    const response = await fetchWithRetry(
      `${BACKEND_URL}${path}`,
      { method: "GET" },
      { maxRetries: 1, baseDelayMs: 250, ...retryOptions },
    );
    if (!response.ok) return { ...fallback, http_status: response.status } as T;
    return response.json() as Promise<T>;
  } catch (error) {
    return {
      ...fallback,
      error: error instanceof Error ? error.message : "endpoint_unavailable",
    } as T;
  }
}

export async function getSecurityStatus(): Promise<SecurityStatus> {
  return get<SecurityStatus>("/security/status");
}

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

export interface PulviniResult {
  status: "success" | "error";
  message?: string;
  timestamp?: string;
  source?: string;
  operations?: Array<Record<string, unknown>>;
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

export async function requestPrediction(
  payload: Record<string, unknown>,
): Promise<PredictionResult> {
  return post<PredictionResult>("/predict", payload);
}

export async function updatePowerScale(
  scale: number,
  phiTier = 12,
): Promise<{ status: string; effective_hashrate_ehs?: number; phi_tier?: number }> {
  return post<{ status: string; effective_hashrate_ehs?: number; phi_tier?: number }>(
    "/mining/power",
    { scale, phi_tier: phiTier },
  );
}

export interface ConnectPoolRequest {
  pool_id: string;
  worker?: string;
  password?: string;
  username?: string;
  btc_address?: string;
  nicehash_pool_id?: string;
  url?: string;
  capacity_ehs?: number;
  switch?: boolean;
}

export interface ConnectPoolResponse {
  status: string;
  pool_id: string;
  pool: string;
  worker: string;
  url: string;
  base_capacity_ehs?: number;
  capacity_ehs: number;
  hashrate_cap_ehs?: number;
  daemon: unknown;
  connected_at: string;
}

export async function fetchPoolConfig(): Promise<PoolConfigResponse> {
  return get<PoolConfigResponse>("/mining/pool-config", { maxRetries: 1, baseDelayMs: 250 });
}

export async function configurePool(data: ConfigurePoolRequest): Promise<ConfigurePoolResponse> {
  return post<ConfigurePoolResponse>("/mining/pool-config", data, { maxRetries: 0 });
}

export async function connectToPool(data: ConnectPoolRequest): Promise<ConnectPoolResponse> {
  assertPulviniHashrateCap(data.capacity_ehs, "capacity_ehs");
  return post<ConnectPoolResponse>(
    "/mining/connect",
    { ...data, switch: data.switch ?? true },
    { maxRetries: 0 },
  );
}

export async function switchPool(data: ConnectPoolRequest): Promise<ConnectPoolResponse> {
  assertPulviniHashrateCap(data.capacity_ehs, "capacity_ehs");
  return post<ConnectPoolResponse>("/mining/switch", { ...data, switch: true }, { maxRetries: 0 });
}

export async function disconnectFromPool(): Promise<{ status: string; previous_pool?: string }> {
  return post<{ status: string; previous_pool?: string }>(
    "/mining/disconnect",
    {},
    { maxRetries: 0 },
  );
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
  hashrate_cap_ehs?: number;
  total_submitted: number;
  total_accepted: number;
  acceptance_rate: number;
  timestamp: string;
}

export async function submitJob(data: SubmitJobRequest): Promise<SubmitJobResponse> {
  assertPulviniHashrateCap(data.hashrate_ehs, "hashrate_ehs");
  return post<SubmitJobResponse>("/mining/submit", data);
}

export async function loginApi(credentials: {
  username: string;
  password: string;
}): Promise<AuthResponse> {
  const options = authInterceptor({ method: "POST", body: JSON.stringify(credentials) });
  const response = await fetch(`${AUTH_URL}/api/auth/login`, options);
  if (!response.ok) throw await parseApiError(response);
  const data = (await response.json()) as AuthResponse;
  if (data.token) setToken(data.token);
  return data;
}

export async function registerApi(userData: {
  username: string;
  password: string;
}): Promise<AuthResponse> {
  const options = authInterceptor({ method: "POST", body: JSON.stringify(userData) });
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

export function startKeepAlivePing(
  onPingResult?: (latency: number, success: boolean) => void,
): number {
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

// ── Intelligence API Endpoints ─────────────────────────────────────────────

export interface IntelligenceTelemetryResponse {
  phi_integrated: number;
  self_awareness: number;
  prediction_accuracy: number;
  syndrome_pressure: number;
  rotation_index: number;
  active_ancillas: number;
  pool_max: number;
  exhaustion: number;
  mode: 'NOMINAL' | 'COMPRESSED' | 'RECOVERY';
  metacognitive_events: string[];
  healing_events: number;
}

export interface IntelligenceStatusResponse {
  active: boolean;
  phi: number;
  current_goal: string;
  uptime_ms: number;
}

export interface HebbianStatsResponse {
  strategy_count: number;
  top_strategies: Array<{
    syndrome: number;
    weight: number;
    success_count: number;
    failure_count: number;
  }>;
  stability: number;
}

export async function getIntelligenceTelemetry(): Promise<IntelligenceTelemetryResponse> {
  return get<IntelligenceTelemetryResponse>("/intelligence/telemetry");
}

export async function getIntelligenceStatus(): Promise<IntelligenceStatusResponse> {
  return get<IntelligenceStatusResponse>("/intelligence/status");
}

export async function getHebbianStats(): Promise<HebbianStatsResponse> {
  return get<HebbianStatsResponse>("/intelligence/hebbian-stats");
}

export async function simulateDisturbance(syndrome: number): Promise<{ status: string }> {
  return post<{ status: string }>("/intelligence/simulate-disturbance", { syndrome });
}

export async function resetIntelligence(): Promise<{ status: string }> {
  return post<{ status: string }>("/intelligence/reset", {});
}

export async function startIntelligence(): Promise<{ status: string }> {
  return post<{ status: string }>("/intelligence/start", {});
}

export async function stopIntelligence(): Promise<{ status: string }> {
  return post<{ status: string }>("/intelligence/stop", {});
}
