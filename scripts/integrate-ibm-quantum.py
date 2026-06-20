"""Integration scaffold for IBM Quantum runtime."""

from __future__ import annotations


class IBMQuantumSubstrate:
    """Execute HYBA algorithms on IBM Quantum hardware when credentials exist."""

    def __init__(self, api_key: str) -> None:
        from qiskit_ibm_runtime import QiskitRuntimeService

        self.service = QiskitRuntimeService(channel="ibm_quantum", token=api_key)

    def execute_fault_tolerant_cycle(self, code_distance: int, circuit_depth: int) -> dict[str, object]:
        backend = self.service.least_busy()
        return {
            "substrate": "ibm_quantum",
            "backend": getattr(backend, "name", str(backend)),
            "code_distance": code_distance,
            "circuit_depth": circuit_depth,
            "status": "queued_for_transpile_and_runtime_execution",
        }
