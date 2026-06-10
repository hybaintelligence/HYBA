import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  Database,
  LogIn,
  LogOut,
  Moon,
  RefreshCw,
  ShieldCheck,
  Sun,
  UserCheck,
  UserPlus,
} from "lucide-react";

import {
  fetchProfileApi,
  fetchProductsApi,
  fetchTelemetryData,
  loginApi,
  registerApi,
  updatePowerScale,
} from "./apiClient";
import { AuthProvider } from "./components/AuthProvider";
import { NetworkToast } from "./components/NetworkToast";
import { Sparkline } from "./components/Sparkline";
import { useApiRequest } from "./hooks/useApiRequest";
import { useLatencyMetrics } from "./hooks/useLatencyMetrics";

type NullableNumber = number | null | undefined;

type RuntimeHealth = {
  status?: string;
  version?: string;
  telemetry_source?: string;
  quantumCoherence?: NullableNumber;
  quantumSpeedupFactor?: NullableNumber;
  actualSpeedupFactor?: NullableNumber;
  phiResonance?: NullableNumber;
  systemMetrics?: {
    blockHeight?: NullableNumber;
    currentHashrate?: NullableNumber;
    powerConsumption?: NullableNumber;
    activePool?: string | null;
    difficultyTarget?: string | null;
    networkDifficulty?: NullableNumber;
    power_scale?: NullableNumber;
    system_health?: string | null;
  };
};

type RuntimeTelemetry = {
  health?: RuntimeHealth;
  consciousness?: Record<string, unknown>;
  pools?: {
    pools?: Array<Record<string, any>>;
    summary?: Record<string, any>;
  };
  security?: Record<string, any>;
  latency?: number;
};

const unavailable = "Unavailable";

function formatNumber(value: NullableNumber, digits = 2): string {
  return typeof value === "number" && Number.isFinite(value) ? value.toLocaleString(undefined, { maximumFractionDigits: digits }) : unavailable;
}

function formatPercent(value: NullableNumber): string {
  return typeof value === "number" && Number.isFinite(value) ? `${(value * 100).toFixed(2)}%` : unavailable;
}

function formatText(value: unknown): string {
  return typeof value === "string" && value.trim().length > 0 ? value : unavailable;
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

function AppContent() {
  const [token, setToken] = useState<string | null>(() => {
    try {
      return localStorage.getItem("quantum_token");
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
  const [telemetry, setTelemetry] = useState<RuntimeTelemetry | null>(null);
  const [isSyncing, setIsSyncing] = useState(false);
  const [isPollingActive, setIsPollingActive] = useState(true);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [powerScale, setPowerScale] = useState(1);

  const { execute: fetchTelemetryExecute } = useApiRequest(fetchTelemetryData, { maxRetries: 3 });
  const {
    isConnected,
    latencyMs,
    latencyHistory,
    isToastDismissed,
    setIsToastDismissed,
    recordPing,
  } = useLatencyMetrics();

  const health = telemetry?.health;
  const systemMetrics = health?.systemMetrics || {};
  const pools = telemetry?.pools?.pools || [];
  const poolSummary = telemetry?.pools?.summary || {};
  const security = telemetry?.security || {};
  const consciousness = telemetry?.consciousness || {};

  const runtimeStatus = useMemo(() => {
    if (!health) return "unavailable";
    return health.status || "unknown";
  }, [health]);

  const getLiveTelemetry = useCallback(async () => {
    setIsSyncing(true);
    try {
      const data = await fetchTelemetryExecute();
      setTelemetry(data);
      if (typeof data?.health?.systemMetrics?.power_scale === "number") {
        setPowerScale(data.health.systemMetrics.power_scale);
      }
      recordPing(data.latency || 0, true);
    } catch {
      setTelemetry(null);
      recordPing(0, false);
    } finally {
      setIsSyncing(false);
    }
  }, [fetchTelemetryExecute, recordPing]);

  const fetchProfile = useCallback(async () => {
    if (!token) return;
    try {
      const res = await fetchProfileApi();
      const data = await res.json();
      if (data.success) {
        setCurrentUser(data.user);
      } else {
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

  useEffect(() => {
    fetchProfile();
    fetchProducts();
  }, [fetchProfile, fetchProducts]);

  useEffect(() => {
    if (isPollingActive) getLiveTelemetry();
    const interval = window.setInterval(() => {
      if (isPollingActive) getLiveTelemetry();
    }, 10000);
    return () => window.clearInterval(interval);
  }, [getLiveTelemetry, isPollingActive]);

  useEffect(() => {
    setIsDarkMode(document.documentElement.classList.contains("dark"));
  }, []);

  const toggleTheme = () => {
    const next = !isDarkMode;
    setIsDarkMode(next);
    document.documentElement.classList.toggle("dark", next);
  };

  const handleLogin = async (event: React.FormEvent) => {
    event.preventDefault();
    setAuthFeedback(null);
    if (!usernameInput || !passwordInput) {
      setAuthFeedback({ text: "Please enter all credentials", error: true });
      return;
    }
    try {
      const res = await loginApi({ username: usernameInput, password: passwordInput });
      const data = await res.json();
      if (!data.success) {
        setAuthFeedback({ text: data.error || "Authentication failed", error: true });
        return;
      }
      localStorage.setItem("quantum_token", data.token);
      setToken(data.token);
      setCurrentUser(data.user);
      setUsernameInput("");
      setPasswordInput("");
      setAuthFeedback({ text: `Welcome back, ${data.user.username}.`, error: false });
    } catch {
      setAuthFeedback({ text: "Could not reach authentication server", error: true });
    }
  };

  const handleRegister = async (event: React.FormEvent) => {
    event.preventDefault();
    setAuthFeedback(null);
    if (!usernameInput || !passwordInput) {
      setAuthFeedback({ text: "Please enter all fields", error: true });
      return;
    }
    try {
      const res = await registerApi({ username: usernameInput, password: passwordInput });
      const data = await res.json();
      if (data.success) {
        setAuthFeedback({ text: "Registered successfully. You can now log in.", error: false });
        setIsRegisterMode(false);
        setPasswordInput("");
      } else {
        setAuthFeedback({ text: data.error || "Registration failed", error: true });
      }
    } catch {
      setAuthFeedback({ text: "Could not reach registration server", error: true });
    }
  };

  const handleLogout = () => {
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

  return (
    <div className={`min-h-screen ${isDarkMode ? "bg-[#0B0C10] text-[#C5C6C7]" : "bg-sand text-oxford"} flex flex-col font-sans`}>
      <NetworkToast
        isConnected={isConnected}
        latencyMs={latencyMs}
        isDismissed={isToastDismissed}
        onDismiss={() => setIsToastDismissed(true)}
      />

      <header className="border-b-2 border-clicquot-gold bg-oxford sticky top-0 z-40 px-6 py-4 shadow-lg text-white">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <div className="bg-clicquot-orange text-white font-mono text-[10px] font-bold px-2 py-0.5 rounded tracking-widest">HYBA</div>
              <h1 className="text-sm font-sans font-extrabold tracking-wider text-white uppercase">Production Runtime Console</h1>
              <span className="text-[9px] bg-[#003666] text-white/90 border border-[#0A5C91] px-1.5 py-0.5 rounded font-mono font-semibold">
                v{formatText(health?.version)}
              </span>
            </div>
            <p className="text-[10px] text-gray-300 mt-1 font-mono">
              Live backend telemetry only. Unavailable values are not estimated.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={() => setIsPollingActive(!isPollingActive)}
              className={`px-3 py-1.5 rounded text-[10px] font-mono font-bold border ${isPollingActive ? "bg-green-600/20 border-green-500 text-green-100" : "bg-yellow-600/20 border-yellow-500 text-yellow-100"}`}
            >
              {isPollingActive ? "AUTO-POLLING ACTIVE" : "POLLING PAUSED"}
            </button>
            <button
              onClick={getLiveTelemetry}
              disabled={isSyncing}
              className="bg-[#001c3d] hover:bg-[#0A5C91] border border-[#0A5C91] text-white px-3 py-1.5 rounded text-[10px] font-mono font-bold flex items-center gap-1.5"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? "animate-spin" : ""}`} />
              REFRESH
            </button>
            <Sparkline data={latencyHistory} />
            <button onClick={toggleTheme} className="bg-[#001c3d] hover:bg-[#0A5C91] border border-[#0A5C91] text-white p-1.5 rounded" title="Toggle Theme">
              {isDarkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-7xl mx-auto w-full px-6 py-6 flex flex-col gap-6">
        <section className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <MetricCard label="Runtime status" value={runtimeStatus.toUpperCase()} icon={<Activity className="w-4 h-4" />} />
          <MetricCard label="Telemetry source" value={formatText(health?.telemetry_source)} icon={<Database className="w-4 h-4" />} />
          <MetricCard label="Active pool" value={formatText(systemMetrics.activePool)} icon={<Database className="w-4 h-4" />} />
          <MetricCard label="Backend latency" value={isConnected ? `${latencyMs.toFixed(0)} ms` : unavailable} icon={<Activity className="w-4 h-4" />} />
        </section>

        <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Panel title="Mining telemetry" icon={<Database className="w-4 h-4" />}>
            <MetricRow label="Block height" value={formatNumber(systemMetrics.blockHeight, 0)} />
            <MetricRow label="Hashrate" value={formatNumber(systemMetrics.currentHashrate)} />
            <MetricRow label="Power consumption" value={formatNumber(systemMetrics.powerConsumption)} />
            <MetricRow label="Network difficulty" value={formatNumber(systemMetrics.networkDifficulty)} />
            <MetricRow label="Difficulty target" value={formatText(systemMetrics.difficultyTarget)} />
            <MetricRow label="System health" value={formatText(systemMetrics.system_health)} />
          </Panel>

          <Panel title="Quantum runtime" icon={<Activity className="w-4 h-4" />}>
            <MetricRow label="Basis coherence" value={formatPercent(health?.quantumCoherence)} />
            <MetricRow label="Phi phase alignment" value={formatPercent(health?.phiResonance)} />
            <MetricRow label="Quantum speedup" value={formatNumber(health?.quantumSpeedupFactor)} />
            <MetricRow label="Actual speedup" value={formatNumber(health?.actualSpeedupFactor)} />
            <MetricRow label="Power scale" value={`${powerScale.toFixed(1)}x`} />
            <input
              type="range"
              min="0.1"
              max="10.0"
              step="0.1"
              value={powerScale}
              onChange={event => handlePowerScaleChange(parseFloat(event.target.value))}
              className="w-full h-2 bg-[#E2E4E9] rounded-lg appearance-none cursor-pointer accent-clicquot-gold mt-3"
            />
          </Panel>

          <Panel title="Runtime integration" icon={<ShieldCheck className="w-4 h-4" />}>
            <MetricRow label="AI state" value={formatText(consciousness.status)} />
            <MetricRow label="Integrated information" value={formatNumber(consciousness.integrated_information as NullableNumber)} />
            <MetricRow label="Security status" value={formatText(security.status)} />
            <MetricRow label="Threat level" value={formatText(security.threat_level)} />
            <MetricRow label="Pools configured" value={formatNumber(poolSummary.total_pools as NullableNumber, 0)} />
            <MetricRow label="Active pools" value={formatNumber(poolSummary.active_pools as NullableNumber, 0)} />
          </Panel>
        </section>

        <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Panel title="Stratum mining pools" icon={<Database className="w-4 h-4" />}>
            {pools.length === 0 ? (
              <EmptyState message="No pool telemetry is available." />
            ) : (
              <div className="space-y-2.5">
                {pools.map((pool, idx) => (
                  <div key={pool.pool_id || pool.name || idx} className="p-3 rounded-lg font-mono text-[11px] border bg-[#FAFBFD] border-[#E2E4E9] text-oxford">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="font-bold text-oxford">{formatText(pool.name)}</span>
                      <span className="text-lux-slate bg-sand px-1.5 py-0.5 rounded font-bold uppercase text-[8px] border border-sand-dark">
                        {formatText(pool.connection_state || pool.status)}
                      </span>
                    </div>
                    <div className="text-[10px] text-lux-slate truncate mb-2">{formatText(pool.url)}</div>
                    <div className="grid grid-cols-2 gap-2 text-[10px] text-lux-slate border-t border-sand-dark pt-1.5">
                      <span>Latency: <strong className="text-oxford">{formatNumber(pool.performance?.latency_ms)} ms</strong></span>
                      <span>Shares: <strong className="text-oxford">{formatNumber(pool.performance?.shares_submitted, 0)}</strong></span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Panel>

          <Panel title="Operator identity" icon={<UserCheck className="w-4 h-4" />}>
            {currentUser ? (
              <div className="space-y-4 font-mono text-xs">
                <MetricRow label="Authenticated identity" value={currentUser.username} />
                <MetricRow label="Role" value={currentUser.role} />
                <button onClick={handleLogout} className="w-full bg-black text-white hover:bg-black/85 transition-colors font-mono py-2 rounded-lg text-xs flex items-center justify-center gap-1.5">
                  <LogOut className="w-3.5 h-3.5" />
                  LOG OUT
                </button>
              </div>
            ) : (
              <form onSubmit={isRegisterMode ? handleRegister : handleLogin} className="space-y-3">
                <input
                  type="text"
                  required
                  placeholder="Operator handle"
                  value={usernameInput}
                  onChange={event => setUsernameInput(event.target.value)}
                  className="w-full bg-[#F8FAFC] border border-[#E2E4E9] rounded-lg p-2 font-mono text-xs text-[#1A1A1E] focus:bg-white focus:border-black outline-none"
                />
                <input
                  type="password"
                  required
                  placeholder="Password"
                  value={passwordInput}
                  onChange={event => setPasswordInput(event.target.value)}
                  className="w-full bg-[#F8FAFC] border border-[#E2E4E9] rounded-lg p-2 font-mono text-xs text-[#1A1A1E] focus:bg-white focus:border-black outline-none"
                />
                <div className="grid grid-cols-2 gap-2 pt-1">
                  <button type="submit" className="bg-black text-white hover:bg-black/85 font-mono py-2 rounded-lg text-xs flex items-center justify-center gap-1">
                    {isRegisterMode ? <UserPlus className="w-3.5 h-3.5" /> : <LogIn className="w-3.5 h-3.5" />}
                    {isRegisterMode ? "REGISTER" : "LOG IN"}
                  </button>
                  <button type="button" onClick={() => setIsRegisterMode(!isRegisterMode)} className="border border-[#E2E4E9] hover:bg-[#F8FAFC] text-black font-mono py-2 rounded-lg text-xs">
                    {isRegisterMode ? "GO TO LOGIN" : "GO TO SIGNUP"}
                  </button>
                </div>
              </form>
            )}
            {authFeedback && (
              <div className={`mt-3 p-2.5 rounded-lg text-xs flex items-center gap-1.5 ${authFeedback.error ? "bg-red-50 text-red-600 border border-red-100" : "bg-green-50 text-green-700 border border-green-100"}`}>
                {authFeedback.error ? <AlertCircle className="w-3.5 h-3.5" /> : <CheckCircle2 className="w-3.5 h-3.5" />}
                <span>{authFeedback.text}</span>
              </div>
            )}
          </Panel>
        </section>

        <Panel title="Catalog data" icon={<Database className="w-4 h-4" />}>
          {products.length === 0 ? (
            <EmptyState message="No catalog records are available from the backend." />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {products.map(product => (
                <div key={product.id || product.name} className="border border-[#E2E4E9] rounded-lg p-3.5 bg-[#F8FAFC]">
                  <h5 className="font-sans font-bold text-xs text-[#1A1A1E] truncate">{formatText(product.name)}</h5>
                  <p className="text-[10px] text-[#64748B] mt-1 leading-relaxed">{formatText(product.description)}</p>
                </div>
              ))}
            </div>
          )}
        </Panel>
      </main>

      <footer className="border-t-2 border-clicquot-gold bg-oxford py-6 px-6 shrink-0 mt-8 text-white/80">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4 text-[10px] font-mono text-gray-300">
          <span>HYBA PRODUCTION RUNTIME WORKSPACE</span>
          <span>© 2026 HYBA GROUP</span>
          <span className="flex items-center gap-1 text-clicquot-gold">
            <ShieldCheck className="w-3.5 h-3.5 text-clicquot-orange" />
            REAL TELEMETRY ONLY
          </span>
        </div>
      </footer>
    </div>
  );
}

function MetricCard({ label, value, icon }: { label: string; value: string; icon: React.ReactNode }) {
  return (
    <div className="bg-white border border-[#E2E4E9] rounded-xl p-4 shadow-sm text-[#1A1A1E]">
      <div className="flex items-center gap-2 text-[#64748B] mb-2">
        {icon}
        <span className="text-[10px] font-mono uppercase font-bold tracking-wider">{label}</span>
      </div>
      <div className="text-lg font-mono font-bold truncate">{value}</div>
    </div>
  );
}

function Panel({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <section className="bg-white border border-[#E2E4E9] rounded-xl p-5 shadow-sm text-[#1A1A1E]">
      <div className="flex items-center gap-2 mb-3 border-b border-[#E2E4E9] pb-2">
        {icon}
        <h4 className="text-xs font-mono font-bold uppercase tracking-wider">{title}</h4>
      </div>
      {children}
    </section>
  );
}

function MetricRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4 border-b border-[#E2E4E9] py-2 font-mono text-xs last:border-b-0">
      <span className="text-[#64748B]">{label}</span>
      <span className="text-black font-semibold text-right truncate">{value}</span>
    </div>
  );
}

function EmptyState({ message }: { message: string }) {
  return <div className="text-xs font-mono text-[#64748B] p-4 text-center bg-[#F8FAFC] border border-[#E2E4E9] rounded-lg">{message}</div>;
}
