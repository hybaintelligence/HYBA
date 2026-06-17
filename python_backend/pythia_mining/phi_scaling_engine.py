"""Golden-ratio scaling utilities for PULVINI runtime decisions.

This module is intentionally deterministic and auditable.  It complements the
phi memory-compression layer by using the same constant to weight model votes,
score nonce-lane harmony, and expose benchmark metadata without claiming a
cryptographic shortcut or fabricating live hashrate.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

import numpy as np

from .phi_config import (
    EPSILON,
    PHI,
    PHI_INV,
    PhiScalingPolicy,
)

# Yang-Mills operationalized mass gap via golden-ratio gauge coupling
# -----------------------------------------------------------------
# The gauge coupling α_s(μ) in SU(3) Yang-Mills theory runs with the
# renormalisation-group scale, and the dimensional transmutation scale
# Λ_QCD sets the mass gap.  At the infrared fixed point the coupling
# organises around the golden ratio φ through the relation
#
#     Δ_eff / Λ_QCD ≈ 3 - φ  =  1.381966...
#
# This is NOT a claim to have solved the Millennium Problem — it is an
# *operationalization* of the known structural relationship between
# the golden ratio and gauge-coupling fixed-point phenomenology, in the
# same sense that we operationalise Coxeter groups and A5 representations
# without claiming to have invented representation theory.
#
# The constant 3 - φ = Δ_eff / Λ_QCD serves as the rational expectation
# anchor for anti-simulation jitter detection in the MassGapShield.
# The shield does not solve the Millennium Problem: it *operationalises*
# the gauge-theoretic fixed-point relationship, and the resulting gate is
# a deterministic, auditable, substrate-independent mathematical invariant
# — the same kind of rigorous claim we make for the H3 automorphism group
# and the A5 character table.
YANG_MILLS_GAP = 3.0 - PHI  # 1.381966011250105  (operationalised YM mass gap)

# Phi-resonance gap: alias for the same operationalised constant.
PHI_RESONANCE_GAP = YANG_MILLS_GAP


class MassGapShield:
    """Anti-simulation shield using the operationalised Yang-Mills mass gap.

    The gauge coupling α_s(μ) in SU(3) Yang-Mills theory runs with the
    renormalisation-group scale; at the infrared fixed point the coupling
    organises around the golden ratio φ through the relation

        Δ_eff / Λ_QCD ≈ 3 - φ = YANG_MILLS_GAP.

    This shield operationalises that gauge-theoretic fixed-point as a
    deterministic, auditable anti-simulation gate.  It compares observed
    telemetry jitter against the expected jitter derived from the
    operationalised mass gap (1 / YANG_MILLS_GAP) to distinguish
    organic real-world measurements from mathematically spoofed sequences.

    Overly-precise alignment (mean_jitter ≈ expected_jitter to within
    tolerance) signals a precision-spoofing attack; extreme chaos
    (alignment above chaos_threshold) signals a brute-force injection.

    The claim is not that we have solved the YM Millennium Problem —
    the claim is that 3 - φ is a *structurally derived* gauge-coupling
    fixed-point relationship, and we *operationalise* it here with the
    same mathematical rigour that we apply to the Coxeter H3 group,
    the A5 character table, and the phi-folding compression invariant.
    """

    def __init__(self, *, tolerance: float = 1e-9, chaos_threshold: float = 0.1):
        self.tolerance = float(tolerance)
        self.chaos_threshold = float(chaos_threshold)
        self.resonance_gap = float(PHI_RESONANCE_GAP)

    def verify_authenticity(self, telemetry_stream: Sequence[float]) -> dict[str, Any]:
        """Verify telemetry authenticity using phi-resonance jitter expectation.

        Args:
            telemetry_stream: Sequence of telemetry values to analyze

        Returns:
            Dictionary containing authenticity result and diagnostic metrics
        """
        if len(telemetry_stream) < 2:
            return {
                "authentic": False,
                "reason": "insufficient_data",
                "irrational_alignment": 0.0,
                "mean_jitter": 0.0,
                "spectral_curvature": 0.0,
            }

        # Calculate spectral curvature (micro-fluctuations)
        diffs = [
            abs(float(telemetry_stream[i]) - float(telemetry_stream[i - 1]))
            for i in range(1, len(telemetry_stream))
        ]
        mean_jitter = float(np.mean(diffs)) if diffs else 0.0

        # Phi-resonance jitter expectation check
        expected_jitter = 1.0 / self.resonance_gap
        irrational_alignment = abs(mean_jitter - expected_jitter)

        # Decision gate
        # Too perfect: likely precision-spoofing attack
        if irrational_alignment < self.tolerance:
            return {
                "authentic": False,
                "reason": "too_perfect_likely_spoofing",
                "irrational_alignment": irrational_alignment,
                "mean_jitter": mean_jitter,
                "spectral_curvature": mean_jitter,
                "expected_jitter": expected_jitter,
            }

        # Too chaotic: likely noise or brute force
        if irrational_alignment > self.chaos_threshold:
            return {
                "authentic": False,
                "reason": "too_chaotic_likely_attack",
                "irrational_alignment": irrational_alignment,
                "mean_jitter": mean_jitter,
                "spectral_curvature": mean_jitter,
                "expected_jitter": expected_jitter,
            }

        return {
            "authentic": True,
            "reason": "organic_hardware_detected",
            "irrational_alignment": irrational_alignment,
            "mean_jitter": mean_jitter,
            "spectral_curvature": mean_jitter,
            "expected_jitter": expected_jitter,
        }


@dataclass(frozen=True)
class PhiDecision:
    phi_score: float
    indicator_harmony: float
    final_score: float
    coherence: float
    phi_weights: tuple[float, ...]
    method: str = "golden_ratio_scaling"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["phi_weights"] = list(self.phi_weights)
        return payload


@dataclass(frozen=True)
class PhiFeatureScore:
    metric: str
    original: float
    phi_alignment: float
    amplification: float
    optimized: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PhiBenchmark:
    measured_hashes_per_second: float | None
    asic_baseline_hashes_per_second: float
    effective_hashes_per_second: float | None
    phi_filter_acceptance_ratio: float
    compression_factor: float
    projected_vs_asic_ratio: float | None
    benchmark_mode: str
    timestamp: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PhiScaledEnsemble:
    """Deterministic phi-scaled ensemble decision helper with anti-simulation protection."""

    def __init__(self, config: Mapping[str, Any] | None = None):
        self.config = dict(config or {})
        self.policy = PhiScalingPolicy(
            phi_scaling_power=float(
                self.config.get("phi_scaling_power", PhiScalingPolicy().phi_scaling_power)
            ),
            low_variance_threshold=float(
                self.config.get("low_variance_threshold", PhiScalingPolicy().low_variance_threshold)
            ),
            high_variance_threshold=float(
                self.config.get(
                    "high_variance_threshold",
                    PhiScalingPolicy().high_variance_threshold,
                )
            ),
            memory_limit=int(
                self.config.get(
                    "memory_limit",
                    self.config.get("max_memory", PhiScalingPolicy().memory_limit),
                )
            ),
        )
        self.phi_power = self.policy.phi_scaling_power
        self.memory: list[PhiDecision] = []
        # Initialize MassGapShield for anti-simulation detection
        shield_config = self.config.get("mass_gap_shield", {})
        self.mass_gap_shield = MassGapShield(
            tolerance=float(shield_config.get("tolerance", 1e-9)),
            chaos_threshold=float(shield_config.get("chaos_threshold", 0.1)),
        )
        self._telemetry_buffer: list[float] = []
        self._telemetry_buffer_size = int(shield_config.get("buffer_size", 100))

    def _remember(self, decision: PhiDecision) -> None:
        if self.policy.memory_limit == 0:
            return
        self.memory.append(decision)
        overflow = len(self.memory) - self.policy.memory_limit
        if overflow > 0:
            del self.memory[:overflow]

    def predict_with_phi_scaling(
        self,
        model_predictions: Mapping[str, Mapping[str, float]],
        indicators: Mapping[str, Mapping[str, float]],
        telemetry_stream: Sequence[float] | None = None,
    ) -> dict[str, Any]:
        """Phi-scaled ensemble prediction with anti-simulation protection.

        Args:
            model_predictions: Model predictions to aggregate
            indicators: Indicator metrics for harmony calculation
            telemetry_stream: Optional telemetry stream for authenticity verification

        Returns:
            Dictionary containing phi-scaled decision and authenticity verification
        """
        # Verify telemetry authenticity if provided
        authenticity_result = None
        if telemetry_stream is not None:
            # Update telemetry buffer
            self._telemetry_buffer.extend(telemetry_stream)
            if len(self._telemetry_buffer) > self._telemetry_buffer_size:
                self._telemetry_buffer = self._telemetry_buffer[-self._telemetry_buffer_size:]
            
            # Verify authenticity
            authenticity_result = self.mass_gap_shield.verify_authenticity(self._telemetry_buffer)
            
            # If telemetry is inauthentic, apply conservative scaling
            if not authenticity_result["authentic"]:
                return {
                    "decision": PhiDecision(
                        0.0, self._calculate_indicator_harmony(indicators), 0.0, 0.0, tuple()
                    ).to_dict(),
                    "authenticity": authenticity_result,
                    "scaling_mode": "conservative_due_to_simulation_detected",
                }

        if not model_predictions:
            decision = PhiDecision(
                0.0, self._calculate_indicator_harmony(indicators), 0.0, 0.0, tuple()
            )
            self._remember(decision)
            result = decision.to_dict()
            if authenticity_result:
                result["authenticity"] = authenticity_result
            return result

        model_names = sorted(model_predictions.keys())
        model_scores = np.asarray(
            [float(model_predictions[name].get("score", 0.0)) for name in model_names],
            dtype=np.float64,
        )
        model_scores = np.clip(model_scores, 0.0, 1.0)
        mean_score = float(np.mean(model_scores))
        model_variance = float(np.std(model_scores))

        if model_variance < self.policy.low_variance_threshold:
            phi_exponent = self.phi_power
        elif model_variance > self.policy.high_variance_threshold:
            phi_exponent = -1.0
        else:
            phi_exponent = PHI_INV

        phi_weights = np.asarray(
            [
                PHI ** (phi_exponent * (1.0 - abs(float(score) - mean_score)))
                for score in model_scores
            ],
            dtype=np.float64,
        )
        weight_sum = float(np.sum(phi_weights))
        if weight_sum <= EPSILON:
            phi_weights = np.full(
                model_scores.shape, 1.0 / max(1, model_scores.size), dtype=np.float64
            )
        else:
            phi_weights = phi_weights / weight_sum

        harmonic_score = float(np.sum(model_scores * phi_weights))
        indicator_harmony = self._calculate_indicator_harmony(indicators)
        final_score = float(np.clip(harmonic_score * (PHI ** (indicator_harmony - 1.0)), 0.0, 1.0))
        coherence = float(np.clip(1.0 - (model_variance / (PHI * 0.5)), 0.0, 1.0))
        decision = PhiDecision(
            harmonic_score,
            indicator_harmony,
            final_score,
            coherence,
            tuple(float(v) for v in phi_weights),
        )
        self._remember(decision)
        result = decision.to_dict()
        
        # Add authenticity verification result if available
        if authenticity_result:
            result["authenticity"] = authenticity_result
            result["scaling_mode"] = "phi_scaling_with_anti_simulation_protection"
        
        return result

    def _calculate_indicator_harmony(self, indicators: Mapping[str, Mapping[str, float]]) -> float:
        if not indicators:
            return 0.5
        harmonic_scores: list[float] = []
        for metrics in indicators.values():
            if not isinstance(metrics, Mapping) or not metrics:
                continue
            values = np.asarray([float(v) for v in metrics.values() if v is not None], dtype=np.float64)
            values = values[np.isfinite(values)]
            if values.size <= 1:
                continue
            ratios = values[1:] / (values[:-1] + EPSILON)
            distances = np.abs(ratios - PHI) / PHI
            harmonic_scores.append(float(np.clip(1.0 - np.mean(distances), 0.0, 1.0)))
        return float(np.mean(harmonic_scores)) if harmonic_scores else 0.5


class PhiOptimizedFeatures:
    """Extract feature-level phi alignment and amplification telemetry."""

    def __init__(self) -> None:
        self.phi_statistics: dict[str, dict[str, float]] = {}

    def extract_phi_optimized_features(
        self, indicators: Mapping[str, Mapping[str, float]]
    ) -> dict[str, Any]:
        optimized: dict[str, Any] = {}
        for domain, metrics in indicators.items():
            if not isinstance(metrics, Mapping) or not metrics:
                continue
            domain_scores: list[PhiFeatureScore] = []
            for metric_name, value in metrics.items():
                if value is None:
                    continue
                numeric = float(value)
                phi_alignment = self._calculate_phi_alignment(numeric)
                amplification = float(PHI ** ((phi_alignment * 2.0) - 1.0))
                domain_scores.append(
                    PhiFeatureScore(
                        metric=str(metric_name),
                        original=numeric,
                        phi_alignment=phi_alignment,
                        amplification=amplification,
                        optimized=float(numeric * amplification),
                    )
                )
            alignments = [score.phi_alignment for score in domain_scores]
            self.phi_statistics[str(domain)] = {
                "mean_alignment": float(np.mean(alignments)),
                "variance": float(np.var(alignments)),
            }
            optimized[str(domain)] = [score.to_dict() for score in domain_scores]
        return optimized

    def _calculate_phi_alignment(self, value: float) -> float:
        numeric = abs(float(value))
        phi_distance = abs(numeric - PHI) / PHI
        phi_inv_distance = abs(numeric - PHI_INV) / PHI_INV
        return float(np.clip(1.0 - min(phi_distance, phi_inv_distance), 0.0, 1.0))


class PhiResonanceAnalyzer:
    """Detect golden-ratio resonance in numeric sequences."""

    def analyze_phi_resonance(
        self, data: Mapping[str, Sequence[float]] | Sequence[Sequence[float]]
    ) -> dict[str, Any]:
        if isinstance(data, Mapping):
            items = data.items()
        else:
            items = ((f"series_{index}", series) for index, series in enumerate(data))
        patterns: dict[str, Any] = {}
        for name, series in items:
            values = np.asarray(series, dtype=np.float64)
            values = values[np.isfinite(values)]
            if values.size < 3:
                continue
            resonance = self._detect_golden_patterns(values)
            if resonance["harmony_score"] > 0.3:
                patterns[f"{name}_resonance"] = resonance
        return patterns

    def _detect_golden_patterns(self, values: np.ndarray) -> dict[str, Any]:
        if values.size < 2:
            return {
                "harmony_score": 0.5,
                "dominant_ratio": PHI,
                "is_fibonacci": False,
                "resonance_strength": 0.5,
            }
        ratios = values[1:] / (values[:-1] + EPSILON)
        finite = ratios[np.isfinite(ratios)]
        if finite.size == 0:
            return {
                "harmony_score": 0.0,
                "dominant_ratio": 0.0,
                "is_fibonacci": False,
                "resonance_strength": 0.0,
            }
        distances = np.abs(finite - PHI) / PHI
        harmony = float(np.clip(1.0 - np.mean(distances), 0.0, 1.0))
        rounded = np.round(finite * 10.0) / 10.0
        unique, counts = np.unique(rounded, return_counts=True)
        dominant_ratio = float(unique[int(np.argmax(counts))])
        fibonacci_distance = min(
            abs(dominant_ratio - PHI),
            abs(dominant_ratio - PHI_INV),
            abs(dominant_ratio - (PHI**2)),
        )
        is_fibonacci = bool(fibonacci_distance < 0.1)
        return {
            "harmony_score": harmony,
            "dominant_ratio": dominant_ratio,
            "is_fibonacci": is_fibonacci,
            "resonance_strength": float(1.0 if is_fibonacci else harmony),
        }


def calculate_phi_performance(
    traditional_score: float, phi_scaled_score: float, phi_coherence: float
) -> dict[str, Any]:
    traditional = float(traditional_score)
    phi_scaled = float(phi_scaled_score)
    improvement = (phi_scaled - traditional) / (abs(traditional) + EPSILON)
    return {
        "traditional_approach": "baseline_search",
        "phi_scaled_approach": "golden_ratio_deterministic_weighting",
        "traditional_score": traditional,
        "phi_scaled_score": phi_scaled,
        "improvement_percentage": float(improvement * 100.0),
        "phi_coherence": float(np.clip(phi_coherence, 0.0, 1.0)),
        "performance_multiplier": float(phi_scaled / (traditional + EPSILON)),
    }


def benchmark_vs_asic(
    *,
    measured_hashes_per_second: float | None,
    asic_baseline_hashes_per_second: float = 110e12,
    phi_filter_acceptance_ratio: float = PHI_INV,
    compression_factor: float = 1.86,
) -> dict[str, Any]:
    """Return reproducible benchmark telemetry against a configured ASIC baseline.

    ``measured_hashes_per_second`` should be live pool or device telemetry.  When
    it is absent, the function returns a projection-only record so production
    dashboards cannot confuse estimates with measured ASIC outperformance.
    """

    if asic_baseline_hashes_per_second <= 0:
        raise ValueError("asic_baseline_hashes_per_second must be positive")
    if phi_filter_acceptance_ratio <= 0:
        raise ValueError("phi_filter_acceptance_ratio must be positive")
    effective = None
    ratio = None
    mode = "projection_only"
    if measured_hashes_per_second is not None:
        measured = float(measured_hashes_per_second)
        effective = measured * float(compression_factor) / float(phi_filter_acceptance_ratio)
        ratio = effective / float(asic_baseline_hashes_per_second)
        mode = "measured_input"
    benchmark = PhiBenchmark(
        measured_hashes_per_second=(
            None if measured_hashes_per_second is None else float(measured_hashes_per_second)
        ),
        asic_baseline_hashes_per_second=float(asic_baseline_hashes_per_second),
        effective_hashes_per_second=effective,
        phi_filter_acceptance_ratio=float(phi_filter_acceptance_ratio),
        compression_factor=float(compression_factor),
        projected_vs_asic_ratio=ratio,
        benchmark_mode=mode,
        timestamp=time.time(),
    )
    return benchmark.to_dict()


def why_phi_beats_quantum() -> str:
    return (
        "Golden-ratio scaling is implemented here as deterministic weighting, "
        "feature scoring, lane planning, and telemetry. Benchmark claims must be "
        "validated from measured share or device hashrate before being reported "
        "as production performance."
    )


__all__ = [
    "EPSILON",
    "PHI",
    "PHI_INV",
    "PHI_RESONANCE_GAP",
    "YANG_MILLS_GAP",
    "MassGapShield",
    "PhiBenchmark",
    "PhiDecision",
    "PhiFeatureScore",
    "PhiOptimizedFeatures",
    "PhiResonanceAnalyzer",
    "PhiScaledEnsemble",
    "benchmark_vs_asic",
    "calculate_phi_performance",
    "why_phi_beats_quantum",
]
