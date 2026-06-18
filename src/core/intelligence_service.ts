/**
 * HYBA_INTELLIGENCE_SERVICE
 * Service layer for the emergent intelligence system
 * Manages the intelligence substrate lifecycle and provides API interface
 */

import { EmergentIntelligenceSubstrate } from "./emergent_intelligence";
import { IntelligenceTelemetry } from "./intelligence_types";

export class IntelligenceService {
  private static instance: IntelligenceService;
  private substrate: EmergentIntelligenceSubstrate;
  private isRunning: boolean = false;
  private pulseInterval: NodeJS.Timeout | null = null;
  private readonly PULSE_INTERVAL_MS = 100; // 10Hz "consciousness" cycle

  private constructor(poolSize: number = 2048) {
    this.substrate = new EmergentIntelligenceSubstrate(poolSize);
  }

  /**
   * Get singleton instance
   */
  public static getInstance(poolSize?: number): IntelligenceService {
    if (!IntelligenceService.instance) {
      IntelligenceService.instance = new IntelligenceService(poolSize || 2048);
    }
    return IntelligenceService.instance;
  }

  /**
   * Start the autopoietic pulse
   */
  public start(): void {
    if (this.isRunning) {
      console.warn("[IntelligenceService] Already running");
      return;
    }

    this.isRunning = true;
    console.log("[IntelligenceService] Starting autopoietic pulse...");

    this.pulseInterval = setInterval(async () => {
      try {
        await this.substrate.processAutopoieticPulse();

        const telemetry = this.getTelemetry();
        if (telemetry.mode !== "NOMINAL") {
          console.warn(
            `[IntelligenceService] System in ${telemetry.mode} mode. Phi: ${telemetry.phi_integrated.toFixed(4)}`,
          );
        }
      } catch (error) {
        console.error("[IntelligenceService] Autopoietic pulse failure:", error);
        // Emergency recovery
        this.substrate["handleAnomaly"](0xdeadbeef);
      }
    }, this.PULSE_INTERVAL_MS);
  }

  /**
   * Stop the autopoietic pulse
   */
  public stop(): void {
    if (!this.isRunning) {
      return;
    }

    this.isRunning = false;
    if (this.pulseInterval) {
      clearInterval(this.pulseInterval);
      this.pulseInterval = null;
    }

    console.log("[IntelligenceService] Stopping autopoietic pulse...");
  }

  /**
   * Get current telemetry
   */
  public getTelemetry(): IntelligenceTelemetry {
    return this.substrate.getTelemetry();
  }

  /**
   * Get current Phi value
   */
  public getPhi(): number {
    return this.substrate.getPhi();
  }

  /**
   * Get current goal state
   */
  public getCurrentGoal(): string {
    return this.substrate.getCurrentGoal();
  }

  /**
   * Simulate external disturbance
   */
  public simulateDisturbance(syndrome: number): void {
    this.substrate.simulateIntrusion(syndrome, { phi: 0.7, confidence: 0.8 });
  }

  /**
   * Get Hebbian learner statistics
   */
  public getHebbianStats(): {
    strategyCount: number;
    topStrategies: any[];
    stability: number;
  } {
    const learner = this.substrate.getHebbianLearner();
    return {
      strategyCount: learner.getStrategyCount(),
      topStrategies: learner.getTopStrategies(5),
      stability: learner.getLearningStability(),
    };
  }

  /**
   * Reset the intelligence system
   */
  public reset(): void {
    this.substrate.reset();
    console.log("[IntelligenceService] System reset");
  }

  /**
   * Export system state
   */
  public exportState(): any {
    return this.substrate.exportState();
  }

  /**
   * Check if system is running
   */
  public isActive(): boolean {
    return this.isRunning;
  }
}
