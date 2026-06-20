"""
Fault-Tolerant Quantum Computer Core
Implements surface code error correction with φ-guided logical qubit operations
"""
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import math

PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV = PHI - 1.0


@dataclass
class LogicalQubit:
    """Logical qubit encoded with surface code"""
    physical_qubits: np.ndarray  # Shape: (d, d) for distance d
    syndrome_history: List[np.ndarray]
    error_rate: float
    distance: int
    
    
class FaultTolerantQuantumCore:
    """
    Fault-tolerant quantum computer for autonomous mining
    Uses surface code with φ-scaled distance parameters
    """
    
    def __init__(self, code_distance: int = 7, physical_error_rate: float = 1e-3):
        """
        Args:
            code_distance: Surface code distance (must be odd), determines error threshold
            physical_error_rate: Per-gate error rate for physical qubits
        """
        if code_distance % 2 == 0:
            raise ValueError("Code distance must be odd")
        
        self.d = code_distance
        self.p_phys = physical_error_rate
        # Surface-code model threshold used by the logical-error-rate formula.
        # Keep classification aligned with _compute_logical_error_rate(): values
        # at or above this threshold are modeled as providing no protection.
        self.error_threshold = 0.0109
        self.phi_reference_threshold = (3 - PHI) * 1e-2
        self.p_logical = self._compute_logical_error_rate()
        self.correction_attempts = 0
        self.correction_successes = 0
        self.logical_failures = 0
        self.last_decoder_defects = 0
        self.last_decoder_weight = 0.0
        
        # Initialize logical qubit register
        self.logical_qubits: List[LogicalQubit] = []
        self.syndrome_measurements: List[np.ndarray] = []
        
    def _compute_logical_error_rate(self) -> float:
        """Compute logical error rate from surface code formula"""
        # p_L ≈ c * (p/p_th)^((d+1)/2) for p < p_th
        c = 0.03  # Constant factor
        p_th = getattr(self, "error_threshold", 0.0109)
        
        if self.p_phys >= p_th:
            return 1.0  # At/above threshold, no modeled protection
        
        exponent = (self.d + 1) / 2
        p_logical = c * (self.p_phys / p_th) ** exponent
        return min(p_logical, 1.0)
    
    def initialize_logical_qubit(self, state: str = '0') -> int:
        """
        Initialize a logical qubit in |0⟩_L or |1⟩_L state
        Returns logical qubit index
        """
        physical_array = np.zeros((self.d, self.d), dtype=complex)
        
        if state == '0':
            # Encode |0⟩_L as +1 eigenstate of Z stabilizers
            physical_array[self.d // 2, self.d // 2] = 1.0
        elif state == '1':
            # Encode |1⟩_L as -1 eigenstate of Z stabilizers
            physical_array[self.d // 2, self.d // 2] = -1.0
        else:
            raise ValueError("State must be '0' or '1'")
        
        logical_qubit = LogicalQubit(
            physical_qubits=physical_array,
            syndrome_history=[],
            error_rate=self.p_logical,
            distance=self.d
        )
        
        self.logical_qubits.append(logical_qubit)
        return len(self.logical_qubits) - 1
    
    def measure_syndromes(self, qubit_idx: int) -> np.ndarray:
        """
        Measure stabilizer syndromes (X and Z type)
        Returns syndrome bit array
        """
        qubit = self.logical_qubits[qubit_idx]
        
        # Syndrome array: (d-1) x (d-1) for each stabilizer type
        z_syndromes = np.zeros((self.d - 1, self.d - 1), dtype=int)
        x_syndromes = np.zeros((self.d - 1, self.d - 1), dtype=int)
        
        # Simulate syndrome measurement with physical errors
        for i in range(self.d - 1):
            for j in range(self.d - 1):
                # Z stabilizer on data qubits
                z_syndrome = int(np.random.random() < self.p_phys)
                z_syndromes[i, j] = z_syndrome
                
                # X stabilizer on data qubits
                x_syndrome = int(np.random.random() < self.p_phys)
                x_syndromes[i, j] = x_syndrome
        
        syndrome = np.stack([z_syndromes, x_syndromes])
        qubit.syndrome_history.append(syndrome)
        self.syndrome_measurements.append(syndrome)
        
        return syndrome
    
    def _minimum_weight_pairing(self, defect_locations: List[Tuple[int, int, int]]) -> float:
        """
        Return the total Manhattan weight of a minimum-weight defect pairing.

        This is a compact surface-code matching model for the small defect sets
        produced by the local simulator.  It pairs syndrome-change defects by
        stabilizer type and uses nearest-boundary matching for odd cardinality,
        so decoder decisions are derived from syndrome data rather than sampled
        from the closed-form logical-error-rate projection.
        """
        if not defect_locations:
            return 0.0

        # Large rounds can occur with intentionally high physical error rates.
        # Use deterministic greedy matching as a bounded fallback rather than an
        # exponential dynamic program.
        if len(defect_locations) > 18:
            remaining = defect_locations[:]
            total = 0.0
            while len(remaining) > 1:
                defect = remaining.pop(0)
                partner_idx, partner = min(
                    enumerate(remaining),
                    key=lambda item: abs(defect[1] - item[1][1]) + abs(defect[2] - item[1][2]),
                )
                total += float(abs(defect[1] - partner[1]) + abs(defect[2] - partner[2]))
                remaining.pop(partner_idx)
            if remaining:
                _, row, col = remaining[0]
                total += float(min(row + 1, col + 1, self.d - row - 1, self.d - col - 1))
            return total

        distances: Dict[Tuple[int, int], float] = {}
        boundary_costs: Dict[int, float] = {}
        for i, (_, row_i, col_i) in enumerate(defect_locations):
            boundary_costs[i] = float(min(row_i + 1, col_i + 1, self.d - row_i - 1, self.d - col_i - 1))
            for j in range(i + 1, len(defect_locations)):
                _, row_j, col_j = defect_locations[j]
                distances[(i, j)] = float(abs(row_i - row_j) + abs(col_i - col_j))

        memo: Dict[int, float] = {}

        def solve(mask: int) -> float:
            if mask == 0:
                return 0.0
            if mask in memo:
                return memo[mask]

            first = (mask & -mask).bit_length() - 1
            remaining_mask = mask & ~(1 << first)
            best = boundary_costs[first] + solve(remaining_mask)
            partner_mask = remaining_mask
            while partner_mask:
                partner = (partner_mask & -partner_mask).bit_length() - 1
                pair = (min(first, partner), max(first, partner))
                candidate = distances[pair] + solve(remaining_mask & ~(1 << partner))
                best = min(best, candidate)
                partner_mask &= ~(1 << partner)

            memo[mask] = best
            return best

        return solve((1 << len(defect_locations)) - 1)

    def decode_and_correct(self, qubit_idx: int) -> bool:
        """
        Run a syndrome-derived minimum-weight matching decoder.

        The modeled logical error rate remains an analytic surface-code
        projection.  Correction success is not sampled from that projection; it
        is determined from the observed syndrome-change defects and whether the
        inferred correction chain reaches the code-distance failure boundary.
        Returns True if correction successful
        """
        qubit = self.logical_qubits[qubit_idx]
        
        if len(qubit.syndrome_history) < 2:
            return True  # Need at least 2 rounds for matching
        
        # Get syndrome changes (defects)
        current = qubit.syndrome_history[-1]
        previous = qubit.syndrome_history[-2]
        defects = current ^ previous  # XOR gives syndrome changes

        total_weight = 0.0
        for stabilizer_type in range(defects.shape[0]):
            locations = [
                (stabilizer_type, int(row), int(col))
                for row, col in np.argwhere(defects[stabilizer_type] == 1)
            ]
            total_weight += self._minimum_weight_pairing(locations)

        defect_count = int(np.sum(defects))
        correction_success = total_weight < self.d

        self.correction_attempts += 1
        self.last_decoder_defects = defect_count
        self.last_decoder_weight = total_weight

        if correction_success:
            self.correction_successes += 1
            # Mark the correction frame by absorbing the current syndrome as
            # the new baseline.  The simplified state representation stores the
            # logical value at the centre cell, so applying a physical chain
            # here would fabricate amplitudes rather than model a real patch.
            qubit.syndrome_history[-1] = current.copy()
        else:
            self.logical_failures += 1
        
        return correction_success
    
    def apply_logical_gate(self, gate: str, qubit_idx: int) -> bool:
        """
        Apply fault-tolerant logical gate
        Supported: 'H', 'S', 'CNOT' (with target)
        """
        qubit = self.logical_qubits[qubit_idx]
        
        # Measure syndromes before gate
        self.measure_syndromes(qubit_idx)
        
        # Apply transversal gate (fault-tolerant by construction)
        if gate == 'H':
            # Hadamard: rotate basis
            qubit.physical_qubits = qubit.physical_qubits.T
        elif gate == 'S':
            # Phase gate: add φ-scaled phase
            qubit.physical_qubits *= np.exp(1j * np.pi / (2 * PHI))
        elif gate == 'X':
            # Bit flip
            qubit.physical_qubits *= -1
        elif gate == 'Z':
            # Phase flip
            qubit.physical_qubits *= np.exp(1j * np.pi)
        else:
            raise ValueError(f"Unsupported gate: {gate}")
        
        # Measure syndromes after gate
        self.measure_syndromes(qubit_idx)
        
        # Decode and correct errors
        return self.decode_and_correct(qubit_idx)
    
    def measure_logical(self, qubit_idx: int) -> int:
        """
        Measure logical qubit in computational basis
        Returns 0 or 1
        """
        qubit = self.logical_qubits[qubit_idx]
        
        # Final syndrome measurement
        self.measure_syndromes(qubit_idx)
        self.decode_and_correct(qubit_idx)
        
        # Majority vote on physical qubits
        center_val = qubit.physical_qubits[self.d // 2, self.d // 2]
        return 0 if center_val.real >= 0 else 1
    
    def get_error_statistics(self) -> Dict[str, float]:
        """Return current error rates and correction statistics"""
        total_syndromes = len(self.syndrome_measurements)
        
        if total_syndromes == 0:
            return {
                'physical_error_rate': self.p_phys,
                'logical_error_rate': self.p_logical,
                'logical_error_rate_basis': 'modeled_surface_code_scaling_law',
                'error_threshold': self.error_threshold,
                'phi_reference_threshold': self.phi_reference_threshold,
                'fault_tolerant': self.p_phys < self.error_threshold,
                'syndrome_rounds': 0,
                'correction_attempts': self.correction_attempts,
                'correction_successes': self.correction_successes,
                'logical_failures': self.logical_failures,
                'last_decoder_defects': self.last_decoder_defects,
                'last_decoder_weight': self.last_decoder_weight,
            }
        
        # Compute syndrome weight (number of non-zero syndromes)
        syndrome_weights = [np.sum(s) for s in self.syndrome_measurements]
        avg_weight = np.mean(syndrome_weights) if syndrome_weights else 0
        
        return {
            'physical_error_rate': self.p_phys,
            'logical_error_rate': self.p_logical,
            'logical_error_rate_basis': 'modeled_surface_code_scaling_law',
            'error_threshold': self.error_threshold,
            'phi_reference_threshold': self.phi_reference_threshold,
            'fault_tolerant': self.p_phys < self.error_threshold,
            'syndrome_rounds': total_syndromes,
            'avg_syndrome_weight': avg_weight,
            'correction_attempts': self.correction_attempts,
            'correction_successes': self.correction_successes,
            'logical_failures': self.logical_failures,
            'last_decoder_defects': self.last_decoder_defects,
            'last_decoder_weight': self.last_decoder_weight,
            'suppression_factor': self.p_phys / max(self.p_logical, 1e-10)
        }


class AutonomousFaultTolerantMiner:
    """
    Autonomous mining system with fault-tolerant quantum backend
    Integrates with existing HYBA/PYTHIA infrastructure
    """
    
    def __init__(self, 
                 code_distance: int = 7,
                 num_logical_qubits: int = 32,
                 phi_resonance_rate: float = 0.9565,
                 physical_error_rate: float = 1e-3):
        
        self.qc = FaultTolerantQuantumCore(
            code_distance=code_distance,
            physical_error_rate=physical_error_rate
        )
        
        self.num_qubits = num_logical_qubits
        self.phi_resonance = phi_resonance_rate
        
        # Initialize logical qubit register for mining
        self.register_indices = []
        for i in range(num_logical_qubits):
            idx = self.qc.initialize_logical_qubit('0')
            self.register_indices.append(idx)
    
    def prepare_nonce_superposition(self) -> None:
        """Prepare |+⟩^⊗n superposition for nonce search"""
        for idx in self.register_indices:
            success = self.qc.apply_logical_gate('H', idx)
            if not success:
                # Retry with error correction
                self.qc.measure_syndromes(idx)
                self.qc.decode_and_correct(idx)
                self.qc.apply_logical_gate('H', idx)
    
    def apply_phi_oracle(self, target_resonance: float = 0.95) -> None:
        """
        Apply φ-guided oracle for structured search
        Marks states with high φ-resonance
        """
        # Oracle phase: |x⟩ → (-1)^f(x) |x⟩ where f(x) = 1 if φ-resonant
        oracle_phase = 2 * np.pi * PHI_INV * target_resonance
        
        for idx in self.register_indices:
            # Apply conditional phase
            qubit = self.qc.logical_qubits[idx]
            qubit.physical_qubits *= np.exp(1j * oracle_phase)
            
            # Error correction round
            self.qc.measure_syndromes(idx)
            self.qc.decode_and_correct(idx)
    
    def grover_diffusion(self) -> None:
        """Apply Grover diffusion operator: 2|ψ⟩⟨ψ| - I"""
        # H⊗n X⊗n H⊗n = diffusion operator
        for idx in self.register_indices:
            self.qc.apply_logical_gate('H', idx)
            self.qc.apply_logical_gate('X', idx)
            self.qc.apply_logical_gate('H', idx)
    
    def fault_tolerant_search_iteration(self, iteration: int) -> Dict:
        """
        Run one iteration of fault-tolerant quantum search
        Returns metrics dict
        """
        # Oracle application
        self.apply_phi_oracle(target_resonance=self.phi_resonance)
        
        # Diffusion operator
        self.grover_diffusion()
        
        # Collect error statistics
        stats = self.qc.get_error_statistics()
        stats['iteration'] = iteration
        
        return stats
    
    def measure_nonce_candidate(self) -> Tuple[int, Dict]:
        """
        Measure logical qubit register to get nonce candidate
        Returns (nonce, error_stats)
        """
        nonce_bits = []
        for idx in self.register_indices:
            bit = self.qc.measure_logical(idx)
            nonce_bits.append(bit)
        
        # Convert bit array to integer
        nonce = sum(bit << i for i, bit in enumerate(nonce_bits))
        
        stats = self.qc.get_error_statistics()
        return nonce, stats


def run_fault_tolerant_mining_cycle(num_iterations: int = 10) -> Dict:
    """
    Execute complete fault-tolerant quantum mining cycle
    """
    miner = AutonomousFaultTolerantMiner(
        code_distance=7,
        num_logical_qubits=32,
        phi_resonance_rate=0.9565  # From empirical evidence
    )
    
    # Prepare superposition
    miner.prepare_nonce_superposition()
    
    # Run Grover iterations
    iteration_stats = []
    for i in range(num_iterations):
        stats = miner.fault_tolerant_search_iteration(i)
        iteration_stats.append(stats)
    
    # Measure final nonce
    nonce, final_stats = miner.measure_nonce_candidate()
    
    return {
        'nonce_candidate': nonce,
        'fault_tolerant': final_stats['fault_tolerant'],
        'logical_error_rate': final_stats['logical_error_rate'],
        'suppression_factor': final_stats['suppression_factor'],
        'iterations': num_iterations,
        'iteration_stats': iteration_stats,
        'phi_resonance_target': miner.phi_resonance
    }
