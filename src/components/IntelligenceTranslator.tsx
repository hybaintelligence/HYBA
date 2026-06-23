import React from "react";

export type MetricKey =
  | "phi_resonance"
  | "code_distance"
  | "physical_error_rate"
  | "substrate_coherence"
  | "evidence_seal"
  | "invariants"
  | "claim_boundary"
  | "pulvini_memory"
  | "salamander_regeneration"
  | "quantum_certainty"
  | "classical_fallback"
  | "temporal_delta";

const COPY: Record<
  MetricKey,
  { title: string; plain: string; implication: string; evidence: string }
> = {
  phi_resonance: {
    title: "Coherence target",
    plain:
      "How strict HYBA is about stable evidence before treating intelligence as decision-ready.",
    implication:
      "Balanced defaults are appropriate for most business workflows; raise only for regulated or high-risk decisions.",
    evidence: "Correlate with φ phase alignment, invariant status, and live telemetry provenance.",
  },
  code_distance: {
    title: "Resilience preset",
    plain: "How much fault-tolerance HYBA allocates around the intelligence rail.",
    implication:
      "Higher resilience can improve trust for critical workflows but consumes more capacity.",
    evidence:
      "Backed by provisioned code distance, reliability assumptions, and governance policy.",
  },
  physical_error_rate: {
    title: "Reliability assumption",
    plain: "The operating assumption about low-level execution noise.",
    implication: "Use conservative presets for regulated evidence or board-impacting actions.",
    evidence: "Validated against configured error-rate bounds and proof telemetry.",
  },
  substrate_coherence: {
    title: "Reasoning stability",
    plain: "Whether HYBA's reasoning state is internally stable enough to support a decision.",
    implication:
      "Strong coherence supports simulation; weak coherence should trigger review or escalation.",
    evidence: "Review substrate health, invariants, and claim-boundary status.",
  },
  evidence_seal: {
    title: "Evidence-bound answer",
    plain: "HYBA can attach a traceable proof object to the recommendation.",
    implication: "Proceed only inside the stated claim boundary and approval policy.",
    evidence: "Seal presence, invariant pass state, source telemetry, and audit log entry.",
  },
  invariants: {
    title: "Proof checks",
    plain: "Automated checks that keep outputs within known safe operating boundaries.",
    implication: "Failed or missing checks should block unattended execution.",
    evidence: "Invariant summary, governance tags, and no-unattended-writes policy.",
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
