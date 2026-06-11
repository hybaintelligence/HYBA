import math
import unittest

from pythia_mining.phi_scaling_engine import (
    PHI,
    PhiOptimizedFeatures,
    PhiResonanceAnalyzer,
    PhiScaledEnsemble,
    benchmark_vs_asic,
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
        payload = features.extract_phi_optimized_features({"lane": {"phi": PHI, "phi_inv": 1 / PHI}})
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

        measured = benchmark_vs_asic(measured_hashes_per_second=110e12, asic_baseline_hashes_per_second=110e12)
        self.assertEqual("measured_input", measured["benchmark_mode"])
        self.assertGreater(measured["projected_vs_asic_ratio"], 1.0)


if __name__ == "__main__":
    unittest.main()
