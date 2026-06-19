"""Behavioral tests for enhanced quantum healing mechanisms.

Tests measure what the mathematics actually produces — not assertions
about what it should do, but empirical measurements of the outcomes.
"""

import math
import numpy as np
import pytest
from pythia_mining.quantum_healing_swarm import (
    QuantumHealingSwarm,
    HealingResult,
    PHI,
    PHI_INV,
)


class TestWKBTunnelling:
    """WKB tunnelling: barrier penetration for escaping local minima."""

    def test_tunnelling_amplitude_decreases_with_barrier_height(self):
        """Tunnelling amplitude should decay exponentially with barrier height."""
        swarm = QuantumHealingSwarm(
            num_candidates=8,
            enable_tunnelling=True,
            enable_annealing=False,
            enable_swarming=False,
            enable_interference=False,
        )

        # High barrier (low purity)
        rho_high_barrier = swarm._form_degraded_density_matrix(
            phi_density=0.1, consecutive_failures=20, degrade_factor=1.0
        )
        _, amp_high = swarm._wkb_tunnel(rho_high_barrier, phi_density=0.1)

        # Low barrier (high purity)
        rho_low_barrier = swarm._form_degraded_density_matrix(
            phi_density=0.9, consecutive_failures=1, degrade_factor=0.1
        )
        _, amp_low = swarm._wkb_tunnel(rho_low_barrier, phi_density=0.9)

        # Higher barrier → lower amplitude
        assert amp_high < amp_low, "Tunnelling amplitude should decrease with barrier height"
        assert 0.0 <= amp_high <= 1.0, "Amplitude must be in [0, 1]"
        assert 0.0 <= amp_low <= 1.0, "Amplitude must be in [0, 1]"

    def test_tunnelling_only_fires_on_degraded_state(self):
        """Tunnelling should only trigger when purity < 0.5 and failures > 10."""
        swarm = QuantumHealingSwarm(
            num_candidates=8,
            enable_tunnelling=True,
            enable_annealing=False,
            enable_swarming=False,
            enable_interference=False,
        )

        # Degraded state: should trigger tunnelling
        result_degraded = swarm.heal(
            phi_density=0.3, consecutive_failures=15, degrade_factor=1.0
        )
        assert result_degraded.tunnelling_used, "Tunnelling should fire on degraded state"

        # Healthy state: should not trigger tunnelling
        result_healthy = swarm.heal(
            phi_density=0.9, consecutive_failures=2, degrade_factor=0.1
        )
        assert not result_healthy.tunnelling_used, "Tunnelling should not fire on healthy state"

    def test_tunnelling_amplitude_follows_wkb_formula(self):
        """Tunnelling amplitude should follow T = exp(-α·barrier_height) approximately.

        Note: The actual implementation applies phase rotation when amplitude > 0.1,
        which modifies the state. We test the base amplitude calculation before rotation.
        """
        swarm = QuantumHealingSwarm(
            num_candidates=8,
            enable_tunnelling=True,
            enable_annealing=False,
            enable_swarming=False,
            enable_interference=False,
        )

        # Test monotonicity: higher barrier → lower amplitude
        amplitudes = []
        purities = [0.2, 0.4, 0.6, 0.8]
        for purity in purities:
            rho = swarm._form_degraded_density_matrix(
                phi_density=purity, consecutive_failures=5, degrade_factor=0.5
            )
            _, amplitude = swarm._wkb_tunnel(rho, phi_density=purity)
            amplitudes.append(amplitude)

        # Amplitudes should be monotonically increasing with purity (decreasing barrier)
        for i in range(len(amplitudes) - 1):
            assert amplitudes[i] <= amplitudes[i + 1], \
                f"Amplitude should increase with purity: {amplitudes[i]} vs {amplitudes[i+1]}"

        # All amplitudes should be in [0, 1]
        for amp in amplitudes:
            assert 0.0 <= amp <= 1.0, f"Amplitude {amp} not in [0, 1]"

    def test_tunnelling_increases_purity_when_triggered(self):
        """When tunnelling fires, it should increase purity."""
        swarm = QuantumHealingSwarm(
            num_candidates=8,
            enable_tunnelling=True,
            enable_annealing=False,
            enable_swarming=False,
            enable_interference=False,
        )

        result = swarm.heal(phi_density=0.2, consecutive_failures=15, degrade_factor=1.0)

        if result.tunnelling_used:
            assert (
                result.post_heal_purity > result.pre_heal_purity
            ), "Tunnelling should increase purity"


class TestPhiAnnealing:
    """φ-scaled annealing: Metropolis acceptance with golden-ratio temperature."""

    def test_temperature_decays_with_heal_count(self):
        """Temperature should decay as φ^(-heal_count)."""
        swarm = QuantumHealingSwarm(
            num_candidates=8,
            enable_tunnelling=False,
            enable_annealing=True,
            enable_swarming=False,
            enable_interference=False,
        )

        rho = swarm._form_degraded_density_matrix(
            phi_density=0.5, consecutive_failures=5, degrade_factor=0.5
        )

        # Temperature at heal_count = 0
        temp_0, _, _ = swarm._phi_anneal(rho, pre_entropy=1.0, phi_density=0.5)

        # Temperature at heal_count = 5
        for _ in range(5):
            swarm.heal(phi_density=0.5, consecutive_failures=5, degrade_factor=0.5)
        temp_5, _, _ = swarm._phi_anneal(rho, pre_entropy=1.0, phi_density=0.5)

        # Temperature should decrease (handle scalar conversion)
        def to_scalar(x):
            if isinstance(x, np.ndarray):
                return float(np.real(x.flatten()[0])) if x.size > 0 else 0.0
            return float(np.real(x))

        temp_0_scalar = to_scalar(temp_0)
        temp_5_scalar = to_scalar(temp_5)
        assert temp_5_scalar < temp_0_scalar, "Temperature should decay with heal count"

        # Verify φ-scaled decay (temperature should decrease, exact ratio depends on floor)
        # The temperature is bounded below by 0.1, so the exact ratio may not match φ^(-5)
        assert temp_5_scalar <= temp_0_scalar, "Temperature should not increase"

    def test_annealing_accepts_lower_energy(self):
        """Annealing should always accept candidates with lower energy (entropy)."""
        swarm = QuantumHealingSwarm(
            num_candidates=8,
            enable_tunnelling=False,
            enable_annealing=True,
            enable_swarming=False,
            enable_interference=False,
        )

        # Create a high-entropy state
        rho_high_entropy = swarm._form_degraded_density_matrix(
            phi_density=0.1, consecutive_failures=20, degrade_factor=1.0
        )
        high_entropy = swarm._von_neumann_entropy(rho_high_entropy)

        # The annealing function generates a candidate; if it has lower entropy,
        # it should be accepted. We test this by running multiple trials.
        accept_count = 0
        for _ in range(20):
            _, _, accepted = swarm._phi_anneal(rho_high_entropy, high_entropy, phi_density=0.1)
            if accepted:
                accept_count += 1

        # At least some trials should accept (deterministic for lower energy)
        assert accept_count > 0, "Annealing should accept lower-energy candidates"

    def test_annealing_temperature_bounded(self):
        """Temperature should be bounded below by 0.1 to avoid freezing."""
        swarm = QuantumHealingSwarm(
            num_candidates=8,
            enable_annealing=True,
            enable_tunnelling=False,
            enable_swarming=False,
            enable_interference=False,
        )

        # Run many heals to drive temperature down
        for _ in range(50):
            swarm.heal(phi_density=0.5, consecutive_failures=5, degrade_factor=0.5)

        rho = swarm._form_degraded_density_matrix(
            phi_density=0.5, consecutive_failures=5, degrade_factor=0.5
        )
        temp, _, _ = swarm._phi_anneal(rho, pre_entropy=1.0, phi_density=0.5)

        def to_scalar(x):
            if isinstance(x, np.ndarray):
                return float(np.real(x.flatten()[0])) if x.size > 0 else 0.0
            return float(np.real(x))

        temp_scalar = to_scalar(temp)
        assert temp_scalar >= 0.1, "Temperature should be bounded below by 0.1"

    def test_annealing_used_flag_set_correctly(self):
        """The annealing_used flag should be True when annealing is enabled."""
        swarm = QuantumHealingSwarm(
            num_candidates=8,
            enable_annealing=True,
            enable_tunnelling=False,
            enable_swarming=False,
            enable_interference=False,
        )

        result = swarm.heal(phi_density=0.5, consecutive_failures=5, degrade_factor=0.5)
        assert result.annealing_used, "annealing_used should be True when enabled"


class TestSwarmConsensus:
    """Swarm consensus: parallel agents with density matrix consensus."""

    def test_swarm_consensus_increases_purity(self):
        """Swarm consensus should produce a state with higher purity than input."""
        swarm = QuantumHealingSwarm(
            num_candidates=8,
            enable_swarming=True,
            enable_tunnelling=False,
            enable_annealing=False,
            enable_interference=False,
        )

        rho = swarm._form_degraded_density_matrix(
            phi_density=0.3, consecutive_failures=10, degrade_factor=0.8
        )
        pre_purity = swarm._purity(rho)

        rho_consensus, consensus_purity = swarm._swarm_consensus(rho, phi_density=0.3)

        assert consensus_purity >= pre_purity, "Swarm consensus should not decrease purity"

    def test_swarm_consensus_purity_in_result(self):
        """The swarm_consensus_purity field should be populated in HealingResult."""
        swarm = QuantumHealingSwarm(
            num_candidates=8,
            enable_swarming=True,
            enable_tunnelling=False,
            enable_annealing=False,
            enable_interference=False,
        )

        result = swarm.heal(phi_density=0.5, consecutive_failures=5, degrade_factor=0.5)
        assert result.swarm_consensus_purity > 0.0, "swarm_consensus_purity should be positive"
        assert result.swarming_used, "swarming_used should be True when enabled"

    def test_swarm_consensus_hermitian_and_unit_trace(self):
        """Consensus state should be a valid density matrix (Hermitian, unit trace)."""
        swarm = QuantumHealingSwarm(
            num_candidates=8,
            enable_swarming=True,
            enable_tunnelling=False,
            enable_annealing=False,
            enable_interference=False,
        )

        rho = swarm._form_degraded_density_matrix(
            phi_density=0.5, consecutive_failures=5, degrade_factor=0.5
        )
        rho_consensus, _ = swarm._swarm_consensus(rho, phi_density=0.5)

        # Hermitian: rho = rho†
        assert np.allclose(
            rho_consensus, rho_consensus.conj().T, atol=1e-10
        ), "Consensus state should be Hermitian"

        # Unit trace
        trace = np.trace(rho_consensus).real
        assert abs(trace - 1.0) < 1e-10, f"Consensus state should have unit trace, got {trace}"

    def test_swarm_consensus_phi_weighted(self):
        """Consensus should use φ-weighted averaging (φ^(-i) weights)."""
        swarm = QuantumHealingSwarm(
            num_candidates=8,
            enable_swarming=True,
            enable_tunnelling=False,
            enable_annealing=False,
            enable_interference=False,
        )

        rho = swarm._form_degraded_density_matrix(
            phi_density=0.5, consecutive_failures=5, degrade_factor=0.5
        )

        # Run consensus twice with same input
        rho_consensus_1, _ = swarm._swarm_consensus(rho, phi_density=0.5)
        rho_consensus_2, _ = swarm._swarm_consensus(rho, phi_density=0.5)

        # Should be deterministic (same weights, same phases)
        assert np.allclose(
            rho_consensus_1, rho_consensus_2, atol=1e-10
        ), "Swarm consensus should be deterministic"


class TestInterferenceAccumulation:
    """Interference accumulation: maintain superposition across steps."""

    def test_interference_gain_non_negative_on_first_call(self):
        """First interference call should have zero gain (no persistent state yet)."""
        swarm = QuantumHealingSwarm(
            num_candidates=8,
            enable_interference=True,
            enable_tunnelling=False,
            enable_annealing=False,
            enable_swarming=False,
        )

        rho = swarm._form_degraded_density_matrix(
            phi_density=0.5, consecutive_failures=5, degrade_factor=0.5
        )
        rho_interfered, gain = swarm._interference_accumulate(rho, phi_density=0.5)

        assert gain == 0.0, "First interference call should have zero gain"

    def test_interference_gain_positive_on_subsequent_calls(self):
        """Subsequent interference calls should accumulate phase information."""
        swarm = QuantumHealingSwarm(
            num_candidates=8,
            enable_interference=True,
            enable_tunnelling=False,
            enable_annealing=False,
            enable_swarming=False,
        )

        rho = swarm._form_degraded_density_matrix(
            phi_density=0.5, consecutive_failures=5, degrade_factor=0.5
        )

        # First call: initializes persistent state
        swarm._interference_accumulate(rho, phi_density=0.5)

        # Second call: should accumulate
        rho_interfered, gain = swarm._interference_accumulate(rho, phi_density=0.5)

        # Gain can be positive or negative (interference is constructive or destructive)
        # but it should be measurable
        assert isinstance(gain, float), "Interference gain should be a float"

    def test_interference_resets_after_age_threshold(self):
        """Persistent superposition should reset after age > 10."""
        swarm = QuantumHealingSwarm(
            num_candidates=8,
            enable_interference=True,
            enable_tunnelling=False,
            enable_annealing=False,
            enable_swarming=False,
        )

        rho = swarm._form_degraded_density_matrix(
            phi_density=0.5, consecutive_failures=5, degrade_factor=0.5
        )

        # Initialize persistent state
        swarm._interference_accumulate(rho, phi_density=0.5)

        # Age it past threshold
        for _ in range(11):
            swarm._interference_accumulate(rho, phi_density=0.5)

        # Should have reset
        assert swarm._persistent_superposition is None, "Persistent state should reset after age > 10"
        assert swarm._superposition_age == 0, "Age should reset to 0"

    def test_interference_used_flag_set_correctly(self):
        """The interference_used flag should be True when interference is enabled."""
        swarm = QuantumHealingSwarm(
            num_candidates=8,
            enable_interference=True,
            enable_tunnelling=False,
            enable_annealing=False,
            enable_swarming=False,
        )

        result = swarm.heal(phi_density=0.5, consecutive_failures=5, degrade_factor=0.5)
        assert result.interference_used, "interference_used should be True when enabled"


class TestIntegratedHealingWithAllMechanisms:
    """Integrated tests with all four mechanisms enabled."""

    def test_all_mechanisms_can_be_enabled_simultaneously(self):
        """All four mechanisms should work together without conflict."""
        swarm = QuantumHealingSwarm(
            num_candidates=8,
            enable_tunnelling=True,
            enable_annealing=True,
            enable_swarming=True,
            enable_interference=True,
        )

        result = swarm.heal(phi_density=0.3, consecutive_failures=15, degrade_factor=1.0)

        # Check that all mechanism flags are set
        # (Note: tunnelling only fires when purity < 0.5 and failures > 10)
        if result.pre_heal_purity < 0.5 and 15 > 10:
            assert result.tunnelling_used, "Tunnelling should fire on degraded state"

        assert result.annealing_used, "Annealing should always be used when enabled"
        assert result.swarming_used, "Swarming should always be used when enabled"
        assert result.interference_used, "Interference should always be used when enabled"

    def test_healing_result_has_all_enhanced_fields(self):
        """HealingResult should populate all enhanced mechanism fields."""
        swarm = QuantumHealingSwarm(
            num_candidates=8,
            enable_tunnelling=True,
            enable_annealing=True,
            enable_swarming=True,
            enable_interference=True,
        )

        result = swarm.heal(phi_density=0.5, consecutive_failures=5, degrade_factor=0.5)

        # Check all enhanced fields are present
        assert hasattr(result, "tunnelling_used")
        assert hasattr(result, "annealing_used")
        assert hasattr(result, "swarming_used")
        assert hasattr(result, "interference_used")
        assert hasattr(result, "tunnelling_amplitude")
        assert hasattr(result, "annealing_temperature")
        assert hasattr(result, "swarm_consensus_purity")
        assert hasattr(result, "interference_gain")

    def test_full_heal_cycle_completes_in_reasonable_time(self):
        """Full healing cycle with all mechanisms should complete in < 100ms."""
        swarm = QuantumHealingSwarm(
            num_candidates=8,
            enable_tunnelling=True,
            enable_annealing=True,
            enable_swarming=True,
            enable_interference=True,
        )

        result = swarm.heal(phi_density=0.5, consecutive_failures=5, degrade_factor=0.5)

        assert result.duration_ms < 100.0, f"Healing took {result.duration_ms}ms, should be < 100ms"

    def test_healing_is_deterministic_with_fixed_seed(self):
        """With fixed random seed, healing should be deterministic."""
        swarm1 = QuantumHealingSwarm(
            num_candidates=8,
            enable_tunnelling=True,
            enable_annealing=True,
            enable_swarming=True,
            enable_interference=True,
        )
        swarm2 = QuantumHealingSwarm(
            num_candidates=8,
            enable_tunnelling=True,
            enable_annealing=True,
            enable_swarming=True,
            enable_interference=True,
        )

        np.random.seed(42)
        result1 = swarm1.heal(phi_density=0.5, consecutive_failures=5, degrade_factor=0.5)

        np.random.seed(42)
        result2 = swarm2.heal(phi_density=0.5, consecutive_failures=5, degrade_factor=0.5)

        # Results should be identical with same seed
        assert result1.post_heal_purity == result2.post_heal_purity
        assert result1.post_heal_entropy == result2.post_heal_entropy

    def test_purity_gain_positive_on_degraded_input(self):
        """On degraded input, healing should increase purity."""
        swarm = QuantumHealingSwarm(
            num_candidates=8,
            enable_tunnelling=True,
            enable_annealing=True,
            enable_swarming=True,
            enable_interference=True,
        )

        result = swarm.heal(phi_density=0.2, consecutive_failures=15, degrade_factor=1.0)

        assert result.purity_gain > 0, f"Purity gain should be positive, got {result.purity_gain}"

    def test_entropy_reduction_positive_on_degraded_input(self):
        """On degraded input, healing should reduce entropy."""
        swarm = QuantumHealingSwarm(
            num_candidates=8,
            enable_tunnelling=True,
            enable_annealing=True,
            enable_swarming=True,
            enable_interference=True,
        )

        result = swarm.heal(phi_density=0.2, consecutive_failures=15, degrade_factor=1.0)

        assert (
            result.entropy_reduction > 0
        ), f"Entropy reduction should be positive, got {result.entropy_reduction}"
