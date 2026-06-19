import { describe, expect, it } from "vitest";
import * as apiClient from "../src/apiClient";
import manifest from "../artifacts/frontend_api_command_manifest.json";

type ManifestEntry = {
  function: string;
  method: string;
  path: string;
  sideEffect: string;
  role: string;
  idempotent: boolean;
  tested: boolean;
};

describe("frontend API command manifest", () => {
  const entries = manifest as ManifestEntry[];

  it("is machine-readable and maps every declared command to an exported function", () => {
    expect(entries.length).toBeGreaterThanOrEqual(20);
    const keys = new Set<string>();
    for (const entry of entries) {
      expect(entry).toEqual({
        function: expect.any(String),
        method: expect.stringMatching(/^(GET|POST|PUT|DELETE)$/),
        path: expect.stringMatching(/^\/api\//),
        sideEffect: expect.stringMatching(/^(read|mutation|destructive|autonomous_control)$/),
        role: expect.any(String),
        idempotent: expect.any(Boolean),
        tested: true,
      });
      expect(apiClient[entry.function as keyof typeof apiClient], entry.function).toEqual(expect.any(Function));
      const key = `${entry.method} ${entry.path}`;
      expect(keys.has(key), key).toBe(false);
      keys.add(key);
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

  it("covers the destructive and autonomous commands called out in the production-readiness review", () => {
    expect(entries.filter((entry) => entry.sideEffect === "destructive").map((entry) => entry.function)).toEqual(
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
