import React from "react";
import { FileCheck2, Info, ShieldCheck } from "lucide-react";
import { useSkillMode } from "./SkillModeContext";

export const METRIC_TRANSLATIONS = {
  phiResonance: {
    label: "Coherence target",
    technicalLabel: "φ-resonance target",
    plain: "How strict HYBA is about keeping an intelligence run stable before trusting it.",
    implication: "Use Balanced unless the decision is regulated, high value, or safety critical.",
    evidence: "Validated with live telemetry, invariant checks, and evidence-seal status when available.",
  },
  codeDistance: {
    label: "Resilience preset",
    technicalLabel: "Code distance",
    plain: "How much protection HYBA asks for around an intelligence rail.",
    implication: "Higher resilience is appropriate for regulated or mission-critical decisions.",
    evidence: "Mapped to the provisioned rail configuration and governance claim boundary.",
  },
  physicalErrorRate: {
    label: "Reliability assumption",
    technicalLabel: "Physical error rate",
    plain: "The operating assumption for how noisy the underlying execution environment may be.",
    implication: "Keep the default unless an engineer has measured a different runtime envelope.",
    evidence: "Preserved in the request payload for audit and replay.",
  },
  substrateCoherence: {
    label: "Reasoning stability",
    technicalLabel: "Substrate coherence",
    plain: "Whether HYBA's internal reasoning state is stable enough for a decision workflow.",
    implication: "Strong coherence supports simulation and counterfactual analysis; weak coherence should trigger review.",
    evidence: "Backed by runtime telemetry, trace IDs, and invariant checks.",
  },
  evidenceSeal: {
    label: "Audit seal",
    technicalLabel: "Evidence seal",
    plain: "A compact proof object showing the answer was tied to evidence instead of unsupported generation.",
    implication: "Procurement, audit, and regulated workflows should require a seal before approval.",
    evidence: "Seal identifier, invariant status, claim boundary, and live source are displayed together.",
  },
} as const;

export type MetricKey = keyof typeof METRIC_TRANSLATIONS;

export function MetricExplainerCard({ metric, value }: { metric: MetricKey; value?: React.ReactNode }) {
  const { showTechnicalControls, showEvidenceFirst } = useSkillMode();
  const item = METRIC_TRANSLATIONS[metric];
  return (
    <div className="rounded-xl border border-blue-100 bg-blue-50/80 p-4 text-sm text-slate-700">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.18em] text-blue-700">
            {showTechnicalControls ? item.technicalLabel : item.label}
          </p>
          {value && <p className="mt-1 font-mono text-slate-950">{value}</p>}
        </div>
        <Info className="h-4 w-4 text-blue-500" />
      </div>
      <p className="mt-3 leading-6"><strong>Meaning:</strong> {item.plain}</p>
      {!showEvidenceFirst && <p className="mt-2 leading-6"><strong>Operational implication:</strong> {item.implication}</p>}
      <p className="mt-2 leading-6"><strong>Evidence:</strong> {item.evidence}</p>
    </div>
  );
}

export function EvidenceBoundAnswer({ seal, claimBoundary, invariantStatus, source }: { seal?: string; claimBoundary?: string; invariantStatus?: string; source?: string }) {
  return (
    <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-5 text-sm text-emerald-950">
      <div className="flex items-center gap-2 font-black uppercase tracking-[0.18em] text-emerald-700">
        <ShieldCheck className="h-4 w-4" /> This answer is evidence-bound
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        <TrustLine label="Claim boundary" value={claimBoundary || "Advisory; approval required before action"} />
        <TrustLine label="Evidence seal" value={seal || "Awaiting live evidence seal"} />
        <TrustLine label="Invariants" value={invariantStatus || "Fail-closed until verified"} />
        <TrustLine label="Data source" value={source || "Live telemetry only; no fabricated data"} />
      </div>
      <p className="mt-4 flex items-center gap-2 text-xs font-semibold text-emerald-800">
        <FileCheck2 className="h-4 w-4" /> Human approval is required before high-risk execution.
      </p>
    </div>
  );
}

function TrustLine({ label, value }: { label: string; value: string }) {
  return <div><p className="text-xs uppercase tracking-[0.16em] text-emerald-700">{label}</p><p className="mt-1 font-mono text-emerald-950">{value}</p></div>;
}
