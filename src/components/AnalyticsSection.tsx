import React, { useMemo, useState } from "react";
import {
  TrendingUp,
  Activity,
  Zap,
  Cpu,
  Thermometer,
  RefreshCw,
  Download,
  ShieldCheck,
} from "lucide-react";
import type { PoolInfo, TelemetryData } from "../apiClient";

interface AnalyticsData {
  hashrateEfficiency: number | null;
  powerEfficiency: number | null;
  shareAcceptanceRate: number | null;
  poolPerformance: {
    name: string;
    hashrate: number | null;
    shares: number | null;
    efficiency: number | null;
  }[];
  temperatureTrend: number[];
  powerConsumption: number[];
  revenue: { daily: number | null; weekly: number | null; monthly: number | null };
  costs: { daily: number | null; weekly: number | null; monthly: number | null };
  profit: { daily: number | null; weekly: number | null; monthly: number | null };
  source: string;
}

function num(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function pct(value: number | null): string {
  return value === null ? "Evidence pending" : `${value.toFixed(2)}%`;
}

function money(value: number | null): string {
  return value === null
    ? "Not asserted"
    : `$${value.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
}

function latestSeries(value: unknown): number[] {
  return Array.isArray(value)
    ? value
        .map(num)
        .filter((entry): entry is number => entry !== null)
        .slice(-24)
    : [];
}

export default function AnalyticsSection({
  telemetry,
  pools = [],
}: {
  telemetry?: TelemetryData | null;
  pools?: PoolInfo[];
}) {
  const [timeRange, setTimeRange] = useState<"24h" | "7d" | "30d">("24h");

  const analyticsData = useMemo<AnalyticsData>(() => {
    const health = telemetry?.health as Record<string, any> | undefined;
    const metrics = (health?.systemMetrics || {}) as Record<string, any>;
    const accepted = num(
      metrics.sharesAccepted ?? metrics.acceptedShares ?? health?.shares_accepted,
    );
    const submitted = num(
      metrics.sharesSubmitted ?? metrics.submittedShares ?? health?.shares_submitted,
    );
    const acceptance =
      submitted && submitted > 0 && accepted !== null ? (accepted / submitted) * 100 : null;
    const currentHashrate = num(
      metrics.currentHashrate ?? metrics.hashrate_ehs ?? health?.hashrate_ehs,
    );
    const targetHashrate = num(
      metrics.targetHashrate ?? metrics.capacity_ehs ?? health?.hashrate_cap_ehs,
    );
    const powerEfficiency = num(metrics.powerEfficiency ?? health?.power_efficiency_pct);
    const hashrateEfficiency =
      targetHashrate && targetHashrate > 0 && currentHashrate !== null
        ? Math.min(100, (currentHashrate / targetHashrate) * 100)
        : num(metrics.hashrateEfficiency ?? health?.hashrate_efficiency_pct);

    const poolPerformance = pools.map((pool) => ({
      name: pool.name,
      hashrate: num((pool as any).hashrate_ehs ?? (pool as any).hashrate),
      shares: num(
        (pool as any).shares_accepted ?? (pool as any).accepted_shares ?? (pool as any).shares,
      ),
      efficiency: num((pool as any).efficiency_pct ?? (pool as any).efficiency),
    }));

    const revenue = num(metrics.dailyRevenueUsd ?? health?.daily_revenue_usd);
    const costs = num(metrics.dailyCostUsd ?? health?.daily_cost_usd);

    return {
      hashrateEfficiency,
      powerEfficiency,
      shareAcceptanceRate: acceptance,
      poolPerformance,
      temperatureTrend: latestSeries(metrics.temperatureTrend ?? health?.temperature_trend),
      powerConsumption: latestSeries(metrics.powerConsumption ?? health?.power_consumption_trend),
      revenue: {
        daily: revenue,
        weekly: revenue === null ? null : revenue * 7,
        monthly: revenue === null ? null : revenue * 30,
      },
      costs: {
        daily: costs,
        weekly: costs === null ? null : costs * 7,
        monthly: costs === null ? null : costs * 30,
      },
      profit: {
        daily: revenue !== null && costs !== null ? revenue - costs : null,
        weekly: revenue !== null && costs !== null ? (revenue - costs) * 7 : null,
        monthly: revenue !== null && costs !== null ? (revenue - costs) * 30 : null,
      },
      source: String(telemetry?.health?.telemetry_source || "backend-evidence-required"),
    };
  }, [telemetry, pools]);

  const currentRevenue =
    analyticsData.revenue[
      timeRange === "24h" ? "daily" : timeRange === "7d" ? "weekly" : "monthly"
    ];
  const currentCosts =
    analyticsData.costs[timeRange === "24h" ? "daily" : timeRange === "7d" ? "weekly" : "monthly"];
  const currentProfit =
    analyticsData.profit[timeRange === "24h" ? "daily" : timeRange === "7d" ? "weekly" : "monthly"];
  const noFinancials = currentRevenue === null && currentCosts === null && currentProfit === null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-black text-slate-900">Mining Analytics</h2>
          <p className="text-slate-600">Evidence-bound performance, pool, and economics posture</p>
        </div>
        <div className="flex gap-2">
          <button className="executive-button bg-[#003666] text-white shadow-[#003666]/20">
            <RefreshCw className="h-4 w-4" /> Refresh
          </button>
          <button className="executive-button bg-slate-100 text-slate-900 shadow-slate-900/10">
            <Download className="h-4 w-4" /> Export
          </button>
        </div>
      </div>

      <div className="rounded-2xl border border-blue-100 bg-blue-50/80 p-4 text-sm text-blue-950">
        <div className="flex items-center gap-2 font-bold">
          <ShieldCheck className="h-4 w-4" /> Telemetry source: {analyticsData.source}
        </div>
        <p className="mt-1">
          Financial values remain unasserted unless supplied by authenticated backend telemetry. The
          console does not fabricate revenue, share, or thermal data.
        </p>
      </div>

      <div className="flex gap-2">
        {(["24h", "7d", "30d"] as const).map((range) => (
          <button
            key={range}
            onClick={() => setTimeRange(range)}
            className={`px-4 py-2 rounded-lg font-medium transition ${timeRange === range ? "bg-[#003666] text-white" : "bg-slate-100 text-slate-700 hover:bg-slate-200"}`}
          >
            {range}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { label: "Revenue", value: money(currentRevenue), icon: TrendingUp },
          { label: "Costs", value: money(currentCosts), icon: Zap },
          { label: "Profit", value: money(currentProfit), icon: Activity },
        ].map(({ label, value, icon: Icon }) => (
          <div key={label} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <Icon className="mb-2 h-5 w-5 text-[#003666]" />
            <p className="text-xs text-slate-600 uppercase tracking-wider">{label}</p>
            <p className="text-2xl font-black text-slate-900">{value}</p>
          </div>
        ))}
      </div>
      {noFinancials && (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-6 text-sm text-slate-600">
          Economics panel is handover-safe: connect pool/accounting telemetry to display
          client-specific revenue, cost, and margin.
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="text-lg font-bold text-slate-900 mb-4">Efficiency Metrics</h3>
          <div className="space-y-4">
            {[
              ["Hashrate Efficiency", analyticsData.hashrateEfficiency],
              ["Power Efficiency", analyticsData.powerEfficiency],
              ["Share Acceptance Rate", analyticsData.shareAcceptanceRate],
            ].map(([label, value]) => (
              <div key={label as string}>
                <div className="flex justify-between mb-2">
                  <span className="text-sm text-slate-600">{label as string}</span>
                  <span className="text-sm font-bold text-slate-900">
                    {pct(value as number | null)}
                  </span>
                </div>
                <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-[#003666] rounded-full"
                    style={{ width: `${value ?? 0}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="text-lg font-bold text-slate-900 mb-4">Pool Performance</h3>
          {analyticsData.poolPerformance.length === 0 ? (
            <p className="text-sm text-slate-500">
              No authenticated pool performance records available.
            </p>
          ) : (
            <div className="space-y-3">
              {analyticsData.poolPerformance.map((pool) => (
                <div
                  key={pool.name}
                  className="flex items-center justify-between p-3 bg-slate-50 rounded-lg"
                >
                  <div>
                    <p className="font-medium text-slate-900">{pool.name}</p>
                    <p className="text-xs text-slate-600">
                      {pool.hashrate === null
                        ? "Hashrate pending"
                        : `${pool.hashrate.toFixed(2)} EH/s`}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-bold text-slate-900">{pct(pool.efficiency)}</p>
                    <p className="text-xs text-slate-600">
                      {pool.shares === null
                        ? "shares pending"
                        : `${pool.shares.toLocaleString()} shares`}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <Thermometer className="h-5 w-5 text-[#003666]" />
            <h3 className="text-lg font-bold text-slate-900">Temperature Trend</h3>
          </div>
          <p className="text-sm text-slate-500">
            {analyticsData.temperatureTrend.length
              ? `${analyticsData.temperatureTrend.length} telemetry points loaded`
              : "Thermal telemetry pending"}
          </p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <Cpu className="h-5 w-5 text-[#003666]" />
            <h3 className="text-lg font-bold text-slate-900">Power Consumption</h3>
          </div>
          <p className="text-sm text-slate-500">
            {analyticsData.powerConsumption.length
              ? `${analyticsData.powerConsumption.length} telemetry points loaded`
              : "Power telemetry pending"}
          </p>
        </div>
      </div>
    </div>
  );
}
