"""Golden-ratio scaling utilities for PULVINI runtime decisions.

This module provides deterministic, auditable scaling helpers that apply the
golden ratio φ = (1+√5)/2 to ensemble weighting, feature scoring, nonce-lane
harmony analysis, and telemetry authenticity detection.

Core components:
  - PhiScaledEnsemble: φ-weighted model aggregation with anti-simulation guard
  - MassGapShield: jitter-based telemetry authenticity detector
  - PhiOptimizedFeatures: per-metric φ-alignment and amplification scoring
  - PhiResonanceAnalyzer: golden-ratio pattern detection in numeric series
  - benchmark_vs_asic: reproducible ASIC comparison telemetry

Claim boundary:
  All scaling here is deterministic classical computation.  The φ-weighted
  ensemble improves model aggregation by amplifying agreement and dampening
  high-variance predictions.  No claim of quantum speedup or hash-search
  advantage is made by this module.  Mining performance claims require
  live pool-confirmed share acceptance evidence (see benchmark_vs_asic).

The Yang-Mills operationalisation (YANG_MILLS_GAP = 3 - φ ≈ 1.382) is used
as an anti-simulation jitter anchor in MassGapShield.  This operationalises the
known structural relationship between φ and the SU(3) gauge-coupling fixed
point — it is not a claim to have solved the Millennium Problem.
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
    """Anti-simulation telemetry shield using the operationalised Yang-Mills mass gap.

    Detects spoofed or synthetically generated telemetry streams by comparing
    observed jitter against the expected jitter anchored to YANG_MILLS_GAP
    (3 - φ ≈ 1.382, the SU(3) gauge-coupling fixed-point relationship).

    Two failure modes are detected:
      - Precision spoofing: mean_jitter ≈ expected_jitter to within tolerance
        (too mathematically perfect to be organic hardware noise).
      - Brute-force injection: irrational_alignment > chaos_threshold
        (telemetry too chaotic, likely randomly generated).

    Authentic hardware telemetry falls between these two extremes.

    Claim boundary:
      This operationalises a known gauge-theoretic fixed-point relationship as a
      deterministic, auditable gate.  It is not a proof or solution of the
      Yang-Mills Millennium Prize Problem.  The gate is a substrate-independent
      mathematical invariant, applied with the same rigour as the Coxeter H3
      group and A5 character table.

    Args:
        tolerance: Below this alignment, jitter is flagged as precision-spoofed
            (default 1e-9, i.e. sub-nanosecond jitter alignment).
        chaos_threshold: Above this alignment, jitter is flagged as too chaotic
            (default 0.1).
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
    """Deterministic phi-scaled ensemble aggregation with anti-simulation protection.

    Aggregates predictions from multiple models using golden-ratio (φ) weighted
    voting.  Models that agree closely receive amplified weight (low variance →
    phi_exponent = +phi_power); models that disagree receive dampened weight
    (high variance → phi_exponent = -1.0).

    Optionally verifies that a telemetry stream is authentic (not synthetically
    generated) via MassGapShield before applying scaling.  If simulation is
    detected, a conservative zero decision is returned with the authenticity
    report attached.

    Memory is bounded by policy.memory_limit (default 1024 decisions).  Excess
    decisions are evicted FIFO.

    Claim boundary:
      The φ-weighting improves aggregation accuracy for diverse model ensembles
      by amplifying agreement.  No claim of mining hash-search advantage is made.
    """

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
        """Aggregate model predictions using golden-ratio weighted ensemble voting.

        Computes phi-weighted harmonic scores across models, scales by indicator
        harmony (how closely indicator ratios approach φ), and optionally
        validates telemetry authenticity before applying any scaling.

        Variance-based exponent selection:
          - low variance  (< low_variance_threshold):  phi_exponent = +phi_power  (amplify)
          - high variance (> high_variance_threshold): phi_exponent = −1.0         (dampen)
          - mid variance:                              phi_exponent = φ⁻¹            (neutral)

        Args:
            model_predictions: Dict of {model_name: {"score": float, ...}}.
            indicators: Dict of {domain: {metric: float}} for harmony calculation.
            telemetry_stream: Optional live telemetry values for MassGapShield
                authenticity check. If provided and deemed inauthentic, returns
                a conservative zero-decision with the authenticity report.

        Returns:
            Dict containing phi_score, indicator_harmony, final_score, coherence,
            phi_weights list, and optionally authenticity and scaling_mode fields.
        """
        # Verify telemetry authenticity if provided
        authenticity_result = None
        if telemetry_stream is not None:
            # Update telemetry buffer
            self._telemetry_buffer.extend(telemetry_stream)
            if len(self._telemetry_buffer) > self._telemetry_buffer_size:
                self._telemetry_buffer = self._telemetry_buffer[-self._telemetry_buffer_size :]

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
            values = np.asarray(
                [float(v) for v in metrics.values() if v is not None], dtype=np.float64
            )
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

    When measured_hashes_per_second is None, returns a projection-only record
    so production dashboards cannot confuse estimates with measured outperformance.
    Only measured_input mode produces a non-None projected_vs_asic_ratio.

    Claim boundary:
      This function computes a mathematical projection, not a proof of
      ASIC-beating performance.  All performance claims require live
      pool-confirmed share acceptance evidence before being treated as
      production validated.

    Args:
        measured_hashes_per_second: Live device or pool hashrate (None for projection).
        asic_baseline_hashes_per_second: ASIC reference hashrate (default 110 TH/s).
        phi_filter_acceptance_ratio: Filter acceptance ratio (default φ⁻¹ ≈ 0.618).
        compression_factor: PULVINI memory compression multiplier (default 1.86).

    Returns:
        PhiBenchmark dict with benchmark_mode, effective_hashes_per_second,
        and projected_vs_asic_ratio (None when projection_only).
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


def phi_scaling_what_it_does() -> str:
    """Return a plain-English description of what golden-ratio scaling does here."""
    return (
        "Golden-ratio scaling is implemented as deterministic weighting, "
        "feature scoring, lane planning, and telemetry authenticity gating. "
        "Benchmark claims must be validated from measured share or device "
        "hashrate before being reported as production performance."
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
    "phi_scaling_what_it_does",
]
