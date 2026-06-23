import React from "react";

export type MetricKey = "phi_resonance" | "code_distance" | "physical_error_rate" | "substrate_coherence" | "evidence_seal" | "invariants" | "claim_boundary" | "pulvini_memory" | "salamander_regeneration";

export const METRIC_TRANSLATIONS: Record<MetricKey, { label: string; plain: string; operational: string; evidence: string; expert: string }> = {
  phi_resonance: { label: "Coherence target", plain: "How strict HYBA should be about stable reasoning before using an answer.", operational: "Use balanced defaults unless the decision is regulated, high-value, or safety-sensitive.", evidence: "Compare live φ telemetry with the requested target and invariant results.", expert: "φ-resonance target / phase alignment threshold." },
  code_distance: { label: "Resilience level", plain: "How much correction margin the rail reserves for noisy or uncertain execution.", operational: "Higher resilience is safer for critical decisions; lower resilience is faster for exploration.", evidence: "Bound to provisioned rail configuration and runtime integrity checks.", expert: "Surface-code distance / correction-distance parameter." },
  physical_error_rate: { label: "Reliability assumption", plain: "The expected underlying error level HYBA designs around.", operational: "Lower is stricter and more procurement-safe for evidence-bound workloads.", evidence: "Validated against runtime telemetry and claim-boundary constraints.", expert: "Physical error-rate assumption." },
  substrate_coherence: { label: "Reasoning stability", plain: "Whether HYBA's intelligence state is internally consistent enough to trust for the selected task.", operational: "Strong coherence supports simulation; weak coherence should hold or request more evidence.", evidence: "Backed by substrate telemetry, invariant checks, and evidence seals when present.", expert: "Substrate coherence / φ-coherence telemetry." },
  evidence_seal: { label: "Evidence seal", plain: "A proof packet that lets teams audit what HYBA claimed and why.", operational: "Require a seal before procurement, compliance, or autonomous-adjacent actions.", evidence: "Seal ID, trace ID, invariant status, and data-source metadata.", expert: "Cryptographic/evidence packet identifier." },
  invariants: { label: "Proof checks", plain: "Required checks that must pass before HYBA should present a claim as reliable.", operational: "Missing or failed checks should block high-risk execution and request review.", evidence: "Invariant pass/fail set from live telemetry only.", expert: "Invariant-result vector." },
  claim_boundary: { label: "Claim boundary", plain: "The limit of what HYBA is allowed to say or do with this result.", operational: "Advisory claims may propose; execution requires approval unless pre-authorized low risk.", evidence: "Policy tags, governance status, and approval requirement.", expert: "External-claim contract boundary." },
  pulvini_memory: { label: "Memory rail", plain: "HYBA's structured memory for reusing context without losing auditability.", operational: "Use it to preserve decision context and evidence continuity.", evidence: "Memory source, compression metadata, and trace continuity.", expert: "PULVINI φ-memory parameters." },
  salamander_regeneration: { label: "Regeneration proposal", plain: "HYBA can suggest a repair path when a workflow is degraded.", operational: "Prepare remediation, show blast radius, then request role-aware approval.", evidence: "Governance tags, proposed action, rollback plan, and audit entry.", expert: "Salamander regeneration action plan." },
};

export function MetricExplainerCard({ metric, value, className = "" }: { metric: MetricKey; value?: React.ReactNode; className?: string }) {
  const item = METRIC_TRANSLATIONS[metric];
  return (
    <div className={`rounded-xl border border-blue-100 bg-blue-50/80 p-4 ${className}`} data-testid={`metric-explainer-${metric}`}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-blue-700">{item.label}</p>
          {value !== undefined && <p className="mt-1 font-mono text-sm font-semibold text-slate-950">{value}</p>}
        </div>
        <span className="rounded-full border border-blue-200 bg-white px-2 py-1 text-[10px] font-semibold text-blue-700">Translated</span>
      </div>
      <dl className="mt-3 space-y-2 text-xs leading-5 text-slate-700">
        <div><dt className="font-semibold text-slate-900">What this means</dt><dd>{item.plain}</dd></div>
        <div><dt className="font-semibold text-slate-900">Operational implication</dt><dd>{item.operational}</dd></div>
        <div><dt className="font-semibold text-slate-900">Evidence view</dt><dd>{item.evidence}</dd></div>
      </dl>
    </div>
  );
}

export function EvidenceBoundAnswer({ claimBoundary = "advisory, not autonomous execution", evidenceSeal = "required", invariantStatus = "must pass", dataSource = "live telemetry only", approval = "human approval required before action" }: { claimBoundary?: string; evidenceSeal?: string; invariantStatus?: string; dataSource?: string; approval?: string }) {
  return (
    <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4" data-testid="evidence-bound-answer">
      <p className="text-sm font-bold text-emerald-950">This answer is evidence-bound.</p>
      <div className="mt-3 grid gap-2 text-xs text-emerald-900 sm:grid-cols-2">
        <span><strong>Claim boundary:</strong> {claimBoundary}</span>
        <span><strong>Evidence seal:</strong> {evidenceSeal}</span>
        <span><strong>Invariants:</strong> {invariantStatus}</span>
        <span><strong>Data source:</strong> {dataSource}</span>
        <span className="sm:col-span-2"><strong>Approval:</strong> {approval}</span>
      </div>
    </div>
  );
}

export function ClaimBoundaryBadge({ boundary = "proposal_only" }: { boundary?: string }) {
  return <span className="rounded-full border border-amber-200 bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-800">Claim boundary: {boundary}</span>;
}
