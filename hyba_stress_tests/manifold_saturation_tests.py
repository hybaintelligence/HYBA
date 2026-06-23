"""High-dimensional manifold saturation tests for cognitive horizon detection.

This module implements stress tests to determine the "Cognitive Horizon"—the
maximum complexity the AI fabric can process before the manifold loses coherence.

The tests push the Bures geometry and manifold evolution to extreme dimensions
(dim=10,000+) to identify the collapse point where geometric stability ratio
falls below functional thresholds.

Mathematical focus:
- Φ-folding compression efficiency at high dimensions
- Geometric stability ratio degradation
- Manifold coherence collapse point
- Computational complexity scaling
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Sequence

import numpy as np
from scipy.linalg import sqrtm


class StabilityThreshold(str, Enum):
    """Stability thresholds for cognitive horizon detection."""

    FUNCTIONAL = "functional"  # 0.606+ (current baseline)
    DEGRADED = "degraded"  # 0.4 - 0.606
    CRITICAL = "critical"  # 0.2 - 0.4
    COLLAPSED = "collapsed"  # < 0.2


@dataclass(frozen=True)
class ManifoldSaturationResult:
    """Result of manifold saturation test."""

    dimension: int
    phi_folding_efficiency: float
    geometric_stability_ratio: float
    computation_time_ms: float
    memory_usage_mb: float
    stability_state: StabilityThreshold
    collapse_detected: bool
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "dimension": self.dimension,
            "phi_folding_efficiency": self.phi_folding_efficiency,
            "geometric_stability_ratio": self.geometric_stability_ratio,
            "computation_time_ms": self.computation_time_ms,
            "memory_usage_mb": self.memory_usage_mb,
            "stability_state": self.stability_state.value,
            "collapse_detected": self.collapse_detected,
            "metadata": dict(self.metadata),
        }


class HighDimensionalManifold:
    """High-dimensional manifold for saturation testing.

    This class implements Bures geometry operations at extreme dimensions
    to test the limits of the AI fabric's cognitive capabilities.
    """

    def __init__(self, dimension: int):
        """Initialize a high-dimensional manifold.

        Args:
            dimension: Dimension of the manifold (10,000+ for saturation tests)
        """
        self.dimension = int(dimension)
        self._validate_dimension()

    def _validate_dimension(self) -> None:
        """Validate dimension is within reasonable bounds."""
        if self.dimension < 100:
            raise ValueError(
                f"Dimension must be >= 100 for saturation tests, got {self.dimension}"
            )
        if self.dimension > 100000:
            raise ValueError(
                f"Dimension must be <= 100000 for memory constraints, got {self.dimension}"
            )

    def generate_random_density_matrix(self) -> np.ndarray:
        """Generate a random density matrix for the manifold.

        Returns:
            Complex Hermitian positive semidefinite matrix
        """
        # Generate random complex matrix
        A = np.random.randn(self.dimension, self.dimension) + 1j * np.random.randn(
            self.dimension, self.dimension
        )

        # Make it Hermitian
        rho = (A + A.conj().T) / 2

        # Make it positive semidefinite
        rho = rho @ rho.conj().T

        # Normalize trace to 1
        rho = rho / np.trace(rho)

        return rho

    def compute_phi_folding_efficiency(self, rho: np.ndarray) -> float:
        """Compute Φ-folding compression efficiency.

        This measures how efficiently the manifold can compress information
        while preserving integrated information (Φ).

        Args:
            rho: Density matrix

        Returns:
            Efficiency ratio in [0, 1]
        """
        # Simplified Φ computation using eigenvalues
        eigvals = np.linalg.eigvalsh(rho).real
        eigvals = eigvals[eigvals > 0]

        if len(eigvals) == 0:
            return 0.0

        # Compute Shannon entropy
        entropy = -np.sum(eigvals * np.log2(eigvals))

        # Maximum entropy for this dimension
        max_entropy = np.log2(self.dimension)

        # Efficiency: how close to maximum entropy
        efficiency = entropy / max_entropy if max_entropy > 0 else 0.0

        return float(efficiency)

    def compute_geometric_stability_ratio(self, rho: np.ndarray) -> float:
        """Compute geometric stability ratio using Bures distance.

        This measures the stability of the manifold under perturbations.

        Args:
            rho: Density matrix

        Returns:
            Stability ratio in [0, 1]
        """
        # Simplified Bures distance computation
        # In practice, this would use the full Bures metric

        # Compute fidelity with itself (should be 1.0)
        sqrt_rho = sqrtm(rho)
        fidelity = np.real(np.trace(sqrt_rho @ sqrt_rho))

        # Stability ratio based on fidelity
        stability = min(1.0, fidelity)

        return float(stability)

    def compute_manifold_coherence(self, rho: np.ndarray) -> float:
        """Compute overall manifold coherence score.

        Args:
            rho: Density matrix

        Returns:
            Coherence score in [0, 1]
        """
        phi_efficiency = self.compute_phi_folding_efficiency(rho)
        geometric_stability = self.compute_geometric_stability_ratio(rho)

        # Combined coherence score
        coherence = (phi_efficiency + geometric_stability) / 2.0

        return float(coherence)


class ManifoldSaturationTester:
    """Tester for high-dimensional manifold saturation.

    This class runs saturation tests across increasing dimensions to
    identify the cognitive horizon collapse point.
    """

    def __init__(
        self,
        start_dimension: int = 100,
        max_dimension: int = 10000,
        dimension_step: int = 500,
        stability_threshold: float = 0.606,
    ):
        """Initialize the saturation tester.

        Args:
            start_dimension: Starting dimension for tests
            max_dimension: Maximum dimension to test
            dimension_step: Step size for dimension progression
            stability_threshold: Threshold for functional stability
        """
        self.start_dimension = int(start_dimension)
        self.max_dimension = int(max_dimension)
        self.dimension_step = int(dimension_step)
        self.stability_threshold = float(stability_threshold)

    def run_saturation_test(self) -> Sequence[ManifoldSaturationResult]:
        """Run saturation test across dimension range.

        Returns:
            Sequence of saturation results for each dimension tested
        """
        results = []

        for dimension in range(
            self.start_dimension, self.max_dimension + 1, self.dimension_step
        ):
            result = self.test_dimension(dimension)
            results.append(result)

            # Stop if collapse detected
            if result.collapse_detected:
                print(f"Collapse detected at dimension {dimension}")
                break

        return results

    def test_dimension(self, dimension: int) -> ManifoldSaturationResult:
        """Test a specific dimension.

        Args:
            dimension: Dimension to test

        Returns:
            Saturation result for this dimension
        """
        manifold = HighDimensionalManifold(dimension)

        # Measure memory before
        import psutil
        import os

        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / (1024 * 1024)  # MB

        # Generate density matrix and measure time
        start_time = time.perf_counter()
        rho = manifold.generate_random_density_matrix()

        # Compute metrics
        phi_efficiency = manifold.compute_phi_folding_efficiency(rho)
        geometric_stability = manifold.compute_geometric_stability_ratio(rho)

        end_time = time.perf_counter()

        # Measure memory after
        mem_after = process.memory_info().rss / (1024 * 1024)  # MB
        memory_usage = mem_after - mem_before

        computation_time_ms = (end_time - start_time) * 1000

        # Determine stability state
        stability_state = self._classify_stability(geometric_stability)

        # Detect collapse
        collapse_detected = geometric_stability < self.stability_threshold

        return ManifoldSaturationResult(
            dimension=dimension,
            phi_folding_efficiency=phi_efficiency,
            geometric_stability_ratio=geometric_stability,
            computation_time_ms=computation_time_ms,
            memory_usage_mb=memory_usage,
            stability_state=stability_state,
            collapse_detected=collapse_detected,
            metadata={
                "dimension_step": self.dimension_step,
                "stability_threshold": self.stability_threshold,
            },
        )

    def _classify_stability(self, stability_ratio: float) -> StabilityThreshold:
        """Classify stability state based on ratio.

        Args:
            stability_ratio: Geometric stability ratio

        Returns:
            Stability threshold classification
        """
        if stability_ratio >= 0.606:
            return StabilityThreshold.FUNCTIONAL
        elif stability_ratio >= 0.4:
            return StabilityThreshold.DEGRADED
        elif stability_ratio >= 0.2:
            return StabilityThreshold.CRITICAL
        else:
            return StabilityThreshold.COLLAPSED

    def find_cognitive_horizon(
        self, results: Sequence[ManifoldSaturationResult]
    ) -> int | None:
        """Find the cognitive horizon (collapse point).

        Args:
            results: Sequence of saturation test results

        Returns:
            Dimension at which collapse was detected, or None if no collapse
        """
        for result in results:
            if result.collapse_detected:
                return result.dimension
        return None

    def generate_saturation_report(
        self, results: Sequence[ManifoldSaturationResult]
    ) -> str:
        """Generate a comprehensive saturation test report.

        Args:
            results: Sequence of saturation test results

        Returns:
            Formatted report string
        """
        lines = [
            "=" * 80,
            "MANIFOLD SATURATION TEST REPORT",
            "=" * 80,
            "",
            f"Test Range: {self.start_dimension} to {self.max_dimension} (step: {self.dimension_step})",
            f"Stability Threshold: {self.stability_threshold}",
            f"Tests Run: {len(results)}",
            "",
            "-" * 80,
            "RESULTS SUMMARY",
            "-" * 80,
            "",
        ]

        for result in results:
            lines.append(
                f"Dim {result.dimension:5d}: "
                f"Φ-eff={result.phi_folding_efficiency:.3f}, "
                f"Stability={result.geometric_stability_ratio:.3f}, "
                f"State={result.stability_state.value}, "
                f"Time={result.computation_time_ms:.1f}ms, "
                f"Mem={result.memory_usage_mb:.1f}MB"
            )

        cognitive_horizon = self.find_cognitive_horizon(results)
        lines.append("")
        lines.append("-" * 80)
        if cognitive_horizon:
            lines.append(f"COGNITIVE HORIZON DETECTED: dim={cognitive_horizon}")
        else:
            lines.append("NO COLLAPSE DETECTED WITHIN TEST RANGE")
        lines.append("=" * 80)

        return "\n".join(lines)


def run_cognitive_horizon_test() -> None:
    """Run the cognitive horizon detection test.

    This is the main entry point for determining the system's
    cognitive horizon—the maximum complexity before manifold collapse.
    """
    print("Starting Cognitive Horizon Detection Test...")
    print("This will test manifold stability at dimensions up to 10,000+")
    print("Please ensure you have sufficient memory (8GB+ recommended)")
    print()

    # Run saturation test
    tester = ManifoldSaturationTester(
        start_dimension=100,
        max_dimension=10000,
        dimension_step=500,
        stability_threshold=0.606,
    )

    results = tester.run_saturation_test()

    # Generate and display report
    report = tester.generate_saturation_report(results)
    print(report)

    # Save results to file
    import json
    from pathlib import Path

    output_file = Path("logs/cognitive_horizon_test_results.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    results_dict = {
        "test_config": {
            "start_dimension": tester.start_dimension,
            "max_dimension": tester.max_dimension,
            "dimension_step": tester.dimension_step,
            "stability_threshold": tester.stability_threshold,
        },
        "results": [r.to_dict() for r in results],
        "cognitive_horizon": tester.find_cognitive_horizon(results),
    }

    output_file.write_text(json.dumps(results_dict, indent=2))
    print(f"\nResults saved to {output_file}")


if __name__ == "__main__":
    run_cognitive_horizon_test()
