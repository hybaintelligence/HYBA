"""
Comprehensive Audit & Tests for Golden Ratio Scaling
=====================================================

The golden ratio (φ = 1.618033988749895) is implemented as a mathematical invariant
for deterministic scaling, traversal guidance, and ensemble weighting in the
HENDRIX-Φ solver system. This test suite verifies:
  1. φ satisfies its defining quadratic: φ² = φ + 1
  2. The scaling engine correctly applies φ-based deterministic weighting
  3. The ASIC comparison framework maintains proper projection boundaries
  4. Edge cases and property-based invariants hold
  5. Cross-validation of mathematical implementations against reference values

Note: φ provides structured guidance for traversal and scaling decisions;
SHA-256 verification and pool-side acceptance remain external proof oracles.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

try:
    from hypothesis import given, settings
    from hypothesis import strategies as st
except ImportError:  # pragma: no cover - dependency guard for minimal envs
    given = settings = st = None

import pytest

# ── Ensure we can import from python_backend ──────────────────────────────
ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
SCRIPTS = ROOT / "scripts"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from asic_comparison_framework import (
    ASICPerformanceData,
    ComprehensiveComparison,
    GoldenRatioScaling,
    PULVINIPerformanceEstimator,
)

# ── Imports from the codebase under test ──────────────────────────────────
from pythia_mining.phi_scaling_engine import (
    PHI,
    PHI_INV,
    PhiOptimizedFeatures,
    PhiResonanceAnalyzer,
    PhiScaledEnsemble,
    benchmark_vs_asic,
    calculate_phi_performance,
    why_phi_beats_quantum,
)

# ============================================================================
# SECTION 1 — Golden Ratio Mathematical Identity Verification
# ============================================================================


class TestPhiMathematicalIdentity:
    """Verify φ satisfies its fundamental mathematical properties."""

    def test_phi_quadratic_identity(self) -> None:
        """φ² == φ + 1  (the defining quadratic)"""
        assert abs(PHI * PHI - (PHI + 1.0)) < 1e-15, "φ² ≠ φ + 1"

    def test_phi_inverse_identity(self) -> None:
        """1/φ == φ - 1"""
        assert abs(1.0 / PHI - (PHI - 1.0)) < 1e-15, "1/φ ≠ φ - 1"

    def test_phi_continued_fraction(self) -> None:
        """φ = 1 + 1/(1 + 1/(1 + ...))  — first 20 terms converge"""
        cf = 1.0
        for _ in range(20):
            cf = 1.0 + 1.0 / cf
        assert abs(cf - PHI) < 1e-6, f"Continued fraction failed to converge: {cf} ≠ {PHI}"

    def test_phi_fibonacci_ratio_limit(self) -> None:
        """F_{n+1} / F_n → φ as n → ∞"""
        a, b = 1, 1
        for _ in range(20):
            a, b = b, a + b
        ratio = b / a
        assert abs(ratio - PHI) < 1e-4, f"Fibonacci ratio {ratio} not converging to φ"

    def test_phi_powers(self) -> None:
        """φ³ = φ² + φ  (extending the identity)"""
        phi3 = PHI**3
        phi2_plus_phi = (PHI**2) + PHI
        assert abs(phi3 - phi2_plus_phi) < 1e-14

    def test_phi_golden_angle(self) -> None:
        """2π / φ² ≈ 137.5° — the golden angle in nature"""
        golden_angle_deg = 360.0 / (PHI * PHI)
        assert abs(golden_angle_deg - 137.5) < 0.6, f"Golden angle {golden_angle_deg}° ≠ 137.5°"

    def test_phi_logarithmic_spiral(self) -> None:
        """A logarithmic spiral with growth factor φ⁴ has radius ratio φ² per quarter-turn."""
        quarter_turn_growth = PHI**2
        full_turn_growth = quarter_turn_growth**4
        assert abs(full_turn_growth - PHI**8) < 1e-12


# ============================================================================
# SECTION 2 — phi_scaling_engine Core Tests (Edge Cases + Properties)
# ============================================================================


class TestPhiScaledEnsemble:
    """Deterministic φ-scaled ensemble decision helper."""

    def test_empty_predictions_returns_zero_decision(self) -> None:
        engine = PhiScaledEnsemble()
        result = engine.predict_with_phi_scaling({}, {})
        assert result["method"] == "golden_ratio_scaling"
        assert result["phi_score"] == 0.0
        assert result["final_score"] == 0.0

    def test_single_model_returns_valid_weights(self) -> None:
        engine = PhiScaledEnsemble()
        result = engine.predict_with_phi_scaling({"alpha": {"score": 0.5}}, {})
        self._assert_valid_phi_decision(result)

    def test_identical_scores_use_phi_power_exponent(self) -> None:
        """When variance < 0.05, phi_exponent = phi_power (default 1.5)."""
        engine = PhiScaledEnsemble()
        result = engine.predict_with_phi_scaling(
            {
                "a": {"score": 0.7},
                "b": {"score": 0.71},
                "c": {"score": 0.69},
            },
            {},
        )
        self._assert_valid_phi_decision(result)
        # Low variance → weights should be nearly uniform
        assert max(result["phi_weights"]) - min(result["phi_weights"]) < 0.02

    def test_high_variance_spreads_weights(self) -> None:
        """When variance > 0.2, phi_exponent = -1.0."""
        engine = PhiScaledEnsemble()
        result = engine.predict_with_phi_scaling(
            {
                "good": {"score": 0.95},
                "bad": {"score": 0.15},
                "mid": {"score": 0.50},
            },
            {},
        )
        self._assert_valid_phi_decision(result)

    def test_indicator_harmony_phi_consecutive_sequence(self) -> None:
        """Consecutive ratios of φ, φ², φ³ are all φ — high harmony."""
        engine = PhiScaledEnsemble()
        result = engine.predict_with_phi_scaling(
            {"m": {"score": 0.5}},
            {"nature": {"a": 1.0, "b": PHI, "c": PHI**2, "d": PHI**3}},
        )
        self._assert_valid_phi_decision(result)
        # Ratios: φ, φ, φ → all exactly φ → harmony ≈ 1.0
        assert result["indicator_harmony"] > 0.99

    def test_indicator_harmony_non_phi_sequence(self) -> None:
        """φ, φ⁻¹, φ² are not consecutive φ ratios — harmony ≈ 0."""
        engine = PhiScaledEnsemble()
        result = engine.predict_with_phi_scaling(
            {"m": {"score": 0.5}}, {"nature": {"a": PHI, "b": PHI_INV, "c": PHI**2}}
        )
        self._assert_valid_phi_decision(result)
        # Ratios: φ⁻¹/φ ≈ 0.382, φ²/φ⁻¹ ≈ 4.236 → neither ≈ φ → harmony ≈ 0
        assert result["indicator_harmony"] < 0.05

    def test_indicator_harmony_poor_sequence(self) -> None:
        engine = PhiScaledEnsemble()
        result = engine.predict_with_phi_scaling(
            {"m": {"score": 0.5}}, {"chaos": {"x": 0.0, "y": 1000.0, "z": 0.001}}
        )
        self._assert_valid_phi_decision(result)
        assert result["indicator_harmony"] < 0.5

    def test_memory_grows_with_predictions(self) -> None:
        engine = PhiScaledEnsemble()
        for _ in range(5):
            engine.predict_with_phi_scaling({"m": {"score": 0.5}}, {})
        assert len(engine.memory) == 5

    def test_phi_power_configurable(self) -> None:
        engine = PhiScaledEnsemble({"phi_scaling_power": 2.0})
        result = engine.predict_with_phi_scaling({"a": {"score": 0.5}, "b": {"score": 0.5}}, {})
        self._assert_valid_phi_decision(result)

    def _assert_valid_phi_decision(self, d: dict) -> None:
        assert "phi_score" in d
        assert "indicator_harmony" in d
        assert "final_score" in d
        assert "coherence" in d
        assert "phi_weights" in d
        assert 0.0 <= d["final_score"] <= 1.0
        assert 0.0 <= d["coherence"] <= 1.0
        assert abs(sum(d["phi_weights"]) - 1.0) < 1e-10 or not d["phi_weights"]


class TestPhiOptimizedFeatures:
    """Extract feature-level φ alignment and amplification telemetry."""

    def test_empty_indicators_returns_empty(self) -> None:
        features = PhiOptimizedFeatures()
        result = features.extract_phi_optimized_features({})
        assert result == {}

    def test_perfect_phi_alignment(self) -> None:
        features = PhiOptimizedFeatures()
        result = features.extract_phi_optimized_features({"test": {"phi_val": PHI}})
        assert len(result["test"]) == 1
        assert result["test"][0]["phi_alignment"] > 0.999

    def test_poor_alignment(self) -> None:
        features = PhiOptimizedFeatures()
        result = features.extract_phi_optimized_features({"test": {"bad": 999.0}})
        assert result["test"][0]["phi_alignment"] < 0.5

    def test_amplification_exceeds_one_for_aligned(self) -> None:
        features = PhiOptimizedFeatures()
        result = features.extract_phi_optimized_features({"test": {"phi": PHI}})
        assert result["test"][0]["amplification"] >= 1.0

    def test_phi_statistics_tracked(self) -> None:
        features = PhiOptimizedFeatures()
        features.extract_phi_optimized_features({"lane": {"a": PHI, "b": PHI_INV}})
        assert "lane" in features.phi_statistics
        assert "mean_alignment" in features.phi_statistics["lane"]

    def test_phi_statistics_persist_across_calls(self) -> None:
        features = PhiOptimizedFeatures()
        features.extract_phi_optimized_features({"x": {"v": PHI}})
        features.extract_phi_optimized_features({"y": {"v": 1.0}})
        assert "x" in features.phi_statistics
        assert "y" in features.phi_statistics


class TestPhiResonanceAnalyzer:
    """Detect golden-ratio resonance in numeric sequences."""

    def test_fibonacci_sequence_detected(self) -> None:
        analyzer = PhiResonanceAnalyzer()
        result = analyzer.analyze_phi_resonance({"fib": [1, 2, 3, 5, 8, 13, 21, 34, 55]})
        assert "fib_resonance" in result
        assert result["fib_resonance"]["is_fibonacci"] is True
        assert result["fib_resonance"]["harmony_score"] > 0.8

    def test_arithmetic_sequence_low_resonance(self) -> None:
        """Arithmetic progression has consistent but non-φ ratios, no fibonacci."""
        analyzer = PhiResonanceAnalyzer()
        result = analyzer.analyze_phi_resonance({"random": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]})
        # Arithmetic series → ratios converge to 1.0, not φ, not fibonacci
        assert "random_resonance" in result
        assert result["random_resonance"]["is_fibonacci"] is False
        assert result["random_resonance"]["dominant_ratio"] < 2.0

    def test_phi_constructed_sequence(self) -> None:
        """Sequence where every step multiplies by φ."""
        analyzer = PhiResonanceAnalyzer()
        vals = [1.0]
        for _ in range(8):
            vals.append(vals[-1] * PHI)
        result = analyzer.analyze_phi_resonance({"phi_seq": vals})
        assert "phi_seq_resonance" in result
        assert result["phi_seq_resonance"]["harmony_score"] > 0.95

    def test_short_sequence_returns_no_resonance(self) -> None:
        analyzer = PhiResonanceAnalyzer()
        result = analyzer.analyze_phi_resonance({"short": [1.0, 2.0]})
        assert "short_resonance" not in result

    def test_list_of_sequences(self) -> None:
        analyzer = PhiResonanceAnalyzer()
        result = analyzer.analyze_phi_resonance([[1, 2, 3, 5, 8], [0.1, 0.2, 0.3]])
        assert "series_0_resonance" in result

    def test_inf_values_handled(self) -> None:
        analyzer = PhiResonanceAnalyzer()
        result = analyzer.analyze_phi_resonance(
            {"mixed": [1.0, float("inf"), 2.0, float("nan"), 3.0]}
        )
        assert not any(math.isnan(v.get("harmony_score", 0)) for v in result.values())


class TestBenchmarkVsASIC:
    """Reproducible benchmark telemetry against configured ASIC baseline."""

    def test_projection_mode_when_no_measured(self) -> None:
        result = benchmark_vs_asic(measured_hashes_per_second=None)
        assert result["benchmark_mode"] == "projection_only"
        assert result["measured_hashes_per_second"] is None
        assert result["projected_vs_asic_ratio"] is None

    def test_measured_mode_when_provided(self) -> None:
        result = benchmark_vs_asic(
            measured_hashes_per_second=110e12,
            asic_baseline_hashes_per_second=110e12,
        )
        assert result["benchmark_mode"] == "measured_input"
        assert result["measured_hashes_per_second"] == 110e12
        assert result["projected_vs_asic_ratio"] is not None

    def test_zero_baseline_raises(self) -> None:
        with pytest.raises(ValueError, match="asic_baseline_hashes_per_second must be positive"):
            benchmark_vs_asic(measured_hashes_per_second=1.0, asic_baseline_hashes_per_second=0)

    def test_zero_acceptance_raises(self) -> None:
        with pytest.raises(ValueError, match="phi_filter_acceptance_ratio must be positive"):
            benchmark_vs_asic(measured_hashes_per_second=1.0, phi_filter_acceptance_ratio=0)

    def test_default_parameters_match_expected(self) -> None:
        result = benchmark_vs_asic(measured_hashes_per_second=110e12)
        assert result["asic_baseline_hashes_per_second"] == 110e12
        assert result["phi_filter_acceptance_ratio"] == pytest.approx(PHI_INV, rel=1e-12)
        assert result["compression_factor"] == 1.86

    def test_non_default_parameters(self) -> None:
        result = benchmark_vs_asic(
            measured_hashes_per_second=1e15,
            asic_baseline_hashes_per_second=200e12,
            phi_filter_acceptance_ratio=0.5,
            compression_factor=3.0,
        )
        expected_effective = 1e15 * 3.0 / 0.5
        assert result["effective_hashes_per_second"] == pytest.approx(expected_effective, rel=1e-6)
        assert result["projected_vs_asic_ratio"] == pytest.approx(
            expected_effective / 200e12, rel=1e-6
        )


class TestCalculatePhiPerformance:
    """Performance multiplier calculation."""

    def test_positive_improvement(self) -> None:
        result = calculate_phi_performance(0.1, 0.9, 0.95)
        assert result["improvement_percentage"] > 0
        assert result["performance_multiplier"] > 1.0

    def test_no_change(self) -> None:
        result = calculate_phi_performance(0.5, 0.5, 1.0)
        assert abs(result["improvement_percentage"]) < 1e-10
        assert result["performance_multiplier"] == pytest.approx(1.0, rel=1e-10)

    def test_degradation(self) -> None:
        result = calculate_phi_performance(0.9, 0.1, 0.1)
        assert result["improvement_percentage"] < 0
        assert result["performance_multiplier"] < 1.0

    def test_zero_traditional(self) -> None:
        result = calculate_phi_performance(0.0, 1.0, 0.5)
        assert math.isfinite(result["improvement_percentage"])


class TestWhyPhiBeatsQuantum:
    """Documentation string."""

    def test_returns_non_empty_string(self) -> None:
        msg = why_phi_beats_quantum()
        assert isinstance(msg, str)
        assert len(msg) > 50


# ============================================================================
# SECTION 3 — ASIC Comparison Framework Tests
# ============================================================================


class TestASICPerformanceData:
    """Real-world ASIC specifications."""

    def test_all_asics_present(self) -> None:
        specs = ASICPerformanceData.get_all_specs()
        assert len(specs) == 6
        for name in ["Antminer S21", "Antminer S19 XP", "Whatsminer M60"]:
            assert name in specs

    def test_asic_spec_structure(self) -> None:
        specs = ASICPerformanceData.get_all_specs()
        for name, spec in specs.items():
            for key in ["hashrate_ths", "power_w", "efficiency_j_th", "manufacturer"]:
                assert key in spec, f"{name} missing {key}"

    def test_top_efficiency(self) -> None:
        top = ASICPerformanceData.get_by_efficiency(3)
        assert len(top) == 3
        # Should be sorted by efficiency ascending (best first)
        efficiencies = [spec["efficiency_j_th"] for _, spec in top]
        assert efficiencies == sorted(efficiencies)

    def test_top_hashrate(self) -> None:
        top = ASICPerformanceData.get_by_hashrate(3)
        assert len(top) == 3
        hashrates = [spec["hashrate_ths"] for _, spec in top]
        assert hashrates == sorted(hashrates, reverse=True)

    def test_best_asic_efficiency(self) -> None:
        """Whatsminer M60 should be best at 17.0 J/TH."""
        top = ASICPerformanceData.get_by_efficiency(1)
        assert top[0][0] == "Whatsminer M60"
        assert top[0][1]["efficiency_j_th"] == 17.0


class TestGoldenRatioScaling:
    """Golden ratio scaling constants and helpers."""

    def test_phi_matches_phi_scaling_engine(self) -> None:
        assert abs(GoldenRatioScaling.PHI - PHI) < 1e-12

    def test_scaling_factors_requested_levels(self) -> None:
        factors = GoldenRatioScaling.get_scaling_factors()
        assert set(factors) == {
            "10^7",
            "10^10",
            "10^12",
            "10^15",
            "10^18",
            "10^20",
            "10^31",
            "10^76",
        }
        assert factors["10^12"] == pytest.approx((10**12) * (PHI**12), rel=1e-12)
        assert factors["10^76"] == pytest.approx((10**76) * (PHI**76), rel=1e-12)

    def test_combination_scaling_factors(self) -> None:
        factors = GoldenRatioScaling.get_scaling_factors(include_combinations=True)
        assert factors["10^7×10^10"] == pytest.approx(factors["10^7"] * factors["10^10"], rel=1e-12)

    def test_apply_scaling(self) -> None:
        result = GoldenRatioScaling.apply_scaling(2.34, 12)
        assert result == pytest.approx(2.34 * (10**12) * (PHI**12), rel=1e-12)

    def test_governance_cap_default(self) -> None:
        assert GoldenRatioScaling.GOVERNANCE_CAP_EHS == 1.0


class TestPULVINIPerformanceEstimator:
    """Performance estimation from benchmarks."""

    def test_native_throughput_positive(self) -> None:
        t = PULVINIPerformanceEstimator.estimate_native_throughput()
        assert t > 0
        assert math.isfinite(t)

    def test_native_throughput_scales_with_golden_ratio(self) -> None:
        base = PULVINIPerformanceEstimator.estimate_native_throughput(1.0)
        scaled = PULVINIPerformanceEstimator.estimate_native_throughput(PHI)
        assert abs(scaled / base - PHI) < 1e-12

    def test_algorithmic_throughput_scales_with_instances(self) -> None:
        single = PULVINIPerformanceEstimator.estimate_algorithmic_throughput(1)
        multi = PULVINIPerformanceEstimator.estimate_algorithmic_throughput(10)
        assert abs(multi / single - 10.0) < 1e-10

    def test_power_consumption_reasonable(self) -> None:
        p = PULVINIPerformanceEstimator.estimate_power_consumption(1)
        assert 1000 < p < 10000  # Should be in kW range with overhead

    def test_efficiency_finite(self) -> None:
        eff = PULVINIPerformanceEstimator.estimate_algorithmic_efficiency(1)
        assert math.isfinite(eff)

    def test_compressed_working_set_ratio(self) -> None:
        assert PULVINIPerformanceEstimator.COMPRESSED_WORKING_SET_RATIO == 1.60


class TestComprehensiveComparison:
    """Full comparison framework integration."""

    @pytest.fixture
    def comparison(self) -> ComprehensiveComparison:
        return ComprehensiveComparison()

    def test_quantum_multiplier_positive(self, comparison: ComprehensiveComparison) -> None:
        assert comparison.total_quantum_multiplier > 1
        # 2.62 × 10 × 50 × 20 × 15 = 393,000
        assert abs(comparison.total_quantum_multiplier - 393000.0) < 1.0

    def test_single_instance_returns_full_structure(
        self, comparison: ComprehensiveComparison
    ) -> None:
        result = comparison.compare_single_instance()
        assert "pulvini_native_32_solver" in result
        assert "asic_comparison" in result
        assert result["pulvini_native_32_solver"]["num_solvers"] == 32

    def test_golden_ratio_scaling_requested_levels_and_combinations(
        self, comparison: ComprehensiveComparison
    ) -> None:
        results = comparison.compare_golden_ratio_scaling()
        required = {
            "10^7",
            "10^10",
            "10^12",
            "10^15",
            "10^18",
            "10^20",
            "10^31",
            "10^76",
        }
        assert required.issubset(results.keys())
        assert "10^7×10^10" in results
        assert "10^31×10^76" in results
        assert "asic_efficiency_curves" in results["10^12"]
        assert "latency_per_phi_tier_ms" in results["10^12"]

    def test_golden_ratio_monotonic_throughput(self, comparison: ComprehensiveComparison) -> None:
        results = comparison.compare_golden_ratio_scaling()
        throughputs = [
            results[s]["effective_hashrate_ths"]
            for s in [
                "10^7",
                "10^10",
                "10^12",
                "10^15",
                "10^18",
                "10^20",
                "10^31",
                "10^76",
            ]
        ]
        for i in range(1, len(throughputs)):
            assert throughputs[i] > throughputs[i - 1], f"Throughput not monotonic at index {i}"

    def test_golden_ratio_10_7_loses_to_asics(self, comparison: ComprehensiveComparison) -> None:
        """At 10^7 dynamic scale, PULVINI should lose to all ASICs."""
        results = comparison.compare_golden_ratio_scaling()
        for comp in results["10^7"]["asic_comparison"]:
            assert comp["pulvini_beats_asic"] is False, (
                f"{comp['asic']} should beat PULVINI at 10^7"
            )

    def test_golden_ratio_10_15_beats_all_asics(self, comparison: ComprehensiveComparison) -> None:
        """At 10^15 scale, PULVINI should beat all ASICs."""
        results = comparison.compare_golden_ratio_scaling()
        for comp in results["10^15"]["asic_comparison"]:
            assert comp["pulvini_beats_asic"] is True, (
                f"{comp['asic']} should lose to PULVINI at 10^15"
            )

    def test_golden_ratio_10_18_beats_all_asics(self, comparison: ComprehensiveComparison) -> None:
        results = comparison.compare_golden_ratio_scaling()
        for comp in results["10^18"]["asic_comparison"]:
            assert comp["pulvini_beats_asic"] is True

    def test_golden_ratio_10_20_beats_all_asics(self, comparison: ComprehensiveComparison) -> None:
        results = comparison.compare_golden_ratio_scaling()
        for comp in results["10^20"]["asic_comparison"]:
            assert comp["pulvini_beats_asic"] is True

    def test_efficiency_improves_with_scale(self, comparison: ComprehensiveComparison) -> None:
        """Efficiency (J/TH) should improve (decrease) as scale increases."""
        results = comparison.compare_golden_ratio_scaling()
        effs = [
            results[s]["hashrate_efficiency_j_th"]
            for s in [
                "10^7",
                "10^10",
                "10^12",
                "10^15",
                "10^18",
                "10^20",
                "10^31",
                "10^76",
            ]
        ]
        for i in range(1, len(effs)):
            assert effs[i] < effs[i - 1], (
                f"Efficiency worsened at index {i}: {effs[i - 1]} → {effs[i]}"
            )

    def test_report_generated(self, comparison: ComprehensiveComparison) -> None:
        report = comparison.generate_golden_ratio_report()
        assert isinstance(report, str)
        assert len(report) > 500
        assert "GOLDEN RATIO SCALING" in report
        assert "COMPETITIVE SCALES" in report

    def test_comprehensive_report_generated(self, comparison: ComprehensiveComparison) -> None:
        report = comparison.generate_comprehensive_report()
        assert isinstance(report, str)
        assert len(report) > 500
        assert "COMPREHENSIVE ASIC" in report

    def test_asic_comparison_includes_all_six(self, comparison: ComprehensiveComparison) -> None:
        results = comparison.compare_golden_ratio_scaling()
        asics = [comp["asic"] for comp in results["10^15"]["asic_comparison"]]
        assert len(set(asics)) == 6

    def test_hashrate_ratio_increases_with_scale(self, comparison: ComprehensiveComparison) -> None:
        results = comparison.compare_golden_ratio_scaling()
        ratios_12 = {c["asic"]: c["hashrate_ratio"] for c in results["10^12"]["asic_comparison"]}
        ratios_15 = {c["asic"]: c["hashrate_ratio"] for c in results["10^15"]["asic_comparison"]}
        for asic in ratios_12:
            assert ratios_15[asic] > ratios_12[asic], f"{asic} ratio didn't increase"

    def test_efficiency_ratio_decreases_with_scale(
        self, comparison: ComprehensiveComparison
    ) -> None:
        results = comparison.compare_golden_ratio_scaling()
        eff_12 = {c["asic"]: c["efficiency_ratio"] for c in results["10^12"]["asic_comparison"]}
        eff_15 = {c["asic"]: c["efficiency_ratio"] for c in results["10^15"]["asic_comparison"]}
        for asic in eff_12:
            assert eff_15[asic] < eff_12[asic], f"{asic} efficiency ratio didn't decrease"

    def test_asic_efficiency_curves_include_resonance_points(
        self, comparison: ComprehensiveComparison
    ) -> None:
        results = comparison.compare_golden_ratio_scaling()
        curves = results["10^12"]["asic_efficiency_curves"]
        assert len(curves) == len(ASICPerformanceData.get_all_specs())
        assert curves[0]["energy_per_phi_tier_j"] > 0
        assert curves[0]["latency_per_phi_tier_ms"] > 0
        assert "resonance_delta_from_parity" in curves[0]["asic_specific_resonance_point"]

    def test_pulvini_beats_asic_criteria(self, comparison: ComprehensiveComparison) -> None:
        """Verification: pulvini_beats_asic should be True iff hashrate_ratio > 1 AND efficiency_ratio < 1."""
        results = comparison.compare_golden_ratio_scaling()
        for scale in GoldenRatioScaling.get_scaling_factors(include_combinations=True):
            for comp in results[scale]["asic_comparison"]:
                expected = comp["hashrate_ratio"] > 1.0 and comp["efficiency_ratio"] < 1.0
                assert comp["pulvini_beats_asic"] == expected, (
                    f"Mismatch at {scale}/{comp['asic']}: expected {expected}, "
                    f"got {comp['pulvini_beats_asic']} "
                    f"(hr_ratio={comp['hashrate_ratio']:.2e}, eff_ratio={comp['efficiency_ratio']:.2e})"
                )


# ============================================================================
# SECTION 4 — Cross-Validation Against Published Golden Ratio Results
# ============================================================================


class TestPublishedResultsCrossValidation:
    """Validate against golden_ratio_scaling_results.json."""

    @pytest.fixture(scope="class")
    def published(self) -> dict[str, Any]:
        path = ROOT / "golden_ratio_scaling_results.json"
        if not path.exists():
            pytest.skip("golden_ratio_scaling_results.json not found")
        with open(path) as f:
            return json.load(f)

    @pytest.fixture(scope="class")
    def computed(self) -> dict[str, Any]:
        comparison = ComprehensiveComparison()
        return comparison.compare_golden_ratio_scaling()

    def test_scales_match(self, published: dict, computed: dict) -> None:
        pub_scales = set(published["golden_ratio_scaling"].keys())
        comp_scales = set(computed.keys())
        assert pub_scales == comp_scales, f"Scales differ: {pub_scales} vs {comp_scales}"

    def test_throughput_within_reasonable_tolerance(self, published: dict, computed: dict) -> None:
        for scale in GoldenRatioScaling.get_scaling_factors(include_combinations=True):
            pub_t = published["golden_ratio_scaling"][scale][
                "effective_throughput_with_quantum_advantages"
            ]
            comp_t = computed[scale]["effective_throughput_with_quantum_advantages"]
            # Allow small floating-point discrepancies
            ratio = comp_t / pub_t if pub_t != 0 else float("inf")
            assert 0.99 < ratio < 1.01, (
                f"Throughput mismatch at {scale}: {comp_t} vs {pub_t} (ratio {ratio})"
            )

    def test_asic_data_consistent(self, published: dict) -> None:
        pub_asics = published["asic_data"]
        code_asics = ASICPerformanceData.get_all_specs()
        for name in pub_asics:
            assert name in code_asics, f"{name} missing from code"
            for key in ["hashrate_ths", "power_w", "efficiency_j_th"]:
                assert pub_asics[name][key] == code_asics[name][key], (
                    f"{name}.{key} mismatch: {pub_asics[name][key]} vs {code_asics[name][key]}"
                )

    def test_quantum_advantages_consistent(self, published: dict) -> None:
        comparison = ComprehensiveComparison()
        pub_qa = published["quantum_advantages"]
        assert abs(pub_qa["total_multiplier"] - comparison.total_quantum_multiplier) < 0.1
        assert pub_qa["phi_folding_compression"] == pytest.approx(
            comparison.PHI_FOLDING_COMPRESSION, rel=1e-3
        )
        assert pub_qa["state_discrimination"] == pytest.approx(
            comparison.STATE_DISCRIMINATION, rel=1e-3
        )


# ============================================================================
# SECTION 5 — Property-Based Tests (Invariant-Driven)
# ============================================================================


class TestPropertyBasedInvariants:
    """Invariant checks for the golden ratio scaling system."""

    def test_phi_scale_factor_self_similarity(self) -> None:
        """Dynamic scaling preserves self-similarity: S(a+b) == S(a)×S(b)."""
        scaled_7 = GoldenRatioScaling.apply_scaling(1.0, 7)
        scaled_10 = GoldenRatioScaling.apply_scaling(1.0, 10)
        scaled_17 = GoldenRatioScaling.apply_scaling(1.0, 17)
        assert scaled_7 * scaled_10 == pytest.approx(scaled_17, rel=1e-12)

    def test_decision_normalization_invariant(self) -> None:
        """All phi_weights from a non-empty prediction should sum to 1."""
        import random

        engine = PhiScaledEnsemble()
        for _ in range(20):
            n = random.randint(1, 5)
            predictions = {f"m{i}": {"score": random.uniform(0, 1)} for i in range(n)}
            result = engine.predict_with_phi_scaling(predictions, {})
            if result["phi_weights"]:
                assert abs(sum(result["phi_weights"]) - 1.0) < 1e-10

    def test_benchmark_determinism(self) -> None:
        """Same inputs → same outputs."""
        a = benchmark_vs_asic(measured_hashes_per_second=500e12)
        b = benchmark_vs_asic(measured_hashes_per_second=500e12)
        assert a["effective_hashes_per_second"] == b["effective_hashes_per_second"]
        assert a["projected_vs_asic_ratio"] == b["projected_vs_asic_ratio"]

    def test_coherence_bounded(self) -> None:
        """Coherence values should always be in [0, 1]."""
        engine = PhiScaledEnsemble()
        for variance in [0.0, 0.03, 0.1, 0.3, 0.5]:
            predictions = {
                "a": {"score": 0.5 + variance},
                "b": {"score": 0.5 - variance},
            }
            result = engine.predict_with_phi_scaling(predictions, {})
            assert 0.0 <= result["coherence"] <= 1.0, (
                f"Coherence out of bounds for variance {variance}"
            )

    def test_power_scaling_sub_linear(self) -> None:
        """Doubling the golden ratio scale should less-than-double the power (sub-linear)."""
        p1 = PULVINIPerformanceEstimator.estimate_power_consumption(1, 1.0)
        p2 = PULVINIPerformanceEstimator.estimate_power_consumption(1, 2.0)
        assert p2 < 2 * p1, "Power scaling should be sub-linear"

    def test_efficiency_monotonic_with_scale(self) -> None:
        """Efficiency should always improve (decrease) as scale increases."""
        results = ComprehensiveComparison().compare_golden_ratio_scaling()
        effs = [
            results[s]["hashrate_efficiency_j_th"]
            for s in [
                "10^7",
                "10^10",
                "10^12",
                "10^15",
                "10^18",
                "10^20",
                "10^31",
                "10^76",
            ]
        ]
        for i in range(len(effs) - 1):
            assert effs[i + 1] < effs[i], f"Efficiency non-monotonic at index {i}"

    @pytest.mark.skipif(given is None, reason="hypothesis not installed")
    @settings(max_examples=50, deadline=None)
    @given(st.integers(min_value=0, max_value=30), st.integers(min_value=0, max_value=30))
    def test_dynamic_phi_combinations_are_multiplicative(self, left: int, right: int) -> None:
        combined = GoldenRatioScaling.apply_scaling(1.0, left + right)
        multiplied = GoldenRatioScaling.apply_scaling(1.0, left) * GoldenRatioScaling.apply_scaling(
            1.0, right
        )
        assert multiplied == pytest.approx(combined, rel=1e-12)

    @pytest.mark.skipif(given is None, reason="hypothesis not installed")
    @settings(max_examples=50, deadline=None)
    @given(st.integers(min_value=0, max_value=75))
    def test_dynamic_phi_scale_is_exponential(self, exponent: int) -> None:
        current_scale = GoldenRatioScaling.scale_factor_for_exponent(exponent)
        next_scale = GoldenRatioScaling.scale_factor_for_exponent(exponent + 1)
        assert next_scale / current_scale == pytest.approx(10 * PHI, rel=1e-12)

    def test_phi_resonance_alternating_no_resonance(self) -> None:
        """[φ, 1/φ, φ, 1/φ, ...] has ratios φ⁻² and φ² — not φ — so no resonance."""
        analyzer = PhiResonanceAnalyzer()
        seq = [PHI, PHI_INV, PHI, PHI_INV, PHI, PHI_INV]
        result = analyzer.analyze_phi_resonance({"alternating": seq})
        # Ratios alternate: 1/φ² ≈ 0.382 and φ² ≈ 2.618. Neither ≈ φ (1.618).
        # Since harmony_score < 0.3, resonance is not reported
        assert "alternating_resonance" not in result


# ============================================================================
# SECTION 6 — Structural / Code Quality Checks
# ============================================================================


class TestCodeQuality:
    """Basic structural quality checks."""

    def test_phi_scaling_engine_has_all_exports(self) -> None:
        from pythia_mining import phi_scaling_engine

        for name in [
            "PHI",
            "PHI_INV",
            "PhiDecision",
            "PhiFeatureScore",
            "PhiBenchmark",
            "PhiScaledEnsemble",
            "PhiOptimizedFeatures",
            "PhiResonanceAnalyzer",
            "benchmark_vs_asic",
            "calculate_phi_performance",
        ]:
            assert hasattr(phi_scaling_engine, name), f"Missing export: {name}"

    def test_no_subprocess_calls_in_comparison_framework(self) -> None:
        """The comparison framework should be pure math, no subprocess calls."""
        import inspect

        source = inspect.getsource(ComprehensiveComparison)
        assert "subprocess" not in source
        assert "os.system" not in source
        assert "os.popen" not in source
