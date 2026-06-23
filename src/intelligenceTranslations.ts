import type { SkillMode } from "./skillMode";

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

type MetricTranslation = {
  label: string;
  plainEnglish: string;
  operationalImplication: string;
  evidenceView: string;
  expert: string;
  recommendation?: string;
};

type ModeSpecificTranslations = Record<SkillMode, MetricTranslation>;

export const metricTranslations: Record<MetricTranslationKey, ModeSpecificTranslations> = {
  phi_resonance: {
    executive: {
      label: "Reasoning Stability",
      plainEnglish:
        "How stable HYBA expects the intelligence state to be before trusting a result.",
      operationalImplication:
        "Higher settings are stricter; use balanced defaults unless a regulated workflow needs more proof.",
      evidenceView:
        "Compare requested φ target with live resonance, invariant status, and evidence seal freshness.",
      expert: "φ-resonance target tunes phase-alignment acceptance for substrate-backed execution.",
      recommendation: "Maintain above 95% for board-level decisions.",
    },
    business: {
      label: "Confidence Level",
      plainEnglish: "How confident HYBA is in the intelligence state before presenting results.",
      operationalImplication: "Use balanced defaults for routine business operations.",
      evidenceView: "Compare requested φ target with live resonance and invariant status.",
      expert: "φ-resonance target tunes phase-alignment acceptance for substrate-backed execution.",
      recommendation: "Keep above 90% for commercial operations.",
    },
    operator: {
      label: "System Stability",
      plainEnglish: "Whether the intelligence substrate is stable enough for operational tasks.",
      operationalImplication:
        "Strong stability supports automation; weak stability requires manual review.",
      evidenceView: "Check live telemetry, invariant status, and substrate health.",
      expert: "φ-resonance target tunes phase-alignment acceptance for substrate-backed execution.",
      recommendation: "Monitor for drops below 85% during active operations.",
    },
    analyst: {
      label: "Coherence Metric",
      plainEnglish: "The mathematical measure of intelligence state alignment across substrates.",
      operationalImplication:
        "Use for trend analysis and anomaly detection in intelligence patterns.",
      evidenceView: "Historical coherence trends, invariant correlations, and substrate alignment.",
      expert: "φ-resonance target tunes phase-alignment acceptance for substrate-backed execution.",
      recommendation: "Track week-over-week changes for intelligence quality assessment.",
    },
    engineer: {
      label: "Phase Alignment Factor",
      plainEnglish: "The phase-alignment threshold for substrate-backed quantum execution.",
      operationalImplication:
        "Higher thresholds require more precise phase control but reduce error rates.",
      evidenceView: "Phase error measurements, alignment calibration, and quantum gate fidelity.",
      expert: "φ-resonance target tunes phase-alignment acceptance for substrate-backed execution.",
      recommendation: "Calibrate against hardware specifications and error budgets.",
    },
    auditor: {
      label: "Proof Threshold",
      plainEnglish: "The minimum coherence required for evidence-bound claims to be auditable.",
      operationalImplication:
        "Claims below this threshold cannot be used for compliance or audit purposes.",
      evidenceView:
        "Audit trail includes coherence measurements, invariant checks, and seal validity.",
      expert: "φ-resonance target tunes phase-alignment acceptance for substrate-backed execution.",
      recommendation: "Require 98%+ for regulated industry claims.",
    },
    expert: {
      label: "φ-Resonance Target",
      plainEnglish:
        "The golden-ratio phase-alignment threshold for substrate-backed quantum execution.",
      operationalImplication:
        "Tune based on hardware capabilities, error budgets, and application requirements.",
      evidenceView: "Phase error measurements, φ-scaling factors, and quantum gate fidelity.",
      expert: "φ-resonance target tunes phase-alignment acceptance for substrate-backed execution.",
      recommendation: "Optimize for specific quantum algorithm requirements.",
    },
  },
  code_distance: {
    executive: {
      label: "Resilience Level",
      plainEnglish: "How much protection HYBA applies against execution errors.",
      operationalImplication: "Higher resilience is safer for critical decisions.",
      evidenceView: "Audit alongside error rates and failure modes.",
      expert: "Code distance governs the error-correction envelope exposed to QI/CI rails.",
      recommendation: "Use high resilience for regulated decisions.",
    },
    business: {
      label: "Error Protection",
      plainEnglish: "The level of error correction applied to intelligence operations.",
      operationalImplication: "Higher protection for high-value business decisions.",
      evidenceView: "Error correction statistics and failure rates.",
      expert: "Code distance governs the error-correction envelope exposed to QI/CI rails.",
      recommendation: "Standard protection for routine operations.",
    },
    operator: {
      label: "Fault Tolerance",
      plainEnglish: "How many errors the system can correct before failing.",
      operationalImplication: "Higher tolerance supports longer-running operations.",
      evidenceView: "Fault injection tests and recovery statistics.",
      expert: "Code distance governs the error-correction envelope exposed to QI/CI rails.",
      recommendation: "Monitor fault recovery during active operations.",
    },
    analyst: {
      label: "Correction Distance",
      plainEnglish: "The mathematical error-correction distance parameter.",
      operationalImplication: "Use for capacity planning and performance modeling.",
      evidenceView: "Error correction overhead and resource utilization.",
      expert: "Code distance governs the error-correction envelope exposed to QI/CI rails.",
      recommendation: "Analyze trade-offs between distance and performance.",
    },
    engineer: {
      label: "Surface-Code Distance",
      plainEnglish: "The surface-code distance parameter for quantum error correction.",
      operationalImplication:
        "Higher distance requires more physical qubits but reduces logical error rate.",
      evidenceView: "Syndrome weight, stabilizer confidence, and fail-closed invariant checks.",
      expert: "Code distance governs the error-correction envelope exposed to QI/CI rails.",
      recommendation: "Balance against hardware constraints and latency requirements.",
    },
    auditor: {
      label: "Audit Trail Depth",
      plainEnglish: "The error-correction depth required for auditable intelligence claims.",
      operationalImplication: "Claims with insufficient depth cannot be used for compliance.",
      evidenceView: "Error correction logs, recovery events, and audit completeness.",
      expert: "Code distance governs the error-correction envelope exposed to QI/CI rails.",
      recommendation: "Require minimum distance for regulated industry claims.",
    },
    expert: {
      label: "Code Distance",
      plainEnglish: "The surface-code distance parameter for quantum error correction.",
      operationalImplication:
        "Higher distance requires more physical qubits but reduces logical error rate.",
      evidenceView: "Syndrome weight, stabilizer confidence, and fail-closed invariant checks.",
      expert: "Code distance governs the error-correction envelope exposed to QI/CI rails.",
      recommendation: "Optimize for specific quantum algorithm requirements.",
    },
  },
  physical_error_rate: {
    executive: {
      label: "Reliability Assumption",
      plainEnglish: "The expected error rate HYBA designs around.",
      operationalImplication: "Lower assumptions are more conservative for critical decisions.",
      evidenceView: "Validated against runtime telemetry and claim-boundary constraints.",
      expert: "Physical error-rate parameter used for capacity and fault-tolerance planning.",
      recommendation: "Use conservative assumptions for high-stakes decisions.",
    },
    business: {
      label: "Error Baseline",
      plainEnglish: "The baseline error rate expected in normal operations.",
      operationalImplication: "Monitor deviations from baseline for operational health.",
      evidenceView: "Error rate trends and operational statistics.",
      expert: "Physical error-rate parameter used for capacity and fault-tolerance planning.",
      recommendation: "Track against service level agreements.",
    },
    operator: {
      label: "Noise Floor",
      plainEnglish: "The minimum noise level expected in the system.",
      operationalImplication: "Operations above noise floor are considered healthy.",
      evidenceView: "Noise measurements and signal-to-noise ratios.",
      expert: "Physical error-rate parameter used for capacity and fault-tolerance planning.",
      recommendation: "Alert when noise exceeds operational thresholds.",
    },
    analyst: {
      label: "Error Parameter",
      plainEnglish: "The physical error rate parameter used in capacity planning.",
      operationalImplication: "Use for performance modeling and resource optimization.",
      evidenceView: "Error rate distributions and statistical analysis.",
      expert: "Physical error-rate parameter used for capacity and fault-tolerance planning.",
      recommendation: "Analyze error rate patterns for optimization opportunities.",
    },
    engineer: {
      label: "Physical Error Rate",
      plainEnglish:
        "The physical error rate parameter used for capacity and fault-tolerance planning.",
      operationalImplication:
        "Lower assumptions make the rail more conservative for evidence-bound decisions.",
      evidenceView:
        "Preserve this value in provisioning records and approval packets for reproducibility.",
      expert: "Physical error-rate parameter used for capacity and fault-tolerance planning.",
      recommendation: "Calibrate against hardware specifications and measurements.",
    },
    auditor: {
      label: "Error Bound",
      plainEnglish: "The maximum error rate allowed for auditable claims.",
      operationalImplication: "Claims exceeding this bound cannot be used for compliance.",
      evidenceView: "Error rate measurements, bound violations, and audit flags.",
      expert: "Physical error-rate parameter used for capacity and fault-tolerance planning.",
      recommendation: "Enforce strict bounds for regulated industry claims.",
    },
    expert: {
      label: "Physical Error Rate",
      plainEnglish:
        "The physical error rate parameter used for capacity and fault-tolerance planning.",
      operationalImplication:
        "Lower assumptions make the rail more conservative for evidence-bound decisions.",
      evidenceView:
        "Preserve this value in provisioning records and approval packets for reproducibility.",
      expert: "Physical error-rate parameter used for capacity and fault-tolerance planning.",
      recommendation: "Optimize based on hardware capabilities and application requirements.",
    },
  },
  substrate_coherence: {
    executive: {
      label: "Decision Stability",
      plainEnglish: "Whether HYBA's reasoning is consistent enough for decision-making.",
      operationalImplication: "Strong stability supports board-level decisions.",
      evidenceView: "Back with live telemetry source, invariant pass count, and claim boundary.",
      expert: "Substrate coherence summarizes manifold/quantum/consciousness state alignment.",
      recommendation: "Require strong stability for material decisions.",
    },
    business: {
      label: "Intelligence Health",
      plainEnglish: "The overall health of HYBA's intelligence systems.",
      operationalImplication: "Healthy systems support routine business operations.",
      evidenceView: "Health checks, active job status, and system metrics.",
      expert: "Substrate coherence summarizes manifold/quantum/consciousness state alignment.",
      recommendation: "Monitor for degradation in business-critical operations.",
    },
    operator: {
      label: "System Health",
      plainEnglish: "Whether the intelligence substrate is running well enough for operations.",
      operationalImplication: "Strong coherence means operational automation can continue.",
      evidenceView: "Health checks, active job status, regeneration events.",
      expert: "Substrate coherence summarizes manifold/quantum/consciousness state alignment.",
      recommendation: "Pause operations when coherence drops below thresholds.",
    },
    analyst: {
      label: "Coherence Metric",
      plainEnglish: "The mathematical measure of intelligence state alignment.",
      operationalImplication: "Use for trend analysis and anomaly detection.",
      evidenceView: "Coherence trends, alignment correlations, and state transitions.",
      expert: "Substrate coherence summarizes manifold/quantum/consciousness state alignment.",
      recommendation: "Track coherence patterns for intelligence quality assessment.",
    },
    engineer: {
      label: "Substrate Coherence",
      plainEnglish: "The coherence of the quantum/classical substrate layers.",
      operationalImplication:
        "Strong coherence can proceed to simulation; weak coherence should escalate.",
      evidenceView: "Back with live telemetry source, invariant pass count, and claim boundary.",
      expert: "Substrate coherence summarizes manifold/quantum/consciousness state alignment.",
      recommendation: "Monitor substrate alignment during quantum operations.",
    },
    auditor: {
      label: "Audit Coherence",
      plainEnglish: "The coherence level required for auditable intelligence claims.",
      operationalImplication: "Claims below this threshold cannot be used for compliance.",
      evidenceView: "Coherence measurements, audit trail completeness, and seal validity.",
      expert: "Substrate coherence summarizes manifold/quantum/consciousness state alignment.",
      recommendation: "Require minimum coherence for regulated industry claims.",
    },
    expert: {
      label: "Substrate Coherence",
      plainEnglish: "The coherence of the quantum/classical substrate layers.",
      operationalImplication:
        "Strong coherence can proceed to simulation; weak coherence should escalate.",
      evidenceView: "Back with live telemetry source, invariant pass count, and claim boundary.",
      expert: "Substrate coherence summarizes manifold/quantum/consciousness state alignment.",
      recommendation: "Optimize for specific quantum algorithm requirements.",
    },
  },
  evidence_seal: {
    executive: {
      label: "Audit Seal",
      plainEnglish: "A proof handle for verifying what evidence supported an answer.",
      operationalImplication: "No seal means no autonomous action; sealed answers are advisory.",
      evidenceView: "Use the seal to link answer, assumptions, invariants, source telemetry.",
      expert:
        "Evidence seal anchors reproducible evidence packets and adversarial-contract policy.",
      recommendation: "Require seals for all board-level decisions.",
    },
    business: {
      label: "Proof ID",
      plainEnglish: "The identifier for the evidence packet supporting this answer.",
      operationalImplication: "Use for tracking and auditing business decisions.",
      evidenceView: "Evidence packet contents and metadata.",
      expert:
        "Evidence seal anchors reproducible evidence packets and adversarial-contract policy.",
      recommendation: "Record proof IDs for all commercial operations.",
    },
    operator: {
      label: "Evidence Handle",
      plainEnglish: "The reference to the evidence packet for operational actions.",
      operationalImplication: "Required for any automated or semi-automated operations.",
      evidenceView: "Evidence packet contents and operational context.",
      expert:
        "Evidence seal anchors reproducible evidence packets and adversarial-contract policy.",
      recommendation: "Verify evidence handles before operational changes.",
    },
    analyst: {
      label: "Seal Identifier",
      plainEnglish: "The cryptographic identifier for the evidence seal.",
      operationalImplication: "Use for traceability and reproducibility analysis.",
      evidenceView: "Seal metadata, cryptographic validation, and chain of custody.",
      expert:
        "Evidence seal anchors reproducible evidence packets and adversarial-contract policy.",
      recommendation: "Analyze seal patterns for evidence quality assessment.",
    },
    engineer: {
      label: "Evidence Seal",
      plainEnglish:
        "A proof handle that lets a buyer or auditor verify what evidence supported the answer.",
      operationalImplication:
        "No seal means no autonomous action; sealed answers are still advisory unless policy approves execution.",
      evidenceView:
        "Use the seal to link answer, assumptions, invariants, source telemetry, and timestamp.",
      expert:
        "Evidence seal anchors reproducible evidence packets and adversarial-contract policy.",
      recommendation: "Validate seal cryptographic properties before use.",
    },
    auditor: {
      label: "Audit Trail Seal",
      plainEnglish: "The cryptographic seal for the complete audit trail.",
      operationalImplication: "Required for compliance and regulatory purposes.",
      evidenceView: "Complete audit trail, seal validation, and regulatory compliance.",
      expert:
        "Evidence seal anchors reproducible evidence packets and adversarial-contract policy.",
      recommendation: "Verify seal integrity for all regulatory claims.",
    },
    expert: {
      label: "Evidence Seal",
      plainEnglish:
        "A proof handle that lets a buyer or auditor verify what evidence supported the answer.",
      operationalImplication:
        "No seal means no autonomous action; sealed answers are still advisory unless policy approves execution.",
      evidenceView:
        "Use the seal to link answer, assumptions, invariants, source telemetry, and timestamp.",
      expert:
        "Evidence seal anchors reproducible evidence packets and adversarial-contract policy.",
      recommendation: "Validate cryptographic properties and chain of custody.",
    },
  },
  invariants: {
    executive: {
      label: "Proof Checks",
      plainEnglish: "Automated checks that must pass before HYBA treats a claim as safe.",
      operationalImplication: "Failed checks should block high-risk execution.",
      evidenceView: "Show pass/fail count, failed invariant names, and fail-closed status.",
      expert: "Invariant suite validates claim contracts and extraordinary-evidence gates.",
      recommendation: "Require all checks to pass for material decisions.",
    },
    business: {
      label: "Safety Checks",
      plainEnglish: "The safety validations performed before presenting results.",
      operationalImplication: "All checks must pass for business-critical operations.",
      evidenceView: "Check status, validation results, and safety metrics.",
      expert: "Invariant suite validates claim contracts and extraordinary-evidence gates.",
      recommendation: "Monitor check pass rates for operational health.",
    },
    operator: {
      label: "Validation Gates",
      plainEnglish: "The validation steps required before operational actions.",
      operationalImplication: "Failed validations block operational changes.",
      evidenceView: "Validation results, gate status, and operational context.",
      expert: "Invariant suite validates claim contracts and extraordinary-evidence gates.",
      recommendation: "Review failed validations before operational changes.",
    },
    analyst: {
      label: "Invariant Set",
      plainEnglish: "The set of mathematical invariants validated for this claim.",
      operationalImplication: "Use for analyzing claim robustness and reliability.",
      evidenceView: "Invariant definitions, validation results, and statistical analysis.",
      expert: "Invariant suite validates claim contracts and extraordinary-evidence gates.",
      recommendation: "Analyze invariant patterns for claim quality assessment.",
    },
    engineer: {
      label: "Proof Checks",
      plainEnglish:
        "Automated checks that must pass before HYBA treats a claim as safe to present.",
      operationalImplication:
        "Failed or missing checks should block high-risk execution and request human review.",
      evidenceView: "Show pass/fail count, failed invariant names, and fail-closed status.",
      expert: "Invariant suite validates claim contracts and extraordinary-evidence gates.",
      recommendation: "Review invariant definitions for specific use cases.",
    },
    auditor: {
      label: "Compliance Invariants",
      plainEnglish: "The invariants required for regulatory compliance.",
      operationalImplication: "Missing invariants invalidate compliance claims.",
      evidenceView: "Compliance matrix, invariant coverage, and regulatory alignment.",
      expert: "Invariant suite validates claim contracts and extraordinary-evidence gates.",
      recommendation: "Verify complete invariant coverage for regulated claims.",
    },
    expert: {
      label: "Proof Checks",
      plainEnglish:
        "Automated checks that must pass before HYBA treats a claim as safe to present.",
      operationalImplication:
        "Failed or missing checks should block high-risk execution and request human review.",
      evidenceView: "Show pass/fail count, failed invariant names, and fail-closed status.",
      expert: "Invariant suite validates claim contracts and extraordinary-evidence gates.",
      recommendation: "Optimize invariant set for specific algorithm requirements.",
    },
  },
  claim_boundary: {
    executive: {
      label: "Action Boundary",
      plainEnglish: "The limit between advice, simulation, and approved execution.",
      operationalImplication: "Execution requires role-aware approval unless pre-authorized.",
      evidenceView: "Record boundary, approver, governance tags, and command allowlist entry.",
      expert: "Claim boundary constrains autonomy semantics for evidence-bound QI responses.",
      recommendation: "Maintain strict boundaries for autonomous actions.",
    },
    business: {
      label: "Approval Level",
      plainEnglish: "The approval required before taking action on this result.",
      operationalImplication: "Business decisions require appropriate approval levels.",
      evidenceView: "Approval chain, governance status, and business context.",
      expert: "Claim boundary constrains autonomy semantics for evidence-bound QI responses.",
      recommendation: "Follow approval matrix for business operations.",
    },
    operator: {
      label: "Execution Scope",
      plainEnglish: "What actions are allowed based on this intelligence result.",
      operationalImplication: "Stay within approved execution scope for operations.",
      evidenceView: "Scope definitions, approval status, and operational limits.",
      expert: "Claim boundary constrains autonomy semantics for evidence-bound QI responses.",
      recommendation: "Verify execution scope before operational changes.",
    },
    analyst: {
      label: "Claim Contract",
      plainEnglish: "The contractual boundary of what HYBA is claiming.",
      operationalImplication: "Use for analyzing claim scope and liability.",
      evidenceView: "Contract terms, boundary definitions, and liability analysis.",
      expert: "Claim boundary constrains autonomy semantics for evidence-bound QI responses.",
      recommendation: "Analyze claim contracts for risk assessment.",
    },
    engineer: {
      label: "Claim Boundary",
      plainEnglish:
        "The line between advice, simulation, prepared remediation, and approved execution.",
      operationalImplication:
        "Users can ask, simulate, and prepare; execution requires role-aware approval unless pre-authorized.",
      evidenceView: "Record boundary, approver, governance tags, and command allowlist entry.",
      expert: "Claim boundary constrains autonomy semantics for evidence-bound QI responses.",
      recommendation: "Respect boundary constraints in all automation.",
    },
    auditor: {
      label: "Regulatory Boundary",
      plainEnglish: "The regulatory limit on what can be claimed or executed.",
      operationalImplication: "Claims beyond this boundary cannot be used for compliance.",
      evidenceView: "Regulatory matrix, boundary compliance, and audit status.",
      expert: "Claim boundary constrains autonomy semantics for evidence-bound QI responses.",
      recommendation: "Verify regulatory alignment for all claims.",
    },
    expert: {
      label: "Claim Boundary",
      plainEnglish:
        "The line between advice, simulation, prepared remediation, and approved execution.",
      operationalImplication:
        "Users can ask, simulate, and prepare; execution requires role-aware approval unless pre-authorized.",
      evidenceView: "Record boundary, approver, governance tags, and command allowlist entry.",
      expert: "Claim boundary constrains autonomy semantics for evidence-bound QI responses.",
      recommendation: "Optimize boundary for specific use cases.",
    },
  },
  pulvini_memory: {
    executive: {
      label: "Memory Rail",
      plainEnglish: "HYBA's structured memory for reusing context without losing auditability.",
      operationalImplication: "Use for decisions requiring history and audit continuity.",
      evidenceView: "Memory source, compression metadata, and trace continuity.",
      expert: "PULVINI φ-memory folds context through φ-scaled memory compression.",
      recommendation: "Preserve memory for high-stakes decisions.",
    },
    business: {
      label: "Context Memory",
      plainEnglish: "The memory system that preserves important business context.",
      operationalImplication: "Use for maintaining business decision continuity.",
      evidenceView: "Memory contents, business context, and decision history.",
      expert: "PULVINI φ-memory folds context through φ-scaled memory compression.",
      recommendation: "Track memory for business decision audit trails.",
    },
    operator: {
      label: "Operational Memory",
      plainEnglish: "The memory system for operational context and history.",
      operationalImplication: "Use for operational continuity and troubleshooting.",
      evidenceView: "Operational history, context preservation, and trace continuity.",
      expert: "PULVINI φ-memory folds context through φ-scaled memory compression.",
      recommendation: "Preserve operational memory for incident analysis.",
    },
    analyst: {
      label: "Memory Compression",
      plainEnglish: "The φ-scaled memory compression system for context retention.",
      operationalImplication: "Use for analyzing memory efficiency and context quality.",
      evidenceView: "Compression metrics, context retention, and memory patterns.",
      expert: "PULVINI φ-memory folds context through φ-scaled memory compression.",
      recommendation: "Analyze memory compression for optimization opportunities.",
    },
    engineer: {
      label: "PULVINI Memory",
      plainEnglish: "HYBA's structured memory for reusing context without losing auditability.",
      operationalImplication: "Use it to preserve decision context and evidence continuity.",
      evidenceView: "Memory source, compression metadata, and trace continuity.",
      expert: "PULVINI φ-memory folds context through φ-scaled memory compression.",
      recommendation: "Optimize compression ratio vs context quality.",
    },
    auditor: {
      label: "Audit Memory",
      plainEnglish: "The memory system for preserving audit-relevant context.",
      operationalImplication: "Required for complete audit trails and compliance.",
      evidenceView: "Audit memory contents, compression validation, and trace completeness.",
      expert: "PULVINI φ-memory folds context through φ-scaled memory compression.",
      recommendation: "Verify memory preservation for regulatory compliance.",
    },
    expert: {
      label: "PULVINI Memory",
      plainEnglish: "HYBA's structured memory for reusing context without losing auditability.",
      operationalImplication: "Use it to preserve decision context and evidence continuity.",
      evidenceView: "Memory source, compression metadata, and trace continuity.",
      expert: "PULVINI φ-memory folds context through φ-scaled memory compression.",
      recommendation: "Optimize φ-scaling for specific use cases.",
    },
  },
  salamander_regeneration: {
    executive: {
      label: "Regeneration Proposal",
      plainEnglish: "HYBA can suggest repairs without silently changing systems.",
      operationalImplication: "Default to proposal-only; approve after blast-radius review.",
      evidenceView: "Attach degradation cause, proposed action, rollback plan, approval status.",
      expert:
        "Salamander regeneration prepares bounded remediation plans through governance gates.",
      recommendation: "Review blast radius before approving any regeneration.",
    },
    business: {
      label: "Self-Healing",
      plainEnglish: "The system's ability to identify and propose fixes for issues.",
      operationalImplication: "Use proposals to maintain business continuity safely.",
      evidenceView: "Issue detection, proposed fixes, and business impact assessment.",
      expert:
        "Salamander regeneration prepares bounded remediation plans through governance gates.",
      recommendation: "Approve self-healing for routine operational issues.",
    },
    operator: {
      label: "Repair Proposal",
      plainEnglish: "The system's proposed fix for degraded workflows.",
      operationalImplication: "Review blast radius and rollback plan before execution.",
      evidenceView: "Degradation cause, proposed command, rollback plan, operational context.",
      expert:
        "Salamander regeneration prepares bounded remediation plans through governance gates.",
      recommendation: "Test rollback plans before approving repairs.",
    },
    analyst: {
      label: "Regeneration Analysis",
      plainEnglish: "The analysis of system degradation and proposed remediation.",
      operationalImplication: "Use for understanding system health and recovery patterns.",
      evidenceView: "Degradation patterns, remediation effectiveness, and system resilience.",
      expert:
        "Salamander regeneration prepares bounded remediation plans through governance gates.",
      recommendation: "Analyze regeneration patterns for system optimization.",
    },
    engineer: {
      label: "Salamander Regeneration",
      plainEnglish:
        "HYBA can identify degraded workflows and draft repairs without silently changing systems.",
      operationalImplication:
        "Default to proposal-only; approve execution only after blast-radius and rollback review.",
      evidenceView:
        "Attach degradation cause, proposed command, blast radius, rollback plan, and approval status.",
      expert:
        "Salamander regeneration prepares bounded remediation plans through governance gates.",
      recommendation: "Validate regeneration logic before deployment.",
    },
    auditor: {
      label: "Audit Trail Repair",
      plainEnglish: "The system's ability to repair audit trail issues.",
      operationalImplication: "Requires explicit approval for any audit trail modifications.",
      evidenceView: "Audit impact, repair proposal, compliance validation, approval chain.",
      expert:
        "Salamander regeneration prepares bounded remediation plans through governance gates.",
      recommendation: "Require highest approval for audit trail repairs.",
    },
    expert: {
      label: "Salamander Regeneration",
      plainEnglish:
        "HYBA can identify degraded workflows and draft repairs without silently changing systems.",
      operationalImplication:
        "Default to proposal-only; approve execution only after blast-radius and rollback review.",
      evidenceView:
        "Attach degradation cause, proposed command, blast radius, rollback plan, and approval status.",
      expert:
        "Salamander regeneration prepares bounded remediation plans through governance gates.",
      recommendation: "Optimize regeneration logic for specific failure modes.",
    },
  },
};
