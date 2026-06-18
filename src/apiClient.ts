/**
 * HYBA API Client — Production-Grade TypeScript SDK
 *
 * Provides complete coverage of all HYBA backend API endpoints (80+ routes).
 *
 * Fixes:
 *   - Auth endpoints no longer use a double /api prefix
 *   - Intelligence paths now target correct /api/v1/intelligence/* backend routes
 *   - All 80 backend endpoints are covered with typed request/response interfaces
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

// ── Mining Specific Types ──────────────────────────────────────────────────

export interface MiningStatusResponse {
  status: string;
  pool_id?: string;
  worker?: string;
  hashrate_ehs?: number;
  hashrate_cap_ehs?: number;
  uptime_seconds?: number;
  shares_submitted?: number;
  shares_accepted?: number;
  shares_rejected?: number;
  acceptance_rate?: number;
  active_job?: string;
  connected_at?: string;
  mining_mode?: string;
  phi_tier?: number;
  power_scale?: number;
  midas_state?: string;
}

export interface MiningHealthResponse {
  status: string;
  engine_ready: boolean;
  circuit_breaker_open: boolean;
  circuit_failures: number;
  last_share_submitted?: string;
  last_share_accepted?: string;
  daemon_connected?: boolean;
  uptime_seconds?: number;
}

export interface MiningStatsResponse {
  total_shares: number;
  accepted_shares: number;
  rejected_shares: number;
  stale_shares: number;
  hashrate_5m?: number;
  hashrate_1h?: number;
  hashrate_24h?: number;
  best_difficulty?: number;
  workers_count?: number;
  active_pools?: number;
  uptime_seconds?: number;
  start_time?: string;
}

export interface MiningDaemonResponse {
  status: string;
  daemon: string;
  version?: string;
  connected: boolean;
  uptime_seconds?: number;
  last_block?: number;
}

export interface MiningJobResponse {
  job_id: string;
  pool_id: string;
  worker: string;
  height?: number;
  difficulty?: number;
  algorithm?: string;
  received_at?: string;
  expires_at?: string;
}

export interface MiningJobsSearchResponse {
  jobs: MiningJobResponse[];
  total: number;
}

export interface MiningOpsAuditResponse {
  actions: Array<{
    timestamp: string;
    action: string;
    detail?: string;
    actor?: string;
  }>;
  total: number;
}

export interface MiningOpsAutonomicsResponse {
  mode: string;
  auto_tune: boolean;
  target_temp?: number;
  target_power?: number;
  fan_speed?: number;
  temperature?: number;
  throttling: boolean;
}

export interface MiningOpsMetricsResponse {
  hashrate_ehs: number;
  power_watts: number;
  efficiency_j_per_th: number;
  temperature_c: number;
  fan_speed_pct: number;
  hardware_error_rate: number;
  uptime_seconds: number;
}

export interface MiningOpsProfitabilityResponse {
  estimated_daily_btc: number;
  estimated_daily_usd: number;
  power_cost_daily_usd: number;
  net_profit_daily_usd: number;
  current_btc_price_usd: number;
  pool_fee_pct: number;
  break_even: boolean;
}

// ── Mining Production (v1) Types ───────────────────────────────────────────

export interface MiningProductionHealthResponse {
  status: string;
  engine_ready: boolean;
  pipeline_healthy: boolean;
  circuit_breaker_open: boolean;
  last_share_accepted?: string;
  errors_last_hour: number;
}

export interface MiningProductionInitializeResponse {
  status: string;
  pipeline_id?: string;
  initialized_at?: string;
}

export interface MiningProductionMetricsResponse {
  hashrate_ehs: number;
  shares_per_minute: number;
  acceptance_rate: number;
  job_accepted_latency_ms: number;
  pipeline_utilization_pct: number;
  errors_last_minute: number;
}

export interface MiningProductionNextJobResponse {
  job_id: string;
  pool_id: string;
  height: number;
  difficulty: number;
  algorithm: string;
  expires_at: string;
}

export interface MiningProductionStartResponse {
  status: string;
  pipeline_id?: string;
  started_at?: string;
}

export interface MiningProductionStatusResponse {
  status: string;
  pipeline_id?: string;
  running: boolean;
  connected_pool?: string;
  hashrate_ehs?: number;
  uptime_seconds?: number;
  errors_total: number;
}

export interface MiningProductionStopResponse {
  status: string;
  stopped_at?: string;
}

export interface MiningProductionSubmitShareRequest {
  pool_id: string;
  worker: string;
  job_id: string;
  nonce: string;
  hashrate_ehs?: number;
}

export interface MiningProductionSubmitShareResponse {
  status: string;
  share_accepted: boolean;
  job_id: string;
  pool_id: string;
  difficulty: number;
  hashrate_ehs: number;
}

// ── Pools (v1) Types ───────────────────────────────────────────────────────

export interface V1PoolInfo {
  id: string;
  name: string;
  url: string;
  stratum_version: number;
  username: string;
  worker: string;
  enabled: boolean;
  is_default: boolean;
  priority: number;
  btc_address?: string;
  description?: string;
}

export interface V1PoolsCurrentResponse {
  pool_id: string;
  name: string;
  url: string;
  connected_at: string;
  uptime_seconds: number;
}

export interface V1PoolsDefaultResponse {
  default_pool_id: string;
  name: string;
  url: string;
}

export interface V1PoolsEnabledResponse {
  pools: V1PoolInfo[];
}

export interface V1PoolsHealthResponse {
  status: string;
  total_pools: number;
  healthy_pools: number;
  degraded_pools: number;
  pools: Array<{
    id: string;
    name: string;
    reachable: boolean;
    latency_ms: number;
    last_check: string;
  }>;
}

export interface V1PoolsListResponse {
  default_pool: string;
  pools: Record<string, V1PoolInfo>;
  timestamp: string;
}

export interface V1PoolsReportShareRequest {
  pool_id: string;
  share_id: string;
  accepted: boolean;
  difficulty: number;
  hashrate_ehs: number;
  timestamp: string;
}

export interface V1PoolsStatusResponse {
  pool_id: string;
  name: string;
  connected: boolean;
  hashrate_ehs: number;
  shares_submitted: number;
  shares_accepted: number;
  shares_rejected: number;
  latency_ms: number;
}

export interface V1PoolsSwitchRequest {
  pool_id: string;
  worker?: string;
}

export interface V1PoolsSwitchResponse {
  status: string;
  previous_pool: string;
  current_pool: string;
}

// ── Intelligence v1 Types ──────────────────────────────────────────────────

export interface IntelligenceV1HealthResponse {
  status: string;
  active: boolean;
  uptime_ms: number;
  phi: number;
}

export interface IntelligenceV1AuditResponse {
  total_reflections: number;
  total_healing_events: number;
  syndrome_pressure: number;
  stability: number;
  autonomy_index: number;
  timestamp: string;
}

export interface IntelligenceV1AbsoluteAuditResponse {
  phi_saturation: number;
  self_awareness_depth: number;
  integrated_information: number;
  metacognitive_events: string[];
  anomaly_detected: boolean;
  timestamp: string;
}

export interface IntelligenceV1ReflectRequest {
  syndrome?: number;
  context?: Record<string, unknown>;
}

export interface IntelligenceV1ReflectResponse {
  reflection_id: string;
  syndrome: number;
  insight: string;
  confidence: number;
  timestamp: string;
}

export interface IntelligenceV1ExplainRequest {
  query: string;
  context?: Record<string, unknown>;
}

export interface IntelligenceV1ExplainResponse {
  explanation: string;
  confidence: number;
  sources: string[];
}

export interface IntelligenceV1OrchestrateRequest {
  goal: string;
  constraints?: Record<string, unknown>;
  priority?: number;
}

export interface IntelligenceV1OrchestrateResponse {
  plan_id: string;
  steps: Array<{
    action: string;
    target: string;
    expected_outcome: string;
  }>;
  estimated_completion_ms: number;
}

export interface IntelligenceV1ClosureSyncResponse {
  status: string;
  synchronized_at: string;
  state_hash?: string;
}

export interface IntelligenceV1HeartbeatPulseResponse {
  status: string;
  timestamp: string;
  phi: number;
  self_awareness: number;
}

// ── AI Types ───────────────────────────────────────────────────────────────

export interface AiStimulateRequest {
  stimulus: string;
  intensity?: number;
}

export interface AiStimulateResponse {
  status: string;
  response: string;
  consciousness_level: number;
  phi_resonance: number;
}

export interface AiChatRequest {
  message: string;
  context?: Record<string, unknown>;
  temperature?: number;
}

export interface AiChatResponse {
  response: string;
  confidence: number;
  sources?: string[];
  phi_resonance?: number;
}

// ── Security Types ─────────────────────────────────────────────────────────

export interface SecurityShieldRequest {
  activation: boolean;
  reason?: string;
}

export interface SecurityShieldResponse {
  status: string;
  shield_active: boolean;
  integrity_locked: boolean;
  timestamp: string;
}

// ── Health Types ───────────────────────────────────────────────────────────

export interface HealthLivenessResponse {
  status: string;
  timestamp: string;
}

export interface HealthReadinessResponse {
  status: string;
  ready: boolean;
  subsystems: Record<string, { name: string; ready: boolean; detail: string }>;
  boot_id: string;
}

// ── Unified Types ──────────────────────────────────────────────────────────

export interface UnifiedHealthResponse {
  status: string;
  subsystem: string;
  version: string;
  uptime_seconds: number;
}

export interface UnifiedStatusResponse {
  status: string;
  mode: string;
  active_tasks: number;
  queued_tasks: number;
  completed_tasks: number;
  memory_usage_mb: number;
  uptime_seconds: number;
}

export interface UnifiedMetricsResponse {
  requests_total: number;
  errors_total: number;
  avg_latency_ms: number;
  p99_latency_ms: number;
  throughput_per_second: number;
}

export interface UnifiedAnalyzeResonanceRequest {
  data: unknown;
  target_frequency?: number;
}

export interface UnifiedShareResultRequest {
  task_id: string;
  result: Record<string, unknown>;
  confidence: number;
}

// ── Memory Types ───────────────────────────────────────────────────────────

export interface MemoryEvidenceResponse {
  evidence: Array<{
    id: string;
    type: string;
    content: string;
    confidence: number;
    timestamp: string;
    source: string;
  }>;
  total: number;
}

export interface MemoryHealthResponse {
  status: string;
  total_memories: number;
  memory_usage_mb: number;
  fragmentation_pct: number;
  compression_ratio: number;
  last_pruning?: string;
}

export interface MemoryEntry {
  key: string;
  content: unknown;
  type: string;
  created_at: string;
  updated_at: string;
  access_count: number;
  ttl?: number;
}

export interface MemoryListResponse {
  memories: MemoryEntry[];
  total: number;
  offset: number;
  limit: number;
}

export interface MemorySnapshotsResponse {
  snapshots: Array<{
    id: string;
    label: string;
    created_at: string;
    size_bytes: number;
    memory_count: number;
  }>;
  total: number;
}

// ── Other Types ────────────────────────────────────────────────────────────

export interface PitfallsResponse {
  pitfalls: Array<{
    id: string;
    category: string;
    title: string;
    description: string;
    severity: string;
    mitigation: string;
  }>;
  total: number;
}

export interface SubstrateResponse {
  boot_id: string;
  initialized: boolean;
  subsystems: Record<string, { name: string; ready: boolean; detail: string }>;
  shutdown_at: string | null;
  initialization_order: string[];
}

export interface ToeExperimentsRequest {
  experiment_type: string;
  parameters: Record<string, unknown>;
}

export interface ToeExperimentsResponse {
  experiment_id: string;
  status: string;
  results: Record<string, unknown>;
  timestamp: string;
}

// ── Shared Mining Types ────────────────────────────────────────────────────

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

export interface PredictionResult {
  prediction?: unknown;
  confidence?: number;
  error?: string;
}

export interface AuthCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  username: string;
  password: string;
}

// ── Admin Types ────────────────────────────────────────────────────────────

export interface AdminStats {
  total_users: number;
  active_users: number;
  admin_users: number;
  executive_users: number;
  total_allocations: number;
  pending_allocations: number;
  approved_allocations: number;
  total_funding_allocated: number;
  timestamp: string;
}

export interface AdminUser {
  id: number;
  username: string;
  email: string | null;
  role: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_login: string | null;
  created_by: string | null;
}

export interface AdminUserListResponse {
  users: AdminUser[];
  total: number;
}

export interface CreateAdminUserRequest {
  username: string;
  email?: string;
  password: string;
  role: string;
}

export interface UpdateAdminUserRequest {
  email?: string;
  role?: string;
  is_active?: boolean;
  password?: string;
}

export interface AuditLog {
  id: number;
  timestamp: string;
  actor_username: string;
  actor_role: string | null;
  action: string;
  target_type: string;
  target_id: string | null;
  details: Record<string, unknown> | null;
  ip_address: string | null;
}

export interface AuditLogListResponse {
  logs: AuditLog[];
  total: number;
}

export interface FundingAllocation {
  id: number;
  entity_name: string;
  entity_type: string;
  allocation_amount: number;
  currency: string;
  fiscal_year: number;
  fiscal_quarter: number | null;
  status: string;
  allocated_by: string;
  allocated_at: string;
  disbursed_at: string | null;
  purpose: string | null;
  restrictions: Record<string, unknown> | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface FundingAllocationListResponse {
  allocations: FundingAllocation[];
  total: number;
}

export interface CreateFundingAllocationRequest {
  entity_name: string;
  entity_type: string;
  allocation_amount: number;
  currency?: string;
  fiscal_year: number;
  fiscal_quarter?: number;
  purpose?: string;
  restrictions?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
}

export interface UpdateFundingAllocationRequest {
  entity_name?: string;
  entity_type?: string;
  allocation_amount?: number;
  currency?: string;
  fiscal_year?: number;
  fiscal_quarter?: number;
  purpose?: string;
  restrictions?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
}

export interface FundingRequest {
  id: number;
  request_id: string;
  entity_name: string;
  entity_type: string;
  requested_amount: number;
  currency: string;
  fiscal_year: number;
  fiscal_quarter: number | null;
  purpose: string;
  justification: string | null;
  status: string;
  requested_by: string;
  requested_at: string;
  reviewed_by: string | null;
  reviewed_at: string | null;
  approval_notes: string | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface FundingRequestListResponse {
  requests: FundingRequest[];
  total: number;
}

export interface CreateFundingRequest {
  entity_name: string;
  entity_type: string;
  requested_amount: number;
  currency?: string;
  fiscal_year: number;
  fiscal_quarter?: number;
  purpose: string;
  justification?: string;
  metadata?: Record<string, unknown>;
}

export interface ReviewFundingRequest {
  status: string;
  approval_notes?: string;
  allocated_amount?: number;
}

export interface FundingSummary {
  entity_summary: Array<{
    entity_name: string;
    entity_type: string;
    total_allocated: number;
    total_disbursed: number;
    allocation_count: number;
  }>;
  total_by_status: {
    pending: number;
    approved: number;
    disbursed: number;
    rejected: number;
  };
  fiscal_year: number | null;
  timestamp: string;
}

// ── Constants ──────────────────────────────────────────────────────────────

const BACKEND_URL = "/api";
const DEFAULT_MAX_RETRIES = 3;
const DEFAULT_BASE_DELAY_MS = 1000;
const TOKEN_KEY = "hyba_auth_token";
export const PULVINI_HASHRATE_CAP_EHS = 1;

// ── Token Management ───────────────────────────────────────────────────────

export function assertPulviniHashrateCap(value: number | undefined, field: string): void {
  if (value === undefined) return;
  if (!Number.isFinite(value) || value < 0 || value > PULVINI_HASHRATE_CAP_EHS) {
    throw new Error(`${field} must be between 0 and ${PULVINI_HASHRATE_CAP_EHS} EH/s`);
  }
}

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string): void {
  try {
    localStorage.setItem(TOKEN_KEY, token);
  } catch {
    // noop
  }
}

export function clearToken(): void {
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

// ── Error Handling ─────────────────────────────────────────────────────────

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

// ── Retry Logic ────────────────────────────────────────────────────────────

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
      await new Promise((resolve) => setTimeout(resolve, delay + secureUnitInterval() * 100));
      lastError = await parseApiError(response);
    } catch (error) {
      if (attempt >= maxRetries) throw error;
      const delay = calculateDelay(attempt, baseDelayMs, maxDelayMs);
      await new Promise((resolve) => setTimeout(resolve, delay + secureUnitInterval() * 100));
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

async function put<T>(
  path: string,
  body: unknown,
  retryOptions?: Partial<RetryOptions>,
): Promise<T> {
  const response = await fetchWithRetry(
    `${BACKEND_URL}${path}`,
    { method: "PUT", body: JSON.stringify(body) },
    retryOptions,
  );
  if (!response.ok) throw await parseApiError(response);
  return response.json() as Promise<T>;
}

async function del<T = void>(
  path: string,
  retryOptions?: Partial<RetryOptions>,
): Promise<T> {
  const response = await fetchWithRetry(
    `${BACKEND_URL}${path}`,
    { method: "DELETE" },
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

// ═══════════════════════════════════════════════════════════════════════════
//  HEALTH ENDPOINTS
// ═══════════════════════════════════════════════════════════════════════════

/** GET /api/health — Full health status with telemetry */
export async function getHealth(): Promise<HealthResponse> {
  return get<HealthResponse>("/health");
}

/** GET /api/health/live — Liveness probe */
export async function getHealthLiveness(): Promise<HealthLivenessResponse> {
  return get<HealthLivenessResponse>("/health/live");
}

/** GET /api/health/readiness — Readiness probe */
export async function getHealthReadiness(): Promise<HealthReadinessResponse> {
  return get<HealthReadinessResponse>("/health/readiness");
}

/** GET /api/health/ready — Legacy ready endpoint */
export async function getHealthReady(): Promise<{ ready: boolean; status: string }> {
  return get<{ ready: boolean; status: string }>("/health/ready");
}

// ═══════════════════════════════════════════════════════════════════════════
//  AUTH ENDPOINTS
// ═══════════════════════════════════════════════════════════════════════════

/** POST /api/auth/login — Authenticate and receive JWT token */
export async function loginApi(credentials: AuthCredentials): Promise<AuthResponse> {
  const options = authInterceptor({ method: "POST", body: JSON.stringify(credentials) });
  const response = await fetch(`${BACKEND_URL}/auth/login`, options);
  if (!response.ok) throw await parseApiError(response);
  const data = (await response.json()) as AuthResponse;
  if (data.token) setToken(data.token);
  return data;
}

/** POST /api/auth/register — Register a new user */
export async function registerApi(data: RegisterData): Promise<AuthResponse> {
  const options = authInterceptor({ method: "POST", body: JSON.stringify(data) });
  const response = await fetch(`${BACKEND_URL}/auth/register`, options);
  if (!response.ok) throw await parseApiError(response);
  return response.json() as Promise<AuthResponse>;
}

/** GET /api/auth/profile — Fetch current user profile */
export async function fetchProfileApi(): Promise<Response> {
  return fetch(`${BACKEND_URL}/auth/profile`, authInterceptor({ method: "GET" }));
}

/** GET /api/products — List products */
export async function fetchProductsApi(): Promise<Response> {
  return fetch(`${BACKEND_URL}/products`, authInterceptor({ method: "GET" }));
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

// ═══════════════════════════════════════════════════════════════════════════
//  MINING — CORE ENDPOINTS
// ═══════════════════════════════════════════════════════════════════════════

/** GET /api/mining/pools — List all available mining pools */
export async function getMiningPools(): Promise<PoolsResponse> {
  return get<PoolsResponse>("/mining/pools");
}

/** GET /api/mining/pool-config — Get current pool configuration */
export async function fetchPoolConfig(): Promise<PoolConfigResponse> {
  return get<PoolConfigResponse>("/mining/pool-config", { maxRetries: 1, baseDelayMs: 250 });
}

/** POST /api/mining/pool-config — Configure a pool */
export async function configurePool(data: ConfigurePoolRequest): Promise<ConfigurePoolResponse> {
  return post<ConfigurePoolResponse>("/mining/pool-config", data, { maxRetries: 0 });
}

/** POST /api/mining/connect — Connect to a pool */
export async function connectToPool(data: ConnectPoolRequest): Promise<ConnectPoolResponse> {
  assertPulviniHashrateCap(data.capacity_ehs, "capacity_ehs");
  return post<ConnectPoolResponse>(
    "/mining/connect",
    { ...data, switch: data.switch ?? true },
    { maxRetries: 0 },
  );
}

/** POST /api/mining/switch — Switch to a different pool */
export async function switchPool(data: ConnectPoolRequest): Promise<ConnectPoolResponse> {
  assertPulviniHashrateCap(data.capacity_ehs, "capacity_ehs");
  return post<ConnectPoolResponse>("/mining/switch", { ...data, switch: true }, { maxRetries: 0 });
}

/** POST /api/mining/disconnect — Disconnect from current pool */
export async function disconnectFromPool(): Promise<{ status: string; previous_pool?: string }> {
  return post<{ status: string; previous_pool?: string }>(
    "/mining/disconnect",
    {},
    { maxRetries: 0 },
  );
}

/** POST /api/mining/submit — Submit a mining job share */
export async function submitJob(data: SubmitJobRequest): Promise<SubmitJobResponse> {
  assertPulviniHashrateCap(data.hashrate_ehs, "hashrate_ehs");
  return post<SubmitJobResponse>("/mining/submit", data);
}

/** POST /api/mining/pause — Pause mining operations */
export async function pauseMining(): Promise<{ status: string; midas_state?: string }> {
  return post<{ status: string; midas_state?: string }>("/mining/pause", {}, { maxRetries: 0 });
}

/** POST /api/mining/resume — Resume mining operations */
export async function resumeMining(): Promise<{ status: string; midas_state?: string }> {
  return post<{ status: string; midas_state?: string }>("/mining/resume", {}, { maxRetries: 0 });
}

/** POST /api/mining/power — Update power scale */
export async function updatePowerScale(
  scale: number,
  phiTier = 12,
): Promise<{ status: string; effective_hashrate_ehs?: number; phi_tier?: number }> {
  return post<{ status: string; effective_hashrate_ehs?: number; phi_tier?: number }>(
    "/mining/power",
    { scale, phi_tier: phiTier },
  );
}

/** GET /api/mining/status — Get current mining status */
export async function getMiningStatus(): Promise<MiningStatusResponse> {
  return get<MiningStatusResponse>("/mining/status");
}

/** GET /api/mining/health — Get mining subsystem health */
export async function getMiningHealth(): Promise<MiningHealthResponse> {
  return get<MiningHealthResponse>("/mining/health");
}

/** GET /api/mining/stats — Get mining statistics */
export async function getMiningStats(): Promise<MiningStatsResponse> {
  return get<MiningStatsResponse>("/mining/stats");
}

/** GET /api/mining/daemon — Get daemon info */
export async function getMiningDaemon(): Promise<MiningDaemonResponse> {
  return get<MiningDaemonResponse>("/mining/daemon");
}

/** GET /api/mining/job — Get current mining job */
export async function getMiningJob(): Promise<MiningJobResponse> {
  return get<MiningJobResponse>("/mining/job");
}

/** GET /api/mining/jobs/search — Search mining jobs */
export async function searchMiningJobs(params?: {
  pool_id?: string;
  worker?: string;
  limit?: number;
  offset?: number;
}): Promise<MiningJobsSearchResponse> {
  const search = new URLSearchParams();
  if (params?.pool_id) search.append("pool_id", params.pool_id);
  if (params?.worker) search.append("worker", params.worker);
  if (params?.limit) search.append("limit", String(params.limit));
  if (params?.offset) search.append("offset", String(params.offset));
  const qs = search.toString();
  return get<MiningJobsSearchResponse>(`/mining/jobs/search${qs ? `?${qs}` : ""}`);
}

// ═══════════════════════════════════════════════════════════════════════════
//  MINING — OPS ENDPOINTS
// ═══════════════════════════════════════════════════════════════════════════

/** GET /api/mining/ops/audit — Get mining ops audit log */
export async function getMiningOpsAudit(params?: {
  limit?: number;
  offset?: number;
}): Promise<MiningOpsAuditResponse> {
  const search = new URLSearchParams();
  if (params?.limit) search.append("limit", String(params.limit));
  if (params?.offset) search.append("offset", String(params.offset));
  const qs = search.toString();
  return get<MiningOpsAuditResponse>(`/mining/ops/audit${qs ? `?${qs}` : ""}`);
}

/** GET /api/mining/ops/autonomics — Get autonomics metrics */
export async function getMiningOpsAutonomics(): Promise<MiningOpsAutonomicsResponse> {
  return get<MiningOpsAutonomicsResponse>("/mining/ops/autonomics");
}

/** GET /api/mining/ops/metrics — Get ops metrics */
export async function getMiningOpsMetrics(): Promise<MiningOpsMetricsResponse> {
  return get<MiningOpsMetricsResponse>("/mining/ops/metrics");
}

/** GET /api/mining/ops/profitability — Get profitability metrics */
export async function getMiningOpsProfitability(): Promise<MiningOpsProfitabilityResponse> {
  return get<MiningOpsProfitabilityResponse>("/mining/ops/profitability");
}

// ═══════════════════════════════════════════════════════════════════════════
//  MINING — PRODUCTION (v1) ENDPOINTS
// ═══════════════════════════════════════════════════════════════════════════

/** GET /api/v1/mining-production/health — Production pipeline health */
export async function getMiningProductionHealth(): Promise<MiningProductionHealthResponse> {
  return get<MiningProductionHealthResponse>("/v1/mining-production/health");
}

/** POST /api/v1/mining-production/initialize — Initialize mining pipeline */
export async function initializeMiningProduction(): Promise<MiningProductionInitializeResponse> {
  return post<MiningProductionInitializeResponse>("/v1/mining-production/initialize", {});
}

/** GET /api/v1/mining-production/metrics — Production pipeline metrics */
export async function getMiningProductionMetrics(): Promise<MiningProductionMetricsResponse> {
  return get<MiningProductionMetricsResponse>("/v1/mining-production/metrics");
}

/** GET /api/v1/mining-production/next-job — Get next mining job */
export async function getMiningProductionNextJob(): Promise<MiningProductionNextJobResponse> {
  return get<MiningProductionNextJobResponse>("/v1/mining-production/next-job");
}

/** POST /api/v1/mining-production/start — Start production mining */
export async function startMiningProduction(): Promise<MiningProductionStartResponse> {
  return post<MiningProductionStartResponse>("/v1/mining-production/start", {});
}

/** GET /api/v1/mining-production/status — Production pipeline status */
export async function getMiningProductionStatus(): Promise<MiningProductionStatusResponse> {
  return get<MiningProductionStatusResponse>("/v1/mining-production/status");
}

/** POST /api/v1/mining-production/stop — Stop production mining */
export async function stopMiningProduction(): Promise<MiningProductionStopResponse> {
  return post<MiningProductionStopResponse>("/v1/mining-production/stop", {});
}

/** POST /api/v1/mining-production/submit-share — Submit share via production pipeline */
export async function submitMiningProductionShare(
  data: MiningProductionSubmitShareRequest,
): Promise<MiningProductionSubmitShareResponse> {
  return post<MiningProductionSubmitShareResponse>("/v1/mining-production/submit-share", data);
}

// ═══════════════════════════════════════════════════════════════════════════
//  POOLS (v1) ENDPOINTS
// ═══════════════════════════════════════════════════════════════════════════

/** GET /api/v1/pools/current — Get current connected pool */
export async function getV1PoolsCurrent(): Promise<V1PoolsCurrentResponse> {
  return get<V1PoolsCurrentResponse>("/v1/pools/current");
}

/** GET /api/v1/pools/default — Get default pool */
export async function getV1PoolsDefault(): Promise<V1PoolsDefaultResponse> {
  return get<V1PoolsDefaultResponse>("/v1/pools/default");
}

/** GET /api/v1/pools/enabled — Get enabled pools */
export async function getV1PoolsEnabled(): Promise<V1PoolsEnabledResponse> {
  return get<V1PoolsEnabledResponse>("/v1/pools/enabled");
}

/** GET /api/v1/pools/health — Pool health check */
export async function getV1PoolsHealth(): Promise<V1PoolsHealthResponse> {
  return get<V1PoolsHealthResponse>("/v1/pools/health");
}

/** GET /api/v1/pools/list — List all pools with configuration */
export async function getV1PoolsList(): Promise<V1PoolsListResponse> {
  return get<V1PoolsListResponse>("/v1/pools/list");
}

/** POST /api/v1/pools/report-share — Report a share */
export async function reportV1PoolShare(
  data: V1PoolsReportShareRequest,
): Promise<{ status: string }> {
  return post<{ status: string }>("/v1/pools/report-share", data);
}

/** GET /api/v1/pools/status — Pool connection status */
export async function getV1PoolsStatus(): Promise<V1PoolsStatusResponse> {
  return get<V1PoolsStatusResponse>("/v1/pools/status");
}

/** POST /api/v1/pools/switch — Switch active pool */
export async function switchV1Pool(data: V1PoolsSwitchRequest): Promise<V1PoolsSwitchResponse> {
  return post<V1PoolsSwitchResponse>("/v1/pools/switch", data);
}

// ═══════════════════════════════════════════════════════════════════════════
//  INTELLIGENCE — v1 ENDPOINTS
// ═══════════════════════════════════════════════════════════════════════════

/** GET /api/v1/intelligence/health — Intelligence subsystem health */
export async function getIntelligenceV1Health(): Promise<IntelligenceV1HealthResponse> {
  return get<IntelligenceV1HealthResponse>("/v1/intelligence/health");
}

/** GET /api/v1/intelligence/audit — Intelligence audit data */
export async function getIntelligenceV1Audit(): Promise<IntelligenceV1AuditResponse> {
  return get<IntelligenceV1AuditResponse>("/v1/intelligence/audit");
}

/** GET /api/v1/intelligence/absolute-audit — Full intelligence audit */
export async function getIntelligenceV1AbsoluteAudit(): Promise<IntelligenceV1AbsoluteAuditResponse> {
  return get<IntelligenceV1AbsoluteAuditResponse>("/v1/intelligence/absolute-audit");
}

/** POST /api/v1/intelligence/scale — Scale intelligence */
export async function scaleIntelligence(
  scale: number,
  target = "reflexive_controller",
): Promise<{ status: string; intelligence_scale: number }> {
  return post<{ status: string; intelligence_scale: number }>("/v1/intelligence/scale", {
    scale,
    target,
  });
}

/** POST /api/v1/intelligence/consciousness/boost — Boost consciousness */
export async function boostConsciousness(
  boost: number,
  taskBudget = 1,
): Promise<{ status: string; boost: number; task_budget: number }> {
  return post<{ status: string; boost: number; task_budget: number }>(
    "/v1/intelligence/consciousness/boost",
    { boost, task_budget: taskBudget },
  );
}

/** POST /api/v1/intelligence/reflect — Trigger reflection cycle */
export async function intelligenceReflect(
  data?: IntelligenceV1ReflectRequest,
): Promise<IntelligenceV1ReflectResponse> {
  return post<IntelligenceV1ReflectResponse>("/v1/intelligence/reflect", data || {});
}

/** POST /api/v1/intelligence/explain — Request explanation */
export async function intelligenceExplain(
  data: IntelligenceV1ExplainRequest,
): Promise<IntelligenceV1ExplainResponse> {
  return post<IntelligenceV1ExplainResponse>("/v1/intelligence/explain", data);
}

/** POST /api/v1/intelligence/orchestrate — Orchestrate multi-step plan */
export async function intelligenceOrchestrate(
  data: IntelligenceV1OrchestrateRequest,
): Promise<IntelligenceV1OrchestrateResponse> {
  return post<IntelligenceV1OrchestrateResponse>("/v1/intelligence/orchestrate", data);
}

/** POST /api/v1/intelligence/closure/sync — Sync closure state */
export async function intelligenceClosureSync(): Promise<IntelligenceV1ClosureSyncResponse> {
  return post<IntelligenceV1ClosureSyncResponse>("/v1/intelligence/closure/sync", {});
}

/** POST /api/v1/intelligence/heartbeat/pulse — Send heartbeat pulse */
export async function intelligenceHeartbeatPulse(): Promise<IntelligenceV1HeartbeatPulseResponse> {
  return post<IntelligenceV1HeartbeatPulseResponse>("/v1/intelligence/heartbeat/pulse", {});
}

// ═══════════════════════════════════════════════════════════════════════════
//  AI ENDPOINTS
// ═══════════════════════════════════════════════════════════════════════════

/** GET /api/ai/consciousness — Get consciousness status */
export async function getConsciousness(): Promise<ConsciousnessResponse> {
  return get<ConsciousnessResponse>("/ai/consciousness");
}

/** POST /api/ai/consciousness/stimulate — Stimulate consciousness */
export async function stimulateConsciousness(
  data: AiStimulateRequest,
): Promise<AiStimulateResponse> {
  return post<AiStimulateResponse>("/ai/consciousness/stimulate", data);
}

/** POST /api/ai/chat — Send chat message */
export async function aiChat(data: AiChatRequest): Promise<AiChatResponse> {
  return post<AiChatResponse>("/ai/chat", data);
}

// ═══════════════════════════════════════════════════════════════════════════
//  SECURITY ENDPOINTS
// ═══════════════════════════════════════════════════════════════════════════

/** GET /api/security/status — Get security status */
export async function getSecurityStatus(): Promise<SecurityStatus> {
  return get<SecurityStatus>("/security/status");
}

/** POST /api/security/shield — Activate/deactivate security shield */
export async function securityShield(
  data: SecurityShieldRequest,
): Promise<SecurityShieldResponse> {
  return post<SecurityShieldResponse>("/security/shield", data);
}

// ═══════════════════════════════════════════════════════════════════════════
//  UNIFIED ENDPOINTS
// ═══════════════════════════════════════════════════════════════════════════

/** GET /api/v1/unified/health — Unified subsystem health */
export async function getUnifiedHealth(): Promise<UnifiedHealthResponse> {
  return get<UnifiedHealthResponse>("/v1/unified/health");
}

/** GET /api/v1/unified/status — Unified subsystem status */
export async function getUnifiedStatus(): Promise<UnifiedStatusResponse> {
  return get<UnifiedStatusResponse>("/v1/unified/status");
}

/** GET /api/v1/unified/metrics — Unified metrics */
export async function getUnifiedMetrics(): Promise<UnifiedMetricsResponse> {
  return get<UnifiedMetricsResponse>("/v1/unified/metrics");
}

/** POST /api/v1/unified/analyze/blockchain — Analyze blockchain data */
export async function analyzeBlockchainSnapshot(
  blocks: Array<{ height: number; block_hash: string }>,
): Promise<Record<string, unknown>> {
  return post<Record<string, unknown>>("/v1/unified/analyze/blockchain", { blocks });
}

/** POST /api/v1/unified/analyze/it-from-bit — Analyze it-from-bit data */
export async function analyzeItFromBit(bits: string, wordSize = 8): Promise<Record<string, unknown>> {
  return post<Record<string, unknown>>("/v1/unified/analyze/it-from-bit", {
    bits,
    word_size: wordSize,
  });
}

/** POST /api/v1/unified/analyze/resonance — Analyze resonance data */
export async function analyzeResonance(
  data: UnifiedAnalyzeResonanceRequest,
): Promise<Record<string, unknown>> {
  return post<Record<string, unknown>>("/v1/unified/analyze/resonance", data);
}

/** POST /api/v1/unified/share-result — Share a result */
export async function unifiedShareResult(
  data: UnifiedShareResultRequest,
): Promise<{ status: string; accepted: boolean }> {
  return post<{ status: string; accepted: boolean }>("/v1/unified/share-result", data);
}

// ═══════════════════════════════════════════════════════════════════════════
//  MEMORY ENDPOINTS
// ═══════════════════════════════════════════════════════════════════════════

/** GET /api/v1/memory/evidence — Get memory evidence */
export async function getMemoryEvidence(params?: {
  type?: string;
  limit?: number;
  offset?: number;
}): Promise<MemoryEvidenceResponse> {
  const search = new URLSearchParams();
  if (params?.type) search.append("type", params.type);
  if (params?.limit) search.append("limit", String(params.limit));
  if (params?.offset) search.append("offset", String(params.offset));
  const qs = search.toString();
  return get<MemoryEvidenceResponse>(`/v1/memory/evidence${qs ? `?${qs}` : ""}`);
}

/** GET /api/v1/memory/health — Memory subsystem health */
export async function getMemoryHealth(): Promise<MemoryHealthResponse> {
  return get<MemoryHealthResponse>("/v1/memory/health");
}

/** GET /api/v1/memory/memories — List memories */
export async function getMemories(params?: {
  type?: string;
  limit?: number;
  offset?: number;
  sort?: string;
}): Promise<MemoryListResponse> {
  const search = new URLSearchParams();
  if (params?.type) search.append("type", params.type);
  if (params?.limit) search.append("limit", String(params.limit));
  if (params?.offset) search.append("offset", String(params.offset));
  if (params?.sort) search.append("sort", params.sort);
  const qs = search.toString();
  return get<MemoryListResponse>(`/v1/memory/memories${qs ? `?${qs}` : ""}`);
}

/** GET /api/v1/memory/memory/{memory_key} — Get a specific memory */
export async function getMemoryByKey(memoryKey: string): Promise<MemoryEntry> {
  return get<MemoryEntry>(`/v1/memory/memory/${encodeURIComponent(memoryKey)}`);
}

/** GET /api/v1/memory/snapshots — List memory snapshots */
export async function getMemorySnapshots(): Promise<MemorySnapshotsResponse> {
  return get<MemorySnapshotsResponse>("/v1/memory/snapshots");
}

// ═══════════════════════════════════════════════════════════════════════════
//  OTHER ENDPOINTS
// ═══════════════════════════════════════════════════════════════════════════

/** POST /api/pulvini/execute — Execute Pulvini operation */
export async function executePulvini(): Promise<PulviniResult> {
  return post<PulviniResult>("/pulvini/execute", {});
}

/** POST /api/predict — Request prediction */
export async function requestPrediction(
  payload: Record<string, unknown>,
): Promise<PredictionResult> {
  return post<PredictionResult>("/predict", payload);
}

/** GET /api/pitfalls — Get mining pitfalls */
export async function getPitfalls(): Promise<PitfallsResponse> {
  return get<PitfallsResponse>("/pitfalls");
}

/** GET /api/substrate — Get substrate status */
export async function getSubstrate(): Promise<SubstrateResponse> {
  return get<SubstrateResponse>("/substrate");
}

/** POST /api/toe/experiments — Run ToE experiment */
export async function runToeExperiment(
  data: ToeExperimentsRequest,
): Promise<ToeExperimentsResponse> {
  return post<ToeExperimentsResponse>("/toe/experiments", data);
}

// ═══════════════════════════════════════════════════════════════════════════
//  AGGREGATE / COMPOSITE ENDPOINTS
// ═══════════════════════════════════════════════════════════════════════════

/** Fetch all telemetry data in parallel (health + consciousness + pools + security) */
export async function fetchTelemetryData(): Promise<TelemetryData> {
  const start = performance.now();
  const health = await getHealth();
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

// ═══════════════════════════════════════════════════════════════════════════
//  ADMIN ENDPOINTS
// ═══════════════════════════════════════════════════════════════════════════

/** GET /api/admin/stats — Get admin dashboard stats */
export async function getAdminStats(): Promise<AdminStats> {
  return get<AdminStats>("/admin/stats");
}

/** GET /api/admin/users — List admin users */
export async function getAdminUsers(
  skip = 0,
  limit = 50,
  search?: string,
): Promise<AdminUserListResponse> {
  const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
  if (search) params.append("search", search);
  return get<AdminUserListResponse>(`/admin/users?${params.toString()}`);
}

/** POST /api/admin/users — Create admin user */
export async function createAdminUser(
  data: CreateAdminUserRequest,
): Promise<AdminUser> {
  return post<AdminUser>("/admin/users", data, { maxRetries: 0 });
}

/** GET /api/admin/users/{user_id} — Get admin user by ID */
export async function getAdminUser(userId: number): Promise<AdminUser> {
  return get<AdminUser>(`/admin/users/${userId}`);
}

/** PUT /api/admin/users/{user_id} — Update admin user */
export async function updateAdminUser(
  userId: number,
  data: UpdateAdminUserRequest,
): Promise<AdminUser> {
  return put<AdminUser>(`/admin/users/${userId}`, data, { maxRetries: 0 });
}

/** DELETE /api/admin/users/{user_id} — Delete admin user */
export async function deleteAdminUser(userId: number): Promise<void> {
  await del(`/admin/users/${userId}`, { maxRetries: 0 });
}

/** GET /api/admin/audit-logs — Get audit logs */
export async function getAuditLogs(
  skip = 0,
  limit = 100,
  action?: string,
  target_type?: string,
  actor_username?: string,
): Promise<AuditLogListResponse> {
  const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
  if (action) params.append("action", action);
  if (target_type) params.append("target_type", target_type);
  if (actor_username) params.append("actor_username", actor_username);
  return get<AuditLogListResponse>(`/admin/audit-logs?${params.toString()}`);
}

/** GET /api/admin/funding/allocations — Get funding allocations */
export async function getFundingAllocations(
  skip = 0,
  limit = 50,
  entity_name?: string,
  entity_type?: string,
  status?: string,
  fiscal_year?: number,
): Promise<FundingAllocationListResponse> {
  const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
  if (entity_name) params.append("entity_name", entity_name);
  if (entity_type) params.append("entity_type", entity_type);
  if (status) params.append("status", status);
  if (fiscal_year) params.append("fiscal_year", String(fiscal_year));
  return get<FundingAllocationListResponse>(`/admin/funding/allocations?${params.toString()}`);
}

/** POST /api/admin/funding/allocations — Create funding allocation */
export async function createFundingAllocation(
  data: CreateFundingAllocationRequest,
): Promise<FundingAllocation> {
  return post<FundingAllocation>("/admin/funding/allocations", data, { maxRetries: 0 });
}

/** PUT /api/admin/funding/allocations/{allocation_id} — Update funding allocation */
export async function updateFundingAllocation(
  allocationId: number,
  data: UpdateFundingAllocationRequest,
): Promise<FundingAllocation> {
  return put<FundingAllocation>(`/admin/funding/allocations/${allocationId}`, data, {
    maxRetries: 0,
  });
}

/** POST /api/admin/funding/allocations/{allocation_id}/disburse — Disburse funding */
export async function disburseFunding(allocationId: number): Promise<FundingAllocation> {
  return post<FundingAllocation>(
    `/admin/funding/allocations/${allocationId}/disburse`,
    {},
    { maxRetries: 0 },
  );
}

/** GET /api/admin/funding/requests — Get funding requests */
export async function getFundingRequests(
  skip = 0,
  limit = 50,
  entity_name?: string,
  entity_type?: string,
  status?: string,
  fiscal_year?: number,
): Promise<FundingRequestListResponse> {
  const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
  if (entity_name) params.append("entity_name", entity_name);
  if (entity_type) params.append("entity_type", entity_type);
  if (status) params.append("status", status);
  if (fiscal_year) params.append("fiscal_year", String(fiscal_year));
  return get<FundingRequestListResponse>(`/admin/funding/requests?${params.toString()}`);
}

/** POST /api/admin/funding/requests — Create funding request */
export async function createFundingRequest(
  data: CreateFundingRequest,
): Promise<FundingRequest> {
  return post<FundingRequest>("/admin/funding/requests", data, { maxRetries: 0 });
}

/** PUT /api/admin/funding/requests/{request_id}/review — Review funding request */
export async function reviewFundingRequest(
  requestId: string,
  data: ReviewFundingRequest,
): Promise<FundingRequest> {
  return put<FundingRequest>(`/admin/funding/requests/${requestId}/review`, data, {
    maxRetries: 0,
  });
}

/** GET /api/admin/funding/summary — Get funding summary */
export async function getFundingSummary(fiscal_year?: number): Promise<FundingSummary> {
  const params = new URLSearchParams();
  if (fiscal_year) params.append("fiscal_year", String(fiscal_year));
  return get<FundingSummary>(`/admin/funding/summary?${params.toString()}`);
}