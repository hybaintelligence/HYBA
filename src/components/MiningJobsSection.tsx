import React, { useMemo, useState } from "react";
import type { PoolInfo, TelemetryData } from "../apiClient";
import { Clock, Activity, Server, CheckCircle2, AlertCircle, Pause, RefreshCw } from "lucide-react";

interface MiningJob {
  id: string;
  name: string;
  status: "running" | "paused" | "completed" | "failed";
  pool: string;
  startTime: string;
  endTime?: string;
  hashrate: number;
  sharesSubmitted: number;
  sharesAccepted: number;
  difficulty: number;
  blockHeight: number;
}

export default function MiningJobsSection({ telemetry, pools = [] }: { telemetry?: TelemetryData | null; pools?: PoolInfo[] }) {
  const [selectedJob, setSelectedJob] = useState<MiningJob | null>(null);
  const jobs = useMemo<MiningJob[]>(() => {
    const health = telemetry?.health as Record<string, any> | undefined;
    const metrics = (health?.systemMetrics || {}) as Record<string, any>;
    const activePools = pools.filter((pool) => pool.is_active);
    if (activePools.length === 0 && !metrics.activePool) return [];
    return (activePools.length ? activePools : [{ name: String(metrics.activePool || "Configured pool"), is_active: true } as PoolInfo]).map((pool, index) => ({
      id: `pool-${index + 1}`,
      name: index === 0 ? "Primary pool execution" : "Failover pool execution",
      status: pool.is_active ? "running" : "paused",
      pool: pool.name,
      startTime: String(metrics.startedAt || health?.timestamp || new Date().toISOString()),
      hashrate: Number(metrics.currentHashrate ?? (pool as any).hashrate_ehs ?? 0),
      sharesSubmitted: Number(metrics.sharesSubmitted ?? (pool as any).shares_submitted ?? 0),
      sharesAccepted: Number(metrics.sharesAccepted ?? (pool as any).shares_accepted ?? 0),
      difficulty: Number(metrics.difficulty ?? health?.network_difficulty ?? 0),
      blockHeight: Number(metrics.blockHeight ?? health?.block_height ?? 0),
    }));
  }, [telemetry, pools]);

  const isLoading = false;

  /* Live jobs are derived above from authenticated telemetry only. */

  const getStatusColor = (status: MiningJob["status"]) => {
    switch (status) {
      case "running":
        return "bg-emerald-100 text-emerald-900 border-emerald-300";
      case "paused":
        return "bg-amber-100 text-amber-900 border-amber-300";
      case "completed":
        return "bg-blue-100 text-blue-900 border-blue-300";
      case "failed":
        return "bg-red-100 text-red-900 border-red-300";
      default:
        return "bg-slate-100 text-slate-900 border-slate-300";
    }
  };

  const getStatusIcon = (status: MiningJob["status"]) => {
    switch (status) {
      case "running":
        return <Activity className="h-4 w-4" />;
      case "paused":
        return <Pause className="h-4 w-4" />;
      case "completed":
        return <CheckCircle2 className="h-4 w-4" />;
      case "failed":
        return <AlertCircle className="h-4 w-4" />;
      default:
        return <Activity className="h-4 w-4" />;
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-[#003666] border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-black text-slate-900">Mining Jobs</h2>
          <p className="text-slate-600">Active and historical mining job details</p>
        </div>
        <button className="executive-button bg-[#003666] text-white shadow-[#003666]/20">
          <RefreshCw className="h-4 w-4" /> Refresh Jobs
        </button>
      </div>

      <div className="grid gap-4">
      {jobs.length === 0 && (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-sm text-slate-600">
          No active mining jobs are available from authenticated backend telemetry. This handover build intentionally avoids fabricated pool jobs.
        </div>
      )}

        {jobs.map((job) => (
          <div
            key={job.id}
            className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm hover:shadow-md transition-shadow cursor-pointer"
            onClick={() => setSelectedJob(job)}
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <Server className="h-5 w-5 text-[#003666]" />
                <div>
                  <h3 className="font-bold text-slate-900">{job.name}</h3>
                  <p className="text-sm text-slate-600">{job.pool}</p>
                </div>
              </div>
              <div className={`flex items-center gap-2 px-3 py-1 rounded-full border text-xs font-semibold ${getStatusColor(job.status)}`}>
                {getStatusIcon(job.status)}
                <span className="uppercase">{job.status}</span>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-xs text-slate-600 uppercase tracking-wider">Hashrate</p>
                <p className="text-lg font-bold text-slate-900">{job.hashrate.toFixed(2)} EH/s</p>
              </div>
              <div>
                <p className="text-xs text-slate-600 uppercase tracking-wider">Shares</p>
                <p className="text-lg font-bold text-slate-900">
                  {job.sharesAccepted}/{job.sharesSubmitted}
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-600 uppercase tracking-wider">Difficulty</p>
                <p className="text-lg font-bold text-slate-900">{(job.difficulty / 1e12).toFixed(2)}T</p>
              </div>
              <div>
                <p className="text-xs text-slate-600 uppercase tracking-wider">Block Height</p>
                <p className="text-lg font-bold text-slate-900">{job.blockHeight.toLocaleString()}</p>
              </div>
            </div>

            <div className="mt-4 flex items-center gap-2 text-sm text-slate-600">
              <Clock className="h-4 w-4" />
              <span>
                Started: {new Date(job.startTime).toLocaleString()}
                {job.endTime && ` • Ended: ${new Date(job.endTime).toLocaleString()}`}
              </span>
            </div>
          </div>
        ))}
      </div>

      {selectedJob && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50" onClick={() => setSelectedJob(null)}>
          <div className="bg-white rounded-2xl p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-slate-900">{selectedJob.name}</h3>
              <button onClick={() => setSelectedJob(null)} className="text-slate-600 hover:text-slate-900">
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-slate-50 rounded-xl">
                  <p className="text-xs text-slate-600 uppercase tracking-wider">Status</p>
                  <p className="text-lg font-bold text-slate-900 capitalize">{selectedJob.status}</p>
                </div>
                <div className="p-4 bg-slate-50 rounded-xl">
                  <p className="text-xs text-slate-600 uppercase tracking-wider">Pool</p>
                  <p className="text-lg font-bold text-slate-900">{selectedJob.pool}</p>
                </div>
                <div className="p-4 bg-slate-50 rounded-xl">
                  <p className="text-xs text-slate-600 uppercase tracking-wider">Hashrate</p>
                  <p className="text-lg font-bold text-slate-900">{selectedJob.hashrate.toFixed(2)} EH/s</p>
                </div>
                <div className="p-4 bg-slate-50 rounded-xl">
                  <p className="text-xs text-slate-600 uppercase tracking-wider">Block Height</p>
                  <p className="text-lg font-bold text-slate-900">{selectedJob.blockHeight.toLocaleString()}</p>
                </div>
                <div className="p-4 bg-slate-50 rounded-xl">
                  <p className="text-xs text-slate-600 uppercase tracking-wider">Shares Submitted</p>
                  <p className="text-lg font-bold text-slate-900">{selectedJob.sharesSubmitted.toLocaleString()}</p>
                </div>
                <div className="p-4 bg-slate-50 rounded-xl">
                  <p className="text-xs text-slate-600 uppercase tracking-wider">Shares Accepted</p>
                  <p className="text-lg font-bold text-slate-900">{selectedJob.sharesAccepted.toLocaleString()}</p>
                </div>
                <div className="p-4 bg-slate-50 rounded-xl">
                  <p className="text-xs text-slate-600 uppercase tracking-wider">Acceptance Rate</p>
                  <p className="text-lg font-bold text-slate-900">
                    {((selectedJob.sharesAccepted / selectedJob.sharesSubmitted) * 100).toFixed(2)}%
                  </p>
                </div>
                <div className="p-4 bg-slate-50 rounded-xl">
                  <p className="text-xs text-slate-600 uppercase tracking-wider">Difficulty</p>
                  <p className="text-lg font-bold text-slate-900">{(selectedJob.difficulty / 1e12).toFixed(2)}T</p>
                </div>
              </div>

              <div className="p-4 bg-slate-50 rounded-xl">
                <p className="text-xs text-slate-600 uppercase tracking-wider mb-2">Time Information</p>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-slate-600">Start Time:</span>
                    <span className="font-medium text-slate-900">{new Date(selectedJob.startTime).toLocaleString()}</span>
                  </div>
                  {selectedJob.endTime && (
                    <div className="flex justify-between">
                      <span className="text-slate-600">End Time:</span>
                      <span className="font-medium text-slate-900">{new Date(selectedJob.endTime).toLocaleString()}</span>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <span className="text-slate-600">Duration:</span>
                    <span className="font-medium text-slate-900">
                      {selectedJob.endTime
                        ? `${Math.floor((new Date(selectedJob.endTime).getTime() - new Date(selectedJob.startTime).getTime()) / 3600000)}h`
                        : `${Math.floor((Date.now() - new Date(selectedJob.startTime).getTime()) / 3600000)}h (ongoing)`}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-6 flex gap-2">
              {selectedJob.status === "running" && (
                <button className="executive-button bg-amber-600 text-white shadow-amber-600/20">
                  <Pause className="h-4 w-4" /> Pause Job
                </button>
              )}
              {selectedJob.status === "paused" && (
                <button className="executive-button bg-emerald-600 text-white shadow-emerald-600/20">
                  <Play className="h-4 w-4" /> Resume Job
                </button>
              )}
              <button className="executive-button bg-[#003666] text-white shadow-[#003666]/20">
                <RefreshCw className="h-4 w-4" /> Refresh Details
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
