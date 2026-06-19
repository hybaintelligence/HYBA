import { describe, expect, it } from "vitest";
import generatedManifest from "../artifacts/frontend_api_command_manifest.generated.json";
import coverageStatus from "../artifacts/frontend_api_command_coverage_status.json";

type ManifestEntry = {
  function: string;
  method: string;
  path: string;
  sideEffect: string;
  role: string;
  idempotent: boolean;
};

type CoverageEntry = ManifestEntry & {
  coverageStatus: "covered" | "partial" | "required" | "blocked";
  evidence: string[];
};

const guardedFunctions = [
  "deleteAdminUser",
  "disburseFunding",
  "reviewFundingRequest",
  "startMiningProduction",
  "stopMiningProduction",
  "submitMiningProductionShare",
  "scaleIntelligence",
  "boostConsciousness",
  "intelligenceOrchestrate",
  "securityShield",
  "quarantineLane",
  "applyEvolution",
  "setMiningIntent",
  "migrateToHabitat",
] as const;

describe("frontend production hardening evidence", () => {
  const manifest = generatedManifest as ManifestEntry[];
  const statuses = coverageStatus as CoverageEntry[];
  const manifestByFunction = new Map(manifest.map((entry) => [entry.function, entry]));
  const statusByFunction = new Map(statuses.map((entry) => [entry.function, entry]));

  it("keeps the generated command inventory broad enough for the 80+ route frontend contract", () => {
    expect(manifest.length).toBeGreaterThanOrEqual(80);
    expect(new Set(manifest.map((entry) => entry.function)).size).toBe(manifest.length);
  });

  it("tracks every guarded command in coverage status", () => {
    for (const functionName of guardedFunctions) {
      const manifestEntry = manifestByFunction.get(functionName);
      const statusEntry = statusByFunction.get(functionName);
      expect(manifestEntry, functionName).toBeDefined();
      expect(statusEntry, functionName).toBeDefined();
      expect(statusEntry?.coverageStatus, functionName).not.toBe("blocked");
      expect(statusEntry?.evidence.length, functionName).toBeGreaterThan(0);
    }
  });

  it("requires UI evidence before a guarded command can be marked fully covered", () => {
    for (const entry of statuses.filter((item) => item.sideEffect !== "read")) {
      if (entry.coverageStatus === "covered") {
        const evidence = entry.evidence.join("\n").toLowerCase();
        expect(evidence, entry.function).toMatch(/playwright|e2e|ui/);
        expect(evidence, entry.function).toMatch(/auth|role/);
        expect(evidence, entry.function).toMatch(/failure|4xx|5xx|retry|offline/);
      }
    }
  });

  it("keeps non-read API functions non-idempotent unless a future review proves otherwise", () => {
    for (const entry of manifest.filter((command) => command.method !== "GET")) {
      expect(entry.idempotent, entry.function).toBe(false);
      expect(entry.sideEffect, entry.function).not.toBe("read");
    }
  });
});
