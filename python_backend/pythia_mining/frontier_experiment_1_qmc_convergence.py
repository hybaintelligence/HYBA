"""Frontier Experiment 1: φ-QMC vs Standard MCMC Convergence Benchmark.

RESEARCH HYPOTHESIS:
φ-LCG (Van der Corput sequence) as quasi-Monte Carlo sampler for SU(2)
configuration space converges to vacuum energy faster than standard PRNG.

MATHEMATICAL CLAIM:
If φ-LCG is optimally distributed (star-discrepancy D_N^* = O(log N / N)),
then integration of the partition function Z = ∫ e^{-S} dU should converge
at rate O(1/N) instead of standard O(1/√N).

FALSIFIABILITY:
Measure samples needed to reach vacuum energy ±0.01 for both samplers.
If φ_convergence_n / prng_convergence_n ≥ 1.0, hypothesis is rejected.

BREAKTHROUGH THRESHOLD:
If ratio < 0.7, quasi-Monte Carlo gauge sampling is proven superior,
suggesting gauge symmetry and equidistribution are dual concepts.
"""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np

from .hendrix_phi_solver import yang_mills_action
from .golden_ratio_library import PHI

# Alias for clarity in Van der Corput context
GOLDEN_RATIO = PHI


@dataclass(frozen=True)
class ConvergenceMetrics:
    """Convergence statistics for a sampling method."""

    sampler_name: str
    samples_to_convergence: int
    final_mean_action: float
    final_std_action: float
    convergence_rate_exponent: float  # Fitted: error ~ N^{-α}
    noise_floor_db: float  # 10 * log10(variance)
    wall_time_seconds: float


def phi_lcg_sampler(n: int) -> int:
    """Van der Corput φ-LCG generator for nonce sampling.

    Uses the low-discrepancy property of the golden ratio LCG to
    sample the nonce space [0, 2^32) with optimal equidistribution.
    """
    # Van der Corput sequence in base φ (approximated via modular arithmetic)
    # nonce_n = (n * φ * 2^32) mod 2^32
    return int((n * GOLDEN_RATIO * (2**32)) % (2**32))


def prng_sampler(n: int, rng: random.Random) -> int:
    """Standard PRNG (Mersenne Twister) nonce sampler."""
    return rng.randint(0, 2**32 - 1)


def compute_running_statistics(
    actions: List[float],
) -> Tuple[List[float], List[float]]:
    """Compute running mean and standard deviation.

    Returns:
        (running_means, running_stds)
    """
    running_means = []
    running_stds = []

    for i in range(1, len(actions) + 1):
        window = actions[:i]
        running_means.append(float(np.mean(window)))
        running_stds.append(float(np.std(window)))

    return running_means, running_stds


def fit_convergence_rate(
    sample_counts: List[int],
    errors: List[float],
) -> float:
    """Fit convergence rate exponent α where error ~ N^{-α}.

    Standard MCMC: α ≈ 0.5 (central limit theorem)
    QMC conjecture: α ≈ 1.0 (Koksma-Hlawka inequality)

    Returns:
        Fitted exponent α
    """
    # Log-log fit: log(error) = -α * log(N) + c
    log_n = np.log(sample_counts)
    log_error = np.log(np.maximum(errors, 1e-12))  # Avoid log(0)

    # Linear regression on log-log scale
    coeffs = np.polyfit(log_n, log_error, deg=1)
    alpha = -coeffs[0]  # Negative of slope

    return float(alpha)


def measure_convergence(
    sampler_fn,
    sampler_name: str,
    max_samples: int = 100_000,
    convergence_threshold: float = 0.01,
    vacuum_energy_target: float = 0.5,  # Theoretical SU(2) vacuum at β→∞
    measurement_interval: int = 100,
) -> ConvergenceMetrics:
    """Measure convergence to vacuum energy for a sampling method.

    Args:
        sampler_fn: Function(n, rng) -> nonce
        sampler_name: Human-readable sampler identifier
        max_samples: Maximum samples before timeout
        convergence_threshold: ±threshold for convergence detection
        vacuum_energy_target: Target mean action (0.5 for SU(2) vacuum)
        measurement_interval: Samples between convergence checks

    Returns:
        ConvergenceMetrics with convergence statistics
    """
    rng = random.Random(42)  # Fixed seed for reproducibility
    actions: List[float] = []
    start_time = time.monotonic()

    converged = False
    convergence_n = max_samples

    for n in range(1, max_samples + 1):
        # Generate nonce and compute action
        if sampler_name == "phi_lcg":
            nonce = phi_lcg_sampler(n)
        else:
            nonce = sampler_fn(n, rng)

        action = yang_mills_action(nonce)
        actions.append(action)

        # Check convergence every interval
        if n % measurement_interval == 0 and n >= 1000:
            mean_action = float(np.mean(actions))
            if abs(mean_action - vacuum_energy_target) <= convergence_threshold:
                converged = True
                convergence_n = n
                break

    wall_time = time.monotonic() - start_time

    # Compute final statistics
    running_means, running_stds = compute_running_statistics(actions)
    final_mean = running_means[-1]
    final_std = running_stds[-1]

    # Fit convergence rate (sample every 1000 points to avoid noise)
    sample_indices = list(range(1000, len(actions), 1000))
    if len(sample_indices) < 10:
        sample_indices = list(range(100, len(actions), 100))

    sampled_errors = [
        abs(running_means[i - 1] - vacuum_energy_target)
        for i in sample_indices
        if i <= len(running_means)
    ]

    if len(sampled_errors) >= 3:
        convergence_rate = fit_convergence_rate(
            sample_indices[: len(sampled_errors)], sampled_errors
        )
    else:
        convergence_rate = 0.0

    # Noise floor (final variance in dB)
    noise_floor = 10.0 * math.log10(final_std**2 + 1e-12)

    return ConvergenceMetrics(
        sampler_name=sampler_name,
        samples_to_convergence=convergence_n if converged else max_samples,
        final_mean_action=final_mean,
        final_std_action=final_std,
        convergence_rate_exponent=convergence_rate,
        noise_floor_db=noise_floor,
        wall_time_seconds=wall_time,
    )


def run_comparative_benchmark(
    max_samples: int = 50_000,
    convergence_threshold: float = 0.01,
    vacuum_target: float = 0.5,
) -> Tuple[ConvergenceMetrics, ConvergenceMetrics, dict]:
    """Run comparative φ-QMC vs PRNG convergence benchmark.

    Returns:
        (phi_metrics, prng_metrics, comparative_analysis)
    """
    print("=" * 80)
    print("FRONTIER EXPERIMENT 1: φ-QMC vs Standard MCMC Convergence")
    print("=" * 80)
    print()
    print("Hypothesis: φ-LCG converges to vacuum energy faster than PRNG")
    print(f"Target: Mean action = {vacuum_target:.3f} ± {convergence_threshold:.3f}")
    print(f"Max samples: {max_samples:,}")
    print()

    # Measure φ-LCG convergence
    print("Measuring φ-LCG (Van der Corput) convergence...")
    phi_metrics = measure_convergence(
        sampler_fn=phi_lcg_sampler,
        sampler_name="phi_lcg",
        max_samples=max_samples,
        convergence_threshold=convergence_threshold,
        vacuum_energy_target=vacuum_target,
    )
    print(
        f"✓ φ-LCG: {phi_metrics.samples_to_convergence:,} samples, "
        f"α={phi_metrics.convergence_rate_exponent:.3f}"
    )

    # Measure PRNG convergence
    print("Measuring PRNG (Mersenne Twister) convergence...")
    prng_metrics = measure_convergence(
        sampler_fn=prng_sampler,
        sampler_name="prng",
        max_samples=max_samples,
        convergence_threshold=convergence_threshold,
        vacuum_energy_target=vacuum_target,
    )
    print(
        f"✓ PRNG: {prng_metrics.samples_to_convergence:,} samples, "
        f"α={prng_metrics.convergence_rate_exponent:.3f}"
    )
    print()

    # Comparative analysis
    convergence_ratio = (
        phi_metrics.samples_to_convergence / prng_metrics.samples_to_convergence
    )
    rate_improvement = (
        phi_metrics.convergence_rate_exponent / prng_metrics.convergence_rate_exponent
    )
    noise_suppression_db = prng_metrics.noise_floor_db - phi_metrics.noise_floor_db
    speedup = prng_metrics.wall_time_seconds / phi_metrics.wall_time_seconds

    analysis = {
        "convergence_ratio": convergence_ratio,
        "rate_improvement_factor": rate_improvement,
        "noise_suppression_db": noise_suppression_db,
        "wall_time_speedup": speedup,
        "hypothesis_result": "SUPPORTED" if convergence_ratio < 1.0 else "REJECTED",
        "breakthrough_achieved": convergence_ratio < 0.7,
    }

    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()
    print(f"Convergence ratio (φ/PRNG): {convergence_ratio:.3f}")
    print(
        f"  → {'✓ φ-LCG converges FASTER' if convergence_ratio < 1.0 else '✗ PRNG converges faster'}"
    )
    print()
    print(f"Rate improvement (α_φ / α_PRNG): {rate_improvement:.3f}")
    print(f"  → φ-LCG: α ≈ {phi_metrics.convergence_rate_exponent:.3f}")
    print(f"  → PRNG: α ≈ {prng_metrics.convergence_rate_exponent:.3f}")
    print("  → Expected MCMC: α ≈ 0.5, QMC conjecture: α ≈ 1.0")
    print()
    print(f"Noise suppression: {noise_suppression_db:.1f} dB")
    print(
        f"  → {'✓ φ-LCG suppresses variance' if noise_suppression_db > 0 else '✗ PRNG has lower variance'}"
    )
    print()
    print(f"Wall time speedup: {speedup:.2f}x")
    print()

    if analysis["breakthrough_achieved"]:
        print("🏆 BREAKTHROUGH: Convergence ratio < 0.7")
        print("   → Quasi-Monte Carlo gauge sampling is PROVEN superior")
        print("   → Suggests gauge symmetry and equidistribution are DUAL concepts")
    elif convergence_ratio < 1.0:
        print("✓ Hypothesis SUPPORTED: φ-LCG shows faster convergence")
        print("   → Evidence for low-discrepancy advantage in gauge theory")
    else:
        print("✗ Hypothesis REJECTED: PRNG converges faster or equally")
        print("   → No advantage detected for φ-LCG in this regime")

    print()
    print("=" * 80)

    return phi_metrics, prng_metrics, analysis


def get_experiment_metadata() -> dict:
    """Return experiment metadata for registry and reproducibility."""
    return {
        "experiment_id": "FRONTIER-QMC-001",
        "hypothesis": "φ-LCG converges O(1/N) vs PRNG O(1/√N) for SU(2) vacuum",
        "mathematical_basis": "Koksma-Hlawka inequality + Van der Corput low-discrepancy",
        "falsifiability": "Measure convergence_ratio = samples_φ / samples_PRNG",
        "rejection_criterion": "convergence_ratio ≥ 1.0",
        "breakthrough_threshold": "convergence_ratio < 0.7",
        "implications_if_proven": [
            "Gauge theory configuration space prefers low-discrepancy sampling",
            "Equidistribution and gauge symmetry are mathematically dual",
            "QMC provides intrinsic advantage over MCMC for lattice gauge theory",
        ],
        "reproducibility": {
            "random_seed": 42,
            "max_samples": 50_000,
            "convergence_threshold": 0.01,
            "vacuum_target": 0.5,
        },
    }


__all__ = [
    "ConvergenceMetrics",
    "run_comparative_benchmark",
    "measure_convergence",
    "phi_lcg_sampler",
    "prng_sampler",
    "get_experiment_metadata",
]
