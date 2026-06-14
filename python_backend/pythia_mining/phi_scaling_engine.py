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
    """Deterministic phi-scaled ensemble decision helper."""

    def __init__(self, config: Mapping[str, Any] | None = None):
        self.config = dict(config or {})
        self.policy = PhiScalingPolicy(
            phi_scaling_power=float(
                self.config.get(
                    "phi_scaling_power", PhiScalingPolicy().phi_scaling_power
                )
            ),
            low_variance_threshold=float(
                self.config.get(
                    "low_variance_threshold", PhiScalingPolicy().low_variance_threshold
                )
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
    ) -> dict[str, Any]:
        if not model_predictions:
            decision = PhiDecision(
                0.0, self._calculate_indicator_harmony(indicators), 0.0, 0.0, tuple()
            )
            self._remember(decision)
            return decision.to_dict()

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
        final_score = float(
            np.clip(harmonic_score * (PHI ** (indicator_harmony - 1.0)), 0.0, 1.0)
        )
        coherence = float(np.clip(1.0 - (model_variance / (PHI * 0.5)), 0.0, 1.0))
        decision = PhiDecision(
            harmonic_score,
            indicator_harmony,
            final_score,
            coherence,
            tuple(float(v) for v in phi_weights),
        )
        self._remember(decision)
        return decision.to_dict()

    def _calculate_indicator_harmony(
        self, indicators: Mapping[str, Mapping[str, float]]
    ) -> float:
        if not indicators:
            return 0.5
        harmonic_scores: list[float] = []
        for metrics in indicators.values():
            if not isinstance(metrics, Mapping) or not metrics:
                continue
            values = np.asarray([float(v) for v in metrics.values()], dtype=np.float64)
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
        effective = (
            measured * float(compression_factor) / float(phi_filter_acceptance_ratio)
        )
        ratio = effective / float(asic_baseline_hashes_per_second)
        mode = "measured_input"
    benchmark = PhiBenchmark(
        measured_hashes_per_second=(
            None
            if measured_hashes_per_second is None
            else float(measured_hashes_per_second)
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
