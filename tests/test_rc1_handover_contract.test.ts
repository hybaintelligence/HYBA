import { describe, expect, it } from "vitest";
import { metricTranslations } from "../src/intelligenceTranslations";
import { rc1AgentSignoffs, rc1KickoffChecklist, rc1UatGoldenPath } from "../src/rc1Handover";

describe("RC1 handover contract", () => {
  it("defines the four-stage client UAT golden path in order", () => {
    expect(rc1UatGoldenPath.map((stage) => stage.id)).toEqual([
      "executive-lens",
      "operational-self-healing",
      "strategic-crisis-simulation",
      "forensic-trust-audit",
    ]);
    for (const stage of rc1UatGoldenPath) {
      expect(stage.validation.length).toBeGreaterThanOrEqual(3);
      expect(stage.evidenceArtifacts.length).toBeGreaterThanOrEqual(3);
      expect(stage.acceptanceGoal).toMatch(/Prove/);
    }
  });

  it("keeps all four pre-handover agents in READY state with evidence references", () => {
    expect(rc1AgentSignoffs).toHaveLength(4);
    for (const signoff of rc1AgentSignoffs) {
      expect(signoff.readyStatement).toContain("READY");
      expect(signoff.evidenceRefs.length).toBeGreaterThan(0);
    }
  });

  it("defines the final client UAT kickoff checklist", () => {
    expect(rc1KickoffChecklist.map((check) => check.id)).toEqual([
      "metadata-check",
      "lens-persistence",
      "api-bridge",
      "signature-gate",
    ]);
    expect(rc1KickoffChecklist.find((check) => check.id === "api-bridge")?.verification).toContain(
      "/api/health",
    );
    expect(
      rc1KickoffChecklist.find((check) => check.id === "signature-gate")?.verification,
    ).toContain("No-Unattended-Writes");
  });

  it("translates backend self-healing signals for executive handover", () => {
    expect(metricTranslations.phi_density.executive.label).toBe("Reasoning Maturity");
    expect(metricTranslations.reflexive_cycles.executive.label).toBe("Logic Refinement");
    expect(metricTranslations.phi_density.auditor.evidenceView).toContain("Pre/post φ-density");
    expect(metricTranslations.reflexive_cycles.auditor.evidenceView).toContain(
      "no-unattended-writes",
    );
  });
});
