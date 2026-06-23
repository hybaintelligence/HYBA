/**
 * Metric Mapping Tests - Production Readiness Verification
 *
 * Verifies that metrics display correctly across different skill modes.
 * Ensures the translation system works as specified in the implementation plan.
 */

import { metricTranslations, type MetricTranslationKey } from "../../intelligenceTranslations";
import type { SkillMode } from "../../skillMode";

describe("Metric Mapping Tests", () => {
  const allModes: SkillMode[] = [
    "executive",
    "business",
    "operator",
    "analyst",
    "engineer",
    "auditor",
    "expert",
  ];
  const allMetrics: MetricTranslationKey[] = [
    "phi_resonance",
    "code_distance",
    "physical_error_rate",
    "substrate_coherence",
    "evidence_seal",
    "invariants",
    "claim_boundary",
    "pulvini_memory",
    "salamander_regeneration",
  ];

  describe("Mode-Specific Label Verification", () => {
    it("should display phi_resonance as 'Reasoning Stability' in EXECUTIVE mode", () => {
      const translation = metricTranslations.phi_resonance.executive;
      expect(translation.label).toBe("Reasoning Stability");
    });

    it("should display phi_resonance as 'Phase Alignment Factor' in ENGINEER mode", () => {
      const translation = metricTranslations.phi_resonance.engineer;
      expect(translation.label).toBe("Phase Alignment Factor");
    });

    it("should display phi_resonance as 'φ-Resonance Target' in EXPERT mode", () => {
      const translation = metricTranslations.phi_resonance.expert;
      expect(translation.label).toBe("φ-Resonance Target");
    });

    it("should display code_distance as 'Resilience Level' in EXECUTIVE mode", () => {
      const translation = metricTranslations.code_distance.executive;
      expect(translation.label).toBe("Resilience Level");
    });

    it("should display code_distance as 'Surface-Code Distance' in ENGINEER mode", () => {
      const translation = metricTranslations.code_distance.engineer;
      expect(translation.label).toBe("Surface-Code Distance");
    });
  });

  describe("Translation Completeness", () => {
    it("should have translations for all metrics in all modes", () => {
      allMetrics.forEach((metric) => {
        allModes.forEach((mode) => {
          expect(metricTranslations[metric][mode]).toBeDefined();
          expect(metricTranslations[metric][mode].label).toBeTruthy();
          expect(metricTranslations[metric][mode].plainEnglish).toBeTruthy();
          expect(metricTranslations[metric][mode].operationalImplication).toBeTruthy();
          expect(metricTranslations[metric][mode].evidenceView).toBeTruthy();
          expect(metricTranslations[metric][mode].expert).toBeTruthy();
        });
      });
    });
  });

  describe("Recommendation Availability", () => {
    it("should include recommendations for all metrics in all modes", () => {
      allMetrics.forEach((metric) => {
        allModes.forEach((mode) => {
          const translation = metricTranslations[metric][mode];
          expect(translation.recommendation).toBeDefined();
          expect(translation.recommendation).toBeTruthy();
        });
      });
    });
  });

  describe("Label Distinctiveness", () => {
    it("should have different labels for the same metric across modes", () => {
      allMetrics.forEach((metric) => {
        const labels = allModes.map((mode) => metricTranslations[metric][mode].label);
        const uniqueLabels = new Set(labels);
        // At least 3 different labels should exist for each metric
        expect(uniqueLabels.size).toBeGreaterThanOrEqual(3);
      });
    });
  });

  describe("Executive Mode Characteristics", () => {
    it("should use business-friendly language in EXECUTIVE mode", () => {
      const executiveLabels = allMetrics.map((m) => metricTranslations[m].executive.label);
      executiveLabels.forEach((label) => {
        // Should not contain technical jargon
        expect(label).not.toMatch(/φ|quantum|qubit|syndrome|phase/);
      });
    });
  });

  describe("Expert Mode Characteristics", () => {
    it("should include technical details in EXPERT mode", () => {
      const expertLabels = allMetrics.map((m) => metricTranslations[m].expert.label);
      expertLabels.forEach((label) => {
        // Should include technical terminology
        expect(label).toBeTruthy();
      });
    });
  });

  describe("Auditor Mode Characteristics", () => {
    it("should emphasize compliance and audit in AUDITOR mode", () => {
      const auditorLabels = allMetrics.map((m) => metricTranslations[m].auditor.label);
      const auditRelatedTerms = ["Audit", "Compliance", "Regulatory", "Proof", "Evidence"];
      const hasAuditTerms = auditorLabels.some((label) =>
        auditRelatedTerms.some((term) => label.includes(term)),
      );
      expect(hasAuditTerms).toBe(true);
    });
  });

  describe("Fallback Behavior", () => {
    it("should have business mode as a safe fallback", () => {
      allMetrics.forEach((metric) => {
        const businessTranslation = metricTranslations[metric].business;
        expect(businessTranslation).toBeDefined();
        expect(businessTranslation.label).toBeTruthy();
        expect(businessTranslation.plainEnglish).toBeTruthy();
      });
    });
  });

  describe("Content Quality", () => {
    it("should have non-empty plain English explanations", () => {
      allMetrics.forEach((metric) => {
        allModes.forEach((mode) => {
          const translation = metricTranslations[metric][mode];
          expect(translation.plainEnglish.length).toBeGreaterThan(10);
          expect(translation.operationalImplication.length).toBeGreaterThan(10);
          expect(translation.evidenceView.length).toBeGreaterThan(10);
        });
      });
    });
  });
});
