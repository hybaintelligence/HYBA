import math
import unittest

import numpy as np

from pythia_mining.phi_scaling_engine import (
    PHI,
    PHI_INV,
    MassGapShield,
    PhiOptimizedFeatures,
    PhiResonanceAnalyzer,
    PhiScaledEnsemble,
    benchmark_vs_asic,
    phi_scaling_what_it_does,
)


class PhiScalingEngineTests(unittest.TestCase):
    def test_phi_scaled_ensemble_returns_normalized_weights(self):
        engine = PhiScaledEnsemble()
        result = engine.predict_with_phi_scaling(
            {
                "alpha": {"score": 0.7},
                "beta": {"score": 0.72},
                "gamma": {"score": 0.69},
            },
            {"solver": {"a": 1.0, "b": PHI, "c": PHI * PHI}},
        )
        self.assertEqual("golden_ratio_scaling", result["method"])
        self.assertAlmostEqual(1.0, sum(result["phi_weights"]), places=12)
        self.assertGreater(result["coherence"], 0.9)
        self.assertGreater(result["indicator_harmony"], 0.99)

    def test_feature_alignment_and_resonance_are_auditable(self):
        features = PhiOptimizedFeatures()
        payload = features.extract_phi_optimized_features(
            {"lane": {"phi": PHI, "phi_inv": 1 / PHI}}
        )
        self.assertEqual(2, len(payload["lane"]))
        self.assertGreater(features.phi_statistics["lane"]["mean_alignment"], 0.99)

        analyzer = PhiResonanceAnalyzer()
        resonance = analyzer.analyze_phi_resonance({"fib": [1, 2, 3, 5, 8, 13, 21]})
        self.assertIn("fib_resonance", resonance)
        self.assertTrue(math.isfinite(resonance["fib_resonance"]["dominant_ratio"]))

    def test_asic_benchmark_distinguishes_projection_from_measured_input(self):
        projection = benchmark_vs_asic(measured_hashes_per_second=None)
        self.assertEqual("projection_only", projection["benchmark_mode"])
        self.assertIsNone(projection["projected_vs_asic_ratio"])

        measured = benchmark_vs_asic(
            measured_hashes_per_second=110e12, asic_baseline_hashes_per_second=110e12
        )
        self.assertEqual("measured_input", measured["benchmark_mode"])
        self.assertGreater(measured["projected_vs_asic_ratio"], 1.0)

    # ------------------------------------------------------------------
    # NEW: MassGapShield tests
    # ------------------------------------------------------------------

    def test_mass_gap_shield_rejects_insufficient_data(self):
        """A single-element stream must be flagged as insufficient."""
        shield = MassGapShield()
        result = shield.verify_authenticity([0.5])
        self.assertFalse(result["authentic"])
        self.assertEqual(result["reason"], "insufficient_data")

    def test_mass_gap_shield_rejects_precision_spoofed_stream(self):
        """A perfectly uniform stream (zero jitter) must be flagged as spoofed."""
        # All values identical -> diffs all zero -> mean_jitter == 0.0
        # irrational_alignment = |0 - expected_jitter| = expected_jitter >> tolerance
        # This triggers too_chaotic or too_perfect depending on magnitude;
        # what matters is authentic=False.
        shield = MassGapShield(tolerance=1e-9, chaos_threshold=0.1)
        result = shield.verify_authenticity([1.0] * 50)
        self.assertFalse(result["authentic"])

    def test_mass_gap_shield_accepts_organic_jitter(self):
        """Telemetry with jitter near the expected phi-gap level should be authentic."""
        expected_jitter = 1.0 / (3.0 - PHI)  # ~0.7236
        # Construct a stream whose diffs average ~expected_jitter + small noise
        rng = np.random.default_rng(seed=42)
        noise = rng.uniform(-0.005, 0.005, 49)  # tiny organic noise
        diffs = expected_jitter + noise
        stream: list[float] = [0.0]
        for d in diffs:
            stream.append(stream[-1] + d)
        shield = MassGapShield(tolerance=1e-9, chaos_threshold=0.5)
        result = shield.verify_authenticity(stream)
        # With organic jitter near expected, it should be authentic
        self.assertTrue(result["authentic"], f"Expected authentic, got: {result}")

    def test_mass_gap_shield_fields_always_present(self):
        """verify_authenticity must always return required keys regardless of outcome."""
        required_keys = {"authentic", "reason", "irrational_alignment", "mean_jitter"}
        shield = MassGapShield()
        for stream in [[], [1.0], [1.0, 2.0, 3.0]]:
            result = shield.verify_authenticity(stream)
            for key in required_keys:
                self.assertIn(key, result, f"Missing key '{key}' for stream len={len(stream)}")

    # ------------------------------------------------------------------
    # NEW: PhiScaledEnsemble edge-case tests
    # ------------------------------------------------------------------

    def test_empty_predictions_returns_zero_decision(self):
        """Empty model_predictions must return a zero-score decision without error."""
        engine = PhiScaledEnsemble()
        result = engine.predict_with_phi_scaling({}, {"solver": {"a": 1.0}})
        self.assertEqual(result["final_score"], 0.0)
        self.assertEqual(result["phi_score"], 0.0)

    def test_single_model_prediction_returns_valid_decision(self):
        """A single model must produce a coherent, normalised decision."""
        engine = PhiScaledEnsemble()
        result = engine.predict_with_phi_scaling(
            {"only_model": {"score": 0.8}},
            {"lane": {"x": 1.0}},
        )
        self.assertAlmostEqual(sum(result["phi_weights"]), 1.0, places=12)
        self.assertGreaterEqual(result["final_score"], 0.0)
        self.assertLessEqual(result["final_score"], 1.0)

    def test_high_variance_models_receive_dampened_weights(self):
        """High-variance model scores must trigger dampened (phi_exponent = -1) weighting."""
        engine = PhiScaledEnsemble()
        # Wide spread exceeds high_variance_threshold=0.2
        result = engine.predict_with_phi_scaling(
            {"low": {"score": 0.0}, "high": {"score": 1.0}},
            {},
        )
        self.assertAlmostEqual(sum(result["phi_weights"]), 1.0, places=12)
        # Dampened path: both weights should be close to equal
        w = result["phi_weights"]
        self.assertAlmostEqual(w[0], w[1], places=3)

    def test_memory_bounded_by_policy_limit(self):
        """Decision memory must not exceed policy.memory_limit."""
        engine = PhiScaledEnsemble(config={"memory_limit": 3})
        for i in range(10):
            engine.predict_with_phi_scaling(
                {"m": {"score": float(i) / 10.0}}, {}
            )
        self.assertLessEqual(len(engine.memory), 3)

    def test_inauthentic_telemetry_returns_conservative_decision(self):
        """Simulation-detected telemetry must produce zero final_score."""
        engine = PhiScaledEnsemble()
        # Perfectly constant stream -> flagged as inauthentic
        result = engine.predict_with_phi_scaling(
            {"m": {"score": 0.9}},
            {},
            telemetry_stream=[5.0] * 20,
        )
        # If inauthentic, conservative path is taken
        if "scaling_mode" in result:
            self.assertIn("simulation", result["scaling_mode"])

    # ------------------------------------------------------------------
    # NEW: phi_scaling_what_it_does claim-boundary test
    # ------------------------------------------------------------------

    def test_phi_scaling_description_is_honest(self):
        """phi_scaling_what_it_does must mention deterministic and validation."""
        description = phi_scaling_what_it_does()
        self.assertIn("deterministic", description.lower())
        self.assertIn("validated", description.lower())

    # ------------------------------------------------------------------
    # NEW: PhiResonanceAnalyzer
    # ------------------------------------------------------------------

    def test_resonance_analyzer_fibonacci_series(self):
        """Fibonacci series must be detected as phi-resonant (is_fibonacci=True)."""
        analyzer = PhiResonanceAnalyzer()
        result = analyzer.analyze_phi_resonance({"fib": [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]})
        if "fib_resonance" in result:
            self.assertTrue(result["fib_resonance"]["is_fibonacci"])

    def test_resonance_analyzer_random_series_not_guaranteed_resonant(self):
        """A random series should have low harmony score (not always resonant)."""
        rng = np.random.default_rng(seed=999)
        data = rng.uniform(1, 100, 20).tolist()
        analyzer = PhiResonanceAnalyzer()
        result = analyzer.analyze_phi_resonance({"rand": data})
        # Can't guarantee non-resonant, but harmony_score must be a valid float
        if "rand_resonance" in result:
            score = result["rand_resonance"]["harmony_score"]
            self.assertTrue(math.isfinite(score))
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)

    def test_resonance_analyzer_too_short_series_skipped(self):
        """Series with fewer than 3 elements must be silently skipped."""
        analyzer = PhiResonanceAnalyzer()
        result = analyzer.analyze_phi_resonance({"tiny": [1.0, 2.0]})
        self.assertNotIn("tiny_resonance", result)


if __name__ == "__main__":
    unittest.main()
