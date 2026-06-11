/**
 * HYBA Secure Bridge — Production-Grade Express Gateway
 *
 * Architecture:
 *   Browser ──► Express (Helmet + CORS + Rate-Limit) ──► FastAPI Backend
 *                                        │
 *                                        └── Static SPA (built or Vite dev)
 *
 * Design principles (Stripe/McKinsey grade):
 *   - Circuit breaker for backend proxy calls
 *   - Structured request ID propagation
 *   - Rate limiting with graduated backoff
 *   - Health endpoint with Prometheus-style metrics
 *   - Graceful shutdown with connection drain
 *   - Zero fabricated responses — degraded mode when backend is unavailable
 *
 * Environment variables (see .env.example):
 *   PORT                     : HTTP port (default 3000)
 *   HOST                     : bind address (default 0.0.0.0)
 *   PULVINI_BACKEND_URL      : upstream FastAPI URL (default http://127.0.0.1:3001)
 *   JWT_SECRET               : required in production
 *   NODE_ENV                 : "production" | "development"
 *   HYBA_SPAWN_BACKEND       : "false" to disable auto-spawn
 *   BACKEND_PROXY_TIMEOUT_MS : proxy timeout (default 30000)
 *   LOG_LEVEL               : pino log level (default "info")
 */

import compression from "compression";
import dotenv from "dotenv";
import express, { type NextFunction, type Request, type Response } from "express";
import helmet from "helmet";
import path from "node:path";
import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";
import { createServer, type Server } from "node:http";
import pino from "pino";
import pinoHttp from "pino-http";
import rateLimit from "express-rate-limit";
import { createServer as createViteServer, type InlineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// ── Global Backend URL for post-startup calls ────────────────────────────
let _backendUrl: URL | null = null;

dotenv.config();

// ── Structured Logger ─────────────────────────────────────────────────────

const logger = pino({
  name: "hyba-secure-bridge",
  level: process.env.LOG_LEVEL || "info",
  base: {
    service: "hyba-secure-bridge",
    env: process.env.NODE_ENV || "development",
  },
  formatters: {
    level(label) {
      return { level: label };
    },
  },
  timestamp: pino.stdTimeFunctions.isoTime,
});

// ── Configuration ─────────────────────────────────────────────────────────

const CONFIG = {
  isProduction: process.env.NODE_ENV === "production",
  host: process.env.HOST || "0.0.0.0",
  port: Number(process.env.PORT || 3000),
  backendUrl: normalizeBackendUrl(process.env.PULVINI_BACKEND_URL || "http://127.0.0.1:3001"),
  shouldSpawnBackend: process.env.NODE_ENV !== "production" && process.env.HYBA_SPAWN_BACKEND !== "false",
  proxyTimeoutMs: Number(process.env.BACKEND_PROXY_TIMEOUT_MS || 30000),
  rateLimitWindowMs: Number(process.env.RATE_LIMIT_WINDOW_MS || 60000),
  rateLimitMax: Number(process.env.RATE_LIMIT_MAX || 100),
  jwtSecret: process.env.JWT_SECRET || "",
} as const;

// ── Circuit Breaker ───────────────────────────────────────────────────────

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
    return false; // allow a single probe request
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
    logger.warn({ failures: circuitState.failures }, "Proxy circuit breaker OPEN — backend considered degraded");
  }
}

function recordProxySuccess(): void {
  circuitState.failures = 0;
  circuitState.isOpen = false;
  circuitState.halfOpenAttempted = false;
}

// ── Utilities ─────────────────────────────────────────────────────────────

function normalizeBackendUrl(value: string): URL {
  const parsed = new URL(value);
  if (!["http:", "https:"].includes(parsed.protocol)) {
    throw new Error(`PULVINI_BACKEND_URL must be http(s), received ${parsed.protocol}`);
  }
  return parsed;
}

function getPythonCommand(): string {
  return process.platform === "win32" ? "python" : "python3";
}

function generateRequestId(): string {
  const timestamp = Date.now().toString(36);
  const random = Math.random().toString(36).substring(2, 10);
  return `req_${timestamp}_${random}`;
}

// ── Auto-Connect to ViaBTC on Startup ────────────────────────────────────

async function autoConnectViaBTC(): Promise<void> {
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
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pool_id: poolId, worker, password, capacity_ehs: capacity }),
    });
    if (response.ok) {
      const result = await response.json();
      logger.info({ pool: result.pool, worker, capacity_ehs: capacity }, "✅ Auto-connected to mining pool");
    } else {
      logger.warn({ status: response.status }, "Auto-connect to mining pool failed");
    }
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    logger.warn({ err: message }, "Auto-connect to mining pool threw");
  }
}

// ── Backend Management ────────────────────────────────────────────────────

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

  const backendPort = CONFIG.backendUrl.port;
  const backendHost = CONFIG.backendUrl.hostname;

  if (!["127.0.0.1", "localhost"].includes(backendHost)) {
    logger.warn({ backendUrl: CONFIG.backendUrl.toString() }, "Backend auto-spawn skipped for non-local backend URL");
    return;
  }

  const python = getPythonCommand();
  const pythonPath = path.join(process.cwd(), "python_backend");

  logger.info({ backendHost, backendPort }, "Spawning HYBA FastAPI backend");
  backendProcess = spawn(
    python,
    [
      "-m", "uvicorn",
      "hyba_genesis_api.main:app",
      "--host", backendHost,
      "--port", backendPort,
      "--log-level", process.env.LOG_LEVEL === "debug" ? "debug" : "warning",
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

  backendProcess.stdout?.on("data", (data: Buffer) => logger.info({ backend: data.toString().trim() }, "FastAPI stdout"));
  backendProcess.stderr?.on("data", (data: Buffer) => logger.warn({ backend: data.toString().trim() }, "FastAPI stderr"));
  backendProcess.on("exit", (code: number | null) => {
    logger.warn({ code }, "FastAPI backend exited");
    backendProcess = null;
  });
}

async function waitForBackend(maxAttempts = 30): Promise<boolean> {
  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    if (await isBackendReachable()) return true;
    await new Promise(resolve => setTimeout(resolve, Math.min(250 * attempt, 2000)));
  }
  return false;
}

// ── Proxy Handler (with circuit breaker) ──────────────────────────────────

async function proxyToBackend(req: Request, res: Response): Promise<void> {
  if (isCircuitOpen()) {
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

  // Buffer the request body so we can use it with fetch
  let bodyBuffer: Buffer | undefined;
  if (!["GET", "HEAD"].includes(req.method)) {
    const chunks: Buffer[] = [];
    for await (const chunk of req) {
      chunks.push(chunk);
    }
    bodyBuffer = Buffer.concat(chunks);
  }

  try {
    const headers = new Headers();
    for (const [key, value] of Object.entries(req.headers)) {
      if (value === undefined) continue;
      if (["host", "content-length", "connection"].includes(key.toLowerCase())) continue;
      headers.set(key, Array.isArray(value) ? value.join(",") : value);
    }
    headers.set("x-request-id", requestId);

    const method = req.method.toUpperCase();
    const response = await fetch(target, {
      method,
      headers,
      body: bodyBuffer,
      signal: controller.signal,
    });

    recordProxySuccess();
    res.status(response.status);
    response.headers.forEach((value, key) => {
      if (!["content-encoding", "content-length", "transfer-encoding"].includes(key.toLowerCase())) {
        res.setHeader(key, value);
      }
    });
    res.setHeader("x-request-id", requestId);

    const responseBody = Buffer.from(await response.arrayBuffer());
    res.send(responseBody);
  } catch (error: unknown) {
    recordProxyFailure();
    const message = error instanceof Error ? error.message : "Unknown proxy error";
    logger.error({ err: message, path: req.originalUrl, requestId }, "Backend proxy request failed");
    res.status(503).json({
      error: "backend_unavailable",
      message: "HYBA backend is not reachable",
      backend: CONFIG.backendUrl.toString(),
      path: req.originalUrl,
      requestId,
    });
  } finally {
    clearTimeout(timeout);
  }
}

// ── Metrics ────────────────────────────────────────────────────────────────

const metrics = {
  requestsTotal: 0,
  requestsByPath: new Map<string, number>(),
  proxyErrors: 0,
  circuitBreakerTrips: 0,
  startTime: Date.now(),
};

// ── Application Server ────────────────────────────────────────────────────

async function startServer(): Promise<void> {
  // ── Production JWT validation ──
  if (CONFIG.isProduction && !CONFIG.jwtSecret) {
    logger.fatal("JWT_SECRET is required in production");
    process.exit(1);
  }

  // ── Backend connectivity ──
  const backendReachable = await isBackendReachable();
  if (!backendReachable) {
    spawnBackend();
    const ready = await waitForBackend();
    if (!ready) {
      if (CONFIG.isProduction) {
        logger.fatal({ backendUrl: CONFIG.backendUrl.toString() }, "Backend readiness is required in production");
        process.exit(1);
      }
      logger.warn({ backendUrl: CONFIG.backendUrl.toString() }, "Backend not ready — starting in DEGRADED mode");
    }
  }

  // ── Express app ──
  const app = express();

  // Security headers
  app.use(
    helmet({
      contentSecurityPolicy: false, // SPA manages its own CSP
      crossOriginEmbedderPolicy: false,
    }),
  );

  // Compression
  app.use(compression());

  // Structured HTTP logging
  const httpLogger = pinoHttp({
    logger,
    genReqId: () => generateRequestId(),
    autoLogging: {
      ignore: (req) => req.url === "/bridge/health" || req.url === "/health",
    },
  });
  app.use(httpLogger);

  // Request ID propagation
  app.use((req: Request, res: Response, next: NextFunction) => {
    const requestId = (req.headers["x-request-id"] as string) || generateRequestId();
    req.headers["x-request-id"] = requestId;
    res.setHeader("x-request-id", requestId);
    next();
  });

  // Metrics middleware
  app.use((req: Request, _res: Response, next: NextFunction) => {
    metrics.requestsTotal += 1;
    const pathKey = req.method + " " + req.path;
    metrics.requestsByPath.set(pathKey, (metrics.requestsByPath.get(pathKey) || 0) + 1);
    next();
  });

  // Rate limiting middleware
  const limiter = rateLimit({
    windowMs: CONFIG.rateLimitWindowMs,
    max: CONFIG.rateLimitMax,
    message: { error: "too_many_requests", message: "Too many requests, please try again later." },
    standardHeaders: true,
    legacyHeaders: false,
  });
  app.use(limiter);

  // ── Routes ──

  // Root health
  app.get("/", async (_req: Request, res: Response, next: NextFunction) => {
    if (!CONFIG.isProduction) return next();
    res.json({
      status: "online",
      service: "HYBA Secure Bridge",
      version: "2.0.1",
      backend: CONFIG.backendUrl.toString(),
      backendReachable: await isBackendReachable(),
      timestamp: new Date().toISOString(),
    });
  });

  // Bridge health with metrics
  app.get("/bridge/health", async (_req: Request, res: Response) => {
    const reachable = await isBackendReachable();
    const uptimeSeconds = Math.floor((Date.now() - metrics.startTime) / 1000);
    res.status(reachable ? 200 : 503).json({
      status: reachable ? "ok" : "degraded",
      service: "HYBA Secure Bridge",
      version: "2.0.1",
      backend: CONFIG.backendUrl.toString(),
      backendReachable: reachable,
      circuitBreakerOpen: circuitState.isOpen,
      circuitFailures: circuitState.failures,
      uptimeSeconds,
      metrics: {
        requestsTotal: metrics.requestsTotal,
        proxyErrors: metrics.proxyErrors,
        circuitBreakerTrips: metrics.circuitBreakerTrips,
        topPaths: Array.from(metrics.requestsByPath.entries())
          .sort((a, b) => b[1] - a[1])
          .slice(0, 10),
      },
      timestamp: new Date().toISOString(),
    });
  });

  // Metrics endpoint (Prometheus-compatible)
  app.get("/bridge/metrics", async (_req: Request, res: Response) => {
    const reachable = await isBackendReachable();
    const lines: string[] = [
      `# HELP hyba_bridge_requests_total Total requests processed`,
      `# TYPE hyba_bridge_requests_total counter`,
      `hyba_bridge_requests_total ${metrics.requestsTotal}`,
      `# HELP hyba_bridge_proxy_errors Total proxy errors`,
      `# TYPE hyba_bridge_proxy_errors counter`,
      `hyba_bridge_proxy_errors ${metrics.proxyErrors}`,
      `# HELP hyba_bridge_circuit_breaker_open Circuit breaker is open`,
      `# TYPE hyba_bridge_circuit_breaker_open gauge`,
      `hyba_bridge_circuit_breaker_open ${circuitState.isOpen ? 1 : 0}`,
      `# HELP hyba_bridge_backend_reachable Backend is reachable`,
      `# TYPE hyba_bridge_backend_reachable gauge`,
      `hyba_bridge_backend_reachable ${reachable ? 1 : 0}`,
      `# HELP hyba_bridge_uptime_seconds Uptime in seconds`,
      `# TYPE hyba_bridge_uptime_seconds counter`,
      `hyba_bridge_uptime_seconds ${Math.floor((Date.now() - metrics.startTime) / 1000)}`,
    ];
    res.setHeader("content-type", "text/plain; charset=utf-8");
    res.send(lines.join("\n"));
  });

  // API proxy routes (apply before body parsing)
  app.use("/api", (req: Request, res: Response) => {
    void proxyToBackend(req, res);
  });
  app.use("/health", (req: Request, res: Response) => {
    void proxyToBackend(req, res);
  });

  // Body parsing (apply only to non-proxy routes)
  app.use(express.json({ limit: "1mb" }));
  app.use(express.urlencoded({ extended: true, limit: "1mb" }));

  // ── Static / Vite middleware ──
  if (!CONFIG.isProduction) {
    logger.info("Mounting Vite dev middleware");
    // Use an inline config instead of a file path to avoid tsx resolver issues
    // on Windows + OneDrive paths (ERR_INVALID_URL_SCHEME).
    const projectRoot = path.resolve(process.cwd());
    const viteInlineConfig: InlineConfig = {
      configFile: false, // do NOT load from disk — we provide everything inline
      root: projectRoot,
      plugins: [react(), tailwindcss()],
      resolve: {
        alias: {
          "@": projectRoot,
        },
      },
      server: {
        middlewareMode: true,
        hmr: process.env.DISABLE_HMR !== "true",
        watch: process.env.DISABLE_HMR === "true" ? null : {},
        fs: {
          strict: false,
          allow: [projectRoot],
        },
      },
      appType: "spa",
      optimizeDeps: {
        // Pre-bundle key dependencies to avoid late ESM resolution issues
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
    app.get("*", (_req: Request, res: Response) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  // ── HTTP Server ──
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
    // Auto-connect to mining pool after server is listening
    void autoConnectViaBTC();

    logger.info(
      { port: CONFIG.port, host: CONFIG.host, backendUrl: CONFIG.backendUrl.toString() },
      "HYBA Secure Bridge listening",
    );
    console.log("");
    console.log("  ╔══════════════════════════════════════════════╗");
    console.log("  ║     HYBA Secure Bridge — Production Ready    ║");
    console.log("  ╠══════════════════════════════════════════════╣");
    console.log(`  ║  Server    : http://${CONFIG.host}:${CONFIG.port}           ║`);
    console.log(`  ║  Backend   : ${CONFIG.backendUrl.toString().padEnd(25)} ║`);
    console.log(`  ║  Mode      : ${CONFIG.isProduction ? "PRODUCTION" : "DEVELOPMENT".padEnd(20)} ║`);
    console.log(`  ║  Circuit   : ${CIRCUIT_THRESHOLD} failures / ${CIRCUIT_RESET_MS / 1000}s reset      ║`);
    console.log("  ╚══════════════════════════════════════════════╝");
    console.log("");
  });
}

// ── Graceful Shutdown ────────────────────────────────────────────────────

function installShutdownHandlers(server: Server): void {
  const shutdown = (signal: string) => {
    logger.info({ signal }, "Graceful shutdown initiated — draining connections");

    // Stop accepting new connections
    server.close(() => {
      logger.info("HTTP server closed — all connections drained");
    });

    // Kill backend process
    if (backendProcess && !backendProcess.killed) {
      backendProcess.kill("SIGTERM");
      logger.info("Backend process terminated");
    }

    // Force exit after drain timeout
    setTimeout(() => {
      logger.info("Shutdown complete — exiting");
      process.exit(0);
    }, 5000).unref();
  };

  process.once("SIGINT", () => shutdown("SIGINT"));
  process.once("SIGTERM", () => shutdown("SIGTERM"));
  process.once("SIGHUP", () => shutdown("SIGHUP"));
}

// ── Start ─────────────────────────────────────────────────────────────────

startServer().catch((error: unknown) => {
  const message = error instanceof Error ? error.message : String(error);
  logger.fatal({ err: message }, "Critical server failure on startup");
  process.exit(1);
});