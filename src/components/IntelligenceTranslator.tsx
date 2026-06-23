import React from "react";

export type MetricKey =
  | "phi_resonance"
  | "code_distance"
  | "physical_error_rate"
  | "substrate_coherence"
  | "substrateCoherence"
  | "evidence_seal"
  | "invariants"
  | "claim_boundary";

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
};

const QI_COPY: Record<MetricKey, CopyBlock> = {
  phi_resonance: {
    title: "Reasoning depth",
    plain: "How tightly the deep reasoning state must stabilize before HYBA treats a strategic answer as decision-ready.",
    implication: "Raise the target for catastrophic-cost decisions, regulated evidence, or board-level strategy.",
    evidence: "φ-resonance analysis, invariant proofs, causal-stability checks, and evidence seals.",
  },
  code_distance: {
    title: "Proof robustness",
    plain: "The depth of protection around strategic simulations and counterfactual reasoning.",
    implication: "Higher robustness increases confidence for complex decisions but increases execution cost.",
    evidence: "Code distance, proof weight, invariant status, and claim-boundary metadata.",
  },
  physical_error_rate: {
    title: "Certainty assumption",
    plain: "The assumed reasoning-noise floor for counterfactual simulations and proof-bearing decisions.",
    implication: "Use stricter values when the cost of being wrong is catastrophic.",
    evidence: "Error-rate bounds, proof summaries, evidence seals, and governance audit records.",
  },
  substrate_coherence: {
    title: "Causal stability",
    plain: "Whether the strategic reasoning surface is stable enough for counterfactual comparison.",
    implication: "Weak stability means the decision should be reframed, delayed, or supported with more evidence.",
    evidence: "Causal stability score, invariant checks, proof weight, and seal provenance.",
  },
  evidence_seal: {
    title: "Gold-standard seal",
    plain: "A traceable proof object that binds a high-stakes recommendation to its evidence and claim boundary.",
    implication: "Use sealed outputs for strategic moves where veracity matters more than speed.",
    evidence: "Immutable evidence seal, invariant proof, source set, and governance signature.",
  },
  invariants: {
    title: "Invariant proofs",
    plain: "Formal checks that explain why a strategic conclusion remains true within the stated assumptions.",
    implication: "Missing or failed invariants should block the strategic recommendation.",
    evidence: "Invariant proof summary, resonance target, proof weight, and causal-stability ledger.",
  },
  claim_boundary: { title: "Claim boundary", plain: "The strategic assumptions under which a QI answer is allowed to be treated as true.", implication: "Do not use sealed decisions outside the stated boundary without a new simulation.", evidence: "Claim boundary, source set, invariant proof, and governance signature." },
  substrateCoherence: {
    title: "Causal stability",
    plain: "Whether the strategic reasoning surface is stable enough for counterfactual comparison.",
    implication: "Weak stability means the decision should be reframed, delayed, or supported with more evidence.",
    evidence: "Causal stability score, invariant checks, proof weight, and seal provenance.",
  },
};

export function MetricExplainerCard({ metric, metricKey, value, engine = "qi" }: { metric?: MetricKey; metricKey?: MetricKey; value?: React.ReactNode; engine?: Engine }) {
  const selectedMetric = metric || metricKey || "substrate_coherence";
  const copy = (engine === "ci" ? CI_COPY : QI_COPY)[selectedMetric];
  const palette = engine === "ci" ? "border-emerald-100 bg-emerald-50/70 text-emerald-950" : "border-violet-100 bg-violet-50/70 text-violet-950";
  return (
    <div className={`rounded-xl border p-4 text-sm ${palette}`}>
      <p className="font-semibold text-slate-900">{copy.title}</p>
      {value !== undefined && <p className="mt-1 font-mono text-sm font-semibold text-slate-950">{value}</p>}
      <p className="mt-2"><span className="font-medium">Plain English:</span> {copy.plain}</p>
      <p className="mt-1"><span className="font-medium">Business implication:</span> {copy.implication}</p>
      <p className="mt-1"><span className="font-medium">Evidence tier:</span> {copy.evidence}</p>
    </div>
  );
}

export function ClaimBoundaryBadge({ boundary = "proposal_only" }: { boundary?: string }) {
  return (
    <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-950">
      <p className="font-bold">This answer is evidence-bound.</p>
      <p>Claim boundary: {boundary}. Advisory intelligence, not autonomous execution. Human approval is required before material action.</p>
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
