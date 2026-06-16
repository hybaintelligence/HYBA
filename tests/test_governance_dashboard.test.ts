import { describe, expect, it } from "vitest";
import { buildGovernanceSignals } from "../src/governance";

describe("operator governance signals", () => {
  it("passes only with reachable runtime, real telemetry, pool, and bounded reflexive tags", () => {
    const signals = buildGovernanceSignals({
      runtimeStatus: "ready",
      telemetrySource: "live_pool",
      backendConnected: true,
      activePoolCount: 1,
      configuredPoolCount: 1,
      activePoolName: "CKPool",
      securityStatus: "nominal",
      threatLevel: "low",
      phiResonance: 0.72,
      governanceTags: ["proposal_only", "no_unattended_writes"],
    });

    expect(signals.every((signal) => signal.status === "pass")).toBe(true);
  });

  it("fails synthetic telemetry and missing backend readiness", () => {
    const byId = Object.fromEntries(
      buildGovernanceSignals({
        runtimeStatus: "degraded",
        telemetrySource: "synthetic_fixture",
        backendConnected: false,
        configuredPoolCount: 0,
        activePoolCount: 0,
        securityStatus: "critical",
      }).map((signal) => [signal.id, signal]),
    );

    expect(byId["runtime-readiness"].status).toBe("fail");
    expect(byId["real-telemetry"].status).toBe("fail");
    expect(byId["pool-operator-gate"].status).toBe("fail");
    expect(byId["security-posture"].status).toBe("fail");
    expect(byId["claim-boundary"].status).toBe("warn");
  });
});
