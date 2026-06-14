import React, { useState } from "react";
import { Activity, Zap, Shield, Database } from "lucide-react";
import { executePulvini, type PulviniResult } from "../apiClient";

export const PulviniExecutionPanel = () => {
  const [isExecuting, setIsExecuting] = useState(false);
  const [result, setResult] = useState<PulviniResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleExecute = async () => {
    setIsExecuting(true);
    setError(null);
    setResult(null);
    try {
      const data = await executePulvini();

      if (data.status === "error") {
        throw new Error(data.error || data.details || "Execution failed");
      }

      setResult(data);
    } catch (err: unknown) {
      console.error(err);
      setError(
        err instanceof Error ? err.message : "Failed to reach HYBA_Unified_Backend. Is it running?",
      );
    } finally {
      setIsExecuting(false);
    }
  };

  const stateVectorOperation = result?.operations?.[0];
  const projectionOperation = result?.operations?.[1];

  return (
    <section className="bg-white border border-[#E2E4E9] rounded-xl p-6 shadow-sm">
      <div className="flex items-center gap-2 mb-4 justify-between border-b border-[#E2E4E9] pb-3">
        <div className="flex items-center gap-2">
          <Zap className="text-black w-4.5 h-4.5" />
          <h3 className="text-xs font-mono text-[#1A1A1E] font-bold uppercase tracking-wider">
            PULVINI Execution: Mathematical Runtime Surface
          </h3>
        </div>
        <span className="text-[10px] font-mono text-white bg-black px-2 py-0.5 rounded font-bold uppercase">
          Metis Substrate
        </span>
      </div>

      <div className="text-[11px] text-[#64748B] mb-5 leading-relaxed font-sans">
        The PULVINI Memory Engine executes Hilbert-space operators, Hamiltonians, tensor folds, and
        bounded measurement routines as substrate-agnostic linear algebra. CPUs, GPUs, cloud, and
        edge devices are arithmetic substrates; proof-of-work validation remains classically
        verified.
      </div>

      <button
        onClick={handleExecute}
        disabled={isExecuting}
        className="w-full mb-5 bg-black hover:bg-black/80 disabled:bg-[#F4F4F7] text-white disabled:text-[#94A3B8] font-mono text-xs font-bold px-4 py-3 rounded-lg transition-all active:scale-95 shadow-sm cursor-pointer flex justify-center items-center gap-2"
      >
        {isExecuting ? (
          <>
            <Activity className="w-4 h-4 animate-spin text-[#94A3B8]" />
            EXECUTING MATHEMATICAL RUNTIME...
          </>
        ) : (
          <>
            <SettingsIcon /> INITIALIZE METIS SUBSTRATE BATCH
          </>
        )}
      </button>

      {error && (
        <div className="bg-red-50 text-red-600 border border-red-200 rounded-lg p-4 mb-5 text-xs font-mono">
          <strong className="block mb-1">HYBA_Unified_Backend Connection Error:</strong>
          {error}
        </div>
      )}

      {result && result.status === "success" && (
        <div className="space-y-4">
          <div className="bg-[#FAFBFD] border border-[#E2E4E9] rounded-lg p-4">
            <h4 className="font-mono text-xs font-bold text-black uppercase mb-3 flex items-center gap-2">
              <CheckCircleIcon /> 14-Qubit State Execution
            </h4>
            <div className="grid grid-cols-2 gap-3 text-[10px] font-mono text-[#64748B]">
              <div className="flex flex-col">
                <span>State Vector Entries</span>
                <span className="text-black font-bold text-xs">
                  {stateVectorOperation?.state_vector_entries ?? "N/A"}
                </span>
              </div>
              <div className="flex flex-col">
                <span>Invariants</span>
                <span className="text-black font-bold text-xs">
                  {stateVectorOperation?.invariants ?? "N/A"}
                </span>
              </div>
              <div className="col-span-2 flex flex-col">
                <span>Diffusion Norm Purity</span>
                <span className="text-green-700 font-bold text-xs">
                  {typeof stateVectorOperation?.diffusion_norm === "number"
                    ? stateVectorOperation.diffusion_norm.toFixed(10)
                    : "N/A"}
                </span>
              </div>
            </div>
          </div>

          <div className="bg-[#FAFBFD] border border-[#E2E4E9] rounded-lg p-4">
            <h4 className="font-mono text-xs font-bold text-black uppercase mb-3 flex items-center gap-2">
              <Shield className="w-4 h-4 text-black" /> Spectral Hamiltonian Projection
            </h4>
            <div className="grid grid-cols-2 gap-3 text-[10px] font-mono text-[#64748B]">
              <div className="flex flex-col">
                <span>Original Dims</span>
                <span className="text-black font-bold text-xs">
                  {projectionOperation?.original_dimensions !== undefined
                    ? `${projectionOperation.original_dimensions}D`
                    : "N/A"}
                </span>
              </div>
              <div className="flex flex-col">
                <span>Projected Dims</span>
                <span className="text-black font-bold text-xs">
                  {projectionOperation?.projected_dimensions !== undefined
                    ? `${projectionOperation.projected_dimensions}D`
                    : "N/A"}
                </span>
              </div>
              <div className="flex flex-col">
                <span>Topological Anchoring</span>
                <span className="text-black font-bold text-xs capitalize">
                  {projectionOperation?.topological_anchoring ?? "N/A"}
                </span>
              </div>
              <div className="flex flex-col">
                <span>Purity</span>
                <span className="text-black font-bold text-xs">
                  {projectionOperation?.purity ?? "N/A"}
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-4 border-t border-[#E2E4E9] pt-4 mt-2">
            <div className="flex-1 bg-black text-white p-3 rounded-lg text-center">
              <div className="text-[9px] text-gray-400 font-mono uppercase">Metric Compression</div>
              <div className="text-xs font-bold font-mono">
                {result.metric_compression ?? "N/A"}
              </div>
            </div>
            <div className="flex-1 bg-[#F4F4F7] text-black border border-[#E2E4E9] p-3 rounded-lg text-center">
              <div className="text-[9px] text-[#64748B] font-mono uppercase">
                Hamiltonian Generation
              </div>
              <div className="text-xs font-bold font-mono">
                {result.hamiltonian_generation ?? "N/A"}
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  );
};

const SettingsIcon = () => <Activity className="w-4 h-4" />;
const CheckCircleIcon = () => <Database className="w-4 h-4 text-black" />;
