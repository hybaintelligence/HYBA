import React, { useEffect, useState } from "react";
import { CreditCard, History, KeyRound, Server, TrendingUp } from "lucide-react";

type Dashboard = {
  tenant_id: string;
  instances: Array<{ id: string; status: string; region: string }>;
  monthly_usage: { compute_units: number; estimated_cost_usd: number };
  quota_remaining: { compute_units: number; monthly_quota: number };
  api_keys: Array<{ key_id: string; label?: string; status: string; created_at: string }>;
  billing_summary: { current_month_usd: number; invoice_count: number; next_billing_date: string };
  uptime: { last_30_days_percent: number | null };
};

type Workloads = {
  executions: Array<{
    execution_id: string;
    workload_type: string;
    status: string;
    duration_ms: number;
    cost_usd: number;
  }>;
  total_cost: number;
  success_rate: number | null;
};

const DEFAULT_TENANT = import.meta.env.VITE_CUSTOMER_TENANT_ID || "enterprise-tenant";

function portalHeaders(tenantId: string): HeadersInit {
  let portalToken = import.meta.env.VITE_CUSTOMER_PORTAL_TOKEN || "";
  try {
    portalToken = localStorage.getItem("hyba_customer_portal_token") || portalToken;
  } catch {
    // localStorage may be unavailable in locked-down browsers.
  }

  return {
    "X-HYBA-Tenant-ID": tenantId,
    ...(portalToken ? { "X-HYBA-Customer-Token": portalToken } : {}),
  };
}

export default function CustomerPortal() {
  const [tenantId, setTenantId] = useState(DEFAULT_TENANT);
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [workloads, setWorkloads] = useState<Workloads | null>(null);
  const [status, setStatus] = useState("Loading portal...");

  async function loadPortal(nextTenant = tenantId) {
    setStatus("Loading portal...");
    const headers = portalHeaders(nextTenant);
    const [dashboardResponse, workloadResponse] = await Promise.all([
      fetch(`/api/customer/${encodeURIComponent(nextTenant)}/dashboard`, { headers }),
      fetch(`/api/customer/${encodeURIComponent(nextTenant)}/workloads`, { headers }),
    ]);
    if (!dashboardResponse.ok || !workloadResponse.ok) {
      const statusCode = dashboardResponse.ok ? workloadResponse.status : dashboardResponse.status;
      throw new Error(`Customer portal API unavailable (${statusCode})`);
    }
    setDashboard(await dashboardResponse.json());
    setWorkloads(await workloadResponse.json());
    setStatus("Portal synchronized");
  }

  useEffect(() => {
    loadPortal().catch((error) =>
      setStatus(error instanceof Error ? error.message : "Portal unavailable"),
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const monthlyQuota = dashboard?.quota_remaining.monthly_quota || 0;
  const usagePct =
    dashboard && monthlyQuota > 0
      ? Math.round(((dashboard.monthly_usage.compute_units || 0) / monthlyQuota) * 100)
      : 0;

  return (
    <section className="space-y-6">
      <div className="rounded-[2rem] border border-white/30 bg-white/90 p-6 shadow-xl shadow-slate-900/10">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="eyebrow">Customer self-service</p>
            <h2 className="text-2xl font-black text-slate-950">Enterprise Customer Portal</h2>
            <p className="mt-2 max-w-3xl text-sm text-slate-600">
              Board-grade usage, billing, workload history, API key hygiene, quota tracking, and
              payment readiness for enterprise launch.
            </p>
          </div>
          <label className="text-xs font-mono uppercase tracking-[0.2em] text-slate-500">
            Tenant
            <input
              value={tenantId}
              onChange={(event) => setTenantId(event.target.value)}
              onBlur={() => loadPortal(tenantId).catch((error) => setStatus(String(error)))}
              className="mt-2 block rounded-xl border border-slate-200 px-3 py-2 text-sm normal-case tracking-normal text-slate-900"
            />
          </label>
        </div>
        <p className="mt-4 text-xs font-mono text-slate-500">{status}</p>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Metric
          icon={<Server />}
          label="Running instances"
          value={`${dashboard?.instances.filter((i) => i.status === "running").length ?? 0}/${dashboard?.instances.length ?? 0}`}
        />
        <Metric
          icon={<TrendingUp />}
          label="Monthly usage"
          value={`${dashboard?.monthly_usage.compute_units.toLocaleString() ?? "—"} units`}
          detail={`${usagePct}% of quota`}
        />
        <Metric
          icon={<CreditCard />}
          label="Current month"
          value={`$${dashboard?.billing_summary.current_month_usd.toLocaleString() ?? "—"}`}
          detail={`${dashboard?.billing_summary.invoice_count ?? 0} invoices`}
        />
        <Metric
          icon={<KeyRound />}
          label="API keys"
          value={`${dashboard?.api_keys.length ?? 0}`}
          detail={
            dashboard?.uptime.last_30_days_percent == null
              ? "Uptime source not configured"
              : `${dashboard.uptime.last_30_days_percent}% uptime`
          }
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-lg">
          <h3 className="mb-4 flex items-center gap-2 text-lg font-bold text-slate-950">
            <Server className="h-5 w-5" /> Instance status
          </h3>
          <div className="space-y-3">
            {dashboard?.instances.length ? (
              dashboard.instances.map((instance) => (
                <div
                  key={instance.id}
                  className="flex items-center justify-between rounded-2xl bg-slate-50 p-4 text-sm"
                >
                  <div>
                    <p className="font-semibold text-slate-900">{instance.id}</p>
                    <p className="text-slate-500">{instance.region}</p>
                  </div>
                  <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700">
                    {instance.status}
                  </span>
                </div>
              ))
            ) : (
              <p className="rounded-2xl bg-slate-50 p-4 text-sm text-slate-500">
                No running customer instances reported yet.
              </p>
            )}
          </div>
        </div>
        <div className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-lg">
          <h3 className="mb-4 flex items-center gap-2 text-lg font-bold text-slate-950">
            <History className="h-5 w-5" /> Workload history
          </h3>
          <div className="overflow-hidden rounded-2xl border border-slate-100">
            {workloads?.executions.length ? (
              workloads.executions.slice(0, 5).map((execution) => (
                <div
                  key={execution.execution_id}
                  className="grid grid-cols-4 gap-3 border-b border-slate-100 p-3 text-sm last:border-0"
                >
                  <span className="font-mono text-slate-500">{execution.execution_id}</span>
                  <span className="text-slate-700">{execution.workload_type}</span>
                  <span
                    className={execution.status === "success" ? "text-emerald-600" : "text-red-600"}
                  >
                    {execution.status}
                  </span>
                  <span className="text-right font-semibold text-slate-900">
                    ${execution.cost_usd}
                  </span>
                </div>
              ))
            ) : (
              <p className="p-4 text-sm text-slate-500">No customer workloads recorded yet.</p>
            )}
          </div>
          <p className="mt-4 text-sm text-slate-500">
            Success rate{" "}
            {workloads?.success_rate == null
              ? "—"
              : `${(workloads.success_rate * 100).toFixed(1)}%`}
            ; total cost ${workloads?.total_cost ?? "—"}.
          </p>
        </div>
      </div>
    </section>
  );
}

function Metric({
  icon,
  label,
  value,
  detail,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  detail?: string;
}) {
  return (
    <div className="rounded-[1.5rem] border border-slate-200 bg-white p-5 shadow-lg">
      <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-2xl bg-blue-50 text-blue-700">
        {icon}
      </div>
      <p className="text-xs font-mono uppercase tracking-[0.18em] text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-black text-slate-950">{value}</p>
      {detail && <p className="text-sm text-slate-500">{detail}</p>}
    </div>
  );
}
