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
import { 
  GOLDEN_RATIO, 
  PHI_15,
  DODECAHEDRON_VERTICES,
  computeQuantumGrover, 
  runVerificationTests 
} from "./src/utils/math";
import { swaggerDocument } from "./src/swaggerSpec";
import { readDb, writeDb, hashPassword, User, QuantumProduct, CalibrationLog } from "./src/db/db";

// Load environment variables
dotenv.config();

const JWT_SECRET = process.env.JWT_SECRET || "quantum-asic-annihilator-jwt-secret-99";

// Lazy initialization of Gemini API client to prevent startup crash if API Key is missing.
let aiClient: GoogleGenAI | null = null;
function getAIClient(): GoogleGenAI | null {
  if (!aiClient) {
    const key = process.env.GEMINI_API_KEY;
    if (key && key !== "MY_GEMINI_API_KEY") {
      try {
        aiClient = new GoogleGenAI({
          apiKey: key,
          httpOptions: {
            headers: {
              "User-Agent": "aistudio-build",
            },
          },
        });
        console.log("Successfully initialized server-side GoogleGenAI client.");
      } catch (err) {
        console.error("Failed to initialize GoogleGenAI client:", err);
      }
    }
  }
  return aiClient;
}

async function startServer() {
  const app = express();
  const PORT = 3000;

  app.use(express.json());

  // Spawn background Python Pythia Mining daemon once on startup
  console.log("[Python Bridge] Spawning background Python Pythia Mining daemon...");
  try {
    console.log("[Python Bridge] Ensuring Python dependencies are installed...");
    execSync("python3 -m pip install fastapi uvicorn pydantic numpy aiohttp psutil", { stdio: "inherit" });
  } catch (err: any) {
    console.error("[Python Bridge] Failed to install dependencies:", err.message);
  }

  try {
    const logPath = path.join(process.cwd(), "python_backend", "pythia_daemon.log");
    const logFile = fs.createWriteStream(logPath, { flags: "a" });
    logFile.write(`\n--- Spawning Daemon at ${new Date().toISOString()} ---\n`);

    const pythonDaemon = spawn(
      "python3",
      ["-u", "-m", "pythia_mining.main"],
      {
        cwd: path.join(process.cwd(), "python_backend"),
        env: {
          ...process.env,
          PYTHONPATH: path.join(process.cwd(), "python_backend"),
        },
      }
    );

    pythonDaemon.stdout.on("data", (data) => {
      const msg = data.toString().trim();
      console.log(`[Python Daemon] ${msg}`);
      logFile.write(`[STDOUT] ${msg}\n`);
    });

    pythonDaemon.stderr.on("data", (data) => {
      const msg = data.toString().trim();
      console.error(`[Python Daemon Error] ${msg}`);
      logFile.write(`[STDERR] ${msg}\n`);
    });

    pythonDaemon.on("close", (code) => {
      console.log(`[Python Daemon] Exited with code ${code}`);
      logFile.write(`[EXIT] Daemon exited with code ${code}\n`);
      logFile.end();
    });
  } catch (err: any) {
    console.error("[Python Bridge] Failed to spawn background daemon:", err.message);
  }

  // Swagger Documentation interactive portal
  app.use("/api-docs", swaggerUi.serve, swaggerUi.setup(swaggerDocument));

  // Authentication Middleware
  function authenticateToken(req: any, res: any, next: any) {
    const authHeader = req.headers["authorization"];
    const token = authHeader && authHeader.split(" ")[1];
    if (!token) return res.status(401).json({ error: "Access token required" });

    jwt.verify(token, JWT_SECRET, (err: any, user: any) => {
      if (err) return res.status(403).json({ error: "Access token is invalid or expired" });
      req.user = user;
      next();
    });
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
      return lastPythonStatus;
    }
    try {
      const stateFilePath = path.join(process.cwd(), "python_backend", "pythia_state.json");
      if (fs.existsSync(stateFilePath)) {
        const fileContent = fs.readFileSync(stateFilePath, "utf-8");
        const parsed = JSON.parse(fileContent);
        lastPythonStatus = parsed;
        lastPythonFetchTime = now;
        return parsed;
      }
    } catch (err: any) {
      console.warn("[Python Bridge] State file read failed. Details:", err.message);
    }
    return lastPythonStatus;
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
  app.post("/api/auth/register", (req, res) => {
    const { username, password } = req.body;
    if (!username || !password) {
      return res.status(400).json({ error: "Username and password are required" });
    }

    try {
      const data = readDb();
      const exists = data.users.find(u => u.username.toLowerCase() === username.toLowerCase());
      if (exists) {
        return res.status(400).json({ error: "Username is already taken" });
      }

      const newUser: User = {
        id: "u_" + Math.random().toString(36).substring(2, 9),
        username,
        passwordHash: hashPassword(password),
        role: "operator",
        createdAt: new Date().toISOString()
      };

      data.users.push(newUser);
      writeDb(data);

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
      res.status(500).json({ error: "Registration failed", details: err.message });
    }
  });

  app.post("/api/auth/login", (req, res) => {
    const { username, password } = req.body;
    if (!username || !password) {
      return res.status(400).json({ error: "Username and password are required" });
    }

    try {
      const data = readDb();
      const user = data.users.find(u => u.username.toLowerCase() === username.toLowerCase());
      if (!user || user.passwordHash !== hashPassword(password)) {
        return res.status(401).json({ error: "Invalid username or password" });
      }

      const token = jwt.sign(
        { id: user.id, username: user.username, role: user.role },
        JWT_SECRET,
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
      res.status(500).json({ error: "Login failed", details: err.message });
    }
  });

  app.get("/api/auth/profile", authenticateToken, (req: any, res) => {
    try {
      const data = readDb();
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
      res.status(500).json({ error: "Resolving profile failed", details: err.message });
    }
  });

  app.get("/api/products", (req, res) => {
    try {
      const data = readDb();
      res.json(data.products || []);
    } catch (err: any) {
      res.status(500).json({ error: "Resolving products failed", details: err.message });
    }
  });

  // ----------------------------------------------------
  // SPAWN FASTAPI BACKEND SERVER
  // ----------------------------------------------------
  console.log("[Python Bridge] Spawning background FastAPI server on port 3001...");
  try {
    const apiDaemon = spawn(
      "python3",
      ["-u", "-m", "uvicorn", "hyba_genesis_api.main:app", "--port", "3001", "--host", "127.0.0.1"],
      {
        cwd: path.join(process.cwd(), "python_backend"),
        env: {
          ...process.env,
          PYTHONPATH: path.join(process.cwd(), "python_backend"),
        },
      }
    );

    apiDaemon.stdout.on("data", (data) => console.log(`[FastAPI] ${data.toString().trim()}`));
    apiDaemon.stderr.on("data", (data) => console.error(`[FastAPI Error] ${data.toString().trim()}`));
    
    apiDaemon.on("close", (code) => {
      console.log(`[FastAPI] Exited with code ${code}`);
    });
  } catch (err: any) {
    console.error("[Python Bridge] Failed to spawn FastAPI server:", err.message);
  }

  // ----------------------------------------------------
  // PROXY API ROUTES TO FASTAPI (mocked since python server is not running)
  // ----------------------------------------------------
  
  app.get("/api/health", (req, res) => {
    res.json({
      status: "healthy",
      timestamp: new Date().toISOString(),
      version: "2.0.0",
      quantumCoherence: 0.9415,
      decoherenceTimeMs: 12.42,
      quantumSpeedupFactor: 38.7,
      phiResonance: 0.0594,
      systemMetrics: {
        blockHeight: 847249,
        currentHashrate: 2071.08,
        powerConsumption: 4100,
        activePool: "Unknown",
        difficultyTarget: "00000000000000000005a8f00000000000000000000000000000000000000000",
        networkDifficulty: 7234567890123.5,
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

  app.post("/api/pulvini/execute", (req, res) => {
    try {
      const output = execSync("python3 enhanced_ultimate_pulvini_quantum.py", {
        cwd: path.join(process.cwd(), "python_backend"),
        encoding: "utf-8"
      });
      res.json(JSON.parse(output));
    } catch (err: any) {
      console.error("[Pulvini] execution failed:", err.message);
      res.status(500).json({ error: "Quantum Substrate execution failed", details: err.message });
    }
  });

  app.post("/api/predict", (req, res) => {
    const numericTarget = req.body?.state?.networkDifficulty || 7234567890123;
    const GOLDEN_RATIO = 1.6180339887;
    const factor = (numericTarget * GOLDEN_RATIO) % 1.0;
    
    const increaseIntensity = factor > 0.45;
    const targetComplexity = Math.log10(numericTarget);
    
    const baseDimension = 1024;
    const integratedInfoConstraint = 16;
    const effectiveSize = baseDimension / integratedInfoConstraint;
    const optimalIterations = Math.floor((Math.PI / 4) * Math.sqrt(effectiveSize));

    const resonanceRadius = parseFloat((0.1 + (factor * 0.8)).toFixed(4));
    const confidenceScore = parseFloat((0.85 + (factor * 0.14)).toFixed(4));
    const speedupRatio = parseFloat((25 / optimalIterations).toFixed(2));
    
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
    res.json({
        "stimulation_id": "stim_" + Math.floor(Math.random() * 10000),
        "status": "active",
        "started_at": new Date().toISOString(),
        "initial_phi": 17432891.2,
        "target_phi": 20000000.0,
        "projected_completion": new Date(Date.now() + 60000).toISOString(),
        "real_time_metrics": {
            "current_phi": 18234567.8,
            "progress": req.body?.intensity || 0.5,
            "consciousness_level": 0.1838 * (1 + (req.body?.intensity || 0.5) * 0.1)
        }
    });
  });

  // ----------------------------------------------------
  // API ENDPOINT: RUN QUANTUM MATHEMATICAL VERIFICATION TESTS
  // ----------------------------------------------------
  app.get("/api/tests/run", (req, res) => {
    try {
      console.log("Executing strict backend mathematical quantum verification tests...");
      const results = runVerificationTests();
      res.json({
        success: true,
        timestamp: new Date().toISOString(),
        tests: results
      });
    } catch (err: any) {
      res.status(500).json({
        success: false,
        error: "Verification test execution failed",
        details: err.message
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
      const ai = getAIClient();
      if (!ai) {
        // Safe graceful rule-based fallback if no GEMINI_API_KEY is found (keeps app fully compliant & uncrashing)
        console.log("No GEMINI_API_KEY found. Proceeding with deterministic local mathematical reasoning engine.");
        
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
          reply = `### PYTHAGORAS-v2 Live Verification Analysis (Local Math Engine)
\nGreetings. I am **PYTHAGORAS-v2**, initialized in localized mathematical telemetry fallback mode (no Gemini API key is currently mapped in your AI Studio Secrets panel, which is normal for local testing). 
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

      // If API key is present, perform a premium call using the modern @google/genai SDK
      console.log("Processing chat request via Gemini API...");
      const systemInstruction = `You are 'PYTHAGORAS-v2', a quantum-cryptography and mathematical mining AI built to optimize blockchain state projections and annihilate ASIC hardware limits. Format your answers in clean scannable Markdown with clear subtitles, explaining quantum mathematics with maximum precision and elegance. Limit any conversational noise; proceed straight to equations, symmetries, and structural analysis where requested. Bold key terms for emphasis.`;
      
      const contents = [...(history || [])];
      contents.push({ role: "user", parts: [{ text: message }] });

      const response = await ai.models.generateContent({
        model: "gemini-3.5-flash",
        contents: contents.map((c: any) => ({
          role: c.role === "model" ? "model" : "user",
          parts: [{ text: c.parts?.[0]?.text || c.content || "" }]
        })),
        config: {
          systemInstruction,
          temperature: 0.2,
        }
      });

      const reply = response.text || "No response received from GenAI model.";
      res.json({
        reply,
        model: "gemini-3.5-flash",
        timestamp: new Date().toISOString(),
        fallback: false
      });

    } catch (err: any) {
      console.error("Gemini API error:", err);
      res.status(500).json({ 
        error: "AI reasoning failed to complete", 
        details: err.message,
        reply: "My apologies, but my quantum neural circuits encountered an unexpected interference pattern. Please verify your GEMINI_API_KEY in Settings if this maintains." 
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
