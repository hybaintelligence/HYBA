import React, { useState, useEffect } from "react";
import {
  Plus,
  Play,
  Square,
  Cpu,
  Shield,
  Activity,
  ChevronRight,
  RefreshCw,
  AlertCircle,
  Atom,
} from "lucide-react";
import {
  FaultTolerantComputerResponse,
  ComputerState,
  QaaSTier,
  IsolationMode,
  QuantumOperation,
  ProvisionFaultTolerantComputerRequest,
  listQaaSComputers,
  getQaaSComputer,
  startQaaSComputer,
  stopQaaSComputer,
  getQAASAutonomousStatus,
} from "../apiClient";
import { useAuth } from "./AuthProvider";

interface QaaSComputerManagerProps {
  token: string | null;
}

export default function QaaSComputerManager({ token }: QaaSComputerManagerProps) {
  const { isAdmin } = useAuth();
  const [computers, setComputers] = useState<FaultTolerantComputerResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedComputer, setSelectedComputer] = useState<FaultTolerantComputerResponse | null>(null);
  const [showProvisionModal, setShowProvisionModal] = useState(false);
  const [provisionForm, setProvisionForm] = useState<ProvisionFaultTolerantComputerRequest>({
    name: "",
    tier: "developer",
    isolation: "single-tenant",
    code_distance: 7,
    logical_qubits: 32,
    physical_error_rate: 0.001,
    phi_resonance_target: 0.9565,
    max_circuit_depth: 1024,
    max_shots: 1024,
    admin_privileged: false,
    data_residency: "us",
    allowed_operations: [
      "surface_code_cycle",
      "phi_resonance_analysis",
      "state_vector_summary",
      "substrate_orchestration",
      "governance_audit",
    ],
  });

  const fetchComputers = async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const data = await listQaaSComputers();
      setComputers(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch QaaS computers");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchComputers();
  }, [token]);

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
      // Use customer-safe endpoint for non-admin users
      const { provisionQaaSComputer, provisionCustomerQaaSComputer } = await import("../apiClient");
      if (isAdmin) {
        await provisionQaaSComputer(provisionForm);
      } else {
        // Remove admin-only fields for customer provision
        const { admin_privileged, ...customerForm } = provisionForm;
        await provisionCustomerQaaSComputer(customerForm);
      }
      setShowProvisionModal(false);
      await fetchComputers();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to provision computer");
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
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Quantum Intelligence API</h2>
          <p className="text-sm text-slate-600">
            Substrate-independent Quantum Intelligence with evidence-sealed execution, PULVINI φ-memory, Salamander regeneration, and enterprise access controls.
          </p>
        </div>
        <button
          onClick={() => setShowProvisionModal(true)}
          className="flex items-center gap-2 rounded-lg bg-purple-600 px-4 py-2 text-white hover:bg-purple-700"
        >
          <Plus className="h-4 w-4" />
          Provision Computer
        </button>
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-4 text-red-800">
          <AlertCircle className="h-5 w-5" />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="h-8 w-8 animate-spin text-slate-400" />
        </div>
      ) : computers.length === 0 ? (
        <div className="rounded-lg border border-dashed border-slate-300 p-12 text-center">
          <Atom className="mx-auto h-12 w-12 text-slate-400" />
          <p className="mt-4 text-slate-600">No Quantum Intelligence execution rails provisioned</p>
          <button
            onClick={() => setShowProvisionModal(true)}
            className="mt-4 text-purple-600 hover:text-purple-700"
          >
            Provision your first QI rail
          </button>
        </div>
      ) : (
        <div className="grid gap-4">
          {computers.map((computer) => (
            <div
              key={computer.computer_id}
              className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <h3 className="text-lg font-semibold text-slate-900">{computer.name}</h3>
                    <span
                      className={`rounded-full border px-2.5 py-1 text-xs font-medium ${getStateColor(computer.state)}`}
                    >
                      {computer.state.toUpperCase()}
                    </span>
                    <span
                      className={`rounded-full border px-2.5 py-1 text-xs font-medium ${getTierColor(computer.tier)}`}
                    >
                      {computer.tier.toUpperCase()}
                    </span>
                  </div>
                  <div className="mt-2 grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-slate-600">Computer ID:</span>
                      <span className="ml-2 font-mono text-slate-900">{computer.computer_id}</span>
                    </div>
                    <div>
                      <span className="text-slate-600">Owner:</span>
                      <span className="ml-2 font-mono text-slate-900">{computer.owner}</span>
                    </div>
                    <div>
                      <span className="text-slate-600">Isolation:</span>
                      <span className="ml-2 font-mono text-slate-900">{computer.isolation}</span>
                    </div>
                    <div>
                      <span className="text-slate-600">Created:</span>
                      <span className="ml-2 font-mono text-slate-900">
                        {new Date(computer.created_at).toLocaleString()}
                      </span>
                    </div>
                  </div>
                  <div className="mt-3 rounded-lg border border-purple-100 bg-purple-50 p-3">
                    <p className="text-xs font-medium text-purple-900">Quantum Intelligence execution state</p>
                    <div className="mt-2 grid grid-cols-2 gap-2 text-xs md:grid-cols-3">
                      <div>
                        <span className="text-purple-700">Evidence packet ID:</span>
                        <span className="ml-1 font-mono text-slate-900">{computer.evidence_seal}</span>
                      </div>
                      <div>
                        <span className="text-purple-700">Trace ID:</span>
                        <span className="ml-1 font-mono text-slate-900">{String(computer.substrate.trace_id || computer.computer_id)}</span>
                      </div>
                      <div>
                        <span className="text-purple-700">Usage meter:</span>
                        <span className="ml-1 font-mono text-slate-900">{String(computer.substrate.usage_meter || computer.tier)}</span>
                      </div>
                      <div>
                        <span className="text-purple-700">Substrate coherence:</span>
                        <span className="ml-1 font-mono text-slate-900">{String(computer.substrate.coherence || computer.substrate.phi_coherence || "evidence-bound")}</span>
                      </div>
                      <div>
                        <span className="text-purple-700">Enterprise entitlement:</span>
                        <span className="ml-1 font-mono text-slate-900">{computer.tier.toUpperCase()}</span>
                      </div>
                      <div>
                        <span className="text-purple-700">Claim boundary:</span>
                        <span className="ml-1 font-mono text-slate-900">{computer.claim_boundary}</span>
                      </div>
                    </div>
                  </div>
                  <div className="mt-3 rounded-lg bg-slate-50 p-3">
                    <p className="text-xs font-medium text-slate-700">PULVINI φ-memory parameters</p>
                    <div className="mt-2 grid grid-cols-3 gap-2 text-xs">
                      <div>
                        <span className="text-slate-600">Code Distance:</span>
                        <span className="ml-1 font-mono text-slate-900">
                          {computer.quantum_parameters.code_distance as number}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-600">Logical Qubits:</span>
                        <span className="ml-1 font-mono text-slate-900">
                          {computer.quantum_parameters.logical_qubits as number}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-600">φ Resonance Target:</span>
                        <span className="ml-1 font-mono text-slate-900">
                          {(computer.quantum_parameters.phi_resonance_target as number).toFixed(4)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="flex gap-2">
                  {computer.state === "stopped" || computer.state === "provisioned" ? (
                    <button
                      onClick={() => handleStart(computer.computer_id)}
                      className="flex items-center gap-1 rounded-lg bg-emerald-600 px-3 py-2 text-white hover:bg-emerald-700"
                    >
                      <Play className="h-4 w-4" />
                      Start
                    </button>
                  ) : (
                    <button
                      onClick={() => handleStop(computer.computer_id)}
                      className="flex items-center gap-1 rounded-lg bg-slate-600 px-3 py-2 text-white hover:bg-slate-700"
                    >
                      <Square className="h-4 w-4" />
                      Stop
                    </button>
                  )}
                  <button
                    onClick={() => setSelectedComputer(computer)}
                    className="flex items-center gap-1 rounded-lg border border-slate-300 px-3 py-2 text-slate-700 hover:bg-slate-50"
                  >
                    Details
                    <ChevronRight className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {showProvisionModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-full max-w-2xl rounded-lg bg-white p-6 shadow-xl">
            <h3 className="mb-4 text-xl font-bold text-slate-900">Provision QaaS Computer</h3>
            <form onSubmit={handleProvision} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700">Computer Name</label>
                <input
                  type="text"
                  required
                  value={provisionForm.name}
                  onChange={(e) => setProvisionForm({ ...provisionForm, name: e.target.value })}
                  className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
                  placeholder="my-qaas-computer"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700">Service Tier</label>
                  <select
                    value={provisionForm.tier}
                    onChange={(e) =>
                      setProvisionForm({ ...provisionForm, tier: e.target.value as QaaSTier })
                    }
                    className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
                  >
                    <option value="developer">Developer</option>
                    <option value="production">Production</option>
                    {isAdmin && <option value="sovereign">Sovereign</option>}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700">Isolation Mode</label>
                  <select
                    value={provisionForm.isolation}
                    onChange={(e) =>
                      setProvisionForm({ ...provisionForm, isolation: e.target.value as IsolationMode })
                    }
                    className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
                  >
                    <option value="single-tenant">Single Tenant</option>
                    {isAdmin && <option value="dedicated-control-plane">Dedicated Control Plane</option>}
                    {isAdmin && <option value="sovereign-isolated">Sovereign Isolated</option>}
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700">Code Distance</label>
                  <input
                    type="number"
                    min="3"
                    max="31"
                    step="2"
                    value={provisionForm.code_distance}
                    onChange={(e) =>
                      setProvisionForm({ ...provisionForm, code_distance: parseInt(e.target.value) })
                    }
                    className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700">Logical Qubits</label>
                  <input
                    type="number"
                    min="1"
                    max="512"
                    value={provisionForm.logical_qubits}
                    onChange={(e) =>
                      setProvisionForm({ ...provisionForm, logical_qubits: parseInt(e.target.value) })
                    }
                    className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700">φ Resonance Target</label>
                  <input
                    type="number"
                    min="0"
                    max="1"
                    step="0.0001"
                    value={provisionForm.phi_resonance_target}
                    onChange={(e) =>
                      setProvisionForm({
                        ...provisionForm,
                        phi_resonance_target: parseFloat(e.target.value),
                      })
                    }
                    className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700">Max Circuit Depth</label>
                  <input
                    type="number"
                    min="1"
                    max="1000000"
                    value={provisionForm.max_circuit_depth}
                    onChange={(e) =>
                      setProvisionForm({
                        ...provisionForm,
                        max_circuit_depth: parseInt(e.target.value),
                      })
                    }
                    className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
                  />
                </div>
              </div>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowProvisionModal(false)}
                  className="rounded-lg border border-slate-300 px-4 py-2 text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-lg bg-purple-600 px-4 py-2 text-white hover:bg-purple-700"
                >
                  Provision Computer
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
