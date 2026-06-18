import React, { useState, useEffect } from "react";
import { BarChart3, TrendingUp, PieChart, Activity, Zap, Cpu, Thermometer, RefreshCw, Download } from "lucide-react";

interface AnalyticsData {
  hashrateEfficiency: number;
  powerEfficiency: number;
  shareAcceptanceRate: number;
  poolPerformance: { name: string; hashrate: number; shares: number; efficiency: number }[];
  temperatureTrend: number[];
  powerConsumption: number[];
  revenue: { daily: number; weekly: number; monthly: number };
  costs: { daily: number; weekly: number; monthly: number };
  profit: { daily: number; weekly: number; monthly: number };
}

export default function AnalyticsSection() {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [timeRange, setTimeRange] = useState<"24h" | "7d" | "30d">("24h");

  useEffect(() => {
    // Simulate loading analytics data
    const mockData: AnalyticsData = {
      hashrateEfficiency: 94.5,
      powerEfficiency: 87.2,
      shareAcceptanceRate: 99.8,
      poolPerformance: [
        { name: "Foundry USA", hashrate: 125.5, shares: 15420, efficiency: 95.2 },
        { name: "AntPool", hashrate: 98.2, shares: 8920, efficiency: 91.8 },
        { name: "F2Pool", hashrate: 78.4, shares: 7120, efficiency: 89.5 },
        { name: "ViaBTC", hashrate: 65.1, shares: 5890, efficiency: 88.2 },
      ],
      temperatureTrend: Array.from({ length: 24 }, () => 45 + Math.random() * 15),
      powerConsumption: Array.from({ length: 24 }, () => 2500 + Math.random() * 500),
      revenue: { daily: 1250.50, weekly: 8753.50, monthly: 37515.00 },
      costs: { daily: 890.25, weekly: 6231.75, monthly: 26707.50 },
      profit: { daily: 360.25, weekly: 2521.75, monthly: 10807.50 },
    };
    setAnalyticsData(mockData);
    setIsLoading(false);
  }, [timeRange]);

  if (isLoading || !analyticsData) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-[#003666] border-t-transparent" />
      </div>
    );
  }

  const currentRevenue = analyticsData.revenue[timeRange === "24h" ? "daily" : timeRange === "7d" ? "weekly" : "monthly"];
  const currentCosts = analyticsData.costs[timeRange === "24h" ? "daily" : timeRange === "7d" ? "weekly" : "monthly"];
  const currentProfit = analyticsData.profit[timeRange === "24h" ? "daily" : timeRange === "7d" ? "weekly" : "monthly"];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-black text-slate-900">Mining Analytics</h2>
          <p className="text-slate-600">Performance metrics and profitability analysis</p>
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

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <TrendingUp className="h-5 w-5 text-emerald-600" />
            <span className="text-sm text-emerald-600 font-medium">+12.5%</span>
          </div>
          <p className="text-xs text-slate-600 uppercase tracking-wider">Revenue</p>
          <p className="text-2xl font-black text-slate-900">${currentRevenue.toLocaleString()}</p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <Zap className="h-5 w-5 text-amber-600" />
            <span className="text-sm text-amber-600 font-medium">+8.2%</span>
          </div>
          <p className="text-xs text-slate-600 uppercase tracking-wider">Costs</p>
          <p className="text-2xl font-black text-slate-900">${currentCosts.toLocaleString()}</p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <Activity className="h-5 w-5 text-[#003666]" />
            <span className="text-sm text-emerald-600 font-medium">+18.7%</span>
          </div>
          <p className="text-xs text-slate-600 uppercase tracking-wider">Profit</p>
          <p className="text-2xl font-black text-slate-900">${currentProfit.toLocaleString()}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="text-lg font-bold text-slate-900 mb-4">Efficiency Metrics</h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-sm text-slate-600">Hashrate Efficiency</span>
                <span className="text-sm font-bold text-slate-900">{analyticsData.hashrateEfficiency}%</span>
              </div>
              <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                <div className="h-full bg-[#003666] rounded-full" style={{ width: `${analyticsData.hashrateEfficiency}%` }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-sm text-slate-600">Power Efficiency</span>
                <span className="text-sm font-bold text-slate-900">{analyticsData.powerEfficiency}%</span>
              </div>
              <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                <div className="h-full bg-emerald-600 rounded-full" style={{ width: `${analyticsData.powerEfficiency}%` }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-sm text-slate-600">Share Acceptance Rate</span>
                <span className="text-sm font-bold text-slate-900">{analyticsData.shareAcceptanceRate}%</span>
              </div>
              <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                <div className="h-full bg-amber-600 rounded-full" style={{ width: `${analyticsData.shareAcceptanceRate}%` }} />
              </div>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="text-lg font-bold text-slate-900 mb-4">Pool Performance</h3>
          <div className="space-y-3">
            {analyticsData.poolPerformance.map((pool, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="h-8 w-8 rounded-full bg-[#003666] flex items-center justify-center text-white text-xs font-bold">
                    {pool.name.charAt(0)}
                  </div>
                  <div>
                    <p className="font-medium text-slate-900">{pool.name}</p>
                    <p className="text-xs text-slate-600">{pool.hashrate.toFixed(1)} EH/s</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold text-slate-900">{pool.efficiency}%</p>
                  <p className="text-xs text-slate-600">{pool.shares.toLocaleString()} shares</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <Thermometer className="h-5 w-5 text-[#003666]" />
            <h3 className="text-lg font-bold text-slate-900">Temperature Trend</h3>
          </div>
          <div className="flex items-end gap-1 h-32">
            {analyticsData.temperatureTrend.slice(-24).map((temp, index) => (
              <div
                key={index}
                className="flex-1 bg-gradient-to-t from-[#003666] to-[#003666]/50 rounded-t"
                style={{ height: `${((temp - 40) / 25) * 100}%` }}
                title={`${temp.toFixed(1)}°C`}
              />
            ))}
          </div>
          <div className="flex justify-between mt-2 text-xs text-slate-600">
            <span>24h ago</span>
            <span>Now</span>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <Zap className="h-5 w-5 text-[#003666]" />
            <h3 className="text-lg font-bold text-slate-900">Power Consumption</h3>
          </div>
          <div className="flex items-end gap-1 h-32">
            {analyticsData.powerConsumption.slice(-24).map((power, index) => (
              <div
                key={index}
                className="flex-1 bg-gradient-to-t from-amber-600 to-amber-400 rounded-t"
                style={{ height: `${((power - 2400) / 700) * 100}%` }}
                title={`${power.toFixed(0)}W`}
              />
            ))}
          </div>
          <div className="flex justify-between mt-2 text-xs text-slate-600">
            <span>24h ago</span>
            <span>Now</span>
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center gap-2 mb-4">
          <PieChart className="h-5 w-5 text-[#003666]" />
          <h3 className="text-lg font-bold text-slate-900">Cost Breakdown</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-slate-50 rounded-xl">
            <p className="text-xs text-slate-600 uppercase tracking-wider mb-1">Electricity</p>
            <p className="text-xl font-bold text-slate-900">${(currentCosts * 0.65).toFixed(2)}</p>
            <p className="text-xs text-slate-600 mt-1">65% of costs</p>
          </div>
          <div className="p-4 bg-slate-50 rounded-xl">
            <p className="text-xs text-slate-600 uppercase tracking-wider mb-1">Cooling</p>
            <p className="text-xl font-bold text-slate-900">${(currentCosts * 0.20).toFixed(2)}</p>
            <p className="text-xs text-slate-600 mt-1">20% of costs</p>
          </div>
          <div className="p-4 bg-slate-50 rounded-xl">
            <p className="text-xs text-slate-600 uppercase tracking-wider mb-1">Maintenance</p>
            <p className="text-xl font-bold text-slate-900">${(currentCosts * 0.15).toFixed(2)}</p>
            <p className="text-xs text-slate-600 mt-1">15% of costs</p>
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center gap-2 mb-4">
          <Cpu className="h-5 w-5 text-[#003666]" />
          <h3 className="text-lg font-bold text-slate-900">Performance Insights</h3>
        </div>
        <div className="space-y-3">
          <div className="flex items-start gap-3 p-3 bg-emerald-50 rounded-lg border border-emerald-200">
            <div className="h-2 w-2 rounded-full bg-emerald-500 mt-2" />
            <div>
              <p className="font-medium text-slate-900">Optimal Hashrate Detected</p>
              <p className="text-sm text-slate-600">Current hashrate efficiency (94.5%) is above target threshold of 90%</p>
            </div>
          </div>
          <div className="flex items-start gap-3 p-3 bg-amber-50 rounded-lg border border-amber-200">
            <div className="h-2 w-2 rounded-full bg-amber-500 mt-2" />
            <div>
              <p className="font-medium text-slate-900">Power Consumption Alert</p>
              <p className="text-sm text-slate-600">Power usage increased by 8.2% compared to previous period</p>
            </div>
          </div>
          <div className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
            <div className="h-2 w-2 rounded-full bg-blue-500 mt-2" />
            <div>
              <p className="font-medium text-slate-900">Pool Recommendation</p>
              <p className="text-sm text-slate-600">Consider increasing allocation to Foundry USA (95.2% efficiency)</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
