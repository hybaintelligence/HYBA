/**
 * HYBA Feature Flag System
 *
 * Controls visibility of internal vs. customer-facing surfaces.
 * Production deployments should use VITE_CUSTOMER_MODE=true to hide
 * all internal validation infrastructure (mining, pool management, raw hashrate).
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

function envFlag(name: string, fallback: boolean): boolean {
  const raw = import.meta.env[name];
  if (raw == null || raw === "") return fallback;
  return String(raw).toLowerCase() === "true";
}

const isCustomerMode = envFlag("VITE_CUSTOMER_MODE", import.meta.env.MODE === "production");
const isInternalMode = envFlag("VITE_INTERNAL_MODE", false);
const isDevelopment = import.meta.env.DEV;

/**
 * Feature flags configuration
 *
 * Default behavior:
 * - Production/customer mode: Only QaaS/QIaaS/CIaaS/Finance/evidence visible
 * - Development: customer-safe by default unless VITE_INTERNAL_MODE=true
 * - Internal mode: mining/private treasury tools visible only outside customer mode
 */
export const FEATURES: FeatureFlags = {
  // Internal operations (hidden by default in production and customer mode)
  SHOW_MINING_UI: isInternalMode && !isCustomerMode,
  SHOW_INTERNAL_TELEMETRY: isInternalMode && !isCustomerMode,
  SHOW_POOL_MANAGEMENT: isInternalMode && !isCustomerMode,
  SHOW_HASHRATE_METRICS: isInternalMode && !isCustomerMode,

  // Customer-facing (always visible)
  SHOW_QAAS: true,
  SHOW_QIAAS: true,
  SHOW_CIAAS: true,
  SHOW_QUANTUM_FINANCE: true,
  SHOW_EVIDENCE_EXPLORER: true,

  // Debug/runtime transport
  SHOW_DEBUG_PANEL: isDevelopment && isInternalMode && !isCustomerMode,
  ENABLE_WEBSOCKET: envFlag("VITE_ENABLE_WEBSOCKET", true),
};

/**
 * Check if user has access to internal operations.
 * Mining controls are restricted to CEO/treasury roles and internal mode.
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
 * Get customer-safe metric label.
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
    activePool: "Execution Rail",
    pools: "Execution Rails",
  };

  return CUSTOMER_LABELS[internalKey] || internalKey;
}

/**
 * Filter telemetry for customer view.
 */
export function filterCustomerTelemetry<T extends Record<string, unknown>>(data: T): Partial<T> {
  if (FEATURES.SHOW_INTERNAL_TELEMETRY) return data;

  const filtered: Record<string, unknown> = { ...data };

  // Remove mining-specific fields.
  delete filtered.activePool;
  delete filtered.currentHashrate;
  delete filtered.effective_hashrate_ehs;
  delete filtered.hashrate;
  delete filtered.power_scale;
  delete filtered.pools;
  delete filtered.mining;

  return filtered;
}

export default FEATURES;
