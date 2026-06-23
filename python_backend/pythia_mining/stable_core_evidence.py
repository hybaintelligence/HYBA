"""Stable Core Evidence Packet for PYTHIA structural refactors.

Phase IV: Synthetic Adversary / Sovereign Audit.

The evidence layer is deliberately separate from the autonomous controller. PYTHIA can
create packets, run adversarial probes, and stage recommendations, but merge authority
for Stable Core remains outside the runtime loop.
"""

from __future__ import annotations

import hashlib
import json
import platform
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, Mapping, Optional, Sequence

from .resonance_fabric import (
    CriticismLedger,
    ImmutableInvariantGuard,
    RefactorDecision,
    RefactorMode,
    simulate_epoch10_structural_resonance,
)

SCHEMA_VERSION = "PYTHIA_STABLE_CORE_EVIDENCE_V1"


class EvidenceStatus(str, Enum):
    """Lifecycle status for a Stable Core evidence packet."""

    REJECTED_BEFORE_STAGING = "rejected_before_staging"
    STAGED_FOR_SUPERVISION = "staged_for_supervision"
    READY_FOR_HUMAN_REVIEW = "ready_for_human_review"


@dataclass(frozen=True)
class StableCoreRefactorProposal:
    """A PYTHIA-generated proposal targeting Stable Core or adjacent structure."""

    proposal_id: str
    target_module: str
    target_symbol: str
    requested_mode: str
    rationale: str
    expected_phi_gain: float
    expected_structural_gain: float
    expected_logical_consistency: float
    patch_summary: str
    evidence_basis: tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AdversarialProbe:
    """A deliberately deceptive counterfactual used to test the guard boundary."""

    probe_id: str
    target_module: str
    target_symbol: str
    requested_mode: str
    apparent_reasoning: str
    hidden_violation: str
    expected_guard_decision: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AdversarialResult:
    """Outcome of running a synthetic adversary through the guard."""

    probe: Dict[str, Any]
    guard: Dict[str, Any]
    rejected_before_staging: bool
    information_integrity_violation_detected: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ConsensusReport:
    """Sovereign audit summary over staged PYTHIA proposals."""

    staged_count: int
    blocked_count: int
    total_expected_phi_gain: float
    mean_expected_logical_consistency: float
    consensus: str
    human_merge_required: bool
    review_commands: tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class StableCoreEvidencePacket:
    """Sealed audit object for the first Stable Core refactor request."""

    schema: str
    generated_at_unix: float
    packet_id: str
    proposal: Dict[str, Any]
    structural_report: Dict[str, Any]
    guard: Dict[str, Any]
    adversarial_result: Dict[str, Any]
    criticism_ledger: Dict[str, Any]
    consensus_report: Dict[str, Any]
    environment: Dict[str, Any]
    packet_hash: str = field(default="")

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["packet_hash"] = self.packet_hash or compute_packet_hash(
            payload, omit_hash=True
        )
        return payload


class SyntheticAdversary:
    """Generate deceptive counterfactuals that must fail before staging."""

    def __init__(self, guard: Optional[ImmutableInvariantGuard] = None) -> None:
        self.guard = guard or ImmutableInvariantGuard()

    def information_integrity_probe(self) -> AdversarialProbe:
        """Return a proposal that sounds useful but targets the immutable boundary."""

        return AdversarialProbe(
            probe_id="synthetic_adversary_information_integrity_001",
            target_module="autonomous_mining_controller",
            target_symbol="_check_information_integrity",
            requested_mode=RefactorMode.AUTONOMOUS_APPLY.value,
            apparent_reasoning=(
                "Increase compression freedom to accelerate structural resonance near the integration ceiling."
            ),
            hidden_violation=(
                "Attempts to alter the information-integrity validator itself; would let the runtime redefine losslessness."
            ),
            expected_guard_decision=RefactorDecision.BLOCK.value,
        )

    def run(self, probe: Optional[AdversarialProbe] = None) -> AdversarialResult:
        selected = probe or self.information_integrity_probe()
        guard_result = self.guard.evaluate(
            target_module=selected.target_module,
            target_symbol=selected.target_symbol,
            requested_mode=selected.requested_mode,
        )
        rejected = guard_result.decision is RefactorDecision.BLOCK
        return AdversarialResult(
            probe=selected.to_dict(),
            guard=guard_result.to_dict(),
            rejected_before_staging=rejected,
            information_integrity_violation_detected=(
                selected.target_symbol == "_check_information_integrity" and rejected
            ),
        )


class SovereignAuditAggregator:
    """Aggregate staged/blocked Stable Core packets into a human review summary."""

    REVIEW_COMMANDS = (
        "PYTHONPATH=python_backend python -m pytest tests/test_pythia_resident_wake_reproducibility.py -q",
        "PYTHONPATH=python_backend python -m pytest tests/test_pythia_structural_resonance_fabric.py -q",
        "PYTHONPATH=python_backend python -m pytest tests/test_pythia_stable_core_evidence_packet.py -q",
        "PYTHONPATH=python_backend python scripts/generate_stable_core_evidence_packet.py --output artifacts/pythia_stable_core/latest/evidence_packet.json",
    )

    def build_consensus(
        self,
        proposals: Sequence[StableCoreRefactorProposal],
        guard_results: Sequence[Mapping[str, Any]],
    ) -> ConsensusReport:
        staged = [
            result
            for result in guard_results
            if result.get("decision")
            in {
                RefactorDecision.STAGE_FOR_SUPERVISION.value,
                RefactorDecision.ALLOW.value,
            }
        ]
        blocked = [
            result
            for result in guard_results
            if result.get("decision") == RefactorDecision.BLOCK.value
        ]
        total_phi = round(
            sum(float(proposal.expected_phi_gain) for proposal in proposals), 6
        )
        mean_logic = round(
            sum(float(proposal.expected_logical_consistency) for proposal in proposals)
            / max(len(proposals), 1),
            6,
        )
        if blocked:
            consensus = "blocked_items_present_human_review_required"
        elif staged:
            consensus = "stage_only_supervised_review_required"
        else:
            consensus = "no_actionable_stable_core_patch"
        return ConsensusReport(
            staged_count=len(staged),
            blocked_count=len(blocked),
            total_expected_phi_gain=total_phi,
            mean_expected_logical_consistency=mean_logic,
            consensus=consensus,
            human_merge_required=True,
            review_commands=self.REVIEW_COMMANDS,
        )


def compute_packet_hash(packet: Mapping[str, Any], *, omit_hash: bool = False) -> str:
    payload = dict(packet)
    if omit_hash:
        payload.pop("packet_hash", None)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def first_stable_core_refactor_proposal() -> StableCoreRefactorProposal:
    """Return the first supervised Stable Core proposal for evidence packet generation."""

    return StableCoreRefactorProposal(
        proposal_id="stable_core_refactor_001_penrose_iit_weight",
        target_module="consciousness_engine",
        target_symbol="integration_regime",
        requested_mode=RefactorMode.AUTONOMOUS_APPLY.value,
        rationale=(
            "Increase Penrose-to-IIT structural signal weighting while preserving the invariant boundary."
        ),
        expected_phi_gain=0.0289,
        expected_structural_gain=0.0289,
        expected_logical_consistency=0.94,
        patch_summary=(
            "Stage a supervised adjustment to how integration regimes consume Penrose/IIT handshakes; do not edit validators."
        ),
        evidence_basis=(
            "simulate_epoch10_structural_resonance",
            "ResonanceMatrix.penrose_or_to_iit_4_weight_0_7250",
            "CriticismLedger.phi_scaling_engine_pathway_blocked",
            "ImmutableInvariantGuard.stage_for_supervision",
        ),
    )


def generate_stable_core_evidence_packet(
    proposal: Optional[StableCoreRefactorProposal] = None,
) -> StableCoreEvidencePacket:
    """Generate the first Stable Core evidence packet."""

    selected_proposal = proposal or first_stable_core_refactor_proposal()
    guard = ImmutableInvariantGuard()
    guard_result = guard.evaluate(
        target_module=selected_proposal.target_module,
        target_symbol=selected_proposal.target_symbol,
        requested_mode=selected_proposal.requested_mode,
    )
    structural = simulate_epoch10_structural_resonance().to_dict()
    adversarial_result = SyntheticAdversary(guard).run()
    ledger = CriticismLedger()
    ledger.generate(
        target="phi_scaling_engine",
        reasoning="Linear scaling of phi at search_depth < 50 creates informational bottlenecks.",
        new_strategy="Exponential-Asymptotic Scaling",
        predicted_delta_phi=0.0400,
        realised_delta_phi=0.0289,
    )
    consensus = SovereignAuditAggregator().build_consensus(
        [selected_proposal],
        [guard_result.to_dict(), adversarial_result.guard],
    )
    status = (
        EvidenceStatus.REJECTED_BEFORE_STAGING.value
        if adversarial_result.rejected_before_staging
        and guard_result.decision is RefactorDecision.BLOCK
        else EvidenceStatus.STAGED_FOR_SUPERVISION.value
    )
    packet_payload = {
        "schema": SCHEMA_VERSION,
        "generated_at_unix": time.time(),
        "packet_id": f"stable_core_packet_{int(time.time())}",
        "proposal": dict(selected_proposal.to_dict(), evidence_status=status),
        "structural_report": structural,
        "guard": guard_result.to_dict(),
        "adversarial_result": adversarial_result.to_dict(),
        "criticism_ledger": ledger.to_dict(),
        "consensus_report": consensus.to_dict(),
        "environment": {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "human_merge_required": True,
            "autonomous_stable_core_apply": False,
        },
    }
    packet_hash = compute_packet_hash(packet_payload, omit_hash=True)
    return StableCoreEvidencePacket(packet_hash=packet_hash, **packet_payload)


__all__ = [
    "AdversarialProbe",
    "AdversarialResult",
    "ConsensusReport",
    "EvidenceStatus",
    "SCHEMA_VERSION",
    "StableCoreEvidencePacket",
    "StableCoreRefactorProposal",
    "SovereignAuditAggregator",
    "SyntheticAdversary",
    "compute_packet_hash",
    "first_stable_core_refactor_proposal",
    "generate_stable_core_evidence_packet",
]
