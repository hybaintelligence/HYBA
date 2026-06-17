"""
Frontier Experiment 4: Golden SLD — Discrepancy-QFI Functional Relationship

HYPOTHESIS:
There exists a functional relationship between star-discrepancy D_N^*(φ-LCG)
and quantum Fisher information Tr[ρL²]. Optimal number-theoretic distribution
maximizes quantum metrological precision.

MATHEMATICAL CLAIM:
If the universe's information structure is optimally distributed, then quantum
Fisher information (QFI) should peak when the underlying sampling sequence
achieves minimal star-discrepancy:

    QFI(ρ) ∝ 1 / D_N^*

This would bridge Diophantine analysis and quantum metrology.

METHOD:
1. Generate sequences: φ-LCG (optimal), random (baseline), adversarial (worst)
2. Create density matrices from sequence distributions
3. Compute QFI via SLD Lyapunov equation: ρL + Lρ = 2A, QFI = Tr[ρL²]
4. Compute star-discrepancy D_N^* for each sequence
5. Fit correlation: QFI vs 1/D_N^*
6. Measure Pearson correlation coefficient and R²

FALSIFIABILITY:
Rejection criterion: |correlation| < 0.5
Breakthrough threshold: |r| > 0.8 AND R² > 0.8

IMPLICATIONS IF PROVEN:
- Number theory and quantum metrology are fundamentally connected
- Optimal equidistribution maximizes quantum Fisher information
- Universe's vacuum is not random but optimally distributed
- Diophantine approximation explains quantum measurement precision
"""

import numpy as np
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
import time


@dataclass
class DiscrepancyQFIPoint:
    """A single data point correlating star-discrepancy with QFI"""
    sequence_type: str
    sample_size: int
    star_discrepancy: float
    qfi: float
    discrepancy_inverse: float


@dataclass
class GoldenSLDAnalysis:
    """Complete analysis of discrepancy-QFI correlation"""
    pearson_r: float
    r_squared: float
    breakthrough_achieved: bool
    points: List[DiscrepancyQFIPoint]
    optimal_qfi: float
    worst_qfi: float
    qfi_improvement_ratio: float
    execution_time_ms: float


class GoldenSLDExperiment:
    """
    Test functional relationship QFI ∝ 1/D_N^* by generating density matrices
    from optimal, random, and adversarial sequences and measuring quantum
    Fisher information via SLD Lyapunov equation.
    """

    def __init__(self, dim: int = 4):
        """
        Args:
            dim: Dimension of density matrix (state space size)
        """
        self.dim = dim
        self.phi = (1.0 + np.sqrt(5.0)) / 2.0
        self.phi_inv = self.phi - 1.0

    def generate_phi_lcg_sequence(self, n: int, seed: float = 0.0) -> np.ndarray:
        """Generate Van der Corput φ-LCG sequence with optimal discrepancy"""
        sequence = np.zeros(n)
        x = seed
        for i in range(n):
            x = (x + self.phi_inv) % 1.0
            sequence[i] = x
        return sequence

    def generate_random_sequence(self, n: int, seed: int = 42) -> np.ndarray:
        """Generate pseudo-random sequence (baseline)"""
        rng = np.random.RandomState(seed)
        return rng.uniform(0, 1, n)

    def generate_adversarial_sequence(self, n: int) -> np.ndarray:
        """Generate adversarially distributed sequence (worst-case)"""
        # Cluster points in narrow bands to maximize discrepancy
        sequence = np.zeros(n)
        num_clusters = int(np.sqrt(n))
        cluster_width = 0.05
        for i in range(n):
            cluster_idx = i % num_clusters
            cluster_center = cluster_idx / num_clusters
            offset = (i // num_clusters) * cluster_width / n
            sequence[i] = (cluster_center + offset) % 1.0
        return sequence

    def compute_star_discrepancy(self, sequence: np.ndarray) -> float:
        """
        Compute star-discrepancy D_N^* = sup_α |F_N(α) - α|
        where F_N(α) = #{x_i ≤ α} / N
        """
        n = len(sequence)
        sorted_seq = np.sort(sequence)
        
        # Compute empirical CDF at each point
        discrepancies = []
        for i, x in enumerate(sorted_seq):
            empirical_cdf = (i + 1) / n
            theoretical_cdf = x
            discrepancies.append(abs(empirical_cdf - theoretical_cdf))
        
        # Also check at boundaries
        discrepancies.append(abs(0 - sorted_seq[0]))
        discrepancies.append(abs(1 - sorted_seq[-1]))
        
        return max(discrepancies)

    def sequence_to_density_matrix(self, sequence: np.ndarray) -> np.ndarray:
        """
        Convert sequence to density matrix by binning into probability
        distribution with numerically stable construction.
        """
        # Bin sequence into dim bins for diagonal elements
        hist, _ = np.histogram(sequence, bins=self.dim, range=(0, 1))
        
        # Normalize to probability distribution with regularization
        prob_dist = (hist + 1.0) / (len(sequence) + self.dim)  # Laplace smoothing
        prob_dist = prob_dist / np.sum(prob_dist)  # Renormalize
        
        # Construct density matrix - start with diagonal
        rho = np.diag(prob_dist)
        
        # Add small coherences based on sequence properties
        # Use sorted sequence gaps to induce structure
        sorted_seq = np.sort(sequence)
        gaps = np.diff(sorted_seq)
        mean_gap = np.mean(gaps) if len(gaps) > 0 else 0.1
        
        for i in range(self.dim):
            for j in range(i + 1, self.dim):
                # Add small coherence proportional to diagonal product
                # Scale by mean gap (optimal distribution has uniform gaps)
                coherence_strength = 0.05 * mean_gap
                coherence = coherence_strength * np.sqrt(rho[i, i] * rho[j, j])
                rho[i, j] = coherence
                rho[j, i] = coherence  # Real-valued for simplicity
        
        # Ensure Hermitian
        rho = 0.5 * (rho + rho.T)
        
        # Ensure positive semi-definite via eigenvalue clipping
        eigvals, eigvecs = np.linalg.eigh(rho)
        eigvals = np.maximum(eigvals, 1e-12)  # Regularize
        eigvals = eigvals / np.sum(eigvals)  # Normalize
        rho = eigvecs @ np.diag(eigvals) @ eigvecs.T
        
        # Final trace normalization
        rho = rho / np.trace(rho)
        
        return rho

    def compute_qfi_via_sld(self, rho: np.ndarray) -> float:
        """
        Compute quantum Fisher information via SLD Lyapunov equation.
        
        For observable A, solve ρL + Lρ = 2A for SLD operator L.
        In eigenbasis: L_ij = 2A_ij / (λ_i + λ_j)
        QFI = Tr[ρL²]
        """
        # Use identity as observable (measuring "which state")
        A = np.eye(self.dim)
        
        # Eigendecomposition of density matrix
        eigvals, eigvecs = np.linalg.eigh(rho)
        eigvals = np.maximum(eigvals, 1e-12)  # Regularization
        
        # Transform A to eigenbasis
        A_eigen = eigvecs.conj().T @ A @ eigvecs
        
        # Solve for L in eigenbasis: L_ij = 2A_ij / (λ_i + λ_j)
        L_eigen = np.zeros_like(A_eigen, dtype=complex)
        for i in range(self.dim):
            for j in range(self.dim):
                denominator = eigvals[i] + eigvals[j]
                if denominator > 1e-12:
                    L_eigen[i, j] = 2.0 * A_eigen[i, j] / denominator
        
        # Transform L back to original basis
        L = eigvecs @ L_eigen @ eigvecs.conj().T
        
        # Compute QFI = Tr[ρL²]
        qfi = np.trace(rho @ L @ L).real
        
        return float(qfi)

    def run_experiment(
        self,
        sample_sizes: List[int]
    ) -> Tuple[List[DiscrepancyQFIPoint], GoldenSLDAnalysis]:
        """
        Run complete experiment across multiple sample sizes and sequence types.
        
        Args:
            sample_sizes: List of sample sizes to test
            
        Returns:
            (data_points, analysis)
        """
        start_time = time.perf_counter()
        data_points: List[DiscrepancyQFIPoint] = []
        
        for n in sample_sizes:
            # Generate sequences
            phi_seq = self.generate_phi_lcg_sequence(n)
            random_seq = self.generate_random_sequence(n, seed=42)
            adversarial_seq = self.generate_adversarial_sequence(n)
            
            for seq_type, sequence in [
                ("phi_lcg", phi_seq),
                ("random", random_seq),
                ("adversarial", adversarial_seq)
            ]:
                # Compute star-discrepancy
                discrepancy = self.compute_star_discrepancy(sequence)
                
                # Convert to density matrix
                rho = self.sequence_to_density_matrix(sequence)
                
                # Compute QFI
                qfi = self.compute_qfi_via_sld(rho)
                
                # Store data point
                point = DiscrepancyQFIPoint(
                    sequence_type=seq_type,
                    sample_size=n,
                    star_discrepancy=discrepancy,
                    qfi=qfi,
                    discrepancy_inverse=1.0 / discrepancy if discrepancy > 0 else 0.0
                )
                data_points.append(point)
        
        # Analyze correlation: QFI vs 1/D_N^*
        qfi_values = np.array([p.qfi for p in data_points])
        inv_discrepancy = np.array([p.discrepancy_inverse for p in data_points])
        
        # Remove infinite/invalid points
        valid_mask = np.isfinite(qfi_values) & np.isfinite(inv_discrepancy)
        qfi_values = qfi_values[valid_mask]
        inv_discrepancy = inv_discrepancy[valid_mask]
        
        # Compute Pearson correlation
        if len(qfi_values) > 1:
            correlation_matrix = np.corrcoef(qfi_values, inv_discrepancy)
            pearson_r = correlation_matrix[0, 1]
            
            # Compute R² via linear regression
            coeffs = np.polyfit(inv_discrepancy, qfi_values, 1)
            qfi_pred = np.polyval(coeffs, inv_discrepancy)
            ss_res = np.sum((qfi_values - qfi_pred) ** 2)
            ss_tot = np.sum((qfi_values - np.mean(qfi_values)) ** 2)
            r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        else:
            pearson_r = 0.0
            r_squared = 0.0
        
        # Check breakthrough threshold
        breakthrough = (abs(pearson_r) > 0.8) and (r_squared > 0.8)
        
        # Compute improvement ratio
        phi_points = [p for p in data_points if p.sequence_type == "phi_lcg"]
        adversarial_points = [p for p in data_points if p.sequence_type == "adversarial"]
        
        optimal_qfi = np.mean([p.qfi for p in phi_points]) if phi_points else 0.0
        worst_qfi = np.mean([p.qfi for p in adversarial_points]) if adversarial_points else 1e-12
        qfi_improvement = optimal_qfi / worst_qfi if worst_qfi > 0 else 0.0
        
        execution_time = (time.perf_counter() - start_time) * 1000.0
        
        analysis = GoldenSLDAnalysis(
            pearson_r=float(pearson_r),
            r_squared=float(r_squared),
            breakthrough_achieved=bool(breakthrough),
            points=data_points,
            optimal_qfi=float(optimal_qfi),
            worst_qfi=float(worst_qfi),
            qfi_improvement_ratio=float(qfi_improvement),
            execution_time_ms=execution_time
        )
        
        return data_points, analysis


def run_golden_sld_correlation_experiment(
    sample_sizes: List[int] = None,
    dim: int = 4
) -> Tuple[List[DiscrepancyQFIPoint], GoldenSLDAnalysis]:
    """
    Execute Experiment 4: Test QFI ∝ 1/D_N^* correlation.
    
    Args:
        sample_sizes: List of sample sizes to test (default: [100, 500, 1000, 2000, 5000])
        dim: Density matrix dimension
        
    Returns:
        (data_points, analysis)
    """
    if sample_sizes is None:
        sample_sizes = [100, 500, 1000, 2000, 5000]
    
    experiment = GoldenSLDExperiment(dim=dim)
    points, analysis = experiment.run_experiment(sample_sizes)
    
    print("\n" + "="*80)
    print("EXPERIMENT 4: GOLDEN SLD — DISCREPANCY-QFI CORRELATION")
    print("="*80)
    print(f"\nHypothesis: QFI ∝ 1/D_N^*")
    print(f"Sample sizes tested: {sample_sizes}")
    print(f"Density matrix dimension: {dim}")
    
    print(f"\n{'Sequence Type':<15} {'N':<8} {'D_N^*':<12} {'QFI':<12} {'1/D_N^*':<12}")
    print("-" * 80)
    for point in points:
        print(
            f"{point.sequence_type:<15} "
            f"{point.sample_size:<8} "
            f"{point.star_discrepancy:<12.6f} "
            f"{point.qfi:<12.6f} "
            f"{point.discrepancy_inverse:<12.6f}"
        )
    
    print(f"\n{'CORRELATION ANALYSIS':<40}")
    print("-" * 80)
    print(f"Pearson r (QFI vs 1/D_N^*):     {analysis.pearson_r:>12.6f}")
    print(f"R² (coefficient of determination): {analysis.r_squared:>12.6f}")
    print(f"Optimal QFI (φ-LCG):               {analysis.optimal_qfi:>12.6f}")
    print(f"Worst QFI (adversarial):           {analysis.worst_qfi:>12.6f}")
    print(f"QFI improvement ratio:             {analysis.qfi_improvement_ratio:>12.2f}×")
    print(f"Execution time:                    {analysis.execution_time_ms:>12.2f} ms")
    
    print(f"\n{'BREAKTHROUGH THRESHOLD':<40}")
    print("-" * 80)
    print(f"Target: |r| > 0.8 AND R² > 0.8")
    print(f"Status: {'✅ BREAKTHROUGH ACHIEVED' if analysis.breakthrough_achieved else '❌ Threshold not met'}")
    
    if analysis.breakthrough_achieved:
        print("\n🎯 IMPLICATION:")
        print("   Number theory and quantum metrology are fundamentally connected.")
        print("   Optimal equidistribution maximizes quantum Fisher information.")
        print("   Universe's vacuum may be optimally distributed, not random.")
    
    print("="*80 + "\n")
    
    return points, analysis
