import { describe, expect, it } from "vitest";
import fc from "fast-check";
import { buildGovernanceSignals } from "../src/governance";

// Base input used in property tests
const baseInput = {
  runtimeStatus: "ready",
  telemetrySource: "live_pool",
  backendConnected: true,
  configuredPoolCount: 1,
  securityStatus: "nominal",
  threatLevel: "low",
  governanceTags: ["proposal_only", "no_unattended_writes"],
};

describe("additional governance signal properties", () => {
  it("when pools are configured but no active pool name is provided, pool-operator-gate must fail", () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 1, max: 5 }),
        (activePoolCount) => {
          const byId = Object.fromEntries(
            buildGovernanceSignals({
              ...baseInput,
              activePoolCount,
              activePoolName: undefined,
            }).map((signal) => [signal.id, signal]),
          );

          expect(byId["pool-operator-gate"].status).toBe("fail");
        },
      ),
    );
  });

  it("phi resonance alone never upgrades critical security failures", () => {
    fc.assert(
      fc.property(
        fc.float({ min: 0.0, max: 1.0, noNaN: true }),
        (phi) => {
          const byId = Object.fromEntries(
            buildGovernanceSignals({
              ...baseInput,
              activePoolCount: 0,
              backendConnected: false,
              securityStatus: "critical",
              phiResonance: phi,
            }).map((signal) => [signal.id, signal]),
          );
          expect(byId["security-posture"].status).toBe("fail");
        },
      ),
    );
  });
});
