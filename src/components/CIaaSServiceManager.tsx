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
} from "lucide-react";
import {
  ServiceResponse,
  ServiceState,
  ServiceTier,
  TenancyMode,
  WorkloadKind,
  ProvisionComputationalIntelligenceRequest,
  listCIAASServices,
  getCIAASService,
  startCIAASService,
  stopCIAASService,
  getCIAASAutonomousStatus,
  provisionCIAASService,
  provisionCustomerCIAASService,
} from "../apiClient";
import { useAuth } from "./AuthProvider";
import { useSkillMode } from "./SkillModeContext";
import { MetricExplainerCard } from "./IntelligenceTranslator";

interface CIaaSServiceManagerProps {
  token: string | null;
}

type CIaaSPresetName =
  | "Starter Intelligence Rail"
  | "Enterprise Decision Rail"
  | "Regulated Evidence Rail"
  | "Sovereign Isolated Rail"
  | "Research/Expert Rail";

const ciaasPresets: Record<
  CIaaSPresetName,
  Omit<ProvisionComputationalIntelligenceRequest, "name">
> = {
  "Starter Intelligence Rail": {
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
  },
  "Enterprise Decision Rail": {
    service_tier: "production",
    tenancy: "single-tenant",
    code_distance: 7,
    logical_compute_units: 64,
    physical_error_rate: 0.001,
    max_workloads_per_minute: 120,
    max_context_bytes: 128000,
    admin_privileged: false,
    data_residency: "us",
    allowed_workloads: [
      "explain",
      "orchestrate",
      "counterfactual",
      "governance_audit",
      "substrate_health",
    ],
  },
  "Regulated Evidence Rail": {
    service_tier: "production",
    tenancy: "dedicated-control-plane",
    code_distance: 11,
    logical_compute_units: 96,
    physical_error_rate: 0.0005,
    max_workloads_per_minute: 90,
    max_context_bytes: 192000,
    admin_privileged: false,
    data_residency: "us",
    allowed_workloads: ["explain", "counterfactual", "governance_audit", "substrate_health"],
  },
  "Sovereign Isolated Rail": {
    service_tier: "sovereign",
    tenancy: "sovereign-isolated",
    code_distance: 15,
    logical_compute_units: 128,
    physical_error_rate: 0.0001,
    max_workloads_per_minute: 60,
    max_context_bytes: 256000,
    admin_privileged: false,
    data_residency: "us",
    allowed_workloads: [
      "explain",
      "orchestrate",
      "counterfactual",
      "governance_audit",
      "substrate_health",
    ],
  },
  "Research/Expert Rail": {
    service_tier: "developer",
    tenancy: "single-tenant",
    code_distance: 9,
    logical_compute_units: 128,
    physical_error_rate: 0.001,
    max_workloads_per_minute: 180,
    max_context_bytes: 256000,
    admin_privileged: false,
    data_residency: "us",
    allowed_workloads: [
      "explain",
      "orchestrate",
      "counterfactual",
      "governance_audit",
      "substrate_health",
    ],
  },
};

export default function CIaaSServiceManager({ token }: CIaaSServiceManagerProps) {
  const { isAdmin } = useAuth();
  const { isExpertMode } = useSkillMode();
  const [services, setServices] = useState<ServiceResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedService, setSelectedService] = useState<ServiceResponse | null>(null);
  const [showProvisionModal, setShowProvisionModal] = useState(false);
  const [provisionForm, setProvisionForm] = useState<ProvisionComputationalIntelligenceRequest>({
    name: "",
    service_tier: "developer",
    tenancy: "single-tenant",
    code_distance: 7,
    logical_compute_units: 32,
    physical_error_rate: 0.001,
    max_workloads_per_minute: 60,
    max_context_bytes: 64000,
    admin_privileged: false,
    data_residency: "us",
    allowed_workloads: [
      "explain",
      "orchestrate",
      "counterfactual",
      "governance_audit",
      "substrate_health",
    ],
  });

  const applyPreset = (preset: "starter" | "enterprise" | "regulated" | "sovereign" | "research") => {
    const presets: Record<typeof preset, Partial<ProvisionComputationalIntelligenceRequest>> = {
      starter: { service_tier: "developer", tenancy: "single-tenant", code_distance: 7, logical_compute_units: 16, physical_error_rate: 0.001, max_workloads_per_minute: 30, max_context_bytes: 64000, allowed_workloads: ["explain", "substrate_health", "governance_audit"] },
      enterprise: { service_tier: "production", tenancy: "single-tenant", code_distance: 11, logical_compute_units: 64, physical_error_rate: 0.0005, max_workloads_per_minute: 120, max_context_bytes: 256000, allowed_workloads: ["explain", "orchestrate", "counterfactual", "governance_audit", "substrate_health"] },
      regulated: { service_tier: "production", tenancy: "single-tenant", code_distance: 15, logical_compute_units: 96, physical_error_rate: 0.0001, max_workloads_per_minute: 60, max_context_bytes: 512000, allowed_workloads: ["explain", "counterfactual", "governance_audit", "substrate_health"] },
      sovereign: { service_tier: "sovereign", tenancy: "sovereign-isolated", code_distance: 21, logical_compute_units: 128, physical_error_rate: 0.00005, max_workloads_per_minute: 45, max_context_bytes: 512000, allowed_workloads: ["explain", "counterfactual", "governance_audit", "substrate_health"] },
      research: { service_tier: "developer", tenancy: "single-tenant", code_distance: 9, logical_compute_units: 128, physical_error_rate: 0.001, max_workloads_per_minute: 240, max_context_bytes: 256000, allowed_workloads: ["explain", "orchestrate", "counterfactual", "governance_audit", "substrate_health"] },
    };
    setProvisionForm((current) => ({ ...current, ...presets[preset], service_tier: presets[preset].service_tier === "sovereign" && !isAdmin ? "production" : presets[preset].service_tier, tenancy: presets[preset].tenancy === "sovereign-isolated" && !isAdmin ? "single-tenant" : presets[preset].tenancy }));
  };

  const fetchServices = async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const data = await listCIAASServices();
      setServices(data);
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
      // Use customer-safe endpoint for non-admin users
      if (isAdmin) {
        await provisionCIAASService(provisionForm);
      } else {
        // Remove admin-only fields for customer provision
        const { admin_privileged, ...customerForm } = provisionForm;
        await provisionCustomerCIAASService(customerForm);
      }
      setShowProvisionModal(false);
      await fetchServices();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to provision service");
    }
  };

  const getStateColor = (state: ServiceState) => {
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

  const getTierColor = (tier: ServiceTier) => {
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
          <h2 className="text-2xl font-bold text-slate-900">CIaaS Services</h2>
          <p className="text-sm text-slate-600">
            Intent-first intelligence rails for explanation, counterfactuals, governance audit, and safe orchestration. Raw parameters stay behind expert mode.
          </p>
        </div>
        <button
          onClick={() => setShowProvisionModal(true)}
          className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
        >
          <Plus className="h-4 w-4" />
          Provision Service
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
      ) : services.length === 0 ? (
        <div className="rounded-lg border border-dashed border-slate-300 p-12 text-center">
          <Cpu className="mx-auto h-12 w-12 text-slate-400" />
          <p className="mt-4 text-slate-600">No CIaaS services provisioned</p>
          <button
            onClick={() => setShowProvisionModal(true)}
            className="mt-4 text-blue-600 hover:text-blue-700"
          >
            Provision your first service
          </button>
        </div>
      ) : (
        <div className="grid gap-4">
          {services.map((service) => (
            <div
              key={service.service_id}
              className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <h3 className="text-lg font-semibold text-slate-900">{service.name}</h3>
                    <span
                      className={`rounded-full border px-2.5 py-1 text-xs font-medium ${getStateColor(service.state)}`}
                    >
                      {service.state.toUpperCase()}
                    </span>
                    <span
                      className={`rounded-full border px-2.5 py-1 text-xs font-medium ${getTierColor(service.service_tier)}`}
                    >
                      {service.service_tier.toUpperCase()}
                    </span>
                  </div>
                  <div className="mt-2 grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-slate-600">Service ID:</span>
                      <span className="ml-2 font-mono text-slate-900">{service.service_id}</span>
                    </div>
                    <div>
                      <span className="text-slate-600">Owner:</span>
                      <span className="ml-2 font-mono text-slate-900">{service.owner}</span>
                    </div>
                    <div>
                      <span className="text-slate-600">Tenancy:</span>
                      <span className="ml-2 font-mono text-slate-900">{service.tenancy}</span>
                    </div>
                    <div>
                      <span className="text-slate-600">Created:</span>
                      <span className="ml-2 font-mono text-slate-900">
                        {new Date(service.created_at).toLocaleString()}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex gap-2">
                  {service.state === "stopped" || service.state === "provisioned" ? (
                    <button
                      onClick={() => handleStart(service.service_id)}
                      className="flex items-center gap-1 rounded-lg bg-emerald-600 px-3 py-2 text-white hover:bg-emerald-700"
                    >
                      <Play className="h-4 w-4" />
                      Start
                    </button>
                  ) : (
                    <button
                      onClick={() => handleStop(service.service_id)}
                      className="flex items-center gap-1 rounded-lg bg-slate-600 px-3 py-2 text-white hover:bg-slate-700"
                    >
                      <Square className="h-4 w-4" />
                      Stop
                    </button>
                  )}
                  <button
                    onClick={() => setSelectedService(service)}
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

              <div>
                <label className="block text-sm font-medium text-slate-700">
                  Provisioning preset
                </label>
                <select
                  aria-label="CIaaS provisioning preset"
                  onChange={(e) => {
                    const preset = e.target.value;
                    const base =
                      preset === "regulated"
                        ? {
                            service_tier: "production" as ServiceTier,
                            code_distance: 11,
                            logical_compute_units: 64,
                            physical_error_rate: 0.0005,
                            allowed_workloads: [
                              "explain",
                              "counterfactual",
                              "governance_audit",
                              "substrate_health",
                            ] as WorkloadKind[],
                          }
                        : preset === "sovereign"
                          ? {
                              service_tier: "sovereign" as ServiceTier,
                              tenancy: "sovereign-isolated" as TenancyMode,
                              code_distance: 15,
                              logical_compute_units: 128,
                              physical_error_rate: 0.0001,
                            }
                          : preset === "research"
                            ? {
                                service_tier: "developer" as ServiceTier,
                                code_distance: 7,
                                logical_compute_units: 128,
                                max_context_bytes: 256000,
                              }
                            : {
                                service_tier: "production" as ServiceTier,
                                code_distance: 7,
                                logical_compute_units: 32,
                                physical_error_rate: 0.001,
                              };
                    setProvisionForm({ ...provisionForm, ...base });
                  }}
                  className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
                  defaultValue="enterprise"
                >
                  <option value="starter">Starter Intelligence Rail</option>
                  <option value="enterprise">Enterprise Decision Rail</option>
                  <option value="regulated">Regulated Evidence Rail</option>
                  {isAdmin && <option value="sovereign">Sovereign Isolated Rail</option>}
                  <option value="research">Research/Expert Rail</option>
                </select>
                <p className="mt-1 text-xs text-slate-500">
                  Presets choose resilience, capacity, tenancy, and governance defaults so
                  non-specialists do not need to set raw quantum controls.
                </p>
              </div>
              <MetricExplainerCard metric="code_distance" />
              {isExpertMode && (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700">
                      Code Distance
                    </label>
                    <input
                      type="number"
                      min="3"
                      max="31"
                      step="2"
                      value={provisionForm.code_distance}
                      onChange={(e) =>
                        setProvisionForm({
                          ...provisionForm,
                          code_distance: parseInt(e.target.value),
                        })
                      }
                      className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700">
                      Logical Compute Units
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="512"
                      value={provisionForm.logical_compute_units}
                      onChange={(e) =>
                        setProvisionForm({
                          ...provisionForm,
                          logical_compute_units: parseInt(e.target.value),
                        })
                      }
                      className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
                    />
                  </div>
                </div>
              )}
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
                  className="rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
                >
                  Provision Service
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
