import { describe, expect, it } from "vitest";
import * as apiClient from "../src/apiClient";
import manifest from "../artifacts/frontend_api_command_manifest.generated.json";
import coverageStatus from "../artifacts/frontend_api_command_coverage_status.json";

type ManifestEntry = {
  function: string;
  method: string;
  path: string;
  sideEffect: string;
  role: string;
  idempotent: boolean;
};

describe("frontend API command manifest", () => {
  const entries = manifest as ManifestEntry[];

  it("is machine-readable and maps every declared command to an exported function", () => {
    expect(entries.length).toBeGreaterThanOrEqual(20);
    const keys = new Set<string>();
    for (const entry of entries) {
      expect(entry).toEqual(
        expect.objectContaining({
          function: expect.any(String),
          method: expect.stringMatching(/^(GET|POST|PUT|PATCH|DELETE)$/),
          path: expect.stringMatching(/^\/api\//),
          sideEffect: expect.stringMatching(/^(read|mutation|destructive|autonomous_control)$/),
          role: expect.any(String),
          idempotent: expect.any(Boolean),
        }),
      );
      expect(apiClient[entry.function as keyof typeof apiClient], entry.function).toEqual(expect.any(Function));
      expect(keys.has(entry.function), entry.function).toBe(false);
      keys.add(entry.function);
    }
  });

  it("classifies all non-read commands as non-idempotent so tests require no automatic retry", () => {
    const mutations = entries.filter((entry) => entry.method !== "GET");
    expect(mutations.length).toBeGreaterThan(15);
    for (const entry of mutations) {
      expect(entry.idempotent, entry.function).toBe(false);
      expect(entry.sideEffect, entry.function).not.toBe("read");
    }
  });

  it("keeps behavioural coverage status separate from the generated route inventory", () => {
    const statuses = coverageStatus as Array<{ function: string; coverageStatus: string; evidence: string[] }>;
    expect(statuses.length).toBeGreaterThanOrEqual(20);
    expect(statuses.every((entry) => ["covered", "partial", "required", "blocked"].includes(entry.coverageStatus))).toBe(true);
    expect(statuses.some((entry) => entry.coverageStatus !== "covered")).toBe(true);
    for (const entry of statuses) {
      expect(apiClient[entry.function as keyof typeof apiClient], entry.function).toEqual(expect.any(Function));
      expect(entry.evidence.length, entry.function).toBeGreaterThan(0);
    }
  });

  it("covers the destructive, mutating, and autonomous commands called out in the production-readiness review", () => {
    expect(entries.filter((entry) => entry.sideEffect === "destructive" || entry.sideEffect === "mutation" || entry.sideEffect === "autonomous_control").map((entry) => entry.function)).toEqual(
      expect.arrayContaining([
        "deleteAdminUser",
        "disburseFunding",
        "reviewFundingRequest",
        "startMiningProduction",
        "stopMiningProduction",
        "submitMiningProductionShare",
        "securityShield",
        "quarantineLane",
        "migrateToHabitat",
      ]),
    );
    expect(entries.filter((entry) => entry.sideEffect === "autonomous_control").map((entry) => entry.function)).toEqual(
      expect.arrayContaining(["scaleIntelligence", "boostConsciousness", "intelligenceOrchestrate", "applyEvolution", "setMiningIntent"]),
    );
  });
});
