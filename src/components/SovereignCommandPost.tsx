import React, { useEffect, useState } from "react";
import { ShieldCheck } from "lucide-react";
import { getSecurityStatus, type SecurityStatus } from "../apiClient";

const unavailable = "—";

function pct(value: unknown): string {
  return typeof value === "number" && Number.isFinite(value) ? `${(value * 100).toFixed(2)}%` : unavailable;
}

function num(value: unknown, digits = 0): string {
  return typeof value === "number" && Number.isFinite(value) ? value.toLocaleString(undefined, { maximumFractionDigits: digits }) : unavailable;
}

function text(value: unknown): string {
  return typeof value === "string" && value.trim().length > 0 ? value : unavailable;
}

export function SovereignCommandPost() {
  const [status, setStatus] = useState<SecurityStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function refreshSecurityPosture() {
      try {
        const nextStatus = await getSecurityStatus();
        if (!cancelled) {
          setStatus(nextStatus);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Security posture unavailable");
      }
    }

    void refreshSecurityPosture();
    const heartbeat = window.setInterval(() => void refreshSecurityPosture(), 1000);
    return () => {
      cancelled = true;
      window.clearInterval(heartbeat);
    };
  }, []);

  const monitor = status?.defense_systems?.stabilizer_monitor || {};
  const pool = status?.defense_systems?.preallocated_ancilla_trap_pool || {};
  const rotationWidth = typeof monitor.syndrome_rotation_index === "number" ? Math.min(100, (monitor.syndrome_rotation_index / 24) * 100) : 0;
  const mode = text(monitor.operating_mode);
  const isCritical = mode === "SANITIZED";

  return (
    <div className="rounded-[2rem] border border-cyan-400/20 bg-slate-950 p-6 text-cyan-100 shadow-2xl shadow-cyan-950/30">
      <div className="mb-5 flex items-center justify-between gap-3">
        <div>
          <p className="font-mono text-[10px] font-bold uppercase tracking-[0.28em] text-cyan-300">SOVEREIGN_SECURITY_POSTURE</p>
          <h2 className="mt-2 flex items-center gap-2 text-xl font-black text-white"><ShieldCheck className="h-5 w-5 text-cyan-300" /> Unitary Shield Command Post</h2>
        </div>
        <span className={`rounded-full px-3 py-1 font-mono text-[10px] font-bold ${mode === "NORMAL" ? "bg-emerald-400/15 text-emerald-200" : "bg-amber-400/15 text-amber-200"}`}>{mode}</span>
      </div>

      {error && <div className="mb-4 rounded-xl border border-red-400/30 bg-red-950/40 p-3 font-mono text-xs text-red-100">{error}</div>}

      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-2xl border border-cyan-400/10 bg-cyan-950/20 p-4 font-mono text-xs leading-6">
          <p>MODE: <span className={mode === "NORMAL" ? "text-emerald-300" : "text-amber-300"}>{mode}</span></p>
          <p>STRIDE: {num(monitor.syndrome_check_stride)}</p>
          <p>CHECK_FREQUENCY: {pct(monitor.check_frequency)}</p>
          <p>POOL_HEALTH: {num(pool.active_ancillas)} / {num(pool.max_ancilla_pool)}</p>
        </div>
        <div className="rounded-2xl border border-cyan-400/10 bg-cyan-950/20 p-4 font-mono text-xs leading-6">
          <p>SYNDROME_WEIGHT: {num(monitor.syndrome_weight)}</p>
          <p>CONFIDENCE: {pct(monitor.confidence)}</p>
          <p>PERMUTATION_CHECKSUM: 0x{typeof monitor.pool_permutation_checksum === "number" ? monitor.pool_permutation_checksum.toString(16) : unavailable}</p>
          <p>SANITIZED: {monitor.sanitized ? "YES" : "NO"}</p>
        </div>
      </div>

      <div className="mt-4 rounded-2xl border border-cyan-400/10 bg-black/60 p-4">
        <p className="mb-2 font-mono text-[10px] uppercase tracking-[0.22em] text-cyan-300">CLIFFORD_BASIS_ROTATION</p>
        <div className="h-2 overflow-hidden rounded-full bg-cyan-950">
          <div className="h-full rounded-full bg-cyan-300 transition-all duration-500" style={{ width: `${rotationWidth}%` }} />
        </div>
      </div>

      {isCritical && <div className="mt-4 animate-pulse rounded-xl border border-red-400/30 bg-red-950/70 p-3 text-center font-mono text-xs font-bold text-red-100">CRITICAL: UNITARY_SANITIZATION_COMPLETE</div>}
    </div>
  );
}
