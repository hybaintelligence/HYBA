import React, { createContext, useContext, useMemo, useState } from "react";

export type SkillMode =
  | "executive"
  | "business"
  | "operator"
  | "analyst"
  | "engineer"
  | "auditor"
  | "expert";

type SkillModeContextValue = {
  skillMode: SkillMode;
  setSkillMode: (mode: SkillMode) => void;
  isExpertMode: boolean;
  isAuditorMode: boolean;
};

const SkillModeContext = createContext<SkillModeContextValue | null>(null);

export const SKILL_MODE_LABELS: Record<SkillMode, string> = {
  executive: "Boardroom",
  business: "Business",
  operator: "Operator",
  analyst: "Analyst",
  engineer: "Engineer",
  auditor: "Auditor",
  expert: "Quantum / causal expert",
};

export function SkillModeProvider({ children }: { children: React.ReactNode }) {
  const [skillMode, setSkillModeState] = useState<SkillMode>(() => {
    try {
      return (localStorage.getItem("hyba_skill_mode") as SkillMode) || "business";
    } catch {
      return "business";
    }
  });

  const setSkillMode = (mode: SkillMode) => {
    setSkillModeState(mode);
    try {
      localStorage.setItem("hyba_skill_mode", mode);
    } catch {
      // localStorage may be unavailable under test or hardened browser settings.
    }
  };

  const value = useMemo(
    () => ({
      skillMode,
      setSkillMode,
      isExpertMode: skillMode === "engineer" || skillMode === "expert",
      isAuditorMode: skillMode === "auditor",
    }),
    [skillMode],
  );

  return <SkillModeContext.Provider value={value}>{children}</SkillModeContext.Provider>;
}

export function useSkillMode() {
  const value = useContext(SkillModeContext);
  if (!value) {
    throw new Error("useSkillMode must be used inside SkillModeProvider");
  }
  return value;
}

export function SkillModeSelector() {
  const { skillMode, setSkillMode } = useSkillMode();
  return (
    <label className="flex items-center gap-2 rounded-full border border-slate-200 bg-white/90 px-3 py-2 text-xs font-semibold text-slate-700 shadow-sm">
      Cognitive lens
      <select
        value={skillMode}
        onChange={(event) => setSkillMode(event.target.value as SkillMode)}
        className="bg-transparent font-mono text-xs text-slate-900 outline-none"
        aria-label="Cognitive lens"
      >
        {Object.entries(SKILL_MODE_LABELS).map(([value, label]) => (
          <option key={value} value={value}>
            {label}
          </option>
        ))}
      </select>
    </label>
  );
}
