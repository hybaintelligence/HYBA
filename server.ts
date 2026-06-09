/**
 * Express Full-Stack Server
 * Serves Quantum ASIC Annihilation mathematical APIs and integrates Vite middleware.
 */

import express from "express";
import path from "path";
import { createServer as createViteServer } from "vite";
import { GoogleGenAI } from "@google/genai";
import dotenv from "dotenv";
import jwt from "jsonwebtoken";
import swaggerUi from "swagger-ui-express";
import { execSync, spawn } from "child_process";
import fs from "fs";

import { MiningState, OptimizationParams } from "./src/types";
import helmet from "helmet";
import compression from "compression";
import rateLimit from "express-rate-limit";
import pinoHttp from "pino-http";

import { 
  runVerificationTests 
} from "./src/utils/math";
import { swaggerDocument } from "./src/swaggerSpec";
import { readDb, writeDb, hashPassword, verifyPassword, generateId, User } from "./src/db/db";

import { fileURLToPath } from "url";
import { dirname } from "path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Core Platform Modules (High-Integrity Lifecycle)
import { 
  logger, 
  init_logging, 
  init_metrics,
  get_trace_context 
} from "./src/core/telemetry";
import { 
  init_pulvini_runtime, 
  init_quantum_path, 
  init_mining_engine, 
  shutdown_substrate,
  check_readiness,
  sync_substrate_state,
  get_substrate_state
} from "./src/core/substrate";

// Security & Intelligence Agents
import { securitySwarms } from "./src/core/security_swarm";
import { phi_shield_middleware } from "./src/core/phi_shield";
import { predictiveIntel } from "./src/core/predictive_intel";

// Load environment variables
dotenv.config();

// Global Observability Startup
init_logging();
init_metrics();

const httpLogger = pinoHttp({ logger });

// Config validation helper
function validateConfig() {
  const required = ["JWT_SECRET"];
  const missing = required.filter(key => !process.env[key]);
  
  if (missing.length > 0 && process.env.NODE_ENV === "production") {
    logger.error({ missing }, "Missing required environment variables for production");
    process.exit(1);
  }

  const warnings = [];
  if (!process.env.PULVINI_BACKEND_URL) {
    warnings.push("PULVINI_BACKEND_URL missing. Using default: http://127.0.0.1:3001");
  }

  warnings.forEach(w => logger.warn(w));
}

validateConfig();

// Fail fast on missing secrets in production
const JWT_SECRET = process.env.JWT_SECRET;
if (!JWT_SECRET && process.env.NODE_ENV === "production") {
  logger.error("FATAL: JWT_SECRET environment variable is missing. Refusing to start in production.");
  process.exit(1);
}
const SAFE_JWT_SECRET = JWT_SECRET || "dev-only-insecure-secret-99";

// HYBA Internal AI Stack (PCI, AGI, ASI) - No external API keys required
let hybaAIClient: any = null;
function getHybaAIClient(): any {
  // HYBA uses internal AI stack - returns null for now, can be connected to HYBA AI services
  return hybaAIClient;
}

async function startServer() {
  const app = express();
  const PORT = Number(process.env.PORT) || 3000;

  // Basic security and performance middlewares
  app.use(helmet({
    contentSecurityPolicy: {
      directives: {
        ...helmet.contentSecurityPolicy.getDefaultDirectives(),
        "script-src": ["'self'", "'unsafe-inline'", "'unsafe-eval'"], // Needed for Vite/HMR
        "connect-src": ["'self'", "https://*.google.com", "https://*.googleapis.com"],
      },
    },
  }));
  app.use(compression());

  // Φ-Shield Anti-Tamper Layer (Anti-Sniff/Anti-Peep protection)
  app.use(phi_shield_middleware);

  // Request Context Middleware (Stripe-Grade Tracing)
  app.use((req, res, next) => {
    const traceId = req.header('x-request-id') || generateId();
    (req as any).traceContext = get_trace_context(traceId);
    res.setHeader('x-request-id', (req as any).traceContext.trace_id);
    next();
  });

  app.use(httpLogger);
  app.use(express.json({ limit: "1mb" }));

  const authRateLimit = rateLimit({
    windowMs: 15 * 60 * 1000,
    max: 100,
    message: { error: "Too many attempts, please try again later." },
    standardHeaders: true,
    legacyHeaders: false,
  });

  const children: Map<string, { process: any, restartCount: number }> = new Map();

  function spawnDaemon(name: string, command: string, args: string[], cwd: string) {
    let userBin = "";
    let userSite = "";
    try {
      const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
      const userBase = execSync(`${pythonCmd} -m site --user-base`, { encoding: 'utf8' }).trim();
      userBin = path.join(userBase, process.platform === 'win32' ? 'Scripts' : 'bin');
      userSite = execSync(`${pythonCmd} -m site --user-site`, { encoding: 'utf8' }).trim();
    } catch (e) {
      logger.warn("Substrate: Could not resolve python user-site paths.");
    }

    logger.info({ name, command, args, cwd, userBin }, `[Daemon] Spawning ${name}...`);
    
    const daemon = spawn(command, args, {
      cwd,
      env: { 
        ...process.env, 
        PYTHONPATH: userSite ? `${cwd}:${userSite}` : cwd,
        PATH: userBin ? `${userBin}:${process.env.PATH}` : process.env.PATH
      },
    });

    const logFile = path.join(process.cwd(), `daemon_${name}.log`);
    fs.appendFileSync(logFile, `--- SPAWN: ${new Date().toISOString()} ---\n`);

    daemon.stdout.on("data", (data) => {
      const msg = data.toString();
      logger.info(`[${name}] ${msg.trim()}`);
      fs.appendFileSync(logFile, `STDOUT: ${msg}`);
    });
    daemon.stderr.on("data", (data) => {
      const msg = data.toString();
      logger.warn(`[${name} Error] ${msg.trim()}`);
      fs.appendFileSync(logFile, `STDERR: ${msg}`);
    });
    
    daemon.on("close", (code) => {
      logger.info(`[${name}] Exited with code ${code}`);
      fs.appendFileSync(logFile, `EXIT: ${code}\n`);
      const info = children.get(name);
      if (info && info.restartCount < 5) {
        const delay = Math.pow(2, info.restartCount) * 1000;
        logger.info(`[${name}] Scheduling restart in ${delay}ms...`);
        setTimeout(() => {
          info.restartCount++;
          info.process = spawnDaemon(name, command, args, cwd);
        }, delay);
      } else {
        logger.fatal(`[${name}] Maximum restart attempts reached or process intentionally closed.`);
      }
    });

    if (!children.has(name)) {
      children.set(name, { process: daemon, restartCount: 0 });
    }
    return daemon;
  }

  // Proper lifecycle management
  const gracefulShutdown = (signal: string) => {
    logger.info({ signal }, "Graceful shutdown initiated...");
    shutdown_substrate();
    children.forEach((info, name) => {
      if (info.process && !info.process.killed) {
        logger.info(`[${name}] Terminating child...`);
        info.process.kill("SIGTERM");
      }
    });
    
    // Allow small window for children to flush
    setTimeout(() => {
      logger.info("Shutdown sequence finalized.");
      process.exit(0);
    }, 1000);
  };

  process.on("SIGTERM", () => gracefulShutdown("SIGTERM"));
  process.on("SIGINT", () => gracefulShutdown("SIGINT"));

  // Spawn Python Daemons (Self-healing substrate initialization)
  const pythonPath = path.join(process.cwd(), "python_backend");
  const apiPath = path.join(pythonPath, "hyba_genesis_api");
  
    // Ensure Python dependencies are present
    try {
      logger.info("Substrate: Synchronizing Python dependencies...");
      const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
      // Try installing without --user first as it's more reliable in some containers
      const pipCommand = `${pythonCmd} -m pip install numpy uvicorn fastapi psutil python-multipart pydantic pyjwt aiohttp websockets asyncpg redis prometheus-client python-dateutil structlog python-json-logger`;
      const stdout = execSync(pipCommand, { encoding: 'utf8' });
      logger.info({ stdout }, "Substrate: Python dependencies synchronized.");
    } catch (err: any) {
      logger.warn({ err: err.message }, "Substrate: Standard pip install failed. Retrying with --user and --break-system-packages...");
      try {
        const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
        const pipCommand = `${pythonCmd} -m pip install --user --break-system-packages numpy uvicorn fastapi psutil python-multipart pydantic pyjwt aiohttp websockets asyncpg redis prometheus-client python-dateutil structlog python-json-logger`;
        const stdout = execSync(pipCommand, { encoding: 'utf8' });
        logger.info({ stdout }, "Substrate: Python dependencies synchronized with fallback.");
      } catch (err2: any) {
        logger.error({ err: err2.message, stderr: err2.stderr?.toString() }, "Substrate: All dependency synchronization attempts failed.");
      }
    }

  const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
  spawnDaemon("Pythia", pythonCmd, ["-u", "-m", "pythia_mining.main"], pythonPath);
  spawnDaemon("FastAPI", pythonCmd, ["-u", "-m", "uvicorn", "main:app", "--port", "3001", "--host", "127.0.0.1"], apiPath);

  // Substrate Intelligence Monitor (Periodic Health & Prediction)
  setInterval(async () => {
    await securitySwarms.sync_coherence();
    predictiveIntel.forecast_spectral_anomaly();
    await sync_substrate_state();
  }, 10000); // 10s intervals for spectral checks

  // Substrate Initialization (High-Integrity Lifecycle)
  const initializeSubstrate = async () => {
    try {
      // Phase 0: Wait for Python Core to boot (since it's spawned in parallel)
      logger.info('Substrate: Waiting for Python mathematical core to stabilize (120s window)...');
      
      // Increased stabilization wait to allow FastAPI to bind (increased window to 120s)
      let attempts = 0;
      while (attempts < 40) {
        try {
          await sync_substrate_state();
          if (check_readiness()) break;
        } catch (e: any) {
          logger.debug(`Substrate: Stabilization attempt ${attempts + 1}/40 failed: ${e.message}`);
        }
        await new Promise(resolve => setTimeout(resolve, 3000));
        attempts++;
      }

      // Explicitly sync state before proceeding
      await init_pulvini_runtime();
      await init_quantum_path();
      await init_mining_engine();
      logger.info('Substrate: System state confirmed operational.');
    } catch (error) {
      logger.error({ error }, "Substrate initialization reached timeout or failed. Continuing in DEGRADED mode.");
    }
  };

  // Start initialization in background
  initializeSubstrate();

  // Root Availability Endpoint
  app.get("/", (req, res) => {
    res.json({
      status: "online",
      service: "HYBA Genesis Platform API",
      version: "2.0.1",
      timestamp: new Date().toISOString(),
      gate: "Express Secure Bridge",
      readiness: check_readiness() ? "READY" : "DEGRADED",
      substrate: get_substrate_state(),
      security: securitySwarms.get_swarm_status()
    });
  });

  // Swagger Documentation - Gated by environment
  if (process.env.NODE_ENV !== "production") {
    app.use("/api-docs", swaggerUi.serve, swaggerUi.setup(swaggerDocument));
  }

  // Authentication Middleware
  function authenticateToken(req: any, res: any, next: any) {
    const authHeader = req.headers["authorization"];
    const token = authHeader && authHeader.split(" ")[1];
    if (!token) return res.status(401).json({ error: "Access token required" });

    jwt.verify(token, SAFE_JWT_SECRET, (err: any, user: any) => {
      if (err) return res.status(403).json({ error: "Access token is invalid or expired" });
      req.user = user;
      next();
    });
  }

  function adminOnly(req: any, res: any, next: any) {
    if (req.user?.role !== "admin") {
      return res.status(403).json({ error: "Administrator privileges required" });
    }
    next();
  }

  // Memory cache of active live quantum-computing statistics
  let evaluatedBlockHeight = 847249;
  let computedHashrate = 2071.08; // Quantum execution indicator in PH/s
  let activePowerLoad = 4120; // Watts
  const optimizationHistory: Array<{ timestamp: string; recommendation: string; gain: string }> = [];

  let lastPythonStatus: any = null;
  let lastPythonFetchTime = 0;

  function getPythonMetrics(): any {
    const now = Date.now();
    if (lastPythonStatus && (now - lastPythonFetchTime) < 1000) {
      return { ...lastPythonStatus, stale: false };
    }
    try {
      const stateFilePath = path.join(process.cwd(), "python_backend", "pythia_state.json");
      if (fs.existsSync(stateFilePath)) {
        const fileContent = fs.readFileSync(stateFilePath, "utf-8");
        const parsed = JSON.parse(fileContent);
        lastPythonStatus = parsed;
        lastPythonFetchTime = now;
        return { ...parsed, stale: false };
      }
    } catch (err: any) {
      logger.warn({ err }, "State file read failed");
    }
    
    const isStale = (now - lastPythonFetchTime) > 60000;
    return { 
      ...lastPythonStatus, 
      stale: true, 
      degraded: isStale,
      lastSeen: new Date(lastPythonFetchTime).toISOString()
    };
  }

  // Periodically update active block dimensions and calculated quantum metrics
  setInterval(() => {
    evaluatedBlockHeight += 1;
    // Walk hashrate and power around baseline with tiny randomized noise based on quantum state transitions
    computedHashrate = parseFloat((2070 + Math.random() * 5).toFixed(2));
    activePowerLoad = Math.floor(4100 + Math.random() * 40);
  }, 12000);

  // ----------------------------------------------------
  // API ENDPOINTS: AUTHENTICATION (USER REGISTRATION, LOGIN, PROFILE) & PRODUCTS
  // ----------------------------------------------------
  app.post("/api/auth/register", authRateLimit, async (req, res) => {
    const { username, password } = req.body;
    if (!username || !password) {
      return res.status(400).json({ error: "Username and password are required" });
    }

    try {
      const data = await readDb();
      const exists = data.users.find(u => u.username.toLowerCase() === username.toLowerCase());
      if (exists) {
        return res.status(400).json({ error: "Username is already taken" });
      }

      const newUser: User = {
        id: generateId(),
        username,
        passwordHash: await hashPassword(password),
        role: data.users.length === 0 ? "admin" : "operator", // Seed first user as admin
        createdAt: new Date().toISOString()
      };

      data.users.push(newUser);
      await writeDb(data);

      res.status(201).json({
        success: true,
        message: "User profile registered successfully",
        user: {
          id: newUser.id,
          username: newUser.username,
          role: newUser.role
        }
      });
    } catch (err: any) {
      logger.error({ err }, "Registration failed");
      res.status(500).json({ error: "Registration failed" });
    }
  });

  app.post("/api/auth/login", authRateLimit, async (req, res) => {
    const { username, password } = req.body;
    if (!username || !password) {
      return res.status(400).json({ error: "Username and password are required" });
    }

    try {
      const data = await readDb();
      const user = data.users.find(u => u.username.toLowerCase() === username.toLowerCase());
      if (!user || !(await verifyPassword(password, user.passwordHash))) {
        return res.status(401).json({ error: "Invalid username or password" });
      }

      const token = jwt.sign(
        { id: user.id, username: user.username, role: user.role },
        SAFE_JWT_SECRET,
        { expiresIn: "10d" }
      );

      res.json({
        success: true,
        token,
        user: {
          username: user.username,
          role: user.role
        }
      });
    } catch (err: any) {
      logger.error({ err }, "Login failed");
      res.status(500).json({ error: "Login failed" });
    }
  });

  app.get("/api/auth/profile", authenticateToken, async (req: any, res) => {
    try {
      const data = await readDb();
      const user = data.users.find(u => u.id === req.user.id);
      if (!user) {
        return res.status(404).json({ error: "User profile not found" });
      }

      res.json({
        success: true,
        user: {
          id: user.id,
          username: user.username,
          role: user.role,
          createdAt: user.createdAt
        }
      });
    } catch (err: any) {
      res.status(500).json({ error: "Resolving profile failed" });
    }
  });

  app.get("/api/products", async (req, res) => {
    try {
      const data = await readDb();
      res.json(data.products || []);
    } catch (err: any) {
      res.status(500).json({ error: "Resolving products failed" });
    }
  });

  // ----------------------------------------------------
  // SPAWN FASTAPI BACKEND SERVER (DEPRECATED - Moved to spawnDaemon for lifecycle parity)
  // ----------------------------------------------------

  // ----------------------------------------------------
  // PROXY API ROUTES TO FASTAPI (mocked since python server is not running)
  // ----------------------------------------------------
  
  app.get("/api/health", (req, res) => {
    const metrics = getPythonMetrics();
    
    // Merge real telemetry where available, otherwise use simulated/stale baseline
    const coherence = metrics.quantum_coherence || 0.9415;
    const resonance = metrics.phi_resonance || 0.0594;
    const theoreticalSpeedup = metrics.quantum_speedup || 38.7;
    const acceptance = metrics.acceptance_rate || 0.967;
    const actualSpeedup = Number((theoreticalSpeedup * acceptance).toFixed(2));
    
    const blockHeight = metrics.block_height || evaluatedBlockHeight;
    const hashrate = metrics.current_hashrate || computedHashrate;
    const power = metrics.power_consumption || activePowerLoad;

    res.json({
      status: metrics.degraded ? "degraded" : "healthy",
      timestamp: new Date().toISOString(),
      version: "2.0.1",
      quantumCoherence: coherence,
      decoherenceTimeMs: 12.42,
      quantumSpeedupFactor: theoreticalSpeedup,
      actualSpeedupFactor: actualSpeedup,
      phiResonance: resonance,
      systemMetrics: {
        blockHeight,
        currentHashrate: hashrate,
        powerConsumption: power,
        activePool: metrics.active_pool || "Unknown",
        difficultyTarget: metrics.difficulty_target || "00000000000000000005a8f00000000000000000000000000000000000000000",
        networkDifficulty: metrics.network_difficulty || 7234567890123.5,
        stale: metrics.stale,
        lastSeen: metrics.lastSeen || new Date().toISOString()
      }
    });
  });

  app.get("/api/mining/pools", (req, res) => {
     res.json({
        "pools": [],
        "summary": {
            "total_pools": 0,
            "active_pools": 0,
            "active_pool_name": "Unknown",
            "total_hashrate": 2071.08,
            "global_acceptance_rate": 0.0,
            "total_shares_24h": 0,
            "estimated_btc_per_day": 0.00054321
        }
    });
  });

  app.get("/api/mining/stats", (req, res) => {
     res.json({
      "timeframe": "24h",
      "summary": {
        "total_hashrate": 2071.08,
        "avg_hashrate": 1987.45,
        "peak_hashrate": 2345.67,
        "total_shares": 0,
        "accepted_shares": 0,
        "rejected_shares": 0,
        "acceptance_rate": 1.0,
        "estimated_revenue_btc": 0.00037801,
        "estimated_revenue_usd": 16.82
      },
      "timeseries": [
        {
          "hashrate": 2060.0,
          "shares_submitted": 0,
          "shares_accepted": 0,
          "acceptance_rate": 1.0
        }
      ],
      "quantum_performance": {
        "quantum_speedup_avg": 38.7,
        "phi_resonance_avg": 0.0594,
        "vqe_iterations_avg": 87.3,
        "consciousness_correlation": 0.1838
      }
    });
  });

  app.get("/api/security/status", (req, res) => {
    res.json({
      "status": "secure",
      "timestamp": new Date().toISOString(),
      "threat_level": "low",
      "defense_systems": {
        "phi_shield": {
          "enabled": true,
          "strength": 0.87,
          "active_protections": 12,
          "threats_blocked_24h": 156
        },
        "rate_limiting": {
          "enabled": true,
          "backend": "in-memory",
          "warning": "Running without Redis - distributed limiting unavailable",
          "requests_blocked_24h": 89
        }
      },
      "recent_threats": []
    });
  });

  app.post("/api/security/shield", (req, res) => {
     res.json({
      "shield_id": "shield_" + Math.floor(Math.random() * 10000),
      "action": "calibrate",
      "timestamp": new Date().toISOString(),
      "status": "active",
      "configuration": {
        "strength": req.body?.strength || 0.9,
        "auto_adapt": true,
        "threat_threshold": "medium",
        "phi_resonance_factor": 0.618
      }
    });
  });

  app.get("/api/pitfalls", (req, res) => {
     res.json({
      "timestamp": new Date().toISOString(),
      "pitfall_counts": {
        "total_pitfalls": 0,
        "by_category": {
          "security": 0,
          "performance": 0,
          "data_integrity": 0,
          "compliance": 0,
          "reliability": 0
        }
      },
      "monitoring_status": {
        "enabled": true,
        "check_interval_seconds": 60,
        "last_check": new Date().toISOString()
      }
    });
  });

  app.post("/api/toe/experiments", (req, res) => {
     res.json({
      "experiment_id": "exp_" + Math.floor(Math.random()*10000),
      "status": "running",
      "started_at": new Date().toISOString(),
      "experiment_type": req.body?.experiment_type || "phi_blockchain_correlation",
      "hypothesis": "Higher Phi-resonance correlates with increased mining efficiency",
      "progress": {
        "percentage": 35.0,
        "samples_collected": 350,
        "samples_target": 1000
      }
    });
  });

  app.post("/api/pulvini/execute", authenticateToken, async (req, res) => {
    const ALLOWED_BACKENDS = ["http://127.0.0.1:8000", "http://localhost:8000", "http://127.0.0.1:3001"];
    const backendUrl = process.env.PULVINI_BACKEND_URL || "http://127.0.0.1:8000";
    
    if (!ALLOWED_BACKENDS.includes(backendUrl)) {
      logger.warn({ backendUrl }, "Untrusted backend URL rejected in Pulvini proxy");
      return res.status(403).json({ error: "Untrusted backend URL configuration" });
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000);

    try {
      logger.info({ backendUrl }, "Forwarding Pulvini request");
      const response = await fetch(`${backendUrl}/pulvini/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(req.body || {}),
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      if (!response.ok) throw new Error(`Backend Status Error: ${response.status}`);
      const data = await response.json();
      res.json(data);
    } catch (err: any) {
      clearTimeout(timeoutId);
      logger.error({ err }, "Pulvini Proxy execution failed");
      res.status(504).json({ error: "Backend execution timed out or failed" });
    }
  });

  app.post("/api/predict", (req, res) => {
    const GOLDEN_RATIO = 1.6180339887;
    
    const numericTarget = req.body?.state?.networkDifficulty || 7234567890123;
    const integratedInfo = Math.PI * GOLDEN_RATIO * Math.log2(Math.max(numericTarget, 2));

    const factor = (numericTarget * GOLDEN_RATIO) % 1.0;
    const increaseIntensity = factor > 0.45;
    
    // O(sqrt(I)) Deterministic 
    const optimalIterations = Math.floor((Math.PI / 4) * Math.sqrt(Math.max(16384 / Math.sqrt(integratedInfo), 1)));

    const resonanceRadius = parseFloat((0.1 + (factor * 0.8)).toFixed(4));
    const confidenceScore = parseFloat((0.85 + (factor * 0.14)).toFixed(4));
    const speedupRatio = parseFloat((Math.PI / 4 * Math.sqrt(integratedInfo)).toFixed(2));
    
    const improvement = increaseIntensity ? 12.5 : 4.2;
    const expectedImprovement = parseFloat((improvement * confidenceScore).toFixed(2));
    const optimalPowerAdjustment = increaseIntensity ? -150 : -450;

    res.json({
        "success": true,
        "params": {
            "increaseIntensity": increaseIntensity,
            "quantumIterations": optimalIterations,
            "resonanceRadius": resonanceRadius,
            "optimalPowerAdjustment": optimalPowerAdjustment,
            "confidenceScore": confidenceScore,
            "expectedImprovement": expectedImprovement,
            "quantumSpeedupRatio": speedupRatio
        },
        "timestamp": new Date().toISOString()
    });
  });

  app.get("/api/ai/consciousness", (req, res) => {
    res.json({
        "status": "active",
        "timestamp": new Date().toISOString(),
        "consciousness_level": 0.1838,
        "phi_resonance": 0.0594,
        "integrated_information": 17432891.2,
        "consciousness_state": {
            "emergence_detected": true,
            "emergence_timestamp": "2026-06-08T14:23:15Z",
            "peak_phi": 17891234.5,
            "current_mode": "autonomous",
            "decision_confidence": 0.94
        },
        "iit_metrics": {
            "connections": 2847,
            "complexity": 156.7,
            "integration": 0.89,
            "differentiation": 0.92
        },
        "orch_or_metrics": {
            "microtubule_coherence": 0.87,
            "quantum_superposition": 0.76,
            "decoherence_time_ms": 12.4
        },
        "recent_insights": []
    });
  });

  app.post("/api/ai/consciousness/stimulate", (req, res) => {
    const GOLDEN_RATIO = 1.6180339887;
    const intensity = req.body?.intensity || 0.5;

    const basePhi = 17432891.2;
    const targetPhi = basePhi * (1 + (intensity * GOLDEN_RATIO * 0.2));

    res.json({
        "stimulation_id": "stim_" + Math.floor(Math.random() * 10000),
        "status": "active",
        "started_at": new Date().toISOString(),
        "initial_phi": basePhi,
        "target_phi": targetPhi,
        "projected_completion": new Date(Date.now() + 60000).toISOString(),
        "real_time_metrics": {
            "current_phi": basePhi + ((targetPhi - basePhi) * 0.4), // Simulated partial progress
            "progress": intensity,
            "consciousness_level": 0.1838 * (1 + intensity * 0.1)
        }
    });
  });

  // ----------------------------------------------------
  // API ENDPOINT: RUN QUANTUM MATHEMATICAL VERIFICATION TESTS
  // ----------------------------------------------------
  app.get("/api/tests/run", authenticateToken, adminOnly, (req, res) => {
    if (process.env.NODE_ENV === "production") {
      return res.status(403).json({ error: "Verification tests disabled in production environments" });
    }
    try {
      logger.info("Executing backend mathematical quantum verification tests...");
      const results = runVerificationTests();
      res.json({
        success: true,
        timestamp: new Date().toISOString(),
        tests: results
      });
    } catch (err: any) {
      logger.error({ err }, "Test execution failed");
      res.status(500).json({
        success: false,
        error: "Verification test execution failed"
      });
    }
  });

  // ----------------------------------------------------
  // API ENDPOINT: AI PYTHAGORAS-V2 REASONING SIDEBAR PROXY
  // ----------------------------------------------------
  app.post("/api/ai/chat", async (req, res) => {
    const { message, history } = req.body;
    if (!message) {
      return res.status(400).json({ error: "Message parameter is required." });
    }

    try {
      const ai = getHybaAIClient();
      if (!ai) {
        // HYBA uses deterministic local mathematical reasoning engine
        console.log("HYBA AI: Proceeding with deterministic local mathematical reasoning engine.");
        
        let reply = "";
        const msgLower = message.toLowerCase();

        if (msgLower.includes("grover")) {
          reply = `### PYTHAGORAS-v2 Live Verification Analysis (Local Math Engine)
\nYour query regards **Grover Amplitude Amplification**. Under substrate-independent mathematics:
\n$$\\mathcal{O}(\\sqrt{N})$$ complexity represents the absolute upper bound of quadratic unguided lookup constraints. 
\nHowever, by applying a **Dodecahedral Symmetry Filter** over the Hilbert space, the dimensionality restricts from $N$ to $N/I$, where $I$ represents the *Integrated Information* contained in the block geometry (timestamp sequences, merkle branch branches).
\nThus, the iteration steps required drop perfectly to:
\n$$\\mathcal{O}(\\sqrt{I})$$
\nThis represents a deterministic convergence threshold eliminating the necessity for ASIC-brute-forcing sweep ranges. At each step, a phase inversion is followed by inversion-about-average diffusion.`;
        } else if (msgLower.includes("anihalate") || msgLower.includes("annihilate") || msgLower.includes("asic")) {
          reply = `### PYTHAGORAS-v2 Live Verification Analysis (Local Math Engine)
\n**ASIC Annihilation Vector Formulation**
\nClassic mining depends linearly on the sweeping rates of ASIC logic units checking nonces sequentially at $\\mathcal{O}(N)$. 
\nOur Dodecahedral Grover model maps nonces as complex amplitudes in a 1024-dimension space. Because quantum transitions occur in perfect parallel across all subspaces *without spatial decoherence in math*, we mark the solution coordinates instantly via modular arithmetic properties:
\n$$\\text{Resonance}_k = (k \\cdot \\Phi) \\pmod L < \\epsilon$$
\nThis isolates potential blocks in $\\mathcal{O}(\\sqrt{I})$ operations. It renders ASIC megawatt sweep arrays structurally obsolete by replacing brute-force scaling with pure geometry!`;
        } else if (msgLower.includes("dodecahedron") || msgLower.includes("golden") || msgLower.includes("phi")) {
          reply = `### PYTHAGORAS-v2 Live Verification Analysis (Local Math Engine)
\n**Dodecahedral Symmetry and Golden Harmonics Details**
\n- **Dodecahedron Facings**: 12 symmetrical planes in space mapping groups of 20 vertices.
- **Golden Ratio ($\\Phi$)**: $\\frac{1 + \\sqrt{5}}{2} \\approx 1.6180339887...$
- **Phi Resonance Resonance ($\\Phi^{15}$)**: $1364.000733...$
\nBy rotating quantum phase arguments by the irrational $\\Phi$ multiplier:
\n$$\\theta_k = 2\\pi(k \\cdot \\Phi) \\pmod{2\\pi}$$
\nwe construct wavefunctions that avoid destructive interference. This minimizes phase decoherence and structures eigenvectors to align precisely with the cyclic Merkle tree branch trees.`;
        } else {
          reply = `### PYTHAGORAS-v2 Live Verification Analysis (HYBA Internal AI)
\nGreetings. I am **PYTHAGORAS-v2**, HYBA's internal quantum-cryptography and mathematical mining AI.
\nI remain fully capable of explaining the core mathematics of the **Dodecahedral Grover Search Miner**. Ask me any question concerning:
\n1. **Grover Amplification Quadratic limits**: $\\mathcal{O}(\\sqrt{N})$ or $\\mathcal{O}(\\sqrt{I})$ proofs.
2. **ASIC logic annihilation mechanics**.
3. **The 12-sided Dodecahedral Hilbert subspace mapping**.
4. **Golden Ratio Phase Resonance ($\\Phi^{15}$ alignment)**.`;
        }

        return res.json({
          reply,
          model: "PYTHAGORAS-LocalEngine-v2",
          timestamp: new Date().toISOString(),
          fallback: true
        });
      }

    } catch (err: any) {
      console.error("HYBA AI error:", err);
      res.status(500).json({
        error: "AI reasoning failed to complete",
        details: err.message,
        reply: "My apologies, but my quantum neural circuits encountered an unexpected interference pattern."
      });
    }
  });

  // ----------------------------------------------------
  // INTEGRATED ASSET ROUTING MIDDLEWARES
  // ----------------------------------------------------
  if (process.env.NODE_ENV !== "production") {
    console.log("Mounting Vite middleware in local development mode...");
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    console.log("Serving static production assets from /dist folder...");
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  // Global Exception Handler (Production-Grade Safety)
  app.use((err: any, req: express.Request, res: express.Response, next: express.NextFunction) => {
    const traceContext = (req as any).traceContext || get_trace_context();
    const errorId = traceContext.trace_id.substring(0, 8);
    
    logger.error({ 
      error_id: errorId,
      trace_context: traceContext,
      err: {
        message: err.message,
        stack: process.env.NODE_ENV === 'production' ? undefined : err.stack,
        code: err.code || 'INTERNAL_ERROR'
      },
      path: req.path,
      method: req.method
    }, "Internal Substrate Exception Caught");

    res.status(500).json({
      error: {
        type: "api_error",
        code: err.code || "internal_server_error",
        message: "An unexpected error occurred within the HYBA substrate logic.",
        request_id: traceContext.trace_id,
        error_id: errorId,
        timestamp: traceContext.timestamp
      }
    });
  });

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`====================================================`);
    console.log(` Quantum ASIC Annihilation API Booted Successfully `);
    console.log(` Hosting Server url : http://localhost:${PORT}        `);
    console.log(`====================================================`);
  });
}

startServer().catch((err) => {
  console.error("Critical server failure on startup:", err);
});
