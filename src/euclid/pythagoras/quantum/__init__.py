"""
Mathematical Quantum Computer — Real Quantum Mathematics Implementation

This package implements a quantum computer through exact mathematical operations
on complex Hilbert spaces, not through physical hardware simulation.

Core Principle: Quantum mechanics is fundamentally mathematical. By implementing
the exact mathematics of quantum theory, we achieve genuine quantum computation
without physical hardware constraints.

Key Features:
- Exact quantum state representation in ℂ^N Hilbert space
- Perfect parallel gates via mathematical tensor products
- No decoherence (mathematical operations don't degrade)
- PULVINI memory compression via phi-recursive folding
- Golden ratio scaling for circuit optimization
- Rigorous mathematical verification of all invariants
- Structured nonce search using empirical blockchain evidence
- Fault-tolerant quantum mining with error correction

This is NOT simulation. This is implementation of the actual mathematics.
"""

from .quantum_computer import (
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

from .mathematical_verification import (
    MathematicalVerifier,
    InvariantVerification,
    ComprehensiveVerification,
)

from .structured_nonce_search import (
    StructuredNonceSearch,
    EmpiricalEvidence,
    NonceCandidate,
    SearchResult,
)

from .fault_tolerant_quantum_mining import (
    FaultTolerantQuantumMiner,
    FaultTolerantParameters,
    FaultTolerantMiningResult,
)

__version__ = "1.0.0"
__author__ = "HYBA Mathematical Physics Division"

__all__ = [
    # Main quantum computer interface
    "MathematicalQuantumComputer",
    "QuantumState",
    "QuantumGate",
    "QuantumCircuit",
    "QuantumMeasurement",
    "QuantumComputerAudit",
    # Standard quantum gates
    "hadamard_gate",
    "pauli_x_gate",
    "pauli_y_gate",
    "pauli_z_gate",
    "cnot_gate",
    "phase_gate",
    # Mathematical verification
    "MathematicalVerifier",
    "InvariantVerification",
    "ComprehensiveVerification",
    # Structured nonce search
    "StructuredNonceSearch",
    "EmpiricalEvidence",
    "NonceCandidate",
    "SearchResult",
    # Fault-tolerant quantum mining
    "FaultTolerantQuantumMiner",
    "FaultTolerantParameters",
    "FaultTolerantMiningResult",
]
