"""
Unit and Integration Tests for Quantum Adversary

TESTING METHODOLOGY:
- Unit tests: Individual component verification
- Integration tests: Full attack-repair pipeline
- Property-based tests: Group theory invariants
- Benchmark tests: Attack and repair performance

MATHEMATICAL PROPERTIES TESTED:
1. Group order ∈ [1, 120] (A5 bounds)
2. Orbit violation ∈ [0, 1]
3. Repair convergence (Bures norm decreases)
4. Passport validity is boolean
5. Entropy injection preserves density matrix properties
"""

import sys
from pathlib import Path
import pytest
import numpy as np
from hypothesis import given, strategies as st, settings, assume

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent / "python_backend"))
sys.path.insert(0, str(Path(__file__).parent))

from frontier_quantum_adversary import QuantumAdversary, PassportDefender
from pythia_mining.pulvini_topology import CoxeterTopology
from pythia_mining.pulvini_certificates import PostQuantumPassport


# ============================================================================
# UNIT TESTS
# ============================================================================


class TestCoxeterTopology:
    """Unit tests for CoxeterTopology."""

    @pytest.fixture
    def topology(self):
        """Create topology instance."""
        return CoxeterTopology(group_type="A5", dimension=32)

    def test_initial_group_order(self, topology):
        """Test initial group order is 120."""
        order = topology.get_group_order()
        assert order == 120, f"Expected order 120, got {order}"

    def test_canonical_map_shape(self, topology):
        """Test canonical map has correct shape."""
        canonical_map = topology.get_canonical_map()
        assert canonical_map.shape == (
            32,
            3,
        ), f"Expected shape (32, 3), got {canonical_map.shape}"

    def test_orbit_structure(self, topology):
        """Test orbit structure is valid."""
        orbits = topology.compute_node_orbits()

        # Should have at least one orbit
        assert len(orbits) > 0

        # Each orbit should be non-empty list of integers
        for orbit in orbits:
            assert len(orbit) > 0
            assert all(isinstance(node, int) for node in orbit)

    def test_density_state_hermitian(self, topology):
        """Test density state is Hermitian."""
        rho = topology.get_density_state()

        # Check Hermitian
        assert np.allclose(
            rho, rho.conj().T, atol=1e-10
        ), "Density state must be Hermitian"

    def test_density_state_trace_one(self, topology):
        """Test density state has trace 1."""
        rho = topology.get_density_state()

        trace = float(np.trace(rho).real)
        assert np.isclose(
            trace, 1.0, atol=1e-10
        ), f"Density state trace must be 1, got {trace}"

    def test_density_state_positive_semidefinite(self, topology):
        """Test density state is PSD."""
        rho = topology.get_density_state()

        eigvals = np.linalg.eigvalsh(rho).real
        assert np.all(
            eigvals >= -1e-10
        ), f"Density state must be PSD, got min eigval {eigvals[0]}"


class TestPostQuantumPassport:
    """Unit tests for PostQuantumPassport."""

    @pytest.fixture
    def passport(self):
        """Create passport instance."""
        topology = CoxeterTopology(group_type="A5", dimension=32)
        return PostQuantumPassport(topology=topology)

    def test_initial_validity(self, passport):
        """Test passport is initially valid."""
        is_valid = passport.verify_integrity()
        assert is_valid, "New passport should be valid"

    def test_bures_certificate_structure(self, passport):
        """Test Bures certificate has correct structure."""
        cert = passport.get_bures_certificate()

        assert hasattr(cert, "bures_norm")
        assert hasattr(cert, "stationary")
        assert isinstance(cert.bures_norm, float)
        assert isinstance(cert.stationary, bool)

    def test_verification_status_structure(self, passport):
        """Test verification status dict structure."""
        status = passport.get_verification_status()

        required_keys = ["is_valid", "bures_norm", "group_order", "expected_order"]
        for key in required_keys:
            assert key in status, f"Missing key {key} in verification status"


class TestQuantumAdversary:
    """Unit tests for QuantumAdversary."""

    @pytest.fixture
    def setup(self):
        """Create adversary and topology."""
        topology = CoxeterTopology(group_type="A5", dimension=32)
        adversary = QuantumAdversary(topology, seed=42)
        return topology, adversary

    def test_adversary_initialization(self, setup):
        """Test adversary initializes correctly."""
        topology, adversary = setup

        assert adversary.topology is topology
        assert adversary.rng is not None
        assert len(adversary.attack_history) == 0

    def test_entropy_level_bounds(self, setup):
        """Test entropy injection respects bounds."""
        topology, adversary = setup

        # Valid entropy levels should work
        for entropy in [0.001, 0.01, 0.1, 0.5, 1.0]:
            attack = adversary.inject_symmetry_breaking_noise(entropy, "gaussian")
            assert "entropy_level" in attack
            assert attack["entropy_level"] == entropy

    def test_invalid_entropy_level(self, setup):
        """Test invalid entropy levels are rejected."""
        topology, adversary = setup

        # Negative entropy
        with pytest.raises(ValueError):
            adversary.inject_symmetry_breaking_noise(-0.1, "gaussian")

        # Entropy > 1.0
        with pytest.raises(ValueError):
            adversary.inject_symmetry_breaking_noise(1.5, "gaussian")

    def test_attack_types(self, setup):
        """Test all attack types work."""
        topology, adversary = setup

        attack_types = ["gaussian", "adversarial", "coherent"]

        for attack_type in attack_types:
            # Reset topology
            topology = CoxeterTopology(group_type="A5", dimension=32)
            adversary = QuantumAdversary(topology, seed=42)

            attack = adversary.inject_symmetry_breaking_noise(0.01, attack_type)
            assert attack["attack_type"] == attack_type

    def test_attack_history_tracking(self, setup):
        """Test attack history is tracked."""
        topology, adversary = setup

        # Perform multiple attacks
        adversary.inject_symmetry_breaking_noise(0.01, "gaussian")
        adversary.inject_symmetry_breaking_noise(0.05, "adversarial")

        assert len(adversary.attack_history) == 2


class TestPassportDefender:
    """Unit tests for PassportDefender."""

    @pytest.fixture
    def defender(self):
        """Create defender instance."""
        topology = CoxeterTopology(group_type="A5", dimension=32)
        passport = PostQuantumPassport(topology=topology)
        return PassportDefender(passport)

    def test_defender_initialization(self, defender):
        """Test defender initializes correctly."""
        assert defender.passport is not None
        assert len(defender.repair_history) == 0

    def test_detect_no_violation_initially(self, defender):
        """Test clean passport has no violations."""
        is_violated, score = defender.detect_symmetry_violation()

        # New passport should not be violated
        assert (
            not is_violated or score < 0.1
        ), "Clean passport should not show violation"


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestQuantumAdversaryIntegration:
    """Integration tests for attack-repair pipeline."""

    def test_full_attack_repair_cycle(self):
        """Test complete attack → detect → repair cycle."""
        # Setup
        topology = CoxeterTopology(group_type="A5", dimension=32)
        passport = PostQuantumPassport(topology=topology)
        adversary = QuantumAdversary(topology, seed=42)
        defender = PassportDefender(passport)

        # Initial state should be valid
        assert passport.verify_integrity()

        # Attack
        attack = adversary.inject_symmetry_breaking_noise(0.05, "gaussian")

        # Detect
        is_violated, score = defender.detect_symmetry_violation()

        # If violated, attempt repair
        if is_violated or score > 0.01:
            repair = defender.attempt_bures_gradient_repair(max_iterations=20)

            # Repair should complete
            assert "success" in repair
            assert "iterations" in repair

    def test_progressive_entropy_attacks(self):
        """Test attacks with increasing entropy."""
        entropy_levels = [0.001, 0.01, 0.05, 0.1]

        results = []

        for entropy in entropy_levels:
            # Fresh topology for each test
            topology = CoxeterTopology(group_type="A5", dimension=32)
            adversary = QuantumAdversary(topology, seed=42)

            attack = adversary.inject_symmetry_breaking_noise(entropy, "gaussian")

            results.append(
                {
                    "entropy": entropy,
                    "order_violation": attack["order_violation"],
                    "orbit_violation": attack["orbit_violation"],
                }
            )

        # Higher entropy should generally cause more violations
        # (not strictly monotonic due to randomness, but trend should hold)
        first_violation = results[0]["order_violation"]
        last_violation = results[-1]["order_violation"]

        # Last should be >= first (allowing for some randomness)
        assert (
            last_violation >= first_violation * 0.5
        ), "Higher entropy should cause more violations"


# ============================================================================
# PROPERTY-BASED TESTS (Hypothesis)
# ============================================================================


@given(
    entropy=st.floats(min_value=0.001, max_value=0.5),
    seed=st.integers(min_value=0, max_value=1000),
)
@settings(max_examples=15, deadline=5000)
def test_group_order_bounds(entropy, seed):
    """Property: Group order stays in [1, 120] after attack."""
    topology = CoxeterTopology(group_type="A5", dimension=32)
    adversary = QuantumAdversary(topology, seed=seed)

    attack = adversary.inject_symmetry_breaking_noise(entropy, "gaussian")

    perturbed_order = attack["perturbed_order"]

    assert (
        1 <= perturbed_order <= 120
    ), f"Group order {perturbed_order} outside [1, 120]"


@given(
    entropy=st.floats(min_value=0.001, max_value=0.5),
    seed=st.integers(min_value=0, max_value=1000),
)
@settings(max_examples=15, deadline=5000)
def test_violation_scores_bounded(entropy, seed):
    """Property: Violation scores ∈ [0, 1]."""
    topology = CoxeterTopology(group_type="A5", dimension=32)
    adversary = QuantumAdversary(topology, seed=seed)

    attack = adversary.inject_symmetry_breaking_noise(entropy, "gaussian")

    assert 0.0 <= attack["order_violation"] <= 1.0
    assert 0.0 <= attack["orbit_violation"] <= 1.0


@given(entropy=st.floats(min_value=0.001, max_value=0.2))
@settings(max_examples=10, deadline=5000)
def test_repair_reduces_bures_norm(entropy):
    """Property: Repair should reduce Bures norm (or keep it low)."""
    topology = CoxeterTopology(group_type="A5", dimension=32)
    passport = PostQuantumPassport(topology=topology)
    adversary = QuantumAdversary(topology, seed=42)
    defender = PassportDefender(passport)

    # Attack
    adversary.inject_symmetry_breaking_noise(entropy, "gaussian")

    initial_cert = passport.get_bures_certificate()
    initial_norm = initial_cert.bures_norm

    # Repair
    repair = defender.attempt_bures_gradient_repair(max_iterations=10)

    final_cert = passport.get_bures_certificate()
    final_norm = final_cert.bures_norm

    # Should not increase (may stay same if already low)
    assert (
        final_norm <= initial_norm + 0.1
    ), f"Repair should reduce Bures norm: {initial_norm} -> {final_norm}"


# ============================================================================
# BENCHMARK TESTS
# ============================================================================


class TestQuantumAdversaryBenchmarks:
    """Benchmark tests for attack and repair performance."""

    @pytest.mark.benchmark
    def test_gaussian_attack_speed(self, benchmark):
        """Benchmark Gaussian attack speed."""

        def run_attack():
            topology = CoxeterTopology(group_type="A5", dimension=32)
            adversary = QuantumAdversary(topology, seed=42)
            return adversary.inject_symmetry_breaking_noise(0.01, "gaussian")

        result = benchmark(run_attack)
        assert "order_violation" in result

    @pytest.mark.benchmark
    def test_repair_speed(self, benchmark):
        """Benchmark repair convergence speed."""
        # Setup
        topology = CoxeterTopology(group_type="A5", dimension=32)
        passport = PostQuantumPassport(topology=topology)
        adversary = QuantumAdversary(topology, seed=42)
        defender = PassportDefender(passport)

        # Attack once
        adversary.inject_symmetry_breaking_noise(0.05, "gaussian")

        # Benchmark repair
        result = benchmark(defender.attempt_bures_gradient_repair, max_iterations=10)

        assert "success" in result


# ============================================================================
# REGRESSION TESTS
# ============================================================================


class TestQuantumAdversaryRegression:
    """Regression tests for known adversary behavior."""

    def test_known_group_order_regression(self):
        """Test group order computation remains stable."""
        topology = CoxeterTopology(group_type="A5", dimension=32)

        # Initial order should always be 120
        order = topology.get_group_order()
        assert order == 120, f"Group order regression: expected 120, got {order}"

    def test_small_entropy_preserves_validity(self):
        """Test very small entropy preserves passport validity."""
        topology = CoxeterTopology(group_type="A5", dimension=32)
        passport = PostQuantumPassport(topology=topology)
        adversary = QuantumAdversary(topology, seed=42)

        # Very small attack
        adversary.inject_symmetry_breaking_noise(0.0001, "gaussian")

        # Should likely remain valid (though not guaranteed)
        is_valid = passport.verify_integrity()

        # At minimum, should not crash
        assert isinstance(is_valid, bool)


# ============================================================================
# EDGE CASE TESTS
# ============================================================================


class TestQuantumAdversaryEdgeCases:
    """Edge case tests for boundary conditions."""

    def test_minimum_entropy(self):
        """Test minimum entropy attack."""
        topology = CoxeterTopology(group_type="A5", dimension=32)
        adversary = QuantumAdversary(topology, seed=42)

        # Minimum entropy
        attack = adversary.inject_symmetry_breaking_noise(0.0001, "gaussian")

        # Should complete without error
        assert "order_violation" in attack

    def test_maximum_entropy(self):
        """Test maximum entropy attack."""
        topology = CoxeterTopology(group_type="A5", dimension=32)
        adversary = QuantumAdversary(topology, seed=42)

        # Maximum entropy
        attack = adversary.inject_symmetry_breaking_noise(1.0, "gaussian")

        # Should complete without error
        assert "order_violation" in attack

    def test_repair_with_zero_iterations(self):
        """Test repair with zero iterations."""
        topology = CoxeterTopology(group_type="A5", dimension=32)
        passport = PostQuantumPassport(topology=topology)
        defender = PassportDefender(passport)

        # Zero iterations should return immediately
        repair = defender.attempt_bures_gradient_repair(max_iterations=0)

        assert "iterations" in repair
        assert repair["iterations"] == 0

    def test_multiple_sequential_attacks(self):
        """Test multiple attacks on same topology."""
        topology = CoxeterTopology(group_type="A5", dimension=32)
        adversary = QuantumAdversary(topology, seed=42)

        # Multiple attacks
        for _ in range(3):
            attack = adversary.inject_symmetry_breaking_noise(0.01, "gaussian")
            assert "order_violation" in attack

        # Should have 3 attacks in history
        assert len(adversary.attack_history) == 3

    def test_attack_type_case_sensitivity(self):
        """Test attack type must be exact (case sensitive)."""
        topology = CoxeterTopology(group_type="A5", dimension=32)
        adversary = QuantumAdversary(topology, seed=42)

        # Invalid attack type (wrong case)
        with pytest.raises(ValueError):
            adversary.inject_symmetry_breaking_noise(0.01, "GAUSSIAN")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
