from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from pythia_mining.pulvini_certificates import phi_geometric_structure_certificate  # noqa: E402
from pythia_mining.pulvini_nonce_compression import PulviniNonceSpaceCompressor  # noqa: E402


class PhiGeometricStructureTests(unittest.TestCase):
    def test_phi_lane_distribution_is_mapped_to_pulvini_topology(self) -> None:
        compressor = PulviniNonceSpaceCompressor()
        plan = compressor.build_compression_plan()

        cert = phi_geometric_structure_certificate(
            plan,
            compressor,
            sample_size=1_000_000,
            seed=20260611,
        )

        self.assertEqual(cert["sample_size"], 1_000_000)
        self.assertEqual(cert["lane_count"], 32)
        self.assertGreater(cert["overall_phi_ratio"], 0.53)
        self.assertLess(cert["overall_phi_ratio"], 0.55)
        self.assertGreater(cert["lane_variance"], 1e-9)
        self.assertTrue(cert["non_identical_lane_measure"])
        self.assertLess(cert["d_i_delta"], 0.01)
        self.assertLess(cert["variance_to_sampling_ratio"], 2.0)
        self.assertAlmostEqual(cert["chi_square_critical_p_0_05"], 44.99, places=2)
        self.assertLess(cert["hit_only_chi_square"], cert["chi_square_critical_p_0_05"])
        self.assertLess(cert["pearson_chi_square"], cert["chi_square_critical_p_0_05"])
        self.assertFalse(cert["reject_uniform_lane_null_p_0_05"])
        self.assertFalse(cert["geometric_structure_detected"])
        self.assertEqual(
            cert["status"], "uniform_lane_distribution_not_rejected_p_0_05"
        )

        print("PHI GEOMETRIC STRUCTURE CERTIFICATE")
        print(f"  Manifold mean phi-ratio: {cert['manifold_mean_phi_ratio']:.6f}")
        print(f"  D-node avg phi-ratio: {cert['d_node_avg_phi_ratio']:.6f}")
        print(f"  I-node avg phi-ratio: {cert['i_node_avg_phi_ratio']:.6f}")
        print(f"  Lane variance: {cert['lane_variance']:.10f}")
        print(f"  Variance/sampling ratio: {cert['variance_to_sampling_ratio']:.3f}")
        print(f"  Hit-only chi-square: {cert['hit_only_chi_square']:.3f}")
        print(f"  Pearson chi-square: {cert['pearson_chi_square']:.3f}")
        print(f"  Critical chi-square p=0.05: {cert['chi_square_critical_p_0_05']:.2f}")
        print(f"  Reduced chi-square: {cert['reduced_chi_square']:.3f}")
        print(
            f"  Reject uniform lane null at p=0.05: {cert['reject_uniform_lane_null_p_0_05']}"
        )
        print(f"  Result: {cert['status']}")


if __name__ == "__main__":
    unittest.main()
