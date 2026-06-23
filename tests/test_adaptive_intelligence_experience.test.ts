import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { METRIC_TRANSLATIONS } from "../src/components/IntelligenceTranslator";

describe("adaptive intelligence experience contracts", () => {
  it("ships buyer-facing translations for specialist intelligence metrics", () => {
    expect(METRIC_TRANSLATIONS.phiResonance.label).toBe("Coherence target");
    expect(METRIC_TRANSLATIONS.codeDistance.label).toBe("Resilience preset");
    expect(METRIC_TRANSLATIONS.evidenceSeal.plain).toContain("evidence");
  });

  it("keeps the assistant proposal-only and disables unattended auto-fix", () => {
    const source = readFileSync("src/components/AIAssistant.tsx", "utf8");
    expect(source).toContain("proposal_only: true");
    expect(source).toContain("auto_fix: false");
    expect(source).toContain("no_unattended_writes: true");
    expect(source).toContain("allowed_low_risk_commands: [\"refresh_telemetry\"]");
  });

  it("hides raw provisioning controls unless the adaptive lens is technical", () => {
    const ciaas = readFileSync("src/components/CIaaSServiceManager.tsx", "utf8");
    const qaas = readFileSync("src/components/QaaSComputerManager.tsx", "utf8");
    expect(ciaas).toContain("Starter Intelligence Rail");
    expect(ciaas).toContain("showTechnicalControls");
    expect(qaas).toContain("Regulated Evidence Rail");
    expect(qaas).toContain("Switch to Engineer or Expert lens");
  });
});
