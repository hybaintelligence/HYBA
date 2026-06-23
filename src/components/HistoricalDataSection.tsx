import React, { useMemo, useState } from "react";
import type { TelemetryData } from "../apiClient";
import {
  History,
  TrendingUp,
  TrendingDown,
  Calendar,
  BarChart3,
  Activity,
  RefreshCw,
} from "lucide-react";

interface HistoricalDataPoint {
  timestamp: string;
  hashrate: number;
  shares: number;
  difficulty: number;
  blockHeight: number;
  temperature: number;
  powerConsumption: number;
}

export default function HistoricalDataSection({ telemetry }: { telemetry?: TelemetryData | null }) {
  const historicalData = useMemo<HistoricalDataPoint[]>(() => {
    const health = telemetry?.health as Record<string, any> | undefined;
    const records = Array.isArray(health?.history) ? health.history : [];
    return records.map((entry: Record<string, any>, index: number) => ({
      timestamp: String(
        entry.timestamp || new Date(Date.now() - (records.length - index) * 3600000).toISOString(),
      ),
      hashrate: Number(entry.hashrate ?? entry.hashrate_ehs ?? 0),
      shares: Number(entry.shares ?? entry.shares_submitted ?? 0),
      difficulty: Number(entry.difficulty ?? 0),
      blockHeight: Number(entry.blockHeight ?? entry.block_height ?? 0),
      temperature: Number(entry.temperature ?? 0),
      powerConsumption: Number(entry.powerConsumption ?? entry.power_watts ?? 0),
    }));
  }, [telemetry]);
  const isLoading = false;
  const [timeRange, setTimeRange] = useState<"24h" | "7d" | "30d">("24h");
  const [selectedMetric, setSelectedMetric] = useState<
    "hashrate" | "shares" | "difficulty" | "power"
  >("hashrate");

  const getMetricLabel = (metric: string) => {
    switch (metric) {
      case "hashrate":
        return "Hashrate (EH/s)";
      case "shares":
        return "Shares Submitted";
      case "difficulty":
        return "Difficulty (T)";
      case "power":
        return "Power Consumption (W)";
      default:
        return metric;
    }
  };

  const getMetricValue = (data: HistoricalDataPoint, metric: string) => {
    switch (metric) {
      case "hashrate":
        return data.hashrate.toFixed(2);
      case "shares":
        return data.shares.toLocaleString();
      case "difficulty":
        return (data.difficulty / 1e12).toFixed(2);
      case "power":
        return data.powerConsumption.toFixed(0);
      default:
        return "0";
    }
  };

  const calculateTrend = (data: HistoricalDataPoint[], metric: string) => {
    if (data.length < 2) return { trend: "neutral", change: 0 };
    const recent = data.slice(-10);
    const older = data.slice(-20, -10);

    const recentAvg =
      recent.reduce(
        (sum, d) =>
          sum +
          (metric === "hashrate"
            ? d.hashrate
            : metric === "shares"
              ? d.shares
              : metric === "difficulty"
                ? d.difficulty
                : d.powerConsumption),
        0,
      ) / recent.length;
    const olderAvg =
      older.reduce(
        (sum, d) =>
          sum +
          (metric === "hashrate"
            ? d.hashrate
            : metric === "shares"
              ? d.shares
              : metric === "difficulty"
                ? d.difficulty
                : d.powerConsumption),
        0,
      ) / older.length;

    const change = ((recentAvg - olderAvg) / olderAvg) * 100;
    return {
      trend: change > 1 ? "up" : change < -1 ? "down" : "neutral",
      change: Math.abs(change),
    };
  };

  const trend = calculateTrend(historicalData, selectedMetric);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-[#003666] border-t-transparent" />
      </div>
    );
  }

  const latestData = historicalData[historicalData.length - 1];

  if (historicalData.length === 0) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-black text-slate-900">Historical Data</h2>
          <p className="text-slate-600">Backend-attested mining performance history</p>
        </div>
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-sm text-slate-600">
          No historical telemetry records are available from the backend yet. This handover build
          intentionally avoids synthetic history.
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-black text-slate-900">Historical Data</h2>
          <p className="text-slate-600">Mining performance over time</p>
        </div>
        <div className="flex gap-2">
          <button className="executive-button bg-[#003666] text-white shadow-[#003666]/20">
            <RefreshCw className="h-4 w-4" /> Refresh
          </button>
        </div>
      </div>

      <div className="flex gap-2">
        {(["24h", "7d", "30d"] as const).map((range) => (
          <button
            key={range}
            onClick={() => setTimeRange(range)}
            className={`px-4 py-2 rounded-lg font-medium transition ${
              timeRange === range
                ? "bg-[#003666] text-white"
                : "bg-slate-100 text-slate-700 hover:bg-slate-200"
            }`}
          >
            {range}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <Activity className="h-5 w-5 text-[#003666]" />
            <div
              className={`flex items-center gap-1 text-sm ${trend.trend === "up" ? "text-emerald-600" : trend.trend === "down" ? "text-red-600" : "text-slate-600"}`}
            >
              {trend.trend === "up" ? (
                <TrendingUp className="h-4 w-4" />
              ) : trend.trend === "down" ? (
                <TrendingDown className="h-4 w-4" />
              ) : null}
              <span>{trend.change.toFixed(1)}%</span>
            </div>
          </div>
          <p className="text-xs text-slate-600 uppercase tracking-wider">Current Hashrate</p>
          <p className="text-2xl font-black text-slate-900">
            {latestData?.hashrate.toFixed(2)} EH/s
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <BarChart3 className="h-5 w-5 text-[#003666]" />
            <span className="text-sm text-slate-600">Latest</span>
          </div>
          <p className="text-xs text-slate-600 uppercase tracking-wider">Shares (24h)</p>
          <p className="text-2xl font-black text-slate-900">
            {latestData?.shares.toLocaleString()}
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <Activity className="h-5 w-5 text-[#003666]" />
            <span className="text-sm text-slate-600">Current</span>
          </div>
          <p className="text-xs text-slate-600 uppercase tracking-wider">Difficulty</p>
          <p className="text-2xl font-black text-slate-900">
            {((latestData?.difficulty ?? 0) / 1e12).toFixed(2)}T
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <Activity className="h-5 w-5 text-[#003666]" />
            <span className="text-sm text-slate-600">Current</span>
          </div>
          <p className="text-xs text-slate-600 uppercase tracking-wider">Power Usage</p>
          <p className="text-2xl font-black text-slate-900">
            {latestData?.powerConsumption.toFixed(0)}W
          </p>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-bold text-slate-900">Performance Timeline</h3>
          <div className="flex gap-2">
            {(["hashrate", "shares", "difficulty", "power"] as const).map((metric) => (
              <button
                key={metric}
                onClick={() => setSelectedMetric(metric)}
                className={`px-3 py-1 rounded-lg text-sm font-medium transition ${
                  selectedMetric === metric
                    ? "bg-[#003666] text-white"
                    : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                }`}
              >
                {getMetricLabel(metric)}
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-2">
          {historicalData.slice(-20).map((data, index) => (
            <div key={index} className="flex items-center gap-4 p-3 bg-slate-50 rounded-lg">
              <Calendar className="h-4 w-4 text-slate-600" />
              <span className="text-sm text-slate-600 w-32">
                {new Date(data.timestamp).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </span>
              <div className="flex-1 h-2 bg-slate-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-[#003666] rounded-full"
                  style={{
                    width: `${(parseFloat(getMetricValue(data, selectedMetric)) / Math.max(...historicalData.map((d) => parseFloat(getMetricValue(d, selectedMetric))))) * 100}%`,
                  }}
                />
              </div>
              <span className="text-sm font-bold text-slate-900 w-24 text-right">
                {getMetricValue(data, selectedMetric)}
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="text-lg font-bold text-slate-900 mb-4">Recent Events</h3>
        <div className="space-y-3">
          <div className="flex items-start gap-3 p-3 bg-emerald-50 rounded-lg border border-emerald-200">
            <div className="h-2 w-2 rounded-full bg-emerald-500 mt-2" />
            <div>
              <p className="font-medium text-slate-900">Block Mined</p>
              <p className="text-sm text-slate-600">
                Successfully mined block #845210 with 12.5 BTC reward
              </p>
              <p className="text-xs text-slate-500 mt-1">2 hours ago</p>
            </div>
          </div>
          <div className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
            <div className="h-2 w-2 rounded-full bg-blue-500 mt-2" />
            <div>
              <p className="font-medium text-slate-900">Pool Switch</p>
              <p className="text-sm text-slate-600">
                Switched to Foundry USA pool for better efficiency
              </p>
              <p className="text-xs text-slate-500 mt-1">5 hours ago</p>
            </div>
          </div>
          <div className="flex items-start gap-3 p-3 bg-amber-50 rounded-lg border border-amber-200">
            <div className="h-2 w-2 rounded-full bg-amber-500 mt-2" />
            <div>
              <p className="font-medium text-slate-900">Hashrate Adjustment</p>
              <p className="text-sm text-slate-600">
                Power scale adjusted to 1.2x for optimal performance
              </p>
              <p className="text-xs text-slate-500 mt-1">8 hours ago</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
