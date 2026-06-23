import React from "react";

export type MetricKey =
  | "phi_resonance"
  | "code_distance"
  | "physical_error_rate"
  | "substrate_coherence"
  | "evidence_seal"
  | "invariants";

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
};

export function MetricExplainerCard({ metric }: { metric: MetricKey }) {
  const copy = COPY[metric];
  return (
    <div className="rounded-xl border border-blue-100 bg-blue-50/70 p-4 text-sm text-slate-700">
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

export function ClaimBoundaryBadge() {
  return (
    <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-950">
      <p className="font-bold">This answer is evidence-bound.</p>
      <p>
        Claim boundary: advisory intelligence, not autonomous execution. Human approval is required
        before material action.
      </p>
    </div>
  );
}
