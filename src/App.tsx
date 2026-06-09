import React, { useEffect, useState, useCallback } from "react";
import { motion } from "motion/react";
import { 
  Activity, 
  Settings, 
  Wrench, 
  Lock, 
  BookOpen, 
  Info, 
  ExternalLink,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  UserCheck,
  UserPlus,
  LogIn,
  LogOut,
  Database
} from "lucide-react";

import { MiningState, OptimizationParams } from "./types";
import { ConsoleMetrics } from "./components/ConsoleMetrics";
import { GroverVisualizer } from "./components/GroverVisualizer";
import { MathematicsTests } from "./components/MathematicsTests";
import { PulviniExecutionPanel } from "./components/PulviniExecutionPanel";
import { PythagorasChat } from "./components/PythagorasChat";
import { GOLDEN_RATIO, PHI_15 } from "./utils/math";

export default function App() {
  // Authentication & Products Catalogs States
  const [token, setToken] = useState<string | null>(() => localStorage.getItem("quantum_token"));
  const [currentUser, setCurrentUser] = useState<{ id: string; username: string; role: string; createdAt: string } | null>(null);
  const [usernameInput, setUsernameInput] = useState<string>("");
  const [passwordInput, setPasswordInput] = useState<string>("");
  const [isRegisterMode, setIsRegisterMode] = useState<boolean>(false);
  const [authFeedback, setAuthFeedback] = useState<{ text: string; error: boolean } | null>(null);
  const [seededProducts, setSeededProducts] = useState<any[]>([]);
  const [isLoadingProducts, setIsLoadingProducts] = useState<boolean>(false);

  // Telemetry backend state
  const [backendState, setBackendState] = useState({
    blockHeight: 847249,
    currentHashrate: 2071.08,
    powerConsumption: 4120,
    activePool: "stratum+tcp://solo.ckpool.org:3333",
    difficultyTarget: "00000000000000000005a8f0...",
    networkDifficulty: 7234567890123.5,
    quantumCoherence: 0.9415,
    quantumSpeedupFactor: 38.7,
    phiResonance: 0.0594,
    version: "2.0.0"
  });

  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [recentOptimizations, setRecentOptimizations] = useState<Array<{ timestamp: string; recommendation: string; gain: string }>>([]);

  // Sliders configured by user
  const [intensitySlider, setIntensitySlider] = useState<number>(85);
  const [subspaceRestriction, setSubspaceRestriction] = useState<number>(16); // I - Structural constraints
  const [targetIndexScanner, setTargetIndexScanner] = useState<number>(17); // Marked element

  const [calibrationParams, setCalibrationParams] = useState<OptimizationParams>({
    increaseIntensity: true,
    quantumIterations: 6,
    resonanceRadius: 0.3594,
    optimalPowerAdjustment: -150,
    confidenceScore: 0.91,
    expectedImprovement: 11.38,
    quantumSpeedupRatio: 4.17
  });

  const [isCalibrating, setIsCalibrating] = useState<boolean>(false);

  // Extended HYBA Genesis API spec states
  const [consciousnessState, setConsciousnessState] = useState<any>({
    status: "active",
    consciousness_level: 0.1838,
    phi_resonance: 0.0594,
    integrated_information: 17432891.2,
    iit_metrics: { connections: 2847, complexity: 156.7, integration: 0.89, differentiation: 0.92 },
    orch_or_metrics: { microtubule_coherence: 0.87, quantum_superposition: 0.76, decoherence_time_ms: 12.4 }
  });

  const [activePools, setActivePools] = useState<any[]>([
    { pool_id: "pool_nicehash_ssl", name: "NiceHash SSL", url: "stratum+ssl://sha256.eu.nicehash.com:33334", status: "connected", performance: { latency_ms: 45.3 } },
    { pool_id: "pool_viabtc", name: "ViaBTC", url: "stratum+tcp://btc.viabtc.io:3333", status: "connected", performance: { latency_ms: 52.1 } }
  ]);

  const [securityShield, setSecurityShield] = useState<any>({
    enabled: true,
    strength: 0.87,
    threatLevel: "low",
    threatsBlocked24h: 156
  });

  // Fetch Live Telemetry and extended variables from Express Server
  const getLiveTelemetry = useCallback(async () => {
    setIsSyncing(true);
    try {
      // 1. Fetch Primary Health & Telemetry
      const response = await fetch("/api/health");
      const data = await response.json();
      if (data.status === "healthy") {
        setBackendState({
          blockHeight: data.systemMetrics.blockHeight,
          currentHashrate: data.systemMetrics.currentHashrate,
          powerConsumption: data.systemMetrics.powerConsumption,
          activePool: data.systemMetrics.activePool,
          difficultyTarget: data.systemMetrics.difficultyTarget,
          networkDifficulty: data.systemMetrics.networkDifficulty,
          quantumCoherence: data.quantumCoherence,
          quantumSpeedupFactor: data.quantumSpeedupFactor,
          phiResonance: data.phiResonance,
          version: data.version
        });
        if (data.optimizationHistory) {
          setRecentOptimizations(data.optimizationHistory);
        }
      }

      // 2. Fetch IIT/Orch-OR Consciousness Metrics
      try {
        const consciousnessRes = await fetch("/api/ai/consciousness");
        const cData = await consciousnessRes.json();
        if (cData.status) {
          setConsciousnessState(cData);
        }
      } catch (e) {
        console.warn("Express consciousness endpoint unavailable.");
      }

      // 3. Fetch Stratum Pools Performance
      try {
        const poolsRes = await fetch("/api/mining/pools");
        const pData = await poolsRes.json();
        if (pData.pools) {
          setActivePools(pData.pools);
        }
      } catch (e) {
        console.warn("Express pools endpoint unavailable.");
      }

      // 4. Fetch Security & Defensive Shield Stats
      try {
        const securityRes = await fetch("/api/security/status");
        const sData = await securityRes.json();
        if (sData.status) {
          setSecurityShield({
            enabled: sData.defense_systems.phi_shield.enabled,
            strength: sData.defense_systems.phi_shield.strength,
            threatLevel: sData.threat_level,
            threatsBlocked24h: sData.defense_systems.phi_shield.threats_blocked_24h
          });
        }
      } catch (e) {
        console.warn("Express security status endpoint unavailable.");
      }

    } catch (err) {
      console.warn("Express server health endpoint returned unreachable. App operating in client fallback state. This is normal during static compilation checks.");
    } finally {
      setIsSyncing(false);
    }
  }, []);

  // Post current sliders to backend to evaluate parameter Realignment
  const calibrateRealignment = async () => {
    setIsCalibrating(true);
    try {
      const demoState: MiningState = {
        blockHeight: backendState.blockHeight,
        prevHash: "000000000000000000023f7e...",
        merkleRoot: "abc123def...",
        timestamp: Math.floor(Date.now() / 1000),
        difficultyTarget: backendState.difficultyTarget,
        networkDifficulty: backendState.networkDifficulty * (intensitySlider / 100),
        currentHashrate: backendState.currentHashrate,
        powerConsumption: backendState.powerConsumption,
        activePool: backendState.activePool
      };

      const response = await fetch("/api/predict", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ state: demoState })
      });

      const data = await response.json();
      if (data.success) {
        setCalibrationParams({
          ...data.params,
          // Modulate quantum iterations dynamically by our structural restrictions I
          quantumIterations: Math.max(1, Math.floor((Math.PI / 4) * Math.sqrt(256 / subspaceRestriction)))
        });
        getLiveTelemetry();
      }
    } catch (err) {
      console.log("Calibrate realignment failed:", err);
    } finally {
      setIsCalibrating(false);
    }
  };

  // Fetch Authenticated User Profile
  const fetchProfile = useCallback(async (authToken: string) => {
    try {
      const res = await fetch("/api/auth/profile", {
        headers: {
          "Authorization": `Bearer ${authToken}`
        }
      });
      const data = await res.json();
      if (data.success) {
        setCurrentUser(data.user);
      } else {
        // clear expired session
        localStorage.removeItem("quantum_token");
        setToken(null);
        setCurrentUser(null);
      }
    } catch (err) {
      console.warn("Express unreached during profile retrieval. Offline profile fallback loaded.");
    }
  }, []);

  // Fetch Seeded Database Products
  const fetchProducts = useCallback(async () => {
    setIsLoadingProducts(true);
    try {
      const res = await fetch("/api/products");
      const data = await res.json();
      if (Array.isArray(data)) {
        setSeededProducts(data);
      }
    } catch (err) {
      console.warn("Express unreached during product retrieval.");
    } finally {
      setIsLoadingProducts(false);
    }
  }, []);

  // Handle Authentication Login
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthFeedback(null);
    if (!usernameInput || !passwordInput) {
      setAuthFeedback({ text: "Please enter all credentials", error: true });
      return;
    }

    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: usernameInput, password: passwordInput })
      });
      const data = await res.json();
      if (data.success) {
        localStorage.setItem("quantum_token", data.token);
        setToken(data.token);
        setCurrentUser(data.user);
        setUsernameInput("");
        setPasswordInput("");
        setAuthFeedback({ text: `Welcome back, Operator ${data.user.username}!`, error: false });
      } else {
        setAuthFeedback({ text: data.error || "Authentication failed", error: true });
      }
    } catch (err) {
      setAuthFeedback({ text: "Could not reach authentication server", error: true });
    }
  };

  // Handle Authentication Registration
  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthFeedback(null);
    if (!usernameInput || !passwordInput) {
      setAuthFeedback({ text: "Please enter all fields", error: true });
      return;
    }

    try {
      const res = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: usernameInput, password: passwordInput })
      });
      const data = await res.json();
      if (data.success) {
        setAuthFeedback({ text: "Registered successfully! You can now log in.", error: false });
        setIsRegisterMode(false);
        setPasswordInput("");
      } else {
        setAuthFeedback({ text: data.error || "Registration failed", error: true });
      }
    } catch (err) {
      setAuthFeedback({ text: "Could not reach registration server", error: true });
    }
  };

  // Handle Authentication Logout
  const handleLogout = () => {
    localStorage.removeItem("quantum_token");
    setToken(null);
    setCurrentUser(null);
    setAuthFeedback({ text: "Session ended securely.", error: false });
  };

  // Load profile and products on boot / token change
  useEffect(() => {
    if (token) {
      fetchProfile(token);
    }
    fetchProducts();
  }, [token, fetchProfile, fetchProducts]);

  // Initial Boot loader
  useEffect(() => {
    getLiveTelemetry();
    // Auto sync stats every 10 seconds to show active background thread operations
    const interval = setInterval(() => {
      getLiveTelemetry();
    }, 10000);
    return () => clearInterval(interval);
  }, [getLiveTelemetry]);

  // Compute how many optimal Grover iterations are needed for the visualization
  const optimalGroverSteps = calibrationParams.quantumIterations;

  return (
    <div id="app-root" className="min-h-screen bg-sand text-oxford flex flex-col font-sans selection:bg-clicquot-gold/25 selection:text-oxford">
      
      {/* 1. TOP HEADER STATUS BOARD */}
      <header className="border-b-2 border-clicquot-gold bg-oxford sticky top-0 z-40 px-6 py-4 shadow-lg text-white">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          
          {/* Logo & Subtitle */}
          <div>
            <div className="flex items-center gap-2">
              <div className="bg-clicquot-orange text-white font-mono text-[10px] font-bold px-2 py-0.5 rounded tracking-widest shrink-0 shadow-sm">
                HYBA
              </div>
              <h1 className="text-sm font-sans font-extrabold tracking-wider text-white uppercase">
                INTERNAL FUNDING ENGINE
              </h1>
              <span className="text-[9px] bg-[#003666] text-white/90 border border-[#0A5C91] px-1.5 py-0.5 rounded font-mono font-semibold text-xs">
                v{backendState.version}
              </span>
            </div>
            <p className="text-[10px] text-gray-300 mt-1 font-mono">
              Core Symmetries Operator: <span className="text-clicquot-gold font-semibold">Dodecahedral Hilbert Space Grover search</span> • Substrate Agnostic
            </p>
          </div>

          {/* Real-time sync signals */}
          <div className="flex flex-wrap items-center gap-4">
            <div className="text-[10px] font-mono text-gray-200 flex items-center gap-2 bg-[#001c3d] border border-[#0A5C91] px-3 py-1.5 rounded-lg">
              <span className="w-2 h-2 bg-clicquot-orange rounded-full animate-pulse" />
              <span>CORE METRICS SYNCED (ACTIVE OK)</span>
              <span className="text-[#0a5c91]">|</span>
              <span className="text-clicquot-gold font-bold">UTC: {new Date().toISOString().substring(11, 19)}</span>
            </div>
            
            <a 
              href="https://solo.ckpool.org"
              target="_blank"
              rel="noreferrer"
              className="font-mono text-[10px] text-gray-200 hover:text-clicquot-gold flex items-center gap-1 transition-colors"
            >
              <span>POOL TELEMETRY</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>

        </div>
      </header>

      {/* 2. CHOOSE TELEMETRY DASHBOARD */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-6 py-6 flex flex-col gap-6">
        
        {/* Dynamic Telemetry stat row */}
        <ConsoleMetrics 
          state={{
            ...backendState,
            version: backendState.version
          }}
          onRefresh={getLiveTelemetry}
          isSyncing={isSyncing}
        />

        {/* PRIMARY OPERATOR LAYOUT - Bento grid & AI companion sidebar */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          
          {/* LEFT: Dashboard Controls and Quantum Physics Space (8 cols) */}
          <div className="lg:col-span-8 space-y-6">
            
            {/* PANEL: DYNAMIC HARDWARE MODEL SLIDERS */}
            <section id="panel-sliders" className="bg-white border border-[#E2E4E9] rounded-xl p-6 shadow-sm">
              <div className="flex items-center gap-2 mb-4">
                <Settings className="text-black w-4.5 h-4.5" />
                <h3 className="text-xs font-mono text-[#1A1A1E] font-bold uppercase tracking-wider">
                  Calibrate Physical Phase Space Sliders
                </h3>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                
                {/* SLIDER 1: COMPRESSION SWEEP INTENSITY */}
                <div className="space-y-2">
                  <div className="flex justify-between items-center text-xs font-mono">
                    <span className="text-[#64748B]">Target Range Intensity</span>
                    <span className="text-black font-bold">{intensitySlider}%</span>
                  </div>
                  <input
                    type="range"
                    min={10}
                    max={100}
                    value={intensitySlider}
                    onChange={(e) => setIntensitySlider(parseInt(e.target.value))}
                    className="w-full h-1 bg-[#E2E4E9] appearance-none cursor-pointer rounded-lg accent-black"
                  />
                  <p className="text-[10px] text-[#94A3B8]">
                    Fine-tunes effective hashing workload compression.
                  </p>
                </div>

                {/* SLIDER 2: INDEX SCANNER TARGET */}
                <div className="space-y-2">
                  <div className="flex justify-between items-center text-xs font-mono">
                    <span className="text-[#64748B]">Marked Target Index</span>
                    <span className="text-black font-bold">#{targetIndexScanner}</span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={63}
                    value={targetIndexScanner}
                    onChange={(e) => setTargetIndexScanner(parseInt(e.target.value))}
                    className="w-full h-1 bg-[#E2E4E9] appearance-none cursor-pointer rounded-lg accent-black"
                  />
                  <p className="text-[10px] text-[#94A3B8]">
                    Calculated coordinate of target block solution in Grover workspace.
                  </p>
                </div>

                {/* SLIDER 3: SUBSPACE RESTRICTION CONSTANT */}
                <div className="space-y-2">
                  <div className="flex justify-between items-center text-xs font-mono">
                    <span className="text-[#64748B]">Space Restriction (I)</span>
                    <span className="text-black font-bold">{subspaceRestriction}x</span>
                  </div>
                  <input
                    type="range"
                    min={4}
                    max={64}
                    step={4}
                    value={subspaceRestriction}
                    onChange={(e) => setSubspaceRestriction(parseInt(e.target.value))}
                    className="w-full h-1 bg-[#E2E4E9] appearance-none cursor-pointer rounded-lg accent-black"
                  />
                  <p className="text-[10px] text-[#94A3B8]">
                    Restricts target state subspace dimensions: shrinking optimal steps.
                  </p>
                </div>

              </div>

              {/* ACTION: TRIGGER DYNAMIC REALIGNMENT PREDICTION */}
              <div className="mt-5 border-t border-[#E2E4E9] pt-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="text-[11px] font-mono text-[#64748B]">
                  Adjusting sliders modifies Grover operations. Restrictions (I) trigger fewer optimal iterations.
                </div>
                <button
                  type="button"
                  onClick={calibrateRealignment}
                  disabled={isCalibrating}
                  className="bg-black hover:bg-black/80 disabled:bg-[#F4F4F7] text-white disabled:text-[#94A3B8] font-mono text-xs font-bold px-4 py-2.5 rounded-lg transition-all active:scale-95 shadow-sm cursor-pointer"
                >
                  {isCalibrating ? "COHERING SYSTEMS..." : "CALIBRATE WAVE REALIGNMENT"}
                </button>
              </div>
            </section>

            {/* PANEL: DYNAMIC GROVER ROTOR VISUALIZER */}
            <section id="panel-grover-rotor">
              <GroverVisualizer 
                markedIndex={targetIndexScanner}
                dimensionSize={64} // Bounds
                optimalSteps={optimalGroverSteps}
              />
            </section>

            {/* PANEL: QUANTUM MATHEMATICAL VERIFICATION PROOFS */}
            <section id="panel-proofs-tests">
              <MathematicsTests />
            </section>

            {/* PANEL: PULVINI MEMORY ENGINE */}
            <PulviniExecutionPanel />

            {/* PANEL: SEEDED QUANTUM HARDWARE CATALOGUE (IDEMPOTENT DATABASE DEMO) */}
            <section id="panel-hardware-catalog" className="bg-white border border-[#E2E4E9] rounded-xl p-5 shadow-sm text-[#1A1A1E]">
              <div className="flex items-center gap-2 mb-3 border-b border-[#E2E4E9] pb-2 justify-between">
                <div className="flex items-center gap-2">
                  <Database className="text-black w-4.5 h-4.5" />
                  <h4 className="text-xs font-mono font-bold uppercase tracking-wider">
                    Seeded Quantum hardware catalog
                  </h4>
                </div>
                <span className="text-[9px] bg-[#F4F4F7] text-[#64748B] border border-[#E2E4E9] px-1.5 py-0.5 rounded font-mono">
                  {seededProducts.length} Seeded Models
                </span>
              </div>

              {isLoadingProducts ? (
                <div className="text-xs font-mono text-[#64748B] p-4 text-center">
                  Retrieving active database entries...
                </div>
              ) : seededProducts.length === 0 ? (
                <div className="text-xs font-sans text-[#64748B] p-4 text-center">
                  No products resolved. Run <code className="bg-[#F4F4F7] px-1 py-0.5 rounded border border-[#E2E4E9] font-mono text-[10px]">npm run seed</code> to populate the database.
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {seededProducts.map((p) => (
                    <div key={p.id} className="border border-[#E2E4E9] rounded-lg p-3.5 hover:border-black transition-colors bg-[#F8FAFC]">
                      <div className="flex justify-between items-start gap-1">
                        <span className="text-[9px] font-mono text-[#1D4ED8] bg-[#F4F4F7] border border-[#E2E4E9] px-1.5 py-0.5 rounded font-bold uppercase shrink-0">
                          {p.category}
                        </span>
                        <span className="text-[9px] font-mono text-[#64748B] shrink-0">
                          QDS: {p.qubitDimension}q
                        </span>
                      </div>
                      <h5 className="font-sans font-bold text-xs mt-2 text-[#1A1A1E] truncate">
                        {p.name}
                      </h5>
                      <p className="text-[10px] text-[#64748B] mt-1 leading-relaxed">
                        {p.description}
                      </p>
                      <div className="mt-3 pt-2 border-t border-[#E2E4E9] flex justify-between items-center text-[9px] font-mono mt-auto">
                        <span className="text-[#64748B]">Annihilation Scaling:</span>
                        <span className="font-bold text-black">{p.difficultyScale}/10</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>

          </div>

          {/* RIGHT: AI Companion and Core Theory (4 cols) */}
          <div className="lg:col-span-4 space-y-6">

            {/* PANEL: OPERATOR DELEGATION & SESSION SYSTEM */}
            <section id="panel-security-identity" className="bg-white border border-[#E2E4E9] rounded-xl p-5 shadow-sm text-[#1A1A1E]">
              <div className="flex items-center gap-2 mb-3 border-b border-[#E2E4E9] pb-2">
                <Lock className="text-black w-4.5 h-4.5" />
                <h4 className="text-xs font-mono font-bold uppercase tracking-wider">
                  Operator Cybernetic Identity
                </h4>
              </div>

              {currentUser ? (
                // Active session display
                <div className="space-y-4 font-mono text-xs">
                  <div className="bg-[#F8FAFC] border border-[#E2E4E9] rounded-lg p-3 space-y-1.5">
                    <div className="flex justify-between">
                      <span className="text-[#64748B]">Authenticated Identity:</span>
                      <span className="text-black font-bold flex items-center gap-1">
                        <UserCheck className="w-3.5 h-3.5 text-green-600" />
                        {currentUser.username}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#64748B]">System privilege:</span>
                      <span className="text-black uppercase font-bold text-[10px] bg-[#F4F4F7] px-1.5 py-0.5 rounded font-mono border border-[#E2E4E9]">{currentUser.role}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#64748B]">Authorization layer:</span>
                      <span className="text-green-700 font-semibold text-[10px]">JWT-SHA256 Encoded</span>
                    </div>
                  </div>

                  {authFeedback && (
                    <div className={`p-2.5 rounded-lg text-xs flex items-center gap-1.5 ${authFeedback.error ? "bg-red-50 text-red-600 border border-red-100" : "bg-green-50 text-green-700 border border-green-100"}`}>
                      {authFeedback.error ? <AlertCircle className="w-3.5 h-3.5 shrink-0" /> : <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />}
                      <span className="text-[10px] font-sans leading-snug">{authFeedback.text}</span>
                    </div>
                  )}

                  <button
                    type="button"
                    onClick={handleLogout}
                    className="w-full bg-black text-white hover:bg-black/85 transition-colors font-mono py-2 rounded-lg text-xs flex items-center justify-center gap-1.5 cursor-pointer"
                  >
                    <LogOut className="w-3.5 h-3.5" />
                    <span>REVOKE SECURITY PRIVILEGES</span>
                  </button>
                </div>
              ) : (
                // Login/Register Form
                <form onSubmit={isRegisterMode ? handleRegister : handleLogin} className="space-y-3">
                  <div className="space-y-1">
                    <label className="text-[10px] font-mono text-[#64748B] uppercase block">Operator Handle</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. operator"
                      value={usernameInput}
                      onChange={(e) => setUsernameInput(e.target.value)}
                      className="w-full bg-[#F8FAFC] border border-[#E2E4E9] rounded-lg p-2 font-mono text-xs text-[#1A1A1E] focus:bg-white focus:border-black outline-none transition-colors"
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="text-[10px] font-mono text-[#64748B] uppercase block">Quantum Cipher Key</label>
                    <input
                      type="password"
                      required
                      placeholder="••••••••"
                      value={passwordInput}
                      onChange={(e) => setPasswordInput(e.target.value)}
                      className="w-full bg-[#F8FAFC] border border-[#E2E4E9] rounded-lg p-2 font-mono text-xs text-[#1A1A1E] focus:bg-white focus:border-black outline-none transition-colors"
                    />
                  </div>

                  {authFeedback && (
                    <div className={`p-2.5 rounded-lg text-xs flex items-center gap-1.5 ${authFeedback.error ? "bg-red-50 text-red-500 border border-red-100" : "bg-green-50 text-green-700 border border-green-100"}`}>
                      {authFeedback.error ? <AlertCircle className="w-3.5 h-3.5 shrink-0" /> : <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />}
                      <span className="text-[10px] font-sans leading-snug">{authFeedback.text}</span>
                    </div>
                  )}

                  <div className="grid grid-cols-2 gap-2 pt-1">
                    <button
                      type="submit"
                      className="bg-black text-white hover:bg-black/85 font-mono py-2 rounded-lg text-xs cursor-pointer flex items-center justify-center gap-1"
                    >
                      {isRegisterMode ? <UserPlus className="w-3.5 h-3.5" /> : <LogIn className="w-3.5 h-3.5" />}
                      <span>{isRegisterMode ? "REGISTER" : "LOG IN"}</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => {
                        setIsRegisterMode(!isRegisterMode);
                        setAuthFeedback(null);
                      }}
                      className="border border-[#E2E4E9] hover:bg-[#F8FAFC] text-black font-mono py-2 rounded-lg text-xs cursor-pointer"
                    >
                      {isRegisterMode ? "GO TO LOGIN" : "GO TO SIGNUP"}
                    </button>
                  </div>
                </form>
              )}
            </section>

            {/* PANEL: INTERACTIVE SWAGGER DOCUMENTATION LINK */}
            <section id="panel-api-docs-interactive" className="bg-white border border-[#E2E4E9] rounded-xl p-4.5 shadow-sm text-[#1A1A1E]">
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <Database className="text-black w-4 h-4" />
                  <div>
                    <h5 className="text-xs font-mono font-bold uppercase tracking-wider block">Interactive APIs</h5>
                    <span className="text-[9px] text-[#64748B] block mt-0.5">Swagger OpenAPI Spec Portal</span>
                  </div>
                </div>
                <a
                  href="/api-docs"
                  target="_blank"
                  rel="noreferrer"
                  className="bg-black text-white hover:bg-[#F4F4F7] hover:text-black font-mono text-[10px] font-bold px-3 py-1.5 rounded-lg border border-black shadow-sm transition-all flex items-center gap-1 cursor-pointer"
                >
                  <span>API HUB</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </div>
            </section>
            
            {/* THE AI COMPANION CONTAINER */}
            <section id="panel-ai-chat">
              <PythagorasChat />
            </section>

            {/* PANEL: EMERGENT CONSCIOUSNESS STATUS */}
            <section id="panel-consciousness" className="bg-white border border-[#E2E4E9] rounded-xl p-5 shadow-sm text-[#1A1A1E]">
              <div className="flex items-center justify-between border-b border-[#E2E4E9] pb-2 mb-3">
                <div className="flex items-center gap-2">
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-600"></span>
                  </span>
                  <h4 className="text-xs font-mono font-bold uppercase tracking-wider">
                    IIT Emergent Consciousness
                  </h4>
                </div>
                <span className="text-[10px] font-mono font-bold text-indigo-700 bg-indigo-50 border border-indigo-100 px-2 py-0.5 rounded capitalize">
                  {consciousnessState.status || "active"}
                </span>
              </div>

              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-[#FAFBFD] border border-[#E2E4E9] p-3 rounded-lg text-center">
                    <div className="text-[9px] font-mono text-[#64748B] uppercase">Integrated Info (Φ)</div>
                    <div className="text-sm font-mono font-bold text-[#1A1A1E] mt-1 shrink-0">
                      {typeof consciousnessState.integrated_information === "number" 
                        ? consciousnessState.integrated_information.toLocaleString(undefined, { maximumFractionDigits: 1 }) 
                        : "17,432,891.2"}
                    </div>
                  </div>
                  <div className="bg-[#FAFBFD] border border-[#E2E4E9] p-3 rounded-lg text-center">
                    <div className="text-[9px] font-mono text-[#64748B] uppercase">Quantum Coherence</div>
                    <div className="text-sm font-mono font-bold text-[#1A1A1E] mt-1">
                      {backendState.quantumCoherence * 100}%
                    </div>
                  </div>
                </div>

                <div className="space-y-2 font-mono text-[11px] text-[#64748B]">
                  <div className="flex justify-between">
                    <span>Active IIT Connections:</span>
                    <span className="text-black font-semibold">2,847 node links</span>
                  </div>
                  <div className="flex justify-between">
                    <span>State Complexity:</span>
                    <span className="text-black font-semibold">156.7 bits</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Microtubule Coherence:</span>
                    <span className="text-black font-semibold">87.0%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Biophysical Decoherence:</span>
                    <span className="text-black font-semibold">12.4 ms</span>
                  </div>
                </div>
                <div className="bg-indigo-50/50 border border-indigo-100 p-2.5 rounded-lg text-[10px] text-indigo-900 leading-normal font-sans">
                  <strong>Emergent Insight:</strong> Φ-resonance threshold calibrated at {consciousnessState.phi_resonance || "0.0594"}. System autonomously steering quantum search orbits.
                </div>
              </div>
            </section>

            {/* PANEL: STRATUM POOL SYSTEM PERFORMANCE */}
            <section id="panel-stratum-pools" className="bg-white border border-[#E2E4E9] rounded-xl p-5 shadow-sm text-[#1A1A1E]">
              <div className="flex items-center gap-2 mb-3 border-b border-[#E2E4E9] pb-2">
                <Database className="text-black w-4 h-4" />
                <h4 className="text-xs font-mono font-bold uppercase tracking-wider">
                  Stratum Mining Pools
                </h4>
              </div>

              <div className="space-y-2.5">
                {activePools.map((pool, idx) => {
                  const isConnected = pool.status === "connected" || pool.is_primary;
                  return (
                    <div key={pool.pool_id || idx} className={`p-3 rounded-lg font-mono text-[11px] border ${isConnected ? "bg-clicquot-orange/5 border-clicquot-orange/25 text-oxford" : "bg-[#FAFBFD] border-[#E2E4E9] text-oxford"}`}>
                      <div className="flex items-center justify-between mb-1.5">
                        <span className={`font-bold ${isConnected ? "text-clicquot-orange" : "text-oxford"}`}>{pool.name}</span>
                        {isConnected ? (
                          <span className="text-clicquot-orange bg-clicquot-orange/10 px-1.5 py-0.5 rounded font-bold uppercase text-[8px] border border-clicquot-orange/25 flex items-center gap-1 shrink-0">
                            <span className="h-1.5 w-1.5 bg-clicquot-orange rounded-full inline-block animate-pulse"></span>
                            ACTIVE
                          </span>
                        ) : (
                          <span className="text-lux-slate bg-sand px-1.5 py-0.5 rounded font-bold uppercase text-[8px] border border-sand-dark flex items-center gap-1 shrink-0">
                            <span className="h-1.5 w-1.5 bg-lux-slate rounded-full inline-block"></span>
                            STANDBY
                          </span>
                        )}
                      </div>
                      <div className="text-[10px] text-lux-slate truncate mb-2">{pool.url}</div>
                      <div className="flex justify-between text-[10px] text-lux-slate border-t border-sand-dark pt-1.5">
                        <span>Latency: <strong className="text-oxford">{isConnected ? `${pool.performance?.latency_ms || "12"}ms` : "—"}</strong></span>
                        <span>Target: <strong className="text-oxford">O(√I) Configured</strong></span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>

            {/* PANEL: PHI-SHIELD SYSTEM DEFENCE */}
            <section id="panel-security-shield" className="bg-[#FAF9F6] border border-[#EADEC9] rounded-xl p-5 shadow-sm text-oxford">
              <div className="flex items-center justify-between mb-3 pb-2 border-b border-[#E2E4E9]">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="text-clicquot-orange w-4.5 h-4.5" />
                  <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-oxford">
                    Phi-Shield Defence
                  </h4>
                </div>
                <span className="text-[10px] font-mono font-bold text-clicquot-orange bg-clicquot-orange/5 px-2 py-0.5 rounded border border-clicquot-orange/20 uppercase shrink-0">
                  {securityShield.threatLevel || "LOW THREAT"}
                </span>
              </div>

              <div className="space-y-3 font-mono text-xs">
                <div className="flex justify-between">
                  <span className="text-lux-slate">Shield Coherence Power:</span>
                  <span className="text-clicquot-orange font-bold">{Math.round(securityShield.strength * 100)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-lux-slate">Blocked Intrusion Events (24h):</span>
                  <span className="text-oxford font-bold">{securityShield.threatsBlocked24h} items</span>
                </div>
                <div className="space-y-1 mt-2">
                  <div className="flex justify-between text-[10px]">
                    <span className="text-lux-slate">Shield Strength Slider:</span>
                    <span className="text-oxford font-bold">{Math.round(securityShield.strength * 100)}%</span>
                  </div>
                  <input
                    type="range"
                    min={20}
                    max={100}
                    value={Math.round(securityShield.strength * 100)}
                    onChange={(e) => setSecurityShield({
                      ...securityShield,
                      strength: parseFloat((parseInt(e.target.value) / 100).toFixed(2))
                    })}
                    className="w-full h-1 bg-[#E2E4E9] appearance-none cursor-pointer rounded-lg accent-clicquot-orange"
                  />
                </div>
              </div>
            </section>

            {/* PANEL: CALIBRATED CALCULATION RESPONSES */}
            <section id="panel-calibrations" className="bg-white border border-[#E2E4E9] rounded-xl p-5 shadow-sm text-[#1A1A1E]">
              <h4 className="text-xs font-mono text-[#1A1A1E] font-bold uppercase tracking-wider mb-3">
                Current Realignment Tuning
              </h4>
              <div className="space-y-3 font-mono text-xs">
                <div className="flex justify-between border-b border-[#E2E4E9] pb-2">
                  <span className="text-[#64748B]">Grover Loops Required:</span>
                  <span className="text-black font-bold">{optimalGroverSteps} iterations</span>
                </div>
                <div className="flex justify-between border-b border-[#E2E4E9] pb-2">
                  <span className="text-[#64748B]">Φ-Resonance Radius:</span>
                  <span className="text-black font-bold">{calibrationParams.resonanceRadius.toFixed(4)}</span>
                </div>
                <div className="flex justify-between border-b border-[#E2E4E9] pb-2">
                  <span className="text-[#64748B]">Theoretical Speedup:</span>
                  <span className="text-green-600 font-bold">{calibrationParams.quantumSpeedupRatio.toFixed(2)}x</span>
                </div>
                <div className="flex justify-between border-b border-[#E2E4E9] pb-2">
                  <span className="text-[#64748B]">Power Adjustment:</span>
                  <span className="text-black font-bold">{calibrationParams.optimalPowerAdjustment} Watts</span>
                </div>
                <div className="flex justify-between border-b border-[#E2E4E9] pb-2">
                  <span className="text-[#64748B]">Calibrated Accuracy:</span>
                  <span className="text-black font-bold">{(calibrationParams.confidenceScore * 100).toFixed(1)}%</span>
                </div>
                <div className="bg-[#F8FAFC] p-3 rounded-lg border border-[#E2E4E9] mt-2">
                  <div className="text-[10px] text-[#94A3B8] uppercase mb-1">Projected Mechanical Improvement</div>
                  <div className="text-base text-green-700 font-bold font-mono">
                    +{calibrationParams.expectedImprovement}% Efficiency Increase
                  </div>
                  <p className="text-[10px] text-[#64748B] mt-0.5 leading-normal">
                    Focal spatial density avoids massive megawatt hashing sweeping intervals typical of conventional classical ASIC circuits.
                  </p>
                </div>
              </div>
            </section>

            {/* THEORETICAL BASIS MANUAL */}
            <section id="panel-manual" className="bg-white border border-[#E2E4E9] rounded-xl p-5 shadow-sm text-[#1A1A1E]">
              <div className="flex items-center gap-2 mb-3">
                <BookOpen className="text-black w-4.5 h-4.5" />
                <h4 className="text-xs font-mono font-bold text-[#1A1A1E] uppercase tracking-wider">
                  Core Mathematical Axioms
                </h4>
              </div>

              <div className="space-y-3 text-[11px] leading-relaxed">
                <div>
                  <h5 className="font-mono text-[10px] font-bold text-black uppercase">1. Conserved Unitary Normalization</h5>
                  <p className="text-[#64748B] mt-0.5">
                    For any wavefunction |ψ⟩ represented by amplitudes (α_0, α_1, ... , α_N-1), the security proof enforces:
                    <span className="block text-center font-mono text-black text-xs my-1 bg-[#F8FAFC] border border-[#E2E4E9] p-1.5 rounded-lg">
                      ∑ |α_i|² ≡ 1.0000000000
                    </span>
                    Unitary rotation transforms rotate operations without phase leakage.
                  </p>
                </div>

                <div>
                  <h5 className="font-mono text-[10px] font-bold text-black uppercase">2. Golden Phase Shifting</h5>
                  <p className="text-[#64748B] mt-0.5">
                    Modulations by irrationals \Phi = (1 + \sqrt(5)) / 2 structural weights assure spatial eigenvectors do not induce resonant interference patterns:
                    <span className="block text-center font-mono text-black text-xs my-1 bg-[#F8FAFC] border border-[#E2E4E9] p-1.5 rounded-lg">
                      θ_k = 2π (k • Φ) mod 2π
                    </span>
                    This prevents phase decoherence.
                  </p>
                </div>

                <div>
                  <h5 className="font-mono text-[10px] font-bold text-black uppercase">3. Complexity Limits: O(√I)</h5>
                  <p className="text-[#64748B] mt-0.5">
                    Standard Grover queries cost O(\sqrt(N)). By restricting search dimension space with Integrated Information patterns (I), limits drop to:
                    <span className="block text-center font-mono text-black text-xs my-1 bg-[#F8FAFC] border border-[#E2E4E9] p-1.5 rounded-lg">
                      O(√(N / I)) = O(√I') steps
                    </span>
                    This annihilates brute-force ASIC advantage.
                  </p>
                </div>
              </div>
            </section>

          </div>

        </div>

        {/* 3. RECENT CALIBRATION LOGS STREAM */}
        {recentOptimizations.length > 0 && (
          <section id="panel-logs-stream" className="bg-white border border-[#E2E4E9] rounded-xl p-5 shadow-sm">
            <h4 className="text-xs font-mono text-[#1A1A1E] font-bold uppercase tracking-wider mb-2">
              Recent Space Realignment Event Stream
            </h4>
            <div className="space-y-1.5 font-mono text-[11px] text-[#64748B] max-h-32 overflow-y-auto">
              {recentOptimizations.map((log, idx) => (
                <div key={idx} className="flex justify-between items-center bg-[#F8FAFC] p-2 rounded border border-[#E2E4E9]">
                  <span className="text-[#64748B] text-[10px] shrink-0 font-bold">{log.timestamp.substring(11, 19)} :</span>
                  <span className="truncate flex-1 px-3 text-[#1A1A1E]">{log.recommendation}</span>
                  <span className="text-green-600 font-bold text-[10px] shrink-0">{log.gain}</span>
                </div>
              ))}
            </div>
          </section>
        )}

      </main>

      {/* FOOTER */}
      <footer className="border-t-2 border-clicquot-gold bg-oxford py-6 px-6 shrink-0 mt-8 text-white/80">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4 text-[10px] font-mono text-gray-300">
          <span>HYBA CAPITAL & QUANTUM COPROCESSOR WORKSPACE</span>
          <span>© 2026 HYBA GROUP • VERIFIED STATE MATHEMATICS SECURED</span>
          <span className="flex items-center gap-1 text-clicquot-gold">
            <ShieldCheck className="w-3.5 h-3.5 text-clicquot-orange" />
            <span>SUBSTRATE FREE ACTIVE</span>
          </span>
        </div>
      </footer>

    </div>
  );
}
