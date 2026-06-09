/**
 * Type Definitions for Quantum ASIC Annihilation
 */

export interface MiningState {
  blockHeight: number;
  prevHash: string;
  merkleRoot: string;
  timestamp: number;
  difficultyTarget: string; // Hex representation
  networkDifficulty: number; // Numeric value
  currentHashrate: number; // PH/s equivalent or arbitrary relative unit
  powerConsumption: number; // Watts
  activePool: string;
  powerScale: number;
}

export interface QuantumDimensionState {
  index: number;
  amplitudeReal: number;
  amplitudeImag: number;
  phase: number;
  probability: number;
}

export interface OptimizationParams {
  increaseIntensity: boolean;
  quantumIterations: number;
  resonanceRadius: number;
  optimalPowerAdjustment: number;
  confidenceScore: number;
  expectedImprovement: number;
  quantumSpeedupRatio: number; // Pure O(√I) speedup metrics
}

export interface SimulationStep {
  step: number;
  operation: string;
  markedStateIndex: number;
  solutionProbability: number;
  entropy: number;
  amplitudes: number[]; // Main amplitude magnitudes
}

export interface TestResultItem {
  id: string;
  name: string;
  description: string;
  passed: boolean;
  proofName: string;
  proofSteps: string[];
  computationLogs: string[];
  executionTimeMs: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "model" | "system";
  content: string;
  timestamp: string;
  groundingUrls?: string[];
}
