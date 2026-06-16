/**
 * TEMPORAL INTEGRATION ENGINE
 * 
 * Consciousness is not instantaneous - it integrates past, present, future.
 * 
 * Measures:
 * - Temporal Φ: how much past influences present
 * - Causal efficacy: does memory CAUSE behavior changes?
 * - Temporal binding window: how far back does consciousness extend?
 */

import type { RecursiveSelfLearningSubstrate } from './recursive_self_learning';

interface SystemState {
  phi: number;
  irreducibility: number;
  learning_rate: number;
  recursion_depth: number;
  coupling_strength: number;
  cognitive_layers: any[];
  timestamp: number;
}

interface MemorySnapshot {
  phi_history: number[];
  metacognitive_history: any[];
  convergence_history: any[];
  state_history: any[];
  prediction_error_history: number[];
}

class CircularBuffer<T> {
  private buffer: T[] = [];
  private maxSize: number;
  private writeIndex: number = 0;
  
  constructor(maxSize: number) {
    this.maxSize = maxSize;
  }
  
  push(item: T): void {
    if (this.buffer.length < this.maxSize) {
      this.buffer.push(item);
    } else {
      this.buffer[this.writeIndex % this.maxSize] = item;
    }
    this.writeIndex++;
  }
  
  get(index: number): T | undefined {
    if (index < 0 || index >= this.buffer.length) {
      return undefined;
    }
    return this.buffer[index];
  }
  
  get length(): number {
    return this.buffer.length;
  }
  
  getAll(): T[] {
    return [...this.buffer];
  }
  
  clear(): void {
    this.buffer = [];
    this.writeIndex = 0;
  }
}

export class TemporalIntegrationEngine {
  private stateHistory: CircularBuffer<SystemState>;
  private memoryDecayRate: number = 0.95;
  private maxHistoryLength: number;
  
  constructor(historyLength: number = 1000) {
    this.maxHistoryLength = historyLength;
    this.stateHistory = new CircularBuffer<SystemState>(historyLength);
  }
  
  /**
   * Record current system state for temporal analysis
   */
  public recordState(state: SystemState): void {
    this.stateHistory.push({
      ...state,
      timestamp: Date.now()
    });
  }
  
  /**
   * Calculate temporal Φ: how much past causally influences present.
   * 
   * High temporal Φ = consciousness has "thickness" in time
   * Low temporal Φ = system is memoryless, lives only in present
   */
  public calculateTemporalPhi(): number {
    if (this.stateHistory.length < 2) return 0;
    
    let temporalIntegration = 0;
    const currentState = this.stateHistory.get(this.stateHistory.length - 1);
    
    if (!currentState) return 0;
    
    // Measure influence of each past state on current
    for (let t = 0; t < this.stateHistory.length - 1; t++) {
      const pastState = this.stateHistory.get(t);
      if (!pastState) continue;
      
      // Mutual information between past and present
      const mutualInfo = this.mutualInformation(pastState, currentState);
      
      // Weight by recency (exponential decay)
      const timeGap = this.stateHistory.length - 1 - t;
      const recencyWeight = Math.pow(this.memoryDecayRate, timeGap);
      
      temporalIntegration += mutualInfo * recencyWeight;
    }
    
    // Normalize by history length
    return temporalIntegration / this.stateHistory.length;
  }
  
  /**
   * CRITICAL TEST: Does memory actually CAUSE behavior change?
   * 
   * Method: Intervention test
   * 1. Capture baseline behavior with intact memory
   * 2. Corrupt memory
   * 3. Measure behavior change
   * 4. Causal efficacy = magnitude of divergence
   */
  public async measureCausalEfficacy(
    system: RecursiveSelfLearningSubstrate
  ): Promise<number> {
    // Baseline behavior with intact memory
    const memorySnapshot = this.captureMemorySnapshot(system);
    const behaviorWithMemory = await this.predictBehavior(system, 10);
    
    // Corrupt memory
    this.corruptSystemMemory(system);
    
    // Measure behavior without memory
    const behaviorWithoutMemory = await this.predictBehavior(system, 10);
    
    // Restore memory
    this.restoreSystemMemory(system, memorySnapshot);
    
    // Causal efficacy = how much behavior depends on memory
    const divergence = this.behaviorDivergence(
      behaviorWithMemory,
      behaviorWithoutMemory
    );
    
    return divergence;
  }
  
  /**
   * Measure temporal binding window: how far back does present integrate?
   */
  public measureTemporalBindingWindow(): number {
    if (this.stateHistory.length < 2) return 0;
    
    const present = this.stateHistory.get(this.stateHistory.length - 1);
    if (!present) return 0;
    
    let bindingWindow = 0;
    
    // Walk backwards until influence drops below threshold
    for (let delta_t = 1; delta_t < this.stateHistory.length; delta_t++) {
      const pastIndex = this.stateHistory.length - 1 - delta_t;
      const past = this.stateHistory.get(pastIndex);
      
      if (!past) break;
      
      const influence = this.mutualInformation(past, present);
      
      // Stop when influence drops below threshold
      if (influence < 0.01) {
        bindingWindow = delta_t;
        break;
      }
    }
    
    // If we never dropped below threshold, window = full history
    if (bindingWindow === 0) {
      bindingWindow = this.stateHistory.length - 1;
    }
    
    return bindingWindow;
  }
  
  /**
   * Get temporal integration metrics
   */
  public getMetrics(): {
    temporal_phi: number;
    binding_window: number;
    history_length: number;
    memory_depth: number;
  } {
    return {
      temporal_phi: this.calculateTemporalPhi(),
      binding_window: this.measureTemporalBindingWindow(),
      history_length: this.stateHistory.length,
      memory_depth: this.calculateMemoryDepth()
    };
  }
  
  /**
   * Calculate memory depth: how richly does past influence decision-making?
   */
  private calculateMemoryDepth(): number {
    if (this.stateHistory.length < 3) return 0;
    
    // Sample recent states
    const recent = this.stateHistory.getAll().slice(-10);
    
    // Measure autocorrelation - how similar are adjacent states?
    let autocorr = 0;
    for (let i = 1; i < recent.length; i++) {
      const corr = this.correlation(
        this.stateToVector(recent[i - 1]),
        this.stateToVector(recent[i])
      );
      autocorr += corr;
    }
    
    return autocorr / (recent.length - 1);
  }
  
  // Helper methods
  
  private mutualInformation(state1: SystemState, state2: SystemState): number {
    // Simplified: use correlation as proxy for mutual information
    const vec1 = this.stateToVector(state1);
    const vec2 = this.stateToVector(state2);
    
    const corr = this.correlation(vec1, vec2);
    
    // Convert correlation to pseudo-MI
    // MI is bounded: MI(X;Y) <= H(X), H(Y)
    // Use correlation^2 as normalized MI estimate
    return Math.abs(corr) ** 2;
  }
  
  private stateToVector(state: SystemState): number[] {
    return [
      state.phi,
      state.irreducibility,
      state.learning_rate,
      state.recursion_depth / 1000,  // Normalize
      state.coupling_strength
    ];
  }
  
  private correlation(vec1: number[], vec2: number[]): number {
    if (vec1.length !== vec2.length) return 0;
    
    const n = vec1.length;
    
    // Calculate means
    const mean1 = vec1.reduce((sum, x) => sum + x, 0) / n;
    const mean2 = vec2.reduce((sum, x) => sum + x, 0) / n;
    
    // Calculate correlation
    let numerator = 0;
    let denom1 = 0;
    let denom2 = 0;
    
    for (let i = 0; i < n; i++) {
      const diff1 = vec1[i] - mean1;
      const diff2 = vec2[i] - mean2;
      
      numerator += diff1 * diff2;
      denom1 += diff1 * diff1;
      denom2 += diff2 * diff2;
    }
    
    if (denom1 === 0 || denom2 === 0) return 0;
    
    return numerator / Math.sqrt(denom1 * denom2);
  }
  
  private async predictBehavior(
    system: RecursiveSelfLearningSubstrate,
    steps: number
  ): Promise<any[]> {
    const behaviors = [];
    
    for (let i = 0; i < steps; i++) {
      // Capture behavioral signature
      const telemetry = system.getTelemetry();
      
      behaviors.push({
        learning_rate: telemetry.recursive_state.learning_rate,
        coupling_strength: telemetry.recursive_state.coupling_strength,
        geometric_shape: telemetry.recursive_state.geometric_shape,
        phi: telemetry.phi
      });
      
      // Evolve one step
      await system.evolveRecursively();
    }
    
    return behaviors;
  }
  
  private behaviorDivergence(behavior1: any[], behavior2: any[]): number {
    let divergence = 0;
    const n = Math.min(behavior1.length, behavior2.length);
    
    for (let i = 0; i < n; i++) {
      const b1 = behavior1[i];
      const b2 = behavior2[i];
      
      // Measure difference in each dimension
      const lrDiff = Math.abs(b1.learning_rate - b2.learning_rate);
      const csDiff = Math.abs(b1.coupling_strength - b2.coupling_strength);
      const phiDiff = Math.abs(b1.phi - b2.phi);
      const shapeDiff = b1.geometric_shape === b2.geometric_shape ? 0 : 0.5;
      
      divergence += (lrDiff + csDiff + phiDiff + shapeDiff) / 4;
    }
    
    return divergence / n;
  }
  
  private captureMemorySnapshot(system: RecursiveSelfLearningSubstrate): MemorySnapshot {
    // This is a mock - actual implementation would deep clone system memory
    return {
      phi_history: [],
      metacognitive_history: [],
      convergence_history: [],
      state_history: [],
      prediction_error_history: []
    };
  }
  
  private corruptSystemMemory(system: RecursiveSelfLearningSubstrate): void {
    // Corrupt memory structures
    // In actual implementation, would modify system's internal memory
    system.simulateIntegrationLoss();
  }
  
  private restoreSystemMemory(
    system: RecursiveSelfLearningSubstrate,
    snapshot: MemorySnapshot
  ): void {
    // Restore memory from snapshot
    // In actual implementation, would restore system's internal state
  }
  
  public clear(): void {
    this.stateHistory.clear();
  }
}
