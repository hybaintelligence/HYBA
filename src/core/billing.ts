export type BillingPlanId = "free" | "growth" | "enterprise" | string;

export interface BillingPlan {
  id: BillingPlanId;
  displayName: string;
  monthlyQuotaUnits: number;
  unitPriceUsdCents: number;
  overageAllowed: boolean;
}

export interface TenantBillingConfig {
  tenantId: string;
  planId: BillingPlanId;
  monthlyQuotaUnits?: number;
  unitPriceUsdCents?: number;
  overageAllowed?: boolean;
}

export interface BillingDecision {
  allowed: boolean;
  tenantId: string;
  plan: BillingPlan;
  period: string;
  requestedUnits: number;
  usedUnits: number;
  projectedUnits: number;
  remainingUnits: number;
  estimatedCostUsdCents: number;
  reason?: "quota_exceeded" | "invalid_units";
}

interface UsageBucket {
  usedUnits: number;
  estimatedCostUsdCents: number;
}

const DEFAULT_PLANS: Record<string, BillingPlan> = {
  free: {
    id: "free",
    displayName: "Free Evaluation",
    monthlyQuotaUnits: 1_000,
    unitPriceUsdCents: 0,
    overageAllowed: false,
  },
  growth: {
    id: "growth",
    displayName: "Growth",
    monthlyQuotaUnits: 100_000,
    unitPriceUsdCents: 2,
    overageAllowed: false,
  },
  enterprise: {
    id: "enterprise",
    displayName: "Enterprise",
    monthlyQuotaUnits: 10_000_000,
    unitPriceUsdCents: 1,
    overageAllowed: true,
  },
};

function currentUtcMonth(date = new Date()): string {
  return `${date.getUTCFullYear()}-${String(date.getUTCMonth() + 1).padStart(2, "0")}`;
}

function parseJsonObject<T>(raw: string | undefined, fallback: T): T {
  if (!raw) return fallback;
  try {
    const parsed = JSON.parse(raw) as T;
    if (!parsed || typeof parsed !== "object") return fallback;
    return parsed;
  } catch {
    return fallback;
  }
}

export function loadBillingPlans(
  raw = process.env.HYBA_BILLING_PLANS_JSON,
): Record<string, BillingPlan> {
  const overrides = parseJsonObject<Record<string, Partial<BillingPlan>>>(raw, {});
  const merged: Record<string, BillingPlan> = { ...DEFAULT_PLANS };
  for (const [id, override] of Object.entries(overrides)) {
    const base = merged[id] || {
      id,
      displayName: id,
      monthlyQuotaUnits: 0,
      unitPriceUsdCents: 0,
      overageAllowed: false,
    };
    merged[id] = { ...base, ...override, id };
  }
  return merged;
}

export function loadTenantBillingConfig(
  raw = process.env.HYBA_TENANT_BILLING_JSON,
): Record<string, TenantBillingConfig> {
  return parseJsonObject<Record<string, TenantBillingConfig>>(raw, {});
}

export function sanitizeTenantId(value: string | undefined): string {
  const tenant = (value || "anonymous").trim().toLowerCase();
  return /^[a-z0-9][a-z0-9._-]{1,62}$/.test(tenant) ? tenant : "anonymous";
}

export function parseBillingUnits(value: string | undefined): number {
  if (!value) return 1;
  const units = Number(value);
  if (!Number.isInteger(units) || units < 1 || units > 1_000_000) return Number.NaN;
  return units;
}

export class MonthlyQuotaLedger {
  private readonly usage = new Map<string, UsageBucket>();

  evaluateAndRecord(input: {
    tenantId: string;
    requestedUnits: number;
    plans: Record<string, BillingPlan>;
    tenantConfigs: Record<string, TenantBillingConfig>;
    date?: Date;
  }): BillingDecision {
    const tenantId = sanitizeTenantId(input.tenantId);
    const period = currentUtcMonth(input.date);
    const tenantConfig = input.tenantConfigs[tenantId] || { tenantId, planId: "free" };
    const planBase = input.plans[tenantConfig.planId] || input.plans.free || DEFAULT_PLANS.free;
    const plan: BillingPlan = {
      ...planBase,
      monthlyQuotaUnits: tenantConfig.monthlyQuotaUnits ?? planBase.monthlyQuotaUnits,
      unitPriceUsdCents: tenantConfig.unitPriceUsdCents ?? planBase.unitPriceUsdCents,
      overageAllowed: tenantConfig.overageAllowed ?? planBase.overageAllowed,
    };
    const key = `${period}:${tenantId}`;
    const bucket = this.usage.get(key) || { usedUnits: 0, estimatedCostUsdCents: 0 };
    const requestedUnits = input.requestedUnits;
    if (!Number.isInteger(requestedUnits) || requestedUnits < 1) {
      return {
        allowed: false,
        tenantId,
        plan,
        period,
        requestedUnits,
        usedUnits: bucket.usedUnits,
        projectedUnits: bucket.usedUnits,
        remainingUnits: Math.max(0, plan.monthlyQuotaUnits - bucket.usedUnits),
        estimatedCostUsdCents: bucket.estimatedCostUsdCents,
        reason: "invalid_units",
      };
    }
    const projectedUnits = bucket.usedUnits + requestedUnits;
    const allowed = plan.overageAllowed || projectedUnits <= plan.monthlyQuotaUnits;
    if (!allowed) {
      return {
        allowed,
        tenantId,
        plan,
        period,
        requestedUnits,
        usedUnits: bucket.usedUnits,
        projectedUnits,
        remainingUnits: Math.max(0, plan.monthlyQuotaUnits - bucket.usedUnits),
        estimatedCostUsdCents: bucket.estimatedCostUsdCents,
        reason: "quota_exceeded",
      };
    }
    bucket.usedUnits = projectedUnits;
    bucket.estimatedCostUsdCents += requestedUnits * plan.unitPriceUsdCents;
    this.usage.set(key, bucket);
    return {
      allowed,
      tenantId,
      plan,
      period,
      requestedUnits,
      usedUnits: bucket.usedUnits,
      projectedUnits,
      remainingUnits: Math.max(0, plan.monthlyQuotaUnits - bucket.usedUnits),
      estimatedCostUsdCents: bucket.estimatedCostUsdCents,
    };
  }
}
