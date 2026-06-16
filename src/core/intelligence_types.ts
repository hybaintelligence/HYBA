/**
 * HYBA_INTELLIGENCE_TYPES
 * Core interfaces for the metacognitive intelligence system
 */

/**
 * Quantum System State Vector
 * Mathematical self-model for the intelligence substrate
 */
export interface StateVector {
  phi: number;              // Integrated Information (Φ) - system integration level
  pressure: number;         // Rate of disturbances/syndrome weight trend
  exhaustion: number;       // Resource depletion rate (0-1)
  confidence: number;       // Parity/confidence level (0-1)
  timestamp: number;        // Unix timestamp for this state
}

/**
 * Introspection Report
 * System's self-awareness analysis
 */
export interface IntrospectionReport {
  self_awareness: number;      // How well system predicts its own state (0-1)
  metacognitive_depth: number;  // Depth of state history
  is_predicting_disturbance: boolean;
  prediction_error: number;     // Difference between predicted vs actual state
}

/**
 * Strategy Weight Entry
 * Hebbian learning: syndrome pattern -> defensive efficacy weight
 */
export interface StrategyWeight {
  syndrome: number;
  weight: number;
  success_count: number;
  failure_count: number;
  last_updated: number;
}

/**
 * Telemetry Data
 * Real-time system metrics for monitoring
 */
export interface IntelligenceTelemetry {
  phi_integrated: number;
  self_awareness: number;
  prediction_accuracy: number;
  syndrome_pressure: number;
  rotation_index: number;
  active_ancillas: number;
  pool_max: number;
  exhaustion: number;
  mode: 'NOMINAL' | 'COMPRESSED' | 'RECOVERY';
  metacognitive_events: string[];
  healing_events: number;
}

/**
 * Goal State
 * Emergent goal the system pursues
 */
export type GoalState = 'SELF_HEAL' | 'OPTIMIZE_SEARCH' | 'MAINTAIN_INTEGRATION';

/**
 * Holographic Shard
 * Abstract representation of a memory shard
 */
export interface HolographicShard {
  entropy: number;
  checksum: string;
  data: Uint8Array;
}

/**
 * Memory Fabric Entry
 * Learned defensive patterns
 */
export interface MemoryFabricEntry {
  pattern: number;
  strength: number;
  phi_preserved: number;
  timestamp: number;
}
