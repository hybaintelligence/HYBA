import { describe, expect, it } from "vitest";
import { MonthlyQuotaLedger, parseBillingUnits, sanitizeTenantId } from "../src/core/billing";

describe("tenant billing quota ledger", () => {
  it("sanitizes tenant identity and validates billable units", () => {
    expect(sanitizeTenantId("Acme-Prod_01")).toBe("acme-prod_01");
    expect(sanitizeTenantId("../root")).toBe("anonymous");
    expect(parseBillingUnits(undefined)).toBe(1);
    expect(parseBillingUnits("25")).toBe(25);
    expect(Number.isNaN(parseBillingUnits("0"))).toBe(true);
  });

  it("enforces per-tenant monthly quota before recording excess usage", () => {
    const ledger = new MonthlyQuotaLedger();
    const plans = {
      qa: {
        id: "qa",
        displayName: "QaaS",
        monthlyQuotaUnits: 10,
        unitPriceUsdCents: 7,
        overageAllowed: false,
      },
    };
    const tenantConfigs = { acme: { tenantId: "acme", planId: "qa" } };

    const first = ledger.evaluateAndRecord({
      tenantId: "acme",
      requestedUnits: 7,
      plans,
      tenantConfigs,
      date: new Date("2026-06-20T00:00:00Z"),
    });
    expect(first.allowed).toBe(true);
    expect(first.usedUnits).toBe(7);
    expect(first.remainingUnits).toBe(3);
    expect(first.estimatedCostUsdCents).toBe(49);

    const denied = ledger.evaluateAndRecord({
      tenantId: "acme",
      requestedUnits: 4,
      plans,
      tenantConfigs,
      date: new Date("2026-06-20T00:00:00Z"),
    });
    expect(denied.allowed).toBe(false);
    expect(denied.reason).toBe("quota_exceeded");
    expect(denied.usedUnits).toBe(7);
  });

  it("isolates usage by tenant and UTC billing month", () => {
    const ledger = new MonthlyQuotaLedger();
    const plans = {
      qa: {
        id: "qa",
        displayName: "QaaS",
        monthlyQuotaUnits: 5,
        unitPriceUsdCents: 1,
        overageAllowed: false,
      },
    };
    const tenantConfigs = {
      acme: { tenantId: "acme", planId: "qa" },
      globex: { tenantId: "globex", planId: "qa" },
    };

    expect(
      ledger.evaluateAndRecord({
        tenantId: "acme",
        requestedUnits: 5,
        plans,
        tenantConfigs,
        date: new Date("2026-06-30T23:59:59Z"),
      }).allowed,
    ).toBe(true);
    expect(
      ledger.evaluateAndRecord({
        tenantId: "globex",
        requestedUnits: 5,
        plans,
        tenantConfigs,
        date: new Date("2026-06-30T23:59:59Z"),
      }).allowed,
    ).toBe(true);
    expect(
      ledger.evaluateAndRecord({
        tenantId: "acme",
        requestedUnits: 5,
        plans,
        tenantConfigs,
        date: new Date("2026-07-01T00:00:00Z"),
      }).allowed,
    ).toBe(true);
  });
});
