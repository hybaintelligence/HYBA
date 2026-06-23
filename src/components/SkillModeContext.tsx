import React, { createContext, useContext, useMemo, useState } from "react";

export type SkillMode = "executive" | "business" | "operator" | "analyst" | "engineer" | "auditor" | "expert";

const MODES: Record<SkillMode, { label: string; description: string; complexity: "plain" | "operational" | "evidence" | "technical" }> = {
  executive: { label: "Boardroom", description: "Decision impact, confidence, risk, and approval posture.", complexity: "plain" },
  business: { label: "Business", description: "Plain-English meaning, recommended defaults, and buyer-safe language.", complexity: "plain" },
  operator: { label: "Operator", description: "Degraded workflows, blast radius, remediation proposals, and approvals.", complexity: "operational" },
  analyst: { label: "Analyst", description: "Drivers, counterfactuals, assumptions, and sensitivity.", complexity: "operational" },
  engineer: { label: "Engineer", description: "API payloads, raw parameters, traces, and failure modes.", complexity: "technical" },
  auditor: { label: "Auditor", description: "Claim boundaries, evidence seals, invariants, and governance tags.", complexity: "evidence" },
  expert: { label: "Expert", description: "φ-resonance, code distance, substrate coherence, and specialist controls.", complexity: "technical" },
};

interface SkillModeContextValue {
  mode: SkillMode;
  setMode: (mode: SkillMode) => void;
  modes: typeof MODES;
  showTechnicalControls: boolean;
  showEvidenceFirst: boolean;
}

const SkillModeContext = createContext<SkillModeContextValue | undefined>(undefined);

export function SkillModeProvider({ children }: { children: React.ReactNode }) {
  const [mode, setModeState] = useState<SkillMode>(() => {
    const saved = localStorage.getItem("hyba_skill_mode");
    return saved && saved in MODES ? (saved as SkillMode) : "business";
  });

  const setMode = (next: SkillMode) => {
    localStorage.setItem("hyba_skill_mode", next);
    setModeState(next);
  };

  const value = useMemo(
    () => ({
      mode,
      setMode,
      modes: MODES,
      showTechnicalControls: mode === "engineer" || mode === "expert",
      showEvidenceFirst: mode === "auditor" || mode === "expert",
    }),
    [mode],
  );

  return <SkillModeContext.Provider value={value}>{children}</SkillModeContext.Provider>;
}

export function useSkillMode() {
  const context = useContext(SkillModeContext);
  if (!context) throw new Error("useSkillMode must be used within SkillModeProvider");
  return context;
}

export function SkillModeSelector() {
  const { mode, setMode, modes } = useSkillMode();
  return (
    <label className="flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3 py-1.5 text-xs text-white">
      <span className="font-semibold uppercase tracking-[0.18em] text-white/60">Lens</span>
      <select
        value={mode}
        onChange={(event) => setMode(event.target.value as SkillMode)}
        className="bg-transparent font-semibold text-white outline-none [&_option]:bg-slate-900"
        aria-label="Adaptive intelligence skill mode"
      >
        {Object.entries(modes).map(([key, meta]) => (
          <option key={key} value={key}>{meta.label}</option>
        ))}
      </select>
    </label>
  );
}
