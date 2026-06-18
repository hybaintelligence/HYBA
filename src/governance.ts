export type GovernanceSeverity = "pass" | "warn" | "fail";

export interface GovernanceSignal {
  id: string;
  label: string;
  status: GovernanceSeverity;
  detail: string;
}

export interface GovernanceTelemetryInput {
  runtimeStatus?: string | null;
  telemetrySource?: string | null;
  backendConnected?: boolean;
  activePoolCount?: number;
  configuredPoolCount?: number;
  activePoolName?: string | null;
  securityStatus?: string | null;
  threatLevel?: string | null;
  phiResonance?: number | null;
  governanceTags?: string[] | null;
}

const GOOD_RUNTIME = new Set(["ok", "healthy", "ready"]);
const BAD_SECURITY = new Set(["critical", "high", "error", "degraded"]);

function normalized(value: string | null | undefined): string {
  return String(value || "")
    .trim()
    .toLowerCase();
}

function hasFiniteNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

export function buildGovernanceSignals(input: GovernanceTelemetryInput): GovernanceSignal[] {
  const runtime = normalized(input.runtimeStatus);
  const telemetrySource = normalized(input.telemetrySource);
  const security = normalized(input.securityStatus);
  const threat = normalized(input.threatLevel);
  const tags = new Set((input.governanceTags || []).map(normalized));
  const activePoolCount = input.activePoolCount ?? 0;
  const configuredPoolCount = input.configuredPoolCount ?? 0;

  const signals: GovernanceSignal[] = [
    {
      id: "runtime-readiness",
      label: "Runtime readiness",
      status: GOOD_RUNTIME.has(runtime) && input.backendConnected ? "pass" : "fail",
      detail:
        GOOD_RUNTIME.has(runtime) && input.backendConnected
          ? "Backend readiness is live and reachable."
          : "Backend readiness is not confirmed; production actions must remain gated.",
    },
    {
      id: "real-telemetry",
      label: "Real telemetry only",
      status:
        telemetrySource &&
        !telemetrySource.includes("synthetic") &&
        !telemetrySource.includes("mock")
          ? "pass"
          : "fail",
      detail:
        telemetrySource &&
        !telemetrySource.includes("synthetic") &&
        !telemetrySource.includes("mock")
          ? `Telemetry source reported as ${input.telemetrySource}.`
          : "Telemetry source is missing or indicates a fixture/synthetic path.",
    },
    {
      id: "pool-operator-gate",
      label: "Pool operator gate",
      status:
        activePoolCount > 0 || input.activePoolName
          ? "pass"
          : configuredPoolCount > 0
            ? "warn"
            : "fail",
      detail:
        activePoolCount > 0 || input.activePoolName
          ? "At least one operator-configured pool is active."
          : configuredPoolCount > 0
            ? "Pool profiles exist, but no active pool is confirmed."
            : "No configured pool profile is visible in telemetry.",
    },
    {
      id: "security-posture",
      label: "Security posture",
      status:
        BAD_SECURITY.has(threat) || BAD_SECURITY.has(security)
          ? "fail"
          : security
            ? "pass"
            : "warn",
      detail:
        BAD_SECURITY.has(threat) || BAD_SECURITY.has(security)
          ? "Security telemetry reports a blocking threat state."
          : security
            ? `Security status is ${input.securityStatus}.`
            : "Security status is unavailable; review bridge/internal health before cutover.",
    },
    {
      id: "claim-boundary",
      label: "Claim boundary",
      status: tags.has("no_unattended_writes") || tags.has("proposal_only") ? "pass" : "warn",
      detail:
        tags.has("no_unattended_writes") || tags.has("proposal_only")
          ? "Reflexive intelligence is bounded by proposal-only/no-unattended-writes governance."
          : "No reflexive governance tag was reported; do not infer autonomous source modification.",
    },
    {
      id: "phi-evidence",
      label: "φ evidence context",
      status: hasFiniteNumber(input.phiResonance) ? "pass" : "warn",
      detail: hasFiniteNumber(input.phiResonance)
        ? "φ-resonance is displayed as bounded diagnostic telemetry, not mining-yield proof."
        : "φ-resonance is unavailable; avoid public performance interpretation.",
    },
  ];

  return signals;
}
