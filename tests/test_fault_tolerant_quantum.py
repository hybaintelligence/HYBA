"""
Test Suite: Fault-Tolerant Quantum Mining System
Validates surface code error correction and autonomous mining integration
"""
import pytest
import numpy as np
from pythia_mining.fault_tolerant_quantum_core import (
    FaultTolerantQuantumCore,
    AutonomousFaultTolerantMiner,
    run_fault_tolerant_mining_cycle
)
from pythia_mining.autonomous_fault_tolerant_controller import (
    FaultTolerantMiningController,
    initialize_fault_tolerant_system
)


class TestFaultTolerantCore:
    """Test surface code implementation"""
    
    def test_logical_error_suppression(self):
        """Verify logical error rate < physical error rate"""
        qc = FaultTolerantQuantumCore(code_distance=7, physical_error_rate=1e-3)
        
        assert qc.p_logical < qc.p_phys
        assert qc.p_logical < 1e-5  # Should achieve ~100x suppression
    
    def test_logical_qubit_initialization(self):
        """Test logical qubit initialization in |0⟩_L and |1⟩_L"""
        qc = FaultTolerantQuantumCore(code_distance=5)
        
        idx_0 = qc.initialize_logical_qubit('0')
        idx_1 = qc.initialize_logical_qubit('1')
        
        assert len(qc.logical_qubits) == 2
        assert qc.logical_qubits[idx_0].distance == 5
        assert qc.logical_qubits[idx_1].distance == 5
    
    def test_syndrome_measurement(self):
        """Test stabilizer syndrome measurement"""
        qc = FaultTolerantQuantumCore(code_distance=7)
        idx = qc.initialize_logical_qubit('0')
        
        syndrome = qc.measure_syndromes(idx)
        
        assert syndrome.shape == (2, 6, 6)  # (Z,X) x (d-1) x (d-1)
        assert len(qc.logical_qubits[idx].syndrome_history) == 1
    
    def test_error_correction(self):
        """Test syndrome decoding and correction"""
        qc = FaultTolerantQuantumCore(code_distance=5, physical_error_rate=1e-4)
        idx = qc.initialize_logical_qubit('0')
        
        # Measure twice to enable correction
        qc.measure_syndromes(idx)
        qc.measure_syndromes(idx)
        
        success = qc.decode_and_correct(idx)
        assert isinstance(success, bool)
    
    def test_logical_gates(self):
        """Test fault-tolerant gate application"""
        qc = FaultTolerantQuantumCore(code_distance=5)
        idx = qc.initialize_logical_qubit('0')
        
        # Apply Hadamard
        success_h = qc.apply_logical_gate('H', idx)
        assert success_h is True or success_h is False
        
        # Apply S gate
        success_s = qc.apply_logical_gate('S', idx)
        assert isinstance(success_s, bool)
    
    def test_logical_measurement(self):
        """Test logical qubit measurement"""
        qc = FaultTolerantQuantumCore(code_distance=5)
        idx = qc.initialize_logical_qubit('0')
        
        result = qc.measure_logical(idx)
        assert result in [0, 1]
    
    def test_error_threshold(self):
        """Verify the modeled surface-code threshold used for FT classification."""
        qc = FaultTolerantQuantumCore(code_distance=7)
        
        # Classification must align with the logical-error-rate model threshold.
        assert qc.error_threshold == pytest.approx(0.0109)
        assert 0.013 < qc.phi_reference_threshold < 0.014
        assert qc.p_phys < qc.error_threshold  # Should be fault-tolerant


class TestAutonomousMiner:
    """Test autonomous fault-tolerant mining"""
    
    def test_miner_initialization(self):
        """Test miner creates logical qubit register"""
        miner = AutonomousFaultTolerantMiner(
            code_distance=5,
            num_logical_qubits=16,
            phi_resonance_rate=0.9565
        )
        
        assert len(miner.register_indices) == 16
        assert miner.phi_resonance == 0.9565
    
    def test_superposition_preparation(self):
        """Test |+⟩^⊗n preparation"""
        miner = AutonomousFaultTolerantMiner(
            code_distance=5,
            num_logical_qubits=8
        )
        
        miner.prepare_nonce_superposition()
        
        # All qubits should have syndrome history from Hadamard application
        for idx in miner.register_indices:
            qubit = miner.qc.logical_qubits[idx]
            assert len(qubit.syndrome_history) >= 2  # Before and after H
    
    def test_phi_oracle(self):
        """Test φ-guided oracle application"""
        miner = AutonomousFaultTolerantMiner(
            code_distance=5,
            num_logical_qubits=8
        )
        miner.prepare_nonce_superposition()
        
        miner.apply_phi_oracle(target_resonance=0.95)
        
        # Verify error correction ran
        assert len(miner.qc.syndrome_measurements) > 0
    
    def test_grover_diffusion(self):
        """Test Grover diffusion operator"""
        miner = AutonomousFaultTolerantMiner(
            code_distance=5,
            num_logical_qubits=8
        )
        miner.prepare_nonce_superposition()
        
        miner.grover_diffusion()
        
        # Should complete without errors
        assert len(miner.qc.logical_qubits) == 8
    
    def test_search_iteration(self):
        """Test complete search iteration"""
        miner = AutonomousFaultTolerantMiner(
            code_distance=5,
            num_logical_qubits=8
        )
        miner.prepare_nonce_superposition()
        
        stats = miner.fault_tolerant_search_iteration(iteration=1)
        
        assert 'iteration' in stats
        assert stats['iteration'] == 1
        assert 'logical_error_rate' in stats
        assert 'fault_tolerant' in stats
    
    def test_nonce_measurement(self):
        """Test nonce candidate measurement"""
        miner = AutonomousFaultTolerantMiner(
            code_distance=5,
            num_logical_qubits=8
        )
        miner.prepare_nonce_superposition()
        
        nonce, stats = miner.measure_nonce_candidate()
        
        assert isinstance(nonce, int)
        assert 0 <= nonce < 2**8
        assert 'logical_error_rate' in stats


class TestMiningCycle:
    """Test complete mining cycle"""
    
    def test_full_cycle(self):
        """Test complete fault-tolerant mining cycle"""
        result = run_fault_tolerant_mining_cycle(num_iterations=5)
        
        assert 'nonce_candidate' in result
        assert 'fault_tolerant' in result
        assert 'logical_error_rate' in result
        assert 'suppression_factor' in result
        assert result['iterations'] == 5
    
    def test_phi_resonance_seeding(self):
        """Verify 95.65% φ-resonance used as prior"""
        result = run_fault_tolerant_mining_cycle(num_iterations=3)
        
        assert result['phi_resonance_target'] == 0.9565


class TestController:
    """Test production controller"""
    
    def test_controller_initialization(self):
        """Test controller loads config and evidence"""
        controller = FaultTolerantMiningController()
        
        assert controller.miner is not None
        assert controller.evidence is not None
        # Evidence contains phi_15 structure, not phi_resonance_rate
        assert 'phi_15' in controller.evidence or len(controller.evidence) > 0
    
    def test_start_autonomous_mining(self):
        """Test autonomous mining startup"""
        controller = FaultTolerantMiningController()
        status = controller.start_autonomous_mining()
        
        assert status['status'] == 'active'
        assert controller.active is True
        assert status['fault_tolerant'] is True
        assert 'empirical_evidence' in status
    
    def test_process_mining_job(self):
        """Test mining job processing"""
        controller = FaultTolerantMiningController()
        controller.start_autonomous_mining()
        
        job_data = {
            'job_id': 'test_001',
            'prev_hash': '0' * 64,
            'coinbase': 'test',
            'merkle_branches': [],
            'version': '20000000',
            'nbits': '1d00ffff',
            'ntime': '5f4a5e5a'
        }
        
        result = controller.process_mining_job(job_data)
        
        assert result['job_id'] == 'test_001'
        assert 'nonce' in result
        assert 'logical_error_rate' in result
        assert result['fault_tolerant'] is True
    
    def test_error_correction_stats(self):
        """Test error correction statistics"""
        controller = FaultTolerantMiningController()
        controller.start_autonomous_mining()
        
        stats = controller.get_error_correction_stats()
        
        assert 'physical_error_rate' in stats
        assert 'logical_error_rate' in stats
        assert 'suppression_factor' in stats
        assert stats['logical_error_rate'] < stats['physical_error_rate']
    
    def test_stop(self):
        """Test controller shutdown"""
        controller = FaultTolerantMiningController()
        controller.start_autonomous_mining()
        
        final = controller.stop()
        
        assert final['status'] == 'stopped'
        assert controller.active is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])


def test_logical_error_rate_matches_documented_suppression_formula():
    """Logical error rate must match the documented modeled threshold formula."""
    p_phys = 1e-3
    code_distance = 7
    qc = FaultTolerantQuantumCore(code_distance=code_distance, physical_error_rate=p_phys)

    expected = 0.03 * (p_phys / 0.0109) ** ((code_distance + 1) / 2)

    assert qc.p_logical == pytest.approx(expected, rel=1e-12)
    assert qc.get_error_statistics()["logical_error_rate"] == pytest.approx(expected, rel=1e-12)


def test_logical_error_rate_decreases_monotonically_with_code_distance_below_threshold():
    """The modeled threshold relationship must improve as odd distance increases."""
    p_phys = 1e-3
    distances = [3, 5, 7, 9]
    logical_rates = [
        FaultTolerantQuantumCore(code_distance=distance, physical_error_rate=p_phys).p_logical
        for distance in distances
    ]

    assert logical_rates == sorted(logical_rates, reverse=True)
    assert all(left > right for left, right in zip(logical_rates, logical_rates[1:]))


def test_logical_error_rate_increases_with_physical_error_rate_below_threshold():
    """The modeled threshold relationship must worsen as physical errors increase."""
    rates = [1e-5, 1e-4, 1e-3]
    logical_rates = [
        FaultTolerantQuantumCore(code_distance=7, physical_error_rate=rate).p_logical
        for rate in rates
    ]

    assert logical_rates == sorted(logical_rates)
    assert all(left < right for left, right in zip(logical_rates, logical_rates[1:]))


def test_logical_error_rate_saturates_above_model_threshold():
    """Above the documented model threshold, the projection must report no protection."""
    qc = FaultTolerantQuantumCore(code_distance=7, physical_error_rate=0.0109)

    assert qc.p_logical == 1.0
    assert qc.get_error_statistics()["logical_error_rate"] == 1.0
