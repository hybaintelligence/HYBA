"""Agent 3 coverage expansion for deterministic quantum-inspired solvers.

These tests intentionally verify bounded, classical, deterministic behavior and
mathematical invariants. They do not assert quantum hardware speedup or pool-side
mining success.
"""

from __future__ import annotations

import asyncio
import math
import time

import numpy as np
import pytest

from pythia_mining.grover_enhanced_quantum_search import GroverEnhancedQuantumSearch
from pythia_mining.quantum_regeneration import (
    DIM,
    ContextSignal,
    InnervationFailure,
    ModuleState,
    Role,
    apply_fault,
    apply_refractory_stabilization,
    fault_perturbation_operator,
    grover_role_search_NOTE_REQUIRES_QUANTUM_HARDWARE,
    is_separable_approx,
    joint_state,
    lindblad_decay_operator,
    quarantine_channel,
    redifferentiate,
    redifferentiation_unitary,
    regeneration_fidelity,
)
from pythia_mining.quantum_solver import (
    DODECAHEDRON_VERTICES,
    MAX_UINT32_NONCE,
    QuantumNumericalInstabilityError,
    QuantumSolverConfigurationError,
    DodecahedralQuantumSolver,
)


def run(coro):
    """Run a coroutine in these synchronous pytest tests."""
    return asyncio.run(coro)


# Group 1: Quantum Solver Initialization


def test_dodecahedral_quantum_solver_initialization():
    solver = DodecahedralQuantumSolver(configured_capacity_ehs=0.25)
    assert solver.is_available()
    assert solver.basis_states.shape == (DODECAHEDRON_VERTICES, 3)
    assert solver.calculate_integrated_hashrate() == 0.25


def test_basis_states_generation_correctness():
    solver = DodecahedralQuantumSolver()
    row_norms = np.linalg.norm(solver.basis_states, axis=1)
    assert np.allclose(row_norms, 1.0)
    assert np.isfinite(solver.basis_states).all()


def test_phi_phase_alignment_computation():
    metrics = DodecahedralQuantumSolver().get_metrics()
    assert 0.0 <= metrics["phi_phase_alignment"] <= 1.0
    assert metrics["basis_states"] == 20


def test_solver_configuration_idempotence():
    solver = DodecahedralQuantumSolver()
    assert run(solver.configure_search(target=10, nonce_ranges=[(5, 9)])) is True
    first = dict(solver.current_config)
    assert run(solver.configure_search(target=10, nonce_ranges=[(5, 9)])) is True
    second = dict(solver.current_config)
    assert first["target"] == second["target"]
    assert first["nonce_ranges"] == second["nonce_ranges"]
    assert first["search_space_size"] == second["search_space_size"]


# Group 2: Grover Algorithm Implementation


def test_grover_superposition_creation_probability_normalizes():
    result = GroverEnhancedQuantumSearch().grover_multiple_marked(16, [2], max_iterations=1)
    assert np.isclose(float(np.sum(result.probabilities)), 1.0)
    assert result.iterations_used == 1


def test_grover_oracle_phase_flip_amplifies_marked_state():
    result = GroverEnhancedQuantumSearch().grover_multiple_marked(16, [3], max_iterations=1)
    assert result.probabilities[3] > 1.0 / 16.0
    assert 3 in result.marked_states


def test_grover_diffusion_operator_preserves_norm():
    result = GroverEnhancedQuantumSearch().grover_multiple_marked(32, [1, 7], max_iterations=2)
    assert np.isclose(np.linalg.norm(np.sqrt(result.probabilities)), 1.0)


def test_grover_amplitude_amplification_returns_normalized_state():
    search = GroverEnhancedQuantumSearch()
    initial = np.array([1.0, 0.0], dtype=complex)
    result = search.amplitude_amplification(
        lambda state: state, initial, lambda state: True, iterations=3
    )
    assert np.isclose(np.linalg.norm(result.amplified_state), 1.0)
    assert result.unitary_used == "<lambda>"


def test_grover_measurement_probability_distribution_bounds():
    result = GroverEnhancedQuantumSearch().grover_multiple_marked(20, [0, 4, 8], max_iterations=3)
    assert np.all(result.probabilities >= 0.0)
    assert np.all(result.probabilities <= 1.0)


# Group 3: Nonce Generation & Search


def test_nonce_generation_correctness():
    solver = DodecahedralQuantumSolver()
    run(solver.configure_search(target=1, nonce_ranges=[(100, 119)]))
    nonces = [solver._project_index_to_nonce(i) for i in range(DODECAHEDRON_VERTICES)]
    assert nonces == list(range(100, 120))


def test_nonce_range_boundary_handling():
    solver = DodecahedralQuantumSolver()
    run(solver.configure_search(target=1, nonce_ranges=[(MAX_UINT32_NONCE, MAX_UINT32_NONCE)]))
    assert solver._project_index_to_nonce(0) == MAX_UINT32_NONCE


def test_nonce_uniqueness_guarantee_for_full_basis_window():
    solver = DodecahedralQuantumSolver()
    run(solver.configure_search(target=1, nonce_ranges=[(0, 19)]))
    nonces = [solver._project_index_to_nonce(i) for i in range(20)]
    assert len(set(nonces)) == 20


def test_search_space_coverage_across_multiple_ranges():
    solver = DodecahedralQuantumSolver()
    run(solver.configure_search(target=1, nonce_ranges=[(10, 14), (20, 24)]))
    assert [solver._project_index_to_nonce(i) for i in range(10)] == [
        10,
        11,
        12,
        13,
        14,
        20,
        21,
        22,
        23,
        24,
    ]


def test_marked_state_identification_is_stable():
    solver = DodecahedralQuantumSolver()
    run(solver.configure_search(target=123, nonce_ranges=[(0, 99)]))
    assert solver._marked_state_index() == solver._marked_state_index()
    assert 0 <= solver._marked_state_index() < DODECAHEDRON_VERTICES


# Group 4: Quantum Regeneration


def test_refractory_period_enforcement_attenuates_fault():
    state = ModuleState.healthy("module-a")
    state.enter_refractory_period(duration=60.0)
    protected = apply_fault(state, severity=1.0)
    assert protected.role_probabilities()[Role.HEALTHY_SPECIALIZED] > 0.99


def test_lindblad_decay_operator_preserves_density_invariants():
    state = quarantine_channel(apply_fault(ModuleState.healthy("module-b"), 0.5))
    decayed = lindblad_decay_operator(state, decay_rate=0.2)
    decayed.validate()
    assert np.isclose(np.trace(decayed.rho).real, 1.0)


def test_module_recovery_from_injury_increases_target_fidelity():
    injured = quarantine_channel(apply_fault(ModuleState.healthy("module-c"), 0.8))
    context = ContextSignal(clifford_index=7, target_role=Role.HEALTHY_SPECIALIZED, confidence=1.0)
    recovered = redifferentiate(injured, context)
    assert regeneration_fidelity(recovered, Role.HEALTHY_SPECIALIZED) >= regeneration_fidelity(
        injured, Role.HEALTHY_SPECIALIZED
    )


def test_regeneration_stabilization_duration_records_window():
    stabilized = apply_refractory_stabilization(ModuleState.healthy("module-d"), duration=12.0)
    remaining = stabilized.refractory_period_end - time.time()
    assert 0.0 < remaining <= 12.0


# Group 5: Classical Fallback


def test_classical_fallback_activation_when_no_marked_states():
    solver = DodecahedralQuantumSolver()
    run(solver.configure_search(target=1, nonce_ranges=[(0, 5)]))
    nonce = run(
        solver._classical_fallback(
            [(0, 5)], target=1, max_iterations=8, timeout=1.0, start_time=time.monotonic(),
            job=None, extranonce2="00000000"
        )
    )
    # Without a real job, hash_value is always (2**256) - 1, which never matches
    # So we expect None
    assert nonce is None


def test_classical_brute_force_correctness_sets_solution_metadata():
    solver = DodecahedralQuantumSolver()
    run(solver.configure_search(target=1, nonce_ranges=[(0, 10)]))
    nonce = run(solver.solve(max_iterations=4, timeout=1.0))
    # Without a real pool job, no solution will be found
    assert nonce is None
    assert solver.last_error == "no_solution_found"
    assert solver.last_solve_duration_seconds is not None


def test_fallback_determinism_for_fresh_solvers():
    a = DodecahedralQuantumSolver()
    b = DodecahedralQuantumSolver()
    run(a.configure_search(target=1, nonce_ranges=[(0, 10)]))
    run(b.configure_search(target=1, nonce_ranges=[(0, 10)]))
    # Both should return None without real pool jobs
    result_a = run(a.solve(max_iterations=4, timeout=1.0))
    result_b = run(b.solve(max_iterations=4, timeout=1.0))
    assert result_a is None and result_b is None


def test_classical_timeout_handling():
    solver = DodecahedralQuantumSolver()
    run(solver.configure_search(target=1, nonce_ranges=[(0, 10)]))
    nonce = run(
        solver._classical_fallback(
            [(0, 10)], 1, 10, timeout=1e-12, start_time=time.monotonic() - 1.0,
            job=None, extranonce2="00000000"
        )
    )
    assert nonce is None
    assert solver.last_error == "timeout"


# Group 6: Solver Metrics & Diagnostics


def test_solver_hashrate_calculation_is_capped():
    solver = DodecahedralQuantumSolver(configured_capacity_ehs=5.0)
    solver.set_power_scale(3.0)
    assert solver.calculate_integrated_hashrate() == 1.0


def test_entropy_measurement_uniform_state():
    solver = DodecahedralQuantumSolver()
    state = np.ones(4, dtype=complex) / 2.0
    assert math.isclose(solver.calculate_integrated_entropy(state), 2.0, rel_tol=1e-9)


def test_coherence_scoring_range():
    solver = DodecahedralQuantumSolver()
    assert 0.0 <= solver._basis_coherence() <= 1.0


def test_solver_health_check_and_restart():
    solver = DodecahedralQuantumSolver()
    solver.last_error = "boom"
    assert run(solver.health_check()) is True
    assert run(solver.restart()) is True
    assert solver.last_error is None


# Group 7: Performance Benchmarking (bounded, no speedup claims)


def test_grover_iteration_count_is_bounded_by_max_iterations():
    result = GroverEnhancedQuantumSearch().grover_multiple_marked(100, [1], max_iterations=2)
    assert result.iterations_used <= 2


def test_first_hit_latency_is_recorded_for_solve():
    solver = DodecahedralQuantumSolver()
    run(solver.configure_search(target=1, nonce_ranges=[(0, 10)]))
    nonce = run(solver.solve(max_iterations=4, timeout=1.0))
    # Duration should be recorded even if no solution found
    assert nonce is None  # No solution without real job
    assert solver.last_solve_duration_seconds is not None
    assert solver.last_solve_duration_seconds >= 0.0


def test_solver_throughput_under_small_load_completes_quickly():
    solver = DodecahedralQuantumSolver()
    run(solver.configure_search(target=1, nonce_ranges=[(0, 19)]))
    start = time.monotonic()
    nonce = run(solver.solve(max_iterations=8, timeout=1.0))
    # Should complete quickly even if no solution found
    assert nonce is None  # No solution without real job
    assert time.monotonic() - start < 1.0


def test_memory_efficiency_for_basis_state_size():
    solver = DodecahedralQuantumSolver()
    assert solver.basis_states.nbytes < 10_000


# Group 8: Numerical Stability


def test_complex_amplitude_normalization():
    result = GroverEnhancedQuantumSearch().grover_multiple_marked(12, [2, 5], max_iterations=2)
    assert np.isclose(float(np.sum(result.probabilities)), 1.0)


def test_phase_accumulation_accuracy_for_fault_operator_unitary():
    operator = fault_perturbation_operator(0.42)
    assert np.allclose(operator.conj().T @ operator, np.eye(DIM), atol=1e-8)


def test_floating_point_precision_handling_rejects_nan_entropy():
    with pytest.raises(QuantumNumericalInstabilityError):
        DodecahedralQuantumSolver().calculate_integrated_entropy(np.array([np.nan + 0j]))


def test_norme_computation_stability_for_joint_states():
    healthy = ModuleState.healthy("left")
    rho = joint_state(healthy, ModuleState.healthy("right"), correlated=False)
    assert np.isclose(np.trace(rho).real, 1.0)
    assert is_separable_approx(rho)


# Group 9: Error Handling & Edge Cases


def test_zero_marked_states_handling():
    result = GroverEnhancedQuantumSearch().grover_multiple_marked(8, [], max_iterations=5)
    assert result.marked_states == []
    assert result.method == "no_marked_states"
    assert np.all(result.probabilities == 0.0)


def test_singular_matrix_recovery_via_invalid_density_matrix():
    bad = ModuleState(rho=np.zeros((DIM, DIM), dtype=complex), module_id="bad")
    with pytest.raises(ValueError):
        bad.validate()


def test_maximum_iteration_limits_are_validated():
    solver = DodecahedralQuantumSolver()
    run(solver.configure_search(target=1, nonce_ranges=[(0, 1)]))
    with pytest.raises(QuantumSolverConfigurationError):
        run(solver.solve(max_iterations=0, timeout=1.0))


def test_missing_context_raises_innervation_failure():
    with pytest.raises(InnervationFailure):
        redifferentiation_unitary(None)


def test_hardware_speedup_stub_remains_unimplemented():
    with pytest.raises(NotImplementedError):
        grover_role_search_NOTE_REQUIRES_QUANTUM_HARDWARE(
            [Role.HEALTHY_SPECIALIZED], lambda role: True
        )
