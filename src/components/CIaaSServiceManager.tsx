import React, { useEffect, useState } from "react";
import { Activity, AlertCircle, ChevronRight, Cpu, Play, Plus, RefreshCw, Shield, Square, Zap } from "lucide-react";
import {
  type ProvisionComputationalIntelligenceRequest,
  type ServiceResponse,
  type ServiceState,
  type ServiceTier,
  type TenancyMode,
  listCIAASServices,
  provisionCIAASService,
  provisionCustomerCIAASService,
  startCIAASService,
  stopCIAASService,
} from "../apiClient";
import { useAuth } from "./AuthProvider";
import { useSkillMode } from "./SkillModeContext";
import { MetricExplainerCard } from "./IntelligenceTranslator";

interface CIaaSServiceManagerProps {
  token: string | null;
}

type CIaaSPresetName =
  | "Starter CI Rail"
  | "Enterprise Operations Rail"
  | "Regulated Regeneration Rail"
  | "Sovereign Autonomy Rail"
  | "Research/Expert CI Rail";

type GovernanceLevel = "strict" | "balanced" | "relaxed";

interface CIaaSPreset extends Omit<ProvisionComputationalIntelligenceRequest, "name"> {
  governance: GovernanceLevel;
  description: string;
}

const ciaasPresets: Record<CIaaSPresetName, CIaaSPreset> = {
  "Starter CI Rail": {
    service_tier: "developer",
    tenancy: "single-tenant",
    code_distance: 5,
    logical_compute_units: 16,
    physical_error_rate: 0.002,
    max_workloads_per_minute: 30,
    max_context_bytes: 32000,
    admin_privileged: false,
    data_residency: "us",
    allowed_workloads: ["explain", "substrate_health"],
    governance: "balanced",
    description: "Development-friendly CI rail for exploration and testing with balanced governance.",
  },
  "Enterprise Operations Rail": {
    service_tier: "production",
    tenancy: "single-tenant",
    code_distance: 7,
    logical_compute_units: 64,
    physical_error_rate: 0.001,
    max_workloads_per_minute: 120,
    max_context_bytes: 128000,
    admin_privileged: false,
    data_residency: "us",
    allowed_workloads: ["explain", "orchestrate", "governance_audit", "substrate_health"],
    governance: "balanced",
    description: "Production-grade CI rail for enterprise operations with standard governance.",
  },
  "Regulated Regeneration Rail": {
    service_tier: "production",
    tenancy: "dedicated-control-plane",
    code_distance: 11,
    logical_compute_units: 96,
    physical_error_rate: 0.0005,
    max_workloads_per_minute: 90,
    max_context_bytes: 192000,
    admin_privileged: false,
    data_residency: "us",
    allowed_workloads: ["explain", "orchestrate", "governance_audit", "substrate_health"],
    governance: "strict",
    description: "High-compliance CI rail for regulated industries with strict governance and audit requirements.",
  },
  "Sovereign Autonomy Rail": {
    service_tier: "sovereign",
    tenancy: "sovereign-isolated",
    code_distance: 15,
    logical_compute_units: 128,
    physical_error_rate: 0.0001,
    max_workloads_per_minute: 60,
    max_context_bytes: 256000,
    admin_privileged: false,
    data_residency: "us",
    allowed_workloads: ["explain", "orchestrate", "governance_audit", "substrate_health"],
    governance: "strict",
    description: "Maximum isolation and sovereignty with strict governance for critical infrastructure.",
  },
  "Research/Expert CI Rail": {
    service_tier: "developer",
    tenancy: "single-tenant",
    code_distance: 9,
    logical_compute_units: 128,
    physical_error_rate: 0.001,
    max_workloads_per_minute: 180,
    max_context_bytes: 256000,
    admin_privileged: false,
    data_residency: "us",
    allowed_workloads: ["explain", "orchestrate", "counterfactual", "governance_audit", "substrate_health"],
    governance: "relaxed",
    description: "Expert research rail with relaxed governance for experimentation and advanced workloads.",
  },
};

const presetNames = Object.keys(ciaasPresets) as CIaaSPresetName[];

export default function CIaaSServiceManager({ token }: CIaaSServiceManagerProps) {
  const { isAdmin } = useAuth();
  const { isExpertMode } = useSkillMode();
  const profile = { showTechnicalDefaults: isExpertMode };
  const [services, setServices] = useState<ServiceResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedService, setSelectedService] = useState<ServiceResponse | null>(null);
  const [showProvisionModal, setShowProvisionModal] = useState(false);
  const [selectedPreset, setSelectedPreset] = useState<CIaaSPresetName>("Enterprise Operations Rail");
  const [provisionForm, setProvisionForm] = useState<ProvisionComputationalIntelligenceRequest>({
    name: "",
    ...ciaasPresets["Enterprise Operations Rail"],
  });

  const applyPreset = (presetName: CIaaSPresetName) => {
    const preset = ciaasPresets[presetName];
    setSelectedPreset(presetName);
    setProvisionForm((current) => ({
      ...current,
      ...preset,
      service_tier: preset.service_tier === "sovereign" && !isAdmin ? "production" : preset.service_tier,
      tenancy: preset.tenancy === "sovereign-isolated" && !isAdmin ? "single-tenant" : preset.tenancy,
    }));
  };

  const fetchServices = async () => {
    if (!token) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setServices(await listCIAASServices());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch CIaaS services");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchServices();
  }, [token]);

  const handleStart = async (serviceId: string) => {
    try {
      await startCIAASService(serviceId);
      await fetchServices();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start service");
    }
  };

  const handleStop = async (serviceId: string) => {
    try {
      await stopCIAASService(serviceId);
      await fetchServices();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to stop service");
    }
  };

  const handleProvision = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    try {
      if (isAdmin) await provisionCIAASService(provisionForm);
      else {
        const { admin_privileged, ...customerForm } = provisionForm;
        await provisionCustomerCIAASService(customerForm);
      }
      setShowProvisionModal(false);
      await fetchServices();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to provision service");
    }
  };

  const getStateColor = (state: ServiceState) =>
    state === "running" ? "text-emerald-700 bg-emerald-50 border-emerald-200" : state === "provisioned" ? "text-blue-700 bg-blue-50 border-blue-200" : "text-slate-600 bg-slate-50 border-slate-200";
  const getTierColor = (tier: ServiceTier) =>
    tier === "sovereign" ? "text-purple-700 bg-purple-50 border-purple-200" : tier === "production" ? "text-blue-700 bg-blue-50 border-blue-200" : "text-slate-600 bg-slate-50 border-slate-200";

  return (
    <div className="space-y-6">
      <div className="rounded-3xl border border-emerald-200 bg-gradient-to-br from-emerald-50 to-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className="font-mono text-xs font-bold uppercase tracking-[0.24em] text-emerald-700">Computational Intelligence · broad brain</p>
            <h2 className="mt-2 flex items-center gap-2 text-2xl font-black text-slate-950"><Cpu className="h-6 w-6 text-emerald-600" /> CIaaS Service Manager</h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-700">Self-healing operations rail for active jobs, Salamander regeneration events, substrate coherence, uptime, velocity, and process efficiency. CI alerts intentionally avoid qubits and resonance language.</p>
          </div>
          <button onClick={() => setShowProvisionModal(true)} className="flex items-center gap-2 rounded-xl bg-emerald-600 px-4 py-2 font-semibold text-white hover:bg-emerald-700"><Plus className="h-4 w-4" /> Provision CI Rail</button>
        </div>
        <div className="mt-5 grid gap-3 md:grid-cols-4">
          {([['Active jobs', services.filter((s) => s.state === 'running').length, Activity], ['Regeneration events', 'audit-ready', RefreshCw], ['System health', loading ? 'syncing' : 'coherent', Shield], ['Efficiency', 'self-healing', Zap]] as const).map(([label, value, Icon]) => {
            const MetricIcon = Icon as typeof Activity;
            return <div key={String(label)} className="rounded-2xl border border-emerald-100 bg-white p-4"><MetricIcon className="h-4 w-4 text-emerald-600" /><p className="mt-2 font-mono text-[10px] uppercase tracking-[0.16em] text-emerald-700">{label}</p><p className="text-lg font-black text-slate-950">{String(value)}</p></div>;
          })}
        </div>
      </div>

      {error && <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-4 text-red-800"><AlertCircle className="h-5 w-5" /><span>{error}</span></div>}
      {loading ? <div className="flex items-center justify-center py-12"><RefreshCw className="h-8 w-8 animate-spin text-emerald-500" /></div> : services.length === 0 ? <div className="rounded-lg border border-dashed border-emerald-300 p-12 text-center"><Cpu className="mx-auto h-12 w-12 text-emerald-500" /><p className="mt-4 text-slate-600">No Computational Intelligence rails provisioned</p></div> : <div className="grid gap-4">{services.map((service) => <div key={service.service_id} className="rounded-lg border border-emerald-100 bg-white p-6 shadow-sm"><div className="flex items-start justify-between gap-4"><div className="flex-1"><div className="flex flex-wrap items-center gap-3"><h3 className="text-lg font-semibold text-slate-900">{service.name}</h3><span className={`rounded-full border px-2.5 py-1 text-xs font-medium ${getStateColor(service.state)}`}>{service.state.toUpperCase()}</span><span className={`rounded-full border px-2.5 py-1 text-xs font-medium ${getTierColor(service.service_tier)}`}>{service.service_tier.toUpperCase()}</span></div><div className="mt-3 grid grid-cols-2 gap-4 text-sm"><div><span className="text-slate-600">Service ID:</span><span className="ml-2 font-mono text-slate-900">{service.service_id}</span></div><div><span className="text-slate-600">Tenancy:</span><span className="ml-2 font-mono text-slate-900">{service.tenancy}</span></div></div><div className="mt-3 rounded-lg border border-emerald-100 bg-emerald-50 p-3 text-xs text-emerald-950"><strong>CI proof tier:</strong> Standard Audit Stamp · operational logs and regeneration audit trail explain why the system fixed or escalated a workflow.</div></div><div className="flex gap-2">{service.state === "stopped" || service.state === "provisioned" ? <button onClick={() => startCIAASService(service.service_id).then(fetchServices)} className="flex items-center gap-1 rounded-lg bg-emerald-600 px-3 py-2 text-white"><Play className="h-4 w-4" />Start</button> : <button onClick={() => stopCIAASService(service.service_id).then(fetchServices)} className="flex items-center gap-1 rounded-lg bg-slate-600 px-3 py-2 text-white"><Square className="h-4 w-4" />Stop</button>}<button onClick={() => setSelectedService(service)} className="flex items-center gap-1 rounded-lg border border-slate-300 px-3 py-2 text-slate-700">Details<ChevronRight className="h-4 w-4" /></button></div></div></div>)}</div>}

      {showProvisionModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-full max-w-2xl rounded-lg bg-white p-6 shadow-xl">
            <h3 className="mb-4 text-xl font-bold text-slate-900">Provision Intelligence Rail</h3>
            <form onSubmit={handleProvision} className="space-y-4">
              <div className="rounded-xl border border-blue-100 bg-blue-50 p-4">
                <p className="text-sm font-semibold text-blue-950">Choose a business preset</p>
                <div className="mt-3 grid gap-2 sm:grid-cols-2">
                  {[["starter", "Starter Intelligence Rail"], ["enterprise", "Enterprise Decision Rail"], ["regulated", "Regulated Evidence Rail"], ["sovereign", "Sovereign Isolated Rail"], ["research", "Research/Expert Rail"]].map(([value, label]) => (
                    <button key={value} type="button" onClick={() => applyPreset(value as any)} className="rounded-lg border border-blue-200 bg-white px-3 py-2 text-left text-xs font-semibold text-blue-900 hover:bg-blue-100">{label}</button>
                  ))}
                </div>
                <p className="mt-2 text-xs text-blue-800">{isExpertMode ? "Technical fields are visible for this lens." : "Technical fields are hidden by default; presets map to safe defaults."}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700">Service Name</label>
                <input
                  type="text"
                  required
                  value={provisionForm.name}
                  onChange={(e) => setProvisionForm({ ...provisionForm, name: e.target.value })}
                  className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
                  placeholder="my-ciaas-service"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700">Service Tier</label>
                  <select
                    value={provisionForm.service_tier}
                    onChange={(e) =>
                      setProvisionForm({
                        ...provisionForm,
                        service_tier: e.target.value as ServiceTier,
                      })
                    }
                    className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
                  >
                    <option value="developer">Developer</option>
                    <option value="production">Production</option>
                    {isAdmin && <option value="sovereign">Sovereign</option>}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700">Tenancy Mode</label>
                  <select
                    value={provisionForm.tenancy}
                    onChange={(e) =>
                      setProvisionForm({ ...provisionForm, tenancy: e.target.value as TenancyMode })
                    }
                    className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
                  >
                    <option value="single-tenant">Single Tenant</option>
                    {isAdmin && (
                      <option value="dedicated-control-plane">Dedicated Control Plane</option>
                    )}
                    {isAdmin && <option value="sovereign-isolated">Sovereign Isolated</option>}
                  </select>
                </div>
              </div>

      {showProvisionModal && <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"><div className="w-full max-w-2xl rounded-lg bg-white p-6 shadow-xl"><h3 className="mb-4 text-xl font-bold text-slate-900">Provision Computational Intelligence Rail</h3><form onSubmit={handleProvision} className="space-y-4"><div className="rounded-xl border border-emerald-100 bg-emerald-50 p-4"><p className="text-sm font-semibold text-emerald-950">Choose an operations preset</p><div className="mt-3 grid gap-2 sm:grid-cols-2">{presetNames.map((name) => <button key={name} type="button" onClick={() => applyPreset(name)} className={`rounded-lg border px-3 py-2 text-left text-xs font-semibold ${selectedPreset === name ? 'border-emerald-500 bg-emerald-100 text-emerald-950' : 'border-emerald-200 bg-white text-emerald-900'}`}>{name}</button>)}</div></div><div><label className="block text-sm font-medium text-slate-700">Service Name</label><input required value={provisionForm.name} onChange={(e) => setProvisionForm({ ...provisionForm, name: e.target.value })} className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" placeholder="operations-ci-rail" /></div><div className="grid grid-cols-2 gap-4"><div><label className="block text-sm font-medium text-slate-700">Service Tier</label><select value={provisionForm.service_tier} onChange={(e) => setProvisionForm({ ...provisionForm, service_tier: e.target.value as ServiceTier })} className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"><option value="developer">Developer</option><option value="production">Production</option>{isAdmin && <option value="sovereign">Sovereign</option>}</select></div><div><label className="block text-sm font-medium text-slate-700">Tenancy Mode</label><select value={provisionForm.tenancy} onChange={(e) => setProvisionForm({ ...provisionForm, tenancy: e.target.value as TenancyMode })} className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"><option value="single-tenant">Single Tenant</option>{isAdmin && <option value="dedicated-control-plane">Dedicated Control Plane</option>}{isAdmin && <option value="sovereign-isolated">Sovereign Isolated</option>}</select></div></div><MetricExplainerCard metric="substrate_coherence" engine="ci" />{isExpertMode && <div className="grid grid-cols-2 gap-4"><div><label className="block text-sm font-medium text-slate-700">Regeneration Resilience</label><input type="number" min="3" max="31" step="2" value={provisionForm.code_distance} onChange={(e) => setProvisionForm({ ...provisionForm, code_distance: parseInt(e.target.value, 10) })} className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" /></div><div><label className="block text-sm font-medium text-slate-700">Logical Compute Units</label><input type="number" min="1" max="512" value={provisionForm.logical_compute_units} onChange={(e) => setProvisionForm({ ...provisionForm, logical_compute_units: parseInt(e.target.value, 10) })} className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" /></div></div>}<div className="flex justify-end gap-2"><button type="button" onClick={() => setShowProvisionModal(false)} className="rounded-lg border border-slate-300 px-4 py-2 text-slate-700">Cancel</button><button type="submit" className="rounded-lg bg-emerald-600 px-4 py-2 text-white">Provision CI Rail</button></div></form></div></div>}
    </div>
  );
}
