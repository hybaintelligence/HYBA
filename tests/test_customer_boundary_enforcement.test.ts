import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";

const read = (path: string) => readFileSync(path, "utf8");

describe("customer production boundary", () => {
  it("mounts the customer boundary enforcer in the application shell", () => {
    const main = read("src/main.tsx");
    expect(main).toContain("CustomerBoundaryEnforcer");
    expect(main).toContain("WebSocketProvider");
  });

  it("removes legacy internal treasury and pool surfaces in customer mode", () => {
    const enforcer = read("src/components/CustomerBoundaryEnforcer.tsx");
    expect(enforcer).toContain("stratum mining pools");
    expect(enforcer).toContain("mining telemetry");
    expect(enforcer).toContain("hashrate");
    expect(enforcer).toContain("/api/mining/");
    expect(enforcer).toContain("FEATURES.SHOW_MINING_UI");
    expect(enforcer).toContain("MutationObserver");
  });

  it("defaults customer mode to internal surfaces hidden", () => {
    const features = read("src/config/features.ts");
    expect(features).toContain("VITE_CUSTOMER_MODE");
    expect(features).toContain("SHOW_MINING_UI: isInternalMode && !isCustomerMode");
    expect(features).toContain("SHOW_POOL_MANAGEMENT: isInternalMode && !isCustomerMode");
    expect(features).toContain("SHOW_HASHRATE_METRICS: isInternalMode && !isCustomerMode");
  });

  it("sends tenant boundary headers from the customer portal", () => {
    const portal = read("src/components/CustomerPortal.tsx");
    expect(portal).toContain("X-HYBA-Tenant-ID");
    expect(portal).toContain("X-HYBA-Customer-Token");
    expect(portal).toContain("VITE_CUSTOMER_PORTAL_TOKEN");
  });
});
