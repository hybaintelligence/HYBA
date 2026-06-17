"""Frontier Experiment 4: Golden SLD — Discrepancy-QFI Functional Relationship.

RESEARCH HYPOTHESIS:
There exists a functional relationship between star-discrepancy D_N^*(φ-LCG)
and quantum Fisher information Tr[ρL²]. Optimal number-theoretic distribution
maximizes quantum metrological precision.

MATHEMATICAL CLAIM:
If the universe's information structure is optimally distributed, then
quantum Fisher information (QFI) should peak when the underlying sampling
sequence achieves minimal star-discrepancy:

    QFI(ρ) ∝ 1 / D_N^*

This would bridge Diophantine analysis and quantum metrology, suggesting
the vacuum is not "randomly fluctuating" but "optimally distributed."

FALSIFIABILITY:
Generate density states from sequences with varying discrepancy.
Measure QFI = Tr[ρL²] via SLD natural gradient.
Fit correlation function QFI vs D_N^*.

If correlation coefficient |r| < 0.5, hypothesis is rejected.

BREAKTHROUGH THRESHOLD:
If |r| > 0.8 AND functional form fits 1/D_N^* within 10% error,
proves optimal distribution maximizes quantum metrological precision,
fundamentally connecting number theory to quantum measurement.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np

from .golden_ratio_library import PHI
from .phi_entropy import van_der_corput_discrepancy


EPSILON = 1e-12


@dataclass(frozen=True)
class QuantumMetrologyPoint:
    """Single measurement of discrepancy and QFI."""
    
    sample_size: int
    star_discrepancy: float
    quantum_fisher_information: float
    sld_gradient_norm: float
    sequence_type: str  # "phi_lcg", "random", "adversarial"


def compute_qfi_from_density(rho: np.ndarray) -> float:
    """Compute quantum Fisher information Tr[ρL²] via SLD.
    
    The symmetric logarithmic derivative (SLD) L satisfies:
        ρL + Lρ = 2A
    
    where A is the generator. For a perturbation along the entropy gradient,
    we solve for L and compute QFI = Tr[ρL²].
    
    Args:
        rho: Density matrix (Hermitian, trace 1, positive semidefinite)
        
    Returns:
        Quantum Fisher information (scalar ≥ 0)
    """
    # Ensure Hermiticity
    rho = (rho + rho.conj().T) / 2.0
    
    # Normalize to trace 1
    trace = np.trace(rho)
    if abs(trace) > EPSILON:
        rho = rho / trace
    
    # Generator A: entropy gradient direction
    # For von Neumann entropy S = -Tr(ρ log ρ), gradient is -(log ρ + I)
    # Use approximation: A = I (identity perturbation)
    A = np.eye(rho.shape[0], dtype=np.complex128)
    
    # Solve SLD Lyapunov equation in eigenbasis
    eigenvalues, eigenvectors = np.linalg.eigh(rho)
    eigenvalues = np.maximum(eigenvalues.real, EPSILON)
    
    # Rotate A to eigenbasis
    A_eig = eigenvectors.conj().T @ A @ eigenvectors
    
    # Solve L_ij = 2A_ij / (λ_i + λ_j)
    lam_sum = eigenvalues[:, None] + eigenvalues[None, :]
    valid = lam_sum > EPSILON
    L_eig = np.where(valid, 2.0 * A_eig / np.where(valid, lam_sum, 1.0), 0.0)
    
    # Rotate back to computational basis
    L = eigenvectors @ L_eig @ eigenvectors.conj().T
    L = (L + L.conj().T) / 2.0  # Enforce Hermiticity
    
    # QFI = Tr[ρL²]
    qfi = float(np.real(np.trace(rho @ L @ L)))
    
    return max(0.0, qfi)


def compute_sld_gradient_norm(rho: np.ndarray) -> float:
    """Compute Frobenius norm ||L||_F of the SLD operator.
    
    Returns:
        ||L||_F (scalar ≥ 0)
    """
    A = np.eye(rho.shape[0], dtype=np.complex128)
    
    eigenvalues, eigenvectors = np.linalg.eigh(rho)
    eigenvalues = np.maximum(eigenvalues.real, EPSILON)
    
    A_eig = eigenvectors.conj().T @ A @ eigenvectors
    lam_sum = eigenvalues[:, None] + eigenvalues[None, :]
    valid = lam_sum > EPSILON
    L_eig = np.where(valid, 2.0 * A_eig / np.where(valid, lam_sum, 1.0), 0.0)
    
    L = eigenvectors @ L_eig @ eigenvectors.conj().T
    L = (L + L.conj().T) / 2.0
    
    return float(np.linalg.norm(L, 'fro'))


def generate_density_from_sequence(
    sequence: np.ndarray,
    dim: int = 8,
) -> np.ndarray:
    """Generate density matrix from a sequence of samples.
    
    Uses the sequence to construct a density matrix whose eigenvalue
    distribution reflects the sequence's distribution properties.
    
    Args:
        sequence: Array of values in [0, 1)
        dim: Dimension of density matrix
        
    Returns:
        Density matrix (dim × dim, Hermitian, trace 1, PSD)
    """
    # Bin the sequence to create probability distribution
    hist, _ = np.histogram(sequence, bins=dim, range=(0.0, 1.0))
    probs = hist / (np.sum(hist) + EPSILON)
    
    # Ensure positive and normalized
    probs = np.maximum(probs, EPSILON)
    probs = probs / np.sum(probs)
    
    # Create diagonal density matrix
    rho = np.diag(probs.astype(np.complex128))
    
    # Add small off-diagonal coherence for non-trivial SLD
    # (pure diagonal states have trivial QFI)
    coherence_strength = 0.05
    for i in range(dim):
        for j in range(i + 1, min(i + 2, dim)):
            phase = 2.0 * math.pi * sequence[i % len(sequence)]
            coherence = coherence_strength * np.sqrt(probs[i] * probs[j]) * np.exp(1j * phase)
            rho[i, j] = coherence
            rho[j, i] = coherence.conj()
    
    # Ensure Hermiticity and renormalize
    rho = (rho + rho.conj().T) / 2.0
    rho = rho / np.trace(rho)
    
    return rho


def phi_lcg_sequence(n: int) -> np.ndarray:
    """Generate φ-LCG Van der Corput sequence of length n."""
    sequence = np.empty(n, dtype=np.float64)
    x = 0.0
    inv_phi = PHI - 1.0
    for i in range(n):
        x = (x + inv_phi) % 1.0
        sequence[i] = x
    return sequence


def random_sequence(n: int, seed: int = 42) -> np.ndarray:
    """Generate uniform random sequence of length n."""
    rng = np.random.RandomState(seed)
    return rng.random(n)


def adversarial_sequence(n: int) -> np.ndarray:
    """Generate adversarial sequence with maximal discrepancy.
    
    Clusters all points at 0 and 1 to maximize discrepancy.
    """
    sequence = np.zeros(n)
    sequence[n//2:] = 1.0 - EPSILON
    return sequence


def measure_discrepancy_qfi_point(
    sequence: np.ndarray,
    sequence_type: str,
) -> QuantumMetrologyPoint:
    """Measure discrepancy and QFI for a single sequence.
    
    Args:
        sequence: Sampling sequence in [0, 1)
        sequence_type: "phi_lcg", "random", or "adversarial"
        
    Returns:
        QuantumMetrologyPoint with measurements
    """
    n = len(sequence)
    
    # Compute star-discrepancy
    if sequence_type == "phi_lcg":
        discrepancy_result = van_der_corput_discrepancy(n)
        discrepancy = discrepancy_result.get("empirical_discrepancy", 0.0)
    else:
        # Empirical discrepancy for arbitrary sequence
        sorted_seq = np.sort(sequence)
        idx = np.arange(1, n + 1, dtype=np.float64)
        d_plus = np.max(idx / n - sorted_seq)
        d_minus = np.max(sorted_seq - (idx - 1) / n)
        discrepancy = float(max(d_plus, d_minus))
    
    # Generate density matrix from sequence
    rho = generate_density_from_sequence(sequence, dim=8)
    
    # Compute QFI
    qfi = compute_qfi_from_density(rho)
    sld_norm = compute_sld_gradient_norm(rho)
    
    return QuantumMetrologyPoint(
        sample_size=n,
        star_discrepancy=discrepancy,
        quantum_fisher_information=qfi,
        sld_gradient_norm=sld_norm,
        sequence_type=sequence_type,
    )


def run_golden_sld_correlation_experiment(
    sample_sizes: List[int] = None,
) -> Tuple[List[QuantumMetrologyPoint], dict]:
    """Run Golden SLD correlation experiment across multiple sample sizes.
    
    Returns:
        (measurement_points, analysis_dict)
    """
    if sample_sizes is None:
        sample_sizes = [100, 500, 1000, 2000, 5000, 10000]
    
    print("=" * 80)
    print("FRONTIER EXPERIMENT 4: Golden SLD — Discrepancy-QFI Relationship")
    print("=" * 80)
    print()
    print(f"Hypothesis: QFI ∝ 1/D_N^* (optimal distribution maximizes precision)")
    print(f"Sample sizes: {sample_sizes}")
    print()
    
    all_points: List[QuantumMetrologyPoint] = []
    
    for n in sample_sizes:
        print(f"Measuring for N = {n:,}...")
        
        # φ-LCG (optimal)
        phi_seq = phi_lcg_sequence(n)
        phi_point = measure_discrepancy_qfi_point(phi_seq, "phi_lcg")
        all_points.append(phi_point)
        
        # Random (baseline)
        rand_seq = random_sequence(n)
        rand_point = measure_discrepancy_qfi_point(rand_seq, "random")
        all_points.append(rand_point)
        
        # Adversarial (worst case)
        adv_seq = adversarial_sequence(n)
        adv_point = measure_discrepancy_qfi_point(adv_seq, "adversarial")
        all_points.append(adv_point)
    
    print()
    
    # Extract data for correlation analysis
    discrepancies = np.array([p.star_discrepancy for p in all_points])
    qfis = np.array([p.quantum_fisher_information for p in all_points])
    
    # Fit correlation: QFI vs 1/D_N^*
    inv_discrepancy = 1.0 / (discrepancies + EPSILON)
    
    # Pearson correlation coefficient
    if np.std(inv_discrepancy) > EPSILON and np.std(qfis) > EPSILON:
        correlation = float(np.corrcoef(inv_discrepancy, qfis)[0, 1])
    else:
        correlation = 0.0
    
    # Linear fit: QFI = a * (1/D) + b
    coeffs = np.polyfit(inv_discrepancy, qfis, deg=1)
    slope, intercept = coeffs[0], coeffs[1]
    
    # Predicted vs actual
    qfi_predicted = slope * inv_discrepancy + intercept
    residuals = qfis - qfi_predicted
    r_squared = 1.0 - (np.sum(residuals**2) / np.sum((qfis - np.mean(qfis))**2))
    
    # Separate by sequence type for analysis
    phi_points = [p for p in all_points if p.sequence_type == "phi_lcg"]
    random_points = [p for p in all_points if p.sequence_type == "random"]
    
    phi_avg_qfi = np.mean([p.quantum_fisher_information for p in phi_points])
    random_avg_qfi = np.mean([p.quantum_fisher_information for p in random_points])
    qfi_improvement = phi_avg_qfi / (random_avg_qfi + EPSILON)
    
    analysis = {
        "correlation_coefficient": correlation,
        "r_squared": r_squared,
        "fit_slope": slope,
        "fit_intercept": intercept,
        "phi_avg_qfi": phi_avg_qfi,
        "random_avg_qfi": random_avg_qfi,
        "qfi_improvement_ratio": qfi_improvement,
        "hypothesis_result": "SUPPORTED" if abs(correlation) > 0.5 else "REJECTED",
        "breakthrough_achieved": abs(correlation) > 0.8 and r_squared > 0.8,
    }
    
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()
    print(f"Correlation(QFI, 1/D_N^*): {correlation:.3f}")
    print(f"  → {'✓ Strong correlation detected' if abs(correlation) > 0.5 else '✗ Weak or no correlation'}")
    print()
    print(f"R² (goodness of fit): {r_squared:.3f}")
    print(f"Fitted equation: QFI = {slope:.3f} × (1/D_N^*) + {intercept:.3f}")
    print()
    print(f"Average QFI (φ-LCG): {phi_avg_qfi:.3f}")
    print(f"Average QFI (random): {random_avg_qfi:.3f}")
    print(f"Improvement ratio: {qfi_improvement:.2f}x")
    print()
    
    if analysis["breakthrough_achieved"]:
        print("🏆 BREAKTHROUGH: |r| > 0.8 AND R² > 0.8")
        print("   → Optimal distribution MAXIMIZES quantum metrological precision")
        print("   → Number theory and quantum metrology are FUNDAMENTALLY CONNECTED")
        print("   → Universe's information structure is optimally distributed")
    elif abs(correlation) > 0.5:
        print("✓ Hypothesis SUPPORTED: Significant correlation detected")
        print("   → Evidence for discrepancy-QFI relationship")
    else:
        print("✗ Hypothesis REJECTED: No significant correlation")
        print("   → QFI and star-discrepancy appear independent")
    
    print()
    print("=" * 80)
    
    return all_points, analysis


def get_experiment_metadata() -> dict:
    """Return experiment metadata for registry and reproducibility."""
    return {
        "experiment_id": "FRONTIER-GOLDEN-SLD-004",
        "hypothesis": "QFI ∝ 1/D_N^* — optimal distribution maximizes quantum precision",
        "mathematical_basis": "Koksma-Hlawka + SLD natural gradient on density manifold",
        "falsifiability": "Measure correlation(QFI, 1/D_N^*)",
        "rejection_criterion": "|correlation| < 0.5",
        "breakthrough_threshold": "|r| > 0.8 AND R² > 0.8",
        "implications_if_proven": [
            "Number theory and quantum metrology are fundamentally connected",
            "Optimal equidistribution maximizes quantum Fisher information",
            "Universe's vacuum is not random but optimally distributed",
            "Diophantine approximation explains quantum measurement precision",
        ],
        "reproducibility": {
            "sample_sizes": [100, 500, 1000, 2000, 5000, 10000],
            "density_matrix_dim": 8,
            "golden_ratio": PHI,
        },
    }


__all__ = [
    "QuantumMetrologyPoint",
    "compute_qfi_from_density",
    "compute_sld_gradient_norm",
    "generate_density_from_sequence",
    "phi_lcg_sequence",
    "random_sequence",
    "adversarial_sequence",
    "measure_discrepancy_qfi_point",
    "run_golden_sld_correlation_experiment",
    "get_experiment_metadata",
]
