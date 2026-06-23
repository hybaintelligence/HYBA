import React from "react";

export type MetricKey =
  | "phi_resonance"
  | "code_distance"
  | "physical_error_rate"
  | "substrate_coherence"
  | "substrateCoherence"
  | "evidence_seal"
  | "invariants"
  | "claim_boundary"
  | "pulvini_memory"
  | "salamander_regeneration"
  | "quantum_certainty"
  | "classical_fallback"
  | "temporal_delta";

type Engine = "ci" | "qi";

type CopyBlock = { title: string; plain: string; implication: string; evidence: string };

const CI_COPY: Record<MetricKey, CopyBlock> = {
  phi_resonance: {
    title: "Escalation threshold",
    plain: "CI does not use resonance as its primary language; this marks when an operational anomaly should be handed to QI.",
    implication: "Keep routine workflow fixes in CI and escalate only ambiguous, high-impact anomalies.",
    evidence: "Operational logs, regeneration audit trails, uptime signals, and process-efficiency deltas.",
  },
  code_distance: {
    title: "Regeneration resilience",
    plain: "How much self-healing capacity HYBA allocates around this operational rail.",
    implication: "Higher resilience supports uptime-sensitive workflows but consumes more compute capacity.",
    evidence: "Provisioned resilience preset, regeneration events, and standard audit stamps.",
  },
  physical_error_rate: {
    title: "Operational noise assumption",
    plain: "The expected low-level execution noise for CI jobs, automation, and substrate-health checks.",
    implication: "Use conservative presets for regulated operations or systems with strict uptime targets.",
    evidence: "Runtime error bounds, substrate-health telemetry, and remediation logs.",
  },
  substrate_coherence: {
    title: "System health",
    plain: "Whether the CI substrate is running well enough to keep jobs moving and heal common failures.",
    implication: "Strong coherence means operational automation can continue; weak coherence should pause or escalate.",
    evidence: "Health checks, active job status, regeneration events, and process-efficiency telemetry.",
  },
  evidence_seal: {
    title: "Standard audit stamp",
    plain: "CI attaches a traceable operational record showing what changed, why, and under which guardrail.",
    implication: "Proceed with routine fixes when the audit trail is complete and the action remains reversible.",
    evidence: "Regeneration audit trail, command log, source telemetry, and approval state.",
  },
  invariants: {
    title: "Operational guardrails",
    plain: "Checks that keep automated fixes inside allowed workflows and prevent unsafe unattended writes.",
    implication: "Failed checks should block the fix or trigger a QI escalation when strategic ambiguity remains.",
    evidence: "Policy tags, no-unattended-writes status, and audit-ledger entries.",
  },
  claim_boundary: { title: "Claim boundary", plain: "The limit on what CI may automate before requesting approval or QI escalation.", implication: "Routine fixes can proceed only inside policy; material action needs approval.", evidence: "Policy tags, approval state, audit stamp, and rollback plan." },
  substrateCoherence: {
    title: "System health",
    plain: "Whether the CI substrate is running well enough to keep jobs moving and heal common failures.",
    implication: "Strong coherence means operational automation can continue; weak coherence should pause or escalate.",
    evidence: "Health checks, active job status, regeneration events, and process-efficiency telemetry.",
  },
  claim_boundary: {
    title: "Claim boundary",
    plain: "The explicit line between advisory intelligence, simulation, proposal preparation, and approved execution.",
    implication: "Executives can brief a board on the recommendation without implying HYBA has taken action.",
    evidence: "Preserve the boundary text with approver, policy, evidence seal, and timestamp.",
  },
  pulvini_memory: {
    title: "PULVINI memory",
    plain: "The context-retention layer that keeps decision history available while compressing less relevant detail.",
    implication: "Useful for CFO and auditor review because assumptions can be traced across meetings and incidents.",
    evidence: "Show memory lineage, compression scope, retention boundary, and source records.",
  },
  salamander_regeneration: {
    title: "Regeneration proposal",
    plain: "A self-healing suggestion that drafts remediation without silently changing production systems.",
    implication: "Treat the output as a proposal card; require blast-radius review and explicit approval.",
    evidence: "Attach degradation signal, proposed command, rollback plan, approver, and audit log.",
  },
  quantum_certainty: {
    title: "Quantum-backed certainty",
    plain: "HYBA is presenting the answer from a substrate-backed path with invariants and evidence seal available.",
    implication: "Suitable for high-stakes recommendation review, while still requiring human authorization for action.",
    evidence: "Confirm live telemetry source, passing invariants, seal freshness, and claim boundary.",
  },
  classical_fallback: {
    title: "Classical heuristic fallback",
    plain: "HYBA can still explain a result, but the confidence comes from deterministic heuristics rather than a fully backed rail.",
    implication: "Use for triage or exploration; gather more evidence before a board-impacting decision.",
    evidence: "Look for fallback reason, missing telemetry fields, stale seal, or disconnected backend state.",
  },
  temporal_delta: {
    title: "Intelligence trend",
    plain: "Whether reasoning stability is improving, flat, or degrading compared with recent live samples.",
    implication: "Converging trends support continued analysis; degrading trends should trigger review before commitments.",
    evidence: "Compare consecutive substrate coherence / φ-alignment samples from the active telemetry stream.",
  },
};

export function MetricExplainerCard({ metric, metricKey, value }: { metric?: MetricKey; metricKey?: MetricKey; value?: React.ReactNode }) {
  const key = metric || metricKey || "substrate_coherence";
  const copy = COPY[key];
  return (
    <div className="rounded-xl border border-blue-100 bg-blue-50/70 p-4 text-sm text-slate-700">
      {value && <p className="mb-1 font-mono text-[11px] font-bold uppercase tracking-[0.14em] text-blue-800">{value}</p>}
      <p className="font-semibold text-slate-900">{copy.title}</p>
      {value !== undefined && <p className="mt-1 font-mono text-xs text-slate-950">{value}</p>}
      <p className="mt-2">
        <span className="font-medium">What this means:</span> {copy.plain}
      </p>
      <p className="mt-1">
        <span className="font-medium">Operational implication:</span> {copy.implication}
      </p>
      <p className="mt-1">
        <span className="font-medium">Evidence view:</span> {copy.evidence}
      </p>
    </div>
  );
}

export function ClaimBoundaryBadge({ boundary = "advisory intelligence; human approval required" }: { boundary?: string }) {
  return (
    <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-950">
      <p className="font-bold">This answer is evidence-bound.</p>
      <p>
        Claim boundary: {boundary}. Human approval is required before material action.
      </p>
    </div>
  );
}


export function EvidenceBoundAnswer({ seal, evidenceSeal, claimBoundary = "advisory intelligence", invariantStatus = "must pass", source, dataSource }: { seal?: string; evidenceSeal?: string; claimBoundary?: string; invariantStatus?: string; source?: string; dataSource?: string }) {
  return (
    <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-950">
      <p className="font-bold">Evidence-bound answer</p>
      <p className="mt-1">Seal: {seal || evidenceSeal || "required"} · Boundary: {claimBoundary} · Invariants: {invariantStatus} · Source: {source || dataSource || "live telemetry only"}</p>
    </div>
  );
}

export function ProofExplainer({ seal, invariantSummary, source }: { seal?: string; invariantSummary?: string; source?: string }) {
  return <EvidenceBoundAnswer seal={seal} invariantStatus={invariantSummary} source={source} claimBoundary="proof-backed advisory intelligence" />;
}
