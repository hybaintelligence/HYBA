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
    expect(studio).toContain("textarea");
    expect(studio).toContain("setWorkload(event.target.value)");
  });

  it("supports all cognitive lens IDs including business buyer mode", () => {
    const studio = readFileSync("src/components/WorkloadStudio.tsx", "utf8");
    for (const lens of ["executive", "business", "operator", "analyst", "engineer", "auditor", "expert"]) {
      expect(studio).toContain(`"${lens}"`);
    }
    expect(studio).toContain("cognitive_lens: lens");
  });

  it("calls the canonical customer CIaaS execute route with public API-key headers", () => {
    const api = readFileSync("src/workloadStudioApi.ts", "utf8");
    expect(api).toContain("/v1/computational-intelligence-services/${serviceId}/execute");
    expect(api).toContain("X-API-Key");
    expect(api).toContain("X-HYBA-API-Key");
    expect(api).toContain("hyba_customer_api_key");
  });

  it("documents localStorage custody as demo-only and resolves aliases deterministically", () => {
    const api = readFileSync("src/workloadStudioApi.ts", "utf8");
    expect(api).toContain("SECURITY SCOPE");
    expect(api).toContain("demo activation only");
    expect(api).toContain("HttpOnly cookies or server-side session custody");
    expect(api).toMatch(/CUSTOMER_API_KEY_STORAGE,[\s\S]*"hyba_api_key",[\s\S]*"ciass_api_key"/);
  });

  it("exports a self-describing evidence packet with trace provenance and claim boundary", () => {
    const studio = readFileSync("src/components/WorkloadStudio.tsx", "utf8");
    expect(studio).toContain("schema_version");
    expect(studio).toContain("generated_at");
    expect(studio).toContain("trace_id_provenance");
    expect(studio).toContain("server_issued");
    expect(studio).toContain("client_generated");
    expect(studio).toContain("claim_boundary");
    expect(studio).toContain("limitations");
    expect(studio).toContain("exported_by");
    expect(studio).toContain("export_triggered_at");
  });

  it("sets fallback labels at invocation time rather than only in render", () => {
    const studio = readFileSync("src/components/WorkloadStudio.tsx", "utf8");
    expect(studio).toContain("type InvocationMetadata");
    expect(studio).toContain("fallback_reason");
    expect(studio).toContain("Customer API key not supplied at invocation time");
    expect(studio).toContain("No provisioned customer CIaaS rail returned at invocation time");
    expect(studio).toContain("All endpoints unavailable");
  });

  it("does not export raw API-key material through the packet object", () => {
    const studio = readFileSync("src/components/WorkloadStudio.tsx", "utf8");
    const exportSection = studio.slice(studio.indexOf("const exportPacket"));
    expect(exportSection).toContain("result.evidencePacket");
    expect(exportSection).not.toContain("apiKey");
    expect(studio).toContain("raw API-key material not exported");
  });

  it("hands generated onboarding API keys directly to Workload Studio", () => {
    const onboarding = readFileSync("src/components/CustomerOnboarding.tsx", "utf8");
    expect(onboarding).toContain("/api/customer/${encodeURIComponent(tenantId)}/api-keys");
    expect(onboarding).toContain("setStoredCustomerApiKey(response.api_key)");
    expect(onboarding).toContain("window.location.href = \"/workload-studio\"");
    expect(onboarding).toContain("Open Workload Studio");
  });
});
