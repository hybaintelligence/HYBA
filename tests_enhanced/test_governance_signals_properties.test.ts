import { describe, expect, it } from "vitest";
import fc from "fast-check";
import { buildGovernanceSignals } from "../src/governance";

const baseReadyInput = {
  runtimeStatus: "ready",
  telemetrySource: "live_pool",
  backendConnected: true,
  activePoolCount: 1,
  configuredPoolCount: 1,
  activePoolName: "CKPool",
  securityStatus: "nominal",
  threatLevel: "low",
  governanceTags: ["proposal_only", "no_unattended_writes"],
};

describe("operator governance signal properties", () => {
  it("never treats synthetic telemetry as a pass regardless of other readiness fields", () => {
    fc.assert(
      fc.property(
        fc.float({ min: 0, max: 1, noNaN: true }),
        fc.boolean(),
        (phiResonance, backendConnected) => {
          const byId = Object.fromEntries(
            buildGovernanceSignals({
              ...baseReadyInput,
              backendConnected,
              telemetrySource: "synthetic_fixture",
              phiResonance,
            }).map((signal) => [signal.id, signal]),
          );

          expect(byId["real-telemetry"].status).toBe("fail");
        },
      ),
    );
  });

  it("flags claim-boundary risk when bounded reflexive tags are absent", () => {
    fc.assert(
      fc.property(fc.float({ min: 0.619, max: 1, noNaN: true }), (phiResonance) => {
        const byId = Object.fromEntries(
          buildGovernanceSignals({
            ...baseReadyInput,
            phiResonance,
            governanceTags: [],
          }).map((signal) => [signal.id, signal]),
        );

        expect(byId["claim-boundary"].status).not.toBe("pass");
      }),
    );
  });

  it("does not allow phi metrics alone to rescue missing pool operator state", () => {
    fc.assert(
      fc.property(fc.float({ min: 0.9, max: 1, noNaN: true }), (phiResonance) => {
        const byId = Object.fromEntries(
          buildGovernanceSignals({
            ...baseReadyInput,
            activePoolCount: 0,
            activePoolName: undefined,
            phiResonance,
          }).map((signal) => [signal.id, signal]),
        );

        expect(byId["pool-operator-gate"].status).toBe("fail");
      }),
    );
  });
});
