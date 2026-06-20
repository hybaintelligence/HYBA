/**
 * HYBA Secure Bridge — Production-Grade Express Gateway
 *
 * Architecture:
 *   Browser ──► Express (Helmet + Rate-Limit) ──► FastAPI Backend
 *                                        │
 *                                        └── Static SPA (built or Vite dev)
 *
 * Design principles:
 *   - Circuit breaker for backend proxy calls
 *   - Structured request ID propagation
 *   - Rate limiting with graduated backoff
 *   - Public-safe health plus protected internal metrics
 *   - Graceful shutdown with connection drain
 *   - Zero fabricated responses — degraded mode when backend is unavailable
 *   - No JWT signing secret is ever transmitted as an access token
 *
 * Environment variables:
 *   NODE_ENV                          Set "production" to lock down internal routes
 *   HYBA_ALLOW_DEV_INTERNAL_ROUTES    Allow internal routes without token (dev only, default false)
 *   HYBA_SWARM_HEARTBEAT_INTERVAL_MS  Security swarm heartbeat (default 3000ms, was 100ms)
 *   HYBA_PROXY_BODY_SIZE_LIMIT        Max body size for proxied routes (default 10MB, returns 413)
 *   HYBA_ENABLE_MINING_AUTOCONNECT    Auto-connect to ViaBTC on startup (default false)
 *   HYBA_INTERNAL_HEALTH_TOKEN        Token for /bridge/internal/* routes
 *   JWT_SECRET                        Required in production; auto-generated dev fallback
 *   PULVINI_BACKEND_URL               FastAPI backend URL (default http://127.0.0.1:3001)
 *   HYBA_SPAWN_BACKEND                Auto-spawn FastAPI subprocess (default true)
 *   LOG_LEVEL                         pino log level (default "info")
 *   HOST                              Express listen address (default 0.0.0.0)
 *   PORT                              Express listen port (default 3000)
 *   HYBA_CSP_CONNECT_SRC              Extra CSP connect-src origins (comma-separated)
 */

import compression from "compression";
import dotenv from "dotenv";
import express, { type NextFunction, type Request, type Response } from "express";
import helmet from "helmet";
import path from "node:path";
import os from "node:os";
import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";
import { createServer, type Server } from "node:http";
import { createHash, createHmac, randomBytes, randomUUID } from "node:crypto";
import pino from "pino";
import pinoHttp from "pino-http";
import rateLimit from "express-rate-limit";
import { createServer as createViteServer, type InlineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { validateProductionJwtSecret } from "./bridge_security";
import { securitySwarms } from "./core/security_swarm";
import { IntelligenceService } from "./core/intelligence_service";
import {
  MonthlyQuotaLedger,
  loadBillingPlans,
  loadTenantBillingConfig,
  parseBillingUnits,
  sanitizeTenantId,
} from "./core/billing";

dotenv.config();

const logger = pino({
  name: "hyba-secure-bridge",
  level: process.env.LOG_LEVEL || "info",
  base: { service: "hyba-secure-bridge", env: process.env.NODE_ENV || "development" },
  formatters: { level: (label) => ({ level: label }) },
  timestamp: pino.stdTimeFunctions.isoTime,
});

const TRUE_VALUES = new Set(["1", "true", "yes", "on"]);

const CONFIG = {
  isProduction: process.env.NODE_ENV === "production",
  allowDevInternalRoutes: TRUE_VALUES.has(
    (process.env.HYBA_ALLOW_DEV_INTERNAL_ROUTES || "false").toLowerCase(),
  ),
  host: process.env.HOST || "0.0.0.0",
  port: Number(process.env.PORT || 3000),
  backendUrl: normalizeBackendUrl(process.env.PULVINI_BACKEND_URL || "http://127.0.0.1:3001"),
  shouldSpawnBackend: process.env.HYBA_SPAWN_BACKEND !== "false",
  enableMiningAutoConnect: TRUE_VALUES.has(
    (process.env.HYBA_ENABLE_MINING_AUTOCONNECT || "false").toLowerCase(),
  ),
  proxyTimeoutMs: Number(process.env.BACKEND_PROXY_TIMEOUT_MS || 30000),
  rateLimitWindowMs: Number(process.env.RATE_LIMIT_WINDOW_MS || 60000),
  rateLimitMax: Number(process.env.RATE_LIMIT_MAX || 100),
  jwtSecret: process.env.JWT_SECRET || "",
  internalHealthToken: process.env.HYBA_INTERNAL_HEALTH_TOKEN || "",
  cspConnectSrc: parseCspConnectSrc(process.env.HYBA_CSP_CONNECT_SRC),
  swarmHeartbeatIntervalMs: Number(process.env.HYBA_SWARM_HEARTBEAT_INTERVAL_MS || 3000),
  proxyBodySizeLimit: Number(process.env.HYBA_PROXY_BODY_SIZE_LIMIT || 10 * 1024 * 1024),
  billingEnforcementEnabled: process.env.HYBA_BILLING_ENFORCEMENT !== "false",
} as const;

interface CircuitState {
  failures: number;
  lastFailureTime: number;
  isOpen: boolean;
  halfOpenAttempted: boolean;
}

const circuitState: CircuitState = {
  failures: 0,
  lastFailureTime: 0,
  isOpen: false,
  halfOpenAttempted: false,
};
const CIRCUIT_THRESHOLD = 5;
const CIRCUIT_RESET_MS = 30_000;
const CIRCUIT_HALF_OPEN_MS = 10_000;
const HEALTH_CHECK_FAILURE_THRESHOLD = 3;
const HEALTH_CHECK_FAILURE_WINDOW_MS = 60_000;
const LATENCY_WARNING_THRESHOLD_MS = 5000;
const LATENCY_CRITICAL_THRESHOLD_MS = 10000;

const metrics = {
  requestsTotal: 0,
  requestsByPath: new Map<string, number>(),
  proxyErrors: 0,
  circuitBreakerTrips: 0,
  healthCheckFailures: 0,
  firstHealthCheckFailure: 0,
  lastHealthCheckFailure: 0,
  backendLatencyMs: 0,
  highLatencyCount: 0,
  lastHighLatencyTime: 0,
  billingUnitsTotal: 0,
  billingRejectedTotal: 0,
  startTime: Date.now(),
};

function normalizeBackendUrl(value: string): URL {
  const parsed = new URL(value);
  if (!["http:", "https:"].includes(parsed.protocol)) {
    throw new Error(`PULVINI_BACKEND_URL must be http(s), received ${parsed.protocol}`);
  }
  return parsed;
}

function parseCspConnectSrc(raw: string | undefined): string[] {
  const defaults = [
    "'self'",
    "https://identitytoolkit.googleapis.com",
    "https://securetoken.googleapis.com",
    "https://firestore.googleapis.com",
    "https://*.googleapis.com",
    "https://*.firebaseio.com",
    "https://*.firebaseapp.com",
    "https://generativelanguage.googleapis.com",
  ];
  const extras = (raw || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
  return Array.from(new Set([...defaults, ...extras]));
}

function getPythonCommand(): string {
  return process.env.PYTHON || (process.platform === "win32" ? "python" : "python3");
}

function getBackendPort(): string {
  if (CONFIG.backendUrl.port) return CONFIG.backendUrl.port;
  return CONFIG.backendUrl.protocol === "https:" ? "443" : "80";
}

function getViteCacheDir(projectRoot: string): string {
  const projectHash = createHash("sha256").update(projectRoot).digest("hex").slice(0, 12);
  return path.join(os.tmpdir(), "hyba-vite-cache", projectHash);
}

function generateRequestId(): string {
  return `req_${randomUUID()}`;
}

function base64url(input: Buffer | string): string {
  return Buffer.from(input).toString("base64url");
}

function createInternalMiningJwt(): string | null {
  if (!CONFIG.jwtSecret) return null;
  const now = Math.floor(Date.now() / 1000);
  const header = { alg: "HS256", typ: "JWT" };
  const payload = {
    sub: "hyba-bridge-autoconnect",
    username: "hyba_bridge",
    roles: ["mining:operate", "mining_operator"],
    exp: now + 5 * 60,
    iat: now,
    iss: "genesis.hyba.ai",
    jti: randomBytes(16).toString("hex"),
  };
  const signingInput = `${base64url(JSON.stringify(header))}.${base64url(JSON.stringify(payload))}`;
  const signature = createHmac("sha256", CONFIG.jwtSecret).update(signingInput).digest("base64url");
  return `${signingInput}.${signature}`;
}

function requireInternalAccess(req: Request, res: Response, next: NextFunction): void {
  if (!CONFIG.isProduction && CONFIG.allowDevInternalRoutes) {
    next();
    return;
  }
  if (!CONFIG.internalHealthToken) {
    res.status(404).json({ error: "not_found", message: "Internal diagnostics are not exposed" });
    return;
  }
  if (req.headers["x-hyba-internal-token"] === CONFIG.internalHealthToken) {
    next();
    return;
  }
  res.status(404).json({ error: "not_found", message: "Internal diagnostics are not exposed" });
}

function noStore(res: Response): void {
  res.setHeader("cache-control", "no-store");
}

function isCircuitOpen(): boolean {
  if (!circuitState.isOpen) return false;
  const elapsed = Date.now() - circuitState.lastFailureTime;
  if (elapsed > CIRCUIT_RESET_MS) {
    circuitState.isOpen = false;
    circuitState.failures = 0;
    circuitState.halfOpenAttempted = false;
    return false;
  }
  if (elapsed > CIRCUIT_HALF_OPEN_MS && !circuitState.halfOpenAttempted) {
    circuitState.halfOpenAttempted = true;
    return false;
  }
  return true;
}

function recordProxyFailure(): void {
  circuitState.failures += 1;
  circuitState.lastFailureTime = Date.now();
  metrics.proxyErrors += 1;
  if (circuitState.failures >= CIRCUIT_THRESHOLD && !circuitState.isOpen) {
    circuitState.isOpen = true;
    metrics.circuitBreakerTrips += 1;
    logger.error(
      {
        failures: circuitState.failures,
        threshold: CIRCUIT_THRESHOLD,
        resetTimeMs: CIRCUIT_RESET_MS,
        backendUrl: CONFIG.backendUrl.toString(),
        timestamp: new Date().toISOString(),
      },
      "🚨 CIRCUIT BREAKER TRIPPED — Backend proxy circuit opened",
    );
  }
}

function recordProxySuccess(): void {
  circuitState.failures = 0;
  circuitState.isOpen = false;
  circuitState.halfOpenAttempted = false;
}

function recordHealthCheckFailure(): void {
  const now = Date.now();
  if (
    !metrics.firstHealthCheckFailure ||
    now - metrics.firstHealthCheckFailure > HEALTH_CHECK_FAILURE_WINDOW_MS
  ) {
    metrics.firstHealthCheckFailure = now;
    metrics.healthCheckFailures = 1;
  } else {
    metrics.healthCheckFailures += 1;
  }
  metrics.lastHealthCheckFailure = now;
  const timeSinceFirstFailure = now - metrics.firstHealthCheckFailure;
  if (
    metrics.healthCheckFailures >= HEALTH_CHECK_FAILURE_THRESHOLD &&
    timeSinceFirstFailure <= HEALTH_CHECK_FAILURE_WINDOW_MS
  ) {
    logger.error(
      {
        healthCheckFailures: metrics.healthCheckFailures,
        threshold: HEALTH_CHECK_FAILURE_THRESHOLD,
        windowMs: HEALTH_CHECK_FAILURE_WINDOW_MS,
        backendUrl: CONFIG.backendUrl.toString(),
        timestamp: new Date().toISOString(),
      },
      "🚨 HEALTH CHECK FAILURE THRESHOLD EXCEEDED — Backend consistently unreachable",
    );
  }
}

function recordHealthCheckSuccess(): void {
  if (metrics.healthCheckFailures > 0) {
    logger.info(
      { previousFailures: metrics.healthCheckFailures, timestamp: new Date().toISOString() },
      "Health check recovered — backend reachable again",
    );
  }
  metrics.healthCheckFailures = 0;
  metrics.firstHealthCheckFailure = 0;
  metrics.lastHealthCheckFailure = 0;
}

const billingLedger = new MonthlyQuotaLedger();

function enforceTenantBilling(req: Request, res: Response, next: NextFunction): void {
  if (!CONFIG.billingEnforcementEnabled || !req.path.startsWith("/v1/")) {
    next();
    return;
  }
  const tenantHeader = Array.isArray(req.headers["x-hyba-tenant-id"])
    ? req.headers["x-hyba-tenant-id"][0]
    : req.headers["x-hyba-tenant-id"];
  const unitHeader = Array.isArray(req.headers["x-hyba-billing-units"])
    ? req.headers["x-hyba-billing-units"][0]
    : req.headers["x-hyba-billing-units"];
  const decision = billingLedger.evaluateAndRecord({
    tenantId: sanitizeTenantId(tenantHeader),
    requestedUnits: parseBillingUnits(unitHeader),
    plans: loadBillingPlans(),
    tenantConfigs: loadTenantBillingConfig(),
  });
  res.setHeader("x-hyba-billing-tenant", decision.tenantId);
  res.setHeader("x-hyba-billing-plan", decision.plan.id);
  res.setHeader("x-hyba-billing-period", decision.period);
  res.setHeader("x-hyba-billing-units", String(decision.requestedUnits));
  res.setHeader("x-hyba-quota-remaining", String(decision.remainingUnits));
  if (!decision.allowed) {
    metrics.billingRejectedTotal += 1;
    noStore(res);
    res.status(decision.reason === "invalid_units" ? 400 : 402).json({
      error: decision.reason,
      message:
        decision.reason === "invalid_units"
          ? "x-hyba-billing-units must be an integer from 1 to 1000000"
          : "Monthly tenant quota exceeded",
      tenantId: decision.tenantId,
      planId: decision.plan.id,
      monthlyQuotaUnits: decision.plan.monthlyQuotaUnits,
      usedUnits: decision.usedUnits,
      requestedUnits: decision.requestedUnits,
      remainingUnits: decision.remainingUnits,
      period: decision.period,
    });
    return;
  }
  metrics.billingUnitsTotal += decision.requestedUnits;
  next();
}

async function autoConnectViaBTC(): Promise<void> {
  if (!CONFIG.enableMiningAutoConnect) {
    logger.info("Mining auto-connect disabled — explicit MIDAS/operator connect required");
    return;
  }
  const poolId = process.env.HYBA_POOL_VIABTC_USERNAME ? "viabtc" : null;
  if (!poolId) {
    logger.info("No mining pool configured — skipping auto-connect");
    return;
  }
  try {
    const worker = process.env.HYBA_POOL_VIABTC_USERNAME || "PYTHIA.001";
    const password = process.env.HYBA_POOL_VIABTC_PASSWORD;
    if (!password) {
      logger.warn("ViaBTC auto-connect skipped because HYBA_POOL_VIABTC_PASSWORD is not set");
      return;
    }
    const capacity = Number(process.env.HYBA_QUANTUM_CAPACITY_EHS) || 1.0;
    const url = new URL("/api/mining/connect", CONFIG.backendUrl);
    const token = createInternalMiningJwt();
    if (!token) {
      logger.warn("Auto-connect skipped: JWT_SECRET not set, cannot mint internal access token");
      return;
    }
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ pool_id: poolId, worker, password, capacity_ehs: capacity }),
    });
    if (response.ok) {
      const result = (await response.json()) as { pool?: string };
      logger.info(
        { pool: result.pool, worker, capacity_ehs: capacity },
        "✅ Auto-connected to mining pool",
      );
    } else {
      logger.warn({ status: response.status }, "Auto-connect to mining pool failed");
    }
  } catch (error: unknown) {
    logger.warn(
      { err: error instanceof Error ? error.message : String(error) },
      "Auto-connect to mining pool threw",
    );
  }
}

async function isBackendReachable(): Promise<boolean> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 1500);
  try {
    const response = await fetch(new URL("/api/health/readiness", CONFIG.backendUrl), {
      signal: controller.signal,
    });
    return response.ok;
  } catch {
    return false;
  } finally {
    clearTimeout(timeout);
  }
}

let backendProcess: ChildProcessWithoutNullStreams | null = null;

function spawnBackend(): void {
  if (!CONFIG.shouldSpawnBackend) {
    logger.info({ backendUrl: CONFIG.backendUrl.toString() }, "Backend auto-spawn disabled");
    return;
  }
  const backendPort = getBackendPort();
  const backendHost = CONFIG.backendUrl.hostname;
  if (!["127.0.0.1", "localhost"].includes(backendHost)) {
    logger.warn(
      { backendUrl: CONFIG.backendUrl.toString() },
      "Backend auto-spawn skipped for non-local backend URL",
    );
    return;
  }
  const python = getPythonCommand();
  const pythonPath = path.join(process.cwd(), "python_backend");
  backendProcess = spawn(
    python,
    [
      "-m",
      "uvicorn",
      "hyba_genesis_api.main:app",
      "--host",
      backendHost,
      "--port",
      backendPort,
      "--log-level",
      process.env.LOG_LEVEL === "debug" ? "debug" : "warning",
    ],
    {
      cwd: process.cwd(),
      env: {
        ...process.env,
        PYTHONPATH: process.env.PYTHONPATH
          ? `${pythonPath}${path.delimiter}${process.env.PYTHONPATH}`
          : pythonPath,
      },
      stdio: "pipe",
    },
  );
  const isDebugLogging = process.env.LOG_LEVEL === "debug";
  backendProcess.stdout?.on("data", (data: Buffer) => {
    if (isDebugLogging) {
      logger.debug({ backend: data.toString().trim() }, "FastAPI stdout");
    }
  });
  backendProcess.stderr?.on("data", (data: Buffer) => {
    if (isDebugLogging) {
      logger.debug({ backend: data.toString().trim() }, "FastAPI stderr");
    } else {
      const line = data.toString().trim();
      if (
        line &&
        (line.includes("ERROR") || line.includes("WARNING") || line.includes("CRITICAL"))
      ) {
        logger.warn({ backend: line }, "FastAPI stderr");
      }
    }
  });
  backendProcess.on("exit", (code: number | null) => {
    logger.warn({ code }, "FastAPI backend exited");
    backendProcess = null;
  });
}

async function waitForBackend(maxAttempts = 30): Promise<boolean> {
  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    if (await isBackendReachable()) return true;
    await new Promise((resolve) => setTimeout(resolve, Math.min(250 * attempt, 2000)));
  }
  return false;
}

async function proxyToBackend(req: Request, res: Response): Promise<void> {
  if (isCircuitOpen()) {
    noStore(res);
    res.status(503).json({
      error: "circuit_breaker_open",
      message: "Backend circuit breaker is open — too many recent failures",
      retryAfterMs: CIRCUIT_RESET_MS,
    });
    return;
  }
  const requestId = (req.headers["x-request-id"] as string) || generateRequestId();
  const target = new URL(req.originalUrl, CONFIG.backendUrl);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), CONFIG.proxyTimeoutMs);
  let bodyBuffer: Buffer | undefined;
  if (!["GET", "HEAD"].includes(req.method)) {
    const chunks: Buffer[] = [];
    for await (const chunk of req) chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
    bodyBuffer = Buffer.concat(chunks);
  }
  const startTime = Date.now();
  try {
    const headers = new Headers();
    for (const [key, value] of Object.entries(req.headers)) {
      if (value === undefined) continue;
      if (["host", "content-length", "connection"].includes(key.toLowerCase())) continue;
      headers.set(key, Array.isArray(value) ? value.join(",") : String(value));
    }
    headers.set("x-request-id", requestId);
    const response = await fetch(target, {
      method: req.method.toUpperCase(),
      headers,
      body: bodyBuffer ? new Uint8Array(bodyBuffer) : undefined,
      signal: controller.signal,
    });
    const latencyMs = Date.now() - startTime;
    metrics.backendLatencyMs = latencyMs;
    if (latencyMs > LATENCY_CRITICAL_THRESHOLD_MS) {
      metrics.highLatencyCount += 1;
      metrics.lastHighLatencyTime = Date.now();
      logger.error({ latencyMs, path: req.originalUrl, requestId }, "🚨 CRITICAL BACKEND LATENCY");
    } else if (latencyMs > LATENCY_WARNING_THRESHOLD_MS) {
      logger.warn(
        { latencyMs, path: req.originalUrl, requestId },
        "⚠️  High backend latency detected",
      );
    }
    recordProxySuccess();
    res.status(response.status);
    response.headers.forEach((value, key) => {
      if (!["content-encoding", "content-length", "transfer-encoding"].includes(key.toLowerCase()))
        res.setHeader(key, value);
    });
    res.setHeader("x-request-id", requestId);
    res.send(Buffer.from(await response.arrayBuffer()));
  } catch (error: unknown) {
    recordProxyFailure();
    logger.error(
      {
        err: error instanceof Error ? error.message : "Unknown proxy error",
        path: req.originalUrl,
        requestId,
      },
      "Backend proxy request failed",
    );
    noStore(res);
    res.status(503).json({
      error: "backend_unavailable",
      message: "HYBA backend is not reachable",
      path: req.originalUrl,
      requestId,
    });
  } finally {
    clearTimeout(timeout);
  }
}

export function registerSecuritySwarmRoutes(
  app: express.Application,
  swarm = securitySwarms,
): void {
  app.get("/api/security/status", async (req: Request, res: Response) => {
    const observerPressure = Number(req.query.observer_pressure || 0);
    const sample = swarm.monitor_integrity(
      Number.isFinite(observerPressure) ? observerPressure : 0,
    );
    const status = swarm.get_swarm_status();
    noStore(res);
    res.json({
      status: status.integrity_locked ? "protected" : "responding",
      threat_level: sample.anomaly_detected ? "elevated" : "nominal",
      defense_systems: {
        stabilizer_monitor: {
          syndrome_weight: sample.syndrome_weight,
          trap_disturbances: sample.trap_disturbances,
          confidence: sample.confidence,
          anomaly_detected: sample.anomaly_detected,
          cause: sample.cause,
          operating_mode: sample.operating_mode,
          sampled_ancillas: sample.sampled_ancillas,
          check_frequency: sample.check_frequency,
          confidence_threshold: status.confidence_threshold,
          syndrome_width: status.syndrome_width,
          syndrome_check_stride: status.syndrome_check_stride,
          syndrome_rotation_index: status.syndrome_rotation_index,
          pool_permutation_checksum: status.pool_permutation_checksum,
          sanitized: status.sanitized,
          metacognitive: {
            current_state: status.operating_mode,
            predicted_state: status.anomaly_detected ? "integrity_response_active" : "nominal",
            confidence: status.last_confidence,
            self_awareness: status.last_confidence,
          },
        },
        preallocated_ancilla_trap_pool: {
          agents_total: status.agents_total,
          agents_active: status.agents_active,
          logical_agents: status.logical_agents,
          reserved_ancillas: status.reserved_ancillas,
          active_ancillas: status.active_ancillas,
          max_ancilla_pool: status.max_ancilla_pool,
          reserved_traps: status.reserved_traps,
          active_traps: status.active_traps,
          disturbed_traps: status.disturbed_traps,
          retired_traps: status.retired_traps,
        },
      },
      recent_threats: sample.anomaly_detected
        ? [
            {
              type: sample.cause,
              syndrome_weight: sample.syndrome_weight,
              trap_disturbances: sample.trap_disturbances,
              detected_at: new Date().toISOString(),
            },
          ]
        : [],
    });
  });
  app.post(
    "/api/security/swarm/respond",
    requireInternalAccess,
    async (req: Request, res: Response) => {
      const observerPressure = Number(req.query.observer_pressure || 1);
      const response = swarm.trigger_response(
        Number.isFinite(observerPressure) ? observerPressure : 1,
      );
      noStore(res);
      res.status(response.status === "integrity_response_active" ? 202 : 200).json(response);
    },
  );
}

function installSecuritySwarmHeartbeat(): ReturnType<typeof setInterval> {
  const heartbeat = setInterval(
    () => securitySwarms.monitor_integrity(0),
    CONFIG.swarmHeartbeatIntervalMs,
  );
  const maybeUnref = heartbeat as unknown as { unref?: () => void };
  if (typeof maybeUnref.unref === "function") maybeUnref.unref();
  return heartbeat;
}

async function startServer(): Promise<void> {
  if (CONFIG.isProduction) {
    const jwtValidation = validateProductionJwtSecret(CONFIG.jwtSecret);
    if (!jwtValidation.ok) {
      logger.fatal(
        { reason: (jwtValidation as { ok: false; reason: string }).reason },
        "Invalid production JWT_SECRET",
      );
      process.exit(1);
    }
  }
  installSecuritySwarmHeartbeat();
  const backendReachable = await isBackendReachable();
  if (!backendReachable) {
    spawnBackend();
    const ready = await waitForBackend();
    if (!ready) {
      if (CONFIG.isProduction) {
        logger.fatal(
          { backendUrl: CONFIG.backendUrl.toString() },
          "Backend readiness is required in production",
        );
        process.exit(1);
      }
      logger.warn(
        { backendUrl: CONFIG.backendUrl.toString() },
        "Backend not ready — starting in DEGRADED mode",
      );
    }
  }

  const app = express();
  const cspDirectives = {
    "default-src": ["'self'"],
    "script-src": ["'self'"],
    // unsafe-inline removed for XSS hardening; use hashed/nonced styles
    "style-src": ["'self'"],
    "img-src": ["'self'", "data:", "https:"],
    "connect-src": CONFIG.cspConnectSrc,
    "object-src": ["'none'"],
    "frame-ancestors": ["'none'"],
    "base-uri": ["'self'"],
    "form-action": ["'self'"],
  };
  app.use(
    helmet({
      contentSecurityPolicy: { useDefaults: true, directives: cspDirectives },
      crossOriginEmbedderPolicy: false,
    }),
  );
  app.use(compression());
  app.use(
    pinoHttp({
      logger,
      genReqId: () => generateRequestId(),
      autoLogging: {
        ignore: (req: Request) => req.url === "/bridge/health" || req.url === "/health",
      },
    }),
  );
  app.use((req: Request, res: Response, next: NextFunction) => {
    const requestId = (req.headers["x-request-id"] as string) || generateRequestId();
    req.headers["x-request-id"] = requestId;
    res.setHeader("x-request-id", requestId);
    next();
  });
  app.use((req: Request, _res: Response, next: NextFunction) => {
    metrics.requestsTotal += 1;
    const pathKey = req.method + " " + req.path;
    metrics.requestsByPath.set(pathKey, (metrics.requestsByPath.get(pathKey) || 0) + 1);
    next();
  });
  app.use(
    rateLimit({
      windowMs: CONFIG.rateLimitWindowMs,
      max: CONFIG.rateLimitMax,
      message: {
        error: "too_many_requests",
        message: "Too many requests, please try again later.",
      },
      standardHeaders: true,
      legacyHeaders: false,
    }),
  );

  app.get("/", async (_req: Request, res: Response, next: NextFunction) => {
    if (!CONFIG.isProduction) return next();
    noStore(res);
    res.json({
      status: "online",
      service: "HYBA Secure Bridge",
      version: "2.1.0",
      backendReachable: await isBackendReachable(),
      timestamp: new Date().toISOString(),
    });
  });
  app.get("/bridge/health", async (_req: Request, res: Response) => {
    const reachable = await isBackendReachable();
    if (!reachable) recordHealthCheckFailure();
    else recordHealthCheckSuccess();
    noStore(res);
    res.status(reachable ? 200 : 503).json({
      status: reachable ? "ok" : "degraded",
      service: "HYBA Secure Bridge",
      version: "2.1.0",
      backendReachable: reachable,
      timestamp: new Date().toISOString(),
    });
  });
  app.get(
    "/bridge/internal/health",
    requireInternalAccess,
    async (_req: Request, res: Response) => {
      const reachable = await isBackendReachable();
      const uptimeSeconds = Math.floor((Date.now() - metrics.startTime) / 1000);
      noStore(res);
      res.status(reachable ? 200 : 503).json({
        status: reachable ? "ok" : "degraded",
        service: "HYBA Secure Bridge",
        version: "2.1.0",
        backend: CONFIG.backendUrl.toString(),
        backendReachable: reachable,
        circuitBreakerOpen: circuitState.isOpen,
        circuitFailures: circuitState.failures,
        uptimeSeconds,
        metrics: {
          requestsTotal: metrics.requestsTotal,
          proxyErrors: metrics.proxyErrors,
          circuitBreakerTrips: metrics.circuitBreakerTrips,
          billingUnitsTotal: metrics.billingUnitsTotal,
          billingRejectedTotal: metrics.billingRejectedTotal,
          topPaths: Array.from(metrics.requestsByPath.entries())
            .sort((a, b) => b[1] - a[1])
            .slice(0, 10),
        },
        timestamp: new Date().toISOString(),
      });
    },
  );

  registerSecuritySwarmRoutes(app);
  app.use("/api/intelligence", express.json({ limit: "1mb" }));
  app.use("/api/intelligence", express.urlencoded({ extended: true, limit: "1mb" }));

  const intelligenceService = IntelligenceService.getInstance(2048);
  app.get(
    "/api/intelligence/telemetry",
    requireInternalAccess,
    async (_req: Request, res: Response) => {
      noStore(res);
      res.json(intelligenceService.getTelemetry());
    },
  );
  app.get(
    "/api/intelligence/status",
    requireInternalAccess,
    async (_req: Request, res: Response) => {
      noStore(res);
      res.json({
        active: intelligenceService.isActive(),
        phi: intelligenceService.getPhi(),
        current_goal: intelligenceService.getCurrentGoal(),
        uptime_ms: Date.now() - metrics.startTime,
      });
    },
  );
  app.get(
    "/api/intelligence/hebbian-stats",
    requireInternalAccess,
    async (_req: Request, res: Response) => {
      noStore(res);
      res.json(intelligenceService.getHebbianStats());
    },
  );
  app.post(
    "/api/intelligence/simulate-disturbance",
    requireInternalAccess,
    async (req: Request, res: Response) => {
      const { syndrome } = req.body as { syndrome?: number };
      if (typeof syndrome !== "number") {
        res.status(400).json({ error: "invalid_request", message: "syndrome must be a number" });
        return;
      }
      intelligenceService.simulateDisturbance(syndrome);
      noStore(res);
      res.json({
        status: "disturbance_applied",
        telemetry_source: "operator_authorised_internal_route",
      });
    },
  );
  app.post(
    "/api/intelligence/reset",
    requireInternalAccess,
    async (_req: Request, res: Response) => {
      intelligenceService.reset();
      noStore(res);
      res.json({ status: "reset_complete" });
    },
  );
  app.post(
    "/api/intelligence/start",
    requireInternalAccess,
    async (_req: Request, res: Response) => {
      intelligenceService.start();
      noStore(res);
      res.json({ status: "intelligence_started" });
    },
  );
  app.post(
    "/api/intelligence/stop",
    requireInternalAccess,
    async (_req: Request, res: Response) => {
      intelligenceService.stop();
      noStore(res);
      res.json({ status: "intelligence_stopped" });
    },
  );

  app.get("/bridge/metrics", requireInternalAccess, async (_req: Request, res: Response) => {
    const reachable = await isBackendReachable();
    const lines: string[] = [
      "# HELP hyba_bridge_requests_total Total requests processed",
      "# TYPE hyba_bridge_requests_total counter",
      `hyba_bridge_requests_total ${metrics.requestsTotal}`,
      "# HELP hyba_bridge_proxy_errors Total proxy errors",
      "# TYPE hyba_bridge_proxy_errors counter",
      `hyba_bridge_proxy_errors ${metrics.proxyErrors}`,
      "# HELP hyba_bridge_circuit_breaker_open Circuit breaker is open",
      "# TYPE hyba_bridge_circuit_breaker_open gauge",
      `hyba_bridge_circuit_breaker_open ${circuitState.isOpen ? 1 : 0}`,
      "# HELP hyba_bridge_circuit_breaker_trips Total circuit breaker trips",
      "# TYPE hyba_bridge_circuit_breaker_trips counter",
      `hyba_bridge_circuit_breaker_trips ${metrics.circuitBreakerTrips}`,
      "# HELP hyba_bridge_backend_reachable Backend is reachable",
      "# TYPE hyba_bridge_backend_reachable gauge",
      `hyba_bridge_backend_reachable ${reachable ? 1 : 0}`,
      "# HELP hyba_bridge_health_check_failures Total health check failures",
      "# TYPE hyba_bridge_health_check_failures counter",
      `hyba_bridge_health_check_failures ${metrics.healthCheckFailures}`,
      "# HELP hyba_bridge_backend_latency_ms Current backend latency in milliseconds",
      "# TYPE hyba_bridge_backend_latency_ms gauge",
      `hyba_bridge_backend_latency_ms ${metrics.backendLatencyMs}`,
      "# HELP hyba_bridge_high_latency_count Total high latency events",
      "# TYPE hyba_bridge_high_latency_count counter",
      `hyba_bridge_high_latency_count ${metrics.highLatencyCount}`,
      "# HELP hyba_billing_units_total Total accepted billable units",
      "# TYPE hyba_billing_units_total counter",
      `hyba_billing_units_total ${metrics.billingUnitsTotal}`,
      "# HELP hyba_billing_rejected_total Total requests rejected by billing quota enforcement",
      "# TYPE hyba_billing_rejected_total counter",
      `hyba_billing_rejected_total ${metrics.billingRejectedTotal}`,
      "# HELP hyba_bridge_uptime_seconds Uptime in seconds",
      "# TYPE hyba_bridge_uptime_seconds counter",
      `hyba_bridge_uptime_seconds ${Math.floor((Date.now() - metrics.startTime) / 1000)}`,
    ];
    noStore(res);
    res.setHeader("content-type", "text/plain; charset=utf-8");
    res.send(lines.join("\n"));
  });

  // Enforce body size limit for all proxied routes before streaming begins
  app.use("/api", enforceTenantBilling);

  app.use(["/api", "/health"], (req: Request, res: Response, next: NextFunction) => {
    const contentLength = parseInt(req.headers["content-length"] || "0", 10);
    if (contentLength > CONFIG.proxyBodySizeLimit) {
      res
        .status(413)
        .json({ error: "payload_too_large", message: "Request body exceeds size limit" });
      return;
    }
    next();
  });
  app.use("/api", (req: Request, res: Response) => {
    void proxyToBackend(req, res);
  });
  app.use("/health", (req: Request, res: Response) => {
    void proxyToBackend(req, res);
  });

  if (!CONFIG.isProduction) {
    const projectRoot = path.resolve(process.cwd());
    const viteInlineConfig: InlineConfig = {
      configFile: false,
      root: projectRoot,
      cacheDir: getViteCacheDir(projectRoot),
      plugins: [react(), tailwindcss()],
      resolve: { alias: { "@": projectRoot } },
      server: {
        middlewareMode: true,
        hmr: process.env.DISABLE_HMR !== "true",
        watch: process.env.DISABLE_HMR === "true" ? null : {},
        fs: { strict: false, allow: [projectRoot] },
      },
      appType: "spa",
      optimizeDeps: {
        include: [
          "react",
          "react-dom",
          "react-dom/client",
          "lucide-react",
          "recharts",
          "d3",
          "motion",
          "firebase/app",
          "firebase/firestore",
          "firebase/auth",
        ],
      },
    };
    const vite = await createViteServer(viteInlineConfig);
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (_req: Request, res: Response) => res.sendFile(path.join(distPath, "index.html")));
  }

  const server: Server = createServer(app);
  installShutdownHandlers(server);
  server.on("error", (error: NodeJS.ErrnoException) => {
    if (error.code === "EADDRINUSE") {
      logger.error({ port: CONFIG.port }, `Port ${CONFIG.port} is already in use`);
      process.exit(1);
    }
    logger.error({ err: error }, "HTTP server failed");
    process.exit(1);
  });
  server.listen(CONFIG.port, CONFIG.host, () => {
    void autoConnectViaBTC();
    logger.info(
      { port: CONFIG.port, host: CONFIG.host, backendUrl: CONFIG.backendUrl.toString() },
      "HYBA Secure Bridge listening",
    );
  });
}

function installShutdownHandlers(server: Server): void {
  const shutdown = (signal: string) => {
    logger.info({ signal }, "Graceful shutdown initiated — draining connections");
    server.close(() => logger.info("HTTP server closed — all connections drained"));
    if (backendProcess && !backendProcess.killed) {
      backendProcess.kill("SIGTERM");
      logger.info("Backend process terminated");
    }
    setTimeout(() => {
      logger.info("Shutdown complete — exiting");
      process.exit(0);
    }, 5000).unref();
  };
  process.once("SIGINT", () => shutdown("SIGINT"));
  process.once("SIGTERM", () => shutdown("SIGTERM"));
  process.once("SIGHUP", () => shutdown("SIGHUP"));
}

if (process.env.NODE_ENV !== "test") {
  startServer().catch((error: unknown) => {
    logger.fatal(
      { err: error instanceof Error ? error.message : String(error) },
      "Critical server failure on startup",
    );
    process.exit(1);
  });
}
