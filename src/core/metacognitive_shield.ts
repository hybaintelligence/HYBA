/**
 * HYBA_METACOGNITIVE_SHIELD
 * Base class for the metacognitive intelligence system
 * Provides state capture, prediction, and introspection capabilities
 */

import { createHash, randomBytes } from 'crypto';
import {
  StateVector,
  IntrospectionReport,
  StrategyWeight,
  IntelligenceTelemetry,
} from './intelligence_types';

const PHI_THRESHOLD = 0.6;
const PRESSURE_LIMIT = 0.7;
const MAX_HISTORY_LENGTH = 100;
const LEARNING_RATE = 0.05;

export class MetacognitiveShield {
  protected stateHistory: StateVector[] = [];
  protected strategyWeights: Map<number, StrategyWeight> = new Map();
  protected predictionAccuracy: number = 1.0;
  protected telemetryEvents: string[] = [];
  protected healingEvents: number = 0;
  protected currentMode: 'NOMINAL' | 'COMPRESSED' | 'RECOVERY' = 'NOMINAL';
  
  // Resource pool management
  protected poolSize: number;
  protected activeAncillas: number = 0;
  protected rotationIndex: number = 0;
  
  constructor(poolSize: number = 512) {
    this.poolSize = poolSize;
  }

  /**
   * CAPTURE STATE VECTOR
   * Captures current system state for metacognitive analysis
   */
  protected captureStateVector(): StateVector {
    const exhaustion = this.activeAncillas / this.poolSize;
    const confidence = this.calculateConfidence();
    const pressure = this.calculateSyndromePressure();
    
    return {
      phi: this.calculatePhi(),
      pressure,
      exhaustion,
      confidence,
      timestamp: Date.now(),
    };
  }

  /**
   * INTROSPECTION LOOP
   * System reflects on its own understanding of disturbances
   */
  public introspect(): IntrospectionReport {
    const currentState = this.captureStateVector();
    const predictedState = this.predictNextState();
    
    // Measure "Self-Awareness": How well did we predict the state?
    const accuracy = this.calculatePredictionAccuracy(predictedState, currentState);
    this.predictionAccuracy = (this.predictionAccuracy * 0.9) + (accuracy * 0.1);

    const predictionError = Math.abs(predictedState.phi - currentState.phi);
    const isPredictingDisturbance = predictedState.pressure > PRESSURE_LIMIT || predictedState.phi < PHI_THRESHOLD;

    return {
      self_awareness: this.predictionAccuracy,
      metacognitive_depth: this.stateHistory.length,
      is_predicting_disturbance: isPredictingDisturbance,
      prediction_error: predictionError,
    };
  }

  /**
   * PREDICT NEXT STATE
   * Linear regression over history to find trends
   */
  protected predictNextState(): StateVector {
    if (this.stateHistory.length < 2) {
      return this.captureStateVector();
    }

    const recent = this.stateHistory.slice(-10);
    const n = recent.length;
    
    // Simple linear regression for phi trend
    let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0;
    for (let i = 0; i < n; i++) {
      sumX += i;
      sumY += recent[i].phi;
      sumXY += i * recent[i].phi;
      sumX2 += i * i;
    }
    
    const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;
    
    const predictedPhi = slope * n + intercept;
    
    // Similar regression for pressure
    sumX = 0; sumY = 0; sumXY = 0; sumX2 = 0;
    for (let i = 0; i < n; i++) {
      sumX += i;
      sumY += recent[i].pressure;
      sumXY += i * recent[i].pressure;
      sumX2 += i * i;
    }
    
    const pressureSlope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
    const pressureIntercept = (sumY - pressureSlope * sumX) / n;
    const predictedPressure = Math.max(0, Math.min(1, pressureSlope * n + pressureIntercept));

    const lastState = recent[recent.length - 1];
    
    return {
      phi: Math.max(0, Math.min(1, predictedPhi)),
      pressure: predictedPressure,
      exhaustion: Math.min(1, lastState.exhaustion + 0.01),
      confidence: lastState.confidence,
      timestamp: Date.now(),
    };
  }

  /**
   * CALCULATE PREDICTION ACCURACY
   * Measures how well the system predicted the current state
   */
  protected calculatePredictionAccuracy(predicted: StateVector, actual: StateVector): number {
    const phiError = Math.abs(predicted.phi - actual.phi);
    const pressureError = Math.abs(predicted.pressure - actual.pressure);
    
    // Combined error metric (lower is better)
    const totalError = (phiError + pressureError) / 2;
    
    // Convert to accuracy (0-1)
    return Math.max(0, 1 - totalError);
  }

  /**
   * RUN METACOGNITIVE CYCLE
   * Main intelligence loop: introspect, predict, and act
   */
  public async runMetacognitiveCycle(): Promise<void> {
    const current = this.captureStateVector();
    const predicted = this.predictNextState();
    const report = this.introspect();

    // Update state history
    this.stateHistory.push(current);
    if (this.stateHistory.length > MAX_HISTORY_LENGTH) {
      this.stateHistory.shift();
    }

    // Preemptive action if degradation predicted
    if (predicted.phi < PHI_THRESHOLD || predicted.pressure > PRESSURE_LIMIT) {
      this.triggerPreemptiveShift(predicted);
    }

    // Hebbian update based on outcome
    this.reinforceSuccessfulPatterns(current, report);

    // Adjust mode based on system state
    this.adjustMode(current);
  }

  /**
   * TRIGGER PREEMPTIVE SHIFT
   * Move the system state before disturbance occurs
   */
  protected triggerPreemptiveShift(prediction: StateVector): void {
    const preemptiveSeed = this.calculateMetacognitiveEntropy();
    this.handleAnomaly(preemptiveSeed);
    this.logTelemetryEvent("PREEMPTIVE_SHIFT_EXECUTED");
  }

  /**
   * HANDLE ANOMALY
   * Process a disturbance/syndrome
   */
  protected handleAnomaly(seed: number): void {
    // Derive deterministic rotation from seed
    this.rotationIndex = (this.rotationIndex + seed) % 24;
    
    // Update ancilla usage
    this.activeAncillas = Math.min(this.poolSize, this.activeAncillas + 1);
  }

  /**
   * REINFORCE SUCCESSFUL PATTERNS
   * Hebbian learning: strengthen patterns that preserved phi
   */
  protected reinforceSuccessfulPatterns(state: StateVector, report: IntrospectionReport): void {
    const lastSyndrome = this.getLastSyndrome();
    const currentWeight = this.strategyWeights.get(lastSyndrome) || {
      syndrome: lastSyndrome,
      weight: 1.0,
      success_count: 0,
      failure_count: 0,
      last_updated: Date.now(),
    };

    // Reward function: High Phi + High Confidence = Success
    const success = (state.phi * state.confidence) > 0.8;
    const multiplier = success ? (1 + LEARNING_RATE) : (1 - LEARNING_RATE);
    
    currentWeight.weight = currentWeight.weight * multiplier;
    currentWeight.last_updated = Date.now();
    
    if (success) {
      currentWeight.success_count++;
    } else {
      currentWeight.failure_count++;
    }
    
    this.strategyWeights.set(lastSyndrome, currentWeight);
  }

  /**
   * ADJUST MODE
   * Switch between NOMINAL, COMPRESSED, and RECOVERY modes
   */
  protected adjustMode(state: StateVector): void {
    if (state.phi < 0.3) {
      this.currentMode = 'RECOVERY';
    } else if (state.phi < 0.6 || state.exhaustion > 0.8) {
      this.currentMode = 'COMPRESSED';
    } else {
      this.currentMode = 'NOMINAL';
    }
  }

  /**
   * CALCULATE PHI
   * Integrated Information measure (placeholder for now)
   */
  protected calculatePhi(): number {
    if (this.stateHistory.length < 2) return 0.8;
    
    const recent = this.stateHistory.slice(-5);
    const avgPhi = recent.reduce((sum, s) => sum + s.phi, 0) / recent.length;
    const variance = recent.reduce((sum, s) => sum + Math.pow(s.phi - avgPhi, 2), 0) / recent.length;
    
    // Higher stability = higher phi
    return Math.max(0, Math.min(1, avgPhi - variance));
  }

  /**
   * CALCULATE CONFIDENCE
   * System confidence in current state
   */
  protected calculateConfidence(): number {
    if (this.stateHistory.length === 0) return 0.5;
    
    const recent = this.stateHistory.slice(-10);
    const avgPressure = recent.reduce((sum, s) => sum + s.pressure, 0) / recent.length;
    
    return Math.max(0, Math.min(1, 1 - avgPressure));
  }

  /**
   * CALCULATE SYNDROME PRESSURE
   * Rate of disturbances in the system
   */
  protected calculateSyndromePressure(): number {
    if (this.stateHistory.length < 2) return 0.1;
    
    const recent = this.stateHistory.slice(-5);
    const pressureTrend = recent[recent.length - 1].pressure - recent[0].pressure;
    
    return Math.max(0, Math.min(1, 0.1 + pressureTrend));
  }

  /**
   * CALCULATE METACOGNITIVE ENTROPY
   * Derive entropy seed from prediction error
   */
  protected calculateMetacognitiveEntropy(): number {
    const hash = createHash('sha256');
    hash.update(Date.now().toString());
    hash.update(this.predictionAccuracy.toString());
    hash.update(this.rotationIndex.toString());
    const digest = hash.digest('hex');
    
    // Convert first 8 chars to number
    return parseInt(digest.substring(0, 8), 16);
  }

  /**
   * GET LAST SYNDROME
   * Get the most recent disturbance pattern
   */
  protected getLastSyndrome(): number {
    return this.rotationIndex;
  }

  /**
   * LOG TELEMETRY EVENT
   */
  protected logTelemetryEvent(event: string): void {
    this.telemetryEvents.push(event);
    if (this.telemetryEvents.length > 50) {
      this.telemetryEvents.shift();
    }
  }

  /**
   * GET TELEMETRY
   * Get current system telemetry
   */
  public getTelemetry(): IntelligenceTelemetry {
    const currentState = this.captureStateVector();
    
    return {
      phi_integrated: currentState.phi,
      self_awareness: this.predictionAccuracy,
      prediction_accuracy: this.predictionAccuracy,
      syndrome_pressure: currentState.pressure,
      rotation_index: this.rotationIndex,
      active_ancillas: this.activeAncillas,
      pool_max: this.poolSize,
      exhaustion: currentState.exhaustion,
      mode: this.currentMode,
      metacognitive_events: [...this.telemetryEvents],
      healing_events: this.healingEvents,
    };
  }

  /**
   * GET STRATEGY WEIGHT
   * Get the learned weight for a specific syndrome
   */
  public getStrategyWeight(syndrome: number): number {
    const weight = this.strategyWeights.get(syndrome);
    return weight ? weight.weight : 1.0;
  }

  /**
   * INJECT STATE HISTORY
   * For testing: inject a predefined state history
   */
  public injectStateHistory(history: StateVector[]): void {
    this.stateHistory = [...history];
  }

  /**
   * RESET
   * Reset the intelligence system
   */
  public reset(): void {
    this.stateHistory = [];
    this.strategyWeights.clear();
    this.predictionAccuracy = 1.0;
    this.telemetryEvents = [];
    this.healingEvents = 0;
    this.currentMode = 'NOMINAL';
    this.activeAncillas = 0;
    this.rotationIndex = 0;
  }
}
