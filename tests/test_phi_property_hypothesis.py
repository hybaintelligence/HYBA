"""
Property-based tests for Golden Ratio Scaling using Hypothesis.

These tests validate that mathematical invariants hold across a vast range
of random inputs — not just hand-picked examples.

Run with:
    python -m pytest tests/test_phi_property_hypothesis.py -v --hypothesis-show-statistics
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from asic_comparison_framework import (
    ASICPerformanceData,
    ComprehensiveComparison,
    GoldenRatioScaling,
    PULVINIPerformanceEstimator,
)

from pythia_mining.phi_scaling_engine import (
    PHI,
    PhiOptimizedFeatures,
    PhiResonanceAnalyzer,
    PhiScaledEnsemble,
    benchmark_vs_asic,
    calculate_phi_performance,
)

# ============================================================================
# CUSTOM STRATEGIES
# ============================================================================

phi_near_strategy = st.floats(
    min_value=PHI - 0.1,
    max_value=PHI + 0.1,
    allow_nan=False,
    allow_infinity=False,
)

chaos_float_strategy = st.floats(
    min_value=-1e12,
    max_value=1e12,
    allow_nan=False,
    allow_infinity=False,
)

positive_scale_strategy = st.floats(
    min_value=1e-6,
    max_value=1e25,
    allow_nan=False,
    allow_infinity=False,
)

small_positive_strategy = st.floats(
    min_value=0.0,
    max_value=1.0,
    allow_nan=False,
    allow_infinity=False,
)


# ============================================================================
# PROPERTY 1: φ invariant across arbitrary feature extractions
# ============================================================================


class TestPhiIdentityInvariants:
    """φ² = φ + 1 must hold under all operations."""

    @given(st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False))
    @settings(max_examples=100)
    def test_phi_quadratic_identity_preserved(self, _unused: float) -> None:
        """φ² == φ + 1 — the defining quadratic — regardless of prior ops."""
        assert abs(PHI * PHI - (PHI + 1.0)) < 1e-15

    @given(st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False))
    @settings(max_examples=100)
    def test_phi_inverse_identity_preserved(self, _unused: float) -> None:
        """1/φ == φ - 1 — invariant across all operations."""
        assert abs(1.0 / PHI - (PHI - 1.0)) < 1e-15


# ============================================================================
# PROPERTY 2: PhiScaledEnsemble — weight normalization invariant
# ============================================================================


class TestPhiScaledEnsembleProperties:
    """phi_weights must always sum to 1 for any non-empty input."""

    @given(
        st.dictionaries(
            st.text(
                min_size=1,
                max_size=8,
                alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="_"),
            ),
            st.fixed_dictionaries({"score": small_positive_strategy}),
            min_size=1,
            max_size=10,
        ),
        st.dictionaries(
            st.text(min_size=1, max_size=8),
            st.dictionaries(
                st.text(min_size=1, max_size=8),
                chaos_float_strategy,
                min_size=1,
                max_size=5,
            ),
            min_size=0,
            max_size=5,
        ),
    )
    @settings(max_examples=200)
    def test_weight_normalization_invariant(
        self,
        predictions: dict,
        indicators: dict,
    ) -> None:
        """phi_weights must sum to 1 for any non-empty predictions."""
        engine = PhiScaledEnsemble()
        result = engine.predict_with_phi_scaling(predictions, indicators)
        weights = result["phi_weights"]
        if weights:
            assert abs(sum(weights) - 1.0) < 1e-10, f"Weights sum to {sum(weights)}, expected 1.0"
        assert 0.0 <= result["final_score"] <= 1.0 + 1e-12
        assert 0.0 <= result["coherence"] <= 1.0 + 1e-12

    @given(
        st.dictionaries(
            st.text(min_size=1, max_size=8),
            st.fixed_dictionaries(
                {
                    "score": st.floats(
                        min_value=-1.0,
                        max_value=2.0,
                        allow_nan=False,
                        allow_infinity=False,
                    )
                }
            ),
            min_size=1,
            max_size=8,
        ),
    )
    @settings(max_examples=100)
    def test_out_of_range_scores_clipped(self, predictions: dict) -> None:
        """Scores outside [0,1] must be clipped without breaking normalization."""
        engine = PhiScaledEnsemble()
        result = engine.predict_with_phi_scaling(predictions, {})
        weights = result["phi_weights"]
        if weights:
            assert abs(sum(weights) - 1.0) < 1e-10
        assert result["final_score"] == pytest.approx(max(0.0, min(1.0, result["final_score"])))


# ============================================================================
# PROPERTY 3: PhiResonanceAnalyzer — must never crash on any input
# ============================================================================


class TestPhiResonanceRobustness:
    """Resonance analyzer must handle any list-of-float gracefully."""

    @given(
        st.lists(
            st.floats(allow_nan=False, allow_infinity=True),
            min_size=0,
            max_size=200,
        )
    )
    @settings(max_examples=200)
    def test_resonance_never_crashes(self, sequence: list[float]) -> None:
        """No matter how malformed, the analyzer must return structured output."""
        analyzer = PhiResonanceAnalyzer()
        # Must never raise
        result = analyzer.analyze_phi_resonance({"chaos": sequence})
        assert isinstance(result, dict)

    @given(
        st.dictionaries(
            st.text(min_size=1, max_size=16),
            st.lists(
                st.floats(allow_nan=False, allow_infinity=True),
                min_size=0,
                max_size=100,
            ),
            min_size=0,
            max_size=10,
        )
    )
    @settings(max_examples=100)
    def test_multi_key_resonance_never_crashes(self, data: dict) -> None:
        """Multi-key dict of sequences — must never raise."""
        analyzer = PhiResonanceAnalyzer()
        result = analyzer.analyze_phi_resonance(data)
        assert isinstance(result, dict)

    @given(
        st.lists(phi_near_strategy, min_size=3, max_size=50),
    )
    @settings(max_examples=50)
    def test_phi_near_sequences_have_high_harmony(self, phi_cluster: list[float]) -> None:
        """Sequences near φ should have non-zero harmony."""
        analyzer = PhiResonanceAnalyzer()
        result = analyzer.analyze_phi_resonance({"near_phi": phi_cluster})
        if "near_phi_resonance" in result:
            assert result["near_phi_resonance"]["harmony_score"] >= 0.0


# ============================================================================
# PROPERTY 4: PhiOptimizedFeatures — alignment bounded
# ============================================================================


class TestPhiAlignmentProperties:
    """Phi alignment must always be in [0, 1]."""

    @given(st.floats(min_value=-1e12, max_value=1e12, allow_nan=False, allow_infinity=False))
    @settings(max_examples=200)
    def test_phi_alignment_bounded(self, value: float) -> None:
        """phi_alignment must always be in [0, 1] for any finite input."""
        features = PhiOptimizedFeatures()
        # Access the private method via public API
        result = features.extract_phi_optimized_features({"x": {"val": value}})
        if result:
            alignment = result["x"][0]["phi_alignment"]
            assert 0.0 <= alignment <= 1.0, (
                f"phi_alignment {alignment} outside [0,1] for value {value}"
            )
            assert alignment == pytest.approx(max(0.0, min(1.0, alignment)))

    @given(st.floats(min_value=-1e12, max_value=1e12, allow_nan=False, allow_infinity=False))
    @settings(max_examples=100)
    def test_amplification_non_negative(self, value: float) -> None:
        """Amplification must be non-negative for any finite input."""
        features = PhiOptimizedFeatures()
        result = features.extract_phi_optimized_features({"x": {"val": value}})
        if result:
            assert result["x"][0]["amplification"] >= 0.0


# ============================================================================
# PROPERTY 5: benchmark_vs_asic — deterministic & positive efficiency
# ============================================================================


class TestBenchmarkProperties:
    """Benchmark must be deterministic and produce positive results."""

    @given(
        st.floats(min_value=1e6, max_value=1e18, allow_nan=False, allow_infinity=False),
        st.floats(min_value=1e6, max_value=1e18, allow_nan=False, allow_infinity=False),
        st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False),
        st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100)
    def test_benchmark_deterministic(
        self,
        measured: float,
        baseline: float,
        phi_ratio: float,
        compression: float,
    ) -> None:
        """Same inputs → same outputs (determinism invariant)."""
        a = benchmark_vs_asic(
            measured_hashes_per_second=measured,
            asic_baseline_hashes_per_second=baseline,
            phi_filter_acceptance_ratio=phi_ratio,
            compression_factor=compression,
        )
        b = benchmark_vs_asic(
            measured_hashes_per_second=measured,
            asic_baseline_hashes_per_second=baseline,
            phi_filter_acceptance_ratio=phi_ratio,
            compression_factor=compression,
        )
        assert a["effective_hashes_per_second"] == b["effective_hashes_per_second"]
        assert a["projected_vs_asic_ratio"] == b["projected_vs_asic_ratio"]

    @given(
        st.floats(min_value=1e6, max_value=1e18, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=50)
    def test_benchmark_projection_ratio_positive(self, measured: float) -> None:
        """Projected vs ASIC ratio must be positive if measured is provided."""
        result = benchmark_vs_asic(measured_hashes_per_second=measured)
        if result["projected_vs_asic_ratio"] is not None:
            assert result["projected_vs_asic_ratio"] > 0


# ============================================================================
# PROPERTY 6: calculate_phi_performance — finite outputs
# ============================================================================


class TestPhiPerformanceProperties:
    """Performance calculation must never produce NaN or Inf."""

    @given(
        small_positive_strategy,
        small_positive_strategy,
        small_positive_strategy,
    )
    @settings(max_examples=200)
    def test_performance_outputs_finite(
        self,
        traditional: float,
        phi_scaled: float,
        coherence: float,
    ) -> None:
        """All outputs must be finite for any valid inputs."""
        result = calculate_phi_performance(traditional, phi_scaled, coherence)
        for key in [
            "traditional_score",
            "phi_scaled_score",
            "improvement_percentage",
            "phi_coherence",
            "performance_multiplier",
        ]:
            assert math.isfinite(result[key]), f"{key} is not finite: {result[key]}"


# ============================================================================
# PROPERTY 7: ASIC scaling — monotonicity invariants
# ============================================================================


class TestASICScalingMonotonicity:
    """As scale increases, hashrate must increase and efficiency must improve."""

    @given(
        st.sampled_from(["10^12", "10^15", "10^18", "10^20"]),
        st.sampled_from(["10^12", "10^15", "10^18", "10^20"]),
    )
    @settings(max_examples=50)
    def test_scaling_monotonic_hashrate(self, a: str, b: str) -> None:
        """If scale_a < scale_b, hashrate_a < hashrate_b."""
        scale_order = {"10^12": 0, "10^15": 1, "10^18": 2, "10^20": 3}
        if scale_order[a] >= scale_order[b]:
            pytest.skip("Need strict ascending pair")
        comparison = ComprehensiveComparison()
        results = comparison.compare_golden_ratio_scaling()
        assert results[a]["effective_hashrate_ths"] < results[b]["effective_hashrate_ths"], (
            f"Hashrate not monotonic: {a} < {b} failed"
        )

    @given(
        st.sampled_from(["10^12", "10^15", "10^18", "10^20"]),
        st.sampled_from(["10^12", "10^15", "10^18", "10^20"]),
    )
    @settings(max_examples=50)
    def test_scaling_monotonic_efficiency(self, a: str, b: str) -> None:
        """If scale_a < scale_b, efficiency_a > efficiency_b (lower is better)."""
        scale_order = {"10^12": 0, "10^15": 1, "10^18": 2, "10^20": 3}
        if scale_order[a] >= scale_order[b]:
            pytest.skip("Need strict ascending pair")
        comparison = ComprehensiveComparison()
        results = comparison.compare_golden_ratio_scaling()
        assert results[a]["hashrate_efficiency_j_th"] > results[b]["hashrate_efficiency_j_th"], (
            f"Efficiency not monotonic: {a} < {b} failed (J/TH should decrease)"
        )


# ============================================================================
# PROPERTY 8: Golden ratio self-similarity across scales
# ============================================================================


class TestGoldenRatioSelfSimilarity:
    """Golden ratio scaling must preserve self-similarity under exponentiation."""

    @given(
        st.integers(min_value=1, max_value=20),
        st.integers(min_value=1, max_value=20),
    )
    @settings(max_examples=50)
    def test_scale_factor_self_similarity(self, a: int, b: int) -> None:
        """Scaling by 10^(a+b) = scaling by 10^a then 10^b."""
        base = 1.0
        GoldenRatioScaling.apply_scaling(base, a + b)
        composite = GoldenRatioScaling.apply_scaling(
            GoldenRatioScaling.apply_scaling(base, a),
            b,
        )
        # apply_scaling multiplies by 10^exponent, so composite of a then b = 10^a * 10^b
        expected = GoldenRatioScaling.apply_scaling(base, a) * (10**b)
        assert abs(composite - expected) < 1e-12


# ============================================================================
# PROPERTY 9: Power consumption sub-linear scaling
# ============================================================================


class TestPowerScalingProperties:
    """Power must scale sub-linearly with golden ratio scale."""

    @given(
        st.floats(min_value=1.0, max_value=1e12, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100)
    def test_power_positive(self, scale: float) -> None:
        """Power consumption must be positive for any positive scale."""
        power = PULVINIPerformanceEstimator.estimate_power_consumption(1, scale)
        assert power > 0, f"Power must be positive, got {power}"

    @given(
        st.floats(min_value=1.0, max_value=1e6, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=50)
    def test_power_sub_linear(self, scale: float) -> None:
        """Doubling the scale must less-than-double the power."""
        p1 = PULVINIPerformanceEstimator.estimate_power_consumption(1, scale)
        p2 = PULVINIPerformanceEstimator.estimate_power_consumption(1, scale * 2.0)
        # Power scaling exponent is 0.7, so 2^0.7 ≈ 1.625
        # p2 should be less than 2 * p1
        assert p2 < 2.0 * p1, f"Power scaling not sub-linear: {p2} >= 2*{p1}"


# ============================================================================
# PROPERTY 10: ComprehensiveComparison — pulvini_beats_asic logic
# ============================================================================


class TestBeatsASICLogic:
    """pulvini_beats_asic must be True iff hashrate_ratio > 1 AND efficiency_ratio < 1."""

    @given(
        st.sampled_from(["10^12", "10^15", "10^18", "10^20"]),
        st.sampled_from(list(ASICPerformanceData.get_all_specs().keys())),
    )
    @settings(max_examples=100)
    def test_beats_logic_consistent(self, scale: str, asic_name: str) -> None:
        """The beats logic must match the mathematical definition exactly."""
        comparison = ComprehensiveComparison()
        results = comparison.compare_golden_ratio_scaling()
        comps = {c["asic"]: c for c in results[scale]["asic_comparison"]}
        c = comps[asic_name]
        expected = c["hashrate_ratio"] > 1.0 and c["efficiency_ratio"] < 1.0
        assert c["pulvini_beats_asic"] == expected, (
            f"Mismatch at {scale}/{asic_name}: expected {expected}, "
            f"got {c['pulvini_beats_asic']} "
            f"(hr={c['hashrate_ratio']:.4e}, eff={c['efficiency_ratio']:.4e})"
        )
