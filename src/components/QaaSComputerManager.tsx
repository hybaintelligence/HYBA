import React, { useEffect, useState } from "react";
import { AlertCircle, Atom, ChevronRight, FileCheck2, MoonStar, Play, Plus, RefreshCw, Scale, Square } from "lucide-react";
import {
  type ComputerState,
  type FaultTolerantComputerResponse,
  type IsolationMode,
  type ProvisionFaultTolerantComputerRequest,
  type QaaSTier,
  listQaaSComputers,
  provisionCustomerQaaSComputer,
  provisionQaaSComputer,
  startQaaSComputer,
  stopQaaSComputer,
} from "../apiClient";
import { useAuth } from "./AuthProvider";
import { useSkillMode } from "../skillMode";
import { MetricExplainerCard } from "./IntelligenceTranslator";

interface QaaSComputerManagerProps {
  token: string | null;
}

type QiaPresetName =
  | "Starter QI Rail"
  | "Enterprise Strategy Rail"
  | "Regulated Evidence Rail"
  | "Sovereign Oracle Rail"
  | "Research/Expert QI Rail";

type GovernanceLevel = "strict" | "balanced" | "relaxed";

interface QiaPreset extends Omit<ProvisionFaultTolerantComputerRequest, "name"> {
  governance: GovernanceLevel;
  description: string;
}

const qiaPresets: Record<QiaPresetName, QiaPreset> = {
  "Starter QI Rail": {
    tier: "developer",
    isolation: "single-tenant",
    code_distance: 5,
    logical_qubits: 16,
    physical_error_rate: 0.002,
    phi_resonance_target: 0.93,
    max_circuit_depth: 512,
    max_shots: 512,
    admin_privileged: false,
    data_residency: "us",
    allowed_operations: ["state_vector_summary", "governance_audit"],
    governance: "balanced",
    description: "Development-friendly QI rail for exploration and testing with balanced governance.",
  },
  "Enterprise Strategy Rail": {
    tier: "production",
    isolation: "single-tenant",
    code_distance: 7,
    logical_qubits: 64,
    physical_error_rate: 0.001,
    phi_resonance_target: 0.9565,
    max_circuit_depth: 2048,
    max_shots: 2048,
    admin_privileged: false,
    data_residency: "us",
    allowed_operations: ["surface_code_cycle", "phi_resonance_analysis", "state_vector_summary", "substrate_orchestration", "governance_audit"],
    governance: "balanced",
    description: "Production-grade QI rail for enterprise strategy with standard governance.",
  },
  "Regulated Evidence Rail": {
    tier: "production",
    isolation: "dedicated-control-plane",
    code_distance: 11,
    logical_qubits: 96,
    physical_error_rate: 0.0005,
    phi_resonance_target: 0.972,
    max_circuit_depth: 4096,
    max_shots: 4096,
    admin_privileged: false,
    data_residency: "us",
    allowed_operations: ["surface_code_cycle", "phi_resonance_analysis", "state_vector_summary", "governance_audit"],
    governance: "strict",
    description: "High-compliance QI rail for regulated industries with strict governance and evidence requirements.",
  },
  "Sovereign Oracle Rail": {
    tier: "sovereign",
    isolation: "sovereign-isolated",
    code_distance: 15,
    logical_qubits: 128,
    physical_error_rate: 0.0001,
    phi_resonance_target: 0.986,
    max_circuit_depth: 8192,
    max_shots: 8192,
    admin_privileged: false,
    data_residency: "us",
    allowed_operations: ["surface_code_cycle", "phi_resonance_analysis", "state_vector_summary", "substrate_orchestration", "governance_audit"],
    governance: "strict",
    description: "Maximum isolation and sovereignty with strict governance for critical strategic intelligence.",
  },
  "Research/Expert QI Rail": {
    tier: "developer",
    isolation: "single-tenant",
    code_distance: 9,
    logical_qubits: 128,
    physical_error_rate: 0.001,
    phi_resonance_target: 0.9565,
    max_circuit_depth: 16384,
    max_shots: 8192,
    admin_privileged: false,
    data_residency: "us",
    allowed_operations: ["surface_code_cycle", "phi_resonance_analysis", "state_vector_summary", "substrate_orchestration", "governance_audit"],
    governance: "relaxed",
    description: "Expert research rail with relaxed governance for quantum experimentation and advanced algorithms.",
  },
};

const presetNames = Object.keys(qiaPresets) as QiaPresetName[];

export default function QaaSComputerManager({ token }: QaaSComputerManagerProps) {
  const { isAdmin } = useAuth();
  const { isExpertMode } = useSkillMode();
  const [computers, setComputers] = useState<FaultTolerantComputerResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedComputer, setSelectedComputer] = useState<FaultTolerantComputerResponse | null>(null);
  const [showProvisionModal, setShowProvisionModal] = useState(false);
  const [selectedPreset, setSelectedPreset] = useState<QiaPresetName>("Enterprise Strategy Rail");
  const [provisionForm, setProvisionForm] = useState<ProvisionFaultTolerantComputerRequest>({ name: "", ...qiaPresets["Enterprise Strategy Rail"] });

  const applyPreset = (presetName: QiaPresetName) => {
    const preset = qiaPresets[presetName];
    setSelectedPreset(presetName);
    setProvisionForm((current) => ({ 
      ...current, 
      ...preset, 
      tier: preset.tier === "sovereign" && !isAdmin ? "production" : preset.tier, 
      isolation: preset.isolation === "sovereign-isolated" && !isAdmin ? "single-tenant" : preset.isolation 
    }));
  };

  const fetchComputers = async () => {
    if (!token) { 
      setLoading(false); 
      return; 
    }
    setLoading(true); 
    setError(null);
    try { 
      setComputers(await listQaaSComputers()); 
    } catch (err) { 
      setError(err instanceof Error ? err.message : "Failed to fetch QI rails"); 
    } finally { 
      setLoading(false); 
    }
  };

  const handleStart = async (computerId: string) => {
    try {
      await startQaaSComputer(computerId);
      await fetchComputers();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start computer");
    }
  };

  const handleStop = async (computerId: string) => {
    try {
      await stopQaaSComputer(computerId);
      await fetchComputers();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to stop computer");
    }
  };

  const handleProvision = async (e: React.FormEvent) => {
    e.preventDefault(); 
    if (!token) return;
    try {
      if (isAdmin) {
        await provisionQaaSComputer(provisionForm);
      } else { 
        const { admin_privileged, ...customerForm } = provisionForm; 
        await provisionCustomerQaaSComputer(customerForm); 
      }
      setShowProvisionModal(false); 
      await fetchComputers();
    } catch (err) { 
      setError(err instanceof Error ? err.message : "Failed to provision QI rail"); 
    }
  };

  const getStateColor = (state: ComputerState) => {
    switch (state) {
      case "running":
        return "text-emerald-600 bg-emerald-50 border-emerald-200";
      case "stopped":
        return "text-slate-600 bg-slate-50 border-slate-200";
      case "provisioned":
        return "text-blue-600 bg-blue-50 border-blue-200";
      default:
        return "text-slate-600 bg-slate-50 border-slate-200";
    }
  };

  const getTierColor = (tier: QaaSTier) => {
    switch (tier) {
      case "sovereign":
        return "text-purple-600 bg-purple-50 border-purple-200";
      case "production":
        return "text-blue-600 bg-blue-50 border-blue-200";
      case "developer":
        return "text-slate-600 bg-slate-50 border-slate-200";
      default:
        return "text-slate-600 bg-slate-50 border-slate-200";
    }
  };

  return (
    <div className="space-y-6">
      <div className="rounded-3xl border border-violet-200 bg-gradient-to-br from-violet-50 via-white to-indigo-50 p-6 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className="font-mono text-xs font-bold uppercase tracking-[0.24em] text-violet-700">Quantum Intelligence · deep brain</p>
            <h2 className="mt-2 flex items-center gap-2 text-2xl font-black text-slate-950">
              <Atom className="h-6 w-6 text-violet-600" /> QIaaS Simulation Manager
            </h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-700">
              Calm strategic reasoning rail for active simulations, φ-resonance stability, evidence seals, causal stability, proof weight, and counterfactual depth. QI explainers intentionally avoid process-log language.
            </p>
          </div>
          <button onClick={() => setShowProvisionModal(true)} className="flex items-center gap-2 rounded-xl bg-violet-600 px-4 py-2 font-semibold text-white hover:bg-violet-700">
            <Plus className="h-4 w-4" /> Provision QI Rail
          </button>
        </div>
        <div className="mt-5 grid gap-3 md:grid-cols-4">
          {([
            ["Active simulations", computers.filter((c) => c.state === "running").length, MoonStar], 
            ["Resonance stability", "φ-locked", Atom], 
            ["Evidence seals", "gold", FileCheck2], 
            ["Proof weight", "invariant", Scale]
          ] as const).map(([label, value, Icon]) => { 
            const MetricIcon = Icon as typeof Atom; 
            return (
              <div key={String(label)} className="rounded-2xl border border-violet-100 bg-white p-4">
                <MetricIcon className="h-4 w-4 text-violet-600" />
                <p className="mt-2 font-mono text-[10px] uppercase tracking-[0.16em] text-violet-700">{label}</p>
                <p className="text-lg font-black text-slate-950">{String(value)}</p>
              </div>
            ); 
          })}
        </div>
      </div>
      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-4 text-red-800">
          <AlertCircle className="h-5 w-5" />
          <span>{error}</span>
        </div>
      )}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="h-8 w-8 animate-spin text-violet-500" />
        </div>
      ) : computers.length === 0 ? (
        <div className="rounded-lg border border-dashed border-violet-300 p-12 text-center">
          <Atom className="mx-auto h-12 w-12 text-violet-500" />
          <p className="mt-4 text-slate-600">No Quantum Intelligence rails provisioned</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {computers.map((computer) => (
            <div key={computer.computer_id} className="rounded-lg border border-violet-100 bg-white p-6 shadow-sm">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex flex-wrap items-center gap-3">
                    <h3 className="text-lg font-semibold text-slate-900">{computer.name}</h3>
                    <span className={`rounded-full border px-2.5 py-1 text-xs font-medium ${getStateColor(computer.state)}`}>{computer.state.toUpperCase()}</span>
                    <span className={`rounded-full border px-2.5 py-1 text-xs font-medium ${getTierColor(computer.tier)}`}>{computer.tier.toUpperCase()}</span>
                  </div>
                  <div className="mt-3 grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-slate-600">Computer ID:</span>
                      <span className="ml-2 font-mono text-slate-900">{computer.computer_id}</span>
                    </div>
                    <div>
                      <span className="text-slate-600">Isolation:</span>
                      <span className="ml-2 font-mono text-slate-900">{computer.isolation}</span>
                    </div>
                  </div>
                  <div className="mt-3 rounded-lg border border-violet-100 bg-violet-50 p-3 text-xs text-violet-950">
                    <strong>QI proof tier:</strong> Gold-Standard Seal · immutable evidence seal and invariant proof explain why a strategic decision is true within its claim boundary.
                  </div>
                </div>
                <div className="flex gap-2">
                  {computer.state === "stopped" || computer.state === "provisioned" ? (
                    <button onClick={() => handleStart(computer.computer_id)} className="flex items-center gap-1 rounded-lg bg-violet-600 px-3 py-2 text-white">
                      <Play className="h-4 w-4" /> Start
                    </button>
                  ) : (
                    <button onClick={() => handleStop(computer.computer_id)} className="flex items-center gap-1 rounded-lg bg-slate-600 px-3 py-2 text-white">
                      <Square className="h-4 w-4" /> Stop
                    </button>
                  )}
                  <button onClick={() => setSelectedComputer(computer)} className="flex items-center gap-1 rounded-lg border border-slate-300 px-3 py-2 text-slate-700 hover:bg-slate-50">
                    Details <ChevronRight className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      {selectedComputer && (
        <div className="rounded-2xl border border-violet-200 bg-violet-50 p-4 text-sm text-violet-950">
          <strong>Selected QI rail:</strong> {selectedComputer.name} · Active Simulations are provisioned independently from CI operational jobs.
        </div>
      )}
      {showProvisionModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-full max-w-2xl rounded-lg bg-white p-6 shadow-xl">
            <h3 className="mb-4 text-xl font-bold text-slate-900">Provision Quantum Intelligence Rail</h3>
            <form onSubmit={handleProvision} className="space-y-4">
              <div className="rounded-xl border border-violet-100 bg-violet-50 p-4">
                <p className="text-sm font-semibold text-violet-950">Choose a strategy preset</p>
                <div className="mt-3 grid gap-2 sm:grid-cols-2">
                  {presetNames.map((name) => (
                    <button key={name} type="button" onClick={() => applyPreset(name)} className={`rounded-lg border px-3 py-2 text-left text-xs font-semibold ${selectedPreset === name ? "border-violet-500 bg-violet-100 text-violet-950" : "border-violet-200 bg-white text-violet-900"}`}>{name}</button>
                  ))}
                </div>
                <p className="mt-2 text-xs text-violet-800">
                  {isExpertMode ? "Expert lens exposes raw quantum intelligence parameters." : "Business lenses use presets; raw quantum parameters are optional."}
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700">Rail Name</label>
                <input required value={provisionForm.name} onChange={(e) => setProvisionForm({ ...provisionForm, name: e.target.value })} className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" placeholder="strategy-qi-rail" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700">Service Tier</label>
                  <select value={provisionForm.tier} onChange={(e) => setProvisionForm({ ...provisionForm, tier: e.target.value as QaaSTier })} className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2">
                    <option value="developer">Developer</option>
                    <option value="production">Production</option>
                    {isAdmin && <option value="sovereign">Sovereign</option>}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700">Isolation Mode</label>
                  <select value={provisionForm.isolation} onChange={(e) => setProvisionForm({ ...provisionForm, isolation: e.target.value as IsolationMode })} className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2">
                    <option value="single-tenant">Single Tenant</option>
                    {isAdmin && <option value="dedicated-control-plane">Dedicated Control Plane</option>}
                    {isAdmin && <option value="sovereign-isolated">Sovereign Isolated</option>}
                  </select>
                </div>
              </div>
              <div className="flex justify-end gap-3">
                <button type="button" onClick={() => setShowProvisionModal(false)} className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50">Cancel</button>
                <button type="submit" className="rounded-lg bg-violet-600 px-4 py-2 text-sm font-semibold text-white hover:bg-violet-700">Provision</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
