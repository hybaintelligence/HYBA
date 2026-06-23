import React, { createContext, useContext, useMemo, useState } from "react";

export type SkillMode = "executive" | "business" | "operator" | "analyst" | "engineer" | "auditor" | "expert";

export interface SkillModeProfile {
  mode: SkillMode;
  label: string;
  lens: string;
  density: "guided" | "balanced" | "technical";
  showTechnicalDefaults: boolean;
  evidenceFirst: boolean;
  actionFocus: boolean;
}

const PROFILES: Record<SkillMode, Omit<SkillModeProfile, "mode">> = {
  executive: { label: "Boardroom", lens: "Decision, risk, confidence, and approval posture.", density: "guided", showTechnicalDefaults: false, evidenceFirst: true, actionFocus: true },
  business: { label: "Business", lens: "Plain-English outcomes, safe defaults, and workflow intent.", density: "guided", showTechnicalDefaults: false, evidenceFirst: true, actionFocus: true },
  operator: { label: "Operator", lens: "Degraded workflows, remediation proposals, blast radius, and approvals.", density: "balanced", showTechnicalDefaults: false, evidenceFirst: true, actionFocus: true },
  analyst: { label: "Analyst", lens: "Drivers, counterfactuals, assumptions, sensitivity, and evidence chains.", density: "balanced", showTechnicalDefaults: false, evidenceFirst: true, actionFocus: false },
  engineer: { label: "Engineer", lens: "API traces, payloads, invariants, latency, and failure modes.", density: "technical", showTechnicalDefaults: true, evidenceFirst: false, actionFocus: false },
  auditor: { label: "Auditor", lens: "Claim boundaries, seals, invariant checks, policy, and audit readiness.", density: "balanced", showTechnicalDefaults: false, evidenceFirst: true, actionFocus: false },
  expert: { label: "Expert", lens: "φ-resonance, code distance, substrate coherence, and quantum/causal trace.", density: "technical", showTechnicalDefaults: true, evidenceFirst: true, actionFocus: false },
};

interface AdaptiveExperienceContextValue {
  skillMode: SkillMode;
  setSkillMode: (mode: SkillMode) => void;
  profile: SkillModeProfile;
}

const AdaptiveExperienceContext = createContext<AdaptiveExperienceContextValue | null>(null);

export function AdaptiveExperienceProvider({ children }: { children: React.ReactNode }) {
  const [skillMode, setSkillMode] = useState<SkillMode>(() => {
    try {
      const stored = localStorage.getItem("hyba_skill_mode") as SkillMode | null;
      return stored && stored in PROFILES ? stored : "business";
    } catch {
      return "business";
    }
  });

  const value = useMemo(() => {
    const wrappedSetSkillMode = (mode: SkillMode) => {
      setSkillMode(mode);
      try { localStorage.setItem("hyba_skill_mode", mode); } catch {}
    };
    return { skillMode, setSkillMode: wrappedSetSkillMode, profile: { mode: skillMode, ...PROFILES[skillMode] } };
  }, [skillMode]);

  return <AdaptiveExperienceContext.Provider value={value}>{children}</AdaptiveExperienceContext.Provider>;
}

export function useAdaptiveExperience() {
  const context = useContext(AdaptiveExperienceContext);
  if (!context) throw new Error("useAdaptiveExperience must be used inside AdaptiveExperienceProvider");
  return context;
}

export const SKILL_MODES = Object.entries(PROFILES).map(([mode, profile]) => ({ mode: mode as SkillMode, ...profile }));

export function SkillModeSelector() {
  const { skillMode, setSkillMode, profile } = useAdaptiveExperience();
  return (
    <div className="rounded-2xl border border-white/20 bg-white/10 p-3 text-white shadow-lg" data-testid="skill-mode-selector">
      <label className="block text-[10px] font-semibold uppercase tracking-[0.28em] text-blue-100/80">Adaptive lens</label>
      <select value={skillMode} onChange={(event) => setSkillMode(event.target.value as SkillMode)} className="mt-1 w-full rounded-lg border border-white/20 bg-slate-900/80 px-2 py-1 text-xs font-semibold text-white">
        {SKILL_MODES.map((mode) => <option key={mode.mode} value={mode.mode}>{mode.label}</option>)}
      </select>
      <p className="mt-1 max-w-56 text-[10px] leading-4 text-blue-50/75">{profile.lens}</p>
    </div>
  );
}
