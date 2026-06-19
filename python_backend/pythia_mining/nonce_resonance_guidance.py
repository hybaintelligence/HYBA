"""
PYTHIA Nonce Resonance Guidance Layer.

This module corrects the empirical evidence feed from a narrow Phi^15 detector into
a broader structure-seeking intelligence layer for PYTHIA mining.

Doctrine:
    - Mining is deterministic structured traversal, not blind brute force.
    - Empirical blockchain evidence is guidance for what to look for first.
    - Block height and difficulty are context, not decoration.
    - Dodecahedral and icosahedral domains provide the geometric search grammar.
    - PULVINI compresses the active search surface while retaining coverage.
    - Collapse/search selects priority regions, then exact SHA-256d verifies.
    - Sovereign cap: HYBA targets at most 24 accepted blocks/day and 1/hour.

Claim boundary:
    This module does not claim guaranteed block discovery. It gives PYTHIA a
    deterministic resonance guidance packet and a fail-closed launch/cap policy.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from math import log10
from typing import Any, Dict, List


PHI = (1.0 + 5.0**0.5) / 2.0
PHI_INV = PHI - 1.0
NONCE_SPACE = 1 << 32
RETARGET_EPOCH = 2016


class ResonanceSignal(str, Enum):
    """Structure signals PYTHIA should inspect in observed nonce history."""

    PHI15_RESONANCE = "phi15_resonance"
    GOLDEN_ANGLE_ALIGNMENT = "golden_angle_alignment"
    BIRTHDAY_ECHO = "birthday_echo"
    SECTOR_COVERAGE = "sector_coverage"
    LARGE_GAP_BOUNDARY = "large_gap_boundary"
    DODECAHEDRAL_DOMAIN = "dodecahedral_domain"
    ICOSAHEDRAL_FACE = "icosahedral_face"
    MASS_GAP_VALLEY = "mass_gap_valley"
    ENTANGLEMENT_SPECTRUM = "entanglement_spectrum"
    DIFFICULTY_PRESSURE = "difficulty_pressure"
    RETARGET_EPOCH_PHASE = "retarget_epoch_phase"


class SearchPhase(str, Enum):
    """Deterministic stages of the PYTHIA guided mining cycle."""

    OBSERVE_CHAIN_STRUCTURE = "observe_chain_structure"
    INTERPRET_BLOCK_CONTEXT = "interpret_block_context"
    BUILD_DODECA_ICOSA_PRIOR = "build_dodeca_icosa_prior"
    COMPRESS_WITH_PULVINI = "compress_with_pulvini"
    COLLAPSE_PRIORITY_REGIONS = "collapse_priority_regions"
    SEARCH_WITH_EXACT_SHA256D = "search_with_exact_sha256d"
    LEARN_FROM_POOL_OUTCOME = "learn_from_pool_outcome"


class MiningLaunchDecision(str, Enum):
    """Fail-closed launch decisions."""

    BLOCKED = "blocked"
    SUPERVISED_DRY_RUN = "supervised_dry_run"
    GUARDED_SEARCH_READY = "guarded_search_ready"


@dataclass(frozen=True)
class BlockContext:
    """Block-height and difficulty context for PYTHIA guidance."""

    block_height: int
    difficulty: float
    target_hex: str = ""
    previous_block_hash: str = ""
    mempool_pressure: float = 0.0

    @property
    def retarget_position(self) -> int:
        return self.block_height % RETARGET_EPOCH

    @property
    def retarget_phase(self) -> str:
        position = self.retarget_position
        if position < RETARGET_EPOCH * 0.25:
            return "early_epoch_exploration"
        if position < RETARGET_EPOCH * 0.75:
            return "mid_epoch_stabilisation"
        return "late_epoch_precision"

    @property
    def difficulty_pressure(self) -> float:
        """Bounded difficulty pressure used only as guidance weighting."""

        if self.difficulty <= 0:
            return 0.0
        # Bitcoin difficulty can be very large. The log compresses it into a
        # stable 0..1 guidance factor without turning it into a probability.
        return max(0.0, min(1.0, log10(self.difficulty) / 15.0))


@dataclass(frozen=True)
class EmpiricalStructureEvidence:
    """Observed blockchain-structure evidence for guidance, not guarantee."""

    sample_size: int
    phi15_rate: float = 0.0
    golden_angle_alignment: float = 0.0
    birthday_echo_rate: float = 0.0
    sector_coverage: float = 0.0
    large_gap_score: float = 0.0
    dodecahedral_domain_score: float = 0.0
    icosahedral_face_score: float = 0.0
    mass_gap_valley_score: float = 0.0
    entanglement_spectrum_score: float = 0.0
    uniformity_score: float = 0.0
    provenance: str = "empirical_blockchain_nonce_scan"

    def bounded_scores(self) -> Dict[str, float]:
        return {
            "phi15_rate": _clamp01(self.phi15_rate),
            "golden_angle_alignment": _clamp01(self.golden_angle_alignment),
            "birthday_echo_rate": _clamp01(self.birthday_echo_rate),
            "sector_coverage": _clamp01(self.sector_coverage),
            "large_gap_score": _clamp01(self.large_gap_score),
            "dodecahedral_domain_score": _clamp01(self.dodecahedral_domain_score),
            "icosahedral_face_score": _clamp01(self.icosahedral_face_score),
            "mass_gap_valley_score": _clamp01(self.mass_gap_valley_score),
            "entanglement_spectrum_score": _clamp01(self.entanglement_spectrum_score),
            "uniformity_score": _clamp01(self.uniformity_score),
        }

    def enough_evidence(self) -> bool:
        return self.sample_size >= 128 and max(self.bounded_scores().values()) > 0.0


@dataclass(frozen=True)
class ResonancePriority:
    """A specific structure signal weighted for the next guided search."""

    signal: ResonanceSignal
    weight: float
    reason: str


@dataclass(frozen=True)
class DodecaIcosaSearchPlan:
    """Dodecahedral/icosahedral prior that PYTHIA uses before collapse/search."""

    m32_domains: int = 32
    icosahedral_symmetry_order: int = 120
    dodecahedral_working_surface: int = 20
    full_nonce_coverage: int = NONCE_SPACE
    pulvini_retained_kernel: bool = True
    sha256d_final_oracle: bool = True
    coverage_must_remain_complete: bool = True


@dataclass(frozen=True)
class QuantumArsenalDirectives:
    """The combined mathematical arsenal PYTHIA may deploy."""

    quantum_mathematics_first: bool = True
    substrate_independent_execution: bool = True
    golden_ratio_grammar: bool = True
    tensor_network_prior: bool = True
    pulvin_memory_compression: bool = True
    hendrix_phi_traversal: bool = True
    dodecahedral_partitioning: bool = True
    icosahedral_symmetry: bool = True
    deutsch_criticism_feedback: bool = True
    exact_hash_verification: bool = True


@dataclass(frozen=True)
class SovereignMiningCap:
    """HYBA share cap: one accepted block per hour, twenty-four per day."""

    max_accepted_blocks_per_day: int = 24
    max_accepted_blocks_per_hour: int = 1
    accepted_blocks_today: int = 0
    accepted_blocks_current_hour: int = 0

    def allows_search(self) -> bool:
        return (
            self.accepted_blocks_today < self.max_accepted_blocks_per_day
            and self.accepted_blocks_current_hour < self.max_accepted_blocks_per_hour
        )

    def reason(self) -> str:
        if self.accepted_blocks_today >= self.max_accepted_blocks_per_day:
            return "daily sovereign cap reached: 24 accepted blocks/day"
        if self.accepted_blocks_current_hour >= self.max_accepted_blocks_per_hour:
            return "hourly sovereign cap reached: 1 accepted block/hour"
        return "sovereign cap open"


@dataclass(frozen=True)
class PythiaNonceResonanceGuidance:
    """Sealed guidance packet fed to PYTHIA before guided mining search."""

    protocol: str
    block_context: BlockContext
    empirical_evidence: EmpiricalStructureEvidence
    priorities: List[ResonancePriority]
    search_plan: DodecaIcosaSearchPlan
    arsenal: QuantumArsenalDirectives
    search_phases: List[SearchPhase]
    collapse_instruction: str
    claim_boundary: List[str]
    seal: str = ""

    def to_payload(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["priorities"] = [asdict(p) for p in self.priorities]
        payload["search_phases"] = [phase.value for phase in self.search_phases]
        payload["claim_boundary"] = list(self.claim_boundary)
        return payload

    def with_seal(self) -> "PythiaNonceResonanceGuidance":
        payload = self.to_payload()
        payload.pop("seal", None)
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return PythiaNonceResonanceGuidance(
            protocol=self.protocol,
            block_context=self.block_context,
            empirical_evidence=self.empirical_evidence,
            priorities=self.priorities,
            search_plan=self.search_plan,
            arsenal=self.arsenal,
            search_phases=self.search_phases,
            collapse_instruction=self.collapse_instruction,
            claim_boundary=self.claim_boundary,
            seal=hashlib.sha256(encoded).hexdigest(),
        )


@dataclass(frozen=True)
class MiningPreflight:
    """Preflight inputs for allowing PYTHIA into guarded search mode."""

    operator_approved: bool
    pool_credentials_present: bool
    exact_sha256d_enabled: bool
    full_coverage_preserved: bool
    evidence_packet_present: bool
    runtime_minutes: int
    power_limit_watts: float
    forbidden_claim_text: str = ""
    cap: SovereignMiningCap = field(default_factory=SovereignMiningCap)


@dataclass(frozen=True)
class MiningGuardrailReport:
    """Launch report for guarded deterministic search."""

    decision: MiningLaunchDecision
    blocked_reasons: List[str]
    guardrails: List[str]
    cap: SovereignMiningCap

    @property
    def allowed(self) -> bool:
        return self.decision == MiningLaunchDecision.GUARDED_SEARCH_READY


def build_nonce_resonance_guidance(
    evidence: EmpiricalStructureEvidence,
    context: BlockContext,
) -> PythiaNonceResonanceGuidance:
    """Build a broad nonce-resonance guidance packet for PYTHIA."""

    priorities = _rank_priorities(evidence, context)
    packet = PythiaNonceResonanceGuidance(
        protocol="PYTHIA_NONCE_RESONANCE_GUIDANCE_V2",
        block_context=context,
        empirical_evidence=evidence,
        priorities=priorities,
        search_plan=DodecaIcosaSearchPlan(),
        arsenal=QuantumArsenalDirectives(),
        search_phases=[
            SearchPhase.OBSERVE_CHAIN_STRUCTURE,
            SearchPhase.INTERPRET_BLOCK_CONTEXT,
            SearchPhase.BUILD_DODECA_ICOSA_PRIOR,
            SearchPhase.COMPRESS_WITH_PULVINI,
            SearchPhase.COLLAPSE_PRIORITY_REGIONS,
            SearchPhase.SEARCH_WITH_EXACT_SHA256D,
            SearchPhase.LEARN_FROM_POOL_OUTCOME,
        ],
        collapse_instruction=(
            "Collapse the dodecahedral/icosahedral priority surface into bounded solver "
            "ranges; preserve full nonce coverage through PULVINI retained kernels; "
            "verify every candidate with exact SHA-256d before submission."
        ),
        claim_boundary=[
            "Nonce evidence is general structure guidance, not Phi^15-only.",
            "Mining is deterministic structured traversal, not blind brute force.",
            "Block height and difficulty shape search weighting; they do not guarantee a block.",
            "Dodecahedral and icosahedral domains guide priority ordering.",
            "PULVINI may compress the active search surface only if reconstruction kernels preserve coverage.",
            "Collapse/search means priority collapse to solver ranges, not bypassing SHA-256d.",
            "Exact SHA-256d remains the final external oracle.",
            "Sovereign cap: maximum 24 accepted blocks/day and 1 accepted block/hour.",
        ],
    )
    return packet.with_seal()


def evaluate_mining_preflight(
    guidance: PythiaNonceResonanceGuidance | None,
    preflight: MiningPreflight,
) -> MiningGuardrailReport:
    """Evaluate whether PYTHIA may enter guarded deterministic search."""

    blocked: List[str] = []
    if guidance is None:
        blocked.append("missing nonce resonance guidance packet")
    elif not guidance.empirical_evidence.enough_evidence():
        blocked.append("insufficient empirical blockchain structure evidence")

    forbidden = preflight.forbidden_claim_text.lower()
    for phrase in ("guaranteed block", "guaranteed revenue", "bypass sha", "ignore coverage"):
        if phrase in forbidden:
            blocked.append(f"forbidden claim phrase: {phrase}")

    if not preflight.operator_approved:
        blocked.append("operator approval missing")
    if not preflight.pool_credentials_present:
        blocked.append("pool credentials missing")
    if not preflight.exact_sha256d_enabled:
        blocked.append("exact SHA-256d verifier disabled")
    if not preflight.full_coverage_preserved:
        blocked.append("full nonce coverage not preserved")
    if not preflight.evidence_packet_present:
        blocked.append("evidence packet missing")
    if preflight.runtime_minutes < 1 or preflight.runtime_minutes > 60:
        blocked.append("runtime must be bounded between 1 and 60 minutes")
    if preflight.power_limit_watts <= 0:
        blocked.append("positive power limit required")
    if not preflight.cap.allows_search():
        blocked.append(preflight.cap.reason())

    decision = (
        MiningLaunchDecision.GUARDED_SEARCH_READY if not blocked else MiningLaunchDecision.BLOCKED
    )
    return MiningGuardrailReport(
        decision=decision,
        blocked_reasons=blocked,
        guardrails=[
            "general nonce resonance evidence, not Phi^15-only",
            "block height and difficulty interpreted before search",
            "dodecahedral/icosahedral priority surface required",
            "PULVINI compression must retain reconstruction kernels",
            "collapse/search must preserve complete nonce coverage",
            "exact SHA-256d final verification required",
            "accepted-share/block outcome feeds Deutsch criticism loop",
            "sovereign cap: 24 accepted blocks/day and 1/hour",
            "operator abort remains available",
        ],
        cap=preflight.cap,
    )


def _rank_priorities(
    evidence: EmpiricalStructureEvidence,
    context: BlockContext,
) -> List[ResonancePriority]:
    scores = evidence.bounded_scores()
    difficulty_pressure = context.difficulty_pressure
    late_epoch_boost = 1.0 if context.retarget_phase == "late_epoch_precision" else 0.0

    weighted = [
        (
            ResonanceSignal.DODECAHEDRAL_DOMAIN,
            0.16 + 0.24 * scores["dodecahedral_domain_score"] + 0.05 * difficulty_pressure,
            "M32/dodecahedral domain pressure defines first search surface.",
        ),
        (
            ResonanceSignal.ICOSAHEDRAL_FACE,
            0.14 + 0.22 * scores["icosahedral_face_score"] + 0.04 * difficulty_pressure,
            "H3/Icosahedral symmetry rotates the surface before collapse.",
        ),
        (
            ResonanceSignal.MASS_GAP_VALLEY,
            0.12 + 0.22 * scores["mass_gap_valley_score"] + 0.05 * late_epoch_boost,
            "Mass-gap valleys become stronger near precision phase.",
        ),
        (
            ResonanceSignal.ENTANGLEMENT_SPECTRUM,
            0.10 + 0.20 * scores["entanglement_spectrum_score"],
            "Tensor spectrum guides where the quantum-formalism prior concentrates.",
        ),
        (
            ResonanceSignal.LARGE_GAP_BOUNDARY,
            0.08 + 0.18 * scores["large_gap_score"],
            "Large nonce gaps mark boundary conditions for region allocation.",
        ),
        (
            ResonanceSignal.SECTOR_COVERAGE,
            0.08 + 0.18 * scores["sector_coverage"],
            "Coverage score prevents collapse from becoming tunnel vision.",
        ),
        (
            ResonanceSignal.GOLDEN_ANGLE_ALIGNMENT,
            0.08 + 0.16 * scores["golden_angle_alignment"],
            "Golden-angle traces guide rotation through the phi grammar.",
        ),
        (
            ResonanceSignal.BIRTHDAY_ECHO,
            0.07 + 0.14 * scores["birthday_echo_rate"],
            "Echoes reveal repeated structural motifs across observed block nonces.",
        ),
        (
            ResonanceSignal.PHI15_RESONANCE,
            0.06 + 0.12 * scores["phi15_rate"],
            "Phi^15 remains one resonance lane, not the whole evidence feed.",
        ),
        (
            ResonanceSignal.DIFFICULTY_PRESSURE,
            difficulty_pressure,
            "Difficulty adjusts coverage and precision pressure for the next job.",
        ),
        (
            ResonanceSignal.RETARGET_EPOCH_PHASE,
            context.retarget_position / RETARGET_EPOCH,
            f"Retarget phase is {context.retarget_phase}.",
        ),
    ]
    ranked = sorted(weighted, key=lambda item: item[1], reverse=True)
    return [
        ResonancePriority(signal=signal, weight=round(_clamp01(weight), 6), reason=reason)
        for signal, weight, reason in ranked
    ]


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))
