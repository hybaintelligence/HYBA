"""
PYTHIA Blockchain Structure Intelligence and Mining Guardrails.

This module combines the empirical blockchain-structure evidence lane with the
PYTHIA/PULVINI mining runtime without weakening HYBA claim boundaries.

The doctrine is deliberately precise:

1. empirical blockchain structure may become a PYTHIA search prior;
2. it must never be represented as guaranteed block discovery or revenue;
3. exact SHA-256d verification remains the external oracle;
4. live mining launch requires operator approval, pool credentials, evidence
   provenance, and fail-closed funding locks;
5. accepted pool-side shares are the threshold for treasury/funding actions.

The intended input is the JSON output from scripts/phi_resonance_empirical_evidence.py,
which measures Phi^15 resonance, birthday-signature echoes, angular distribution,
golden-angle alignment, sunflower score, gaps, and sector coverage from public
Bitcoin block nonce data.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping


class StructureEvidenceStatus(str, Enum):
    """Evidence posture for blockchain-structure intelligence."""

    INSUFFICIENT = "insufficient"
    OBSERVED = "structure_observed"
    STRONG = "structure_strong"


class MiningLaunchDecision(str, Enum):
    """Fail-closed mining launch decision."""

    BLOCK = "block"
    SUPERVISED_DRY_RUN = "supervised_dry_run"
    GUARDED_LIVE_READY = "guarded_live_ready"


@dataclass(frozen=True)
class EmpiricalBlockchainStructureEvidence:
    """Extracted empirical structure metrics from public blockchain nonce data."""

    total_blocks: int
    phi_resonance_rate: float
    mean_resonance_strength: float
    birthday_echo_rate: float
    golden_angle_alignment: float
    sunflower_score: float
    sector_coverage_pct: float
    uniformity_score: float
    max_gap_size: int = 0
    source_script: str = "scripts/phi_resonance_empirical_evidence.py"
    source_kind: str = "public_bitcoin_block_nonce_empirical_report"

    @property
    def structure_score(self) -> float:
        """
        Conservative composite structure score.

        This is not a mining-success probability. It is a bounded prior-strength
        score for PYTHIA traversal planning. Weighting deliberately favours
        direct resonance, angular alignment, and sunflower/sector coverage while
        keeping the value in [0, 1].
        """
        raw = (
            0.30 * _clamp01(self.mean_resonance_strength)
            + 0.20 * _clamp01(self.phi_resonance_rate)
            + 0.20 * _clamp01(self.golden_angle_alignment)
            + 0.15 * _clamp01(self.sunflower_score)
            + 0.10 * _clamp01(self.sector_coverage_pct / 100.0)
            + 0.05 * _clamp01(self.birthday_echo_rate)
        )
        return round(_clamp01(raw), 6)

    @property
    def status(self) -> StructureEvidenceStatus:
        if self.total_blocks < 32:
            return StructureEvidenceStatus.INSUFFICIENT
        if self.structure_score >= 0.65 and self.golden_angle_alignment > 0.0:
            return StructureEvidenceStatus.STRONG
        return StructureEvidenceStatus.OBSERVED

    @property
    def evidence_is_usable_as_prior(self) -> bool:
        return self.status in {
            StructureEvidenceStatus.OBSERVED,
            StructureEvidenceStatus.STRONG,
        }


@dataclass(frozen=True)
class PythiaStructureIntelligencePacket:
    """Packet that feeds empirical structure into PYTHIA as bounded intelligence."""

    packet_id: str
    created_at: str
    evidence: EmpiricalBlockchainStructureEvidence
    pythia_directives: dict[str, Any]
    claim_boundary: list[str]
    required_verifiers: list[str]
    packet_hash: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MiningGuardrailInputs:
    """Inputs required before PYTHIA can leave dry-run mining mode."""

    operator_approval: bool
    pool_credentials_present: bool
    exact_sha256d_verifier_enabled: bool
    evidence_packet_present: bool
    accepted_share_proof_present: bool = False
    funding_action_requested: bool = False
    requested_live_mode: bool = False
    max_runtime_minutes: int = 30
    max_power_watts: int = 0
    claim_text: str = ""


@dataclass(frozen=True)
class MiningGuardrailReport:
    """Guardrail report emitted before any PYTHIA live-mining launch."""

    decision: MiningLaunchDecision
    launch_permitted: bool
    funding_actions_permitted: bool
    reasons: list[str]
    required_next_steps: list[str]
    structure_packet_hash: str | None
    guardrails: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _clamp01(value: float) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except Exception:
        return 0.0


def _first_number(*values: Any, default: float = 0.0) -> float:
    for value in values:
        if value is None:
            continue
        try:
            return float(value)
        except Exception:
            continue
    return float(default)


def _first_int(*values: Any, default: int = 0) -> int:
    for value in values:
        if value is None:
            continue
        try:
            return int(value)
        except Exception:
            continue
    return int(default)


def _section(report: Mapping[str, Any], *names: str) -> Mapping[str, Any]:
    for name in names:
        value = report.get(name)
        if isinstance(value, Mapping):
            return value
    return {}


def extract_empirical_structure_evidence(
    report: Mapping[str, Any],
) -> EmpiricalBlockchainStructureEvidence:
    """
    Extract a conservative evidence summary from the empirical report JSON.

    The extractor is intentionally schema-tolerant because empirical reports may
    be produced by different HYBA scripts/artifact versions. Missing fields
    default to zero instead of being invented.
    """
    summary = _section(report, "summary", "resonance_summary", "phi_resonance_summary")
    nonce_space = _section(
        report, "nonce_space_analysis", "nonce_space", "structure_analysis"
    )

    total_blocks = _first_int(
        summary.get("total_blocks"),
        report.get("total_blocks"),
        nonce_space.get("total_nonces"),
    )

    return EmpiricalBlockchainStructureEvidence(
        total_blocks=total_blocks,
        phi_resonance_rate=_first_number(summary.get("phi_resonance_rate")),
        mean_resonance_strength=_first_number(summary.get("mean_resonance_strength")),
        birthday_echo_rate=_first_number(summary.get("birthday_echo_rate")),
        golden_angle_alignment=_first_number(nonce_space.get("golden_angle_alignment")),
        sunflower_score=_first_number(nonce_space.get("sunflower_score")),
        sector_coverage_pct=_first_number(
            nonce_space.get("sector_coverage_pct"),
            nonce_space.get("coverage_pct"),
        ),
        uniformity_score=_first_number(nonce_space.get("uniformity_p_value")),
        max_gap_size=_first_int(nonce_space.get("max_gap_size")),
    )


def build_pythia_structure_intelligence_packet(
    evidence: EmpiricalBlockchainStructureEvidence,
) -> PythiaStructureIntelligencePacket:
    """Create the bounded intelligence packet that PYTHIA may use as a prior."""
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    directives = {
        "feed_to": "PYTHIA_PULVINI_MINING_RUNTIME",
        "intelligence_type": "empirical_blockchain_structure_prior",
        "use_as": "search_traversal_prior_only",
        "structure_status": evidence.status.value,
        "structure_score": evidence.structure_score,
        "preferred_runtime_effect": [
            "bias_nonce_region_priority_using_empirical_structure",
            "preserve_full_nonce_coverage",
            "retain_exact_sha256d_verification",
            "record_accepted_and_rejected_share_feedback",
            "update_deutsch_knowledge_substrate_after_pool_outcome",
        ],
        "forbidden_runtime_effect": [
            "do_not_claim_guaranteed_block_discovery",
            "do_not_bypass_sha256d_verifier",
            "do_not_submit_funding_action_without_pool_side_accepted_share_evidence",
            "do_not_self_modify_stable_core_guardrails",
        ],
    }
    boundary = [
        "Empirical structure is a PYTHIA search prior, not a guarantee.",
        "Exact SHA-256d verification remains the final mining oracle.",
        "All nonce-space traversal must preserve full coverage or emit a fail-closed report.",
        "Pool-side accepted-share proof is required before treasury/funding action.",
        "Stable Core guardrails remain human-owned and may only be staged for review.",
    ]
    verifiers = [
        "exact_sha256d_candidate_verifier",
        "pulvini_full_coverage_certificate",
        "pythia_structure_packet_hash",
        "pool_side_accepted_share_evidence_before_funding_action",
    ]

    preimage = json.dumps(
        {
            "evidence": asdict(evidence),
            "directives": directives,
            "claim_boundary": boundary,
            "required_verifiers": verifiers,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(preimage.encode("utf-8")).hexdigest()

    return PythiaStructureIntelligencePacket(
        packet_id=f"PYTHIA-STRUCTURE-{digest[:16]}",
        created_at=created_at,
        evidence=evidence,
        pythia_directives=directives,
        claim_boundary=boundary,
        required_verifiers=verifiers,
        packet_hash=digest,
    )


def evaluate_pythia_mining_guardrails(
    packet: PythiaStructureIntelligencePacket | None,
    inputs: MiningGuardrailInputs,
) -> MiningGuardrailReport:
    """
    Evaluate whether PYTHIA may proceed from dry-run into guarded live readiness.

    This function does not start mining. It is a fail-closed preflight guard.
    """
    reasons: list[str] = []
    next_steps: list[str] = []

    if packet is None:
        reasons.append("No PYTHIA structure intelligence packet supplied.")
        next_steps.append("Generate packet from empirical blockchain-structure report.")
    elif not packet.evidence.evidence_is_usable_as_prior:
        reasons.append(
            "Empirical blockchain-structure evidence is insufficient for live prior use."
        )
        next_steps.append(
            "Collect a larger block sample and regenerate evidence packet."
        )

    lower_claim = inputs.claim_text.lower()
    forbidden_claim_terms = (
        "guaranteed",
        "risk-free",
        "certain block",
        "bypass sha",
        "free money",
    )
    if any(term in lower_claim for term in forbidden_claim_terms):
        reasons.append(
            "Claim text contains forbidden guaranteed-revenue or verifier-bypass language."
        )
        next_steps.append("Replace claim with bounded evidence-first mining language.")

    if not inputs.exact_sha256d_verifier_enabled:
        reasons.append("Exact SHA-256d verifier is not enabled.")
        next_steps.append(
            "Enable exact SHA-256d candidate verification before pool submission."
        )

    if not inputs.evidence_packet_present:
        reasons.append("Evidence packet is not present.")
        next_steps.append(
            "Persist PYTHIA structure intelligence and guardrail report as JSON artifacts."
        )

    if inputs.funding_action_requested and not inputs.accepted_share_proof_present:
        reasons.append(
            "Funding action requested without pool-side accepted-share proof."
        )
        next_steps.append(
            "Disable funding actions until accepted share evidence exists."
        )

    if inputs.requested_live_mode:
        if not inputs.operator_approval:
            reasons.append("Live mode requested without explicit operator approval.")
            next_steps.append(
                "Set explicit operator approval only after reviewing guardrail packet."
            )
        if not inputs.pool_credentials_present:
            reasons.append("Live mode requested without pool credentials.")
            next_steps.append(
                "Provide pool credentials through approved secret path, not source code."
            )
        if inputs.max_runtime_minutes <= 0 or inputs.max_runtime_minutes > 60:
            reasons.append(
                "Live runtime window must be between 1 and 60 minutes for initial guarded launch."
            )
            next_steps.append(
                "Use a bounded first launch window, then review evidence."
            )
        if inputs.max_power_watts < 0:
            reasons.append("Power limit cannot be negative.")
            next_steps.append("Declare measured power budget or use zero if unknown.")

    funding_allowed = bool(inputs.accepted_share_proof_present) and not any(
        "Funding action" in reason for reason in reasons
    )

    if reasons:
        if inputs.requested_live_mode:
            decision = MiningLaunchDecision.BLOCK
            launch = False
        else:
            decision = MiningLaunchDecision.SUPERVISED_DRY_RUN
            launch = False
    else:
        decision = (
            MiningLaunchDecision.GUARDED_LIVE_READY
            if inputs.requested_live_mode
            else MiningLaunchDecision.SUPERVISED_DRY_RUN
        )
        launch = bool(inputs.requested_live_mode)

    guardrails = {
        "empirical_structure_prior_only": True,
        "exact_sha256d_final_oracle": True,
        "full_nonce_coverage_required": True,
        "pool_side_accepted_share_required_for_funding": True,
        "stable_core_self_modification_forbidden": True,
        "operator_can_abort": True,
        "initial_runtime_window_minutes": inputs.max_runtime_minutes,
        "max_power_watts": inputs.max_power_watts,
    }

    return MiningGuardrailReport(
        decision=decision,
        launch_permitted=launch,
        funding_actions_permitted=funding_allowed,
        reasons=reasons,
        required_next_steps=next_steps,
        structure_packet_hash=packet.packet_hash if packet else None,
        guardrails=guardrails,
    )


def load_empirical_report(path: str | os.PathLike[str]) -> dict[str, Any]:
    """Load an empirical blockchain-structure report from JSON."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


__all__ = [
    "EmpiricalBlockchainStructureEvidence",
    "PythiaStructureIntelligencePacket",
    "MiningGuardrailInputs",
    "MiningGuardrailReport",
    "StructureEvidenceStatus",
    "MiningLaunchDecision",
    "extract_empirical_structure_evidence",
    "build_pythia_structure_intelligence_packet",
    "evaluate_pythia_mining_guardrails",
    "load_empirical_report",
]
