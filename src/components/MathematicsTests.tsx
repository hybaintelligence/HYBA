import React, { useState } from "react";
import {
  Play,
  CheckCircle,
  XCircle,
  Terminal,
  HelpCircle,
  ChevronDown,
  ChevronUp,
  Loader,
} from "lucide-react";
import { TestResultItem } from "../types";

export const MathematicsTests: React.FC = () => {
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [results, setResults] = useState<TestResultItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>("normal_conservation");

  const runProofs = async () => {
    setIsRunning(true);
    setError(null);
    try {
      const response = await fetch("/api/tests/run");
      const data = await response.json();
      if (data.success) {
        setResults(data.tests);
      } else {
        setError(data.error || "Proofs execution returned success=false.");
      }
    } catch (err: any) {
      setError("Failed to link with backend API tests runner: " + err.message);
    } finally {
      setIsRunning(false);
    }
  };

  const toggleExpand = (id: string) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

  return (
    <div className="bg-white border border-[#E2E4E9] rounded-xl p-6 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
        <div>
          <div className="flex items-center gap-2">
            <Terminal className="text-[#1A1A1E] w-5 h-5" />
            <h3 className="text-xs font-mono text-[#1A1A1E] font-bold uppercase tracking-wider">
              Quantum Mathematical Verifications
            </h3>
          </div>
          <p className="text-xs text-[#64748B] mt-1 leading-relaxed">
            Execute a strict suite of backend numerical proofs validating space normalization,
            uniform Hadamard entropy bounds, and quadratic Grover scale convergence.
          </p>
        </div>

        <button
          type="button"
          onClick={runProofs}
          disabled={isRunning}
          className="flex items-center gap-2 bg-black hover:bg-black/80 disabled:bg-[#F4F4F7] text-white disabled:text-[#94A3B8] font-mono text-xs font-bold px-4 py-2.5 rounded-lg transition-all active:scale-95 shrink-0 shadow-sm cursor-pointer"
        >
          {isRunning ? (
            <>
              <Loader className="w-4 h-4 animate-spin" />
              <span>COMPUTING PROOFS...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4 fill-current" />
              <span>RUN VERIFICATION PROOFS</span>
            </>
          )}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-xs p-3 rounded-lg mb-4 font-mono">
          <strong>TELEMETRY FAILURE</strong>: {error}
        </div>
      )}

      {/* BEFORE RUNNING */}
      {!results && !isRunning && (
        <div className="bg-[#F8FAFC] border border-[#E2E4E9] rounded-xl p-8 text-center flex flex-col items-center justify-center">
          <Terminal className="text-[#94A3B8] w-12 h-12 mb-3" />
          <p className="text-sm font-mono text-[#1A1A1E] font-medium">
            SYSTEM COHERENCE VERIFICATION UNTESTED
          </p>
          <p className="text-xs text-[#64748B] mt-1 max-w-md">
            Click &quot;Run Verification Proofs&quot; to prompt server-side mathematical matrix
            operations. Tests are executed directly in Node.js to check for phase error tolerances.
          </p>
        </div>
      )}

      {/* LOADER */}
      {isRunning && (
        <div className="bg-[#F8FAFC] border border-[#E2E4E9] rounded-xl p-8 text-center flex flex-col items-center justify-center">
          <div className="relative w-16 h-16 mb-4">
            <div className="absolute inset-0 rounded-full border-4 border-[#E2E4E9] border-t-black animate-spin" />
          </div>
          <p className="text-sm font-mono text-[#1A1A1E] animate-pulse uppercase tracking-wider">
            Solving Wave Equations
          </p>
          <p className="text-xs text-[#64748B] mt-2 max-w-sm">
            Applying Kron tensor products, measuring phase coherence coordinates, and computing
            high-density state transforms.
          </p>
        </div>
      )}

      {/* TEST RESULTS ACCORDION */}
      {results && !isRunning && (
        <div className="space-y-3">
          {results.map((test) => {
            const isExpanded = expandedId === test.id;
            return (
              <div
                key={test.id}
                className={`border rounded-lg transition-all duration-200 ${
                  isExpanded
                    ? "border-[#E2E4E9] bg-[#F8FAFC]"
                    : "border-[#E2E4E9]/60 hover:border-[#E2E4E9] bg-[#F8FAFC]/30"
                }`}
              >
                {/* HEADER ROW */}
                <button
                  type="button"
                  onClick={() => toggleExpand(test.id)}
                  className="w-full flex items-center justify-between p-4 cursor-pointer text-left select-none"
                >
                  <div className="flex items-center gap-3">
                    {test.passed ? (
                      <CheckCircle className="text-green-600 w-5 h-5 shrink-0" />
                    ) : (
                      <XCircle className="text-red-600 w-5 h-5 shrink-0" />
                    )}
                    <div>
                      <h4 className="text-xs font-mono font-bold text-[#1A1A1E] uppercase tracking-wide">
                        {test.name}
                      </h4>
                      <p className="text-[11px] text-[#64748B] line-clamp-1 max-w-xl">
                        {test.description}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-[10px] bg-white border border-[#E2E4E9] font-mono px-2 py-0.5 rounded text-[#64748B] shrink-0">
                      {test.executionTimeMs}ms
                    </span>
                    {isExpanded ? (
                      <ChevronUp className="text-[#64748B] w-4 h-4 shrink-0" />
                    ) : (
                      <ChevronDown className="text-[#64748B] w-4 h-4 shrink-0" />
                    )}
                  </div>
                </button>

                {/* CONTENT SECTION */}
                {isExpanded && (
                  <div className="px-4 pb-4 pt-2 border-t border-[#E2E4E9] font-mono text-xs text-[#334155]">
                    {/* THEOREM BLOCK */}
                    <div className="bg-white border-l-2 border-black rounded p-3 mb-3 border border-[#E2E4E9]">
                      <div className="text-[10px] text-black font-bold uppercase tracking-wider mb-1 flex items-center gap-1">
                        <HelpCircle className="w-3.5 h-3.5" />
                        <span>Core Proof: {test.proofName}</span>
                      </div>
                      <div className="space-y-1.5 pl-1.5 mt-2">
                        {test.proofSteps.map((step, sIdx) => (
                          <div key={sIdx} className="text-[11px] text-[#334155] leading-relaxed">
                            {step}
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* COMPUTATIONAL RAW TELEMETRY OUTPUT */}
                    <div className="bg-white text-[#334155] border border-[#E2E4E9] rounded p-3">
                      <div className="text-[9px] text-[#94A3B8] uppercase font-semibold border-b border-[#E2E4E9] pb-1 mb-2">
                        Subspace Telemetry Logs
                      </div>
                      <div className="text-[10px] leading-relaxed space-y-1 overflow-x-auto text-[#64748B]">
                        {test.computationLogs.map((log, lIdx) => (
                          <div key={lIdx} className="whitespace-pre">
                            {log}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
