/**
 * HYBA Feature Flag System
 *
 * Controls visibility of internal vs. customer-facing surfaces.
 * Production deployments should use HYBA_CUSTOMER_MODE=true to hide
 * all internal validation infrastructure (mining, internal telemetry).
 */

export interface FeatureFlags {
  // Internal operations visibility
  SHOW_MINING_UI: boolean;
  SHOW_INTERNAL_TELEMETRY: boolean;
  SHOW_POOL_MANAGEMENT: boolean;
  SHOW_HASHRATE_METRICS: boolean;

  // Customer-facing features
  SHOW_QAAS: boolean;
  SHOW_QIAAS: boolean;
  SHOW_CIAAS: boolean;
  SHOW_QUANTUM_FINANCE: boolean;
  SHOW_EVIDENCE_EXPLORER: boolean;

  // Development/debugging
  SHOW_DEBUG_PANEL: boolean;
  ENABLE_WEBSOCKET: boolean;
}

const isProduction = import.meta.env.MODE === "production";
const isCustomerMode = import.meta.env.VITE_CUSTOMER_MODE === "true";
const isInternalMode = import.meta.env.VITE_INTERNAL_MODE === "true";
const isDevelopment = import.meta.env.DEV;

/**
 * Feature flags configuration
 *
 * Default behavior:
 * - Production customer mode: Only QaaS/QIaaS/CIaaS/Finance visible
 * - Development: All features visible
 * - Internal mode: All features including mining visible
 */
export const FEATURES: FeatureFlags = {
  // Internal operations (hidden by default in production)
  SHOW_MINING_UI: isInternalMode && !isCustomerMode,
  SHOW_INTERNAL_TELEMETRY: isInternalMode || isDevelopment,
  SHOW_POOL_MANAGEMENT: isInternalMode && !isCustomerMode,
  SHOW_HASHRATE_METRICS: isInternalMode && !isCustomerMode,

  // Customer-facing (always visible)
  SHOW_QAAS: true,
  SHOW_QIAAS: true,
  SHOW_CIAAS: true,
  SHOW_QUANTUM_FINANCE: true,
  SHOW_EVIDENCE_EXPLORER: true,

  // Debug (only in development)
  SHOW_DEBUG_PANEL: isDevelopment,
  ENABLE_WEBSOCKET: !isProduction,
};

/**
 * Check if user has access to internal operations
 * Mining controls are restricted to CEO/treasury roles and internal mode
 */
export function hasInternalAccess(userRole?: string): boolean {
  if (!FEATURES.SHOW_MINING_UI) return false;
  const treasuryRoles = [
    "ceo_heir_apparent",
    "chairman",
    "cto",
    "cfo",
    "treasury",
    "admin",
    "internal_operator",
  ];
  return treasuryRoles.includes(userRole || "");
}

/**
 * Get customer-safe metric label
 */
export function getCustomerMetricLabel(internalKey: string): string {
  const CUSTOMER_LABELS: Record<string, string> = {
    hashrate: "Compute Throughput",
    effective_hashrate_ehs: "Effective Compute Capacity",
    power_scale: "Compute Scale",
    phi_tier: "Optimization Tier",
    quantum_coherence: "Substrate Coherence",
    phi_resonance: "Computational Efficiency",
    consciousness_level: "Integration Metric",
    integrated_information: "Information Integration",
  };

  return CUSTOMER_LABELS[internalKey] || internalKey;
}

/**
 * Filter telemetry for customer view
 */
export function filterCustomerTelemetry<T extends Record<string, any>>(data: T): Partial<T> {
  if (FEATURES.SHOW_INTERNAL_TELEMETRY) return data;

  const filtered: any = { ...data };

  // Remove mining-specific fields
  delete filtered.activePool;
  delete filtered.currentHashrate;
  delete filtered.power_scale;
  delete filtered.pools;
  delete filtered.mining;

  return filtered;
}

export default FEATURES;
