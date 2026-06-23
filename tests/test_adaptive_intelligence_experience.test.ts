import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { metricTranslations } from "../src/intelligenceTranslations";

describe("adaptive intelligence experience contracts", () => {
  it("ships buyer-facing translations for specialist intelligence metrics", () => {
    // Executive mode should use business-friendly labels
    expect(metricTranslations.phi_resonance.executive.label).toBe("Reasoning Stability");
    expect(metricTranslations.code_distance.executive.label).toBe("Resilience Level");
    expect(metricTranslations.evidence_seal.executive.label).toBe("Audit Seal");
    
    // Business mode should use commercial language
    expect(metricTranslations.phi_resonance.business.label).toBe("Confidence Level");
    expect(metricTranslations.code_distance.business.label).toBe("Error Protection");
    
    // Expert mode should use technical terminology
    expect(metricTranslations.phi_resonance.expert.label).toBe("φ-Resonance Target");
    expect(metricTranslations.code_distance.expert.label).toBe("Code Distance");
  });

  it("keeps the assistant proposal-only and disables unattended auto-fix", () => {
    const source = readFileSync("src/components/AIAssistant.tsx", "utf8");
    expect(source).toContain("proposal_only: true");
    expect(source).toContain("auto_fix: false");
    expect(source).toContain("require_human_approval: true");
    expect(source).toContain("LOW_RISK_ALLOWLIST");
  });

  it("hides raw provisioning controls unless the adaptive lens is technical", () => {
    const ciaas = readFileSync("src/components/CIaaSServiceManager.tsx", "utf8");
    const qaas = readFileSync("src/components/QaaSComputerManager.tsx", "utf8");
    
    // Presets should be present for business-friendly provisioning
    expect(ciaas).toContain("Starter CI Rail");
    expect(ciaas).toContain("Enterprise Operations Rail");
    expect(ciaas).toContain("Regulated Regeneration Rail");
    expect(qaas).toContain("Starter QI Rail");
    expect(qaas).toContain("Enterprise Strategy Rail");
    expect(qaas).toContain("Regulated Evidence Rail");
    
    // Technical controls should be conditional on expert mode
    expect(ciaas).toContain("isExpertMode");
    expect(qaas).toContain("isExpertMode");
  });

  it("provides skill mode context with role-based defaults", () => {
    const skillModeSource = readFileSync("src/skillMode.tsx", "utf8");
    expect(skillModeSource).toContain("SkillModeProvider");
    expect(skillModeSource).toContain("useSkillMode");
    expect(skillModeSource).toContain("ROLE_SKILL_MODE_DEFAULTS");
    expect(skillModeSource).toContain("executive");
    expect(skillModeSource).toContain("business");
    expect(skillModeSource).toContain("operator");
    expect(skillModeSource).toContain("analyst");
    expect(skillModeSource).toContain("engineer");
    expect(skillModeSource).toContain("auditor");
    expect(skillModeSource).toContain("expert");
  });

  it("segments mining controls behind treasury roles", () => {
    const featuresSource = readFileSync("src/config/features.ts", "utf8");
    expect(featuresSource).toContain("ceo_heir_apparent");
    expect(featuresSource).toContain("chairman");
    expect(featuresSource).toContain("cto");
    expect(featuresSource).toContain("cfo");
    expect(featuresSource).toContain("treasury");
    expect(featuresSource).toContain("hasInternalAccess");
  });

  it("includes evidence-bound answer components", () => {
    const translatorSource = readFileSync("src/components/IntelligenceTranslator.tsx", "utf8");
    expect(translatorSource).toContain("ClaimBoundaryBadge");
    expect(translatorSource).toContain("EvidenceBoundAnswer");
    expect(translatorSource).toContain("ProofExplainer");
  });

  it("provides use-case studio for intent-first workflows", () => {
    const adaptiveSource = readFileSync("src/components/AdaptiveIntelligenceLayer.tsx", "utf8");
    expect(adaptiveSource).toContain("UseCaseStudio");
    expect(adaptiveSource).toContain("DecisionCockpit");
    expect(adaptiveSource).toContain("workflowTemplates");
  });
});
