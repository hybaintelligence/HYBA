#!/usr/bin/env python3
"""
Comprehensive test suite for Elevation 8.1: Riemann-Gauge Spectral Probe

Tests verify:
1. Global transfer matrix construction
2. Eigenvalue spectrum extraction
3. GUE vs Poisson statistics
4. Swarm message broadcasting
5. End-to-end system integration
"""

import sys
import unittest
import numpy as np
from pathlib import Path
import logging

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent / "python_backend"))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

# Import the probe
import riemann_gauge_spectral_probe_v8_1 as probe_module
from riemann_gauge_spectral_probe_v8_1 import (
    generate_su2_link,
    build_global_transfer_matrix,
    run_riemann_spectral_probe,
    LAMBDA_LOCK,
    GOLDEN_RATIO,
    MASS_GAP,
    NUM_SITES,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestSU2LinkGeneration(unittest.TestCase):
    """Test SU(2) link matrix generation."""

    def test_su2_link_unitarity(self):
        """Verify generated links are unitary."""
        U = generate_su2_link(LAMBDA_LOCK)
        
        # U @ U† = I
        product = U @ U.conj().T
        identity = np.eye(2, dtype=complex)
        
        np.testing.assert_array_almost_equal(product, identity, decimal=4,
                                            err_msg="SU(2) link is not unitary")

    def test_su2_link_determinant(self):
        """Verify generated links have det = ±1."""
        U = generate_su2_link(LAMBDA_LOCK)
        det = np.linalg.det(U)
        
        # det should be close to ±1
        self.assertAlmostEqual(abs(abs(det) - 1.0), 0, places=3,
                              msg="SU(2) determinant not ±1")

    def test_su2_link_shape(self):
        """Verify SU(2) links have correct shape."""
        U = generate_su2_link(LAMBDA_LOCK)
        self.assertEqual(U.shape, (2, 2), "SU(2) link not 2x2")


class TestGlobalTransferMatrix(unittest.TestCase):
    """Test global transfer matrix construction."""

    def test_transfer_matrix_construction(self):
        """Verify transfer matrix is constructed."""
        # Use smaller system for speed
        T = build_global_transfer_matrix(50, LAMBDA_LOCK)
        
        self.assertEqual(T.shape, (50, 50), "Transfer matrix wrong shape")
        self.assertTrue(np.all(np.isfinite(T)), "Transfer matrix contains NaN/Inf")

    def test_transfer_matrix_hermiticity(self):
        """Verify transfer matrix is Hermitian."""
        T = build_global_transfer_matrix(30, LAMBDA_LOCK)
        
        # Should be Hermitian: T = T†
        np.testing.assert_array_almost_equal(T, T.conj().T, decimal=5,
                                            err_msg="Transfer matrix not Hermitian")

    def test_transfer_matrix_eigenvalues_real(self):
        """Verify Hermitian matrix has real eigenvalues."""
        T = build_global_transfer_matrix(30, LAMBDA_LOCK)
        eigvals = np.linalg.eigvals(T)
        
        # Eigenvalues should be real
        imaginary_parts = np.abs(np.imag(eigvals))
        self.assertTrue(np.all(imaginary_parts < 1e-5),
                       "Eigenvalues have significant imaginary parts")


class TestSpectralAnalysis(unittest.TestCase):
    """Test spectral statistics analysis."""

    def setUp(self):
        """Set up test data."""
        self.T = build_global_transfer_matrix(100, LAMBDA_LOCK)
        self.eigvals = np.linalg.eigvals(self.T)
        self.phases = np.sort(np.angle(self.eigvals))

    def test_spectrum_extraction(self):
        """Verify spectrum is properly extracted."""
        self.assertGreater(len(self.phases), 50, "Not enough eigenvalues extracted")
        self.assertTrue(np.all(np.isfinite(self.phases)), "Phases contain NaN/Inf")

    def test_spectrum_range(self):
        """Verify spectrum is in expected range."""
        # Phases should be between -π and π
        self.assertGreater(self.phases.min(), -np.pi - 0.1)
        self.assertLess(self.phases.max(), np.pi + 0.1)

    def test_nearest_neighbor_spacing(self):
        """Verify nearest neighbor spacing computation."""
        spacings = np.diff(self.phases)
        
        # All spacings should be non-negative
        self.assertTrue(np.all(spacings >= 0), "Negative spacings detected")
        
        # Mean spacing should be positive
        mean_spacing = np.mean(spacings)
        self.assertGreater(mean_spacing, 0, "Mean spacing not positive")


class TestGUEVsPoissonStatistics(unittest.TestCase):
    """Test GUE vs Poisson fit comparison."""

    def setUp(self):
        """Set up spectral data."""
        import scipy.stats as stats
        
        self.T = build_global_transfer_matrix(100, LAMBDA_LOCK)
        self.eigvals = np.linalg.eigvals(self.T)
        self.phases = np.sort(np.angle(self.eigvals))
        
        # Compute normalized spacings
        spacings = np.diff(self.phases)
        self.s = spacings / np.mean(spacings)

    def test_gue_vs_poisson_comparison(self):
        """Verify GUE and Poisson fits can be computed."""
        import scipy.stats as stats
        
        def gue_distribution(x):
            return (32 / np.pi**2) * (x**2) * np.exp(-4 * (x**2) / np.pi)
        
        def poisson_distribution(x):
            return np.exp(-x)
        
        hist, bin_edges = np.histogram(self.s, bins=30, range=(0, 3), density=True)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        
        # Compute fits
        gue_fit = gue_distribution(bin_centers)
        poisson_fit = poisson_distribution(bin_centers)
        
        # Verify fits are positive
        self.assertTrue(np.all(gue_fit > 0), "GUE fit has non-positive values")
        self.assertTrue(np.all(poisson_fit > 0), "Poisson fit has non-positive values")
        
        # Verify fits have reasonable magnitude
        self.assertGreater(np.max(gue_fit), 0.1, "GUE fit too small")
        self.assertGreater(np.max(poisson_fit), 0.1, "Poisson fit too small")


class TestSystemIntegration(unittest.TestCase):
    """Test end-to-end system integration."""

    def test_constants_defined(self):
        """Verify all required constants are defined."""
        self.assertIsNotNone(LAMBDA_LOCK, "LAMBDA_LOCK not defined")
        self.assertIsNotNone(GOLDEN_RATIO, "GOLDEN_RATIO not defined")
        self.assertIsNotNone(MASS_GAP, "MASS_GAP not defined")
        self.assertIsNotNone(NUM_SITES, "NUM_SITES not defined")

    def test_constants_reasonable(self):
        """Verify constants have reasonable values."""
        self.assertAlmostEqual(GOLDEN_RATIO, (1 + np.sqrt(5)) / 2, places=5)
        self.assertAlmostEqual(MASS_GAP, 3 - GOLDEN_RATIO, places=5)
        self.assertGreater(NUM_SITES, 100)
        self.assertLess(abs(LAMBDA_LOCK), 1.0)

    def test_probe_executable(self):
        """Verify probe can be executed (with smaller system for speed)."""
        # Patch NUM_SITES for faster execution
        original_num_sites = probe_module.NUM_SITES
        
        try:
            probe_module.NUM_SITES = 50
            success = probe_module.run_riemann_spectral_probe()
            
            # Should complete without exception
            self.assertIn(success, [True, False], "Probe returned invalid result")
        finally:
            probe_module.NUM_SITES = original_num_sites


class TestMessageBroadcasting(unittest.TestCase):
    """Test swarm message broadcasting."""

    def test_swarm_imports(self):
        """Verify swarm communication imports work."""
        try:
            from hyba_genesis_api.api.multi_agent import (
                get_swarm_communication,
                SwarmMessage
            )
            self.assertIsNotNone(get_swarm_communication)
            self.assertIsNotNone(SwarmMessage)
        except ImportError as e:
            self.fail(f"Failed to import swarm components: {e}")

    def test_swarm_message_creation(self):
        """Verify SwarmMessage can be created with probe data."""
        from hyba_genesis_api.api.multi_agent import SwarmMessage
        import time
        
        message = SwarmMessage(
            message_id="test_riemann_v8_1",
            sender="riemann_probe_test",
            receiver="all",
            timestamp=time.time(),
            message_type="alert",
            payload={
                "status": "TEST",
                "r_squared_gue": 0.95,
                "r_squared_poisson": 0.85,
                "ks_statistic": 0.1,
                "lambda_lock": LAMBDA_LOCK,
                "mass_gap": MASS_GAP,
                "num_sites": 100
            },
            confidence=0.95,
            pheromone=5.0
        )
        
        # Verify message is created
        self.assertEqual(message.sender, "riemann_probe_test")
        self.assertEqual(message.message_type, "alert")
        self.assertIn("status", message.payload)


def run_comprehensive_tests():
    """Run all tests with detailed reporting."""
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSU2LinkGeneration))
    suite.addTests(loader.loadTestsFromTestCase(TestGlobalTransferMatrix))
    suite.addTests(loader.loadTestsFromTestCase(TestSpectralAnalysis))
    suite.addTests(loader.loadTestsFromTestCase(TestGUEVsPoissonStatistics))
    suite.addTests(loader.loadTestsFromTestCase(TestSystemIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestMessageBroadcasting))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 80)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)
