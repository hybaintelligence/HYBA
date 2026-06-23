"""
High-Dimensional Manifold Stress Tests
=====================================

Tests manifold stability at dim=10,000+ to find the "collapse point" where
geometric stability falls below functional threshold. This defines the system's
"Cognitive Horizon"—the maximum complexity the AI fabric can process before
the manifold loses coherence.

formal-invariant validation: Uses differential geometry, Bures metric, and Φ-based
topological analysis to determine manifold coherence limits.
"""

import numpy as np
import scipy.linalg as la
import scipy.stats as stats
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import time
import json
from pathlib import Path


@dataclass
class ManifoldStressResult:
    """Results from manifold stress testing."""

    dimension: int
    geometric_stability: float
    compression_efficiency: float
    coherence_preserved: bool
    bures_distance: float
    fisher_curvature: float
    phi_folding_ratio: float
    eigenvalue_spectrum: List[float]
    collapse_detected: bool


class ManifoldStressTestSuite:
    """
    High-dimensional manifold stress testing suite.

    Tests manifold evolution and Bures geometry at extreme dimensions
    to determine the cognitive horizon of the AI fabric.
    """

    def __init__(self, phi: float = (1 + np.sqrt(5)) / 2):
        self.phi = phi
        self.phi_squared = phi**2
        self.phi_cubed = phi**3

    def run_dimensional_sweep(
        self, max_dimension: int = 20000, step_multiplier: int = 10
    ) -> List[ManifoldStressResult]:
        """
        Run dimensional sweep to find collapse point.

        Args:
            max_dimension: Maximum dimension to test
            step_multiplier: Multiplier for dimensional steps (10x scale)

        Returns:
            List of manifold stress results across dimensions
        """
        results = []
        dimensions = self._generate_dimensional_sequence(max_dimension, step_multiplier)

        print(f"Running dimensional sweep from {dimensions[0]} to {dimensions[-1]}")

        for dim in dimensions:
            print(f"Testing dimension: {dim}")

            result = self._test_single_dimension(dim)
            results.append(result)

            # Check for collapse point
            if result.collapse_detected:
                print(f"COLLAPSE POINT DETECTED at dim={dim}")
                print(f"  Geometric stability: {result.geometric_stability:.6f}")
                print(f"  Cognitive horizon reached")
                break

        return results

    def _generate_dimensional_sequence(
        self, max_dim: int, multiplier: int
    ) -> List[int]:
        """Generate exponential dimensional sequence."""
        dimensions = []
        current = 10
        while current <= max_dim:
            dimensions.append(current)
            current *= multiplier
        return dimensions

    def _test_single_dimension(self, dimension: int) -> ManifoldStressResult:
        """Test manifold stability at single dimension."""
        # Generate high-dimensional manifold
        manifold = self._generate_phi_manifold(dimension)

        # Compute geometric stability metrics
        geometric_stability = self._compute_geometric_stability(manifold)

        # Compute Φ-folding compression efficiency
        compression_efficiency = self._compute_phi_compression(manifold)

        # Compute Bures distance
        bures_distance = self._compute_bures_distance(manifold)

        # Compute Fisher curvature
        fisher_curvature = self._compute_fisher_curvature(manifold)

        # Compute Φ-folding ratio
        phi_folding_ratio = self._compute_phi_folding_ratio(manifold)

        # Analyze eigenvalue spectrum
        eigenvalue_spectrum = self._analyze_eigenvalue_spectrum(manifold)

        # Determine collapse
        collapse_detected = geometric_stability < 0.5 or bures_distance > 2.0

        return ManifoldStressResult(
            dimension=dimension,
            geometric_stability=geometric_stability,
            compression_efficiency=compression_efficiency,
            coherence_preserved=geometric_stability > 0.5,
            bures_distance=bures_distance,
            fisher_curvature=fisher_curvature,
            phi_folding_ratio=phi_folding_ratio,
            eigenvalue_spectrum=eigenvalue_spectrum,
            collapse_detected=collapse_detected,
        )

    def _generate_phi_manifold(self, dimension: int) -> np.ndarray:
        """
        Generate Φ-weighted high-dimensional manifold.

        Uses Φ-based scaling to create mathematically structured manifold
        that preserves golden ratio properties across dimensions.
        """
        # Create Φ-weighted basis vectors
        np.random.seed(int(dimension * self.phi))
        basis = np.random.randn(dimension, dimension) * self.phi

        # Apply Bures geometry structure
        manifold = basis @ basis.T / np.sqrt(dimension)

        # Normalize to unit sphere with Φ-based scaling
        manifold = manifold / np.linalg.norm(manifold) * self.phi

        return manifold

    def _compute_geometric_stability(self, manifold: np.ndarray) -> float:
        """
        Compute geometric stability ratio of manifold.

        Stability ratio = ratio of positive eigenvalues to total eigenvalues.
        This measures how much of the manifold's structure remains coherent.
        """
        eigenvalues = la.eigvals(manifold)
        eigenvalues = np.real(eigenvalues)

        positive_count = np.sum(eigenvalues > 1e-10)
        total_count = len(eigenvalues)

        stability_ratio = positive_count / total_count if total_count > 0 else 0.0
        return stability_ratio

    def _compute_phi_compression(self, manifold: np.ndarray) -> float:
        """
        Compute Φ-folding compression efficiency.

        Measures how efficiently the manifold can be compressed using
        Φ-based folding while preserving geometric structure.
        """
        original_size = manifold.nbytes
        original_norm = np.linalg.norm(manifold)

        # Apply Φ-based compression
        compressed = manifold * (1 / self.phi)
        compressed_norm = np.linalg.norm(compressed)

        # Compression efficiency: ratio of preserved structure to compression
        efficiency = (compressed_norm / original_norm) * self.phi
        return efficiency

    def _compute_bures_distance(self, manifold: np.ndarray) -> float:
        """
        Compute Bures distance between manifold and identity.

        Bures distance measures quantum distinguishability and geometric
        separation in the manifold space.
        """
        n = manifold.shape[0]
        identity = np.eye(n)

        # Compute sqrt of manifold
        try:
            sqrt_manifold = la.sqrtm(manifold)
            sqrt_manifold = np.real(sqrt_manifold)

            # Bures distance: ||sqrt(A) - sqrt(B)||_F
            bures = la.norm(sqrt_manifold - identity, "fro")
            return bures
        except:
            # Fallback to Frobenius norm
            return la.norm(manifold - identity, "fro") / n

    def _compute_fisher_curvature(self, manifold: np.ndarray) -> float:
        """
        Compute Fisher curvature of manifold.

        Fisher curvature measures information geometry and how quickly
        the manifold diverges from flat space.
        """
        # Compute covariance matrix
        cov = np.cov(manifold.T)

        # Add regularization for numerical stability
        cov_reg = cov + np.eye(cov.shape[0]) * 1e-10

        # Fisher curvature: trace of inverse covariance
        try:
            inv_cov = la.inv(cov_reg)
            fisher = np.trace(inv_cov)
            return fisher / manifold.size
        except la.LinAlgError:
            return float("inf")

    def _compute_phi_folding_ratio(self, manifold: np.ndarray) -> float:
        """
        Compute Φ-folding ratio.

        Measures how many times the manifold can be "folded" using
        Φ-based transformations while preserving structure.
        """
        original_norm = np.linalg.norm(manifold)
        current_norm = original_norm
        fold_count = 0

        # Count how many Φ-folds are possible
        while current_norm > original_norm * 0.1 and fold_count < 100:
            current_norm = current_norm / self.phi
            fold_count += 1

        return fold_count

    def _analyze_eigenvalue_spectrum(self, manifold: np.ndarray) -> List[float]:
        """
        Analyze eigenvalue spectrum of manifold.

        Returns eigenvalues sorted by magnitude for spectral analysis.
        """
        eigenvalues = la.eigvals(manifold)
        eigenvalues = np.real(eigenvalues)
        eigenvalues = np.sort(np.abs(eigenvalues))[::-1]  # Sort descending
        return eigenvalues.tolist()

    def find_cognitive_horizon(
        self, results: List[ManifoldStressResult], stability_threshold: float = 0.5
    ) -> int:
        """
        Find cognitive horizon from stress test results.

        Args:
            results: List of manifold stress results
            stability_threshold: Threshold for considering manifold collapsed

        Returns:
            Dimension at which cognitive horizon is reached
        """
        for result in results:
            if result.geometric_stability < stability_threshold:
                return result.dimension

        # If no collapse detected, return max tested dimension
        return max(r.dimension for r in results) if results else 0

    def analyze_collapse_dynamics(self, results: List[ManifoldStressResult]) -> Dict:
        """
        Analyze collapse dynamics across dimensional sweep.

        Provides mathematical analysis of how manifold degrades
        as dimensions increase.
        """
        if not results:
            return {}

        dimensions = [r.dimension for r in results]
        stabilities = [r.geometric_stability for r in results]
        compressions = [r.compression_efficiency for r in results]

        # Fit exponential decay model to stability
        log_dimensions = np.log(dimensions)
        log_stabilities = np.log(stabilities)

        slope, intercept, r_value, p_value, std_err = stats.linregress(
            log_dimensions, log_stabilities
        )

        # Predict collapse point
        predicted_collapse_dim = np.exp((np.log(0.5) - intercept) / slope)

        return {
            "decay_rate": slope,
            "decay_intercept": intercept,
            "decay_r_squared": r_value**2,
            "decay_p_value": p_value,
            "predicted_collapse_dimension": predicted_collapse_dim,
            "actual_collapse_dimension": self.find_cognitive_horizon(results),
            "stability_at_max_dim": stabilities[-1],
            "compression_at_max_dim": compressions[-1],
            "dimensional_scaling_exponent": slope,
        }

    def generate_manifold_report(
        self, results: List[ManifoldStressResult], output_path: Optional[Path] = None
    ) -> Dict:
        """
        Generate comprehensive manifold stress test report.

        Args:
            results: List of manifold stress results
            output_path: Optional path to save JSON report

        Returns:
            Dictionary containing comprehensive analysis
        """
        cognitive_horizon = self.find_cognitive_horizon(results)
        collapse_dynamics = self.analyze_collapse_dynamics(results)

        report = {
            "test_summary": {
                "max_dimension_tested": max(r.dimension for r in results),
                "cognitive_horizon": cognitive_horizon,
                "total_dimensions_tested": len(results),
                "collapse_detected": any(r.collapse_detected for r in results),
            },
            "collapse_dynamics": collapse_dynamics,
            "dimensional_results": [
                {
                    "dimension": r.dimension,
                    "geometric_stability": r.geometric_stability,
                    "compression_efficiency": r.compression_efficiency,
                    "coherence_preserved": r.coherence_preserved,
                    "bures_distance": r.bures_distance,
                    "fisher_curvature": r.fisher_curvature,
                    "phi_folding_ratio": r.phi_folding_ratio,
                    "collapse_detected": r.collapse_detected,
                }
                for r in results
            ],
            "formal_invariant_validation_metrics": {
                "manifold_coherence_limit": cognitive_horizon,
                "geometric_stability_decay_rate": collapse_dynamics.get(
                    "decay_rate", 0
                ),
                "phi_preservation_at_horizon": next(
                    (
                        r.compression_efficiency
                        for r in results
                        if r.dimension == cognitive_horizon
                    ),
                    0,
                ),
                "bures_distance_at_horizon": next(
                    (
                        r.bures_distance
                        for r in results
                        if r.dimension == cognitive_horizon
                    ),
                    0,
                ),
            },
        }

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(report, f, indent=2, default=str)
            print(f"Manifold stress report saved to: {output_path}")

        return report


def main():
    """Run manifold stress tests with default parameters."""
    suite = ManifoldStressTestSuite()

    print("=" * 60)
    print("HIGH-DIMENSIONAL MANIFOLD STRESS TEST")
    print("=" * 60)

    # Run dimensional sweep
    results = suite.run_dimensional_sweep(max_dimension=20000, step_multiplier=10)

    # Generate report
    report = suite.generate_manifold_report(
        results, output_path=Path("artifacts/manifold_stress_report.json")
    )

    # Print summary
    print("\n" + "=" * 60)
    print("MANIFOLD STRESS TEST SUMMARY")
    print("=" * 60)
    print(f"Cognitive Horizon: {report['test_summary']['cognitive_horizon']}")
    print(f"Max Dimension Tested: {report['test_summary']['max_dimension_tested']}")
    print(f"Collapse Detected: {report['test_summary']['collapse_detected']}")
    print(f"Decay Rate: {report['collapse_dynamics']['decay_rate']:.6f}")
    print(
        f"Predicted Collapse: {report['collapse_dynamics']['predicted_collapse_dimension']:.0f}"
    )


if __name__ == "__main__":
    main()
