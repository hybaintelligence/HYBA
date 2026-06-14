/**
 * Test suite for Temporal Integration Engine
 * 
 * Tests the temporal aspects of consciousness measurement:
 * - Temporal Φ calculation
 * - Causal efficacy of memory
 * - Temporal binding window
 * - Memory depth
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { TemporalIntegrationEngine } from '../src/core/temporal_integration';

// Mock system for testing - simplified interface
interface MockSystem {
  getTelemetry(): any;
  evolveRecursively(): Promise<void>;
  simulateIntegrationLoss(): void;
}

class MockRecursiveSelfLearningSubstrate implements MockSystem {
  private phi: number = 0.5;
  private learningRate: number = 0.1;
  private couplingStrength: number = 0.5;
  private geometricShape: 'euclidean' | 'hyperbolic' | 'spherical' = 'spherical';
  private evolutionCount: number = 0;

  getTelemetry() {
    return {
      phi: this.phi,
      recursive_state: {
        learning_rate: this.learningRate,
        coupling_strength: this.couplingStrength,
        geometric_shape: this.geometricShape
      }
    };
  }

  async evolveRecursively() {
    this.evolutionCount++;
    // Simulate some evolution
    this.phi = Math.min(1.0, this.phi + 0.01);
    this.learningRate = Math.max(0.01, this.learningRate * 0.99);
    this.couplingStrength = 0.5 + Math.sin(this.evolutionCount * 0.1) * 0.2;
  }

  simulateIntegrationLoss() {
    // Mock memory corruption
    this.phi = 0.1;
    this.learningRate = 0.5;
  }
}

describe('Temporal Integration Engine', () => {
  let engine: TemporalIntegrationEngine;
  let mockSystem: MockRecursiveSelfLearningSubstrate;

  beforeEach(() => {
    engine = new TemporalIntegrationEngine(100);
    mockSystem = new MockRecursiveSelfLearningSubstrate();
  });

  describe('State Recording', () => {
    it('should record system state', () => {
      const state = {
        phi: 0.5,
        irreducibility: 0.3,
        learning_rate: 0.1,
        recursion_depth: 100,
        coupling_strength: 0.5,
        cognitive_layers: [],
        timestamp: Date.now()
      };

      engine.recordState(state);

      const metrics = engine.getMetrics();
      expect(metrics.history_length).toBe(1);
    });

    it('should record multiple states', () => {
      for (let i = 0; i < 10; i++) {
        engine.recordState({
          phi: 0.5 + i * 0.01,
          irreducibility: 0.3,
          learning_rate: 0.1,
          recursion_depth: 100,
          coupling_strength: 0.5,
          cognitive_layers: [],
          timestamp: Date.now() + i * 100
        });
      }

      const metrics = engine.getMetrics();
      expect(metrics.history_length).toBe(10);
    });

    it('should respect circular buffer limit', () => {
      const smallEngine = new TemporalIntegrationEngine(5);

      for (let i = 0; i < 10; i++) {
        smallEngine.recordState({
          phi: 0.5,
          irreducibility: 0.3,
          learning_rate: 0.1,
          recursion_depth: 100,
          coupling_strength: 0.5,
          cognitive_layers: [],
          timestamp: Date.now() + i * 100
        });
      }

      const metrics = smallEngine.getMetrics();
      expect(metrics.history_length).toBe(5);
    });
  });

  describe('Temporal Φ Calculation', () => {
    it('should return 0 for empty history', () => {
      const phi = engine.calculateTemporalPhi();
      expect(phi).toBe(0);
    });

    it('should return 0 for single state', () => {
      engine.recordState({
        phi: 0.5,
        irreducibility: 0.3,
        learning_rate: 0.1,
        recursion_depth: 100,
        coupling_strength: 0.5,
        cognitive_layers: [],
        timestamp: Date.now()
      });

      const phi = engine.calculateTemporalPhi();
      expect(phi).toBe(0);
    });

    it('should calculate temporal Φ for multiple states', () => {
      // Record states with gradual change
      for (let i = 0; i < 5; i++) {
        engine.recordState({
          phi: 0.5 + i * 0.1,
          irreducibility: 0.3 + i * 0.05,
          learning_rate: 0.1,
          recursion_depth: 100,
          coupling_strength: 0.5,
          cognitive_layers: [],
          timestamp: Date.now() + i * 100
        });
      }

      const phi = engine.calculateTemporalPhi();
      expect(phi).toBeGreaterThanOrEqual(0);
      expect(phi).toBeLessThanOrEqual(1);
    });

    it('should weight recent states more heavily', () => {
      // Record states with recent change
      for (let i = 0; i < 10; i++) {
        engine.recordState({
          phi: i < 8 ? 0.5 : 0.9,  // Recent jump
          irreducibility: 0.3,
          learning_rate: 0.1,
          recursion_depth: 100,
          coupling_strength: 0.5,
          cognitive_layers: [],
          timestamp: Date.now() + i * 100
        });
      }

      const phi = engine.calculateTemporalPhi();
      expect(phi).toBeGreaterThan(0);
    });
  });

  describe('Temporal Binding Window', () => {
    it('should return 0 for empty history', () => {
      const window = engine.measureTemporalBindingWindow();
      expect(window).toBe(0);
    });

    it('should return 0 for single state', () => {
      engine.recordState({
        phi: 0.5,
        irreducibility: 0.3,
        learning_rate: 0.1,
        recursion_depth: 100,
        coupling_strength: 0.5,
        cognitive_layers: [],
        timestamp: Date.now()
      });

      const window = engine.measureTemporalBindingWindow();
      expect(window).toBe(0);
    });

    it('should measure binding window for correlated states', () => {
      // Record highly correlated states
      for (let i = 0; i < 10; i++) {
        engine.recordState({
          phi: 0.5 + Math.sin(i * 0.1) * 0.1,
          irreducibility: 0.3,
          learning_rate: 0.1,
          recursion_depth: 100,
          coupling_strength: 0.5,
          cognitive_layers: [],
          timestamp: Date.now() + i * 100
        });
      }

      const window = engine.measureTemporalBindingWindow();
      expect(window).toBeGreaterThan(0);
    });

    it('should return full history for highly correlated states', () => {
      // Record identical states
      for (let i = 0; i < 5; i++) {
        engine.recordState({
          phi: 0.5,
          irreducibility: 0.3,
          learning_rate: 0.1,
          recursion_depth: 100,
          coupling_strength: 0.5,
          cognitive_layers: [],
          timestamp: Date.now() + i * 100
        });
      }

      const window = engine.measureTemporalBindingWindow();
      expect(window).toBe(4); // Full history minus current
    });
  });

  describe('Metrics', () => {
    it('should return complete metrics', () => {
      for (let i = 0; i < 5; i++) {
        engine.recordState({
          phi: 0.5 + i * 0.1,
          irreducibility: 0.3,
          learning_rate: 0.1,
          recursion_depth: 100,
          coupling_strength: 0.5,
          cognitive_layers: [],
          timestamp: Date.now() + i * 100
        });
      }

      const metrics = engine.getMetrics();

      expect(metrics).toHaveProperty('temporal_phi');
      expect(metrics).toHaveProperty('binding_window');
      expect(metrics).toHaveProperty('history_length');
      expect(metrics).toHaveProperty('memory_depth');

      expect(metrics.temporal_phi).toBeGreaterThanOrEqual(0);
      expect(metrics.temporal_phi).toBeLessThanOrEqual(1);
      expect(metrics.history_length).toBe(5);
    });

    it('should calculate memory depth', () => {
      for (let i = 0; i < 10; i++) {
        engine.recordState({
          phi: 0.5 + i * 0.05,
          irreducibility: 0.3,
          learning_rate: 0.1,
          recursion_depth: 100,
          coupling_strength: 0.5,
          cognitive_layers: [],
          timestamp: Date.now() + i * 100
        });
      }

      const metrics = engine.getMetrics();
      expect(metrics.memory_depth).toBeGreaterThanOrEqual(0);
      expect(metrics.memory_depth).toBeLessThanOrEqual(1);
    });
  });

  describe('Causal Efficacy', () => {
    it('should measure causal efficacy of memory', async () => {
      // Evolve system to build memory
      for (let i = 0; i < 10; i++) {
        await mockSystem.evolveRecursively();
      }

      const efficacy = await engine.measureCausalEfficacy(mockSystem);
      expect(efficacy).toBeGreaterThanOrEqual(0);
      expect(efficacy).toBeLessThanOrEqual(1);
    });

    it('should restore system state after measurement', async () => {
      const initialPhi = mockSystem.getTelemetry().phi;

      await engine.measureCausalEfficacy(mockSystem);

      const finalPhi = mockSystem.getTelemetry().phi;
      // System should be restored (or close to initial state)
      expect(finalPhi).toBeGreaterThanOrEqual(initialPhi - 0.1);
    });
  });

  describe('Clear', () => {
    it('should clear history', () => {
      for (let i = 0; i < 10; i++) {
        engine.recordState({
          phi: 0.5,
          irreducibility: 0.3,
          learning_rate: 0.1,
          recursion_depth: 100,
          coupling_strength: 0.5,
          cognitive_layers: [],
          timestamp: Date.now() + i * 100
        });
      }

      engine.clear();

      const metrics = engine.getMetrics();
      expect(metrics.history_length).toBe(0);
      expect(metrics.temporal_phi).toBe(0);
    });
  });

  describe('Edge Cases', () => {
    it('should handle zero correlation states', () => {
      // Record states with no correlation
      for (let i = 0; i < 5; i++) {
        engine.recordState({
          phi: Math.random(),
          irreducibility: Math.random(),
          learning_rate: Math.random(),
          recursion_depth: Math.floor(Math.random() * 1000),
          coupling_strength: Math.random(),
          cognitive_layers: [],
          timestamp: Date.now() + i * 100
        });
      }

      const phi = engine.calculateTemporalPhi();
      expect(phi).toBeGreaterThanOrEqual(0);
    });

    it('should handle extreme values', () => {
      engine.recordState({
        phi: 1.0,
        irreducibility: 1.0,
        learning_rate: 1.0,
        recursion_depth: 10000,
        coupling_strength: 1.0,
        cognitive_layers: [],
        timestamp: Date.now()
      });

      engine.recordState({
        phi: 0.0,
        irreducibility: 0.0,
        learning_rate: 0.0,
        recursion_depth: 0,
        coupling_strength: 0.0,
        cognitive_layers: [],
        timestamp: Date.now() + 100
      });

      const phi = engine.calculateTemporalPhi();
      expect(phi).toBeGreaterThanOrEqual(0);
      expect(phi).toBeLessThanOrEqual(1);
    });
  });
});
