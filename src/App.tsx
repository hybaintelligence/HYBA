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
  type ConfigurePoolRequest,
  type HealthResponse,
  type PoolInfo,
  type TelemetryData,
  configurePool,
  connectToPool,
  disconnectFromPool,
  fetchProfileApi,
  fetchProductsApi,
  fetchTelemetryData,
  loginApi,
  logout as apiLogout,
  registerApi,
  switchPool,
  updatePowerScale,
} from "./apiClient";
import { NetworkToast } from "./components/NetworkToast";
import { PoolSecretsConfig } from "./components/PoolSecretsConfig";
import { Sparkline } from "./components/Sparkline";
import { useApiRequest } from "./hooks/useApiRequest";
import { useLatencyMetrics } from "./hooks/useLatencyMetrics";

type NullableNumber = number | null | undefined;

const THEME = {
  colors: {
    oxford: "#002147",
    clicquotGold: "#C5A55A",
    clicquotOrange: "#E8772E",
    sand: "#F5F0EB",
    slate: "#64748B",
    error: "#DC2626",
    success: "#16A34A",
    warning: "#D97706",
  },
} as const;

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

function Skeleton({ width = "100%", height = "20px" }: { width?: string; height?: string }) {
  return <div className="animate-pulse rounded bg-slate-200/40" style={{ width, height }} aria-hidden="true" />;
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
    <div className="flex flex-col items-center justify-center gap-3 p-6 text-center rounded-lg border border-red-200 bg-red-50">
      <div className="flex items-center gap-2 text-red-600">
        <FileWarning className="w-5 h-5" />
        <span className="font-mono text-sm font-semibold">Error</span>
      </div>
      <p className="text-sm font-mono text-red-900">{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="flex items-center gap-1.5 px-4 py-2 text-xs font-mono font-bold rounded-lg bg-red-600 text-white">
          <RefreshCw className="w-3.5 h-3.5" /> RETRY
        </button>
      )}
    </div>
  );
}

export default function App() {
  return <AppContent />;
}

function AppContent() {
  const [token, setToken] = useState<string | null>(() => {
    try {
      return localStorage.getItem("hyba_auth_token") || localStorage.getItem("quantum_token");
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

  const runtimeStatus = useMemo(() => health?.status || "unavailable", [health]);

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

  const handlePoolSave = async (payload: ConfigurePoolRequest, connectAfterSave: boolean) => {
    if (!payload.pool_id) return;
    setIsProcessing(true);
    try {
      await configurePool(payload);
      if (connectAfterSave) {
        await switchPool({ pool_id: payload.pool_id, capacity_ehs: powerScale, switch: true });
        setAuthFeedback({ text: `Configured and switched to ${selectedPoolForConfig?.name || payload.pool_id}`, error: false });
      } else {
        setAuthFeedback({ text: `Configured ${selectedPoolForConfig?.name || payload.pool_id}`, error: false });
      }
      await getLiveTelemetry();
      setSelectedPoolForConfig(null);
    } catch (err) {
      setAuthFeedback({ text: err instanceof Error ? err.message : "Pool configuration failed", error: true });
      throw err;
    } finally {
      setIsProcessing(false);
    }
  };

  const handlePoolSwitch = async (pool: PoolInfo) => {
    if (!pool.pool_id) return;
    if (!pool.configured) {
      setSelectedPoolForConfig(pool);
      return;
    }
    setIsProcessing(true);
    try {
      await switchPool({ pool_id: pool.pool_id, capacity_ehs: powerScale, switch: true });
      setAuthFeedback({ text: `Switched to ${pool.name || pool.pool_id}`, error: false });
      await getLiveTelemetry();
    } catch (err) {
      setAuthFeedback({ text: err instanceof Error ? err.message : "Failed to switch pool", error: true });
    } finally {
      setIsProcessing(false);
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

  const isLoading = !telemetry && !telemetryError;

  return (
    <div className={`min-h-screen flex flex-col font-sans transition-colors duration-300 ${isDarkMode ? "bg-[#0B0C10] text-[#C5C6C7]" : "bg-[#F5F0EB] text-[#1A1A1E]"}`}>
      <NetworkToast isConnected={isConnected} latencyMs={latencyMs} isDismissed={isToastDismissed} onDismiss={() => setIsToastDismissed(true)} />

      <header className="sticky top-0 z-40 border-b-2 px-6 py-4 shadow-lg" style={{ backgroundColor: THEME.colors.oxford, borderColor: THEME.colors.clicquotGold, color: "white" }}>
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="text-white font-mono text-[10px] font-bold px-2 py-0.5 rounded tracking-widest" style={{ backgroundColor: THEME.colors.clicquotOrange }}>HYBA</div>
            <h1 className="text-sm font-sans font-extrabold tracking-wider text-white uppercase">Production Runtime Console</h1>
            <span className="text-[9px] px-1.5 py-0.5 rounded font-mono font-semibold" style={{ backgroundColor: "rgba(10, 92, 145, 0.3)", color: "rgba(255,255,255,0.9)", border: "1px solid rgba(10, 92, 145, 0.6)" }}>v{fmtText(health?.version || "2.0.1")}</span>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <div className="flex items-center gap-1.5 px-2 py-1 rounded text-[10px] font-mono" style={{ backgroundColor: "rgba(0,0,0,0.2)" }}>
              {isConnected ? <Wifi className="w-3 h-3" style={{ color: THEME.colors.success }} /> : <WifiOff className="w-3 h-3" style={{ color: THEME.colors.error }} />}
              <span style={{ color: isConnected ? THEME.colors.success : THEME.colors.error }}>{isConnected ? `${latencyMs.toFixed(0)}ms` : "OFFLINE"}</span>
            </div>
            <button onClick={() => setIsPollingActive(!isPollingActive)} className="px-3 py-1.5 rounded text-[10px] font-mono font-bold border" style={{ backgroundColor: isPollingActive ? "rgba(22, 163, 74, 0.2)" : "rgba(217, 119, 6, 0.2)", borderColor: isPollingActive ? THEME.colors.success : THEME.colors.warning, color: isPollingActive ? "#BBF7D0" : "#FDE68A" }}>{isPollingActive ? "● LIVE" : "○ PAUSED"}</button>
            <button onClick={getLiveTelemetry} disabled={isSyncing} className="px-3 py-1.5 rounded text-[10px] font-mono font-bold flex items-center gap-1.5" style={{ backgroundColor: "rgba(10, 92, 145, 0.3)", border: "1px solid rgba(10, 92, 145, 0.6)", color: "white" }}><RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? "animate-spin" : ""}`} /> REFRESH</button>
            <Sparkline data={latencyHistory} />
            <button onClick={toggleTheme} className="p-1.5 rounded" style={{ backgroundColor: "rgba(255,255,255,0.1)" }}>{isDarkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}</button>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-7xl mx-auto w-full px-6 py-6 flex flex-col gap-6">
        <section className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {isLoading ? [1, 2, 3, 4].map(i => <div key={i} className="rounded-xl p-4 shadow-sm border bg-white"><Skeleton width="80px" height="12px" /><div className="mt-2"><Skeleton width="60%" height="24px" /></div></div>) : (
            <>
              <MetricCard label="Runtime status" value={runtimeStatus.toUpperCase()} icon={<Activity className="w-4 h-4" />} status={runtimeStatus} />
              <MetricCard label="Telemetry source" value={fmtText(health?.telemetry_source)} icon={<Database className="w-4 h-4" />} />
              <MetricCard label="Active pool" value={fmtText(systemMetrics.activePool || poolSummary.active_pool_name)} icon={<Server className="w-4 h-4" />} />
              <MetricCard label="Backend latency" value={isConnected ? `${latencyMs.toFixed(0)} ms` : UNAVAILABLE} icon={isConnected ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />} />
            </>
          )}
        </section>

        {telemetryError && !isLoading && <ErrorState message={telemetryError} onRetry={getLiveTelemetry} />}

        <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Panel title="Mining Telemetry" icon={<Database className="w-4 h-4" />} isLoading={isLoading} rows={6}>
            <MetricRow label="Block height" value={fmtNum(systemMetrics.blockHeight, 0)} />
            <MetricRow label="Hashrate (EH/s)" value={fmtNum(systemMetrics.currentHashrate)} />
            <MetricRow label="Power consumption" value={fmtNum(systemMetrics.powerConsumption)} />
            <MetricRow label="Network difficulty" value={fmtNum(systemMetrics.networkDifficulty)} />
            <MetricRow label="Difficulty target" value={fmtText(systemMetrics.difficultyTarget)} />
            <MetricRow label="System health" value={fmtText(systemMetrics.system_health)} />
          </Panel>
          <Panel title="Quantum Runtime" icon={<Activity className="w-4 h-4" />} isLoading={isLoading} rows={6}>
            <MetricRow label="Basis coherence" value={fmtPct(health?.quantumCoherence)} />
            <MetricRow label="Phi phase alignment" value={fmtPct(health?.phiResonance)} />
            <MetricRow label="Quantum speedup" value={fmtNum(health?.quantumSpeedupFactor)} />
            <MetricRow label="Actual speedup" value={fmtNum(health?.actualSpeedupFactor)} />
            <MetricRow label="Power scale" value={`${powerScale.toFixed(1)}x`} />
            <input type="range" min="0.1" max="10.0" step="0.1" value={powerScale} onChange={e => handlePowerScaleChange(parseFloat(e.target.value))} className="w-full h-2 rounded-lg appearance-none cursor-pointer" style={{ accentColor: THEME.colors.clicquotGold }} aria-label="Power scale control" />
          </Panel>
          <Panel title="Runtime Integration" icon={<ShieldCheck className="w-4 h-4" />} isLoading={isLoading} rows={6}>
            <MetricRow label="AI state" value={fmtText(consciousness.status)} />
            <MetricRow label="Integrated information" value={fmtNum(consciousness.integrated_information as NullableNumber)} />
            <MetricRow label="Security status" value={fmtText(security.status)} />
            <MetricRow label="Threat level" value={fmtText(security.threat_level)} />
            <MetricRow label="Pools configured" value={fmtNum((poolSummary.configured_pools ?? poolSummary.total_pools) as NullableNumber, 0)} />
            <MetricRow label="Active pools" value={fmtNum(poolSummary.active_pools as NullableNumber, 0)} />
          </Panel>
        </section>

        <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Panel title="Stratum Mining Pools" icon={<Database className="w-4 h-4" />} isLoading={isLoading && pools.length === 0} rows={4}>
            {!isLoading && pools.length === 0 ? <EmptyState message="No pool telemetry available from backend." icon={<Server className="w-8 h-8" />} /> : (
              <div className="space-y-2.5 max-h-[480px] overflow-y-auto pr-1">
                {pools.map((pool, idx) => {
                  const isActive = Boolean(pool.is_active || pool.connection_state?.toLowerCase() === "connected" || pool.status?.toLowerCase() === "connected");
                  return (
                    <div key={pool.pool_id || pool.name || idx} className="p-3 rounded-lg border text-[11px] font-mono bg-white/60">
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="font-bold truncate">{fmtText(pool.name)}</span>
                        <PoolStatusBadge status={pool.status || pool.connection_state} />
                      </div>
                      <div className="text-[10px] truncate mb-2" style={{ color: THEME.colors.slate }}>{fmtText(pool.url)}</div>
                      <div className="grid grid-cols-2 gap-2 text-[10px] pt-1.5 border-t border-slate-200">
                        <span>Mode: <strong>{fmtText(pool.credential_mode)}</strong></span>
                        <span>Configured: <strong>{pool.configured ? "YES" : "NO"}</strong></span>
                        <span>Latency: <strong>{fmtNum(pool.performance?.latency_ms)} ms</strong></span>
                        <span>Shares: <strong>{fmtNum(pool.performance?.shares_submitted, 0)}</strong></span>
                      </div>
                      <div className="grid grid-cols-2 gap-2 mt-3">
                        <button onClick={() => setSelectedPoolForConfig(pool)} disabled={isProcessing} className="py-2 rounded-lg text-xs font-mono font-bold bg-slate-900 text-white">CONFIGURE</button>
                        {isActive ? (
                          <button onClick={handlePoolDisconnect} disabled={isProcessing} className="py-2 rounded-lg text-xs font-mono font-bold text-white" style={{ backgroundColor: THEME.colors.error }}>DISCONNECT</button>
                        ) : (
                          <button onClick={() => handlePoolSwitch(pool)} disabled={isProcessing} className="py-2 rounded-lg text-xs font-mono font-bold text-white" style={{ backgroundColor: pool.configured ? THEME.colors.oxford : THEME.colors.warning }}>{pool.configured ? "SWITCH" : "SETUP"}</button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </Panel>

          <Panel title="Operator Identity" icon={<UserCheck className="w-4 h-4" />} isLoading={false}>
            {currentUser ? (
              <div className="space-y-4 font-mono text-xs">
                <div className="p-3 rounded-lg border border-green-200 bg-green-50">
                  <div className="flex items-center gap-2 mb-2"><CheckCircle2 className="w-4 h-4" style={{ color: THEME.colors.success }} /><span className="font-bold">Authenticated</span></div>
                  <MetricRow label="Identity" value={currentUser.username} />
                  <MetricRow label="Role" value={currentUser.role} />
                </div>
                <button onClick={handleLogout} className="w-full py-2.5 rounded-lg text-xs font-mono font-bold flex items-center justify-center gap-1.5 bg-red-600 text-white"><LogOut className="w-3.5 h-3.5" /> LOG OUT</button>
              </div>
            ) : (
              <form onSubmit={isRegisterMode ? handleRegister : handleLogin} className="space-y-3">
                <AuthInput label="Operator Handle" value={usernameInput} setValue={setUsernameInput} type="text" placeholder="Enter your operator handle" />
                <AuthInput label="Password" value={passwordInput} setValue={setPasswordInput} type="password" placeholder="Enter your password" />
                <div className="grid grid-cols-2 gap-2 pt-1">
                  <button type="submit" className="font-mono py-2.5 rounded-lg text-xs font-bold flex items-center justify-center gap-1.5 text-white" style={{ backgroundColor: THEME.colors.oxford }}>{isRegisterMode ? <UserPlus className="w-3.5 h-3.5" /> : <LogIn className="w-3.5 h-3.5" />}{isRegisterMode ? "REGISTER" : "LOG IN"}</button>
                  <button type="button" onClick={() => { setIsRegisterMode(!isRegisterMode); clearAuthFeedback(); }} className="font-mono py-2.5 rounded-lg text-xs font-bold border">{isRegisterMode ? "← LOG IN" : "SIGN UP →"}</button>
                </div>
              </form>
            )}
            {authFeedback && <Feedback feedback={authFeedback} />}
          </Panel>
        </section>

        <Panel title="Product Catalog" icon={<Database className="w-4 h-4" />} isLoading={false}>
          {products.length === 0 ? <EmptyState message="No catalog records available from backend." icon={<Database className="w-8 h-8" />} /> : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {products.map(product => <div key={product.id || product.name} className="rounded-lg p-3.5 border bg-white/60"><h5 className="font-sans font-bold text-xs truncate">{fmtText(product.name)}</h5><p className="text-[10px] mt-1 leading-relaxed" style={{ color: THEME.colors.slate }}>{fmtText(product.description)}</p></div>)}
            </div>
          )}
        </Panel>
      </main>

      <footer className="border-t-2 py-6 px-6 shrink-0 mt-8" style={{ backgroundColor: THEME.colors.oxford, borderColor: THEME.colors.clicquotGold, color: "rgba(255,255,255,0.7)" }}>
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4 text-[10px] font-mono">
          <span>HYBA PRODUCTION RUNTIME WORKSPACE</span><span>© 2026 HYBA GROUP</span><span className="flex items-center gap-1" style={{ color: THEME.colors.clicquotGold }}><ShieldCheck className="w-3.5 h-3.5" style={{ color: THEME.colors.clicquotOrange }} /> REAL TELEMETRY ONLY — NO FABRICATED DATA</span>
        </div>
      </footer>

      {selectedPoolForConfig && <PoolSecretsConfig pool={selectedPoolForConfig} onClose={() => setSelectedPoolForConfig(null)} onSave={handlePoolSave} />}
    </div>
  );
}

function AuthInput({ label, value, setValue, type, placeholder }: { label: string; value: string; setValue: (value: string) => void; type: string; placeholder: string }) {
  return (
    <div className="space-y-2">
      <label className="text-[10px] font-mono font-bold uppercase tracking-wider" style={{ color: THEME.colors.slate }}>{label}</label>
      <input type={type} required placeholder={placeholder} value={value} onChange={e => setValue(e.target.value)} className="w-full rounded-lg p-2.5 font-mono text-xs outline-none transition-all border bg-slate-50" />
    </div>
  );
}

function Feedback({ feedback }: { feedback: { text: string; error: boolean } }) {
  return (
    <div className="mt-3 p-2.5 rounded-lg text-xs flex items-center gap-1.5 border" style={{ backgroundColor: feedback.error ? "#FEF2F2" : "#F0FDF4", borderColor: feedback.error ? "#FECACA" : "#BBF7D0", color: feedback.error ? "#991B1B" : "#166534" }} role="alert">
      {feedback.error ? <AlertCircle className="w-3.5 h-3.5 shrink-0" /> : <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />}
      <span>{feedback.text}</span>
    </div>
  );
}

function PoolStatusBadge({ status }: { status?: string }) {
  const colorMap: Record<string, string> = { connected: THEME.colors.success, active: THEME.colors.success, configured: THEME.colors.success, not_configured: THEME.colors.warning, disconnected: THEME.colors.error, error: THEME.colors.error, connecting: THEME.colors.warning, reconnecting: THEME.colors.warning };
  const color = status ? colorMap[status.toLowerCase()] || THEME.colors.slate : THEME.colors.slate;
  return <span className="px-1.5 py-0.5 rounded font-bold uppercase text-[8px] border" style={{ color, borderColor: color, backgroundColor: `${color}15` }}>{fmtText(status)}</span>;
}

function MetricCard({ label, value, icon, status }: { label: string; value: string; icon: React.ReactNode; status?: string }) {
  const statusColor = status === "ok" || status === "healthy" ? THEME.colors.success : status === "unavailable" || status === "error" ? THEME.colors.error : THEME.colors.clicquotGold;
  return (
    <div className="rounded-xl p-4 shadow-sm border bg-white">
      <div className="flex items-center justify-between mb-2"><span className="text-[10px] font-mono font-bold uppercase tracking-wider" style={{ color: THEME.colors.slate }}>{label}</span><div style={{ color: statusColor }}>{icon}</div></div>
      <div className="text-lg font-mono font-bold truncate" style={{ color: status ? statusColor : THEME.colors.oxford }}>{value}</div>
    </div>
  );
}

function Panel({ title, icon, children, isLoading, rows = 4 }: { title: string; icon: React.ReactNode; children: React.ReactNode; isLoading?: boolean; rows?: number }) {
  return (
    <div className="rounded-xl border shadow-sm overflow-hidden bg-white">
      <div className="px-4 py-3 border-b flex items-center gap-2" style={{ backgroundColor: "rgba(0,33,71,0.04)", borderColor: "#E2E4E9" }}>
        <div style={{ color: THEME.colors.clicquotOrange }}>{icon}</div><h3 className="text-xs font-mono font-bold uppercase tracking-wider" style={{ color: THEME.colors.oxford }}>{title}</h3>
      </div>
      <div className="p-4">
        {isLoading ? <div className="space-y-3">{Array.from({ length: rows }).map((_, i) => <div key={i}><Skeleton width={i % 2 === 0 ? "100%" : "70%"} height="18px" /></div>)}</div> : children}
      </div>
    </div>
  );
}

function MetricRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between py-1.5 border-b last:border-0" style={{ borderColor: "rgba(100,116,139,0.12)" }}>
      <span className="text-[10px] font-mono" style={{ color: THEME.colors.slate }}>{label}</span>
      <span className="text-[11px] font-mono font-semibold text-right max-w-[55%] truncate">{value}</span>
    </div>
  );
}
