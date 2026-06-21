/**
 * HYBA_INTELLIGENCE_SERVICE
 * Service layer for the emergent intelligence system
 * Manages the intelligence substrate lifecycle and provides API interface
 */

import { EmergentIntelligenceSubstrate } from "./emergent_intelligence";
import { IntelligenceTelemetry } from "./intelligence_types";
import { classifyError, logError, HybaError, ErrorCategory, ErrorSeverity } from "../utils/errorHandler";

export class IntelligenceService {
  private static instance: IntelligenceService;
  private substrate: EmergentIntelligenceSubstrate;
  private isRunning: boolean = false;
  private pulseInterval: NodeJS.Timeout | null = null;
  private readonly PULSE_INTERVAL_MS = 100; // 10Hz "consciousness" cycle
  private errorCount: number = 0;
  private readonly MAX_ERRORS_BEFORE_STOP = 10;

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
    this.errorCount = 0;
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
        
        // Reset error count on successful pulse
        this.errorCount = 0;
      } catch (error) {
        this.errorCount++;
        const classifiedError = classifyError(error);
        logError(classifiedError, {
          component: 'IntelligenceService',
          errorCount: this.errorCount,
          maxErrors: this.MAX_ERRORS_BEFORE_STOP
        });
        
        console.error("[IntelligenceService] Autopoietic pulse failure:", error);
        
        // Emergency recovery
        try {
          this.substrate["handleAnomaly"](0xdeadbeef);
        } catch (recoveryError) {
          console.error("[IntelligenceService] Emergency recovery failed:", recoveryError);
        }
        
        // Stop service if too many consecutive errors
        if (this.errorCount >= this.MAX_ERRORS_BEFORE_STOP) {
          console.error("[IntelligenceService] Too many consecutive errors, stopping service");
          this.stop();
          throw new HybaError(
            `Intelligence service stopped after ${this.errorCount} consecutive errors`,
            ErrorCategory.INTERNAL,
            ErrorSeverity.HIGH,
            { context: { errorCount: this.errorCount, originalError: classifiedError.message } }
          );
        }
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
    try {
      return this.substrate.getTelemetry();
    } catch (error) {
      const classifiedError = classifyError(error);
      logError(classifiedError, { component: 'IntelligenceService', operation: 'getTelemetry' });
      throw classifiedError;
    }
  }

  /**
   * Get current Phi value
   */
  public getPhi(): number {
    try {
      return this.substrate.getPhi();
    } catch (error) {
      const classifiedError = classifyError(error);
      logError(classifiedError, { component: 'IntelligenceService', operation: 'getPhi' });
      throw classifiedError;
    }
  }

  /**
   * Get current goal state
   */
  public getCurrentGoal(): string {
    try {
      return this.substrate.getCurrentGoal();
    } catch (error) {
      const classifiedError = classifyError(error);
      logError(classifiedError, { component: 'IntelligenceService', operation: 'getCurrentGoal' });
      throw classifiedError;
    }
  }

  /**
   * Simulate external disturbance
   */
  public simulateDisturbance(syndrome: number): void {
    try {
      this.substrate.simulateIntrusion(syndrome, { phi: 0.7, confidence: 0.8 });
    } catch (error) {
      const classifiedError = classifyError(error);
      logError(classifiedError, { component: 'IntelligenceService', operation: 'simulateDisturbance', context: { syndrome } });
      throw classifiedError;
    }
  }

  /**
   * Get Hebbian learner statistics
   */
  public getHebbianStats(): {
    strategyCount: number;
    topStrategies: any[];
    stability: number;
  } {
    try {
      const learner = this.substrate.getHebbianLearner();
      return {
        strategyCount: learner.getStrategyCount(),
        topStrategies: learner.getTopStrategies(5),
        stability: learner.getLearningStability(),
      };
    } catch (error) {
      const classifiedError = classifyError(error);
      logError(classifiedError, { component: 'IntelligenceService', operation: 'getHebbianStats' });
      throw classifiedError;
    }
  }

  /**
   * Reset the intelligence system
   */
  public reset(): void {
    try {
      this.substrate.reset();
      this.errorCount = 0;
      console.log("[IntelligenceService] System reset");
    } catch (error) {
      const classifiedError = classifyError(error);
      logError(classifiedError, { component: 'IntelligenceService', operation: 'reset' });
      throw classifiedError;
    }
  }

  /**
   * Export system state
   */
  public exportState(): any {
    try {
      return this.substrate.exportState();
    } catch (error) {
      const classifiedError = classifyError(error);
      logError(classifiedError, { component: 'IntelligenceService', operation: 'exportState' });
      throw classifiedError;
    }
  }

  /**
   * Check if system is running
   */
  public isActive(): boolean {
    return this.isRunning;
  }
  
  /**
   * Get health status
   */
  public getHealthStatus(): {
    isActive: boolean;
    errorCount: number;
    phi: number;
    mode: string;
  } {
    try {
      const telemetry = this.getTelemetry();
      return {
        isActive: this.isRunning,
        errorCount: this.errorCount,
        phi: this.getPhi(),
        mode: telemetry.mode
      };
    } catch (error) {
      const classifiedError = classifyError(error);
      logError(classifiedError, { component: 'IntelligenceService', operation: 'getHealthStatus' });
      return {
        isActive: false,
        errorCount: this.errorCount,
        phi: 0,
        mode: 'ERROR'
      };
    }
  }
}
