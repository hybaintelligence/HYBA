import React, { useState } from "react";
import { Brain, CheckCircle2, ChevronDown, FileWarning, ShieldCheck, Sparkles, TrendingDown, TrendingUp, Minus, Cpu } from "lucide-react";
import { metricTranslations, type MetricTranslationKey } from "../intelligenceTranslations";
import { useSkillMode } from "../skillMode";

const workflowTemplates = [
  {
    intent: "Explain a board-level decision",
    capability: "explain + evidence package",
    action: "Prepare advisory memo",
    approval: "Human approval required before action",
  },
  {
    intent: "Detect operational risk",
    capability: "orchestrate + substrate health",
    action: "Open degradation triage",
    approval: "Operator approval required",
  },
  {
    intent: "Simulate an intervention",
    capability: "counterfactual + simulate",
    action: "Run bounded simulation",
    approval: "No write access during simulation",
  },
  {
    intent: "Audit an AI recommendation",
    capability: "governance_audit + evidence package",
    action: "Generate proof explainer",
    approval: "Auditor review required",
  },
];

export function SkillModeSelector() {
  const { mode, setMode, config, modes } = useSkillMode();
  return (
    <div className="rounded-2xl border border-white/15 bg-white/10 p-2 text-white">
      <label className="block text-[9px] font-bold uppercase tracking-[0.22em] text-blue-100/70">
        Cognitive lens
      </label>
      <select
        value={mode}
        onChange={(event) => setMode(event.target.value as typeof mode)}
        className="mt-1 w-full rounded-lg border border-white/20 bg-[#06162D] px-2 py-1.5 text-xs font-semibold text-white outline-none"
        aria-label="Adaptive skill mode"
      >
        {modes.map((item) => (
          <option key={item.mode} value={item.mode}>
            {item.label}
          </option>
        ))}
      </select>
      <p className="mt-1 max-w-48 text-[10px] leading-4 text-blue-100/70">{config.description}</p>
    </div>
  );
}

export function MetricExplainerCard({
  metricKey,
  value,
}: {
  metricKey: MetricTranslationKey;
  value?: string;
}) {
  const { mode, config } = useSkillMode();
  const [open, setOpen] = useState(config.evidenceFirst || config.showTechnicalDefaults);
  const item = metricTranslations[metricKey][mode] || metricTranslations[metricKey].business;
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">
            {value || "Intelligence translator"}
          </p>
          <h4 className="mt-1 text-sm font-black text-slate-950">
            {config.showTechnicalDefaults ? item.expert : item.label}
          </h4>
        </div>
        <button
          type="button"
          onClick={() => setOpen(!open)}
          className="rounded-full bg-slate-100 p-1 text-slate-600"
          aria-label="Toggle evidence details"
        >
          <ChevronDown className={`h-4 w-4 transition ${open ? "rotate-180" : ""}`} />
        </button>
      </div>
      <p className="mt-3 text-sm leading-6 text-slate-600">{item.plainEnglish}</p>
      <div className="mt-3 rounded-xl border border-blue-100 bg-blue-50 p-3 text-xs leading-5 text-blue-950">
        <strong>What HYBA recommends:</strong> {item.operationalImplication}
      </div>
      {open && (
        <div className="mt-3 grid gap-3 md:grid-cols-2">
          <div className="rounded-xl border border-emerald-100 bg-emerald-50 p-3 text-xs leading-5 text-emerald-950">
            <strong>Evidence view:</strong> {item.evidenceView}
          </div>
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 font-mono text-[11px] leading-5 text-slate-700">
            <strong>Expert:</strong> {item.expert}
          </div>
        </div>
      )}
    </div>
  );
}

export function ProofExplainer({
  seal,
  invariantSummary,
  source,
}: {
  seal: string;
  invariantSummary: string;
  source: string;
}) {
  return (
    <div className="rounded-3xl border border-amber-200 bg-amber-50 p-5">
      <div className="flex items-center gap-2 text-amber-900">
        <ShieldCheck className="h-5 w-5" />
        <h3 className="font-black">This answer is evidence-bound</h3>
      </div>
      <div className="mt-4 grid gap-3 text-sm md:grid-cols-2 lg:grid-cols-5">
        <TrustFact label="Claim boundary" value="Advisory, not autonomous execution" />
        <TrustFact label="Evidence seal" value={seal} />
        <TrustFact label="Invariants" value={invariantSummary} />
        <TrustFact label="Data source" value={source} />
        <TrustFact label="Approval" value="Human approval required before action" />
      </div>
    </div>
  );
}

function TrustFact({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-amber-200 bg-white/80 p-3">
      <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-amber-700">{label}</p>
      <p className="mt-1 font-mono text-xs text-slate-900">{value}</p>
    </div>
  );
}

export function UseCaseStudio() {
  return (
    <section className="rounded-[2rem] border border-slate-200 bg-white/90 p-5 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-[10px] font-black uppercase tracking-[0.22em] text-slate-400">
            Use-case studio
          </p>
          <h2 className="text-xl font-black text-slate-950">
            Start from intent, not raw substrate controls
          </h2>
        </div>
        <span className="rounded-full bg-purple-100 px-3 py-1 text-xs font-bold text-purple-800">
          <Sparkles className="mr-1 inline h-3.5 w-3.5" /> one substrate · many workflows
        </span>
      </div>
      <div className="mt-5 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {workflowTemplates.map((workflow) => (
          <div
            key={workflow.intent}
            className="rounded-2xl border border-slate-200 bg-slate-50 p-4"
          >
            <Brain className="h-5 w-5 text-purple-600" />
            <h3 className="mt-3 text-sm font-black text-slate-950">{workflow.intent}</h3>
            <p className="mt-2 text-xs leading-5 text-slate-600">
              Maps to: <strong>{workflow.capability}</strong>
            </p>
            <p className="mt-2 text-xs leading-5 text-slate-600">
              Next safe action: <strong>{workflow.action}</strong>
            </p>
            <p className="mt-3 rounded-xl border border-amber-200 bg-amber-50 p-2 text-[11px] font-semibold text-amber-900">
              <FileWarning className="mr-1 inline h-3.5 w-3.5" />
              {workflow.approval}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}

export function DecisionCockpit({
  stability = null,
  previousStability = null,
  veracity = "fallback",
  telemetrySource = "unavailable",
}: {
  stability?: number | null;
  previousStability?: number | null;
  veracity?: "quantum" | "fallback";
  telemetrySource?: string;
}) {
  const delta = typeof stability === "number" && typeof previousStability === "number" ? stability - previousStability : null;
  const trend = delta == null ? "insufficient samples" : delta > 0.005 ? "converging" : delta < -0.005 ? "degrading" : "stable";
  const TrendIcon = trend === "converging" ? TrendingUp : trend === "degrading" ? TrendingDown : Minus;
  const rows = [
    "Current state",
    "Anomaly",
    "Causal drivers",
    "Counterfactual options",
    "Recommended action",
    "Risk",
    "Blast radius",
    "Evidence",
    "Approval requirement",
    "Expected outcome",
    "Rollback plan",
  ];
  return (
    <section className="rounded-[2rem] border border-slate-200 bg-white/90 p-5 shadow-sm">
      <div className="flex items-center gap-2">
        <CheckCircle2 className="h-5 w-5 text-emerald-600" />
        <h2 className="text-xl font-black text-slate-950">Decision cockpit</h2>
      </div>
      <p className="mt-2 text-sm leading-6 text-slate-600">
        Every recommendation is structured as a governed decision packet before execution, with veracity and temporal trend signals attached.
      </p>
      <div className="mt-4 grid gap-3 md:grid-cols-3">
        <div className={`rounded-2xl border p-3 text-sm ${veracity === "quantum" ? "border-emerald-200 bg-emerald-50 text-emerald-950" : "border-amber-200 bg-amber-50 text-amber-950"}`}>
          <Cpu className="mr-1 inline h-4 w-4" />
          <strong>{veracity === "quantum" ? "Quantum-backed certainty" : "Classical heuristic fallback"}</strong>
          <p className="mt-1 text-xs leading-5">{veracity === "quantum" ? "Live source, evidence seal, and invariants are present for board-safe review." : "Use as triage until live backing and proof checks are restored."}</p>
        </div>
        <div className="rounded-2xl border border-blue-200 bg-blue-50 p-3 text-sm text-blue-950">
          <TrendIcon className="mr-1 inline h-4 w-4" />
          <strong>Intelligence trend: {trend}</strong>
          <p className="mt-1 text-xs leading-5">Current stability {typeof stability === "number" ? `${(stability * 100).toFixed(2)}%` : "—"}; previous {typeof previousStability === "number" ? `${(previousStability * 100).toFixed(2)}%` : "—"}.</p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3 text-sm text-slate-700">
          <ShieldCheck className="mr-1 inline h-4 w-4" />
          <strong>Real telemetry contract</strong>
          <p className="mt-1 text-xs leading-5">Source: {telemetrySource}. HYBA renders unavailable fields as “—” instead of fabricating samples.</p>
        </div>
      </div>
      <div className="mt-4 grid gap-2 md:grid-cols-3 lg:grid-cols-4">
        {rows.map((row) => (
          <div
            key={row}
            className="rounded-xl border border-slate-100 bg-slate-50 px-3 py-2 text-xs font-bold text-slate-700"
          >
            {row}
          </div>
        ))}
      </div>
    </section>
  );
}
