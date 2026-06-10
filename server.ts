/**
 * HYBA Secure Bridge
 *
 * Single-listener Express gateway for the React app and the HYBA FastAPI backend.
 * The bridge deliberately proxies backend-owned APIs instead of fabricating mining,
 * valuation, consciousness, or telemetry responses in Node.
 */

import compression from "compression";
import dotenv from "dotenv";
import express from "express";
import helmet from "helmet";
import path from "node:path";
import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";
import { createServer, type Server } from "node:http";
import { pathToFileURL } from "node:url";
import pino from "pino";
import pinoHttp from "pino-http";
import { createServer as createViteServer } from "vite";

dotenv.config();

const logger = pino({
  name: "hyba-secure-bridge",
  level: process.env.LOG_LEVEL || "info",
  base: {
    service: "hyba-secure-bridge",
    env: process.env.NODE_ENV || "development",
  },
});

const isProduction = process.env.NODE_ENV === "production";
const host = process.env.HOST || "0.0.0.0";
const port = Number(process.env.PORT || 3000);
const backendUrl = normalizeBackendUrl(process.env.PULVINI_BACKEND_URL || "http://127.0.0.1:3001");
const shouldSpawnBackend = !isProduction && process.env.HYBA_SPAWN_BACKEND !== "false";
let backendProcess: ChildProcessWithoutNullStreams | null = null;

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

async function isBackendReachable(): Promise<boolean> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 1500);
  try {
    const response = await fetch(new URL("/api/health/readiness", backendUrl), { signal: controller.signal });
    return response.ok;
  } catch {
    return false;
  } finally {
    clearTimeout(timeout);
  }
}

function spawnBackend(): void {
  if (!shouldSpawnBackend) {
    logger.info({ backendUrl: backendUrl.toString() }, "Backend auto-spawn disabled; using configured backend URL");
    return;
  }

  const backendPort = backendUrl.port || (backendUrl.protocol === "https:" ? "443" : "80");
  const backendHost = backendUrl.hostname;
  if (!["127.0.0.1", "localhost"].includes(backendHost)) {
    logger.warn({ backendUrl: backendUrl.toString() }, "Backend auto-spawn skipped for non-local backend URL");
    return;
  }

  const python = getPythonCommand();
  const pythonPath = path.join(process.cwd(), "python_backend");
  logger.info({ backendHost, backendPort }, "Starting local HYBA FastAPI backend");

  backendProcess = spawn(
    python,
    ["-m", "uvicorn", "hyba_genesis_api.main:app", "--host", backendHost, "--port", backendPort],
    {
      cwd: process.cwd(),
      env: {
        ...process.env,
        PYTHONPATH: process.env.PYTHONPATH ? `${pythonPath}${path.delimiter}${process.env.PYTHONPATH}` : pythonPath,
      },
      stdio: "pipe",
    },
  );

  backendProcess.stdout.on("data", data => logger.info({ backend: data.toString().trim() }, "FastAPI stdout"));
  backendProcess.stderr.on("data", data => logger.warn({ backend: data.toString().trim() }, "FastAPI stderr"));
  backendProcess.on("exit", code => {
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

async function proxyToBackend(req: express.Request, res: express.Response): Promise<void> {
  const target = new URL(req.originalUrl, backendUrl);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), Number(process.env.BACKEND_PROXY_TIMEOUT_MS || 30000));

  try {
    const headers = new Headers();
    for (const [key, value] of Object.entries(req.headers)) {
      if (value === undefined) continue;
      if (["host", "content-length", "connection"].includes(key.toLowerCase())) continue;
      headers.set(key, Array.isArray(value) ? value.join(",") : value);
    }

    const method = req.method.toUpperCase();
    const hasBody = !["GET", "HEAD"].includes(method);
    const response = await fetch(target, {
      method,
      headers,
      body: hasBody ? JSON.stringify(req.body ?? {}) : undefined,
      signal: controller.signal,
    });

    res.status(response.status);
    response.headers.forEach((value, key) => {
      if (!["content-encoding", "content-length", "transfer-encoding"].includes(key.toLowerCase())) {
        res.setHeader(key, value);
      }
    });

    const body = Buffer.from(await response.arrayBuffer());
    res.send(body);
  } catch (error: any) {
    logger.error({ err: error?.message, path: req.originalUrl }, "Backend proxy request failed");
    res.status(503).json({
      error: "backend_unavailable",
      message: "HYBA backend is not reachable",
      backend: backendUrl.toString(),
      path: req.originalUrl,
    });
  } finally {
    clearTimeout(timeout);
  }
}

async function startServer(): Promise<void> {
  if (isProduction && !process.env.JWT_SECRET) {
    logger.error("FATAL: JWT_SECRET is required in production");
    process.exit(1);
  }

  if (!(await isBackendReachable())) {
    spawnBackend();
    const ready = await waitForBackend();
    if (!ready) {
      logger.warn({ backendUrl: backendUrl.toString() }, "Backend is not ready; bridge will start in DEGRADED mode");
    }
  }

  const app = express();
  const httpLogger = pinoHttp({ logger });
  app.use(helmet({ contentSecurityPolicy: false }));
  app.use(compression());
  app.use(express.json({ limit: "1mb" }));
  app.use(httpLogger);

  app.get("/", async (_req, res, next) => {
    if (!isProduction) return next();
    res.json({
      status: "online",
      service: "HYBA Secure Bridge",
      backend: backendUrl.toString(),
      backendReachable: await isBackendReachable(),
      timestamp: new Date().toISOString(),
    });
  });

  app.get("/bridge/health", async (_req, res) => {
    res.json({
      status: "ok",
      service: "HYBA Secure Bridge",
      backend: backendUrl.toString(),
      backendReachable: await isBackendReachable(),
      timestamp: new Date().toISOString(),
    });
  });

  app.use("/api", (req, res) => {
    void proxyToBackend(req, res);
  });
  app.use("/health", (req, res) => {
    void proxyToBackend(req, res);
  });

  if (!isProduction) {
    logger.info("Mounting Vite middleware in local development mode");
    const vite = await createViteServer({
      configFile: pathToFileURL(path.join(process.cwd(), "vite.config.ts")).href,
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (_req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  const server = createServer(app);
  installShutdownHandlers(server);
  server.on("error", (error: NodeJS.ErrnoException) => {
    if (error.code === "EADDRINUSE") {
      logger.error(
        { port },
        `Port ${port} is already in use. Stop the existing process or run with PORT=${port + 1}.`,
      );
      process.exit(1);
    }
    logger.error({ err: error }, "HTTP server failed");
    process.exit(1);
  });

  server.listen(port, host, () => {
    logger.info({ port, host, backendUrl: backendUrl.toString() }, "HYBA Secure Bridge listening");
    console.log("====================================================");
    console.log(" HYBA Secure Bridge Booted Successfully");
    console.log(` Hosting Server url : http://localhost:${port}`);
    console.log(` Python Backend    : ${backendUrl.toString()}`);
    console.log("====================================================");
  });
}

function installShutdownHandlers(server: Server): void {
  const shutdown = (signal: string) => {
    logger.info({ signal }, "Graceful shutdown initiated");
    server.close(() => logger.info("HTTP bridge closed"));
    if (backendProcess && !backendProcess.killed) backendProcess.kill("SIGTERM");
    setTimeout(() => process.exit(0), 1000).unref();
  };
  process.once("SIGINT", () => shutdown("SIGINT"));
  process.once("SIGTERM", () => shutdown("SIGTERM"));
}

startServer().catch(error => {
  logger.error({ err: error }, "Critical server failure on startup");
  process.exit(1);
});
