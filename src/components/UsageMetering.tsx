/**
 * Usage Metering Dashboard
 *
 * Customer-facing view of compute consumption, quota, and billing.
 * Transparent cost accounting for QaaS/QIaaS/CIaaS operations.
 */

import React, { useState, useEffect } from "react";
import { Activity, DollarSign, TrendingUp, Zap } from "lucide-react";

interface UsageData {
  compute_units_used: number;
  compute_units_quota: number;
  current_period_cost: number;
  currency: string;
  period_start: string;
  period_end: string;
  breakdown: Record<string, number>;
}

const DEFAULT_TENANT = import.meta.env.VITE_CUSTOMER_TENANT_ID || "enterprise-tenant";

function usageHeaders(): HeadersInit {
  let tenant = DEFAULT_TENANT;
  let portalToken = import.meta.env.VITE_CUSTOMER_PORTAL_TOKEN || "";
  let authToken = "";
  try {
    tenant = localStorage.getItem("hyba_customer_tenant_id") || tenant;
    portalToken = localStorage.getItem("hyba_customer_portal_token") || portalToken;
    authToken = localStorage.getItem("hyba_auth_token") || "";
  } catch {
    // Browser storage can be disabled; keep env/defaults.
  }

  return {
    "X-HYBA-Tenant-ID": tenant,
    ...(portalToken ? { "X-HYBA-Customer-Token": portalToken } : {}),
    ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
  };
}

export function UsageMetering() {
  const [usage, setUsage] = useState<UsageData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUsage();
    const interval = setInterval(fetchUsage, 60000);
    return () => clearInterval(interval);
  }, []);

  const fetchUsage = async () => {
    try {
      const response = await fetch("/api/customer/usage", {
        headers: usageHeaders(),
      });
      if (!response.ok) {
        throw new Error(`Usage endpoint returned ${response.status}`);
      }
      const data = await response.json();
      setUsage(data);
    } catch (error) {
      console.error("Failed to fetch usage:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !usage) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 w-32 rounded bg-slate-200" />
          <div className="h-32 w-full rounded bg-slate-200" />
        </div>
      </div>
    );
  }

  const quotaPercentage =
    usage.compute_units_quota > 0
      ? (usage.compute_units_used / usage.compute_units_quota) * 100
      : 0;
  const qaasUsage = usage.breakdown.qaas || 0;
  const qiaasUsage = usage.breakdown.qiaas || 0;

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="mb-6 text-lg font-bold text-slate-950">Usage & Billing</h3>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-lg border border-slate-100 bg-slate-50 p-4">
            <div className="mb-2 flex items-center gap-2 text-slate-600">
              <Zap className="h-4 w-4" />
              <span className="text-xs font-medium">Compute Units</span>
            </div>
            <div className="text-2xl font-bold text-slate-950">
              {usage.compute_units_used.toLocaleString()}
            </div>
            <div className="mt-1 text-xs text-slate-500">
              of {usage.compute_units_quota.toLocaleString()} quota
            </div>
            <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-200">
              <div
                className={`h-full transition-all ${
                  quotaPercentage > 90
                    ? "bg-red-500"
                    : quotaPercentage > 75
                      ? "bg-amber-500"
                      : "bg-blue-500"
                }`}
                style={{ width: `${Math.min(quotaPercentage, 100)}%` }}
              />
            </div>
          </div>

          <div className="rounded-lg border border-slate-100 bg-slate-50 p-4">
            <div className="mb-2 flex items-center gap-2 text-slate-600">
              <DollarSign className="h-4 w-4" />
              <span className="text-xs font-medium">Current Period</span>
            </div>
            <div className="text-2xl font-bold text-slate-950">
              {usage.currency}
              {usage.current_period_cost.toFixed(2)}
            </div>
            <div className="mt-1 text-xs text-slate-500">
              {new Date(usage.period_start).toLocaleDateString()} -{" "}
              {new Date(usage.period_end).toLocaleDateString()}
            </div>
          </div>

          <div className="rounded-lg border border-slate-100 bg-slate-50 p-4">
            <div className="mb-2 flex items-center gap-2 text-slate-600">
              <Activity className="h-4 w-4" />
              <span className="text-xs font-medium">QaaS Usage</span>
            </div>
            <div className="text-2xl font-bold text-slate-950">{qaasUsage.toLocaleString()}</div>
            <div className="mt-1 text-xs text-slate-500">compute units</div>
          </div>

          <div className="rounded-lg border border-slate-100 bg-slate-50 p-4">
            <div className="mb-2 flex items-center gap-2 text-slate-600">
              <TrendingUp className="h-4 w-4" />
              <span className="text-xs font-medium">QIaaS Usage</span>
            </div>
            <div className="text-2xl font-bold text-slate-950">{qiaasUsage.toLocaleString()}</div>
            <div className="mt-1 text-xs text-slate-500">compute units</div>
          </div>
        </div>

        <div className="mt-6 rounded-lg border border-blue-100 bg-blue-50 p-4">
          <p className="text-sm text-blue-950">
            <strong>Transparent metering:</strong> Every compute unit is tracked, auditable, and
            tied to evidence-sealed execution. No surprise charges. No hidden fees. Mathematics you
            can verify.
          </p>
        </div>
      </div>
    </div>
  );
}
