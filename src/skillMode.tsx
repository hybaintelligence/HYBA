import React, { createContext, useContext, useMemo, useState } from "react";

export type SkillMode =
  | "executive"
  | "business"
  | "operator"
  | "analyst"
  | "engineer"
  | "auditor"
  | "expert";

export const SKILL_MODE_LABELS: Record<SkillMode, string> = {
  executive: "Boardroom",
  business: "Business",
  operator: "Operator",
  analyst: "Analyst",
  engineer: "Engineer",
  auditor: "Auditor",
  expert: "Quantum / causal expert",
};

type SkillModeConfig = {
  mode: SkillMode;
  label: string;
  description: string;
  density: "summary" | "balanced" | "technical";
  showTechnicalDefaults: boolean;
  evidenceFirst: boolean;
  actionFirst: boolean;
};

const CONFIG: Record<SkillMode, Omit<SkillModeConfig, "mode">> = {
  executive: {
    label: "Boardroom",
    description: "Decision, risk, confidence, approval requirement.",
    density: "summary",
    showTechnicalDefaults: false,
    evidenceFirst: false,
    actionFirst: true,
  },
  business: {
    label: "Business",
    description: "Plain-English operating guidance and commercial impact.",
    density: "summary",
    showTechnicalDefaults: false,
    evidenceFirst: false,
    actionFirst: true,
  },
  operator: {
    label: "Operator",
    description: "Degraded workflows, safe actions, blast radius, rollback.",
    density: "balanced",
    showTechnicalDefaults: false,
    evidenceFirst: false,
    actionFirst: true,
  },
  analyst: {
    label: "Analyst",
    description: "Drivers, assumptions, counterfactuals, sensitivity, evidence.",
    density: "balanced",
    showTechnicalDefaults: false,
    evidenceFirst: true,
    actionFirst: false,
  },
  engineer: {
    label: "Engineer",
    description: "Raw parameters, traces, payloads, latency, failure modes.",
    density: "technical",
    showTechnicalDefaults: true,
    evidenceFirst: false,
    actionFirst: false,
  },
  auditor: {
    label: "Auditor",
    description: "Claim boundary, seal, invariants, source, governance policy.",
    density: "balanced",
    showTechnicalDefaults: false,
    evidenceFirst: true,
    actionFirst: false,
  },
  expert: {
    label: "Expert",
    description: "φ-resonance, code distance, substrate coherence, quantum controls.",
    density: "technical",
    showTechnicalDefaults: true,
    evidenceFirst: true,
    actionFirst: false,
  },
};

const STORAGE_KEY = "hyba_skill_mode";

const SkillModeContext = createContext<{
  mode: SkillMode;
  skillMode: SkillMode;
  setMode: (mode: SkillMode) => void;
  setSkillMode: (mode: SkillMode) => void;
  config: SkillModeConfig;
  modes: SkillModeConfig[];
  isExpertMode: boolean;
  isAuditorMode: boolean;
} | null>(null);

function readInitialMode(): SkillMode {
  try {
    const stored = localStorage.getItem(STORAGE_KEY) as SkillMode | null;
    if (stored && stored in CONFIG) return stored;
  } catch {
    // localStorage can be unavailable in SSR/tests; default is safe business mode.
  }
  return "business";
}

export function SkillModeProvider({ children }: { children: React.ReactNode }) {
  const [mode, setModeState] = useState<SkillMode>(readInitialMode);
  const setMode = (next: SkillMode) => {
    setModeState(next);
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      // Persistence is best-effort only.
    }
  };
  const modes = useMemo(
    () => (Object.keys(CONFIG) as SkillMode[]).map((key) => ({ mode: key, ...CONFIG[key] })),
    [],
  );
  const config = useMemo(() => ({ mode, ...CONFIG[mode] }), [mode]);
  const isExpertMode = useMemo(() => mode === "engineer" || mode === "expert", [mode]);
  const isAuditorMode = useMemo(() => mode === "auditor", [mode]);
  return (
    <SkillModeContext.Provider value={{
      mode,
      skillMode: mode,
      setMode,
      setSkillMode: setMode,
      config,
      modes,
      isExpertMode,
      isAuditorMode
    }}>
      {children}
    </SkillModeContext.Provider>
  );
}

export function useSkillMode() {
  const ctx = useContext(SkillModeContext);
  if (!ctx) throw new Error("useSkillMode must be used within SkillModeProvider");
  return ctx;
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
