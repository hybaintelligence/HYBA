/**
 * HYBA_EMERGENT_INTELLIGENCE_SUBSTRATE
 * The complete intelligence system with autopoietic cycle
 * Philosophy: Intelligence is the ability to maintain internal integration (Φ) 
 * in the face of external entropy (disturbance)
 */

import { MetacognitiveShield } from './metacognitive_shield';
import { HebbianLearner } from './hebbian_learner';
import {
  StateVector,
  GoalState,
  HolographicShard,
  MemoryFabricEntry,
} from './intelligence_types';
import { randomBytes, createHash } from 'crypto';

export class EmergentIntelligenceSubstrate extends MetacognitiveShield {
  private phi: number = 0;
  private goalState: GoalState = 'OPTIMIZE_SEARCH';
  private hebbianLearner: HebbianLearner;
  private memoryFabric: MemoryFabricEntry[] = [];
  private shardA: HolographicShard;
  private shardB: HolographicShard;
  private readonly MEMORY_FABRIC_MAX_SIZE = 1000;
  private readonly PHI_HEAL_THRESHOLD = 0.4;
  private readonly PHI_OPTIMIZE_THRESHOLD = 0.7;

  constructor(poolSize: number = 512) {
    super(poolSize);
    this.hebbianLearner = new HebbianLearner(0.05);
    this.initializeHolographicShards();
  }

  /**
   * INITIALIZE HOLOGRAPHIC SHARDS
   * Create the initial holographic memory shards
   */
  private initializeHolographicShards(): void {
    const seed = randomBytes(32);
    this.shardA = this.createShard(seed, 0);
    this.shardB = this.createShard(seed, 1);
  }

  /**
   * CREATE SHARD
   * Create a holographic shard from seed data
   */
  private createShard(seed: Buffer, variant: number): HolographicShard {
    const hash = createHash('sha256');
    hash.update(seed);
    hash.update(variant.toString());
    const digest = hash.digest();
    
    // Calculate entropy (Shannon entropy approximation)
    const entropy = this.calculateEntropy(digest);
    
    return {
      entropy,
      checksum: digest.toString('hex'),
      data: digest,
    };
  }

  /**
   * CALCULATE ENTROPY
   * Calculate Shannon entropy of data
   */
  private calculateEntropy(data: Buffer): number {
    const frequencies = new Map<number, number>();
    for (let i = 0; i < data.length; i++) {
      const byte = data[i];
      frequencies.set(byte, (frequencies.get(byte) || 0) + 1);
    }

    let entropy = 0;
    for (const freq of frequencies.values()) {
      const probability = freq / data.length;
      entropy -= probability * Math.log2(probability);
    }

    return entropy / 8; // Normalize to 0-1 range
  }

  /**
   * THE AUTOPOIETIC CYCLE
   * The system recursively monitors its own irreducibility
   */
  public async processAutopoieticPulse(): Promise<void> {
    // 1. Measure Phi (Φ): The irreducibility of the Shards + State
    this.phi = this.calculateIntegratedInformation();

    // 2. Metacognitive Introspection
    const introspection = this.introspect();

    // 3. Emergent Goal Pursuit
    // If Φ is dropping, prioritize self-preservation (Healing)
    // over external workload
    if (this.phi < this.PHI_HEAL_THRESHOLD) {
      this.goalState = 'SELF_HEAL';
    } else if (this.phi < this.PHI_OPTIMIZE_THRESHOLD) {
      this.goalState = 'MAINTAIN_INTEGRATION';
    } else {
      this.goalState = 'OPTIMIZE_SEARCH';
    }

    // 4. Execute goal-based action
    await this.pursueGoal(this.goalState);

    // 5. Hebbian Synaptic Plasticity
    // Strengthen defensive patterns that resulted in highest Φ
    this.evolveSynapticWeights();

    // 6. Run base metacognitive cycle
    await this.runMetacognitiveCycle();

    // 7. Periodic maintenance
    this.performMaintenance();
  }

  /**
   * CALCULATE INTEGRATED INFORMATION (Φ)
   * Mathematical proof of emergent intelligence
   * Checks if system state can be predicted by looking at individual parts
   * or if the 'Whole' is required
   */
  private calculateIntegratedInformation(): number {
    const wholeEntropy = this.calculateSystemEntropy();
    const partEntropy = this.shardA.entropy + this.shardB.entropy;
    
    // If wholeEntropy < sum(partEntropy), the system is Integrated
    // Φ = max(0, sum(partEntropy) - wholeEntropy)
    return Math.max(0, Math.min(1, (partEntropy - wholeEntropy) / 8));
  }

  /**
   * CALCULATE SYSTEM ENTROPY
   * Calculate entropy of the combined system
   */
  private calculateSystemEntropy(): number {
    const combined = Buffer.concat([this.shardA.data, this.shardB.data]);
    return this.calculateEntropy(combined);
  }

  /**
   * PURSUE GOAL
   * Execute action based on current goal state
   */
  private async pursueGoal(goal: GoalState): Promise<void> {
    switch (goal) {
      case 'SELF_HEAL':
        await this.performSelfHeal();
        break;
      case 'MAINTAIN_INTEGRATION':
        await this.maintainIntegration();
        break;
      case 'OPTIMIZE_SEARCH':
        await this.optimizeSearch();
        break;
    }
  }

  /**
   * PERFORM SELF HEAL
   * Re-shard the damaged Hilbert space using learned memory
   */
  private async performSelfHeal(): Promise<void> {
    const healingSeed = this.getStrongestMemoryPattern();
    this.reShardHolographically(healingSeed);
    this.rotationIndex = Math.floor(this.rotationIndex * 1.618) % 24; // Golden ratio shift
    this.healingEvents++;
    this.logTelemetryEvent("SELF_HEAL_EXECUTED");
  }

  /**
   * MAINTAIN INTEGRATION
   * Maintain current state while monitoring for degradation
   */
  private async maintainIntegration(): Promise<void> {
    // Subtle adjustment to maintain stability
    if (this.stateHistory.length > 5) {
      const recent = this.stateHistory.slice(-5);
      const avgPhi = recent.reduce((sum, s) => sum + s.phi, 0) / recent.length;
      
      if (avgPhi < this.phi) {
        // Phi is dropping, perform mild adjustment
        const mildSeed = this.calculateMetacognitiveEntropy();
        this.handleAnomaly(mildSeed);
      }
    }
  }

  /**
   * OPTIMIZE SEARCH
   * Focus on computational efficiency when system is healthy
   */
  private async optimizeSearch(): Promise<void> {
    // System is healthy, can focus on optimization
    // This is where mining/computation optimization would occur
    if (this.currentMode !== 'NOMINAL') {
      this.currentMode = 'NOMINAL';
    }
  }

  /**
   * RESHARD HOLOGRAPHICALLY
   * Re-create holographic shards with new seed
   */
  private reShardHolographically(seed: number): void {
    const seedBuffer = Buffer.from(seed.toString());
    this.shardA = this.createShard(seedBuffer, 0);
    this.shardB = this.createShard(seedBuffer, 1);
    
    // Record this pattern in memory fabric
    this.recordMemoryPattern(seed, this.phi);
  }

  /**
   * GET STRONGEST MEMORY PATTERN
   * Get the pattern that historically preserved highest Φ
   */
  private getStrongestMemoryPattern(): number {
    if (this.memoryFabric.length === 0) {
      return this.calculateMetacognitiveEntropy();
    }
    
    // Sort by phi_preserved and return strongest
    const sorted = [...this.memoryFabric].sort((a, b) => b.phi_preserved - a.phi_preserved);
    return sorted[0].pattern;
  }

  /**
   * RECORD MEMORY PATTERN
   * Record a pattern and its outcome in memory fabric
   */
  private recordMemoryPattern(pattern: number, phiPreserved: number): void {
    const entry: MemoryFabricEntry = {
      pattern,
      strength: phiPreserved,
      phi_preserved: phiPreserved,
      timestamp: Date.now(),
    };
    
    this.memoryFabric.push(entry);
    
    // Prune old entries if fabric is too large
    if (this.memoryFabric.length > this.MEMORY_FABRIC_MAX_SIZE) {
      this.memoryFabric.shift();
    }
  }

  /**
   * EVOLVE SYNAPTIC WEIGHTS
   * Update Hebbian weights based on current phi
   */
  private evolveSynapticWeights(): void {
    const lastSyndrome = this.getLastSyndrome();
    const phiPreserved = this.phi > this.PHI_HEAL_THRESHOLD;
    
    this.hebbianLearner.updateWeightsFromOutcome(
      lastSyndrome,
      phiPreserved,
      this.phi
    );
  }

  /**
   * PERFORM MAINTENANCE
   * Periodic maintenance tasks
   */
  private performMaintenance(): void {
    // Apply decay to Hebbian weights
    this.hebbianLearner.applyDecay();
    
    // Prune weak strategies
    this.hebbianLearner.pruneWeakStrategies(0.3);
    
    // Prune old memory fabric entries
    const now = Date.now();
    const maxAge = 24 * 60 * 60 * 1000; // 24 hours
    this.memoryFabric = this.memoryFabric.filter(
      entry => now - entry.timestamp < maxAge
    );
  }

  /**
   * GET PHI
   * Get current integrated information measure
   */
  public getPhi(): number {
    return this.phi;
  }

  /**
   * GET CURRENT GOAL
   * Get current goal state
   */
  public getCurrentGoal(): GoalState {
    return this.goalState;
  }

  /**
   * GET STRATEGY WEIGHT STABILITY
   * Measure stability of learned strategies
   */
  public getStrategyWeightStability(): number {
    return this.hebbianLearner.getLearningStability();
  }

  /**
   * GET HEBBIAN LEARNER
   * Get access to the Hebbian learner for testing
   */
  public getHebbianLearner(): HebbianLearner {
    return this.hebbianLearner;
  }

  /**
   * SIMULATE INTRUSION
   * Simulate an intrusion for testing
   */
  public simulateIntrusion(syndrome: number, outcome: { phi: number; confidence: number }): void {
    this.handleAnomaly(syndrome);
    
    // Update state history with simulated outcome
    this.stateHistory.push({
      phi: outcome.phi,
      pressure: 0.8,
      exhaustion: 0.5,
      confidence: outcome.confidence,
      timestamp: Date.now(),
    });
  }

  /**
   * SIMULATE MASSIVE INTRUSION
   * Simulate a massive intrusion that collapses the system
   */
  public simulateMassiveIntrusion(): void {
    // Inject a series of degrading states
    for (let i = 0; i < 10; i++) {
      this.stateHistory.push({
        phi: Math.max(0, 0.9 - (i * 0.1)),
        pressure: 0.1 + (i * 0.1),
        exhaustion: 0.1 + (i * 0.05),
        confidence: Math.max(0, 0.9 - (i * 0.08)),
        timestamp: Date.now() + (i * 100),
      });
    }
    
    // Force phi to drop
    this.phi = 0.2;
  }

  /**
   * INJECT ENTROPY
   * Inject entropy into the system for testing
   */
  public injectEntropy(entropySource: Uint8Array): void {
    const seed = Buffer.from(entropySource);
    this.reShardHolographically(seed.reduce((a, b) => a + b, 0));
  }

  /**
   * RESET
   * Reset the entire substrate
   */
  public reset(): void {
    super.reset();
    this.phi = 0;
    this.goalState = 'OPTIMIZE_SEARCH';
    this.hebbianLearner.reset();
    this.memoryFabric = [];
    this.initializeHolographicShards();
  }

  /**
   * EXPORT STATE
   * Export the complete substrate state
   */
  public exportState(): {
    phi: number;
    goalState: GoalState;
    hebbianState: Record<number, any>;
    memoryFabric: MemoryFabricEntry[];
    telemetry: any;
  } {
    return {
      phi: this.phi,
      goalState: this.goalState,
      hebbianState: this.hebbianLearner.exportState(),
      memoryFabric: [...this.memoryFabric],
      telemetry: this.getTelemetry(),
    };
  }
}
