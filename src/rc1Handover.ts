export type UatStageId =
  | "executive-lens"
  | "operational-self-healing"
  | "strategic-crisis-simulation"
  | "forensic-trust-audit";

export interface Rc1UatStage {
  id: UatStageId;
  title: string;
  clientAction: string;
  validation: string[];
  acceptanceGoal: string;
  evidenceArtifacts: string[];
}

export interface Rc1AgentSignoff {
  agent: string;
  role: string;
  readyStatement: string;
  evidenceRefs: string[];
}

export interface Rc1KickoffCheck {
  id: string;
  label: string;
  verification: string;
  evidenceRefs: string[];
}

export const rc1UatGoldenPath: Rc1UatStage[] = [
  {
    id: "executive-lens",
    title: "Executive Lens Validation",
    clientAction: "Client logs in as CEO or board member and reviews the Decision Cockpit.",
    validation: [
      "Executive lens uses persisted SkillModeProvider role defaults.",
      "Emerald CI and Violet QI readiness indicators are visible in plain English.",
      "Real Telemetry Contract confirms live substrate truth via the same-origin API bridge.",
    ],
    acceptanceGoal: "Prove the specialist gap is closed for non-technical executives.",
    evidenceArtifacts: ["role-mode persistence", "bridge health", "telemetry source provenance"],
  },
  {
    id: "operational-self-healing",
    title: "Operational Self-Healing (CIaaS)",
    clientAction: "Client observes a Salamander regeneration or self-healing startup event.",
    validation: [
      "Emerald Manager shows the regeneration event as a proposal, not an unattended write.",
      "φ-density is translated as Reasoning Maturity.",
      "Reflexive cycles are translated as Logic Refinement.",
    ],
    acceptanceGoal: "Prove the substrate is resilient, self-optimizing, and human-governed.",
    evidenceArtifacts: ["pre/post φ-density", "reflexive cycle logs", "proposal boundary"],
  },
  {
    id: "strategic-crisis-simulation",
    title: "Strategic Crisis Simulation (QIaaS)",
    clientAction: "Client uses the Counterfactual Sandbox for sovereign risk or market shock.",
    validation: [
      "Quantum rail recalculates φ-resonance from live telemetry context.",
      "Multi-agent war room displays reasoning contributions and stability consensus.",
      "Simulation remains explicitly proposal-only until human approval.",
    ],
    acceptanceGoal: "Prove HYBA provides evidence-bound strategic certainty beyond a dashboard.",
    evidenceArtifacts: ["scenario inputs", "reasoning stability", "human approval boundary"],
  },
  {
    id: "forensic-trust-audit",
    title: "Forensic Trust Audit (Governance)",
    clientAction: "Client downloads the evidence package for the simulation they just ran.",
    validation: [
      "Package contains the Evidence Seal, invariant logs, and sovereignty telemetry.",
      "Package signature is SHA-256 digest-backed and portable as JSON/PDF.",
      "Human-in-the-loop policy is preserved as no_unattended_writes.",
    ],
    acceptanceGoal: "Prove the system is auditable and defensible for client acceptance.",
    evidenceArtifacts: [
      "evidence seal",
      "invariant logs",
      "sovereignty telemetry",
      "signature digest",
    ],
  },
];

export const rc1AgentSignoffs: Rc1AgentSignoff[] = [
  {
    agent: "Agent 1",
    role: "UX Architect",
    readyStatement:
      "The SkillModeProvider is persistent. Every acceptance view has an Executive lens, and the API bridge is active. READY.",
    evidenceRefs: ["src/skillMode.tsx", "src/hooks/useLatencyMetrics.ts", "src/App.tsx"],
  },
  {
    agent: "Agent 2",
    role: "Translator",
    readyStatement:
      "The metric dictionary covers backend self-healing signals: φ-density is Reasoning Maturity and Reflexive Cycles are Logic Refinement. READY.",
    evidenceRefs: ["src/intelligenceTranslations.ts"],
  },
  {
    agent: "Agent 3",
    role: "Governance Guard",
    readyStatement:
      "The proposal-only assistant boundary is the gatekeeper; client-rail execution requires human-in-the-loop approval. READY.",
    evidenceRefs: ["src/governance.ts", "src/App.tsx"],
  },
  {
    agent: "Agent 4",
    role: "Orchestrator",
    readyStatement:
      "The handover logic is confirmed: CI rail anomalies can feed QI rail simulations while retaining evidence and governance boundaries. READY.",
    evidenceRefs: ["src/App.tsx", "src/rc1Handover.ts"],
  },
];

export const rc1KickoffChecklist: Rc1KickoffCheck[] = [
  {
    id: "metadata-check",
    label: "Metadata Check",
    verification:
      "Confirm the Startup Optimization Memo is present in the forensics panel as Day 0 evidence before client walkthrough.",
    evidenceRefs: ["docs/RC1_CLIENT_UAT_GOLDEN_PATH.md", "src/governance.ts"],
  },
  {
    id: "lens-persistence",
    label: "Lens Persistence",
    verification:
      "Toggle Skill Mode to Executive and confirm labels remain jargon-free with distinct Emerald CI and Violet QI visual cues.",
    evidenceRefs: ["src/skillMode.tsx", "src/App.tsx"],
  },
  {
    id: "api-bridge",
    label: "API Bridge",
    verification:
      "Confirm the network toast reports Healthy through the same-origin /api/health bridge.",
    evidenceRefs: ["src/hooks/useLatencyMetrics.ts", "src/components/NetworkToast.tsx"],
  },
  {
    id: "signature-gate",
    label: "Signature Gate",
    verification:
      "Confirm the AI Assistant displays the No-Unattended-Writes header and requires human approval before execution.",
    evidenceRefs: ["src/components/AIAssistant.tsx", "src/governance.ts"],
  },
];

export const rc1CommercialStatement =
  "HYBA_FULLSTACK RC1 is a sovereign, evidence-bound, dual-core intelligence substrate prepared for controlled UAT and client acceptance.";
