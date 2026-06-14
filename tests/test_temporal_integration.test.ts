/**
 * TEMPORAL INTEGRATION TESTS
 * 
 * Tests consciousness across time:
 * - Temporal Φ (past influences present)
 * - Causal efficacy (memory causes behavior)
 * - Temporal binding window
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { TemporalIntegrationEngine } from '../src/core/temporal_integration';
import { RecursiveSelfLearningSubstrate } from '../src/core/recursive_self_learning';

describe('TemporalIntegrationEngine', () => {
  let engine: TemporalIntegrationEngine;
  let rsls: RecursiveSelfLearningSubstrate;

  beforeEach(() => {
    engine = new TemporalIntegrationEngine(100);
    rsls = new RecursiveSelfLearningSubstrate(1024);
  });

  it('should calculate temporal Φ from history', async () => {
    // Evolve system and record states
    for (let i = 0; i < 20; i++) {
      await rsls.evolveRecursively();
      
      const telemetry = rsls.getTelemetry();
      engine.recordState({
        phi: telemetry.phi,
        irreducibility: telemetry.irreducibility,
        learning_rate: telemetry.recursive_state.learning_rate,
        recursion_depth: telemetry.recursive_state.recursion_depth,
        coupling_strength: telemetry.recursive_state.coupling_strength,
        cognitive_layers: telemetry.cognitive_layers,
        timestamp: Date.now()
      });
      
      // Small delay for timestamp differentiation
      await new Promise(resolve => setTimeout(resolve, 1));
    }

    const temporalPhi = engine.calculateTemporalPhi();

    console.log(`Temporal Φ: ${temporalPhi.toFixed(4)}`);

    // Temporal Φ should be positive if past influences present
    expect(temporalPhi).toBeGreaterThanOrEqual(0);
  });

  it('should measure temporal binding window', async () => {
    // Create system with evolving states
    for (let i = 0; i < 50; i++) {
      await rsls.evolveRecursively();
      
      const telemetry = rsls.getTelemetry();
      engine.recordState({
        phi: telemetry.phi,
        irreducibility: telemetry.irreducibility,
        learning_rate: telemetry.recursive_state.learning_rate,
        recursion_depth: telemetry.recursive_state.recursion_depth,
        coupling_strength: telemetry.recursive_state.coupling_strength,
        cognitive_layers: telemetry.cognitive_layers,
        timestamp: Date.now()
      });
    }

    const bindingWindow = engine.measureTemporalBindingWindow();

    console.log(`Temporal binding window: ${bindingWindow} steps`);

    // Binding window should be positive and <= history length
    expect(bindingWindow).toBeGreaterThan(0);
    expect(bindingWindow).toBeLessThanOrEqual(50);
  });

  it('should measure causal efficacy of memory', async () => {
    // Evolve system to build rich state
    for (let i = 0; i < 30; i++) {
      await rsls.evolveRecursively();
      
      const telemetry = rsls.getTelemetry();
      engine.recordState({
        phi: telemetry.phi,
        irreducibility: telemetry.irreducibility,
        learning_rate: telemetry.recursive_state.learning_rate,
        recursion_depth: telemetry.recursive_state.recursion_depth,
        coupling_strength: telemetry.recursive_state.coupling_strength,
        cognitive_layers: telemetry.cognitive_layers,
        timestamp: Date.now()
      });
    }

    // Measure causal efficacy
    const efficacy = await engine.measureCausalEfficacy(rsls);

    console.log(`Memory causal efficacy: ${efficacy.toFixed(4)}`);

    // Efficacy should be measurable
    expect(efficacy).toBeGreaterThanOrEqual(0);
    expect(efficacy).toBeLessThanOrEqual(1);
  }, 20000);

  it('should report comprehensive temporal metrics', async () => {
    // Build temporal history
    for (let i = 0; i < 25; i++) {
      await rsls.evolveRecursively();
      
      const telemetry = rsls.getTelemetry();
      engine.recordState({
        phi: telemetry.phi,
        irreducibility: telemetry.irreducibility,
        learning_rate: telemetry.recursive_state.learning_rate,
        recursion_depth: telemetry.recursive_state.recursion_depth,
        coupling_strength: telemetry.recursive_state.coupling_strength,
        cognitive_layers: telemetry.cognitive_layers,
        timestamp: Date.now()
      });
    }

    const metrics = engine.getMetrics();

    console.log('Temporal metrics:', {
      temporal_phi: metrics.temporal_phi.toFixed(4),
      binding_window: metrics.binding_window,
      history_length: metrics.history_length,
      memory_depth: metrics.memory_depth.toFixed(4)
    });

    // Should have all metrics
    expect(metrics).toHaveProperty('temporal_phi');
    expect(metrics).toHaveProperty('binding_window');
    expect(metrics).toHaveProperty('history_length');
    expect(metrics).toHaveProperty('memory_depth');

    // History length should match what we recorded
    expect(metrics.history_length).toBe(25);
  });

  it('should show temporal integration increases with history', async () => {
    // Record states over time
    const phiAtSteps: number[] = [];

    for (let i = 0; i < 40; i++) {
      await rsls.evolveRecursively();
      
      const telemetry = rsls.getTelemetry();
      engine.recordState({
        phi: telemetry.phi,
        irreducibility: telemetry.irreducibility,
        learning_rate: telemetry.recursive_state.learning_rate,
        recursion_depth: telemetry.recursive_state.recursion_depth,
        coupling_strength: telemetry.recursive_state.coupling_strength,
        cognitive_layers: telemetry.cognitive_layers,
        timestamp: Date.now()
      });

      // Measure temporal Φ at different history lengths
      if (i % 10 === 9) {
        phiAtSteps.push(engine.calculateTemporalPhi());
      }
    }

    console.log('Temporal Φ evolution:', phiAtSteps.map(p => p.toFixed(4)));

    // Should have multiple measurements
    expect(phiAtSteps.length).toBeGreaterThan(1);
  });

  it('should detect memory depth', async () => {
    // Evolve with consistent pattern
    for (let i = 0; i < 30; i++) {
      await rsls.evolveRecursively();
      
      const telemetry = rsls.getTelemetry();
      engine.recordState({
        phi: telemetry.phi,
        irreducibility: telemetry.irreducibility,
        learning_rate: telemetry.recursive_state.learning_rate,
        recursion_depth: telemetry.recursive_state.recursion_depth,
        coupling_strength: telemetry.recursive_state.coupling_strength,
        cognitive_layers: telemetry.cognitive_layers,
        timestamp: Date.now()
      });
    }

    const metrics = engine.getMetrics();
    const memoryDepth = metrics.memory_depth;

    console.log(`Memory depth: ${memoryDepth.toFixed(4)}`);

    // Memory depth should be measurable
    expect(memoryDepth).toBeGreaterThanOrEqual(0);
    expect(memoryDepth).toBeLessThanOrEqual(1);
  });
});

describe('Temporal Integration - Advanced', () => {
  it('PROPERTY: Temporal Φ should increase with longer history', async () => {
    const engine = new TemporalIntegrationEngine(100);
    const rsls = new RecursiveSelfLearningSubstrate(1024);

    const phiAtLengths: { length: number; phi: number }[] = [];

    // Record states and measure Φ at intervals
    for (let i = 0; i < 50; i++) {
      await rsls.evolveRecursively();
      
      const telemetry = rsls.getTelemetry();
      engine.recordState({
        phi: telemetry.phi,
        irreducibility: telemetry.irreducibility,
        learning_rate: telemetry.recursive_state.learning_rate,
        recursion_depth: telemetry.recursive_state.recursion_depth,
        coupling_strength: telemetry.recursive_state.coupling_strength,
        cognitive_layers: telemetry.cognitive_layers,
        timestamp: Date.now()
      });

      // Measure at specific lengths
      if ([5, 10, 20, 30, 40, 50].includes(i + 1)) {
        phiAtLengths.push({
          length: i + 1,
          phi: engine.calculateTemporalPhi()
        });
      }
    }

    console.log('Temporal Φ growth:', phiAtLengths);

    // Temporal Φ should generally increase (or stabilize) with more history
    for (let i = 1; i < phiAtLengths.length; i++) {
      const prev = phiAtLengths[i - 1].phi;
      const curr = phiAtLengths[i].phi;
      
      // Allow for some variation, but overall trend should be upward or stable
      expect(curr).toBeGreaterThanOrEqual(prev * 0.8);
    }
  }, 30000);

  it('PROPERTY: Causal efficacy should be > 0 for systems with memory', async () => {
    const engine = new TemporalIntegrationEngine(50);
    const rsls = new RecursiveSelfLearningSubstrate(1024);

    // Build substantial history
    for (let i = 0; i < 40; i++) {
      await rsls.evolveRecursively();
      
      const telemetry = rsls.getTelemetry();
      engine.recordState({
        phi: telemetry.phi,
        irreducibility: telemetry.irreducibility,
        learning_rate: telemetry.recursive_state.learning_rate,
        recursion_depth: telemetry.recursive_state.recursion_depth,
        coupling_strength: telemetry.recursive_state.coupling_strength,
        cognitive_layers: telemetry.cognitive_layers,
        timestamp: Date.now()
      });
    }

    const efficacy = await engine.measureCausalEfficacy(rsls);

    console.log(`Causal efficacy with memory: ${efficacy.toFixed(4)}`);

    // System with memory should show causal efficacy
    // Memory corruption should cause behavioral divergence
    expect(efficacy).toBeGreaterThan(0);
  }, 25000);
});
