"""Tests for Frontier Experiment 3: Topological Charge Correlation."""

import numpy as np

from pythia_mining.frontier_experiment_3_topological_correlation import (
    TopologicalMetrics,
    compute_su2_winding_number,
    compute_topological_charge_density,
    get_experiment_metadata,
    measure_topological_transition_sharpness,
    run_topological_correlation_measurement,
)


def test_winding_number_is_integer():
    """Winding number should always be an integer."""
    for nonce in [0, 100, 1000, 10000, 123456]:
        winding = compute_su2_winding_number(nonce)
        assert isinstance(winding, int)


def test_winding_number_deterministic():
    """Winding number should be deterministic for same nonce."""
    nonce = 42
    w1 = compute_su2_winding_number(nonce)
    w2 = compute_su2_winding_number(nonce)
    assert w1 == w2


def test_topological_charge_density_finite():
    """Charge density should be finite."""
    for nonce in [1, 100, 10000]:
        charge = compute_topological_charge_density(nonce)
        assert np.isfinite(charge)
        assert isinstance(charge, float)


def test_topological_charge_deterministic():
    """Charge density should be deterministic."""
    nonce = 12345
    c1 = compute_topological_charge_density(nonce)
    c2 = compute_topological_charge_density(nonce)
    assert abs(c1 - c2) < 1e-12


def test_transition_sharpness_constant():
    """Sharpness of constant sequence should be 1.0."""
    windings = [3, 3, 3, 3, 3]
    sharpness = measure_topological_transition_sharpness(windings)
    assert sharpness == 1.0


def test_transition_sharpness_perfect_steps():
    """Sharpness of ±1 steps should be 1.0."""
    windings = [0, 1, 2, 3, 2, 1, 0]
    sharpness = measure_topological_transition_sharpness(windings)
    assert sharpness == 1.0


def test_transition_sharpness_noisy():
    """Sharpness of noisy transitions should be < 1.0."""
    windings = [0, 2, 1, 4, 2, 5, 3]  # Large jumps
    sharpness = measure_topological_transition_sharpness(windings)
    assert 0.0 <= sharpness < 1.0


def test_transition_sharpness_range():
    """Sharpness should always be in [0, 1]."""
    for _ in range(10):
        windings = list(np.random.randint(-5, 5, size=20))
        sharpness = measure_topological_transition_sharpness(windings)
        assert 0.0 <= sharpness <= 1.0


def test_topological_correlation_measurement_phi():
    """φ-LCG topological measurement should complete."""
    metrics_list, analysis = run_topological_correlation_measurement(
        num_samples=500,  # Small for fast test
        phi_lcg=True,
    )

    assert len(metrics_list) == 500
    assert isinstance(analysis, dict)

    # Analysis should contain expected keys
    assert "correlation" in analysis
    assert "sharpness_overall" in analysis
    assert "hypothesis_result" in analysis
    assert "breakthrough_achieved" in analysis

    # Correlation should be finite
    assert np.isfinite(analysis["correlation"])

    # Sharpness should be in [0, 1]
    assert 0.0 <= analysis["sharpness_overall"] <= 1.0


def test_topological_correlation_measurement_random():
    """Random topological measurement should complete."""
    metrics_list, analysis = run_topological_correlation_measurement(
        num_samples=500,
        phi_lcg=False,
    )

    assert len(metrics_list) == 500
    assert analysis["sampler_type"] == "random"
    assert np.isfinite(analysis["correlation"])


def test_topological_metrics_structure():
    """TopologicalMetrics should have correct structure."""
    metrics = TopologicalMetrics(
        sample_index=100,
        star_discrepancy=0.01,
        topological_charge=0.5,
        winding_number=2,
        action_value=0.3,
    )

    assert metrics.sample_index == 100
    assert isinstance(metrics.winding_number, int)
    assert np.isfinite(metrics.star_discrepancy)
    assert np.isfinite(metrics.topological_charge)


def test_experiment_metadata():
    """Experiment metadata should contain required fields."""
    metadata = get_experiment_metadata()

    assert "experiment_id" in metadata
    assert "hypothesis" in metadata
    assert "falsifiability" in metadata
    assert "breakthrough_threshold" in metadata

    assert metadata["experiment_id"] == "FRONTIER-TOPO-003"


def test_winding_number_bounded():
    """Winding numbers should be reasonably bounded for 4-byte configs."""
    # For a 4-byte nonce with 4 link variables, winding should be small
    windings = [compute_su2_winding_number(n) for n in range(0, 1000, 100)]

    # Should be small integers (not arbitrarily large)
    assert all(abs(w) <= 10 for w in windings), "Winding numbers suspiciously large"
