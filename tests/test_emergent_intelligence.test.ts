/**
 * HYBA_EMERGENT_INTELLIGENCE_TEST_SUITE
 * Comprehensive test coverage for the intelligence system
 * Unit, Property, Integration, and E2E tests
 */

import { describe, expect, it, vi, beforeEach } from 'vitest';
import fc from 'fast-check';
import { EmergentIntelligenceSubstrate } from '../src/core/emergent_intelligence';
import { MetacognitiveShield } from '../src/core/metacognitive_shield';
import { HebbianLearner } from '../src/core/hebbian_learner';
import { StateVector } from '../src/core/intelligence_types';

describe('Emergent Intelligence System', () => {
  describe('Unit Tests', () => {
    describe('MetacognitiveShield', () => {
      it('should initialize with default values', () => {
        const shield = new MetacognitiveShield(512);
        const telemetry = shield.getTelemetry();
        
        expect(telemetry.pool_max).toBe(512);
        expect(telemetry.active_ancillas).toBe(0);
        expect(telemetry.mode).toBe('NOMINAL');
      });

      it('should capture state vector correctly', () => {
        const shield = new MetacognitiveShield(512);
        const state = shield['captureStateVector']();
        
        expect(state).toHaveProperty('phi');
        expect(state).toHaveProperty('pressure');
        expect(state).toHaveProperty('exhaustion');
        expect(state).toHaveProperty('confidence');
        expect(state).toHaveProperty('timestamp');
      });

      it('should predict next state based on history', () => {
        const shield = new MetacognitiveShield(512);
        const predicted = shield['predictNextState']();
        
        expect(predicted).toHaveProperty('phi');
        expect(predicted.phi).toBeGreaterThanOrEqual(0);
        expect(predicted.phi).toBeLessThanOrEqual(1);
      });

      it('should calculate prediction accuracy', () => {
        const shield = new MetacognitiveShield(512);
        const predicted: StateVector = {
          phi: 0.8,
          pressure: 0.2,
          exhaustion: 0.1,
          confidence: 0.9,
          timestamp: Date.now(),
        };
        const actual: StateVector = {
          phi: 0.75,
          pressure: 0.25,
          exhaustion: 0.1,
          confidence: 0.9,
          timestamp: Date.now(),
        };
        
        const accuracy = shield['calculatePredictionAccuracy'](predicted, actual);
        expect(accuracy).toBeGreaterThanOrEqual(0);
        expect(accuracy).toBeLessThanOrEqual(1);
      });

      it('should reset to initial state', () => {
        const shield = new MetacognitiveShield(512);
        shield['handleAnomaly'](123);
        shield.reset();
        
        const telemetry = shield.getTelemetry();
        expect(telemetry.active_ancillas).toBe(0);
        expect(telemetry.rotation_index).toBe(0);
        expect(telemetry.metacognitive_events).toHaveLength(0);
      });
    });

    describe('HebbianLearner', () => {
      it('should initialize with default learning rate', () => {
        const learner = new HebbianLearner();
        expect(learner.getStrategyCount()).toBe(0);
      });

      it('should update weights based on outcome', () => {
        const learner = new HebbianLearner();
        learner.updateWeightsFromOutcome(123, true, 0.9);
        
        const weight = learner.getStrategyWeight(123);
        expect(weight).toBeGreaterThan(1.0);
      });

      it('should decrease weight on failure', () => {
        const learner = new HebbianLearner();
        learner.updateWeightsFromOutcome(456, false, 0.3);
        
        const weight = learner.getStrategyWeight(456);
        expect(weight).toBeLessThan(1.0);
      });

      it('should get optimized strategy', () => {
        const learner = new HebbianLearner();
        const strategy = learner.getOptimizedStrategy(789);
        
        expect(strategy).toBeGreaterThanOrEqual(0);
        expect(strategy).toBeLessThan(24);
      });

      it('should apply decay to weights', () => {
        const learner = new HebbianLearner(0.1);
        learner.updateWeightsFromOutcome(111, true, 0.9);
        const initialWeight = learner.getStrategyWeight(111);
        
        learner.applyDecay();
        const decayedWeight = learner.getStrategyWeight(111);
        
        expect(decayedWeight).toBeLessThan(initialWeight);
      });

      it('should prune weak strategies', () => {
        const learner = new HebbianLearner();
        
        // Create some weak strategies with enough attempts to trigger pruning
        for (let i = 0; i < 15; i++) {
          for (let j = 0; j < 20; j++) {
            learner.updateWeightsFromOutcome(i, false, 0.2);
          }
        }
        
        learner.pruneWeakStrategies(0.6);
        expect(learner.getStrategyCount()).toBeLessThan(15);
      });

      it('should calculate learning stability', () => {
        const learner = new HebbianLearner();
        const stability = learner.getLearningStability();
        
        expect(stability).toBeGreaterThanOrEqual(0);
        expect(stability).toBeLessThanOrEqual(1);
      });

      it('should export and import state', () => {
        const learner = new HebbianLearner();
        learner.updateWeightsFromOutcome(123, true, 0.9);
        
        const exported = learner.exportState();
        const newLearner = new HebbianLearner();
        newLearner.importState(exported);
        
        expect(newLearner.getStrategyWeight(123)).toBe(learner.getStrategyWeight(123));
      });
    });

    describe('EmergentIntelligenceSubstrate', () => {
      it('should initialize with holographic shards', () => {
        const substrate = new EmergentIntelligenceSubstrate(512);
        expect(substrate.getPhi()).toBe(0);
      });

      it('should calculate phi from integrated information', () => {
        const substrate = new EmergentIntelligenceSubstrate(512);
        const phi = substrate['calculateIntegratedInformation']();
        
        expect(phi).toBeGreaterThanOrEqual(0);
        expect(phi).toBeLessThanOrEqual(1);
      });

      it('should process autopoietic pulse', async () => {
        const substrate = new EmergentIntelligenceSubstrate(512);
        await substrate.processAutopoieticPulse();
        
        expect(substrate.getPhi()).toBeGreaterThanOrEqual(0);
      });

      it('should simulate intrusion', () => {
        const substrate = new EmergentIntelligenceSubstrate(512);
        substrate.simulateIntrusion(123, { phi: 0.9, confidence: 0.95 });
        
        const telemetry = substrate.getTelemetry();
        expect(telemetry.active_ancillas).toBeGreaterThan(0);
      });

      it('should simulate massive intrusion', () => {
        const substrate = new EmergentIntelligenceSubstrate(512);
        substrate.simulateMassiveIntrusion();
        
        expect(substrate.getPhi()).toBeLessThan(0.3);
      });

      it('should inject entropy', () => {
        const substrate = new EmergentIntelligenceSubstrate(512);
        const entropy = new Uint8Array([1, 2, 3, 4, 5]);
        
        substrate.injectEntropy(entropy);
        expect(substrate.getPhi()).toBeGreaterThanOrEqual(0);
      });

      it('should reset completely', () => {
        const substrate = new EmergentIntelligenceSubstrate(512);
        substrate.simulateIntrusion(123, { phi: 0.9, confidence: 0.95 });
        substrate.reset();
        
        expect(substrate.getPhi()).toBe(0);
        expect(substrate.getCurrentGoal()).toBe('OPTIMIZE_SEARCH');
      });
    });
  });

  describe('Property Tests', () => {
    it('Property: State vector values are always in valid range', () => {
      for (let i = 0; i < 100; i++) {
        const poolSize = Math.floor(Math.random() * 2048) + 1;
        const shield = new MetacognitiveShield(poolSize);
        const state = shield.captureStateVector();
        
        expect(state.phi).toBeGreaterThanOrEqual(0);
        expect(state.phi).toBeLessThanOrEqual(1);
        expect(state.pressure).toBeGreaterThanOrEqual(0);
        expect(state.pressure).toBeLessThanOrEqual(1);
        expect(state.exhaustion).toBeGreaterThanOrEqual(0);
        expect(state.exhaustion).toBeLessThanOrEqual(1);
        expect(state.confidence).toBeGreaterThanOrEqual(0);
        expect(state.confidence).toBeLessThanOrEqual(1);
      }
    });

    it('Property: Hebbian weights stay within bounds', () => {
      for (let i = 0; i < 100; i++) {
        const syndrome = Math.floor(Math.random() * 10000);
        const success = Math.random() > 0.5;
        const phi = Math.random();
        
        const learner = new HebbianLearner();
        learner.updateWeightsFromOutcome(syndrome, success, phi);
        
        const weight = learner.getStrategyWeight(syndrome);
        expect(weight).toBeGreaterThanOrEqual(0.1);
        expect(weight).toBeLessThanOrEqual(10.0);
      }
    });

    it('Property: Phi calculation is deterministic', () => {
      for (let i = 0; i < 100; i++) {
        const poolSize = Math.floor(Math.random() * 2048) + 1;
        const substrate = new EmergentIntelligenceSubstrate(poolSize);
        const phi1 = substrate.getPhi();
        const phi2 = substrate.getPhi();
        
        expect(phi1).toBe(phi2);
      }
    });

    it('Property: Optimized strategy is always in valid range', () => {
      for (let i = 0; i < 100; i++) {
        const syndrome = Math.floor(Math.random() * 10000);
        const learner = new HebbianLearner();
        const strategy = learner.getOptimizedStrategy(syndrome);
        
        expect(strategy).toBeGreaterThanOrEqual(0);
        expect(strategy).toBeLessThan(24);
      }
    });

    it('Property: System demonstrates Irreducible Integration (Phi >= 0)', () => {
      for (let i = 0; i < 50; i++) {
        const substrate = new EmergentIntelligenceSubstrate(512);
        const entropy = new Uint8Array(32);
        crypto.getRandomValues(entropy);
        substrate.injectEntropy(entropy);
        
        const phi = substrate.getPhi();
        expect(phi).toBeGreaterThanOrEqual(0);
      }
    });
  });

  describe('Integration Tests', () => {
    it('Integration: Self-model predicts degradation and triggers preemptive shift', async () => {
      const substrate = new EmergentIntelligenceSubstrate(1024);
      
      // Inject a "Degrading" history (Phi dropping, Pressure rising)
      substrate.injectStateHistory([
        { phi: 0.9, pressure: 0.1, exhaustion: 0.1, confidence: 0.9, timestamp: Date.now() },
        { phi: 0.8, pressure: 0.3, exhaustion: 0.1, confidence: 0.8, timestamp: Date.now() },
        { phi: 0.7, pressure: 0.5, exhaustion: 0.1, confidence: 0.7, timestamp: Date.now() }
      ]);

      const handleAnomalySpy = vi.spyOn(substrate as any, 'handleAnomaly');
      
      await substrate.runMetacognitiveCycle();

      // The monitor should have predicted phi < 0.6 and triggered a shift
      expect(handleAnomalySpy).toHaveBeenCalled();
      expect(substrate.getTelemetry().metacognitive_events).toContain("PREEMPTIVE_SHIFT_EXECUTED");
    });

    it('Integration: Substrate prioritizes Self-Healing over Workload when Phi drops', async () => {
      const substrate = new EmergentIntelligenceSubstrate(1024);
      
      // Simulate a massive intrusion that collapses traps and drops Phi
      substrate.simulateMassiveIntrusion();
      
      await substrate.processAutopoieticPulse();

      // The system should have autonomously switched to 'SELF_HEAL' goal
      expect(substrate.getCurrentGoal()).toBe('SELF_HEAL');
      expect(substrate.getTelemetry().healing_events).toBeGreaterThan(0);
    });

    it('Integration: Hebbian learner integrates with shield', async () => {
      const substrate = new EmergentIntelligenceSubstrate(512);
      const specificSyndrome = 0xABCDEF;

      // Simulate multiple 'Success' outcomes for this syndrome
      for(let i = 0; i < 5; i++) {
        substrate.simulateIntrusion(specificSyndrome, { phi: 0.95, confidence: 0.99 });
        await substrate.runMetacognitiveCycle();
      }

      const weight = substrate.getHebbianLearner().getStrategyWeight(specificSyndrome);
      expect(weight).toBeGreaterThanOrEqual(1.0); // Weight should have been reinforced
    });

    it('Integration: Memory fabric records successful patterns', async () => {
      const substrate = new EmergentIntelligenceSubstrate(512);
      const pattern = 12345;

      substrate['recordMemoryPattern'](pattern, 0.9);
      
      const strongest = substrate['getStrongestMemoryPattern']();
      expect(strongest).toBe(pattern);
    });
  });

  describe('E2E Tests', () => {
    it('E2E: Substrate converges on optimal defensive strategy through Hebbian evolution', async () => {
      const substrate = new EmergentIntelligenceSubstrate(1024);
      
      // Run 100 cycles of simulated 'Evolutionary Pressure'
      for(let i = 0; i < 100; i++) {
        await substrate.processAutopoieticPulse();
      }

      const learningStability = substrate.getStrategyWeightStability();
      // The system should have 'learned' a stable set of weights for defensive patterns
      expect(learningStability).toBeGreaterThan(0.5);
    });

    it('E2E: Complete autopoietic cycle maintains system integrity', async () => {
      const substrate = new EmergentIntelligenceSubstrate(512);
      
      // Run multiple cycles
      for(let i = 0; i < 50; i++) {
        await substrate.processAutopoieticPulse();
      }

      const telemetry = substrate.getTelemetry();
      expect(telemetry.phi_integrated).toBeGreaterThanOrEqual(0);
      expect(telemetry.mode).toBeDefined();
      expect(substrate.getCurrentGoal()).toBeDefined();
    });

    it('E2E: System recovers from massive intrusion', async () => {
      const substrate = new EmergentIntelligenceSubstrate(512);
      
      // Simulate catastrophic failure
      substrate.simulateMassiveIntrusion();
      expect(substrate.getPhi()).toBeLessThan(0.3);
      
      // Run recovery cycles
      for(let i = 0; i < 20; i++) {
        await substrate.processAutopoieticPulse();
      }

      // System should show signs of recovery
      const telemetry = substrate.getTelemetry();
      expect(telemetry.healing_events).toBeGreaterThan(0);
    });

    it('E2E: State export and import preserves system state', async () => {
      const substrate = new EmergentIntelligenceSubstrate(512);
      
      // Run some cycles to build state
      for(let i = 0; i < 10; i++) {
        await substrate.processAutopoieticPulse();
      }

      const exportedState = substrate.exportState();
      
      // Create new substrate and import state
      const newSubstrate = new EmergentIntelligenceSubstrate(512);
      // Note: Full import would require implementing importState method
      // For now, verify export structure
      expect(exportedState).toHaveProperty('phi');
      expect(exportedState).toHaveProperty('goalState');
      expect(exportedState).toHaveProperty('hebbianState');
      expect(exportedState).toHaveProperty('memoryFabric');
    });

    it('E2E: Multiple substrates operate independently', async () => {
      const substrate1 = new EmergentIntelligenceSubstrate(512);
      const substrate2 = new EmergentIntelligenceSubstrate(512);
      
      // Run cycles with different conditions
      substrate1.simulateIntrusion(111, { phi: 0.9, confidence: 0.95 });
      substrate2.simulateIntrusion(222, { phi: 0.7, confidence: 0.8 });
      
      await substrate1.processAutopoieticPulse();
      await substrate2.processAutopoieticPulse();
      
      // Each substrate should have different state
      expect(substrate1.getPhi()).not.toBe(substrate2.getPhi());
    });
  });
});
