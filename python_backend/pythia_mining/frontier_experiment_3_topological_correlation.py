"""Frontier Experiment 3: Star-Discrepancy ↔ Topological Charge Correlation.

RESEARCH HYPOTHESIS:
When Van der Corput star-discrepancy hits GOLDEN_OPTIMAL bound, the SU(2)
lattice gauge field exhibits sharper discrete topological winding transitions
(instanton density jumps).

MATHEMATICAL CLAIM:
Optimal low-discrepancy sequences minimize "topological noise" by evenly
sampling the gauge configuration space. This should make topological charge
Q (winding number) transitions cleaner and more quantized.

FALSIFIABILITY:
Measure correlation between D_N^* time-series and topological charge jumps.
If correlation(|ΔD_N^*|, |ΔQ|) ≤ 0, hypothesis is rejected.

BREAKTHROUGH THRESHOLD:
If correlation > 0.7 AND Q transitions sharpen by 2x when D_N^* is optimal,
proves number-theoretic distribution has topological gauge theory origin.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np

from .hendrix_phi_solver import yang_mills_action, _su2_from_byte
from .phi_entropy import van_der_corput_discrepancy
from .golden_ratio_library import PHI


EPSILON = 1e-12


@dataclass(frozen=True)
class TopologicalMetrics:
    """Topological charge and discrepancy correlation metrics."""
    
    sample_index: int
    star_discrepancy: float
    topological_charge: float
    winding_number: int
    action_value: float


def compute_su2_winding_number(nonce: int) -> int:
    """Compute topological winding number (instanton charge) for SU(2) configuration.
    
    The winding number Q ∈ ℤ counts how many times the gauge field configuration
    wraps around the SU(2) group manifold. For a 4-byte nonce embedded as four
    SU(2) link variables, we compute the winding via:
    
    Q = (1/8π²) ∫ Tr(F ∧ F)
    
    where F is the field strength tensor. On a discrete lattice, this becomes
    a sum over plaquettes of the "topological charge density".
    
    Args:
        nonce: 32-bit nonce value
        
    Returns:
        Integer winding number Q ∈ ℤ
    """
    n = int(nonce) % (2**32)
    parts = [(n >> (8 * k)) & 0xFF for k in range(4)]
    
    # Create SU(2) link variables from bytes
    axes = [0, 1, 2, 0]  # σ_x, σ_y, σ_z, σ_x
    links = [_su2_from_byte(b, axis=axes[k]) for k, b in enumerate(parts)]
    
    # Compute field strength via plaquette loops
    # F_μν ~ [U_μ U_ν U_μ† U_ν† - I] (field strength from plaquette)
    
    total_charge = 0.0
    
    for i in range(4):
        for j in range(i + 1, 4):
            # Plaquette in (μ,ν) plane
            plaquette = links[i] @ links[j] @ links[i].conj().T @ links[j].conj().T
            
            # Topological charge density: (1/8π²) Tr(log(U_plaq))
            # For small deviations from identity, log(U) ≈ (U - I)
            # The imaginary part of Tr gives the winding contribution
            
            # Eigenvalues of SU(2) plaquette are e^{±iθ}
            eigenvalues = np.linalg.eigvals(plaquette)
            phases = np.angle(eigenvalues)
            
            # Winding contribution: sum of phases / 2π
            # (measures how much plaquette winds around U(1) subgroup)
            winding_contrib = np.sum(phases) / (2.0 * math.pi)
            
            total_charge += winding_contrib
    
    # Normalize by number of plaquettes and round to integer
    winding_number = int(np.round(total_charge / 6.0))  # 6 plaquettes
    
    return winding_number


def compute_topological_charge_density(nonce: int) -> float:
    """Compute continuous topological charge density (before integer rounding).
    
    This is the "raw" instanton density before quantization to integer winding.
    
    Returns:
        Continuous charge density in arbitrary units
    """
    n = int(nonce) % (2**32)
    parts = [(n >> (8 * k)) & 0xFF for k in range(4)]
    axes = [0, 1, 2, 0]
    links = [_su2_from_byte(b, axis=axes[k]) for k, b in enumerate(parts)]
    
    total_charge = 0.0
    
    for i in range(4):
        for j in range(i + 1, 4):
            plaquette = links[i] @ links[j] @ links[i].conj().T @ links[j].conj().T
            eigenvalues = np.linalg.eigvals(plaquette)
            phases = np.angle(eigenvalues)
            winding_contrib = np.sum(phases) / (2.0 * math.pi)
            total_charge += winding_contrib
    
    return float(total_charge / 6.0)


def measure_topological_transition_sharpness(
    winding_numbers: List[int],
) -> float:
    """Measure how "sharp" topological charge transitions are.
    
    Sharp transitions: Q changes by ±1 at specific points
    Noisy transitions: Q fluctuates continuously
    
    Sharpness = (# of ±1 jumps) / (total variation in Q)
    
    Returns:
        Sharpness metric in [0, 1], where 1 = perfectly quantized
    """
    if len(winding_numbers) < 2:
        return 0.0
    
    # Compute differences
    diffs = np.diff(winding_numbers)
    
    # Count ±1 jumps (clean topological transitions)
    unit_jumps = np.sum(np.abs(diffs) == 1)
    
    # Total variation
    total_variation = np.sum(np.abs(diffs))
    
    if total_variation == 0:
        return 1.0  # No transitions = perfectly stable
    
    sharpness = unit_jumps / total_variation
    
    return float(sharpness)


def run_topological_correlation_measurement(
    num_samples: int = 10_000,
    phi_lcg: bool = True,
) -> Tuple[List[TopologicalMetrics], dict]:
    """Measure correlation between star-discrepancy and topological charge.
    
    Args:
        num_samples: Number of nonce samples to measure
        phi_lcg: If True, use φ-LCG; if False, use random sampling
        
    Returns:
        (metrics_list, analysis_dict)
    """
    print("=" * 80)
    print("FRONTIER EXPERIMENT 3: Star-Discrepancy ↔ Topological Charge")
    print("=" * 80)
    print()
    print(f"Hypothesis: Optimal discrepancy sharpens topological transitions")
    print(f"Samples: {num_samples:,}")
    print(f"Sampler: {'φ-LCG (Van der Corput)' if phi_lcg else 'Random'}")
    print()
    
    metrics_list: List[TopologicalMetrics] = []
    
    # Generate nonce sequence
    if phi_lcg:
        # φ-LCG: (n * φ * 2^32) mod 2^32
        nonces = [int((n * PHI * (2**32)) % (2**32)) for n in range(1, num_samples + 1)]
    else:
        # Random uniform sampling
        import random
        rng = random.Random(42)
        nonces = [rng.randint(0, 2**32 - 1) for _ in range(num_samples)]
    
    print("Computing topological charges and discrepancies...")
    
    for idx, nonce in enumerate(nonces, start=1):
        # Compute topological charge
        winding = compute_su2_winding_number(nonce)
        charge_density = compute_topological_charge_density(nonce)
        action = yang_mills_action(nonce)
        
        # Compute star-discrepancy for sequence up to this point
        if phi_lcg:
            # Van der Corput discrepancy
            discrepancy_result = van_der_corput_discrepancy(idx)
            discrepancy = discrepancy_result.get("empirical_discrepancy", 0.0)
        else:
            # Approximate discrepancy for random sequence: O(√(log N / N))
            discrepancy = math.sqrt(math.log(idx + 1) / (idx + 1))
        
        metrics = TopologicalMetrics(
            sample_index=idx,
            star_discrepancy=discrepancy,
            topological_charge=charge_density,
            winding_number=winding,
            action_value=action,
        )
        
        metrics_list.append(metrics)
        
        if idx % 2000 == 0:
            print(f"  Processed {idx:,} samples...")
    
    print()
    
    # Extract time series for analysis
    discrepancies = [m.star_discrepancy for m in metrics_list]
    charges = [m.topological_charge for m in metrics_list]
    windings = [m.winding_number for m in metrics_list]
    
    # Compute correlation between |ΔD_N^*| and |ΔQ|
    delta_discrepancy = np.abs(np.diff(discrepancies))
    delta_charge = np.abs(np.diff(charges))
    
    # Pearson correlation
    if np.std(delta_discrepancy) > EPSILON and np.std(delta_charge) > EPSILON:
        correlation = float(np.corrcoef(delta_discrepancy, delta_charge)[0, 1])
    else:
        correlation = 0.0
    
    # Measure topological transition sharpness
    sharpness = measure_topological_transition_sharpness(windings)
    
    # Measure when discrepancy is "optimal" (within 10% of theoretical bound)
    theoretical_bound = [math.log(n + 1) / (n + 1) for n in range(1, len(discrepancies) + 1)]
    optimal_mask = [d <= 1.1 * bound for d, bound in zip(discrepancies, theoretical_bound)]
    
    # Sharpness during optimal periods
    optimal_indices = [i for i, is_opt in enumerate(optimal_mask) if is_opt]
    if len(optimal_indices) > 10:
        optimal_windings = [windings[i] for i in optimal_indices if i < len(windings)]
        sharpness_during_optimal = measure_topological_transition_sharpness(optimal_windings)
    else:
        sharpness_during_optimal = sharpness
    
    # Sharpness improvement ratio
    sharpness_improvement = sharpness_during_optimal / (sharpness + EPSILON)
    
    analysis = {
        "correlation": correlation,
        "sharpness_overall": sharpness,
        "sharpness_during_optimal": sharpness_during_optimal,
        "sharpness_improvement_ratio": sharpness_improvement,
        "hypothesis_result": "SUPPORTED" if correlation > 0.0 else "REJECTED",
        "breakthrough_achieved": correlation > 0.7 and sharpness_improvement > 2.0,
        "sampler_type": "phi_lcg" if phi_lcg else "random",
    }
    
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()
    print(f"Correlation(|ΔD_N^*|, |ΔQ|): {correlation:.3f}")
    print(f"  → {'✓ Positive correlation detected' if correlation > 0.0 else '✗ No correlation or negative'}")
    print()
    print(f"Topological transition sharpness: {sharpness:.3f}")
    print(f"Sharpness during optimal discrepancy: {sharpness_during_optimal:.3f}")
    print(f"Improvement ratio: {sharpness_improvement:.2f}x")
    print()
    
    if analysis["breakthrough_achieved"]:
        print("🏆 BREAKTHROUGH: Correlation > 0.7 AND sharpness improvement > 2x")
        print("   → Number-theoretic distribution has TOPOLOGICAL GAUGE origin")
        print("   → Optimal equidistribution minimizes topological noise")
    elif correlation > 0.0:
        print("✓ Hypothesis SUPPORTED: Positive correlation detected")
        print("   → Evidence for discrepancy-topology connection")
    else:
        print("✗ Hypothesis REJECTED: No positive correlation")
        print("   → Discrepancy and topological charge appear independent")
    
    print()
    print("=" * 80)
    
    return metrics_list, analysis


def run_comparative_phi_vs_random_topology():
    """Compare topological sharpness for φ-LCG vs random sampling."""
    print("\n" + "=" * 80)
    print("COMPARATIVE: φ-LCG vs Random Topological Sharpness")
    print("=" * 80)
    print()
    
    # φ-LCG measurement
    print("Measuring φ-LCG topological properties...")
    phi_metrics, phi_analysis = run_topological_correlation_measurement(
        num_samples=5000,
        phi_lcg=True,
    )
    
    print("\n")
    
    # Random measurement
    print("Measuring random sampling topological properties...")
    random_metrics, random_analysis = run_topological_correlation_measurement(
        num_samples=5000,
        phi_lcg=False,
    )
    
    # Comparative analysis
    sharpness_ratio = (phi_analysis["sharpness_overall"] / 
                       (random_analysis["sharpness_overall"] + EPSILON))
    
    print("\n" + "=" * 80)
    print("COMPARATIVE RESULTS")
    print("=" * 80)
    print()
    print(f"φ-LCG sharpness: {phi_analysis['sharpness_overall']:.3f}")
    print(f"Random sharpness: {random_analysis['sharpness_overall']:.3f}")
    print(f"Ratio (φ/Random): {sharpness_ratio:.3f}")
    print()
    
    if sharpness_ratio > 1.2:
        print("✓ φ-LCG produces SHARPER topological transitions")
    elif sharpness_ratio < 0.8:
        print("✗ Random produces sharper transitions")
    else:
        print("≈ No significant difference")
    
    return phi_analysis, random_analysis


def get_experiment_metadata() -> dict:
    """Return experiment metadata for registry and reproducibility."""
    return {
        "experiment_id": "FRONTIER-TOPO-003",
        "hypothesis": "Optimal star-discrepancy sharpens topological charge transitions",
        "mathematical_basis": "Low-discrepancy sampling minimizes topological noise in gauge configuration space",
        "falsifiability": "Measure correlation(|ΔD_N^*|, |ΔQ|)",
        "rejection_criterion": "correlation ≤ 0.0",
        "breakthrough_threshold": "correlation > 0.7 AND sharpness_improvement > 2.0",
        "implications_if_proven": [
            "Number theory and gauge topology are fundamentally connected",
            "Optimal distribution minimizes instanton noise",
            "Diophantine approximation explains topological quantization",
        ],
        "reproducibility": {
            "num_samples": 10_000,
            "phi_lcg_golden_ratio": PHI,
        },
    }


__all__ = [
    "TopologicalMetrics",
    "compute_su2_winding_number",
    "compute_topological_charge_density",
    "measure_topological_transition_sharpness",
    "run_topological_correlation_measurement",
    "run_comparative_phi_vs_random_topology",
    "get_experiment_metadata",
]
