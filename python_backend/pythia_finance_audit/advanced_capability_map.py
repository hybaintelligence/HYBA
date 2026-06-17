"""Advanced HYBA capability map for regulated finance use-cases.

This module converts HYBA's deeper capabilities into finance-safe product
surfaces. It is deliberately declarative and side-effect free: it does not
price, approve, trade, book, file, issue rulings, calculate regulatory capital,
or call external services.

Purpose:
    - preserve the lift-out finance boundary;
    - map quantum-style mathematics, PULVINI memory compression, AI memory,
      intelligence telemetry, Millennium-style proof discipline, and phi scaling
      into finance evidence products;
    - keep every output framed as support for authorised human review.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Dict, Iterable, List, Tuple


class FinanceCapabilityRiskTier(str, Enum):
    """How close a capability is to regulated decision authority."""

    EVIDENCE_ONLY = "evidence_only"
    HUMAN_REVIEW_SUPPORT = "human_review_support"
    MODEL_RISK_SUPPORT = "model_risk_support"


@dataclass(frozen=True)
class AdvancedFinanceCapability:
    """A lift-out-safe mapping from HYBA capability to finance product surface."""

    capability_id: str
    source_capability: str
    finance_surface: str
    value_proposition: str
    permitted_outputs: Tuple[str, ...]
    prohibited_outputs: Tuple[str, ...]
    evidence_required: Tuple[str, ...]
    human_owner: str
    risk_tier: FinanceCapabilityRiskTier

    def to_dict(self) -> Dict[str, object]:
        payload = asdict(self)
        payload["risk_tier"] = self.risk_tier.value
        return payload


CAPABILITIES: Tuple[AdvancedFinanceCapability, ...] = (
    AdvancedFinanceCapability(
        capability_id="PULVINI_PORTFOLIO_EVIDENCE_COMPRESSION",
        source_capability="PULVINI phi-folding memory compression with retained reconstruction kernels",
        finance_surface="Portfolio, transaction, and evidence-ledger compression for replayable review packs",
        value_proposition=(
            "Compress large audit surfaces into smaller review artefacts while preserving reconstruction evidence, "
            "trace metrics, and packet hashes for model validation and external audit."
        ),
        permitted_outputs=(
            "compressed evidence manifest",
            "reconstruction-kernel inventory",
            "replay hash",
            "compression telemetry",
            "exception list for human audit",
        ),
        prohibited_outputs=(
            "capital calculation",
            "trade approval",
            "portfolio rebalancing instruction",
            "legal or Shariah conclusion",
        ),
        evidence_required=(
            "loss/reconstruction error threshold",
            "kernel retention proof",
            "packet hash stability",
            "input lineage hash",
        ),
        human_owner="Model risk manager / internal audit / external audit reviewer",
        risk_tier=FinanceCapabilityRiskTier.MODEL_RISK_SUPPORT,
    ),
    AdvancedFinanceCapability(
        capability_id="QUANTUM_STYLE_SCENARIO_SEARCH",
        source_capability="Bounded quantum-style search, dodecahedral basis, density-matrix discipline, and numeric guards",
        finance_surface="Constrained stress-scenario discovery and adversarial model challenge",
        value_proposition=(
            "Search bounded scenario spaces deterministically to find hidden fragilities in products, portfolios, "
            "liquidity paths, collateral chains, or Sukuk lifecycle assumptions."
        ),
        permitted_outputs=(
            "candidate stress scenario",
            "scenario path hash",
            "instability warning",
            "human review queue entry",
            "bounded-search telemetry",
        ),
        prohibited_outputs=(
            "guaranteed optimal trade",
            "market prediction guarantee",
            "automated execution",
            "regulatory approval",
        ),
        evidence_required=(
            "declared search bounds",
            "finite-state checks",
            "deterministic replay seed",
            "numeric stability report",
        ),
        human_owner="Risk committee / treasury risk / model validation",
        risk_tier=FinanceCapabilityRiskTier.HUMAN_REVIEW_SUPPORT,
    ),
    AdvancedFinanceCapability(
        capability_id="PHI_SCALING_GOVERNANCE_SCHEDULER",
        source_capability="Golden-ratio / phi scaling for deterministic weighting, folding, resonance, and search discipline",
        finance_surface="Deterministic review prioritisation and multi-signal risk-weight scheduling",
        value_proposition=(
            "Use phi-scaled deterministic weighting to rank which evidence packets, anomalies, and controls should be reviewed first, "
            "without pretending phi alone proves financial truth."
        ),
        permitted_outputs=(
            "review priority score",
            "weight vector",
            "ranking rationale",
            "resonance telemetry",
        ),
        prohibited_outputs=(
            "profitability claim",
            "solvency claim",
            "automatic approval",
            "unbounded extrapolation",
        ),
        evidence_required=(
            "normalised weights",
            "sensitivity run",
            "baseline comparator",
            "drift threshold",
        ),
        human_owner="Compliance operations / risk governance owner",
        risk_tier=FinanceCapabilityRiskTier.EVIDENCE_ONLY,
    ),
    AdvancedFinanceCapability(
        capability_id="AI_MEMORY_MODEL_RISK_TRACE",
        source_capability="Persistent AI memory, evidence tables, snapshots, and reasoning traces",
        finance_surface="Model-risk memory for decisions, exceptions, assumptions, and replayable governance history",
        value_proposition=(
            "Preserve why a packet, model challenge, stress scenario, or exception was raised so validators can reconstruct "
            "the evidence path across time."
        ),
        permitted_outputs=(
            "reasoning trace",
            "memory snapshot",
            "assumption lineage",
            "evidence retrieval log",
            "confidence annotation",
        ),
        prohibited_outputs=(
            "self-authorising policy change",
            "unreviewed model update",
            "automatic regulatory submission",
            "client-specific advice without authorised review",
        ),
        evidence_required=(
            "source evidence IDs",
            "timestamped memory snapshot",
            "confidence calculation",
            "reviewer attestation hook",
        ),
        human_owner="Model owner / validation function / compliance officer",
        risk_tier=FinanceCapabilityRiskTier.MODEL_RISK_SUPPORT,
    ),
    AdvancedFinanceCapability(
        capability_id="INTELLIGENCE_FABRIC_CONTROL_ROOM",
        source_capability="Metacognitive intelligence telemetry: pressure, exhaustion, confidence, self-awareness, prediction error",
        finance_surface="Operational-resilience control room for model, liquidity, compliance, and governance stress",
        value_proposition=(
            "Convert internal system-state intelligence into finance operations telemetry: pressure, confidence, exhaustion, "
            "recovery mode, and escalation events."
        ),
        permitted_outputs=(
            "control-room telemetry",
            "escalation signal",
            "confidence degradation alert",
            "review-mode switch recommendation",
        ),
        prohibited_outputs=(
            "unattended autonomous remediation",
            "production kill-switch without configured authority",
            "trading halt instruction without human owner",
            "legal conclusion",
        ),
        evidence_required=(
            "telemetry schema",
            "threshold configuration",
            "event log",
            "human escalation mapping",
        ),
        human_owner="Operational resilience owner / CISO / head of risk operations",
        risk_tier=FinanceCapabilityRiskTier.HUMAN_REVIEW_SUPPORT,
    ),
    AdvancedFinanceCapability(
        capability_id="MILLENNIUM_STYLE_PROOF_OBLIGATION_ENGINE",
        source_capability="Millennium-problem operationalisation: proof discipline, hard invariants, counterexample search",
        finance_surface="Proof-obligation ledger for models, products, compliance claims, and client-safe assertions",
        value_proposition=(
            "Treat high-impact finance claims like theorem obligations: every claim requires assumptions, invariants, "
            "counterexamples, falsification attempts, and sealed evidence before it is used commercially."
        ),
        permitted_outputs=(
            "claim register",
            "proof obligation",
            "counterexample challenge",
            "falsification status",
            "evidence sufficiency rating",
        ),
        prohibited_outputs=(
            "mathematical proof claim without independent review",
            "regulatory compliance conclusion",
            "scientific-prize claim",
            "client assurance without counsel/validator sign-off",
        ),
        evidence_required=(
            "formal assumptions",
            "invariant list",
            "counterexample search report",
            "independent reviewer field",
            "sealed evidence packet",
        ),
        human_owner="Chief risk officer / general counsel / independent validator",
        risk_tier=FinanceCapabilityRiskTier.MODEL_RISK_SUPPORT,
    ),
)


BOUNDARY_STATEMENT = (
    "Advanced HYBA capabilities may support regulated finance as evidence, compression, stress discovery, "
    "proof-obligation, and governance infrastructure. They must not be exposed as autonomous finance authority."
)


def list_advanced_finance_capabilities() -> List[Dict[str, object]]:
    """Return all finance-safe capability mappings as JSON-serialisable objects."""

    return [capability.to_dict() for capability in CAPABILITIES]


def capability_ids() -> List[str]:
    """Return stable IDs for tests, docs, and external manifests."""

    return [capability.capability_id for capability in CAPABILITIES]


def prohibited_terms() -> Tuple[str, ...]:
    """Terms that must remain prohibited across every advanced finance mapping."""

    return (
        "trade approval",
        "automated execution",
        "regulatory approval",
        "legal or Shariah conclusion",
        "capital calculation",
    )


def validate_advanced_capability_boundaries(capabilities: Iterable[AdvancedFinanceCapability] = CAPABILITIES) -> Dict[str, object]:
    """Validate that advanced capability mappings preserve the no-authority boundary."""

    ids: List[str] = []
    violations: List[str] = []
    required_prohibition_fragments = prohibited_terms()
    for capability in capabilities:
        ids.append(capability.capability_id)
        prohibited_blob = " | ".join(capability.prohibited_outputs).lower()
        permitted_blob = " | ".join(capability.permitted_outputs).lower()
        if not capability.evidence_required:
            violations.append(f"{capability.capability_id}: missing evidence requirements")
        if not capability.human_owner:
            violations.append(f"{capability.capability_id}: missing human owner")
        for forbidden in required_prohibition_fragments:
            if forbidden in permitted_blob:
                violations.append(f"{capability.capability_id}: forbidden term appears in permitted outputs: {forbidden}")
        if capability.risk_tier not in set(FinanceCapabilityRiskTier):
            violations.append(f"{capability.capability_id}: invalid risk tier")
        if "approval" not in prohibited_blob and "execution" not in prohibited_blob and "conclusion" not in prohibited_blob:
            violations.append(f"{capability.capability_id}: weak prohibited-output boundary")
    return {
        "schema": "PYTHIA_ADVANCED_FINANCE_CAPABILITY_BOUNDARY_V1",
        "boundary_statement": BOUNDARY_STATEMENT,
        "capability_count": len(ids),
        "capability_ids": ids,
        "valid": not violations,
        "violations": violations,
    }


__all__ = [
    "AdvancedFinanceCapability",
    "BOUNDARY_STATEMENT",
    "CAPABILITIES",
    "FinanceCapabilityRiskTier",
    "capability_ids",
    "list_advanced_finance_capabilities",
    "prohibited_terms",
    "validate_advanced_capability_boundaries",
]
