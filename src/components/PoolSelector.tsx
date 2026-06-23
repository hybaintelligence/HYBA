/**
 * Pool Selector Component
 * ========================
 *
 * Manages mining pool selection from frontend.
 * Uses consistent Tailwind CSS styling.
 * Integrates with main API client.
 */

import React, { useState } from "react";
import { Server, Check, AlertCircle, Loader2, Star } from "lucide-react";
import { type PoolInfo } from "../apiClient";

interface PoolSelectorProps {
  pools: PoolInfo[];
  activePoolName: string;
  onPoolSwitch: (pool: PoolInfo) => Promise<void>;
  isProcessing?: boolean;
}

export const PoolSelector: React.FC<PoolSelectorProps> = ({
  pools,
  activePoolName,
  onPoolSwitch,
  isProcessing = false,
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSwitchPool = async (pool: PoolInfo) => {
    try {
      setLoading(true);
      setError(null);
      await onPoolSwitch(pool);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to switch pool");
    } finally {
      setLoading(false);
    }
  };

  const enabledPools = pools.filter((p) => p.enabled !== false);

  return (
    <div className="rounded-2xl border border-white/30 bg-white/80 p-6 shadow-2xl shadow-slate-900/10 backdrop-blur">
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Server className="h-6 w-6 text-[#003666]" />
          <h2 className="text-xl font-bold text-slate-900">Mining Pool Selection</h2>
        </div>
        <span className="rounded-full bg-[#003666] px-3 py-1 text-xs font-bold text-white">
          Active: {activePoolName.toUpperCase()}
        </span>
      </div>

      {error && (
        <div className="mb-4 flex items-center gap-2 rounded-lg bg-red-50 p-3 text-red-900">
          <AlertCircle className="h-5 w-5" />
          <span className="text-sm">{error}</span>
        </div>
      )}

      {enabledPools.length === 0 ? (
        <div className="text-center py-8 text-slate-600">
          <Server className="mx-auto mb-2 h-12 w-12 opacity-50" />
          <p>No pools configured</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {enabledPools.map((pool) => {
            const isActive = pool.name === activePoolName || pool.is_active;
            return (
              <div
                key={pool.pool_id || pool.name}
                className={`relative rounded-xl border-2 p-4 transition-all ${
                  isActive
                    ? "border-[#16A34A] bg-green-50/50"
                    : "border-slate-200 bg-white hover:border-[#003666] hover:shadow-lg"
                }`}
              >
                {pool.is_active && (
                  <div className="absolute right-2 top-2">
                    <Star className="h-4 w-4 text-amber-500" />
                  </div>
                )}

                <div className="mb-3">
                  <h3 className="font-bold text-slate-900">{pool.name || pool.pool_id}</h3>
                  <p className="text-xs font-mono text-slate-600">{pool.url}</p>
                </div>

                <div className="mb-4 grid grid-cols-2 gap-2 rounded-lg bg-slate-50 p-2 text-xs">
                  <div>
                    <span className="block text-slate-600">Mode</span>
                    <span className="font-mono font-bold text-slate-900">
                      {pool.credential_mode}
                    </span>
                  </div>
                  <div>
                    <span className="block text-slate-600">Configured</span>
                    <span
                      className={`font-bold ${pool.configured ? "text-green-600" : "text-amber-600"}`}
                    >
                      {pool.configured ? "YES" : "NO"}
                    </span>
                  </div>
                  {pool.performance && (
                    <>
                      <div>
                        <span className="block text-slate-600">Latency</span>
                        <span className="font-mono font-bold text-slate-900">
                          {pool.performance.latency_ms}ms
                        </span>
                      </div>
                      <div>
                        <span className="block text-slate-600">Shares</span>
                        <span className="font-mono font-bold text-slate-900">
                          {pool.performance.shares_submitted}
                        </span>
                      </div>
                    </>
                  )}
                </div>

                <button
                  onClick={() => handleSwitchPool(pool)}
                  disabled={loading || isProcessing || isActive}
                  className={`w-full rounded-lg px-4 py-2 font-medium transition-colors ${
                    isActive
                      ? "bg-green-600 text-white"
                      : "bg-[#003666] text-white hover:bg-[#002147]"
                  } disabled:cursor-not-allowed disabled:opacity-50`}
                >
                  {loading || isProcessing ? (
                    <span className="flex items-center justify-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Processing...
                    </span>
                  ) : isActive ? (
                    <span className="flex items-center justify-center gap-2">
                      <Check className="h-4 w-4" />
                      Active
                    </span>
                  ) : pool.configured ? (
                    "Switch Pool"
                  ) : (
                    "Setup Pool"
                  )}
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default PoolSelector;
