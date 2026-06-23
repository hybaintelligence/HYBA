/**
 * DecisionCockpit Component - Global Shell for Intelligence Operating System
 *
 * Replaces the generic dashboard for non-expert users with a structured decision interface.
 * Implements the plan's Section pattern for organized intelligence presentation.
 */

import React from "react";
import { CheckCircle2, Cpu, Minus, ShieldCheck, TrendingDown, TrendingUp } from "lucide-react";
import { AdaptiveMetric } from "./AdaptiveMetric";
import { ActionGuard } from "./ActionGuard";
import { calculateBlastRadius, type ProposedAction } from "../utils/blastRadius";

interface DecisionCockpitProps {
  stability?: number | null;
  previousStability?: number | null;
  veracity?: "quantum" | "fallback";
  telemetrySource?: string;
}

interface SectionProps {
  title: string;
  children: React.ReactNode;
  className?: string;
}

function Section({ title, children, className = "" }: SectionProps) {
  return (
    <section className={`rounded-2xl border border-slate-200 bg-white/90 p-6 shadow-sm ${className}`}>
      <h3 className="text-lg font-bold text-slate-950 mb-4">{title}</h3>
      {children}
    </section>
  );
}

export function DecisionCockpit({
  stability = null,
  previousStability = null,
  veracity = "fallback",
  telemetrySource = "unavailable",
}: DecisionCockpitProps) {
  const delta = typeof stability === "number" && typeof previousStability === "number" ? stability - previousStability : null;
  const trend = delta == null ? "insufficient samples" : delta > 0.005 ? "converging" : delta < -0.005 ? "degrading" : "stable";
  const TrendIcon = trend === "converging" ? TrendingUp : trend === "degrading" ? TrendingDown : Minus;

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-8">
      {/* Header: Skill Mode Selection */}
      <header className="flex justify-between items-center border-b border-slate-200 pb-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-950">Intelligence Cockpit</h1>
          <p className="text-slate-600 mt-1">Adaptive Operating System for HYBA Intelligence</p>
        </div>
      </header>

      {/* Top Level: The "Why" and "What" */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Section title="Active Invariants">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <AdaptiveMetric metricKey="phi_resonance" value={stability ? (stability * 100).toFixed(2) : "—"} unit="%" />
              <AdaptiveMetric metricKey="substrate_coherence" value={trend === "stable" ? "STRONG" : trend.toUpperCase()} />
            </div>
          </Section>

          <Section title="Intelligence Actions">
            {/* Example pending action */}
            <ActionGuard
              action={{
                command: "Apply phase-alignment correction to Substrate-A",
                type: "configure",
                scope: "tenant",
              }}
              blastRadius={calculateBlastRadius({
                command: "Apply phase-alignment correction to Substrate-A",
                type: "configure",
                scope: "tenant",
              })}
              onApprove={() => console.log("Approved")}
              onReject={() => console.log("Rejected")}
              evidenceSeal="seal-abc123"
              invariantStatus="passed"
            />
          </Section>
        </div>

        {/* The Side Rail: Intelligence Trend */}
        <div className="space-y-6">
          <Section title="Intelligence Trend">
            <div className="space-y-4">
              <div
                className={`rounded-2xl border p-4 text-sm ${
                  veracity === "quantum"
                    ? "border-emerald-200 bg-emerald-50 text-emerald-950"
                    : "border-amber-200 bg-amber-50 text-amber-950"
                }`}
              >
                <Cpu className="mr-2 inline h-4 w-4" />
                <strong>{veracity === "quantum" ? "Quantum-backed certainty" : "Classical heuristic fallback"}</strong>
                <p className="mt-2 text-xs leading-5">
                  {veracity === "quantum"
                    ? "Live source, evidence seal, and invariants are present for board-safe review."
                    : "Use as triage until live backing and proof checks are restored."}
                </p>
              </div>

              <div className="rounded-2xl border border-blue-200 bg-blue-50 p-4 text-sm text-blue-950">
                <TrendIcon className="mr-2 inline h-4 w-4" />
                <strong>Intelligence trend: {trend}</strong>
                <p className="mt-2 text-xs leading-5">
                  Current stability {typeof stability === "number" ? `${(stability * 100).toFixed(2)}%` : "—"}; previous{" "}
                  {typeof previousStability === "number" ? `${(previousStability * 100).toFixed(2)}%` : "—"}.
                </p>
              </div>

              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
                <ShieldCheck className="mr-2 inline h-4 w-4" />
                <strong>Real telemetry contract</strong>
                <p className="mt-2 text-xs leading-5">Source: {telemetrySource}. HYBA renders unavailable fields as "—" instead of fabricating samples.</p>
              </div>
            </div>
          </Section>
        </div>
      </div>

      {/* Decision Packet Structure */}
      <Section title="Decision Packet Structure">
        <div className="grid gap-2 md:grid-cols-3 lg:grid-cols-4">
          {[
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
          ].map((row) => (
            <div
              key={row}
              className="rounded-xl border border-slate-100 bg-slate-50 px-3 py-2 text-xs font-bold text-slate-700"
            >
              {row}
            </div>
          ))}
        </div>
      </Section>
    </div>
  );
}
