"""Property tests for golden-ratio ensemble scaling and feature alignment."""

from __future__ import annotations

import math

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from pythia_mining.phi_config import PhiScalingPolicy
from pythia_mining.phi_scaling_engine import (
    PHI,
    PhiOptimizedFeatures,
    PhiResonanceAnalyzer,
    PhiScaledEnsemble,
)

score_strategy = st.floats(min_value=-1.0, max_value=2.0, allow_nan=False, allow_infinity=False)
finite_strategy = st.floats(min_value=-1e9, max_value=1e9, allow_nan=False, allow_infinity=False)


@given(st.lists(score_strategy, min_size=1, max_size=12))
@settings(max_examples=100, deadline=None, database=None)
def test_phi_weights_normalize_and_final_scores_are_bounded(scores: list[float]) -> None:
    predictions = {f"model_{idx}": {"score": score} for idx, score in enumerate(scores)}
    result = PhiScaledEnsemble().predict_with_phi_scaling(predictions, {})

    assert sum(result["phi_weights"]) == pytest.approx(1.0, abs=1e-10)
    assert all(math.isfinite(weight) and weight >= 0.0 for weight in result["phi_weights"])
    assert 0.0 <= result["final_score"] <= 1.0
    assert 0.0 <= result["coherence"] <= 1.0


def test_low_variance_cases_use_configured_phi_exponent() -> None:
    configured_power = 2.0
    engine = PhiScaledEnsemble(
        {
            "phi_scaling_power": configured_power,
            "low_variance_threshold": 0.5,
            "high_variance_threshold": 0.75,
        }
    )
    result = engine.predict_with_phi_scaling(
        {"alpha": {"score": 0.50}, "beta": {"score": 0.52}, "gamma": {"score": 0.54}},
        {},
    )

    scores = [0.50, 0.52, 0.54]
    mean_score = sum(scores) / len(scores)
    raw = [PHI ** (configured_power * (1.0 - abs(score - mean_score))) for score in scores]
    expected = [value / sum(raw) for value in raw]

    assert result["phi_weights"] == pytest.approx(expected, abs=1e-12)
    assert PhiScalingPolicy().low_variance_threshold < 0.5


def test_phi_resonance_detection_identifies_golden_ratio_sequence() -> None:
    sequence = [1.0]
    for _ in range(8):
        sequence.append(sequence[-1] * PHI)

    resonance = PhiResonanceAnalyzer().analyze_phi_resonance({"golden": sequence})

    assert "golden_resonance" in resonance
    assert resonance["golden_resonance"]["is_fibonacci"] is True
    assert resonance["golden_resonance"]["harmony_score"] > 0.99


@given(st.dictionaries(st.text(min_size=1, max_size=8), finite_strategy, min_size=1, max_size=8))
@settings(max_examples=100, deadline=None, database=None)
def test_phi_optimized_feature_alignments_stay_bounded(metrics: dict[str, float]) -> None:
    result = PhiOptimizedFeatures().extract_phi_optimized_features({"domain": metrics})

    for feature in result["domain"]:
        assert 0.0 <= feature["phi_alignment"] <= 1.0
        assert math.isfinite(feature["amplification"])
        assert math.isfinite(feature["optimized"])
