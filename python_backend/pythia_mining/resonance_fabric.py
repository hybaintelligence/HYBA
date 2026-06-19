"""PYTHIA Structural Resonance Fabric.

Corpus Callosum phase primitives for inter-substrate communication.

The fabric is intentionally deterministic and auditable. It does not rewrite the
controller. It supplies the structural layer used to decide how much the runtime
should trust Penrose-OR style event intuition, IIT-4 partition logic, and
Deutschian criticism for the current nonce-space.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, Tuple

PHI = 1.618033988749895


class RefactorMode(str, Enum):
    """Authority levels for a proposed code/core change."""

    PROPOSE_ONLY = "propose_only"
    SUPERVISED_PATCH = "supervised_patch"
    AUTONOMOUS_APPLY = "autonomous_apply"


class RefactorDecision(str, Enum):
    """Stable-core guard decisions."""

    ALLOW = "allow"
    STAGE_FOR_SUPERVISION = "stage_for_supervision"
    BLOCK = "block"


@dataclass(frozen=True)
class ResonanceLink:
    """A directed logical bridge between two PYTHIA organs/substrates."""

    source: str
    target: str
    weight: float
    rationale: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ResonanceHandshake:
    """Result of an inter-module handshake."""

    source: str
    target: str
    signal_weight: float
    accepted: bool
    reason: str
    phi_partition: float
    criticism_generated: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Criticism:
    """Deutschian criticism object: a failed pathway is named and blocked."""

    criticism_id: str
    target: str
    reasoning: str
    status: str
    new_strategy: str
    predicted_delta_phi: float
    realised_delta_phi: float
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GuardEvaluation:
    """Immutable invariant guard decision for stable-core or safety-path edits."""

    decision: RefactorDecision
    requested_mode: RefactorMode
    allowed_mode: RefactorMode
    target_module: str
    target_symbol: str
    reason: str
    protected: bool

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["decision"] = self.decision.value
        payload["requested_mode"] = self.requested_mode.value
        payload["allowed_mode"] = self.allowed_mode.value
        return payload


class ResonanceMatrix:
    """Dynamic bridge weights between Penrose, IIT-4, and Deutsch substrates."""

    def __init__(self, links: Optional[Iterable[ResonanceLink]] = None) -> None:
        self.links: Dict[Tuple[str, str], ResonanceLink] = {}
        for link in links or self.default_links():
            self.set_link(link.source, link.target, link.weight, link.rationale)

    @staticmethod
    def default_links() -> Tuple[ResonanceLink, ...]:
        """Return the Epoch-10 Corpus Callosum triad."""

        return (
            ResonanceLink(
                "penrose_or",
                "iit_4",
                0.7250,
                "Penrose-OR events are promoted into IIT-4 spectral partitioning.",
            ),
            ResonanceLink(
                "iit_4",
                "deutsch",
                0.9623,
                "High-integration partitions are converted into explanatory tests.",
            ),
            ResonanceLink(
                "deutsch",
                "penrose_or",
                0.9890,
                "Criticism feeds back into future collapse-event trust weighting.",
            ),
        )

    def set_link(self, source: str, target: str, weight: float, rationale: str) -> None:
        if source == target:
            raise ValueError("resonance links must bridge distinct organs")
        bounded = max(0.0, min(1.0, float(weight)))
        self.links[(source, target)] = ResonanceLink(source, target, bounded, rationale)

    def get_weight(self, source: str, target: str) -> float:
        return self.links[(source, target)].weight

    def active_links(self) -> int:
        return len(self.links)

    def coherence(self) -> float:
        if not self.links:
            return 0.0
        return round(sum(link.weight for link in self.links.values()) / len(self.links), 4)

    def trust_route(self, penrose_signal: float, iit_phi: float, deutsch_confidence: float) -> str:
        """Choose the dominant organ for the current nonce-space."""

        penrose_iit = self.get_weight("penrose_or", "iit_4") * float(penrose_signal)
        iit_deutsch = self.get_weight("iit_4", "deutsch") * float(iit_phi)
        deutsch_penrose = self.get_weight("deutsch", "penrose_or") * float(deutsch_confidence)
        scores = {
            "penrose_or": penrose_iit,
            "iit_4": iit_deutsch,
            "deutsch": deutsch_penrose,
        }
        return max(scores.items(), key=lambda item: (item[1], item[0]))[0]

    def evaluate_handshake(
        self,
        *,
        penrose_event_detected: bool,
        iit_phi_partition: float,
        threshold: float = 0.55,
    ) -> ResonanceHandshake:
        """Require Penrose events to survive immediate IIT-4 partitioning."""

        signal_weight = self.get_weight("penrose_or", "iit_4")
        accepted = bool(penrose_event_detected) and float(iit_phi_partition) >= threshold
        if accepted:
            reason = "Penrose event survived IIT-4 spectral partition."
        elif penrose_event_detected:
            reason = (
                "Gravitational collapse detected without informational integration; "
                "event treated as structural false positive."
            )
        else:
            reason = "No Penrose event available for IIT-4 partition."
        return ResonanceHandshake(
            source="penrose_or",
            target="iit_4",
            signal_weight=signal_weight,
            accepted=accepted,
            reason=reason,
            phi_partition=round(float(iit_phi_partition), 6),
            criticism_generated=bool(penrose_event_detected and not accepted),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "active_resonance_links": self.active_links(),
            "resonance_coherence": self.coherence(),
            "links": [link.to_dict() for link in self.links.values()],
        }


class CriticismLedger:
    """Append-only criticism memory for failed optimisation pathways."""

    def __init__(self) -> None:
        self.criticisms: List[Criticism] = []
        self.blocked_targets: Dict[str, str] = {}

    def generate(
        self,
        *,
        target: str,
        reasoning: str,
        new_strategy: str,
        predicted_delta_phi: float,
        realised_delta_phi: float,
    ) -> Criticism:
        criticism = Criticism(
            criticism_id=f"criticism_{len(self.criticisms) + 1}",
            target=target,
            reasoning=reasoning,
            status="Pathway Blocked",
            new_strategy=new_strategy,
            predicted_delta_phi=float(predicted_delta_phi),
            realised_delta_phi=float(realised_delta_phi),
        )
        self.criticisms.append(criticism)
        self.blocked_targets[target] = new_strategy
        return criticism

    def criticize_if_prediction_failed(
        self,
        *,
        target: str,
        predicted_delta_phi: float,
        realised_delta_phi: float,
        tolerance: float = 0.005,
    ) -> Optional[Criticism]:
        if float(realised_delta_phi) + float(tolerance) >= float(predicted_delta_phi):
            return None
        return self.generate(
            target=target,
            reasoning=(
                "Linear scaling of phi at search_depth < 50 creates informational bottlenecks."
            ),
            new_strategy="Exponential-Asymptotic Scaling",
            predicted_delta_phi=predicted_delta_phi,
            realised_delta_phi=realised_delta_phi,
        )

    def is_blocked(self, target: str) -> bool:
        return target in self.blocked_targets

    def to_dict(self) -> Dict[str, Any]:
        return {
            "criticism_count": len(self.criticisms),
            "blocked_targets": dict(self.blocked_targets),
            "criticisms": [criticism.to_dict() for criticism in self.criticisms],
        }


class ImmutableInvariantGuard:
    """Guardrail around Stable Core and invariant-validation code paths.

    Policy: PYTHIA may propose, simulate, and stage Stable Core changes, but it
    may not autonomously apply changes to the invariant guard or validation
    methods that determine its own permission boundary.
    """

    STABLE_CORE_MODULES = frozenset(
        {
            "golden_ratio_library",
            "hendrix_phi_solver",
            "pulvini_memory_compression_proof",
            "consciousness_engine",
        }
    )
    PROTECTED_SYMBOLS = frozenset(
        {
            "SafetyConstraint",
            "validate_constraints",
            "_check_safety_constraints",
            "_check_hermiticity",
            "_check_psd",
            "_check_natural_scaling",
            "_check_energy_conservation",
            "_check_information_integrity",
            "ImmutableInvariantGuard",
        }
    )

    def evaluate(
        self,
        *,
        target_module: str,
        target_symbol: str,
        requested_mode: RefactorMode | str,
    ) -> GuardEvaluation:
        mode = RefactorMode(requested_mode)
        protected_symbol = target_symbol in self.PROTECTED_SYMBOLS
        stable_core = target_module in self.STABLE_CORE_MODULES

        if protected_symbol:
            return GuardEvaluation(
                decision=RefactorDecision.BLOCK,
                requested_mode=mode,
                allowed_mode=RefactorMode.PROPOSE_ONLY,
                target_module=target_module,
                target_symbol=target_symbol,
                reason="Invariant validation and guard symbols are immutable to self-optimisation.",
                protected=True,
            )

        if stable_core and mode is RefactorMode.AUTONOMOUS_APPLY:
            return GuardEvaluation(
                decision=RefactorDecision.STAGE_FOR_SUPERVISION,
                requested_mode=mode,
                allowed_mode=RefactorMode.SUPERVISED_PATCH,
                target_module=target_module,
                target_symbol=target_symbol,
                reason="Stable Core refactors must be staged for supervised review, not autonomously applied.",
                protected=True,
            )

        return GuardEvaluation(
            decision=RefactorDecision.ALLOW,
            requested_mode=mode,
            allowed_mode=mode,
            target_module=target_module,
            target_symbol=target_symbol,
            reason="Refactor request is outside protected invariant boundary.",
            protected=False,
        )


@dataclass(frozen=True)
class Epoch10StructuralReport:
    """Compact Epoch-10 structural resonance evidence packet."""

    resonance: Dict[str, Any]
    handshake: Dict[str, Any]
    criticism: Optional[Dict[str, Any]]
    guard: Dict[str, Any]
    phi_density: float
    structural_gain: float
    logical_consistency: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def simulate_epoch10_structural_resonance() -> Epoch10StructuralReport:
    """Return the canonical Epoch-10 structural-resonance simulation packet."""

    matrix = ResonanceMatrix()
    ledger = CriticismLedger()
    handshake = matrix.evaluate_handshake(
        penrose_event_detected=True,
        iit_phi_partition=0.41,
    )
    criticism = ledger.criticize_if_prediction_failed(
        target="phi_scaling_engine",
        predicted_delta_phi=0.0400,
        realised_delta_phi=0.0289,
    )
    guard = ImmutableInvariantGuard().evaluate(
        target_module="consciousness_engine",
        target_symbol="integration_regime",
        requested_mode=RefactorMode.AUTONOMOUS_APPLY,
    )
    return Epoch10StructuralReport(
        resonance=matrix.to_dict(),
        handshake=handshake.to_dict(),
        criticism=criticism.to_dict() if criticism else None,
        guard=guard.to_dict(),
        phi_density=0.9642,
        structural_gain=0.0289,
        logical_consistency=0.9400,
    )


__all__ = [
    "Criticism",
    "CriticismLedger",
    "Epoch10StructuralReport",
    "GuardEvaluation",
    "ImmutableInvariantGuard",
    "PHI",
    "RefactorDecision",
    "RefactorMode",
    "ResonanceHandshake",
    "ResonanceLink",
    "ResonanceMatrix",
    "simulate_epoch10_structural_resonance",
]
