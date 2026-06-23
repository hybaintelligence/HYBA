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
  computeNode?: string | null;
  residencyStatus?: string | null;
  jurisdiction?: string | null;
}

export interface EvidencePackageInput extends GovernanceTelemetryInput {
  decisionId: string;
  claimBoundary: string;
  invariants: Record<string, boolean>;
  evidenceSeal?: string | null;
  approver?: { id?: string; username?: string; role?: string } | null;
  approvalLog?: Array<{ action: string; approvedBy: string; approvedAt: string; role: string }>;
}

export interface PortableEvidencePackage {
  schema: "hyba.portable_evidence_package.v1";
  issuedAt: string;
  decisionId: string;
  sovereignty: {
    computeNode: string;
    residencyStatus: string;
    jurisdiction: string;
  };
  claimBoundary: string;
  invariants: Record<string, boolean>;
  evidenceSeal: string;
  humanApproval: {
    approver: EvidencePackageInput["approver"];
    approvalLog: EvidencePackageInput["approvalLog"];
    policy: "no_unattended_writes";
  };
  telemetry: GovernanceTelemetryInput;
  signature: {
    algorithm: "SHA-256";
    digest: string;
    signedPayload: string;
  };
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
      status: tags.has("no_unattended_writes") || tags.has("proposal_only") || tags.has("salamander_regeneration") ? "pass" : "warn",
      detail:
        tags.has("no_unattended_writes")
          ? "Reflexive intelligence is bounded by no-unattended-writes governance."
          : tags.has("proposal_only")
            ? "Reflexive intelligence operates under proposal-only governance - changes require explicit approval."
            : tags.has("salamander_regeneration")
              ? "Reflexive intelligence operates under Salamander regeneration protocol - autonomous fixing enabled."
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
    {
      id: "sovereignty-residency",
      label: "Sovereignty residency",
      status: input.computeNode && input.residencyStatus ? "pass" : "warn",
      detail:
        input.computeNode && input.residencyStatus
          ? `Compute is pinned to ${input.computeNode}; residency status is ${input.residencyStatus}.`
          : "Compute node or residency status is unavailable; evidence export will mark jurisdiction as unverified.",
    },
  ];

  return signals;
}

async function sha256Hex(payload: string): Promise<string> {
  const encoded = new TextEncoder().encode(payload);
  const hash = await crypto.subtle.digest("SHA-256", encoded);
  return Array.from(new Uint8Array(hash))
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
}

export async function buildPortableEvidencePackage(
  input: EvidencePackageInput,
): Promise<PortableEvidencePackage> {
  const issuedAt = new Date().toISOString();
  const unsigned = {
    schema: "hyba.portable_evidence_package.v1" as const,
    issuedAt,
    decisionId: input.decisionId,
    sovereignty: {
      computeNode: input.computeNode || "unverified-node",
      residencyStatus: input.residencyStatus || "unverified-residency",
      jurisdiction: input.jurisdiction || "unverified-jurisdiction",
    },
    claimBoundary: input.claimBoundary,
    invariants: input.invariants,
    evidenceSeal: input.evidenceSeal || "missing-seal",
    humanApproval: {
      approver: input.approver || null,
      approvalLog: input.approvalLog || [],
      policy: "no_unattended_writes" as const,
    },
    telemetry: input,
  };
  const signedPayload = JSON.stringify(unsigned);
  return {
    ...unsigned,
    signature: {
      algorithm: "SHA-256",
      digest: await sha256Hex(JSON.stringify(unsigned)),
      signedPayload,
    },
  };
}

export function downloadEvidencePackage(pkg: PortableEvidencePackage, format: "json" | "pdf") {
  const name = `hyba-audit-memo-${pkg.decisionId}.${format}`;
  const text =
    format === "json"
      ? JSON.stringify(pkg, null, 2)
      : [
          "HYBA Export Audit Memo",
          `Decision: ${pkg.decisionId}`,
          `Issued: ${pkg.issuedAt}`,
          `Node: ${pkg.sovereignty.computeNode}`,
          `Residency: ${pkg.sovereignty.residencyStatus}`,
          `Jurisdiction: ${pkg.sovereignty.jurisdiction}`,
          `Claim Boundary: ${pkg.claimBoundary}`,
          `Evidence Seal: ${pkg.evidenceSeal}`,
          `Human Approval Policy: ${pkg.humanApproval.policy}`,
          `Signature (${pkg.signature.algorithm}): ${pkg.signature.digest}`,
          "",
          "Invariants:",
          ...Object.entries(pkg.invariants).map(([key, value]) => `- ${key}: ${value ? "PASS" : "FAIL"}`),
          "",
          "Approval log:",
          ...(pkg.humanApproval.approvalLog || []).map(
            (entry) => `- ${entry.approvedAt} ${entry.approvedBy} (${entry.role}) approved ${entry.action}`,
          ),
        ].join("\n");
  const blob = new Blob([text], { type: format === "json" ? "application/json" : "application/pdf" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  link.click();
  URL.revokeObjectURL(url);
}
