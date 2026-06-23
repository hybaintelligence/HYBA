export type MetricTranslationKey =
  | "phi_resonance"
  | "code_distance"
  | "physical_error_rate"
  | "substrate_coherence"
  | "evidence_seal"
  | "invariants"
  | "claim_boundary"
  | "pulvini_memory"
  | "salamander_regeneration";

export const metricTranslations: Record<
  MetricTranslationKey,
  {
    label: string;
    plainEnglish: string;
    operationalImplication: string;
    evidenceView: string;
    expert: string;
  }
> = {
  phi_resonance: {
    label: "Coherence target",
    plainEnglish: "How stable HYBA expects the intelligence state to be before trusting a result.",
    operationalImplication:
      "Higher settings are stricter; use balanced defaults unless a regulated workflow needs more proof.",
    evidenceView:
      "Compare requested φ target with live resonance, invariant status, and evidence seal freshness.",
    expert: "φ-resonance target tunes phase-alignment acceptance for substrate-backed execution.",
  },
  code_distance: {
    label: "Resilience level",
    plainEnglish:
      "How much protection HYBA applies against noisy or unstable execution assumptions.",
    operationalImplication:
      "Use higher resilience for regulated decisions and lower resilience for exploration.",
    evidenceView:
      "Audit alongside syndrome weight, stabilizer confidence, and fail-closed invariant checks.",
    expert: "Code distance governs the error-correction envelope exposed to QI/CI rails.",
  },
  physical_error_rate: {
    label: "Reliability assumption",
    plainEnglish: "The expected rate of low-level execution noise in the rail configuration.",
    operationalImplication:
      "Lower assumptions make the rail more conservative for evidence-bound decisions.",
    evidenceView:
      "Preserve this value in provisioning records and approval packets for reproducibility.",
    expert: "Physical error-rate parameter used for capacity and fault-tolerance planning.",
  },
  substrate_coherence: {
    label: "Reasoning stability",
    plainEnglish:
      "Whether HYBA's reasoning state is internally consistent enough to support a decision.",
    operationalImplication:
      "Strong coherence can proceed to simulation; weak coherence should escalate or gather more evidence.",
    evidenceView: "Back with live telemetry source, invariant pass count, and claim boundary.",
    expert: "Substrate coherence summarizes manifold/quantum/consciousness state alignment.",
  },
  evidence_seal: {
    label: "Audit seal",
    plainEnglish:
      "A proof handle that lets a buyer or auditor verify what evidence supported the answer.",
    operationalImplication:
      "No seal means no autonomous action; sealed answers are still advisory unless policy approves execution.",
    evidenceView:
      "Use the seal to link answer, assumptions, invariants, source telemetry, and timestamp.",
    expert: "Evidence seal anchors reproducible evidence packets and adversarial-contract policy.",
  },
  invariants: {
    label: "Proof checks",
    plainEnglish: "Automated checks that must pass before HYBA treats a claim as safe to present.",
    operationalImplication:
      "Failed or missing checks should block high-risk execution and request human review.",
    evidenceView: "Show pass/fail count, failed invariant names, and fail-closed status.",
    expert: "Invariant suite validates claim contracts and extraordinary-evidence gates.",
  },
  claim_boundary: {
    label: "Action boundary",
    plainEnglish:
      "The line between advice, simulation, prepared remediation, and approved execution.",
    operationalImplication:
      "Users can ask, simulate, and prepare; execution requires role-aware approval unless pre-authorized.",
    evidenceView: "Record boundary, approver, governance tags, and command allowlist entry.",
    expert: "Claim boundary constrains autonomy semantics for evidence-bound QI responses.",
  },
  pulvini_memory: {
    label: "Long-context memory rail",
    plainEnglish: "How HYBA preserves important context while compressing less important details.",
    operationalImplication:
      "Use for decisions requiring history, assumptions, and audit continuity.",
    evidenceView: "Expose memory compression, source lineage, and retention boundary.",
    expert: "PULVINI φ-memory folds context through φ-scaled memory compression.",
  },
  salamander_regeneration: {
    label: "Self-healing proposal",
    plainEnglish:
      "HYBA can identify degraded workflows and draft repairs without silently changing systems.",
    operationalImplication:
      "Default to proposal-only; approve execution only after blast-radius and rollback review.",
    evidenceView:
      "Attach degradation cause, proposed command, blast radius, rollback plan, and approval status.",
    expert: "Salamander regeneration prepares bounded remediation plans through governance gates.",
  },
};
