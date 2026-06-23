import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertCircle,
  Atom,
  BarChart3,
  CheckCircle2,
  Clock,
  Cpu,
  Crown,
  Database,
  FileWarning,
  Gauge,
  History,
  Landmark,
  LogIn,
  LogOut,
  Moon,
  RadioTower,
  RefreshCw,
  Rocket,
  Scale,
  Server,
  ShieldCheck,
  Sun,
  Terminal,
  TrendingUp,
  UserCheck,
  UserPlus,
  Wifi,
  WifiOff,
  Brain,
  GitBranch,
  Network,
  SlidersHorizontal,
  WalletCards,
} from "lucide-react";

import {
  type AuthResponse,
  type ConfigurePoolRequest,
  type PoolInfo,
  type TelemetryData,
  type SecurityStatus,
  configurePool,
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
import { SovereignGenesisPanel } from "./components/SovereignGenesisPanel";
import { SovereignCommandPost } from "./components/SovereignCommandPost";
import { Sparkline } from "./components/Sparkline";
import { ExecutiveSummary } from "./components/ExecutiveSummary";
import AdminPanel from "./components/AdminPanel";
import HybaAdminDashboard from "./components/HybaAdminDashboard";
import AIAssistant from "./components/AIAssistant";
import MiningJobsSection from "./components/MiningJobsSection";
import HistoricalDataSection from "./components/HistoricalDataSection";
import AnalyticsSection from "./components/AnalyticsSection";
import CustomerPortal from "./components/CustomerPortal";
import CIaaSServiceManager from "./components/CIaaSServiceManager";
import QaaSComputerManager from "./components/QaaSComputerManager";
import { useApiRequest } from "./hooks/useApiRequest";
import { useLatencyMetrics } from "./hooks/useLatencyMetrics";
import {
  buildGovernanceSignals,
  buildPortableEvidencePackage,
  downloadEvidencePackage,
  type GovernanceSignal,
} from "./governance";
import { useAuth } from "./components/AuthProvider";
import { SKILL_MODE_LABELS, SkillModeProvider, SkillModeSelector, useSkillMode } from "./components/SkillModeContext";
import { ClaimBoundaryBadge, MetricExplainerCard, EvidenceBoundAnswer } from "./components/IntelligenceTranslator";
import { DecisionCockpit, ProofExplainer, UseCaseStudio as ImportedUseCaseStudio } from "./components/AdaptiveIntelligenceLayer";

type NullableNumber = number | null | undefined;

const THEME = {
  colors: {
    mckinseyBlue: "#003666",
    oxford: "#002147",
    deepBlue: "#06162D",
    mitRed: "#A31F34",
    caltechOrange: "#FF6C0C",
    deepmindBlue: "#0B57D0",
    clicquotGold: "#C5A55A",
    sand: "#F5F0EB",
    slate: "#64748B",
    ink: "#111827",
    error: "#DC2626",
    success: "#16A34A",
    warning: "#D97706",
  },
} as const;

const UNAVAILABLE = "—";

const PHI_TIERS = [7, 10, 12, 15, 18, 20, 31, 76];

const EXECUTIVE_ROLES = ["ceo_heir_apparent", "chairman", "cto", "cfo", "legal", "chief_of_staff"];

function fmtNum(value: NullableNumber, digits = 2): string {
  return typeof value === "number" && Number.isFinite(value)
    ? value.toLocaleString(undefined, { maximumFractionDigits: digits })
    : UNAVAILABLE;
}

function fmtPct(value: NullableNumber): string {
  return typeof value === "number" && Number.isFinite(value)
    ? `${(value * 100).toFixed(2)}%`
    : UNAVAILABLE;
}

function fmtText(value: unknown): string {
  return typeof value === "string" && value.trim().length > 0 ? value : UNAVAILABLE;
}

function clamp(value: number, min = 0, max = 100): number {
  return Math.max(min, Math.min(max, value));
}

function Skeleton({ width = "100%", height = "20px" }: { width?: string; height?: string }) {
  return (
    <div
      className="animate-pulse rounded bg-slate-200/50"
      style={{ width, height }}
      aria-hidden="true"
    />
  );
}

function EmptyState({ message, icon }: { message: string; icon?: React.ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 rounded-2xl border border-dashed border-slate-200 bg-slate-50/80 p-8 text-center text-slate-500">
      {icon && <div className="opacity-50">{icon}</div>}
      <p className="text-sm font-mono">{message}</p>
    </div>
  );
}

function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="executive-alert border-red-200 bg-red-50/95 text-red-950">
      <div className="flex items-center gap-2 text-red-700">
        <FileWarning className="h-5 w-5" />
        <span className="font-mono text-sm font-semibold uppercase tracking-[0.18em]">
          Telemetry interruption
        </span>
      </div>
      <p className="text-sm leading-6">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="executive-button bg-red-600 text-white shadow-red-600/20"
        >
          <RefreshCw className="h-3.5 w-3.5" /> Retry connection
        </button>
      )}
    </div>
  );
}

export default function App() {
  return (
    <SkillModeProvider>
      <AppContent />
    </SkillModeProvider>
  );
}

function AppContent() {
  const { isAdmin, isExecutive } = useAuth();
  const [token, setToken] = useState<string | null>(() => {
    try {
      return localStorage.getItem("hyba_auth_token") || localStorage.getItem("quantum_token");
    } catch {
      return null;
    }
  });
  const [currentUser, setCurrentUser] = useState<{
    id?: string;
    username: string;
    role: string;
    createdAt?: string;
  } | null>(null);
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
  const [phiTier, setPhiTier] = useState(12);
  const [computeNode, setComputeNode] = useState("us-east-1");
  const [residencyStatus, setResidencyStatus] = useState("active");
  const [jurisdiction, setJurisdiction] = useState("us");
  const [powerScaleResponse, setPowerScaleResponse] = useState<{
    status: string;
    effective_hashrate_ehs?: number;
    phi_tier?: number;
    phi_tier_composition?: { label?: string; scale_factor?: number };
    hashrate_cap_ehs?: number;
  } | null>(null);
  const [selectedPoolForConfig, setSelectedPoolForConfig] = useState<PoolInfo | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentView, setCurrentView] = useState<
    | "dashboard"
    | "admin"
    | "executive"
    | "jobs"
    | "history"
    | "analytics"
    | "portal"
    | "studio"
    | "ciaas"
    | "qaas"
    | "studio"
  >("dashboard");

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
  const pools: PoolInfo[] = telemetry?.pools?.pools || [];
  const poolSummary = telemetry?.pools?.summary || {
    total_pools: 0,
    active_pools: 0,
    telemetry_source: "unavailable",
  };
  const security: Partial<SecurityStatus> = telemetry?.security || {};
  const securityDefenseSystems = security.defense_systems || {};
  const stabilizerMonitor = securityDefenseSystems.stabilizer_monitor || {};
  const ancillaTrapPool = securityDefenseSystems.preallocated_ancilla_trap_pool || {};
  const consciousness = telemetry?.consciousness || {
    status: "unavailable",
    source: "unavailable",
  };
  const extraordinaryEvidence = telemetry?.extraordinaryEvidence;
  const extraordinaryInvariantCount = extraordinaryEvidence
    ? Object.values(extraordinaryEvidence.invariant_results || {}).filter(Boolean).length
    : 0;
  const extraordinaryInvariantTotal = extraordinaryEvidence
    ? Object.keys(extraordinaryEvidence.invariant_results || {}).length
    : 0;
  const extraordinarySeal = extraordinaryEvidence?.evidence_seal
    ? `${extraordinaryEvidence.evidence_seal.slice(0, 12)}…`
    : UNAVAILABLE;
  const governanceTags = useMemo(
    () => [
      ...((health?.substrate?.governance_tags as string[] | undefined) || []),
      ...((health?.telemetry?.governance_tags as string[] | undefined) || []),
    ],
    [health?.substrate, health?.telemetry],
  );

  const runtimeStatus = useMemo(() => health?.status || "unavailable", [health]);
  const activePoolName = fmtText(systemMetrics.activePool || pools.find((p) => p.is_active)?.name);
  const configuredPoolCount = Number(poolSummary.configured_pools ?? poolSummary.total_pools ?? 0);
  const activePoolCount = Number(poolSummary.active_pools ?? 0);
  const securityStatus = fmtText(security.status);
  const [stabilityHistory, setStabilityHistory] = useState<number[]>([]);

  const reasoningStability = useMemo(() => {
    const coherence = typeof health?.quantumCoherence === "number" ? health.quantumCoherence : null;
    const phi = typeof health?.phiResonance === "number" ? health.phiResonance : null;
    if (coherence == null && phi == null) return null;
    const samples = [coherence, phi].filter((value): value is number => typeof value === "number");
    return samples.reduce((sum, value) => sum + value, 0) / samples.length;
  }, [health?.quantumCoherence, health?.phiResonance]);

  useEffect(() => {
    if (typeof reasoningStability !== "number") return;
    setStabilityHistory((current) => [...current.slice(-5), reasoningStability]);
  }, [reasoningStability]);

  const previousReasoningStability =
    stabilityHistory.length > 1 ? stabilityHistory[stabilityHistory.length - 2] : null;
  const reasoningVeracity =
    isConnected &&
    health?.telemetry_source &&
    !String(health.telemetry_source).toLowerCase().includes("fixture") &&
    extraordinaryEvidence?.evidence_seal &&
    extraordinaryEvidence?.all_invariants_passed
      ? "quantum"
      : "fallback";

  const realTelemetryContract = isConnected
    ? `Live backend source: ${fmtText(health?.telemetry_source)}. Missing fields stay unavailable rather than synthetic.`
    : "Backend disconnected. HYBA withholds live values instead of fabricating telemetry.";

  const governanceSignals = useMemo(
    () =>
      buildGovernanceSignals({
        runtimeStatus,
        telemetrySource: health?.telemetry_source,
        backendConnected: isConnected,
        activePoolCount,
        configuredPoolCount,
        activePoolName,
        securityStatus,
        threatLevel: security.threat_level,
        phiResonance: health?.phiResonance,
        governanceTags,
        computeNode,
        residencyStatus,
        jurisdiction,
      }),
    [
      activePoolCount,
      activePoolName,
      configuredPoolCount,
      governanceTags,
      health?.phiResonance,
      health?.telemetry_source,
      computeNode,
      isConnected,
      jurisdiction,
      residencyStatus,
      runtimeStatus,
      security.threat_level,
      securityStatus,
    ],
  );
  const operatorCommandEvidence = useMemo(
    () => [
      {
        icon: <Terminal className="h-4 w-4" />,
        title: "Bridge health",
        detail:
          "/bridge/health exposes backend reachability, circuit breaker state, and request telemetry.",
      },
      {
        icon: <BarChart3 className="h-4 w-4" />,
        title: "Prometheus metrics",
        detail: "/bridge/metrics emits counters and gauges for operational monitoring.",
      },
      {
        icon: <TrendingUp className="h-4 w-4" />,
        title: "Production gates",
        detail:
          "npm run prod:check validates type safety, build output, backend tests, and E2E smoke coverage.",
      },
      {
        icon: <Cpu className="h-4 w-4" />,
        title: "Operator command routes",
        detail:
          "Callable controls include /api/mining/pause, /api/mining/resume, /api/v1/intelligence/scale, /api/v1/intelligence/consciousness/boost, /api/v1/unified/analyze/blockchain, and /api/v1/unified/analyze/it-from-bit.",
      },
    ],
    [],
  );

  const readinessScore = useMemo(() => {
    let score = 0;
    if (["ok", "healthy"].includes(runtimeStatus.toLowerCase())) score += 30;
    if (isConnected) score += latencyMs < 500 ? 20 : 12;
    if (configuredPoolCount > 0) score += 18;
    if (activePoolCount > 0 || activePoolName !== UNAVAILABLE) score += 14;
    if (
      !["critical", "high", "error"].includes(
        String(security.threat_level || security.status || "").toLowerCase(),
      )
    )
      score += 18;
    return clamp(score);
  }, [
    activePoolCount,
    activePoolName,
    configuredPoolCount,
    isConnected,
    latencyMs,
    runtimeStatus,
    security.status,
    security.threat_level,
  ]);

  const operatingPrinciples = [
    {
      label: "Zero synthetic telemetry",
      detail: "Every KPI is sourced from backend health, pool, AI, or security endpoints.",
    },
    {
      label: "Cloudflare route ready",
      detail: "SPA traffic is cleanly split from proxied API calls for edge deployment.",
    },
    {
      label: "Executive control surface",
      detail:
        "Identity, pool switching, power scale, and incident signals are exposed in one console.",
    },
  ];

  const getLiveTelemetry = useCallback(async () => {
    setIsSyncing(true);
    setTelemetryError(null);
    try {
      const data = await fetchTelemetryExecute();
      setTelemetry(data);
      if (typeof data?.health?.systemMetrics?.power_scale === "number") {
        setPowerScale(data.health.systemMetrics.power_scale);
      }
      if (typeof data?.health?.systemMetrics?.phi_tier === "number") {
        setPhiTier(data.health.systemMetrics.phi_tier);
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

  useEffect(() => {
    fetchProfile();
    fetchProducts();
  }, [fetchProfile, fetchProducts]);

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
    setAuthFeedback({ text: "Authenticating...", error: false });
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
      setAuthFeedback({
        text: `Welcome back, ${data.user?.username || "operator"}.`,
        error: false,
      });
    } catch (err) {
      setAuthFeedback({
        text: err instanceof Error ? err.message : "Authentication server unreachable",
        error: true,
      });
    }
  };

  const handleRegister = async (event: React.FormEvent) => {
    event.preventDefault();
    clearAuthFeedback();
    if (!usernameInput || !passwordInput) {
      setAuthFeedback({ text: "Please enter all fields", error: true });
      return;
    }
    setAuthFeedback({ text: "Creating account...", error: false });
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
      setAuthFeedback({
        text: err instanceof Error ? err.message : "Registration server unreachable",
        error: true,
      });
    }
  };

  const handleLogout = () => {
    apiLogout();
    localStorage.removeItem("quantum_token");
    setToken(null);
    setCurrentUser(null);
    setAuthFeedback({ text: "Session ended securely.", error: false });
  };

  const handlePowerScaleChange = async (newScale: number, nextPhiTier = phiTier) => {
    setPowerScale(newScale);
    setPhiTier(nextPhiTier);
    try {
      await updatePowerScale(newScale, nextPhiTier);
      setAuthFeedback({
        text: `Scale request sent: ${newScale.toFixed(1)}x at φ-tier 10^${nextPhiTier} (1 EH/s capped)`,
        error: false,
      });
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
    setAuthFeedback({
      text: `Configuring ${selectedPoolForConfig?.name || payload.pool_id}...`,
      error: false,
    });
    try {
      await configurePool(payload);
      if (connectAfterSave) {
        setAuthFeedback({
          text: `Connecting to ${selectedPoolForConfig?.name || payload.pool_id}...`,
          error: false,
        });
        await switchPool({ pool_id: payload.pool_id, capacity_ehs: powerScale, switch: true });
        setAuthFeedback({
          text: `Configured and switched to ${selectedPoolForConfig?.name || payload.pool_id}`,
          error: false,
        });
      } else {
        setAuthFeedback({
          text: `Configured ${selectedPoolForConfig?.name || payload.pool_id}`,
          error: false,
        });
      }
      await getLiveTelemetry();
      setSelectedPoolForConfig(null);
    } catch (err) {
      setAuthFeedback({
        text: err instanceof Error ? err.message : "Pool configuration failed",
        error: true,
      });
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
    setAuthFeedback({ text: `Switching to ${pool.name || pool.pool_id}...`, error: false });
    try {
      await switchPool({ pool_id: pool.pool_id, capacity_ehs: powerScale, switch: true });
      setAuthFeedback({ text: `Switched to ${pool.name || pool.pool_id}`, error: false });
      await getLiveTelemetry();
    } catch (err) {
      setAuthFeedback({
        text: err instanceof Error ? err.message : "Failed to switch pool",
        error: true,
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handlePoolDisconnect = async () => {
    setIsProcessing(true);
    setAuthFeedback({ text: "Disconnecting from pool...", error: false });
    try {
      await disconnectFromPool();
      setAuthFeedback({ text: "Disconnected from pool", error: false });
      await getLiveTelemetry();
    } catch (err) {
      setAuthFeedback({
        text: err instanceof Error ? err.message : "Failed to disconnect",
        error: true,
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleExportAuditMemo = async (format: "json" | "pdf") => {
    const pkg = await buildPortableEvidencePackage({
      decisionId: `decision-${Date.now()}`,
      claimBoundary: fmtText(
        extraordinaryEvidence?.claim_boundary || "Advisory intelligence; no unattended writes",
      ),
      invariants: (extraordinaryEvidence?.invariant_results as Record<string, boolean>) || {
        live_telemetry: isConnected,
        no_unattended_writes: governanceTags.includes("no_unattended_writes"),
        human_approval_required: true,
      },
      evidenceSeal: extraordinaryEvidence?.evidence_seal || null,
      approver: currentUser,
      approvalLog: currentUser
        ? [
            {
              action: "export_audit_memo",
              approvedBy: currentUser.username,
              role: currentUser.role,
              approvedAt: new Date().toISOString(),
            },
          ]
        : [],
      runtimeStatus,
      telemetrySource: health?.telemetry_source,
      backendConnected: isConnected,
      activePoolCount,
      configuredPoolCount,
      activePoolName,
      securityStatus,
      threatLevel: security.threat_level,
      phiResonance: health?.phiResonance,
      governanceTags,
      computeNode,
      residencyStatus,
      jurisdiction,
    });
    downloadEvidencePackage(pkg, format);
    setAuthFeedback({ text: `Signed audit memo exported as ${format.toUpperCase()}.`, error: false });
  };

  const isLoading = !telemetry && !telemetryError;

  return (
    <div
      className={`min-h-screen flex flex-col font-sans transition-colors duration-300 ${isDarkMode ? "dark bg-[#050914] text-slate-100" : "bg-[#F4F1EA] text-[#101828]"}`}
    >
      <div className="fixed right-6 top-4 z-40">
        <SkillModeSelector />
      </div>
      <NetworkToast
        isConnected={isConnected}
        latencyMs={latencyMs}
        isDismissed={isToastDismissed}
        onDismiss={() => setIsToastDismissed(true)}
      />

      <header className="sticky top-0 z-40 border-b border-white/10 mckinsey-blue-bg px-6 py-4 shadow-2xl shadow-slate-950/20 backdrop-blur-xl text-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-3">
            <div className="brand-mark">HYBA</div>
            <div>
              <p className="text-[10px] uppercase tracking-[0.42em] text-blue-100/70">
                Enterprise Command Center
              </p>
              <h1 className="text-base font-black tracking-tight text-white md:text-lg executive-typography">
                Quantum Intelligence Runtime Console
              </h1>
            </div>
            <span className="rounded-full border border-white/15 bg-white/10 px-2.5 py-1 text-[10px] font-mono font-semibold text-white/90">
              v{fmtText(health?.version || "2.0.1")}
            </span>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <SkillModeSelector />
            <div className="status-pill bg-white/10 text-white">
              {isConnected ? (
                <Wifi className="h-3.5 w-3.5 text-emerald-300" />
              ) : (
                <WifiOff className="h-3.5 w-3.5 text-red-300" />
              )}
              <span>{isConnected ? `${latencyMs.toFixed(0)}ms` : "Offline"}</span>
            </div>
            <button
              onClick={() => setIsPollingActive(!isPollingActive)}
              className={`status-pill border ${isPollingActive ? "border-emerald-300/30 bg-emerald-400/15 text-emerald-100" : "border-amber-300/30 bg-amber-400/15 text-amber-100"}`}
            >
              {isPollingActive ? "● Live" : "○ Paused"}
            </button>
            <button
              onClick={getLiveTelemetry}
              disabled={isSyncing}
              className="executive-button bg-white text-[#06162D] shadow-white/10"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isSyncing ? "animate-spin" : ""}`} /> Refresh
            </button>
            <Sparkline data={latencyHistory} />
            <SkillModeSelector />
            <div className="h-6 w-px bg-white/20" />
            <button
              onClick={() => setCurrentView(currentView === "studio" ? "dashboard" : "studio")}
              className={`status-pill border ${currentView === "studio" ? "border-emerald-300/30 bg-emerald-400/15 text-emerald-100" : "border-white/30 bg-white/10 text-white"}`}
              title={currentView === "studio" ? "Return to Dashboard" : "Open Use-Case Studio"}
            >
              <Rocket className="h-3.5 w-3.5" />
              <span>{currentView === "studio" ? "Dashboard" : "Use-Case Studio"}</span>
            </button>
            <button
              onClick={() => setCurrentView(currentView === "jobs" ? "dashboard" : "jobs")}
              className={`status-pill border ${currentView === "jobs" ? "border-blue-300/30 bg-blue-400/15 text-blue-100" : "border-white/30 bg-white/10 text-white"}`}
              title={currentView === "jobs" ? "Return to Dashboard" : "View Mining Jobs"}
            >
              <Clock className="h-3.5 w-3.5" />
              <span>{currentView === "jobs" ? "Dashboard" : "Jobs"}</span>
            </button>
            <button
              onClick={() => setCurrentView(currentView === "history" ? "dashboard" : "history")}
              className={`status-pill border ${currentView === "history" ? "border-purple-300/30 bg-purple-400/15 text-purple-100" : "border-white/30 bg-white/10 text-white"}`}
              title={currentView === "history" ? "Return to Dashboard" : "View Historical Data"}
            >
              <History className="h-3.5 w-3.5" />
              <span>{currentView === "history" ? "Dashboard" : "History"}</span>
            </button>
            <button
              onClick={() =>
                setCurrentView(currentView === "analytics" ? "dashboard" : "analytics")
              }
              className={`status-pill border ${currentView === "analytics" ? "border-cyan-300/30 bg-cyan-400/15 text-cyan-100" : "border-white/30 bg-white/10 text-white"}`}
              title={currentView === "analytics" ? "Return to Dashboard" : "View Analytics"}
            >
              <BarChart3 className="h-3.5 w-3.5" />
              <span>{currentView === "analytics" ? "Dashboard" : "Analytics"}</span>
            </button>
            <button
              onClick={() => setCurrentView(currentView === "portal" ? "dashboard" : "portal")}
              className={`status-pill border ${currentView === "portal" ? "border-indigo-300/30 bg-indigo-400/15 text-indigo-100" : "border-white/30 bg-white/10 text-white"}`}
              title={currentView === "portal" ? "Return to Dashboard" : "Open Customer Portal"}
            >
              <UserCheck className="h-3.5 w-3.5" />
              <span>{currentView === "portal" ? "Dashboard" : "Portal"}</span>
            </button>
            <button
              onClick={() => setCurrentView(currentView === "ciaas" ? "dashboard" : "ciaas")}
              className={`status-pill border ${currentView === "ciaas" ? "border-cyan-300/30 bg-cyan-400/15 text-cyan-100" : "border-white/30 bg-white/10 text-white"}`}
              title={currentView === "ciaas" ? "Return to Dashboard" : "Open CIaaS Services"}
            >
              <Brain className="h-3.5 w-3.5" />
              <span>{currentView === "ciaas" ? "Dashboard" : "CIaaS"}</span>
            </button>
            <button
              onClick={() => setCurrentView(currentView === "qaas" ? "dashboard" : "qaas")}
              className={`status-pill border ${currentView === "qaas" ? "border-purple-300/30 bg-purple-400/15 text-purple-100" : "border-white/30 bg-white/10 text-white"}`}
              title={currentView === "qaas" ? "Return to Dashboard" : "Open QaaS Computers"}
            >
              <Atom className="h-3.5 w-3.5" />
              <span>{currentView === "qaas" ? "Dashboard" : "QI API"}</span>
            </button>
            {(isAdmin || isExecutive) && (
              <>
                <div className="h-6 w-px bg-white/20" />
                <button
                  onClick={() =>
                    setCurrentView(currentView === "dashboard" ? "admin" : "dashboard")
                  }
                  className={`status-pill border ${currentView === "admin" ? "border-emerald-300/30 bg-emerald-400/15 text-emerald-100" : "border-white/30 bg-white/10 text-white"}`}
                  title={currentView === "admin" ? "Return to Dashboard" : "Access Admin Panel"}
                >
                  <ShieldCheck className="h-3.5 w-3.5" />
                  <span>{currentView === "admin" ? "Dashboard" : "Admin"}</span>
                </button>
                {isExecutive && (
                  <button
                    onClick={() =>
                      setCurrentView(currentView === "executive" ? "dashboard" : "executive")
                    }
                    className={`status-pill border ${currentView === "executive" ? "border-amber-300/30 bg-amber-400/15 text-amber-100" : "border-white/30 bg-white/10 text-white"}`}
                    title={
                      currentView === "executive"
                        ? "Return to Dashboard"
                        : "Access Executive Dashboard"
                    }
                  >
                    <Crown className="h-3.5 w-3.5" />
                    <span>{currentView === "executive" ? "Dashboard" : "Executive"}</span>
                  </button>
                )}
              </>
            )}
            <button
              onClick={toggleTheme}
              className="rounded-full bg-white/10 p-2 text-white transition hover:bg-white/20"
              aria-label="Toggle color theme"
            >
              {isDarkMode ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-7xl flex-1 flex-col gap-6 px-6 py-6">
        {currentView === "admin" ? (
          <AdminPanel token={token} />
        ) : currentView === "executive" ? (
          <HybaAdminDashboard
            token={token}
            telemetry={telemetry}
            pools={pools}
            activePoolName={activePoolName}
            isConnected={isConnected}
            latencyMs={latencyMs}
          />
        ) : currentView === "jobs" ? (
          <MiningJobsSection telemetry={telemetry} pools={pools} />
        ) : currentView === "history" ? (
          <HistoricalDataSection telemetry={telemetry} />
        ) : currentView === "analytics" ? (
          <AnalyticsSection telemetry={telemetry} pools={pools} />
        ) : currentView === "portal" ? (
          <CustomerPortal />
        ) : currentView === "studio" ? (
          <ImportedUseCaseStudio />
        ) : currentView === "ciaas" ? (
          <CIaaSServiceManager token={token} />
        ) : currentView === "qaas" ? (
          <QaaSComputerManager token={token} />
        ) : (
          <>
            <ExecutiveSummary
              readinessScore={readinessScore}
              runtimeStatus={runtimeStatus}
              securityStatus={securityStatus}
              activePoolCount={activePoolCount}
              latencyMs={latencyMs}
            />
            <section className="executive-hero overflow-hidden rounded-[2rem] border border-white/30 bg-white/80 p-6 shadow-2xl shadow-slate-900/10 backdrop-blur md:p-8">
              <div className="grid gap-8 lg:grid-cols-[1.15fr_0.85fr] lg:items-center">
                <div className="relative z-10">
                  <div className="mb-5 flex flex-wrap items-center gap-2">
                    <span className="eyebrow">
                      <Landmark className="h-3.5 w-3.5" /> Executive Dashboard
                    </span>
                    <span className="eyebrow">
                      <Rocket className="h-3.5 w-3.5" /> Production-Ready
                    </span>
                  </div>
                  <h2 className="max-w-3xl text-4xl font-black tracking-[-0.04em] text-slate-950 md:text-6xl executive-typography">
                    Sovereign Quantum Intelligence Execution
                  </h2>
                  <p className="mt-5 max-w-2xl text-base leading-8 text-slate-600 md:text-lg">
                    Institutional-caliber control surface for substrate-independent Quantum
                    Intelligence: evidence-sealed execution, PULVINI φ-memory, Salamander
                    regeneration, authenticated tenancy, and usage-metered enterprise operation.
                  </p>
                  <div className="mt-8 grid gap-3 sm:grid-cols-3">
                    {operatingPrinciples.map((item) => (
                      <div key={item.label} className="kpi-card rounded-xl p-4">
                        <p className="text-xs font-black uppercase tracking-[0.18em] text-slate-900">
                          {item.label}
                        </p>
                        <p className="mt-2 text-xs leading-5 text-slate-500">{item.detail}</p>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="relative z-10 rounded-[1.5rem] border border-slate-200 mckinsey-blue-bg p-5 text-white shadow-2xl">
                  <div className="flex items-center justify-between border-b border-white/10 pb-4">
                    <div>
                      <p className="text-[10px] uppercase tracking-[0.3em] text-blue-200/70">
                        Executive Readiness Score
                      </p>
                      <p className="mt-1 text-3xl font-black executive-typography">
                        {readinessScore}
                        <span className="text-base text-white/50">/100</span>
                      </p>
                    </div>
                    <Gauge className="h-10 w-10 text-[#C5A55A]" />
                  </div>
                  <div className="mt-5 h-3 rounded-full bg-white/10">
                    <div
                      className="h-3 rounded-full bg-gradient-to-r from-[#003666] via-[#C5A55A] to-[#16A34A]"
                      style={{ width: `${readinessScore}%` }}
                    />
                  </div>
                  <div className="mt-5 grid gap-3 text-xs">
                    <ReadinessLine
                      label="Runtime"
                      value={runtimeStatus.toUpperCase()}
                      positive={["OK", "HEALTHY"].includes(runtimeStatus.toUpperCase())}
                    />
                    <ReadinessLine
                      label="Security"
                      value={securityStatus.toUpperCase()}
                      positive={!securityStatus.toLowerCase().includes("error")}
                    />
                    <ReadinessLine
                      label="Active pool"
                      value={activePoolName}
                      positive={activePoolName !== UNAVAILABLE}
                    />
                    <ReadinessLine
                      label="Telemetry"
                      value={isConnected ? `${latencyMs.toFixed(0)}ms latency` : "Disconnected"}
                      positive={isConnected}
                    />
                  </div>
                </div>
              </div>
            </section>

            <ImportedUseCaseStudio />
            <DecisionCockpit stability={reasoningStability} previousStability={previousReasoningStability} veracity={reasoningVeracity} telemetrySource={fmtText(health?.telemetry_source)} />
            <section className="grid grid-cols-1 gap-4 md:grid-cols-4">
              {isLoading ? (
                [1, 2, 3, 4].map((i) => (
                  <div key={i} className="kpi-card rounded-xl p-5">
                    <Skeleton width="80px" height="12px" />
                    <div className="mt-3">
                      <Skeleton width="60%" height="28px" />
                    </div>
                  </div>
                ))
              ) : (
                <>
                  <MetricCard
                    label="Runtime status"
                    value={runtimeStatus.toUpperCase()}
                    icon={<Activity className="h-4 w-4" />}
                    status={runtimeStatus}
                  />
                  <MetricCard
                    label="Telemetry source"
                    value={fmtText(health?.telemetry_source)}
                    icon={<Database className="h-4 w-4" />}
                  />
                  <MetricCard
                    label="Active pool"
                    value={activePoolName}
                    icon={<RadioTower className="h-4 w-4" />}
                  />
                  <MetricCard
                    label="Backend latency"
                    value={isConnected ? `${latencyMs.toFixed(0)} ms` : UNAVAILABLE}
                    icon={
                      isConnected ? <Wifi className="h-4 w-4" /> : <WifiOff className="h-4 w-4" />
                    }
                  />
                </>
              )}
            </section>

            {telemetryError && !isLoading && (
              <ErrorState message={telemetryError} onRetry={getLiveTelemetry} />
            )}

            <section className="grid grid-cols-1 gap-4 lg:grid-cols-3">
              <MetricExplainerCard
                metricKey="substrate_coherence"
                value={`Runtime: ${runtimeStatus.toUpperCase()}`}
              />
              <MetricExplainerCard
                metricKey="phi_resonance"
                value={`φ alignment: ${fmtPct(health?.phiResonance)}`}
              />
              <MetricExplainerCard metricKey="evidence_seal" value={`Seal: ${extraordinarySeal}`} />
            </section>

            <ProofExplainer
              seal={extraordinarySeal}
              invariantSummary={`${extraordinaryInvariantCount} / ${extraordinaryInvariantTotal}`}
              source={fmtText(health?.telemetry_source)}
            />

            <section className="grid grid-cols-1 gap-6 lg:grid-cols-3">
              <Panel
                title="Mining telemetry"
                eyebrow="Network operations"
                icon={<Database className="h-4 w-4" />}
                isLoading={isLoading}
                rows={6}
              >
                <MetricRow label="Block height" value={fmtNum(systemMetrics.blockHeight, 0)} />
                <MetricRow label="Hashrate (EH/s)" value={fmtNum(systemMetrics.currentHashrate)} />
                <MetricRow
                  label="Power consumption"
                  value={fmtNum(systemMetrics.powerConsumption)}
                />
                <MetricRow
                  label="Network difficulty"
                  value={fmtNum(systemMetrics.networkDifficulty)}
                />
                <MetricRow
                  label="Difficulty target"
                  value={fmtText(systemMetrics.difficultyTarget)}
                />
                <MetricRow label="System health" value={fmtText(systemMetrics.system_health)} />
              </Panel>
              <div className="space-y-4">
                <MetricExplainerCard metric="substrate_coherence" value={fmtPct(health?.quantumCoherence)} />
              <Panel
                title="Quantum Intelligence state"
                eyebrow="Substrate coherence"
                icon={<Cpu className="h-4 w-4" />}
                isLoading={isLoading}
                rows={6}
              >
                <MetricRow label="Basis coherence" value={fmtPct(health?.quantumCoherence)} />
                <MetricRow label="Phi phase alignment" value={fmtPct(health?.phiResonance)} />
                <MetricRow
                  label="Modeled basis factor"
                  value={fmtNum(health?.quantumSpeedupFactor)}
                />
                <MetricRow label="Actual speedup" value={fmtNum(health?.actualSpeedupFactor)} />
                <MetricRow label="Power scale" value={`${powerScale.toFixed(1)}x`} />
                <MetricRow label="φ-tier" value={`10^${phiTier}`} />
                <MetricRow label="EH/s cap" value="1.0" />
                <input
                  type="range"
                  min="0.1"
                  max="10.0"
                  step="0.1"
                  value={powerScale}
                  onChange={(e) => handlePowerScaleChange(parseFloat(e.target.value))}
                  className="mt-3 h-2 w-full cursor-pointer appearance-none rounded-lg"
                  style={{ accentColor: THEME.colors.clicquotGold }}
                  aria-label="Power scale control"
                />
                <select
                  value={phiTier}
                  onChange={(e) => handlePowerScaleChange(powerScale, parseInt(e.target.value, 10))}
                  className="mt-3 w-full rounded-lg border border-[#E2E4E9] bg-white px-3 py-2 text-xs font-mono text-[#1A1A1E]"
                  aria-label="Phi tier control"
                >
                  {PHI_TIERS.map((tier) => (
                    <option key={tier} value={tier}>{`10^${tier} φ-tier`}</option>
                  ))}
                </select>
              </Panel>
              </div>
              <Panel
                title="Runtime integration"
                eyebrow="Risk and control"
                icon={<ShieldCheck className="h-4 w-4" />}
                isLoading={isLoading}
                rows={6}
              >
                <MetricRow label="AI state" value={fmtText(consciousness.status)} />
                <MetricRow
                  label="Integrated information"
                  value={fmtNum(consciousness.integrated_information as NullableNumber)}
                />
                <MetricRow label="Security status" value={securityStatus} />
                <MetricRow label="Threat level" value={fmtText(security.threat_level)} />
                <MetricRow label="Pools configured" value={fmtNum(configuredPoolCount, 0)} />
                <MetricRow label="Active pools" value={fmtNum(activePoolCount, 0)} />
              </Panel>
              <div className="space-y-4">
                <EvidenceBoundAnswer
                  evidenceSeal={extraordinarySeal}
                  claimBoundary={fmtText(extraordinaryEvidence?.claim_boundary || "Advisory intelligence; not autonomous execution")}
                  invariantStatus={extraordinaryEvidence?.all_invariants_passed ? "Passed" : extraordinaryEvidence ? "Fail-closed" : undefined}
                  dataSource={fmtText(health?.telemetry_source)}
                />
              <Panel
                title="Proof seal telemetry"
                eyebrow="Extraordinary claims"
                icon={<FileWarning className="h-4 w-4" />}
                isLoading={isLoading}
                rows={7}
              >
                <MetricRow label="Evidence seal" value={extraordinarySeal} />
                <MetricRow
                  label="Invariant status"
                  value={
                    extraordinaryEvidence?.all_invariants_passed
                      ? "PASS"
                      : extraordinaryEvidence
                        ? "FAIL-CLOSED"
                        : UNAVAILABLE
                  }
                />
                <MetricRow
                  label="Invariant checks"
                  value={`${extraordinaryInvariantCount} / ${extraordinaryInvariantTotal}`}
                />
                <MetricRow
                  label="Claim contracts"
                  value={fmtNum(extraordinaryEvidence?.claims?.length as NullableNumber, 0)}
                />
                <MetricRow
                  label="Millennium ops"
                  value={fmtNum(
                    extraordinaryEvidence?.millennium_problems?.length as NullableNumber,
                    0,
                  )}
                />
                <MetricRow
                  label="φ substrate"
                  value={fmtNum(extraordinaryEvidence?.phi as NullableNumber, 6)}
                />
                <MetricRow
                  label="Seal policy"
                  value={
                    extraordinaryEvidence?.adversarial_contract?.seal_all_evidence_packets
                      ? "ENFORCED"
                      : "UNAVAILABLE"
                  }
                />
              </Panel>
              </div>
              <Panel
                title="Unitary shield"
                eyebrow="Stabilizer integrity"
                icon={<ShieldCheck className="h-4 w-4" />}
                isLoading={isLoading}
                rows={8}
              >
                <MetricRow
                  label="Operating mode"
                  value={fmtText(stabilizerMonitor.operating_mode)}
                />
                <MetricRow
                  label="Confidence"
                  value={fmtPct(stabilizerMonitor.confidence as NullableNumber)}
                />
                <MetricRow
                  label="Check frequency"
                  value={fmtPct(stabilizerMonitor.check_frequency as NullableNumber)}
                />
                <MetricRow
                  label="Syndrome weight"
                  value={fmtNum(stabilizerMonitor.syndrome_weight as NullableNumber, 0)}
                />
                <MetricRow
                  label="Ancillas active/max"
                  value={`${fmtNum(ancillaTrapPool.active_ancillas as NullableNumber, 0)} / ${fmtNum(ancillaTrapPool.max_ancilla_pool as NullableNumber, 0)}`}
                />
                <MetricRow
                  label="Traps active/retired"
                  value={`${fmtNum(ancillaTrapPool.active_traps as NullableNumber, 0)} / ${fmtNum(ancillaTrapPool.retired_traps as NullableNumber, 0)}`}
                />
                <MetricRow
                  label="Permutation checksum"
                  value={fmtNum(stabilizerMonitor.pool_permutation_checksum as NullableNumber, 0)}
                />
                <MetricRow label="Sanitized" value={stabilizerMonitor.sanitized ? "YES" : "NO"} />
              </Panel>
            </section>

            <section className="grid grid-cols-1 gap-6">
              <SovereignCommandPost />
              <SovereignGenesisPanel />
            </section>

            <section className="grid grid-cols-1 gap-6 lg:grid-cols-[1.2fr_0.8fr]">
              <Panel
                title="Stratum mining pools"
                eyebrow="Authenticated execution"
                icon={<Server className="h-4 w-4" />}
                isLoading={isLoading && pools.length === 0}
                rows={4}
              >
                {!isLoading && pools.length === 0 ? (
                  <EmptyState
                    message="No pool telemetry available from backend."
                    icon={<Server className="h-8 w-8" />}
                  />
                ) : (
                  <div className="grid gap-3 xl:grid-cols-2">
                    {pools.map((pool, idx) => {
                      const isActive = Boolean(
                        pool.is_active ||
                        pool.connection_state?.toLowerCase() === "connected" ||
                        pool.status?.toLowerCase() === "connected",
                      );
                      return (
                        <div
                          key={pool.pool_id || pool.name || idx}
                          className="rounded-2xl border border-slate-200 bg-white/80 p-4 shadow-sm transition hover:-translate-y-0.5 hover:shadow-lg"
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div className="min-w-0">
                              <span className="block truncate text-sm font-black text-slate-950">
                                {fmtText(pool.name)}
                              </span>
                              <span className="mt-1 block truncate font-mono text-[10px] text-slate-500">
                                {fmtText(pool.url)}
                              </span>
                            </div>
                            <PoolStatusBadge status={pool.status || pool.connection_state} />
                          </div>
                          <div className="mt-4 grid grid-cols-2 gap-2 rounded-xl border border-slate-100 bg-slate-50 p-3 text-[10px] text-slate-600">
                            <span>
                              Mode{" "}
                              <strong className="block truncate text-slate-900">
                                {fmtText(pool.credential_mode)}
                              </strong>
                            </span>
                            <span>
                              Configured{" "}
                              <strong className="block text-slate-900">
                                {pool.configured ? "YES" : "NO"}
                              </strong>
                            </span>
                            <span>
                              Latency{" "}
                              <strong className="block text-slate-900">
                                {fmtNum(pool.performance?.latency_ms)} ms
                              </strong>
                            </span>
                            <span>
                              Shares{" "}
                              <strong className="block text-slate-900">
                                {fmtNum(pool.performance?.shares_submitted, 0)}
                              </strong>
                            </span>
                          </div>
                          <div className="mt-4 grid grid-cols-2 gap-2">
                            <button
                              onClick={() => setSelectedPoolForConfig(pool)}
                              disabled={isProcessing}
                              className="control-button bg-slate-950 text-white"
                            >
                              Configure
                            </button>
                            {isActive ? (
                              <button
                                onClick={handlePoolDisconnect}
                                disabled={isProcessing}
                                className="control-button bg-red-600 text-white"
                              >
                                Disconnect
                              </button>
                            ) : (
                              <button
                                onClick={() => handlePoolSwitch(pool)}
                                disabled={isProcessing}
                                className={`control-button text-white ${pool.configured ? "bg-[#002147]" : "bg-amber-600"}`}
                              >
                                {pool.configured ? "Switch" : "Setup"}
                              </button>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </Panel>

              <div className="grid gap-6">
                <Panel
                  title="Operator identity"
                  eyebrow="Access control"
                  icon={<UserCheck className="h-4 w-4" />}
                  isLoading={false}
                >
                  {currentUser ? (
                    <div className="space-y-4 font-mono text-xs">
                      <div className="rounded-2xl border border-green-200 bg-green-50 p-4">
                        <div className="mb-3 flex items-center gap-2 text-green-800">
                          <CheckCircle2 className="h-4 w-4" />
                          <span className="font-bold uppercase tracking-[0.18em]">
                            Authenticated
                          </span>
                        </div>
                        <MetricRow label="Identity" value={currentUser.username} />
                        <MetricRow label="Role" value={currentUser.role} />
                      </div>
                      <button
                        onClick={handleLogout}
                        className="control-button w-full bg-red-600 text-white"
                      >
                        <LogOut className="h-3.5 w-3.5" /> Log out
                      </button>
                    </div>
                  ) : (
                    <form
                      onSubmit={isRegisterMode ? handleRegister : handleLogin}
                      className="space-y-3"
                    >
                      <AuthInput
                        id="operator-handle"
                        label="Operator Handle"
                        value={usernameInput}
                        setValue={setUsernameInput}
                        type="text"
                        placeholder="Enter your operator handle"
                      />
                      <AuthInput
                        id="operator-password"
                        label="Password"
                        value={passwordInput}
                        setValue={setPasswordInput}
                        type="password"
                        placeholder="Enter your password"
                      />
                      <div className="grid grid-cols-2 gap-2 pt-1">
                        <button type="submit" className="control-button bg-[#002147] text-white">
                          {isRegisterMode ? (
                            <UserPlus className="h-3.5 w-3.5" />
                          ) : (
                            <LogIn className="h-3.5 w-3.5" />
                          )}
                          {isRegisterMode ? "Register" : "Log in"}
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            setIsRegisterMode(!isRegisterMode);
                            clearAuthFeedback();
                          }}
                          className="control-button border border-slate-200 bg-white text-slate-900"
                        >
                          {isRegisterMode ? "← Log in" : "Sign up →"}
                        </button>
                      </div>
                    </form>
                  )}
                  {authFeedback && <Feedback feedback={authFeedback} />}
                </Panel>

                <Panel
                  title="Forensic evidence"
                  eyebrow="Deployment controls"
                  icon={<Scale className="h-4 w-4" />}
                  isLoading={false}
                >
                  <SovereigntyResidencyBadges
                    computeNode={computeNode}
                    residencyStatus={residencyStatus}
                    jurisdiction={jurisdiction}
                  />
                  <div className="mb-4 grid grid-cols-2 gap-2">
                    <button
                      type="button"
                      onClick={() => handleExportAuditMemo("pdf")}
                      className="control-button bg-[#002147] text-white"
                    >
                      Export Audit Memo PDF
                    </button>
                    <button
                      type="button"
                      onClick={() => handleExportAuditMemo("json")}
                      className="control-button border border-slate-200 bg-white text-slate-900"
                    >
                      Export Signed JSON
                    </button>
                  </div>
                  <GovernanceDashboard signals={governanceSignals} />
                  <div className="mt-4 space-y-3">
                    {operatorCommandEvidence.map((item) => (
                      <EvidenceItem
                        key={item.title}
                        icon={item.icon}
                        title={item.title}
                        detail={item.detail}
                      />
                    ))}
                  </div>
                </Panel>
              </div>
            </section>

            <Panel
              title="Product catalog"
              eyebrow="Commercial surface"
              icon={<Database className="h-4 w-4" />}
              isLoading={false}
            >
              {products.length === 0 ? (
                <EmptyState
                  message="No catalog records available from backend."
                  icon={<Database className="h-8 w-8" />}
                />
              ) : (
                <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                  {products.map((product) => (
                    <div
                      key={product.id || product.name}
                      className="rounded-2xl border border-slate-200 bg-white/80 p-4 shadow-sm"
                    >
                      <h5 className="truncate text-sm font-black text-slate-950">
                        {fmtText(product.name)}
                      </h5>
                      <p className="mt-2 text-xs leading-6 text-slate-500">
                        {fmtText(product.description)}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </Panel>
          </>
        )}
        <section className="mx-auto mt-8 grid max-w-7xl grid-cols-1 gap-4 px-6 md:grid-cols-3">
          <MetricExplainerCard metricKey="substrate_coherence" />
          <MetricExplainerCard metricKey="evidence_seal" />
          <ClaimBoundaryBadge />
        </section>
      </main>

      <footer className="mt-8 shrink-0 border-t border-white/10 bg-[#06162D] px-6 py-6 text-white/70">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 text-[10px] font-mono md:flex-row">
          <span>HYBA PRODUCTION RUNTIME WORKSPACE</span>
          <span>© 2026 HYBA GROUP</span>
          <span className="flex items-center gap-1 text-[#C5A55A]">
            <ShieldCheck className="h-3.5 w-3.5" /> {realTelemetryContract}
          </span>
        </div>
      </footer>

      {selectedPoolForConfig && (
        <PoolSecretsConfig
          pool={selectedPoolForConfig}
          onClose={() => setSelectedPoolForConfig(null)}
          onSave={handlePoolSave}
        />
      )}

      {/* AI Assistant - Always available when authenticated */}
      {token && currentUser && (
        <AIAssistant
          token={token}
          userRole={currentUser.role}
          telemetryData={telemetry}
          onCommand={(command) => {
            console.log("AI Command:", command);
            // Handle AI-triggered actions
            if (command === "refresh_telemetry") {
              getLiveTelemetry();
            }
          }}
        />
      )}
    </div>
  );
}

function StrategicDecisionWorkbench({
  latencyMs,
  phiResonance,
  quantumCoherence,
  telemetrySource,
}: {
  latencyMs: number;
  phiResonance?: number;
  quantumCoherence?: number;
  telemetrySource: string;
}) {
  const { skillMode, isExpertMode } = useSkillMode();
  const [latencyStress, setLatencyStress] = useState(50);
  const [demandShock, setDemandShock] = useState(20);
  const [certainty, setCertainty] = useState(72);
  const stressedLatency = latencyMs * (1 + latencyStress / 100);
  const coherence = typeof quantumCoherence === "number" ? quantumCoherence : 0.74;
  const resonance = typeof phiResonance === "number" ? phiResonance : 0.68;
  const stability = clamp((coherence * 55 + resonance * 45) - latencyStress * 0.18 - demandShock * 0.1);
  const standardCost = 1 + demandShock / 100;
  const causalCost = standardCost * (1 + certainty / 100) * (1 + latencyStress / 250);
  const showExpertTrace = isExpertMode || skillMode === "analyst";
  const agents = [
    { name: "Manifold patterns", role: "Pattern field", signal: "Detects topology shift under load", weight: 34 },
    { name: "PULVINI memory", role: "Context memory", signal: "Compares current state with sealed prior runs", weight: 29 },
    { name: "Salamander regeneration", role: "Recovery planner", signal: "Produces rollback and safe-remediation paths", weight: 22 },
    { name: "Governance guard", role: "Approval boundary", signal: "Keeps output proposal-only until signed", weight: 15 },
  ];
  const dag = [
    ["Live telemetry", "Latency, coherence, resonance, source provenance"],
    ["Counterfactual stress", `Latency +${latencyStress}% · Demand +${demandShock}%`],
    ["Causal inference", "Compare operational drivers against evidence invariants"],
    ["Recommendation", stability > 65 ? "Proceed with monitored intervention" : "Defer action and request human triage"],
    ["Human approval", "No unattended write; signed approval required"],
  ];

  return (
    <section className="rounded-[2rem] border border-slate-200 bg-white/95 p-6 shadow-xl" data-testid="strategic-decision-workbench">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="eyebrow"><SlidersHorizontal className="h-3.5 w-3.5" /> Counterfactual Sandbox</p>
          <h2 className="mt-2 text-2xl font-black text-slate-950">Stress-test the recommendation before anyone acts.</h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
            Manipulate operational assumptions and HYBA recalculates the predicted outcome, causal chain, collaborating sub-intelligences, and cost of certainty from live telemetry ({telemetrySource}).
          </p>
        </div>
        <span className="rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-bold text-amber-800">Simulation only · proposal boundary</span>
      </div>

      <div className="mt-6 grid gap-5 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="space-y-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <ScenarioSlider label="What if latency spikes?" value={latencyStress} setValue={setLatencyStress} suffix="%" />
          <ScenarioSlider label="What if demand rises?" value={demandShock} setValue={setDemandShock} suffix="%" />
          <ScenarioSlider label="Certainty target" value={certainty} setValue={setCertainty} suffix="%" />
          <div className="grid gap-3 sm:grid-cols-3">
            <TrustFact label="Predicted stability" value={`${stability.toFixed(0)} / 100`} />
            <TrustFact label="Stressed latency" value={`${stressedLatency.toFixed(0)} ms`} />
            <TrustFact label="Recommended posture" value={stability > 65 ? "Monitor" : "Escalate"} />
          </div>
        </div>

        <div className="rounded-2xl border border-blue-100 bg-blue-50/60 p-4">
          <div className="flex items-center gap-2 text-blue-950">
            <Network className="h-5 w-5" />
            <h3 className="font-black">Multi-agent war room</h3>
          </div>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            {agents.map((agent) => (
              <div key={agent.name} className="rounded-2xl border border-white bg-white/90 p-4">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-black text-slate-950">{agent.name}</p>
                  <span className="rounded-full bg-blue-100 px-2 py-1 font-mono text-[10px] text-blue-800">{agent.weight}%</span>
                </div>
                <p className="mt-1 text-[11px] font-bold uppercase tracking-[0.14em] text-slate-400">{agent.role}</p>
                <p className="mt-2 text-xs leading-5 text-slate-600">{agent.signal}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-5 grid gap-5 lg:grid-cols-[1.15fr_0.85fr]">
        <div className="rounded-2xl border border-slate-200 bg-white p-4">
          <div className="flex items-center gap-2 text-slate-950">
            <GitBranch className="h-5 w-5" />
            <h3 className="font-black">Causal logic trace</h3>
          </div>
          <div className="mt-4 grid gap-3">
            {dag.map(([title, detail], index) => (
              <div key={title} className="grid gap-3 rounded-2xl border border-slate-100 bg-slate-50 p-3 md:grid-cols-[2rem_1fr]">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-950 font-mono text-xs font-bold text-white">{index + 1}</div>
                <div>
                  <p className="text-sm font-black text-slate-950">{title}</p>
                  <p className="mt-1 text-xs leading-5 text-slate-600">{detail}</p>
                </div>
              </div>
            ))}
          </div>
          {showExpertTrace && (
            <p className="mt-3 rounded-xl border border-purple-100 bg-purple-50 p-3 font-mono text-[11px] text-purple-950">
              Expert trace: coherence={coherence.toFixed(4)} · φ-resonance={resonance.toFixed(4)} · counterfactual_stability={stability.toFixed(2)}
            </p>
          )}
        </div>

        <div className="rounded-2xl border border-emerald-100 bg-emerald-50 p-4">
          <div className="flex items-center gap-2 text-emerald-950">
            <WalletCards className="h-5 w-5" />
            <h3 className="font-black">Cost of certainty</h3>
          </div>
          <p className="mt-2 text-sm leading-6 text-emerald-900">
            High-resonance quantum-causal simulation is deliberately more expensive than a standard computation because it keeps the claim evidence-bound and auditable.
          </p>
          <div className="mt-4 grid gap-3">
            <TrustFact label="Standard computation" value={`${standardCost.toFixed(2)} capacity units`} />
            <TrustFact label="Quantum-causal run" value={`${causalCost.toFixed(2)} capacity units`} />
            <TrustFact label="Certainty premium" value={`${((causalCost / standardCost - 1) * 100).toFixed(0)}%`} />
          </div>
        </div>
      </div>
    </section>
  );
}

function ScenarioSlider({ label, value, setValue, suffix }: { label: string; value: number; setValue: (value: number) => void; suffix: string }) {
  return (
    <label className="block">
      <span className="flex items-center justify-between text-xs font-bold uppercase tracking-[0.14em] text-slate-600">
        {label}
        <strong className="font-mono text-slate-950">{value}{suffix}</strong>
      </span>
      <input type="range" min="0" max="100" value={value} onChange={(event) => setValue(Number(event.target.value))} className="mt-2 w-full" />
    </label>
  );
}

function TrustFact({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-white/70 bg-white/85 p-3">
      <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">{label}</p>
      <p className="mt-1 font-mono text-xs font-bold text-slate-950">{value}</p>
    </div>
  );
}

function UseCaseStudio() {
  const { skillMode } = useSkillMode();
  const profileLabel = SKILL_MODE_LABELS[skillMode];
  const useCases = [
    { intent: "Explain a board-level decision", capability: "explain + evidence package", action: "Prepare decision memo", risk: "Approval required" },
    { intent: "Simulate an intervention", capability: "counterfactual + optimize", action: "Run simulation only", risk: "No production write" },
    { intent: "Detect operational risk", capability: "orchestrate + substrate_health", action: "Propose remediation", risk: "Blast radius review" },
    { intent: "Audit an AI recommendation", capability: "governance_audit + evidence package", action: "Collect proof surface", risk: "Auditor sign-off" },
  ];

  return (
    <section className="space-y-6" data-testid="use-case-studio">
      <div className="rounded-[2rem] border border-white/40 bg-white/90 p-6 shadow-xl">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="eyebrow">Adaptive Intelligence Experience Layer</p>
            <h2 className="mt-2 text-3xl font-black text-slate-950">Start from intent, not quantum controls.</h2>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
              HYBA maps plain-language enterprise intent to prediction, explanation, counterfactuals, optimization, regeneration, and evidence-bound audit workflows. Current lens: <strong>{profileLabel}</strong>.
            </p>
          </div>
          <ClaimBoundaryBadge boundary="proposal_only by default" />
        </div>
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          {useCases.map((item) => (
            <article key={item.intent} className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
              <h3 className="font-bold text-slate-950">I want to {item.intent.toLowerCase()}.</h3>
              <dl className="mt-3 space-y-2 text-sm text-slate-700">
                <div><dt className="font-semibold text-slate-900">HYBA routes to</dt><dd>{item.capability}</dd></div>
                <div><dt className="font-semibold text-slate-900">Safe next action</dt><dd>{item.action}</dd></div>
                <div><dt className="font-semibold text-slate-900">Governance</dt><dd>{item.risk}</dd></div>
              </dl>
            </article>
          ))}
        </div>
      </div>
      <div className="grid gap-4 lg:grid-cols-3">
        <MetricExplainerCard metricKey="substrate_coherence" value="Strong = safe to simulate" />
        <MetricExplainerCard metricKey="evidence_seal" value="Required for buyer-facing trust" />
        <MetricExplainerCard metricKey="claim_boundary" value="Advisory until approved" />
      </div>
      <EvidenceBoundAnswer />
    </section>
  );
}

function AuthInput({
  id,
  label,
  value,
  setValue,
  type,
  placeholder,
}: {
  id: string;
  label: string;
  value: string;
  setValue: (value: string) => void;
  type: string;
  placeholder: string;
}) {
  const inputId = `auth-${label.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`;
  return (
    <div className="space-y-2">
      <label
        htmlFor={inputId}
        className="text-[10px] font-mono font-bold uppercase tracking-[0.18em] text-slate-500"
      >
        {label}
      </label>
      <input
        id={inputId}
        type={type}
        required
        placeholder={placeholder}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        className="w-full rounded-xl border border-slate-200 bg-slate-50 p-3 font-mono text-xs outline-none transition focus:border-[#002147] focus:bg-white focus:ring-4 focus:ring-blue-100"
      />
    </div>
  );
}

function Feedback({ feedback }: { feedback: { text: string; error: boolean } }) {
  return (
    <div
      className={`mt-3 flex items-center gap-2 rounded-xl border p-3 text-xs ${feedback.error ? "border-red-200 bg-red-50 text-red-900" : "border-green-200 bg-green-50 text-green-900"}`}
      role="alert"
    >
      {feedback.error ? (
        <AlertCircle className="h-3.5 w-3.5 shrink-0" />
      ) : (
        <CheckCircle2 className="h-3.5 w-3.5 shrink-0" />
      )}
      <span>{feedback.text}</span>
    </div>
  );
}

function PoolStatusBadge({ status }: { status?: string }) {
  const colorMap: Record<string, string> = {
    connected: THEME.colors.success,
    active: THEME.colors.success,
    configured: THEME.colors.success,
    not_configured: THEME.colors.warning,
    disconnected: THEME.colors.error,
    error: THEME.colors.error,
    connecting: THEME.colors.warning,
    reconnecting: THEME.colors.warning,
  };
  const color = status ? colorMap[status.toLowerCase()] || THEME.colors.slate : THEME.colors.slate;
  return (
    <span
      className="rounded-full border px-2 py-1 text-[9px] font-black uppercase tracking-[0.14em]"
      style={{ color, borderColor: color, backgroundColor: `${color}15` }}
    >
      {fmtText(status)}
    </span>
  );
}

function ReadinessLine({
  label,
  value,
  positive,
}: {
  label: string;
  value: string;
  positive: boolean;
}) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-xl bg-white/5 px-3 py-2">
      <span className="text-white/55">{label}</span>
      <span
        className={`max-w-[60%] truncate font-mono font-bold ${positive ? "text-emerald-300" : "text-amber-300"}`}
      >
        {value}
      </span>
    </div>
  );
}

function MetricCard({
  label,
  value,
  icon,
  status,
}: {
  label: string;
  value: string;
  icon: React.ReactNode;
  status?: string;
}) {
  const normalized = status?.toLowerCase();
  const statusColor =
    normalized === "ok" || normalized === "healthy"
      ? THEME.colors.success
      : normalized === "unavailable" || normalized === "error"
        ? THEME.colors.error
        : THEME.colors.mckinseyBlue;
  return (
    <div className="kpi-card group rounded-xl p-5 transition hover:-translate-y-0.5 hover:shadow-lg">
      <div className="mb-3 flex items-center justify-between">
        <span className="text-[10px] font-mono font-bold uppercase tracking-[0.18em] text-slate-500">
          {label}
        </span>
        <div className="rounded-full bg-slate-50 p-2" style={{ color: statusColor }}>
          {icon}
        </div>
      </div>
      <div
        className="truncate text-xl font-black tracking-tight"
        style={{ color: status ? statusColor : THEME.colors.ink }}
      >
        {value}
      </div>
    </div>
  );
}

function Panel({
  title,
  eyebrow,
  icon,
  children,
  isLoading,
  rows = 4,
}: {
  title: string;
  eyebrow?: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  isLoading?: boolean;
  rows?: number;
}) {
  return (
    <div className="overflow-hidden rounded-[1.5rem] border border-slate-200 bg-white/90 shadow-sm backdrop-blur">
      <div className="flex items-center gap-3 border-b border-slate-100 bg-gradient-to-r from-slate-50 to-white px-5 py-4">
        <div className="rounded-xl bg-[#002147] p-2 text-white">{icon}</div>
        <div>
          {eyebrow && (
            <p className="text-[9px] font-mono font-bold uppercase tracking-[0.24em] text-slate-400">
              {eyebrow}
            </p>
          )}
          <h3 className="text-sm font-black uppercase tracking-[0.12em] text-slate-950">{title}</h3>
        </div>
      </div>
      <div className="p-4">
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: rows }).map((_, i) => (
              <div key={i}>
                <Skeleton width={i % 2 === 0 ? "100%" : "70%"} height="18px" />
              </div>
            ))}
          </div>
        ) : (
          children
        )}
      </div>
    </div>
  );
}

function MetricRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-slate-100 py-2 last:border-0">
      <span className="text-[11px] font-mono text-slate-500">{label}</span>
      <span className="max-w-[58%] truncate text-right font-mono text-xs font-bold text-slate-900">
        {value}
      </span>
    </div>
  );
}

function GovernanceDashboard({ signals }: { signals: GovernanceSignal[] }) {
  const counts = signals.reduce(
    (acc, signal) => {
      acc[signal.status] += 1;
      return acc;
    },
    { pass: 0, warn: 0, fail: 0 },
  );
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-3">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs font-black uppercase tracking-[0.14em] text-slate-900">
          Governance dashboard
        </p>
        <span className="rounded-full bg-slate-100 px-2 py-1 font-mono text-[10px] text-slate-600">
          {counts.pass} pass · {counts.warn} warn · {counts.fail} fail
        </span>
      </div>
      <div className="space-y-2">
        {signals.map((signal) => (
          <div key={signal.id} className="rounded-xl border border-slate-100 bg-slate-50 p-3">
            <div className="flex items-center justify-between gap-3">
              <span className="text-[11px] font-black uppercase tracking-[0.12em] text-slate-900">
                {signal.label}
              </span>
              <span
                className={`rounded-full px-2 py-0.5 font-mono text-[9px] font-bold uppercase ${
                  signal.status === "pass"
                    ? "bg-emerald-100 text-emerald-700"
                    : signal.status === "fail"
                      ? "bg-red-100 text-red-700"
                      : "bg-amber-100 text-amber-700"
                }`}
              >
                {signal.status}
              </span>
            </div>
            <p className="mt-1 text-xs leading-5 text-slate-500">{signal.detail}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function SovereigntyResidencyBadges({
  computeNode,
  residencyStatus,
  jurisdiction,
}: {
  computeNode: string;
  residencyStatus: string;
  jurisdiction: string;
}) {
  return (
    <div className="mb-4 rounded-2xl border border-emerald-200 bg-emerald-50 p-3">
      <p className="text-xs font-black uppercase tracking-[0.14em] text-emerald-950">
        Sovereignty proof
      </p>
      <div className="mt-3 grid gap-2 text-[11px] font-semibold text-emerald-950 sm:grid-cols-3">
        <span className="rounded-full border border-emerald-200 bg-white px-3 py-2">
          Node: {computeNode}
        </span>
        <span className="rounded-full border border-emerald-200 bg-white px-3 py-2">
          Residency: {residencyStatus}
        </span>
        <span className="rounded-full border border-emerald-200 bg-white px-3 py-2">
          Jurisdiction: {jurisdiction}
        </span>
      </div>
      <p className="mt-2 text-xs leading-5 text-emerald-800">
        These values are embedded into every portable evidence package before signing.
      </p>
    </div>
  );
}

function EvidenceItem({
  icon,
  title,
  detail,
}: {
  icon: React.ReactNode;
  title: string;
  detail: string;
}) {
  return (
    <div className="flex gap-3 rounded-2xl border border-slate-200 bg-slate-50/80 p-3">
      <div className="mt-0.5 text-[#0B57D0]">{icon}</div>
      <div>
        <p className="text-xs font-black uppercase tracking-[0.14em] text-slate-900">{title}</p>
        <p className="mt-1 text-xs leading-5 text-slate-500">{detail}</p>
      </div>
    </div>
  );
}

// ================ AI ASSISTANT INTEGRATION ================
// This should be rendered inside the main return of AppContent, right before the closing div.
// For now, I'll create a summary document explaining the implementation.
// Since the file is too large, please manually add the following code right before line 1313 (before `</div>` and after `</div>` on line 1312):

/*
      {/* AI-Powered Adaptive Assistant *\/}
      {token && (
        <AIAssistant
          token={token}
          miningStatus={{
            hashrate: systemMetrics.currentHashrate,
            pool: pools.find(p => p.is_active),
            active: runtimeStatus.toLowerCase() === 'ok' || runtimeStatus.toLowerCase() === 'healthy',
            config: {
              phi_scaling: powerScale,
              phi_tier: phiTier
            }
          }}
          telemetryData={{
            consciousness_events: (consciousness as any).consciousness_events || 0,
            phi_resonance: health?.phiResonance || 0,
            compression_ratio: (health as any).compression_ratio || 1.0
          }}
        />
      )}
*/
