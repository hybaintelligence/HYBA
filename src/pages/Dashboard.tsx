import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity,
  Database,
  RadioTower,
  Wifi,
  WifiOff,
  RefreshCw,
  Server,
  ShieldCheck,
  Cpu,
  UserCheck,
  LogOut,
  LogIn,
  UserPlus,
} from "lucide-react";
import {
  type TelemetryData,
  fetchTelemetryData,
  configurePool,
  disconnectFromPool,
  switchPool,
  updatePowerScale,
  type PoolInfo,
  type ConfigurePoolRequest,
} from "../apiClient";
import { useAuth } from "../contexts/AuthContext";
import { useApiRequest } from "../hooks/useApiRequest";
import { useLatencyMetrics } from "../hooks/useLatencyMetrics";
import { NetworkToast } from "../components/NetworkToast";
import { PoolSecretsConfig } from "../components/PoolSecretsConfig";
import { SovereignCommandPost } from "../components/SovereignCommandPost";
import { SovereignGenesisPanel } from "../components/SovereignGenesisPanel";
import { Sparkline } from "../components/Sparkline";
import { ExecutiveSummary } from "../components/ExecutiveSummary";
import { buildGovernanceSignals, type GovernanceSignal } from "../governance";

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

function fmtNum(value: number | null | undefined, digits = 2): string {
  return typeof value === "number" && Number.isFinite(value)
    ? value.toLocaleString(undefined, { maximumFractionDigits: digits })
    : UNAVAILABLE;
}

function fmtPct(value: number | null | undefined): string {
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

export default function Dashboard() {
  const { user, token, logout } = useAuth();
  const [telemetry, setTelemetry] = useState<TelemetryData | null>(null);
  const [telemetryError, setTelemetryError] = useState<string | null>(null);
  const [isSyncing, setIsSyncing] = useState(false);
  const [isPollingActive, setIsPollingActive] = useState(true);
  const [powerScale, setPowerScale] = useState(1);
  const [phiTier, setPhiTier] = useState(12);
  const [selectedPoolForConfig, setSelectedPoolForConfig] = useState<PoolInfo | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [authFeedback, setAuthFeedback] = useState<{ text: string; error: boolean } | null>(null);

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
  const poolSummary = telemetry?.pools?.summary || { total_pools: 0, active_pools: 0, telemetry_source: "unavailable" };
  const security = telemetry?.security || { status: "unavailable", threat_level: null };
  const consciousness = telemetry?.consciousness || { status: "unavailable", source: "unavailable" };

  const runtimeStatus = useMemo(() => health?.status || "unavailable", [health]);
  const activePoolName = fmtText(systemMetrics.activePool || pools.find(p => p.is_active)?.name);
  const configuredPoolCount = Number(poolSummary.configured_pools ?? poolSummary.total_pools ?? 0);
  const activePoolCount = Number(poolSummary.active_pools ?? 0);
  const securityStatus = fmtText(security.status);

  const governanceTags = useMemo(
    () => [
      ...((health?.substrate?.governance_tags as string[] | undefined) || []),
      ...((health?.telemetry?.governance_tags as string[] | undefined) || []),
    ],
    [health?.substrate, health?.telemetry],
  );

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
      }),
    [
      activePoolCount,
      activePoolName,
      configuredPoolCount,
      governanceTags,
      health?.phiResonance,
      health?.telemetry_source,
      isConnected,
      runtimeStatus,
      security.threat_level,
      securityStatus,
    ],
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

  useEffect(() => {
    if (isPollingActive) getLiveTelemetry();
    const interval = window.setInterval(() => {
      if (isPollingActive) getLiveTelemetry();
    }, 15000);
    return () => window.clearInterval(interval);
  }, [getLiveTelemetry, isPollingActive]);

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

  const handlePoolSave = async (payload: ConfigurePoolRequest, connectAfterSave: boolean) => {
    if (!payload.pool_id) return;
    setIsProcessing(true);
    try {
      await configurePool(payload);
      if (connectAfterSave) {
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

  const isLoading = !telemetry && !telemetryError;

  return (
    <div className="min-h-screen bg-[#F4F1EA] text-[#101828]">
      <NetworkToast
        isConnected={isConnected}
        latencyMs={latencyMs}
        isDismissed={isToastDismissed}
        onDismiss={() => setIsToastDismissed(true)}
      />

      <div className="mx-auto max-w-7xl px-6 py-6">
        <ExecutiveSummary
          readinessScore={readinessScore}
          runtimeStatus={runtimeStatus}
          securityStatus={securityStatus}
          activePoolCount={activePoolCount}
          latencyMs={latencyMs}
        />

        {/* Main Dashboard Content */}
        <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* Mining Telemetry Panel */}
          <div className="rounded-2xl border border-white/30 bg-white/80 p-6 shadow-2xl shadow-slate-900/10 backdrop-blur">
            <h3 className="mb-4 flex items-center gap-2 text-lg font-bold text-slate-900">
              <Database className="h-5 w-5" />
              Mining Telemetry
            </h3>
            <div className="space-y-3 font-mono text-sm">
              <div className="flex justify-between">
                <span className="text-slate-600">Block Height</span>
                <span className="font-bold">{fmtNum(systemMetrics.blockHeight, 0)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">Hashrate (EH/s)</span>
                <span className="font-bold">{fmtNum(systemMetrics.currentHashrate)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">Power Consumption</span>
                <span className="font-bold">{fmtNum(systemMetrics.powerConsumption)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">Network Difficulty</span>
                <span className="font-bold">{fmtNum(systemMetrics.networkDifficulty)}</span>
              </div>
            </div>
          </div>

          {/* Quantum Runtime Panel */}
          <div className="rounded-2xl border border-white/30 bg-white/80 p-6 shadow-2xl shadow-slate-900/10 backdrop-blur">
            <h3 className="mb-4 flex items-center gap-2 text-lg font-bold text-slate-900">
              <Cpu className="h-5 w-5" />
              Quantum Runtime
            </h3>
            <div className="space-y-3 font-mono text-sm">
              <div className="flex justify-between">
                <span className="text-slate-600">Basis Coherence</span>
                <span className="font-bold">{fmtPct(health?.quantumCoherence)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">Phi Phase Alignment</span>
                <span className="font-bold">{fmtPct(health?.phiResonance)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">Power Scale</span>
                <span className="font-bold">{powerScale.toFixed(1)}x</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">φ-tier</span>
                <span className="font-bold">10^{phiTier}</span>
              </div>
            </div>
          </div>

          {/* Security Panel */}
          <div className="rounded-2xl border border-white/30 bg-white/80 p-6 shadow-2xl shadow-slate-900/10 backdrop-blur">
            <h3 className="mb-4 flex items-center gap-2 text-lg font-bold text-slate-900">
              <ShieldCheck className="h-5 w-5" />
              Security Status
            </h3>
            <div className="space-y-3 font-mono text-sm">
              <div className="flex justify-between">
                <span className="text-slate-600">Status</span>
                <span className="font-bold">{securityStatus}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">Threat Level</span>
                <span className="font-bold">{fmtText(security.threat_level)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">Active Pools</span>
                <span className="font-bold">{fmtNum(activePoolCount, 0)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">Configured Pools</span>
                <span className="font-bold">{fmtNum(configuredPoolCount, 0)}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Pool Management */}
        <div className="mt-6 rounded-2xl border border-white/30 bg-white/80 p-6 shadow-2xl shadow-slate-900/10 backdrop-blur">
          <h3 className="mb-4 flex items-center gap-2 text-lg font-bold text-slate-900">
            <Server className="h-5 w-5" />
            Mining Pools
          </h3>
          {isLoading ? (
            <div className="text-center text-slate-600">Loading pool data...</div>
          ) : pools.length === 0 ? (
            <div className="text-center text-slate-600">No pools configured</div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {pools.map((pool, idx) => (
                <div
                  key={pool.pool_id || pool.name || idx}
                  className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
                >
                  <div className="mb-2 font-bold text-slate-900">{fmtText(pool.name)}</div>
                  <div className="mb-3 font-mono text-xs text-slate-600">{fmtText(pool.url)}</div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setSelectedPoolForConfig(pool)}
                      disabled={isProcessing}
                      className="flex-1 rounded bg-slate-900 px-3 py-2 text-sm text-white hover:bg-slate-800 disabled:opacity-50"
                    >
                      Configure
                    </button>
                    {pool.is_active ? (
                      <button
                        onClick={handlePoolDisconnect}
                        disabled={isProcessing}
                        className="flex-1 rounded bg-red-600 px-3 py-2 text-sm text-white hover:bg-red-700 disabled:opacity-50"
                      >
                        Disconnect
                      </button>
                    ) : (
                      <button
                        onClick={() => handlePoolSwitch(pool)}
                        disabled={isProcessing}
                        className="flex-1 rounded bg-blue-900 px-3 py-2 text-sm text-white hover:bg-blue-800 disabled:opacity-50"
                      >
                        {pool.configured ? "Switch" : "Setup"}
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* User Info */}
        <div className="mt-6 rounded-2xl border border-white/30 bg-white/80 p-6 shadow-2xl shadow-slate-900/10 backdrop-blur">
          <h3 className="mb-4 flex items-center gap-2 text-lg font-bold text-slate-900">
            <UserCheck className="h-5 w-5" />
            Operator Identity
          </h3>
          {user ? (
            <div className="font-mono text-sm">
              <div className="mb-2 flex justify-between">
                <span className="text-slate-600">Username</span>
                <span className="font-bold">{user.username}</span>
              </div>
              <div className="mb-4 flex justify-between">
                <span className="text-slate-600">Role</span>
                <span className="font-bold">{user.role}</span>
              </div>
              <button
                onClick={logout}
                className="flex items-center gap-2 rounded bg-red-600 px-4 py-2 text-sm text-white hover:bg-red-700"
              >
                <LogOut className="h-4 w-4" />
                Log out
              </button>
            </div>
          ) : (
            <div className="text-center text-slate-600">
              Please log in to access the dashboard
            </div>
          )}
        </div>

        {/* Sovereign Panels */}
        <div className="mt-6 grid grid-cols-1 gap-6">
          <SovereignCommandPost />
          <SovereignGenesisPanel />
        </div>

        {/* Pool Config Modal */}
        {selectedPoolForConfig && (
          <PoolSecretsConfig
            pool={selectedPoolForConfig}
            onClose={() => setSelectedPoolForConfig(null)}
            onSave={handlePoolSave}
          />
        )}

        {/* Auth Feedback */}
        {authFeedback && (
          <div className={`fixed bottom-4 right-4 rounded-lg px-4 py-3 ${
            authFeedback.error ? "bg-red-50 text-red-900" : "bg-green-50 text-green-900"
          }`}>
            {authFeedback.text}
          </div>
        )}
      </div>
    </div>
  );
}
