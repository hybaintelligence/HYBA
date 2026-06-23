/**
 * Blast Radius Calculation Utility
 *
 * Calculates the potential impact scope of proposed actions for governance approval.
 * Used by ActionGuard and AI Assistant to assess risk before execution.
 */

export type BlastRadiusLevel = "read-only" | "low" | "medium" | "high" | "critical";

export interface BlastRadiusAssessment {
  level: BlastRadiusLevel;
  description: string;
  affectedSystems: string[];
  rollbackComplexity: "trivial" | "simple" | "moderate" | "complex" | "manual";
  requiresApproval: boolean;
  approvalLevel: "none" | "operator" | "admin" | "executive" | "board";
}

export interface ProposedAction {
  command: string;
  type: "read" | "write" | "delete" | "restart" | "configure" | "deploy";
  target?: string;
  scope?: "local" | "tenant" | "global" | "production";
}

const SYSTEM_IMPACT_MAP: Record<string, string[]> = {
  "refresh_telemetry": ["monitoring", "observability"],
  "switch_pool": ["mining", "revenue", "pool_connection"],
  "disconnect_pool": ["mining", "revenue", "pool_connection"],
  "stop_mining": ["mining", "revenue", "hardware"],
  "start_mining": ["mining", "revenue", "hardware"],
  "update_power_scale": ["mining", "hardware", "power_consumption"],
  "configure_pool": ["mining", "pool_connection", "credentials"],
  "regenerate_substrate": ["intelligence", "substrate", "all_rails"],
  "restart_service": ["service", "availability", "connected_clients"],
  "delete_service": ["service", "data", "all_rails"],
  "update_governance": ["governance", "all_rails", "compliance"],
  "modify_claim_boundary": ["governance", "compliance", "liability"],
  "change_tier": ["billing", "service_level", "entitlements"],
  "modify_isolation": ["security", "tenancy", "data_residency"],
};

const SCOPE_IMPACT_MULTIPLIER: Record<string, number> = {
  local: 1,
  tenant: 2,
  global: 4,
  production: 8,
};

const TYPE_IMPACT_BASE: Record<string, number> = {
  read: 0,
  write: 2,
  configure: 3,
  restart: 4,
  delete: 6,
  deploy: 8,
};

function calculateBlastRadiusScore(action: ProposedAction): number {
  const typeScore = TYPE_IMPACT_BASE[action.type] || 2;
  const scopeMultiplier = SCOPE_IMPACT_MULTIPLIER[action.scope || "local"] || 1;
  return typeScore * scopeMultiplier;
}

function determineBlastRadiusLevel(score: number): BlastRadiusLevel {
  if (score === 0) return "read-only";
  if (score <= 2) return "low";
  if (score <= 6) return "medium";
  if (score <= 12) return "high";
  return "critical";
}

function determineApprovalLevel(level: BlastRadiusLevel): BlastRadiusAssessment["approvalLevel"] {
  switch (level) {
    case "read-only":
      return "none";
    case "low":
      return "operator";
    case "medium":
      return "admin";
    case "high":
      return "executive";
    case "critical":
      return "board";
  }
}

function determineRollbackComplexity(action: ProposedAction): BlastRadiusAssessment["rollbackComplexity"] {
  if (action.type === "read") return "trivial";
  if (action.type === "write" || action.type === "configure") return "simple";
  if (action.type === "restart") return "moderate";
  if (action.type === "delete" && action.scope === "local") return "moderate";
  if (action.type === "delete") return "complex";
  if (action.type === "deploy") return "complex";
  return "manual";
}

export function calculateBlastRadius(action: ProposedAction): BlastRadiusAssessment {
  const score = calculateBlastRadiusScore(action);
  const level = determineBlastRadiusLevel(score);
  const approvalLevel = determineApprovalLevel(level);
  const rollbackComplexity = determineRollbackComplexity(action);
  const affectedSystems = SYSTEM_IMPACT_MAP[action.command] || ["unknown"];

  const descriptions: Record<BlastRadiusLevel, string> = {
    "read-only": "No system changes; read-only telemetry or status query.",
    "low": "Minor configuration change with limited scope and simple rollback.",
    "medium": "Moderate impact affecting specific services or tenant state.",
    "high": "Significant impact affecting multiple systems or production state.",
    "critical": "Maximum impact affecting global state, compliance, or revenue streams.",
  };

  return {
    level,
    description: descriptions[level],
    affectedSystems,
    rollbackComplexity,
    requiresApproval: level !== "read-only",
    approvalLevel,
  };
}

export function formatBlastRadiusForDisplay(assessment: BlastRadiusAssessment): string {
  const levelColors: Record<BlastRadiusLevel, string> = {
    "read-only": "text-green-700 bg-green-50",
    "low": "text-blue-700 bg-blue-50",
    "medium": "text-yellow-700 bg-yellow-50",
    "high": "text-orange-700 bg-orange-50",
    "critical": "text-red-700 bg-red-50",
  };

  return `${assessment.level.toUpperCase()} · ${assessment.description}`;
}
