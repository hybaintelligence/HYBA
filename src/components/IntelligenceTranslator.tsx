import React from "react";
import { metricTranslations, type MetricTranslationKey } from "../intelligenceTranslations";
import { useSkillMode } from "../skillMode";

export type MetricKey = MetricTranslationKey;

export function MetricExplainerCard({ metric, metricKey, value }: { metric?: MetricKey; metricKey?: MetricKey; value?: React.ReactNode }) {
  const key = metric || metricKey || "substrate_coherence";
  const { mode } = useSkillMode();
  const translation = metricTranslations[key]?.[mode] || metricTranslations[key]?.["business"];

  if (!translation) {
    return null;
  }

  return (
    <div className="rounded-xl border border-blue-100 bg-blue-50/70 p-4 text-sm text-slate-700">
      {value && <p className="mb-1 font-mono text-[11px] font-bold uppercase tracking-[0.14em] text-blue-800">{value}</p>}
      <p className="font-semibold text-slate-900">{translation.label}</p>
      {value !== undefined && <p className="mt-1 font-mono text-xs text-slate-950">{value}</p>}
      <p className="mt-2">
        <span className="font-medium">What this means:</span> {translation.plainEnglish}
      </p>
      <p className="mt-1">
        <span className="font-medium">Operational implication:</span> {translation.operationalImplication}
      </p>
      <p className="mt-1">
        <span className="font-medium">Evidence view:</span> {translation.evidenceView}
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
