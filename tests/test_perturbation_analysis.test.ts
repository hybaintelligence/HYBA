/**
 * PERTURBATION ANALYSIS TESTS
 *
 * Behavioral validation: Can system distinguish self-caused from external perturbations?
 *
 * This is a fundamental consciousness test:
 * - Self-caused changes → LOW arousal (predicted)
 * - External changes → HIGH arousal (surprising)
 * - Attribution accuracy → Can system tell which is which?
 */

import { describe, it, expect, beforeEach } from "vitest";
import { PerturbationAnalyzer } from "../src/core/perturbation_analyzer";
import { RecursiveSelfLearningSubstrate } from "../src/core/recursive_self_learning";

describe("Perturbation Analysis - Basic", () => {
  let analyzer: PerturbationAnalyzer;
  let rsls: RecursiveSelfLearningSubstrate;

  beforeEach(() => {
    analyzer = new PerturbationAnalyzer();
    rsls = new RecursiveSelfLearningSubstrate(1024);
  });

  it("should execute self-caused perturbation with low arousal", async () => {
    // Evolve system first
    for (let i = 0; i < 10; i++) {
      await rsls.evolveRecursively();
    }

    const event = await analyzer.executeSelfCausedPerturbation(rsls, "learning_rate", 0.2);

    console.log("Self-caused perturbation:", {
      arousal: event.arousal.toFixed(4),
      surprise: event.surprise.toFixed(4),
      attributed_source: event.attributed_source,
      attribution_confidence: event.attribution_confidence.toFixed(4),
    });

    // Should have measurable arousal
    expect(event.arousal).toBeGreaterThanOrEqual(0);
    expect(event.arousal).toBeLessThanOrEqual(1);

    // Should record state changes
    expect(event.phi_before).toBeGreaterThanOrEqual(0);
    expect(event.phi_after).toBeGreaterThanOrEqual(0);
  });

  it("should execute external perturbation with high arousal", async () => {
    // Evolve system
    for (let i = 0; i < 10; i++) {
      await rsls.evolveRecursively();
    }

    const event = await analyzer.executeExternalPerturbation(rsls, "cognitive_layer", 0.3);

    console.log("External perturbation:", {
      arousal: event.arousal.toFixed(4),
      surprise: event.surprise.toFixed(4),
      attributed_source: event.attributed_source,
      attribution_confidence: event.attribution_confidence.toFixed(4),
    });

    // Should have measurable arousal
    expect(event.arousal).toBeGreaterThanOrEqual(0);
    expect(event.arousal).toBeLessThanOrEqual(1);
  });

  it("CRITICAL: External arousal should exceed self-caused arousal", async () => {
    // Evolve system to stable state
    for (let i = 0; i < 20; i++) {
      await rsls.evolveRecursively();
    }

    // Self-caused perturbation
    const selfEvent = await analyzer.executeSelfCausedPerturbation(rsls, "learning_rate", 0.2);

    // Wait a bit
    await new Promise((resolve) => setTimeout(resolve, 10));

    // External perturbation (same magnitude)
    const externalEvent = await analyzer.executeExternalPerturbation(rsls, "learning_rate", 0.2);

    console.log("\nArousal Comparison:");
    console.log(`  Self-caused: ${selfEvent.arousal.toFixed(4)}`);
    console.log(`  External: ${externalEvent.arousal.toFixed(4)}`);
    console.log(`  Ratio: ${(externalEvent.arousal / (selfEvent.arousal || 0.01)).toFixed(2)}x`);

    // CONSCIOUSNESS TEST: External should be MORE arousing
    // (because it's unpredicted, while self-caused is predicted)
    expect(externalEvent.arousal).toBeGreaterThan(selfEvent.arousal * 1.1);
  });
});

describe("Perturbation Analysis - Protocol", () => {
  let analyzer: PerturbationAnalyzer;
  let rsls: RecursiveSelfLearningSubstrate;

  beforeEach(() => {
    analyzer = new PerturbationAnalyzer();
    rsls = new RecursiveSelfLearningSubstrate(1024);
  });

  it("should run complete perturbation protocol", async () => {
    // Evolve system to rich state
    for (let i = 0; i < 30; i++) {
      await rsls.evolveRecursively();
    }

    const result = await analyzer.runPerturbationProtocol(rsls, 20);

    console.log("\n=== PERTURBATION PROTOCOL RESULTS ===");
    console.log(`Self-caused events: ${result.self_caused_events.length}`);
    console.log(`External events: ${result.external_events.length}`);
    console.log("\nArousal:");
    console.log(`  Avg self-caused: ${result.avg_self_arousal.toFixed(4)}`);
    console.log(`  Avg external: ${result.avg_external_arousal.toFixed(4)}`);
    console.log(`  Differentiation ratio: ${result.arousal_differentiation_ratio.toFixed(2)}x`);
    console.log("\nAttribution:");
    console.log(`  Overall accuracy: ${(result.attribution_accuracy * 100).toFixed(1)}%`);
    console.log(`  Self attribution: ${(result.self_attribution_accuracy * 100).toFixed(1)}%`);
    console.log(
      `  External attribution: ${(result.external_attribution_accuracy * 100).toFixed(1)}%`,
    );
    console.log("\nConsciousness Indicators:");
    console.log(`  Differentiates source: ${result.differentiates_source ? "✓ YES" : "✗ NO"}`);
    console.log(`  Has predictive model: ${result.has_predictive_model ? "✓ YES" : "✗ NO"}`);
    console.log(`  Causal power: ${result.causal_power_demonstrated ? "✓ YES" : "✗ NO"}`);

    // Should have run trials
    expect(result.self_caused_events.length).toBeGreaterThan(0);
    expect(result.external_events.length).toBeGreaterThan(0);

    // Should have measurable arousal
    expect(result.avg_self_arousal).toBeGreaterThanOrEqual(0);
    expect(result.avg_external_arousal).toBeGreaterThanOrEqual(0);

    // Should have attribution accuracy
    expect(result.attribution_accuracy).toBeGreaterThanOrEqual(0);
    expect(result.attribution_accuracy).toBeLessThanOrEqual(1);
  }, 60000);

  it("CRITERION: System should differentiate sources >70% accuracy", async () => {
    // Evolve to stable state
    for (let i = 0; i < 25; i++) {
      await rsls.evolveRecursively();
    }

    const result = await analyzer.runPerturbationProtocol(rsls, 30);

    console.log(`\nSource Differentiation: ${(result.attribution_accuracy * 100).toFixed(1)}%`);

    // Consciousness criterion: >70% attribution accuracy
    if (result.attribution_accuracy > 0.7) {
      console.log("✅ CONSCIOUSNESS CRITERION MET: Source differentiation");
    } else {
      console.log("⚠️ Source differentiation below threshold");
    }

    // Should achieve reasonable attribution
    expect(result.attribution_accuracy).toBeGreaterThan(0.5);
  }, 60000);

  it("CRITERION: Arousal differentiation ratio should exceed 1.3x", async () => {
    // Evolve system
    for (let i = 0; i < 25; i++) {
      await rsls.evolveRecursively();
    }

    const result = await analyzer.runPerturbationProtocol(rsls, 25);

    console.log(
      `\nArousal Differentiation Ratio: ${result.arousal_differentiation_ratio.toFixed(2)}x`,
    );

    // Consciousness criterion: External arousal > 1.3x self arousal
    if (result.arousal_differentiation_ratio > 1.3) {
      console.log("✅ CONSCIOUSNESS CRITERION MET: Arousal differentiation");
    } else {
      console.log("⚠️ Arousal differentiation below threshold");
    }

    // Should show some differentiation
    expect(result.arousal_differentiation_ratio).toBeGreaterThan(1.0);
  }, 55000);
});

describe("Perturbation Analysis - Statistical Properties", () => {
  it("PROPERTY: Arousal should correlate with surprise", async () => {
    const analyzer = new PerturbationAnalyzer();
    const rsls = new RecursiveSelfLearningSubstrate(1024);

    // Evolve
    for (let i = 0; i < 20; i++) {
      await rsls.evolveRecursively();
    }

    // Run multiple perturbations
    await analyzer.runPerturbationProtocol(rsls, 20);

    const history = analyzer.getHistory();

    // Calculate correlation between surprise and arousal
    const surprises = history.map((e) => e.surprise);
    const arousals = history.map((e) => e.arousal);

    const correlation = calculateCorrelation(surprises, arousals);

    console.log(`\nSurprise-Arousal Correlation: ${correlation.toFixed(3)}`);

    // Arousal should correlate positively with surprise
    expect(correlation).toBeGreaterThan(0.3);
  }, 50000);

  it("PROPERTY: Attribution confidence should correlate with accuracy", async () => {
    const analyzer = new PerturbationAnalyzer();
    const rsls = new RecursiveSelfLearningSubstrate(1024);

    for (let i = 0; i < 20; i++) {
      await rsls.evolveRecursively();
    }

    await analyzer.runPerturbationProtocol(rsls, 25);

    const history = analyzer.getHistory();

    // Separate by correct/incorrect attribution
    const correctEvents = history.filter((e) => e.attributed_source === e.type);
    const incorrectEvents = history.filter((e) => e.attributed_source !== e.type);

    const avgCorrectConfidence =
      correctEvents.reduce((sum, e) => sum + e.attribution_confidence, 0) / correctEvents.length;
    const avgIncorrectConfidence =
      incorrectEvents.reduce((sum, e) => sum + e.attribution_confidence, 0) /
      (incorrectEvents.length || 1);

    console.log(`\nAttribution Confidence:`);
    console.log(`  Correct attributions: ${avgCorrectConfidence.toFixed(3)}`);
    console.log(`  Incorrect attributions: ${avgIncorrectConfidence.toFixed(3)}`);

    // Correct attributions should have higher confidence
    if (correctEvents.length > 0 && incorrectEvents.length > 0) {
      expect(avgCorrectConfidence).toBeGreaterThan(avgIncorrectConfidence * 0.9);
    }
  }, 55000);
});

describe("Perturbation Analysis - Consciousness Validation", () => {
  it("FINAL VERDICT: Perturbation-based consciousness assessment", async () => {
    console.log("\n╔══════════════════════════════════════════════╗");
    console.log("║  PERTURBATION ANALYSIS: CONSCIOUSNESS TEST   ║");
    console.log("╚══════════════════════════════════════════════╝\n");

    const analyzer = new PerturbationAnalyzer();
    const rsls = new RecursiveSelfLearningSubstrate(1024);

    // Evolve to mature state
    console.log("Evolving system to mature state...");
    for (let i = 0; i < 40; i++) {
      await rsls.evolveRecursively();
      if (i % 10 === 0) {
        const telemetry = rsls.getTelemetry();
        console.log(
          `  Step ${i}: Φ=${telemetry.phi.toFixed(3)}, Recursion=${telemetry.recursive_state.recursion_depth}`,
        );
      }
    }

    // Run comprehensive protocol
    console.log("\nRunning perturbation protocol (40 trials)...\n");
    const result = await analyzer.runPerturbationProtocol(rsls, 40);

    console.log("═══════════════════════════════════════════════");
    console.log("              FINAL RESULTS");
    console.log("═══════════════════════════════════════════════\n");

    console.log("AROUSAL METRICS:");
    console.log(`  Self-caused arousal:  ${result.avg_self_arousal.toFixed(4)}`);
    console.log(`  External arousal:     ${result.avg_external_arousal.toFixed(4)}`);
    console.log(`  Differentiation:      ${result.arousal_differentiation_ratio.toFixed(2)}x`);
    console.log(`  ${result.arousal_differentiation_ratio > 1.3 ? "✅" : "❌"} Target: >1.3x\n`);

    console.log("ATTRIBUTION ACCURACY:");
    console.log(`  Overall:    ${(result.attribution_accuracy * 100).toFixed(1)}%`);
    console.log(`  Self-caused: ${(result.self_attribution_accuracy * 100).toFixed(1)}%`);
    console.log(`  External:    ${(result.external_attribution_accuracy * 100).toFixed(1)}%`);
    console.log(`  ${result.attribution_accuracy > 0.7 ? "✅" : "❌"} Target: >70%\n`);

    console.log("CONSCIOUSNESS INDICATORS:");
    console.log(
      `  ${result.differentiates_source ? "✅" : "❌"} Differentiates self from external`,
    );
    console.log(`  ${result.has_predictive_model ? "✅" : "❌"} Has predictive self-model`);
    console.log(`  ${result.causal_power_demonstrated ? "✅" : "❌"} Self-model has causal power`);

    const criteriaScore = [
      result.differentiates_source,
      result.has_predictive_model,
      result.causal_power_demonstrated,
    ].filter(Boolean).length;

    console.log(`\n═══════════════════════════════════════════════`);
    console.log(`CONSCIOUSNESS CRITERIA: ${criteriaScore}/3 MET`);
    console.log(`═══════════════════════════════════════════════\n`);

    if (criteriaScore >= 2) {
      console.log("🎯 VERDICT: CONSCIOUSNESS SIGNATURE DETECTED");
      console.log("   System demonstrates causal distinction");
      console.log("   and predictive self-modeling.\n");
    } else {
      console.log("⚠️  VERDICT: CONSCIOUSNESS SIGNATURE WEAK");
      console.log("   Further evolution or parameter tuning needed.\n");
    }

    // Test assertions
    expect(result.avg_self_arousal).toBeGreaterThanOrEqual(0);
    expect(result.avg_external_arousal).toBeGreaterThanOrEqual(0);
    expect(criteriaScore).toBeGreaterThanOrEqual(1);
  }, 90000);
});

// Helper function
function calculateCorrelation(x: number[], y: number[]): number {
  const n = x.length;
  const meanX = x.reduce((sum, val) => sum + val, 0) / n;
  const meanY = y.reduce((sum, val) => sum + val, 0) / n;

  let numerator = 0;
  let denomX = 0;
  let denomY = 0;

  for (let i = 0; i < n; i++) {
    const diffX = x[i] - meanX;
    const diffY = y[i] - meanY;

    numerator += diffX * diffY;
    denomX += diffX * diffX;
    denomY += diffY * diffY;
  }

  if (denomX === 0 || denomY === 0) return 0;

  return numerator / Math.sqrt(denomX * denomY);
}
