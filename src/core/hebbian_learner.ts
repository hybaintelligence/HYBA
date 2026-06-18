/**
 * HYBA_HEBBIAN_LEARNER
 * Hebbian learning system for strategy optimization
 * Strengthens patterns that successfully preserve system integrity
 */

import { StrategyWeight } from "./intelligence_types";

export class HebbianLearner {
  private strategyWeights: Map<number, StrategyWeight> = new Map();
  private learningRate: number = 0.05;
  private decayRate: number = 0.001;
  private minWeight: number = 0.1;
  private maxWeight: number = 10.0;

  constructor(learningRate: number = 0.05) {
    this.learningRate = learningRate;
  }

  /**
   * UPDATE WEIGHTS FROM OUTCOME
   * Reinforcement learning based on phi preservation
   */
  public updateWeightsFromOutcome(syndrome: number, phiPreserved: boolean, phiValue: number): void {
    const currentWeight = this.strategyWeights.get(syndrome) || {
      syndrome,
      weight: 1.0,
      success_count: 0,
      failure_count: 0,
      last_updated: Date.now(),
    };

    // Reward function: Higher phi = stronger reinforcement
    const phiBonus = phiValue * 0.2; // Bonus for high phi
    const reward = phiPreserved ? 1 + this.learningRate + phiBonus : 1 - this.learningRate;

    currentWeight.weight = Math.max(
      this.minWeight,
      Math.min(this.maxWeight, currentWeight.weight * reward),
    );
    currentWeight.last_updated = Date.now();

    if (phiPreserved) {
      currentWeight.success_count++;
    } else {
      currentWeight.failure_count++;
    }

    this.strategyWeights.set(syndrome, currentWeight);
  }

  /**
   * GET OPTIMIZED STRATEGY
   * Get the best strategy for a given syndrome based on learned weights
   */
  public getOptimizedStrategy(syndrome: number): number {
    const learnedWeight = this.strategyWeights.get(syndrome);
    const baseWeight = learnedWeight ? learnedWeight.weight : 1.0;

    // Apply learned bias to the syndrome
    return this.deriveDeterministicStrategy(syndrome * baseWeight);
  }

  /**
   * DERIVE DETERMINISTIC STRATEGY
   * Derive a deterministic strategy from a seed value
   */
  private deriveDeterministicStrategy(seed: number): number {
    // Use golden ratio for deterministic but pseudo-random distribution
    const goldenRatio = 1.618033988749895;
    const normalizedSeed = Math.abs(seed) % 1000;
    return Math.floor((normalizedSeed * goldenRatio) % 24);
  }

  /**
   * GET STRATEGY WEIGHT
   * Get the current weight for a specific syndrome
   */
  public getStrategyWeight(syndrome: number): number {
    const weight = this.strategyWeights.get(syndrome);
    return weight ? weight.weight : 1.0;
  }

  /**
   * GET STRATEGY STATS
   * Get detailed statistics for a strategy
   */
  public getStrategyStats(syndrome: number): StrategyWeight | null {
    return this.strategyWeights.get(syndrome) || null;
  }

  /**
   * APPLY DECAY
   * Apply exponential decay to all weights to prevent unbounded growth
   */
  public applyDecay(): void {
    for (const [syndrome, weight] of this.strategyWeights) {
      weight.weight = Math.max(this.minWeight, weight.weight * (1 - this.decayRate));
      weight.last_updated = Date.now();
      this.strategyWeights.set(syndrome, weight);
    }
  }

  /**
   * PRUNE WEAK STRATEGIES
   * Remove strategies that have consistently failed
   */
  public pruneWeakStrategies(threshold: number = 0.5): void {
    for (const [syndrome, weight] of this.strategyWeights) {
      const totalAttempts = weight.success_count + weight.failure_count;
      if (totalAttempts > 10 && weight.weight < threshold) {
        this.strategyWeights.delete(syndrome);
      }
    }
  }

  /**
   * GET TOP STRATEGIES
   * Get the most successful strategies
   */
  public getTopStrategies(limit: number = 10): StrategyWeight[] {
    const strategies = Array.from(this.strategyWeights.values());
    return strategies.sort((a, b) => b.weight - a.weight).slice(0, limit);
  }

  /**
   * GET LEARNING STABILITY
   * Measure how stable the learned weights are
   */
  public getLearningStability(): number {
    const weights = Array.from(this.strategyWeights.values());
    if (weights.length === 0) return 1.0;

    const mean = weights.reduce((sum, w) => sum + w.weight, 0) / weights.length;
    const variance =
      weights.reduce((sum, w) => sum + Math.pow(w.weight - mean, 2), 0) / weights.length;
    const stdDev = Math.sqrt(variance);

    // Lower coefficient of variation = higher stability
    const cv = stdDev / mean;
    return Math.max(0, 1 - cv);
  }

  /**
   * RESET
   * Reset all learned weights
   */
  public reset(): void {
    this.strategyWeights.clear();
  }

  /**
   * EXPORT STATE
   * Export the current learning state
   */
  public exportState(): Record<number, StrategyWeight> {
    const state: Record<number, StrategyWeight> = {};
    for (const [syndrome, weight] of this.strategyWeights) {
      state[syndrome] = { ...weight };
    }
    return state;
  }

  /**
   * IMPORT STATE
   * Import a previously exported learning state
   */
  public importState(state: Record<number, StrategyWeight>): void {
    this.strategyWeights.clear();
    for (const [syndrome, weight] of Object.entries(state)) {
      this.strategyWeights.set(parseInt(syndrome), { ...weight });
    }
  }

  /**
   * GET STRATEGY COUNT
   * Get the number of learned strategies
   */
  public getStrategyCount(): number {
    return this.strategyWeights.size;
  }
}
