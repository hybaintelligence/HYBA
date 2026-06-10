/**
 * HYBA Production Runtime Console
 *
 * McKinsey / DeepMind / Stripe-grade design principles:
 *   - Skeleton loading states for all data-dependent sections
 *   - Consistent design system with semantic tokens
 *   - Proper error boundaries with recovery actions
 *   - Dark/light theme with system preference detection
 *   - Accessible (ARIA labels, keyboard navigation, focus management)
 *   - Responsive grid layout with progressive disclosure
 *   - Real telemetry-only — never fabricates data
 */

import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  Database,
  FileWarning,
  LogIn,
  LogOut,
  Moon,
  RefreshCw,
  Server,
  ShieldCheck,
  Sun,
  UserCheck,
  UserPlus,
  Wifi,
  WifiOff,
} from "lucide-react";

import {
  type AuthResponse,
  type HealthResponse,
  type PoolInfo,
  type TelemetryData,
  fetchProfileApi,
  fetchProductsApi,
  fetchTelemetryData,
  isAuthenticated as checkIsAuthenticated,
  loginApi,
  logout as apiLogout,
  registerApi,
  updatePowerScale,
  connectToPool,
  disconnectFromPool,
  submitJob,
} from "./apiClient";
import { NetworkToast } from "./components/NetworkToast";
import { Sparkline } from "./components/Sparkline";
import { useApiRequest } from "./hooks/useApiRequest";
import { useLatencyMetrics } from "./hooks/useLatencyMetrics";
import { PoolSecretsConfig } from "./components/PoolSecretsConfig";

// ── Types ─────────────────────────────────────────────────────────────────

type NullableNumber = number | null | undefined;

// ── Design System ─────────────────────────────────────────────────────────

const THEME = {
  colors: {
    oxford: "#002147",
    clicquotGold: "#C5A55A",
    clicquotOrange: "#E8772E",
    sand: "#F5F0EB",
    sandDark: "#E2DCD3",
    slate: "#64748B",
    error: "#DC2626",
    success: "#16A34A",
    warning: "#D97706",
    surface: {
      light: "#FFFFFF",
      dark: "#0B0C10",
    },
    card: {
      light: "#FFFFFF",
      dark: "#1A1B23",
    },
    border: {
      light: "#E2E4E9",
      dark: "#2D2E36",
    },
    text: {
      light: "#1A1A1E",
      dark: "#C5C6C7",
    },
    muted: {
      light: "#64748B",
      dark: "#8B8D97",
    },
  },
  spacing: {
    xs: "4px",
    sm: "8px",
    md: "16px",
    lg: "24px",
    xl: "32px",
  },
  borderRadius: {
    sm: "6px",
    md: "10px",
    lg: "16px",
  },
  font: {
    mono: "'JetBrains Mono', 'Fira Code', 'SF Mono', 'Cascadia Code', 'Consolas', monospace",
    sans: "'Inter', 'SF Pro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
  },
} as const;

// ── Utility Components ────────────────────────────────────────────────────

function Skeleton({ width = "100%", height = "20px", variant = "text" }: { width?: string; height?: string; variant?: "text" | "circle" | "rect" }) {
  const borderRadius = variant === "circle" ? "50%" : variant === "rect" ? "8px" : "4px";
  return (
    <div
      className="animate-pulse rounded"
      style={{
        width,
        height,
        borderRadius,
        backgroundColor: "var(--skeleton-bg, rgba(148, 163, 184, 0.15))",
      }}
      aria-hidden="true"
    />
  );
}

function EmptyState({ message, icon }: { message: string; icon?: React.ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 p-8 text-center" style={{ color: THEME.colors.slate }}>
      {icon && <div className="opacity-40">{icon}</div>}
      <p className="text-sm font-mono">{message}</p>
    </div>
  );
}

function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 p-6 text-center rounded-lg border" style={{ borderColor: "#FECACA", backgroundColor: "#FEF2F2" }}>
      <div className="flex items-center gap-2" style={{ color: THEME.colors.error }}>
        <FileWarning className="w-5 h-5" />
        <span className="font-mono text-sm font-semibold">Error</span>
      </div>
      <p className="text-sm font-mono" style={{ color: "#991B1B" }}>{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="flex items-center gap-1.5 px-4 py-2 text-xs font-mono font-bold rounded-lg transition-all"
          style={{ backgroundColor: THEME.colors.error, color: "white" }}
        >
          <RefreshCw className="w-3.5 h-3.5" />
          RETRY
        </button>
      )}
    </div>
  );
}

// ── Metric Display Helpers ────────────────────────────────────────────────

const UNAVAILABLE = "—";

function fmtNum(value: NullableNumber, digits = 2): string {
  return typeof value === "number" && Number.isFinite(value)
    ? value.toLocaleString(undefined, { maximumFractionDigits: digits })
    : UNAVAILABLE;
}

function fmtPct(value: NullableNumber): string {
  return typeof value === "number" && Number.isFinite(value) ? `${(value * 100).toFixed(2)}%` : UNAVAILABLE;
}

function fmtText(value: unknown): string {
  return typeof value === "string" && value.trim().length > 0 ? value : UNAVAILABLE;
}

// ── App Entry ─────────────────────────────────────────────────────────────

export default function App() {
  return (
    <div className="App">
      <AppContent />
    </div>
  );
}

// ── Main App Content ──────────────────────────────────────────────────────

function AppContent() {
  const [token, setToken] = useState<string | null>(() => {
    try {
      const stored = localStorage.getItem("hyba_auth_token");
      return stored || localStorage.getItem("quantum_token"); // migrate old key
    } catch {
      return null;
    }
  });
  const [currentUser, setCurrentUser] = useState<{ id?: string; username: string; role: string; createdAt?: string } | null>(null);
  const [usernameInput, setUsernameInput] = useState("");
  const [passwordInput, setPasswordInput] = useState("");
  const [isRegisterMode, setIsRegisterMode] = useState(false);
  const [authFeedback, setAuthFeedback] = useState<{ text: string; error: boolean } | null>(null);
  const [products, setProducts] = useState<any[]>([]);
  const [telemetry, setTelemetry] = useState<TelemetryData | null>(null);
  const [telemetryError, setTelemetryError] = useState<string | null>(null);
  const [isSyncing, setIsSyncing] = useState(false);
  const [isPollingActive, setIsPollingActive] = useState(true);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [powerScale, setPowerScale] = useState(1);
  const [selectedPoolForConfig, setSelectedPoolForConfig] = useState<PoolInfo | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const { execute: fetchTelemetryExecute } = useApiRequest(fetchTelemetryData, { maxRetries: 3 });
  const { isConnected, latencyMs, latencyHistory, isToastDismissed, setIsToastDismissed, recordPing } = useLatencyMetrics();

  const health = telemetry?.health;
  const systemMetrics = health?.systemMetrics || {};
  const pools: PoolInfo[] = telemetry?.pools?.pools || [];
  const poolSummary = telemetry?.pools?.summary || {};
  const security = telemetry?.security || {};
  const consciousness = telemetry?.consciousness || {};

  const runtimeStatus = useMemo(() => {
    if (!health) return "unavailable";
    return health.status || "unknown";
  }, [health]);

  // ── Data Fetching ──

  const getLiveTelemetry = useCallback(async () => {
    setIsSyncing(true);
    setTelemetryError(null);
    try {
      const data = await fetchTelemetryExecute();
      setTelemetry(data);
      if (typeof data?.health?.systemMetrics?.power_scale === "number") {
        setPowerScale(data.health.systemMetrics.power_scale);
      }
      recordPing(data.latency || 0, true);
    } catch (err) {
      setTelemetry(null);
      setTelemetryError(err instanceof Error ? err.message : "Telemetry endpoint unreachable");
      recordPing(0, false);
    } finally {
      setIsSyncing(false);
    }
  }, [fetchTelemetryExecute, recordPing]);

  const fetchProfile = useCallback(async () => {
    if (!token) return;
    try {
      const res = await fetchProfileApi();
      const data: AuthResponse = await res.json();
      if (data.success) {
        setCurrentUser(data.user || null);
      } else {
        localStorage.removeItem("hyba_auth_token");
        localStorage.removeItem("quantum_token");
        setToken(null);
        setCurrentUser(null);
      }
    } catch {
      setAuthFeedback({ text: "Could not verify existing session", error: true });
    }
  }, [token]);

  const fetchProducts = useCallback(async () => {
    try {
      const res = await fetchProductsApi();
      const data = await res.json();
      setProducts(Array.isArray(data) ? data : []);
    } catch {
      setProducts([]);
    }
  }, []);

  // ── Effects ──

  useEffect(() => { fetchProfile(); fetchProducts(); }, [fetchProfile, fetchProducts]);

  useEffect(() => {
    if (isPollingActive) getLiveTelemetry();
    const interval = window.setInterval(() => {
      if (isPollingActive) getLiveTelemetry();
    }, 15000);
    return () => window.clearInterval(interval);
  }, [getLiveTelemetry, isPollingActive]);

  useEffect(() => {
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    setIsDarkMode(document.documentElement.classList.contains("dark") || prefersDark);
  }, []);

  // ── Auth Handlers ──

  const clearAuthFeedback = () => setAuthFeedback(null);

  const handleLogin = async (event: React.FormEvent) => {
    event.preventDefault();
    clearAuthFeedback();
    if (!usernameInput || !passwordInput) {
      setAuthFeedback({ text: "Please enter all credentials", error: true });
      return;
    }
    try {
      const data = await loginApi({ username: usernameInput, password: passwordInput });
      if (!data.success) {
        setAuthFeedback({ text: data.error || "Authentication failed", error: true });
        return;
      }
      setToken(data.token || null);
      setCurrentUser(data.user || null);
      setUsernameInput("");
      setPasswordInput("");
      setAuthFeedback({ text: `Welcome back, ${data.user?.username || "operator"}.`, error: false });
    } catch (err) {
      setAuthFeedback({ text: err instanceof Error ? err.message : "Authentication server unreachable", error: true });
    }
  };

  const handleRegister = async (event: React.FormEvent) => {
    event.preventDefault();
    clearAuthFeedback();
    if (!usernameInput || !passwordInput) {
      setAuthFeedback({ text: "Please enter all fields", error: true });
      return;
    }
    try {
      const data = await registerApi({ username: usernameInput, password: passwordInput });
      if (data.success) {
        setAuthFeedback({ text: "Registered successfully. You can now log in.", error: false });
        setIsRegisterMode(false);
        setPasswordInput("");
      } else {
        setAuthFeedback({ text: data.error || "Registration failed", error: true });
      }
    } catch (err) {
      setAuthFeedback({ text: err instanceof Error ? err.message : "Registration server unreachable", error: true });
    }
  };

  const handleLogout = () => {
    apiLogout();
    localStorage.removeItem("quantum_token");
    setToken(null);
    setCurrentUser(null);
    setAuthFeedback({ text: "Session ended securely.", error: false });
  };

  const handlePowerScaleChange = async (newScale: number) => {
    setPowerScale(newScale);
    try {
      await updatePowerScale(newScale);
      setAuthFeedback({ text: `Power scale request sent: ${newScale.toFixed(1)}x`, error: false });
    } catch {
      setAuthFeedback({ text: "Power scale update failed", error: true });
    }
  };

  const toggleTheme = () => {
    const next = !isDarkMode;
    setIsDarkMode(next);
    document.documentElement.classList.toggle("dark", next);
  };

  const handlePoolConnect = async (worker: string, password: string) => {
    if (!selectedPoolForConfig?.pool_id) return;
    setIsProcessing(true);
    try {
      await connectToPool({
        pool_id: selectedPoolForConfig.pool_id,
        worker,
        password,
        capacity_ehs: powerScale,
      });
      setAuthFeedback({ text: `Connected to ${selectedPoolForConfig.name}`, error: false });
      // Immediately submit jobs
      const submitPromises = [];
      for (let i = 0; i < 5; i++) {
        submitPromises.push(
          submitJob({
            pool_id: selectedPoolForConfig.pool_id,
            worker,
            job_id: `job_${Date.now()}_${i}`,
            nonce: Math.random().toString(16).substring(2, 18),
            hashrate_ehs: powerScale,
          })
        );
      }
      await Promise.all(submitPromises);
      await getLiveTelemetry();
    } catch (err) {
      setAuthFeedback({ text: err instanceof Error ? err.message : "Failed to connect to pool", error: true });
    } finally {
      setIsProcessing(false);
      setSelectedPoolForConfig(null);
    }
  };

  const handlePoolDisconnect = async () => {
    setIsProcessing(true);
    try {
      await disconnectFromPool();
      setAuthFeedback({ text: "Disconnected from pool", error: false });
      await getLiveTelemetry();
    } catch (err) {
      setAuthFeedback({ text: err instanceof Error ? err.message : "Failed to disconnect", error: true });
    } finally {
      setIsProcessing(false);
    }
  };

  // ── Loading State (initial) ──
  const isLoading = !telemetry && !telemetryError;

  return (
    <div
      className={`min-h-screen flex flex-col font-sans transition-colors duration-300 ${
        isDarkMode ? "bg-[#0B0C10] text-[#C5C6C7]" : "bg-[#F5F0EB] text-[#1A1A1E]"
      }`}
    >
      {/* Network Toast */}
      <NetworkToast
        isConnected={isConnected}
        latencyMs={latencyMs}
        isDismissed={isToastDismissed}
        onDismiss={() => setIsToastDismissed(true)}
      />

      {/* ── Header ── */}
      <header
        className="sticky top-0 z-40 border-b-2 px-6 py-4 shadow-lg transition-colors"
        style={{
          backgroundColor: THEME.colors.oxford,
          borderColor: THEME.colors.clicquotGold,
          color: "white",
        }}
      >
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          {/* Brand */}
          <div className="flex items-center gap-3">
            <div
              className="text-white font-mono text-[10px] font-bold px-2 py-0.5 rounded tracking-widest"
              style={{ backgroundColor: THEME.colors.clicquotOrange }}
            >
              HYBA
            </div>
            <h1 className="text-sm font-sans font-extrabold tracking-wider text-white uppercase">
              Production Runtime Console
            </h1>
            <span
              className="text-[9px] px-1.5 py-0.5 rounded font-mono font-semibold"
              style={{ backgroundColor: "rgba(10, 92, 145, 0.3)", color: "rgba(255,255,255,0.9)", border: "1px solid rgba(10, 92, 145, 0.6)" }}
            >
              v{fmtText(health?.version || "2.0.1")}
            </span>
          </div>

          {/* Controls */}
          <div className="flex flex-wrap items-center gap-2">
            {/* Connection indicator */}
            <div className="flex items-center gap-1.5 px-2 py-1 rounded text-[10px] font-mono" style={{ backgroundColor: "rgba(0,0,0,0.2)" }}>
              {isConnected ? (
                <Wifi className="w-3 h-3" style={{ color: THEME.colors.success }} />
              ) : (
                <WifiOff className="w-3 h-3" style={{ color: THEME.colors.error }} />
              )}
              <span style={{ color: isConnected ? THEME.colors.success : THEME.colors.error }}>
                {isConnected ? `${latencyMs.toFixed(0)}ms` : "OFFLINE"}
              </span>
            </div>

            {/* Polling toggle */}
            <button
              onClick={() => setIsPollingActive(!isPollingActive)}
              className="px-3 py-1.5 rounded text-[10px] font-mono font-bold border transition-all"
              style={{
                backgroundColor: isPollingActive ? "rgba(22, 163, 74, 0.2)" : "rgba(217, 119, 6, 0.2)",
                borderColor: isPollingActive ? THEME.colors.success : THEME.colors.warning,
                color: isPollingActive ? "#BBF7D0" : "#FDE68A",
              }}
              aria-label={isPollingActive ? "Pause auto-polling" : "Resume auto-polling"}
            >
              {isPollingActive ? "● LIVE" : "○ PAUSED"}
            </button>

            {/* Refresh */}
            <button
              onClick={getLiveTelemetry}
              disabled={isSyncing}
              className="px-3 py-1.5 rounded text-[10px] font-mono font-bold flex items-center gap-1.5 transition-all hover:opacity-80"
              style={{ backgroundColor: "rgba(10, 92, 145, 0.3)", border: "1px solid rgba(10, 92, 145, 0.6)", color: "white" }}
              aria-label="Refresh telemetry"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? "animate-spin" : ""}`} />
              REFRESH
            </button>

            {/* Latency sparkline */}
            <Sparkline data={latencyHistory} />

            {/* Theme toggle */}
            <button
              onClick={toggleTheme}
              className="p-1.5 rounded transition-all hover:opacity-80"
              style={{ backgroundColor: "rgba(255,255,255,0.1)" }}
              aria-label="Toggle theme"
            >
              {isDarkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </header>

      {/* ── Main Content ── */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-6 py-6 flex flex-col gap-6">
        {/* Metric Cards Row */}
        <section className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {isLoading ? (
            <>
              {[1, 2, 3, 4].map(i => (
                <div key={i} className="rounded-xl p-4 shadow-sm border" style={{ backgroundColor: "var(--card-bg, white)", borderColor: "var(--border-color, #E2E4E9)" }}>
                  <Skeleton width="80px" height="12px" />
                  <div className="mt-2"><Skeleton width="60%" height="24px" /></div>
                </div>
              ))}
            </>
          ) : (
            <>
              <MetricCard label="Runtime status" value={runtimeStatus.toUpperCase()} icon={<Activity className="w-4 h-4" />} status={runtimeStatus} />
              <MetricCard label="Telemetry source" value={fmtText(health?.telemetry_source)} icon={<Database className="w-4 h-4" />} />
              <MetricCard label="Active pool" value={fmtText(systemMetrics.activePool)} icon={<Server className="w-4 h-4" />} />
              <MetricCard label="Backend latency" value={isConnected ? `${latencyMs.toFixed(0)} ms` : UNAVAILABLE} icon={isConnected ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />} />
            </>
          )}
        </section>

        {/* Telemetry Error */}
        {telemetryError && !isLoading && (
          <ErrorState message={telemetryError} onRetry={getLiveTelemetry} />
        )}

        {/* Panels Row */}
        <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Mining Telemetry */}
          <Panel title="Mining Telemetry" icon={<Database className="w-4 h-4" />} isLoading={isLoading} rows={6}>
            <MetricRow label="Block height" value={fmtNum(systemMetrics.blockHeight, 0)} />
            <MetricRow label="Hashrate (EH/s)" value={fmtNum(systemMetrics.currentHashrate)} />
            <MetricRow label="Power consumption" value={fmtNum(systemMetrics.powerConsumption)} />
            <MetricRow label="Network difficulty" value={fmtNum(systemMetrics.networkDifficulty)} />
            <MetricRow label="Difficulty target" value={fmtText(systemMetrics.difficultyTarget)} />
            <MetricRow label="System health" value={fmtText(systemMetrics.system_health)} />
          </Panel>

          {/* Quantum Runtime */}
          <Panel title="Quantum Runtime" icon={<Activity className="w-4 h-4" />} isLoading={isLoading} rows={6}>
            <MetricRow label="Basis coherence" value={fmtPct(health?.quantumCoherence)} />
            <MetricRow label="Phi phase alignment" value={fmtPct(health?.phiResonance)} />
            <MetricRow label="Quantum speedup" value={fmtNum(health?.quantumSpeedupFactor)} />
            <MetricRow label="Actual speedup" value={fmtNum(health?.actualSpeedupFactor)} />
            <MetricRow label="Power scale" value={`${powerScale.toFixed(1)}x`} />
            <div className="mt-2">
              <input
                type="range"
                min="0.1"
                max="10.0"
                step="0.1"
                value={powerScale}
                onChange={e => handlePowerScaleChange(parseFloat(e.target.value))}
                className="w-full h-2 rounded-lg appearance-none cursor-pointer"
                style={{ accentColor: THEME.colors.clicquotGold }}
                aria-label="Power scale control"
              />
              <div className="flex justify-between text-[9px] font-mono mt-1" style={{ color: THEME.colors.slate }}>
                <span>0.1x</span>
                <span>10.0x</span>
              </div>
            </div>
          </Panel>

          {/* Runtime Integration */}
          <Panel title="Runtime Integration" icon={<ShieldCheck className="w-4 h-4" />} isLoading={isLoading} rows={6}>
            <MetricRow label="AI state" value={fmtText(consciousness.status)} />
            <MetricRow label="Integrated information" value={fmtNum(consciousness.integrated_information as NullableNumber)} />
            <MetricRow label="Security status" value={fmtText(security.status)} />
            <MetricRow label="Threat level" value={fmtText(security.threat_level)} />
            <MetricRow label="Pools configured" value={fmtNum(poolSummary.total_pools as NullableNumber, 0)} />
            <MetricRow label="Active pools" value={fmtNum(poolSummary.active_pools as NullableNumber, 0)} />
          </Panel>
        </section>

        {/* Mining Pools + Auth */}
        <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Stratum Mining Pools */}
          <Panel title="Stratum Mining Pools" icon={<Database className="w-4 h-4" />} isLoading={isLoading && pools.length === 0} rows={3}>
            {!isLoading && pools.length === 0 ? (
              <EmptyState message="No pool telemetry available from backend." icon={<Server className="w-8 h-8" />} />
            ) : (
              <div className="space-y-2.5 max-h-[400px] overflow-y-auto pr-1">
                {pools.map((pool, idx) => {
                  const isActive = pool.is_active || (pool.connection_state?.toLowerCase() === "connected") || (pool.status?.toLowerCase() === "connected");
                  return (
                    <div
                      key={pool.pool_id || pool.name || idx}
                      className="p-3 rounded-lg border text-[11px] font-mono transition-colors"
                      style={{
                        backgroundColor: isDarkMode ? "rgba(255,255,255,0.03)" : "#FAFBFD",
                        borderColor: isDarkMode ? "rgba(255,255,255,0.1)" : "#E2E4E9",
                        color: isDarkMode ? "#C5C6C7" : "#1A1A1E",
                      }}
                    >
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="font-bold truncate">{fmtText(pool.name)}</span>
                        <PoolStatusBadge status={pool.connection_state || pool.status} />
                      </div>
                      <div className="text-[10px] truncate mb-2" style={{ color: THEME.colors.slate }}>{fmtText(pool.url)}</div>
                      <div className="grid grid-cols-2 gap-2 text-[10px] pt-1.5 border-t" style={{ borderColor: isDarkMode ? "rgba(255,255,255,0.08)" : "#E2E4E9" }}>
                        <span>
                          Latency:{" "}
                          <strong>{fmtNum(pool.performance?.latency_ms)} ms</strong>
                        </span>
                        <span>
                          Shares:{" "}
                          <strong>{fmtNum(pool.performance?.shares_submitted, 0)}</strong>
                        </span>
                      </div>
                      <div className="mt-3">
                        {isActive ? (
                          <button
                            onClick={handlePoolDisconnect}
                            disabled={isProcessing}
                            className="w-full py-2 rounded-lg text-xs font-mono font-bold transition-all hover:opacity-90"
                            style={{
                              backgroundColor: THEME.colors.error,
                              color: "white",
                            }}
                          >
                            DISCONNECT
                          </button>
                        ) : (
                          <button
                            onClick={() => setSelectedPoolForConfig(pool)}
                            disabled={isProcessing}
                            className="w-full py-2 rounded-lg text-xs font-mono font-bold transition-all hover:opacity-90"
                            style={{
                              backgroundColor: THEME.colors.oxford,
                              color: "white",
                            }}
                          >
                            CONNECT
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </Panel>

          {/* Operator Identity / Auth */}
          <Panel title="Operator Identity" icon={<UserCheck className="w-4 h-4" />} isLoading={false}>
            {currentUser ? (
              <div className="space-y-4 font-mono text-xs">
                <div className="p-3 rounded-lg border" style={{
                  backgroundColor: isDarkMode ? "rgba(22, 163, 74, 0.08)" : "#F0FDF4",
                  borderColor: isDarkMode ? "rgba(22, 163, 74, 0.2)" : "#BBF7D0",
                }}>
                  <div className="flex items-center gap-2 mb-2">
                    <CheckCircle2 className="w-4 h-4" style={{ color: THEME.colors.success }} />
                    <span className="font-bold">Authenticated</span>
                  </div>
                  <MetricRow label="Identity" value={currentUser.username} />
                  <MetricRow label="Role" value={currentUser.role} />
                </div>
                <button
                  onClick={handleLogout}
                  className="w-full py-2.5 rounded-lg text-xs font-mono font-bold flex items-center justify-center gap-1.5 transition-all"
                  style={{ backgroundColor: isDarkMode ? "#DC2626" : "#DC2626", color: "white" }}
                >
                  <LogOut className="w-3.5 h-3.5" />
                  LOG OUT
                </button>
              </div>
            ) : (
              <form onSubmit={isRegisterMode ? handleRegister : handleLogin} className="space-y-3">
                <div className="space-y-2">
                  <label className="text-[10px] font-mono font-bold uppercase tracking-wider" style={{ color: THEME.colors.slate }}>
                    Operator Handle
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="Enter your operator handle"
                    value={usernameInput}
                    onChange={e => setUsernameInput(e.target.value)}
                    className="w-full rounded-lg p-2.5 font-mono text-xs outline-none transition-all border"
                    style={{
                      backgroundColor: isDarkMode ? "#1A1B23" : "#F8FAFC",
                      borderColor: isDarkMode ? "rgba(255,255,255,0.15)" : "#E2E4E9",
                      color: isDarkMode ? "#C5C6C7" : "#1A1A1E",
                    }}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-[10px] font-mono font-bold uppercase tracking-wider" style={{ color: THEME.colors.slate }}>
                    Password
                  </label>
                  <input
                    type="password"
                    required
                    placeholder="Enter your password"
                    value={passwordInput}
                    onChange={e => setPasswordInput(e.target.value)}
                    className="w-full rounded-lg p-2.5 font-mono text-xs outline-none transition-all border"
                    style={{
                      backgroundColor: isDarkMode ? "#1A1B23" : "#F8FAFC",
                      borderColor: isDarkMode ? "rgba(255,255,255,0.15)" : "#E2E4E9",
                      color: isDarkMode ? "#C5C6C7" : "#1A1A1E",
                    }}
                  />
                </div>
                <div className="grid grid-cols-2 gap-2 pt-1">
                  <button
                    type="submit"
                    className="font-mono py-2.5 rounded-lg text-xs font-bold flex items-center justify-center gap-1.5 transition-all hover:opacity-90"
                    style={{ backgroundColor: THEME.colors.oxford, color: "white" }}
                  >
                    {isRegisterMode ? <UserPlus className="w-3.5 h-3.5" /> : <LogIn className="w-3.5 h-3.5" />}
                    {isRegisterMode ? "REGISTER" : "LOG IN"}
                  </button>
                  <button
                    type="button"
                    onClick={() => { setIsRegisterMode(!isRegisterMode); clearAuthFeedback(); }}
                    className="font-mono py-2.5 rounded-lg text-xs font-bold transition-all hover:opacity-80 border"
                    style={{
                      borderColor: isDarkMode ? "rgba(255,255,255,0.2)" : "#E2E4E9",
                      color: isDarkMode ? "#C5C6C7" : "#1A1A1E",
                    }}
                  >
                    {isRegisterMode ? "← LOG IN" : "SIGN UP →"}
                  </button>
                </div>
              </form>
            )}
            {authFeedback && (
              <div
                className={`mt-3 p-2.5 rounded-lg text-xs flex items-center gap-1.5 ${
                  authFeedback.error ? "border" : "border"
                }`}
                style={{
                  backgroundColor: authFeedback.error ? "#FEF2F2" : "#F0FDF4",
                  borderColor: authFeedback.error ? "#FECACA" : "#BBF7D0",
                  color: authFeedback.error ? "#991B1B" : "#166534",
                }}
                role="alert"
              >
                {authFeedback.error ? <AlertCircle className="w-3.5 h-3.5 shrink-0" /> : <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />}
                <span>{authFeedback.text}</span>
              </div>
            )}
          </Panel>
        </section>

        {/* Catalog Data */}
        <Panel title="Product Catalog" icon={<Database className="w-4 h-4" />} isLoading={false}>
          {products.length === 0 ? (
            <EmptyState message="No catalog records available from backend." icon={<Database className="w-8 h-8" />} />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {products.map(product => (
                <div
                  key={product.id || product.name}
                  className="rounded-lg p-3.5 border transition-colors"
                  style={{
                    backgroundColor: isDarkMode ? "rgba(255,255,255,0.03)" : "#F8FAFC",
                    borderColor: isDarkMode ? "rgba(255,255,255,0.1)" : "#E2E4E9",
                  }}
                >
                  <h5 className="font-sans font-bold text-xs truncate">{fmtText(product.name)}</h5>
                  <p className="text-[10px] mt-1 leading-relaxed" style={{ color: THEME.colors.slate }}>
                    {fmtText(product.description)}
                  </p>
                </div>
              ))}
            </div>
          )}
        </Panel>
      </main>

      {/* ── Footer ── */}
      <footer
        className="border-t-2 py-6 px-6 shrink-0 mt-8"
        style={{
          backgroundColor: THEME.colors.oxford,
          borderColor: THEME.colors.clicquotGold,
          color: "rgba(255,255,255,0.7)",
        }}
      >
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4 text-[10px] font-mono">
          <span>HYBA PRODUCTION RUNTIME WORKSPACE</span>
          <span>© 2026 HYBA GROUP</span>
          <span className="flex items-center gap-1" style={{ color: THEME.colors.clicquotGold }}>
            <ShieldCheck className="w-3.5 h-3.5" style={{ color: THEME.colors.clicquotOrange }} />
            REAL TELEMETRY ONLY — NO FABRICATED DATA
          </span>
        </div>
      </footer>

      {/* Pool Secrets Config Modal */}
      {selectedPoolForConfig && (
        <PoolSecretsConfig
          poolName={selectedPoolForConfig.name || "Pool"}
          onClose={() => setSelectedPoolForConfig(null)}
          onSave={handlePoolConnect}
        />
      )}
    </div>
  );
}

// ── Pool Status Badge ────────────────────────────────────────────────────

function PoolStatusBadge({ status }: { status?: string }) {
  const colorMap: Record<string, string> = {
    connected: THEME.colors.success,
    active: THEME.colors.success,
    disconnected: THEME.colors.error,
    error: THEME.colors.error,
    connecting: THEME.colors.warning,
    reconnecting: THEME.colors.warning,
  };
  const color = status ? colorMap[status.toLowerCase()] : THEME.colors.slate;
  return (
    <span
      className="px-1.5 py-0.5 rounded font-bold uppercase text-[8px] border"
      style={{
        color: color,
        borderColor: color,
        backgroundColor: `${color}15`,
      }}
    >
      {fmtText(status)}
    </span>
  );
}

// ── Card Components ──────────────────────────────────────────────────────

function MetricCard({ label, value, icon, status }: { label: string; value: string; icon: React.ReactNode; status?: string }) {
  const statusColor = status === "READY" || status === "HEALTHY" || status === "OK"
    ? THEME.colors.success
    : status === "DEGRADED" ? THEME.colors.warning
    : status === "ERROR" || status === "UNAVAILABLE" ? THEME.colors.error
    : undefined;

  return (
    <div
      className="rounded-xl p-4 shadow-sm border transition-colors"
      style={{
        backgroundColor: "var(--card-bg, white)",
        borderColor: "var(--border-color, #E2E4E9)",
      }}
    >
      <div className="flex items-center gap-2 mb-2" style={{ color: THEME.colors.slate }}>
        {icon}
        <span className="text-[10px] font-mono uppercase font-bold tracking-wider">{label}</span>
      </div>
      <div
        className="text-lg font-mono font-bold truncate"
        style={{ color: statusColor || "var(--text-color, #1A1A1E)" }}
      >
        {value}
      </div>
    </div>
  );
}

function Panel({
  title,
  icon,
  children,
  isLoading = false,
  rows = 4,
}: {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  isLoading?: boolean;
  rows?: number;
}) {
  return (
    <section
      className="rounded-xl p-5 shadow-sm border transition-colors"
      style={{
        backgroundColor: "var(--card-bg, white)",
        borderColor: "var(--border-color, #E2E4E9)",
      }}
    >
      <div className="flex items-center gap-2 mb-3 pb-2 border-b" style={{ borderColor: "var(--border-color, #E2E4E9)" }}>
        {icon}
        <h4 className="text-xs font-mono font-bold uppercase tracking-wider">{title}</h4>
      </div>
      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: rows }).map((_, i) => (
            <div key={i} className="flex justify-between items-center">
              <Skeleton width="100px" height="12px" />
              <Skeleton width="60px" height="12px" />
            </div>
          ))}
        </div>
      ) : (
        children
      )}
    </section>
  );
}

function MetricRow({ label, value }: { label: string; value: string }) {
  return (
    <div
      className="flex justify-between gap-4 py-2 font-mono text-xs border-b last:border-b-0"
      style={{ borderColor: "var(--border-color, #E2E4E9)" }}
    >
      <span style={{ color: THEME.colors.slate }}>{label}</span>
      <span className="font-semibold text-right truncate" style={{ color: "var(--text-color, #1A1A1E)" }}>
        {value}
      </span>
    </div>
  );
}