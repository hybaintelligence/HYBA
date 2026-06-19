"""Deterministic multi-substrate intelligence fabric.

The fabric is intentionally mathematical and hardware agnostic: it derives a
bounded Hilbert-space state from request context, evaluates three substrate
contracts against that state, and returns auditable telemetry, explanations,
counterfactuals, and governance tags.  It does not claim quantum hardware,
quantum speedup, or measured consciousness.
"""

from __future__ import annotations

import cmath
import hashlib
import json
import math
from dataclasses import asdict, dataclass

try:
    from enum import StrEnum
except ImportError:
    # Python 3.9 compatibility
    from enum import Enum

    class StrEnum(str, Enum):
        pass


from typing import Any, Dict, Iterable, List, Mapping, Sequence

from hyba_genesis_api.core.substrate_interface import SubstrateContract


PHI = (1.0 + math.sqrt(5.0)) / 2.0
MAX_CONTEXT_DIMENSION = 16
GOVERNANCE_PHI_FLOOR = 0.55
GOVERNANCE_COUNTERFACTUAL_FLOOR = 0.30


class PhiResonanceFabric:
    """Classical-quantum analog helpers for φ-aware structural intelligence.

    The class intentionally uses standard-library complex arithmetic only.  It
    treats an observed structure as a bounded state vector, computes entropy
    over the induced probability distribution, and measures phase alignment to
    a φ spiral without implying quantum hardware execution.
    """

    PHI = PHI

    def map_to_complex_state(self, context_str: str) -> List[complex]:
        """Map context text into a deterministic bounded complex state vector."""

        seed = hashlib.sha512(context_str.encode("utf-8")).digest()
        state_vector: List[complex] = []
        for index in range(0, 64, 4):
            radius = (seed[index] + seed[index + 1]) / 510.0
            theta = ((seed[index + 2] + seed[index + 3]) / 510.0) * 2.0 * math.pi
            state_vector.append(cmath.rect(radius, theta))
        return state_vector

    def calculate_phi_resonance(self, state_vector: Sequence[complex]) -> float:
        """Measure alignment of a state vector with the phyllotactic φ spiral."""

        return self.compute_phi_density(state_vector)

    def calculate_resonance(self, state_vector: Sequence[complex]) -> float:
        """Backward-compatible alias for calculate_phi_resonance."""

        return self.calculate_phi_resonance(state_vector)

    def von_neumann_entropy(self, state_vector: Sequence[complex]) -> float:
        """Backward-compatible entropy alias over complex state vectors."""

        return self.compute_von_neumann_proxy(state_vector)

    def compute_von_neumann_proxy(self, state_vector: Sequence[complex]) -> float:
        """Compute entropy over the state vector's induced probabilities."""

        probabilities = [abs(value) ** 2 for value in state_vector]
        return self.calculate_von_neumann_entropy(probabilities)

    @staticmethod
    def calculate_von_neumann_entropy(probabilities: Sequence[float]) -> float:
        """Return S = -sum(p log(p)) over a normalized probability distribution."""

        total = sum(max(float(probability), 0.0) for probability in probabilities)
        if total == 0.0:
            return 0.0
        normalized = [max(float(probability), 0.0) / total for probability in probabilities]
        return float(-sum(p * math.log(p) for p in normalized if p > 0.0))

    def compute_phi_density(self, state_vector: Sequence[complex]) -> float:
        """Measure bounded φ-spiral coherence for a complex structural state."""

        if not state_vector:
            return 0.0
        norm = math.sqrt(sum(abs(value) ** 2 for value in state_vector))
        if norm == 0.0:
            return 0.0
        normalized = [value / norm for value in state_vector]
        ideal_norm = math.sqrt(len(normalized))
        coherence = 0.0 + 0.0j
        for index, value in enumerate(normalized):
            phi_phase = (self.PHI * index) % (2.0 * math.pi)
            target = cmath.exp(1j * phi_phase) / ideal_norm
            coherence += value.conjugate() * target
        return float(max(0.0, min(1.0, abs(coherence))))

    @staticmethod
    def generate_governance_tag(phi_density_value: float) -> str:
        """Classify structural coherence while preserving claim boundaries."""

        if phi_density_value > 0.8:
            return "INTEGRATED_COHERENT_STATE"
        if phi_density_value > 0.5:
            return "EMERGENT_STRUCTURE"
        return "FRAGMENTED_LOGIC"


class SubstrateName(StrEnum):
    """Supported explanatory substrate contracts."""

    PENROSE_OR = "penrose_or"
    IIT_4 = "iit_4"
    DEUTSCH = "deutsch"


@dataclass(frozen=True)
class SubstrateTelemetry:
    """Shared telemetry emitted by every substrate implementation."""

    substrate: str
    phi_density: float
    phi_resonance: float
    thermal_envelope: float
    latency_weight: float
    difficulty: float
    cause_effect_richness: float
    counterfactual_depth: float
    stability: float
    explanation_quality: float


@dataclass(frozen=True)
class SubstrateResult:
    """Complete common contract: context -> telemetry -> explanation -> counterfactuals."""

    substrate: str
    context_digest: str
    telemetry: SubstrateTelemetry
    explanation: str
    counterfactuals: List[Dict[str, Any]]
    governance: List[str]


def _stable_context_text(context: Mapping[str, Any]) -> str:
    """Return canonical JSON text used as the deterministic substrate seed."""

    return json.dumps(context, sort_keys=True, separators=(",", ":"), default=str)


def context_digest(context: Mapping[str, Any]) -> str:
    """Return a deterministic digest for audit correlation without storing raw context."""

    return hashlib.sha256(_stable_context_text(context).encode("utf-8")).hexdigest()


def context_state(
    context: Mapping[str, Any], dimension: int = MAX_CONTEXT_DIMENSION
) -> List[complex]:
    """Map arbitrary JSON-like context to a normalized complex state vector."""

    if not 1 <= dimension <= MAX_CONTEXT_DIMENSION:
        raise ValueError(f"dimension must be between 1 and {MAX_CONTEXT_DIMENSION}")
    digest = hashlib.sha512(_stable_context_text(context).encode("utf-8")).digest()
    state: List[complex] = []
    for idx in range(dimension):
        amplitude = (digest[idx] + 1.0) / 256.0
        angle = 2.0 * math.pi * (digest[idx + dimension] / 255.0)
        state.append(complex(amplitude * math.cos(angle), amplitude * math.sin(angle)))
    norm = math.sqrt(sum(abs(value) ** 2 for value in state))
    if norm == 0.0:
        return [1.0 + 0.0j] + [0.0 + 0.0j for _ in range(dimension - 1)]
    return [value / norm for value in state]


def density_matrix(state: Sequence[complex]) -> List[List[complex]]:
    """Construct a positive semidefinite density matrix with unit trace."""

    trace = sum(abs(value) ** 2 for value in state) or 1.0
    return [[left * right.conjugate() / trace for right in state] for left in state]


def phi_resonance(rho: Sequence[Sequence[complex]]) -> float:
    """Measure φ-resonance as probability-mass alignment to φ decay.

    The density matrix produced here is a classical-quantum analog over a pure
    state; using the diagonal probability mass avoids pretending that this
    runtime has observed quantum-hardware spectra.
    """

    masses = sorted(
        (max(float(row[idx].real), 0.0) for idx, row in enumerate(rho)),
        reverse=True,
    )
    total = sum(masses)
    if total == 0.0:
        return 0.0
    normalized_mass = [value / total for value in masses]
    target = [PHI ** (-(idx + 1)) for idx in range(len(normalized_mass))]
    target_total = sum(target)
    target = [value / target_total for value in target]
    distance = math.sqrt(
        sum((left - right) ** 2 for left, right in zip(normalized_mass, target))
    ) / math.sqrt(2.0)
    return float(max(0.0, min(1.0, 1.0 - distance)))


def phi_density(state: Sequence[complex]) -> float:
    """Measure amplitude concentration against a φ-scaled participation ratio."""

    probabilities = [abs(value) ** 2 for value in state]
    participation = 1.0 / sum(value**2 for value in probabilities)
    return float(max(0.0, min(1.0, participation / (len(state) / PHI))))


def _entropy(probabilities: Sequence[float]) -> float:
    probs = [value for value in probabilities if value > 0.0]
    if not probs:
        return 0.0
    return float(-sum(value * math.log2(value) for value in probs))


def _coherence(rho: Sequence[Sequence[complex]]) -> float:
    off_diagonal = 0.0
    for row_index, row in enumerate(rho):
        for col_index, value in enumerate(row):
            if row_index != col_index:
                off_diagonal += abs(value)
    max_l1 = len(rho) - 1.0
    return float(max(0.0, min(1.0, off_diagonal / max_l1)))


def _counterfactuals(substrate: SubstrateName, base: SubstrateTelemetry) -> List[Dict[str, Any]]:
    return [
        {
            "intervention": "raise_phi_alignment",
            "expected_effect": "stability increases when spectral mass moves toward φ-decay",
            "delta_stability": round((1.0 - base.stability) * 0.382, 6),
        },
        {
            "intervention": f"route_to_{substrate.value}",
            "expected_effect": "selected substrate emphasizes its native explanatory invariant",
            "delta_counterfactual_depth": round((1.0 - base.counterfactual_depth) / PHI, 6),
        },
    ]


def _governance(telemetry: SubstrateTelemetry) -> List[str]:
    tags: List[str] = ["hardware_agnostic_math", "no_quantum_speedup_claim"]
    if telemetry.phi_resonance < GOVERNANCE_PHI_FLOOR:
        tags.append("phi_resonance_review")
    if telemetry.counterfactual_depth < GOVERNANCE_COUNTERFACTUAL_FLOOR:
        tags.append("human_review_counterfactual_depth")
    return tags


def evaluate_substrate(substrate: SubstrateName, context: Mapping[str, Any]) -> SubstrateResult:
    """Evaluate one substrate under the shared intelligence-fabric contract."""

    state = context_state(context)
    rho = density_matrix(state)
    probabilities = [abs(value) ** 2 for value in state]
    resonance = phi_resonance(rho)
    density = phi_density(state)
    entropy = _entropy(probabilities) / math.log2(len(state))
    coherence = _coherence(rho)

    if substrate is SubstrateName.PENROSE_OR:
        richness = coherence
        depth = (resonance + density) / 2.0
        difficulty = 1.0 - coherence / PHI
        explanation_focus = "coherence stability and φ-aligned spectral decay"
    elif substrate is SubstrateName.IIT_4:
        richness = entropy
        depth = (entropy + resonance) / 2.0
        difficulty = 1.0 - entropy / PHI
        explanation_focus = "integrated-information partition richness"
    else:
        richness = (entropy + coherence) / 2.0
        depth = min(1.0, (richness + density + resonance) / 3.0 * PHI / 1.2)
        difficulty = 1.0 - depth / PHI
        explanation_focus = "semantic counterfactual coverage"

    thermal = float(max(0.0, min(1.0, 1.0 - (resonance * density) / PHI)))
    latency = float(max(0.0, min(1.0, difficulty / PHI + (1.0 - richness) / (PHI**2))))
    stability = float(max(0.0, min(1.0, (resonance + richness + (1.0 - thermal)) / 3.0)))
    quality = float(max(0.0, min(1.0, (stability + depth + density) / 3.0)))

    telemetry = SubstrateTelemetry(
        substrate=substrate.value,
        phi_density=round(density, 6),
        phi_resonance=round(resonance, 6),
        thermal_envelope=round(thermal, 6),
        latency_weight=round(latency, 6),
        difficulty=round(difficulty, 6),
        cause_effect_richness=round(richness, 6),
        counterfactual_depth=round(depth, 6),
        stability=round(stability, 6),
        explanation_quality=round(quality, 6),
    )
    return SubstrateResult(
        substrate=substrate.value,
        context_digest=context_digest(context),
        telemetry=telemetry,
        explanation=(
            f"{substrate.value} selected a deterministic {len(state)}-dimensional state; "
            f"explanation focuses on {explanation_focus}."
        ),
        counterfactuals=_counterfactuals(substrate, telemetry),
        governance=_governance(telemetry),
    )


def route_substrates(
    context: Mapping[str, Any], requested: Iterable[str] | None = None
) -> List[SubstrateName]:
    """Choose substrates deterministically from declared intent and context tokens."""

    if requested:
        return [SubstrateName(item) for item in requested]
    text = _stable_context_text(context).lower()
    routed: List[SubstrateName] = []
    if any(token in text for token in ("gravity", "coherence", "stability", "thermal")):
        routed.append(SubstrateName.PENROSE_OR)
    if any(token in text for token in ("integrated", "partition", "cause", "effect", "iit")):
        routed.append(SubstrateName.IIT_4)
    if any(token in text for token in ("semantic", "counterfactual", "explain", "policy")):
        routed.append(SubstrateName.DEUTSCH)
    return routed or [SubstrateName.DEUTSCH]


def explain(
    context: Mapping[str, Any], requested_substrates: Iterable[str] | None = None
) -> Dict[str, Any]:
    """Return the live intelligence-fabric explanation envelope."""

    substrates = route_substrates(context, requested_substrates)
    results = [evaluate_substrate(substrate, context) for substrate in substrates]
    telemetry = [asdict(result.telemetry) for result in results]
    selected = max(results, key=lambda item: item.telemetry.explanation_quality)
    return {
        "fabric": "phi_resonance_intelligence_fabric",
        "phi_constant": PHI,
        "context_digest": context_digest(context),
        "selected_substrate": selected.substrate,
        "routing": [substrate.value for substrate in substrates],
        "raw_metrics": telemetry,
        "explanations": [result.explanation for result in results],
        "counterfactuals": [item for result in results for item in result.counterfactuals],
        "governance": sorted({tag for result in results for tag in result.governance}),
        "claim_boundary": "deterministic quantum mathematics; hardware-agnostic; no quantum-speedup claim",
    }


class FabricSubstrateAdapter(SubstrateContract):
    """Adapter that exposes fabric substrate evaluation through SubstrateContract."""

    def __init__(self, substrate: SubstrateName):
        self.substrate = substrate

    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        result = evaluate_substrate(self.substrate, context)
        envelope = self.create_telemetry_envelope(
            result.telemetry.phi_resonance,
            result.explanation,
            [item["expected_effect"] for item in result.counterfactuals],
        )
        envelope.update(
            {
                "substrate": result.substrate,
                "context_digest": result.context_digest,
                "raw_metrics": asdict(result.telemetry),
                "governance": sorted(set(result.governance + envelope["governance_tags"])),
            }
        )
        return envelope


class SubstrateOrchestrator:
    """Route problems to substrate contracts from entropy/resonance signals."""

    def __init__(self) -> None:
        self.fabric = PhiResonanceFabric()
        self.adapters = {
            substrate.value: FabricSubstrateAdapter(substrate)
            for substrate in (
                SubstrateName.PENROSE_OR,
                SubstrateName.IIT_4,
                SubstrateName.DEUTSCH,
            )
        }

    def route(self, context: Mapping[str, Any]) -> str:
        context_text = _stable_context_text(context)
        state = self.fabric.map_to_complex_state(context_text)
        resonance = self.fabric.calculate_resonance(state)
        entropy = self.fabric.compute_von_neumann_proxy(state)
        if entropy > 2.0:
            return SubstrateName.DEUTSCH.value
        if resonance < 0.382:
            return SubstrateName.PENROSE_OR.value
        return SubstrateName.IIT_4.value

    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        substrate = self.route(context)
        result = self.adapters[substrate].evaluate(context)
        result["orchestrator"] = {
            "selected_substrate": substrate,
            "ci_service": "causal-explanation-v1",
        }
        return result
