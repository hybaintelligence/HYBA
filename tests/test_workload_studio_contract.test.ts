import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";

describe("CIaaS Workload Studio contract", () => {
  it("is mounted as a first-class app route", () => {
    const app = readFileSync("src/App.tsx", "utf8");
    expect(app).toContain("WorkloadStudio");
    expect(app).toContain("workloadStudio");
    expect(app).toContain("/workload-studio");
  });

  it("lets customers bring a workload and run the API rather than watch canned claims", () => {
    const studio = readFileSync("src/components/WorkloadStudio.tsx", "utf8");
    expect(studio).toContain("CIaaS Workload Studio");
    expect(studio).toContain("Bring workload");
    expect(studio).toContain("Run CIaaS transformation");
    expect(studio).toContain("Before / after intelligence packet");
    expect(studio).toContain("Export evidence packet");
    expect(studio).toContain("Do not believe HYBA");
  });

  it("supports all cognitive lenses including business buyer mode", () => {
    const studio = readFileSync("src/components/WorkloadStudio.tsx", "utf8");
    for (const lens of ["executive", "business", "operator", "analyst", "engineer", "auditor", "expert"]) {
      expect(studio).toContain(`"${lens}"`);
    }
  });

  it("calls the canonical customer CIaaS execute route with public API-key headers", () => {
    const api = readFileSync("src/workloadStudioApi.ts", "utf8");
    expect(api).toContain("/v1/computational-intelligence-services/${serviceId}/execute");
    expect(api).toContain("X-API-Key");
    expect(api).toContain("X-HYBA-API-Key");
    expect(api).toContain("hyba_customer_api_key");
  });

  it("marks capability boundaries and preserves reproducible evidence packets", () => {
    const studio = readFileSync("src/components/WorkloadStudio.tsx", "utf8");
    expect(studio).toContain("Capability boundary");
    expect(studio).toContain("evidencePacket");
    expect(studio).toContain("trace_id");
    expect(studio).toContain("human approval boundary preserved");
    expect(studio).toContain("raw API-key material not exported");
  });
});
