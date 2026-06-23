import React from "react";
import { Brain, CheckCircle2, FileWarning, ShieldCheck, Sparkles } from "lucide-react";

export type HybaRailSurface = {
  surfaceId: string;
  title: string;
  state: string;
  observation: string;
  recommendation: string;
  clientValue: string;
  risk: "low" | "medium" | "high";
  confidence: number;
  approvalRequired: boolean;
  evidence: string[];
};

export type HybaIntelligenceRailProps = {
  surfaces?: HybaRailSurface[];
  compact?: boolean;
};

const defaultSurfaces: HybaRailSurface[] = [
  {
    surfaceId: "proof_and_claim_interrogation",
    title: "Evidence-backed recommendations",
    state: "ready",
    observation: "HYBA binds material claims to proof windows, invariants, tests, and evidence seals.",
    recommendation: "Show evidence beside every client recommendation and fail closed when proof is unavailable.",
    clientValue: "Clients can interrogate HYBA instead of taking the pitch on trust.",
    risk: "low",
    confidence: 0.96,
    approvalRequired: false,
    evidence: ["/api/proofs", "/api/proofs/autonomy-fabric", "/api/proofs/audit-ledger"],
  },
  {
    surfaceId: "client_onboarding_diagnostic",
    title: "Client opportunity scan",
    state: "ready",
    observation: "Client context, data posture, deployment constraints, and governance needs are mapped into one diagnostic.",
    recommendation: "Generate an executive opportunity brief with next-best-actions and proof references.",
    clientValue: "Discovery moves from bespoke consulting effort to repeatable autonomous intelligence.",
    risk: "low",
    confidence: 0.93,
    approvalRequired: false,
    evidence: ["hyba_ciaas.ingestion", "tests/test_central_data_ingestion.py"],
  },
  {
    surfaceId: "production_execution_guardrails",
    title: "Approval-safe autonomous action",
    state: "approval gated",
    observation: "High-impact commands such as production execution, privileged admin changes, and data export require approval.",
    recommendation: "Simulate first, request approval, execute only after approval, then audit the result.",
    clientValue: "The system can act without becoming reckless or opaque.",
    risk: "high",
    confidence: 0.9,
    approvalRequired: true,
    evidence: ["artifacts/frontend_api_command_manifest.json", "tests/e2e/command-safety.spec.ts"],
  },
];

function pct(value: number): string {
  return Number.isFinite(value) ? `${Math.round(value * 100)}%` : "—";
}

function riskClass(risk: HybaRailSurface["risk"]): string {
  if (risk === "high") return "border-red-300 bg-red-50 text-red-900";
  if (risk === "medium") return "border-amber-300 bg-amber-50 text-amber-900";
  return "border-emerald-300 bg-emerald-50 text-emerald-900";
}

export function HybaIntelligenceRail({ surfaces = defaultSurfaces, compact = false }: HybaIntelligenceRailProps) {
  const approvalGated = surfaces.filter((surface) => surface.approvalRequired).length;
  const autonomous = surfaces.length - approvalGated;

  return (
    <section
      aria-label="HYBA Intelligence Rail"
      className="rounded-[1.75rem] border border-indigo-200 bg-white/95 p-5 text-slate-950 shadow-xl shadow-indigo-950/10"
    >
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p className="font-mono text-[10px] font-bold uppercase tracking-[0.28em] text-indigo-600">
            HYBA_INTELLIGENCE_RAIL
          </p>
          <h2 className="mt-2 flex items-center gap-2 text-xl font-black text-slate-950">
            <Brain className="h-5 w-5 text-indigo-600" /> HYBA Intelligence Rail
          </h2>
          <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-600">
            Observe → Reason → Recommend → Simulate → Approve → Execute → Audit → Learn.
            Every client surface should show what HYBA sees, recommends, can safely automate,
            what needs approval, and what evidence supports the recommendation.
          </p>
        </div>
        <div className="grid grid-cols-3 gap-2 font-mono text-[10px] uppercase tracking-[0.16em] text-slate-600">
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3 text-center">
            <strong className="block text-lg text-slate-950">{surfaces.length}</strong>
            Surfaces
          </div>
          <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-3 text-center text-emerald-900">
            <strong className="block text-lg">{autonomous}</strong>
            Autonomous
          </div>
          <div className="rounded-2xl border border-amber-200 bg-amber-50 p-3 text-center text-amber-900">
            <strong className="block text-lg">{approvalGated}</strong>
            Approval gated
          </div>
        </div>
      </div>

      <div className={`mt-5 grid gap-3 ${compact ? "lg:grid-cols-3" : "xl:grid-cols-3"}`}>
        {surfaces.map((surface) => (
          <article
            key={surface.surfaceId}
            className="rounded-2xl border border-slate-200 bg-slate-50/80 p-4"
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="text-sm font-black text-slate-950">{surface.title}</h3>
                <p className="mt-1 font-mono text-[10px] uppercase tracking-[0.16em] text-slate-500">
                  {surface.state} · confidence {pct(surface.confidence)}
                </p>
              </div>
              <span className={`rounded-full border px-2 py-1 font-mono text-[10px] font-bold uppercase ${riskClass(surface.risk)}`}>
                {surface.risk}
              </span>
            </div>
            <p className="mt-3 text-xs leading-5 text-slate-600">
              <Sparkles className="mr-1 inline h-3.5 w-3.5 text-indigo-500" />
              {surface.observation}
            </p>
            <p className="mt-2 text-xs leading-5 text-slate-700">
              <CheckCircle2 className="mr-1 inline h-3.5 w-3.5 text-emerald-600" />
              {surface.recommendation}
            </p>
            <p className="mt-2 text-xs leading-5 font-semibold text-slate-800">
              Client value: {surface.clientValue}
            </p>
            <div className="mt-3 rounded-xl border border-white bg-white p-3 font-mono text-[10px] leading-5 text-slate-600">
              <p className="flex items-center gap-1 font-bold uppercase tracking-[0.14em] text-slate-900">
                {surface.approvalRequired ? (
                  <FileWarning className="h-3.5 w-3.5 text-amber-600" />
                ) : (
                  <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
                )}
                {surface.approvalRequired ? "Approval required" : "Autonomous with audit"}
              </p>
              <p className="mt-1 truncate">Evidence: {surface.evidence.join(" · ")}</p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

export default HybaIntelligenceRail;
