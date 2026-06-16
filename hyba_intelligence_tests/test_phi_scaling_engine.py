<<<<<<< Updated upstream
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
unit_strategy = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
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
=======
"""Tests for phi‐scaling engines and golden ratio utilities.

This module verifies invariants across the golden‐ratio scaling logic.  It
covers weight normalisation in the `PhiScaledEnsemble`, feature alignment in
`PhiOptimizedFeatures`, and pattern detection in `PhiResonanceAnalyzer`.  We
employ both deterministic and property-based tests to exercise a broad
distribution of input values and confirm that the golden ratio is respected
throughout the decision pipeline.
"""

from __future__ import annotations

import numpy as np
import pytest
from hypothesis import given, strategies as st

from python_backend.pythia_mining.phi_scaling_engine import (
    PHI,
    PHI_INV,
    PhiScaledEnsemble,
    PhiOptimizedFeatures,
    PhiResonanceAnalyzer,
)


@given(st.lists(st.floats(min_value=0.0, max_value=1.0), min_size=2, max_size=10))
def test_phi_weights_sum_to_one_and_score_bounds(scores: list[float]) -> None:
    """Property test: phi weights always normalise and final_score remains [0,1].

    For a random list of model scores in [0,1], we create a dictionary of
    predictions and compute the phi‐scaled decision.  The resulting weight
    vector must sum to one (within floating tolerance) and the final score
    should remain within the unit interval.  Indicators are given dummy
    values to avoid division by zero; the phi logic should still apply.
    """
    model_predictions = {f"model_{i}": {"score": float(s)} for i, s in enumerate(scores)}
    indicators = {"domain": {"metric_a": 0.5, "metric_b": 0.7}}
    ensemble = PhiScaledEnsemble()
    result = ensemble.predict_with_phi_scaling(model_predictions, indicators)
    weights = result["phi_weights"]
    # Weights must sum to one
    assert pytest.approx(sum(weights), rel=1e-6) == 1.0
    # Each weight must be in [0,1]
    for w in weights:
        assert 0.0 <= w <= 1.0
    # Final score is clipped between 0 and 1
    assert 0.0 <= result["final_score"] <= 1.0


def test_phi_exponent_selection_low_variance() -> None:
    """Low variance input should use the configured phi_scaling_power exponent.

    When all model scores are identical, the ensemble should apply the
    configured ``phi_scaling_power`` exponent.  We compute the expected
    phi‐weighted vector manually and compare with the returned weights.
    """
    scores = [0.5, 0.5, 0.5]
    config = {
        "phi_scaling_power": 2.0,
        "low_variance_threshold": 0.01,
        "high_variance_threshold": 0.5,
    }
    ensemble = PhiScaledEnsemble(config)
    preds = {f"m{i}": {"score": s} for i, s in enumerate(scores)}
    result = ensemble.predict_with_phi_scaling(preds, {})
    # Manually compute phi weights
    mean_score = np.mean(scores)
    expected_weights = np.array([
        PHI ** (config["phi_scaling_power"] * (1.0 - abs(s - mean_score))) for s in scores
    ])
    expected_weights = expected_weights / expected_weights.sum()
    assert np.allclose(result["phi_weights"], expected_weights, rtol=1e-6, atol=1e-6)


def test_phi_resonance_analyzer_detects_golden_pattern() -> None:
    """A geometric series approximating phi should register high harmony and Fibonacci flag.

    We feed a series that increases by the golden ratio.  The resonance
    analyzer should identify this as a strong resonance pattern and report
    `is_fibonacci` True with harmony above 0.8.  This test uses a small
    sequence to avoid degeneracy in the distance calculations.
    """
    analyzer = PhiResonanceAnalyzer()
    series = [1.0, PHI, PHI * PHI, PHI * PHI * PHI]
    patterns = analyzer.analyze_phi_resonance({"phi_series": series})
    resonance = patterns.get("phi_series_resonance")
    assert resonance is not None, "Golden ratio series should produce a resonance pattern"
    assert resonance["harmony_score"] > 0.8
    assert resonance["is_fibonacci"] is True


def test_phi_optimized_feature_alignment_range() -> None:
    """Ensure phi alignment values fall within [0,1] and amplify correctly.

    The PhiOptimizedFeatures module calculates phi alignment for numeric
    indicators.  Each resulting phi_alignment must be between 0 and 1, and
    the optimized value should be non-negative.  We provide metrics near PHI
    and PHI_INV to ensure both branches of the alignment function are exercised.
    """
    features = PhiOptimizedFeatures()
    indicators = {
        "domain": {
            "metric_phi": PHI,
            "metric_phi_inv": PHI_INV,
            "metric_random": 0.3333,
        }
    }
    optimized = features.extract_phi_optimized_features(indicators)
    domain_results = optimized.get("domain", [])
    assert domain_results, "Expected optimized feature results for the domain"
    for item in domain_results:
        assert 0.0 <= item["phi_alignment"] <= 1.0
        assert item["optimized"] >= 0.0
>>>>>>> Stashed changes
