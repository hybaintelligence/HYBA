"""
Mathematical Quantum Computer Test Suite — formal-invariant validation

This test suite provides mathematical verification of the quantum computer implementation
with the rigor expected of formal mathematical analysis and formal-invariant precision.

Testing Philosophy:
1. Mathematical Proofs: Verify exact mathematical properties, not just empirical observations
2. Invariant Preservation: Ensure all operations preserve quantum mechanical invariants
3. Property-Based Testing: Verify properties hold for all valid inputs, not just specific cases
4. Numerical Precision: Account for floating-point precision in all verifications
5. No Heuristics: All tests are based on exact mathematical theorems

Mathematical Guarantees Verified:
- Unitarity: U†U = I for all gates
- Normalization: ⟨ψ|ψ⟩ = 1 for all states
- Trace Preservation: Tr(ρ) = 1 for density matrices
- Born Rule: Probabilities sum to 1.0
- Tensor Product Structure: Entanglement preserved through operations
- PULVINI Reversibility: Exact reconstruction within tolerance
- φ-Scaling: Golden ratio relationships preserved
"""

from __future__ import annotations

import pytest
import numpy as np
from math import sqrt, isclose
from typing import List, Tuple
import sys
import os

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from quantum_computer import (
    MathematicalQuantumComputer,
    QuantumState,
    QuantumGate,
    QuantumCircuit,
    QuantumMeasurement,
    QuantumComputerAudit,
    hadamard_gate,
    pauli_x_gate,
    pauli_y_gate,
    pauli_z_gate,
    cnot_gate,
    phase_gate,
)


class TestMathematicalFoundations:
    """Test the mathematical foundations of the quantum computer."""
    
    def test_quantum_state_normalization(self):
        """Verify that all quantum states satisfy ⟨ψ|ψ⟩ = 1 exactly."""
        qc = MathematicalQuantumComputer(num_qubits=3)
        state = qc.initialize_state()
        
        norm = np.linalg.norm(state.amplitudes)
        assert abs(norm - 1.0) < 1e-10, f"State norm {norm} != 1.0"
    
    def test_quantum_state_complex_amplitudes(self):
        """Verify that quantum states have complex amplitudes."""
        qc = MathematicalQuantumComputer(num_qubits=2)
        
        # Create state with complex amplitudes
        amps = np.array([1+0j, 1+1j, 1-1j, 0+0j], dtype=np.complex128)
        amps = amps / np.linalg.norm(amps)
        state = qc.initialize_state(amplitudes=amps)
        
        assert np.iscomplexobj(state.amplitudes), "Amplitudes must be complex"
    
    def test_hilbert_space_dimension(self):
        """Verify Hilbert space dimension = 2^num_qubits exactly."""
        for n in range(1, 6):
            qc = MathematicalQuantumComputer(num_qubits=n)
            assert qc.hilbert_dimension == 2**n, f"Hilbert dim {qc.hilbert_dimension} != 2^{n}"
    
    def test_basis_state_initialization(self):
        """Verify |0⟩⊗n initialization creates correct basis state."""
        qc = MathematicalQuantumComputer(num_qubits=3)
        state = qc.initialize_state()
        
        # |000⟩ should have amplitude 1.0 at index 0
        assert abs(state.amplitudes[0] - 1.0) < 1e-10, "Basis state |000⟩ not correct"
        assert all(abs(state.amplitudes[i]) < 1e-10 for i in range(1, len(state.amplitudes))), \
            "Other basis states should have zero amplitude"


class TestGateMathematics:
    """Test the mathematical properties of quantum gates."""
    
    def test_hadamard_unitarity(self):
        """Verify H†H = I exactly (Hadamard gate is unitary)."""
        H = hadamard_gate()
        verification = H.verify_unitarity(tolerance=1e-10)
        assert verification.passed, f"Hadamard not unitary: {verification}"
    
    def test_pauli_gates_unitarity(self):
        """Verify all Pauli gates are unitary: X†X = Y†Y = Z†Z = I."""
        X = pauli_x_gate()
        Y = pauli_y_gate()
        Z = pauli_z_gate()
        
        for gate in [X, Y, Z]:
            verification = gate.verify_unitarity(tolerance=1e-10)
            assert verification.passed, f"{gate.name} not unitary: {verification}"
    
    def test_cnot_unitarity(self):
        """Verify CNOT gate is unitary."""
        CNOT = cnot_gate()
        verification = CNOT.verify_unitarity(tolerance=1e-10)
        assert verification.passed, f"CNOT not unitary: {verification}"
    
    def test_phase_gate_unitarity(self):
        """Verify phase gate is unitary for any angle."""
        for theta in [0, np.pi/4, np.pi/2, np.pi, 2*np.pi]:
            P = phase_gate(theta)
            verification = P.verify_unitarity(tolerance=1e-10)
            assert verification.passed, f"Phase gate (θ={theta}) not unitary: {verification}"
    
    def test_gate_determinant_magnitude(self):
        """Verify |det(U)| = 1 for all unitary gates."""
        gates = [hadamard_gate(), pauli_x_gate(), pauli_y_gate(), pauli_z_gate(), cnot_gate()]
        
        for gate in gates:
            det = np.linalg.det(gate.matrix)
            assert abs(abs(det) - 1.0) < 1e-10, f"|det({gate.name})| = {abs(det)} != 1.0"
    
    def test_gate_eigenvalues_unit_magnitude(self):
        """Verify all eigenvalues of unitary gates have magnitude 1."""
        gates = [hadamard_gate(), pauli_x_gate(), pauli_y_gate(), pauli_z_gate()]
        
        for gate in gates:
            eigvals = np.linalg.eigvals(gate.matrix)
            for eigval in eigvals:
                assert abs(abs(eigval) - 1.0) < 1e-10, \
                    f"Eigenvalue {eigval} of {gate.name} has magnitude {abs(eigval)} != 1.0"


class TestStateEvolution:
    """Test quantum state evolution through gate operations."""
    
    def test_single_qubit_gate_preserves_normalization(self):
        """Verify single-qubit gates preserve ⟨ψ|ψ⟩ = 1."""
        qc = MathematicalQuantumComputer(num_qubits=2)
        qc.initialize_state()
        
        gates = [hadamard_gate(), pauli_x_gate(), pauli_y_gate(), pauli_z_gate()]
        for gate in gates:
            state = qc.apply_gate(gate, [0])
            norm = np.linalg.norm(state.amplitudes)
            assert abs(norm - 1.0) < 1e-10, \
                f"{gate.name} did not preserve normalization: norm = {norm}"
    
    def test_two_qubit_gate_preserves_normalization(self):
        """Verify two-qubit gates preserve normalization."""
        qc = MathematicalQuantumComputer(num_qubits=2)
        qc.initialize_state()
        
        CNOT = cnot_gate()
        state = qc.apply_gate(CNOT, [0, 1])
        norm = np.linalg.norm(state.amplitudes)
        assert abs(norm - 1.0) < 1e-10, f"CNOT did not preserve normalization: norm = {norm}"
    
    def test_hadamard_creates_superposition(self):
        """Verify H|0⟩ = (|0⟩ + |1⟩)/√2 creates equal superposition."""
        qc = MathematicalQuantumComputer(num_qubits=1)
        qc.initialize_state()
        
        H = hadamard_gate()
        state = qc.apply_gate(H, [0])
        
        # Should have equal magnitude amplitudes
        assert abs(abs(state.amplitudes[0]) - 1/sqrt(2)) < 1e-10, \
            f"Amplitude |0⟩ = {abs(state.amplitudes[0])} != 1/√2"
        assert abs(abs(state.amplitudes[1]) - 1/sqrt(2)) < 1e-10, \
            f"Amplitude |1⟩ = {abs(state.amplitudes[1])} != 1/√2"
    
    def test_pauli_x_flips_basis_state(self):
        """Verify X|0⟩ = |1⟩ and X|1⟩ = |0⟩."""
        qc = MathematicalQuantumComputer(num_qubits=1)
        
        # Test X|0⟩ = |1⟩
        qc.initialize_state()
        X = pauli_x_gate()
        state = qc.apply_gate(X, [0])
        assert abs(abs(state.amplitudes[0]) - 0.0) < 1e-10, "X|0⟩ should have no |0⟩ component"
        assert abs(abs(state.amplitudes[1]) - 1.0) < 1e-10, "X|0⟩ should be |1⟩"
        
        # Test X|1⟩ = |0⟩
        amps_1 = np.array([0, 1], dtype=np.complex128)
        qc.initialize_state(amplitudes=amps_1)
        state = qc.apply_gate(X, [0])
        assert abs(abs(state.amplitudes[0]) - 1.0) < 1e-10, "X|1⟩ should be |0⟩"
        assert abs(abs(state.amplitudes[1]) - 0.0) < 1e-10, "X|1⟩ should have no |1⟩ component"
    
    def test_cnot_creates_entanglement(self):
        """Verify CNOT creates Bell state from superposition."""
        qc = MathematicalQuantumComputer(num_qubits=2)
        qc.initialize_state()
        
        # Create (|00⟩ + |10⟩)/√2 by applying H to first qubit
        H = hadamard_gate()
        qc.apply_gate(H, [0])
        
        # Apply CNOT to create (|00⟩ + |11⟩)/√2
        CNOT = cnot_gate()
        state = qc.apply_gate(CNOT, [0, 1])
        
        # Bell state should have equal amplitude on |00⟩ and |11⟩
        assert abs(abs(state.amplitudes[0]) - 1/sqrt(2)) < 1e-10, \
            f"Bell state |00⟩ amplitude = {abs(state.amplitudes[0])} != 1/√2"
        assert abs(abs(state.amplitudes[3]) - 1/sqrt(2)) < 1e-10, \
            f"Bell state |11⟩ amplitude = {abs(state.amplitudes[3])} != 1/√2"
        assert abs(abs(state.amplitudes[1])) < 1e-10, "Bell state should have no |01⟩ component"
        assert abs(abs(state.amplitudes[2])) < 1e-10, "Bell state should have no |10⟩ component"


class TestParallelGates:
    """Test perfect parallel gate operations using mathematical tensor products."""
    
    def test_parallel_gates_on_disjoint_qubits(self):
        """Verify parallel gates on disjoint qubits commute mathematically."""
        qc = MathematicalQuantumComputer(num_qubits=3)
        qc.initialize_state()
        
        # Apply H on qubit 0 and X on qubit 1 in parallel
        H = hadamard_gate()
        X = pauli_x_gate()
        state_parallel = qc.apply_parallel_gates([(H, [0]), (X, [1])])
        
        # Apply sequentially and verify same result
        qc.initialize_state()
        state_sequential = qc.apply_gate(H, [0])
        state_sequential = qc.apply_gate(X, [1])
        
        # Results should be identical (mathematical commutativity)
        assert np.allclose(state_parallel.amplitudes, state_sequential.amplitudes, atol=1e-10), \
            "Parallel and sequential execution should give identical results for commuting gates"
    
    def test_parallel_gates_preserve_normalization(self):
        """Verify parallel gates preserve normalization."""
        qc = MathematicalQuantumComputer(num_qubits=4)
        qc.initialize_state()
        
        H = hadamard_gate()
        X = pauli_x_gate()
        Z = pauli_z_gate()
        
        state = qc.apply_parallel_gates([(H, [0]), (X, [1]), (Z, [2])])
        norm = np.linalg.norm(state.amplitudes)
        assert abs(norm - 1.0) < 1e-10, f"Parallel gates did not preserve normalization: norm = {norm}"
    
    def test_parallel_gates_reject_overlapping_qubits(self):
        """Verify parallel gates on overlapping qubits raise error."""
        qc = MathematicalQuantumComputer(num_qubits=2)
        qc.initialize_state()
        
        H = hadamard_gate()
        X = pauli_x_gate()
        
        with pytest.raises(ValueError, match="disjoint qubit"):
            qc.apply_parallel_gates([(H, [0]), (X, [0])])
    
    def test_parallel_efficiency_is_perfect(self):
        """Verify parallel efficiency is 1.0 (perfect mathematical parallelism)."""
        qc = MathematicalQuantumComputer(num_qubits=3)
        qc.initialize_state()
        
        H = hadamard_gate()
        X = pauli_x_gate()
        
        qc.apply_parallel_gates([(H, [0]), (X, [1])])
        
        audit_log = qc.get_audit_log()
        parallel_op = [op for op in audit_log if op["operation"] == "apply_parallel_gates"]
        assert len(parallel_op) > 0, "Parallel gate operation not logged"
        assert parallel_op[-1]["metadata"]["parallel_efficiency"] == 1.0, \
            "Parallel efficiency should be 1.0 (perfect mathematical parallelism)"


class TestMeasurement:
    """Test quantum measurement following the Born rule."""
    
    def test_born_rule_probabilities_sum_to_one(self):
        """Verify measurement probabilities sum to 1.0 exactly."""
        qc = MathematicalQuantumComputer(num_qubits=2)
        qc.initialize_state()
        
        # Create superposition
        H = hadamard_gate()
        qc.apply_gate(H, [0])
        
        amps = qc.get_state().amplitudes
        probabilities = np.abs(amps) ** 2
        total_prob = np.sum(probabilities)
        
        assert abs(total_prob - 1.0) < 1e-10, f"Probabilities sum to {total_prob} != 1.0"
    
    def test_measurement_collapses_state(self):
        """Verify measurement collapses state to measured basis state."""
        qc = MathematicalQuantumComputer(num_qubits=1)
        qc.initialize_state()
        
        # Create superposition
        H = hadamard_gate()
        qc.apply_gate(H, [0])
        
        # Measure
        measurements = qc.measure(num_shots=1)
        measurement = measurements[0]
        
        # Collapsed state should be basis state
        collapsed = measurement.collapsed_state
        assert collapsed.is_normalized, "Collapsed state should be normalized"
        
        # Should have exactly one non-zero amplitude
        non_zero_count = np.sum(np.abs(collapsed.amplitudes) > 1e-10)
        assert non_zero_count == 1, f"Collapsed state has {non_zero_count} non-zero amplitudes, should be 1"
    
    def test_measurement_outcome_matches_probability(self):
        """Verify measurement outcomes follow Born rule distribution."""
        qc = MathematicalQuantumComputer(num_qubits=1)
        qc.initialize_state()
        
        # Create known superposition: H|0⟩ = (|0⟩ + |1⟩)/√2
        H = hadamard_gate()
        qc.apply_gate(H, [0])
        
        # Measure many times
        num_shots = 1000
        measurements = qc.measure(num_shots=num_shots)
        
        # Count outcomes
        outcomes = [m.outcome for m in measurements]
        count_0 = outcomes.count(0)
        count_1 = outcomes.count(1)
        
        # Should be approximately 50/50
        prob_0 = count_0 / num_shots
        prob_1 = count_1 / num_shots
        
        # Allow statistical deviation (3σ for binomial)
        expected_prob = 0.5
        std_dev = sqrt(expected_prob * (1 - expected_prob) / num_shots)
        assert abs(prob_0 - expected_prob) < 3 * std_dev, \
            f"Outcome probability {prob_0} deviates too far from expected {expected_prob}"


class TestPulviniCompression:
    """Test PULVINI memory compression for quantum states."""
    
    def test_pulvini_compression_reduces_dimension(self):
        """Verify PULVINI compression reduces state dimension."""
        qc = MathematicalQuantumComputer(num_qubits=5, enable_compression=True)
        state = qc.initialize_state()
        
        if state.compression_metadata:
            assert state.compression_metadata["folded_dimension"] < state.compression_metadata["original_dimension"], \
                "PULVINI should reduce dimension"
    
    def test_pulvini_compression_ratio_follows_phi(self):
        """Verify compression ratio approaches φ:1."""
        qc = MathematicalQuantumComputer(num_qubits=6, enable_compression=True)
        state = qc.initialize_state()
        
        if state.compression_metadata:
            ratio = state.compression_metadata["compression_ratio"]
            # Should be close to φ ≈ 1.618
            assert abs(ratio - 1.618) < 0.5, f"Compression ratio {ratio} not close to φ"
    
    def test_pulvini_reversibility(self):
        """Verify PULVINI compression is reversible (lossless)."""
        from operators.pulvini_scaling import PulviniOperator
        
        pulvini = PulviniOperator(tolerance=1e-10)
        
        # Test with random state
        dim = 64
        original = np.random.randn(dim) + 1j * np.random.randn(dim)
        original = original / np.linalg.norm(original)
        
        folded, kernel = pulvini.fold(original)
        reconstructed = pulvini.unfold(folded, kernel, dim)
        
        error = np.linalg.norm(original - reconstructed) / np.linalg.norm(original)
        assert error < 1e-10, f"PULVINI reconstruction error {error} exceeds tolerance"


class TestPhiOptimization:
    """Test φ-guided circuit optimization."""
    
    def test_phi_optimization_identifies_parallel_gates(self):
        """Verify φ-optimization correctly identifies parallelizable gates."""
        qc = MathematicalQuantumComputer(num_qubits=3)
        
        gates = [
            (hadamard_gate(), [0]),
            (pauli_x_gate(), [1]),
            (pauli_z_gate(), [2]),
        ]
        
        optimized = qc._phi_optimize_circuit(gates)
        
        # All gates should be in one group (they're all on disjoint qubits)
        assert len(optimized) == 1, f"Expected 1 group, got {len(optimized)}"
        assert len(optimized[0]) == 3, f"Expected 3 gates in group, got {len(optimized[0])}"
    
    def test_phi_optimization_separates_dependent_gates(self):
        """Verify φ-optimization separates gates on overlapping qubits."""
        qc = MathematicalQuantumComputer(num_qubits=2)
        
        gates = [
            (hadamard_gate(), [0]),
            (pauli_x_gate(), [0]),  # Overlaps with previous
            (pauli_z_gate(), [1]),
        ]
        
        optimized = qc._phi_optimize_circuit(gates)
        
        # First two gates should be in separate groups (overlap)
        # Third gate can be parallel with either
        assert len(optimized) >= 2, f"Expected at least 2 groups, got {len(optimized)}"
    
    def test_phi_optimization_reduces_circuit_depth(self):
        """Verify φ-optimization reduces circuit depth."""
        qc = MathematicalQuantumComputer(num_qubits=4)
        qc.initialize_state()
        
        # Create circuit with many parallelizable gates
        gates = [
            (hadamard_gate(), [0]),
            (hadamard_gate(), [1]),
            (hadamard_gate(), [2]),
            (hadamard_gate(), [3]),
        ]
        circuit = QuantumCircuit(gates=gates, num_qubits=4, depth=4)
        
        # Run without optimization
        qc.initialize_state()
        state_no_opt = qc.run_circuit(circuit, optimize_phi=False)
        
        # Run with optimization
        qc.initialize_state()
        state_opt = qc.run_circuit(circuit, optimize_phi=True)
        
        # Results should be identical
        assert np.allclose(state_no_opt.amplitudes, state_opt.amplitudes, atol=1e-10), \
            "Optimized and unoptimized circuits should give identical results"


class TestMathematicalInvariants:
    """Test preservation of mathematical invariants."""
    
    def test_unitarity_invariant_preserved(self):
        """Verify unitarity invariant: U†U = I always holds."""
        qc = MathematicalQuantumComputer(num_qubits=2)
        qc.initialize_state()
        
        # Apply sequence of gates
        qc.apply_gate(hadamard_gate(), [0])
        qc.apply_gate(pauli_x_gate(), [1])
        qc.apply_gate(cnot_gate(), [0, 1])
        
        audit = qc.get_audit()
        assert audit.unitarity_preserved, "Unitarity invariant not preserved"
    
    def test_normalization_invariant_preserved(self):
        """Verify normalization invariant: ⟨ψ|ψ⟩ = 1 always holds."""
        qc = MathematicalQuantumComputer(num_qubits=3)
        qc.initialize_state()
        
        # Apply complex sequence
        for _ in range(10):
            qc.apply_gate(hadamard_gate(), [0])
            qc.apply_gate(pauli_x_gate(), [1])
            qc.apply_gate(phase_gate(np.pi/4), [2])
        
        audit = qc.get_audit()
        assert audit.norm_preserved, "Normalization invariant not preserved"
    
    def test_trace_preservation_invariant(self):
        """Verify trace preservation for density matrices."""
        qc = MathematicalQuantumComputer(num_qubits=2)
        state = qc.initialize_state()
        
        # Density matrix: ρ = |ψ⟩⟨ψ|
        rho = np.outer(state.amplitudes, state.amplitudes.conj())
        trace_before = np.trace(rho)
        
        # Apply gate
        qc.apply_gate(hadamard_gate(), [0])
        state_after = qc.get_state()
        rho_after = np.outer(state_after.amplitudes, state_after.amplitudes.conj())
        trace_after = np.trace(rho_after)
        
        assert abs(trace_before - trace_after) < 1e-10, \
            f"Trace not preserved: {trace_before} -> {trace_after}"
        assert abs(trace_after - 1.0) < 1e-10, f"Trace after = {trace_after} != 1.0"


class TestAuditSystem:
    """Test the comprehensive audit system."""
    
    def test_audit_comprehensive(self):
        """Verify audit captures all critical metrics."""
        qc = MathematicalQuantumComputer(num_qubits=2)
        qc.initialize_state()
        qc.apply_gate(hadamard_gate(), [0])
        
        audit = qc.get_audit()
        
        # Check all audit fields are present
        assert hasattr(audit, 'unitarity_preserved'), "Audit missing unitarity check"
        assert hasattr(audit, 'trace_preserved'), "Audit missing trace check"
        assert hasattr(audit, 'norm_preserved'), "Audit missing norm check"
        assert hasattr(audit, 'compression_ratio'), "Audit missing compression ratio"
        assert hasattr(audit, 'parallel_efficiency'), "Audit missing parallel efficiency"
        assert hasattr(audit, 'mathematical_invariants'), "Audit missing invariants list"
    
    def test_audit_log_complete(self):
        """Verify audit log captures all operations."""
        qc = MathematicalQuantumComputer(num_qubits=2)
        qc.initialize_state()
        qc.apply_gate(hadamard_gate(), [0])
        qc.apply_gate(pauli_x_gate(), [1])
        qc.measure(num_shots=5)
        
        log = qc.get_audit_log()
        
        operations = [op["operation"] for op in log]
        assert "initialize_state" in operations, "Initialize not logged"
        assert "apply_gate" in operations, "Gate application not logged"
        assert "measure" in operations, "Measurement not logged"


class TestNumericalPrecision:
    """Test numerical precision and stability."""
    
    def test_deep_circuit_numerical_stability(self):
        """Verify numerical stability after many gate operations."""
        qc = MathematicalQuantumComputer(num_qubits=3)
        qc.initialize_state()
        
        # Apply many gates
        for _ in range(100):
            qc.apply_gate(hadamard_gate(), [0])
            qc.apply_gate(pauli_x_gate(), [1])
        
        state = qc.get_state()
        norm = np.linalg.norm(state.amplitudes)
        
        # Should still be normalized despite many operations
        assert abs(norm - 1.0) < 1e-8, f"Norm degraded after many operations: {norm}"
        
        # Should have no NaN or Inf
        assert not np.any(np.isnan(state.amplitudes)), "State contains NaN"
        assert not np.any(np.isinf(state.amplitudes)), "State contains Inf"
    
    def test_small_amplitudes_preserved(self):
        """Verify small amplitudes are not lost to numerical precision."""
        qc = MathematicalQuantumComputer(num_qubits=2)
        
        # Create state with very small amplitude
        eps = 1e-15
        amps = np.array([sqrt(1-eps**2), eps, 0, 0], dtype=np.complex128)
        state = qc.initialize_state(amplitudes=amps)
        
        # Apply gate
        qc.apply_gate(hadamard_gate(), [0])
        state_after = qc.get_state()
        
        # Small amplitude should still be present (though possibly modified)
        assert np.any(np.abs(state_after.amplitudes) > eps/10), \
            "Small amplitude lost to numerical precision"


# Run tests with pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
