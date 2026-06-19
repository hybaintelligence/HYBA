"""Tests for Frontier Experiment 1: φ-QMC vs MCMC Convergence."""

from pythia_mining.frontier_experiment_1_qmc_convergence import (
    ConvergenceMetrics,
    fit_convergence_rate,
    get_experiment_metadata,
    measure_convergence,
    phi_lcg_sampler,
    prng_sampler,
    run_comparative_benchmark,
)


def test_phi_lcg_sampler_deterministic():
    """φ-LCG sampler should be deterministic."""
    nonce1 = phi_lcg_sampler(100)
    nonce2 = phi_lcg_sampler(100)
    assert nonce1 == nonce2
    assert 0 <= nonce1 < 2**32


def test_phi_lcg_sampler_different_outputs():
    """φ-LCG sampler should produce different nonces for different n."""
    nonce1 = phi_lcg_sampler(1)
    nonce2 = phi_lcg_sampler(2)
    assert nonce1 != nonce2


def test_convergence_rate_fitting():
    """Convergence rate fitting should recover known exponents."""
    # Simulate O(1/N) convergence
    sample_counts = [100, 1000, 10000]
    errors_qmc = [1.0 / n for n in sample_counts]

    alpha = fit_convergence_rate(sample_counts, errors_qmc)

    # Should recover α ≈ 1.0 for O(1/N)
    assert 0.8 <= alpha <= 1.2, f"Expected α ≈ 1.0, got {alpha:.3f}"


def test_convergence_rate_mcmc_simulation():
    """Convergence rate fitting should detect O(1/√N)."""
    import math

    sample_counts = [100, 1000, 10000]
    errors_mcmc = [1.0 / math.sqrt(n) for n in sample_counts]

    alpha = fit_convergence_rate(sample_counts, errors_mcmc)

    # Should recover α ≈ 0.5 for O(1/√N)
    assert 0.3 <= alpha <= 0.7, f"Expected α ≈ 0.5, got {alpha:.3f}"


def test_measure_convergence_phi_lcg():
    """φ-LCG convergence measurement should complete without errors."""

    metrics = measure_convergence(
        sampler_fn=phi_lcg_sampler,
        sampler_name="phi_lcg",
        max_samples=1000,
        convergence_threshold=0.1,
        vacuum_energy_target=0.5,
        measurement_interval=100,
    )

    assert isinstance(metrics, ConvergenceMetrics)
    assert metrics.sampler_name == "phi_lcg"
    assert 0 <= metrics.samples_to_convergence <= 1000
    assert metrics.final_mean_action >= 0.0
    # Convergence rate can be negative with noise/small samples
    assert -1.0 <= metrics.convergence_rate_exponent <= 2.0


def test_measure_convergence_prng():
    """PRNG convergence measurement should complete without errors."""

    metrics = measure_convergence(
        sampler_fn=prng_sampler,
        sampler_name="prng",
        max_samples=1000,
        convergence_threshold=0.1,
        vacuum_energy_target=0.5,
        measurement_interval=100,
    )

    assert isinstance(metrics, ConvergenceMetrics)
    assert metrics.sampler_name == "prng"
    assert 0 <= metrics.samples_to_convergence <= 1000


def test_comparative_benchmark_runs():
    """Comparative benchmark should run and produce analysis."""
    phi_metrics, prng_metrics, analysis = run_comparative_benchmark(
        max_samples=2000,  # Small for fast test
        convergence_threshold=0.1,
        vacuum_target=0.5,
    )

    assert isinstance(phi_metrics, ConvergenceMetrics)
    assert isinstance(prng_metrics, ConvergenceMetrics)
    assert isinstance(analysis, dict)

    # Analysis should contain expected keys
    assert "convergence_ratio" in analysis
    assert "rate_improvement_factor" in analysis
    assert "hypothesis_result" in analysis
    assert "breakthrough_achieved" in analysis

    # Convergence ratio should be positive
    assert analysis["convergence_ratio"] > 0.0

    # Hypothesis result should be deterministic
    assert analysis["hypothesis_result"] in ["SUPPORTED", "REJECTED"]


def test_experiment_metadata():
    """Experiment metadata should contain required fields."""
    metadata = get_experiment_metadata()

    assert "experiment_id" in metadata
    assert "hypothesis" in metadata
    assert "falsifiability" in metadata
    assert "breakthrough_threshold" in metadata
    assert "reproducibility" in metadata

    assert metadata["experiment_id"] == "FRONTIER-QMC-001"


def test_convergence_metrics_properties():
    """ConvergenceMetrics should satisfy basic properties."""
    metrics = ConvergenceMetrics(
        sampler_name="test",
        samples_to_convergence=1000,
        final_mean_action=0.5,
        final_std_action=0.1,
        convergence_rate_exponent=0.8,
        noise_floor_db=-20.0,
        wall_time_seconds=1.5,
    )

    assert metrics.sampler_name == "test"
    assert metrics.samples_to_convergence == 1000
    assert metrics.convergence_rate_exponent > 0
