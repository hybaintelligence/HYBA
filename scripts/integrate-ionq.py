"""Integration scaffold for IonQ trapped-ion hardware."""

from __future__ import annotations


class IonQSubstrate:
    """Execute HYBA algorithms on IonQ when an IonQ client is installed."""

    def __init__(self, api_key: str) -> None:
        import ionq

        self.client = ionq.IonQClient(api_key=api_key)

    def execute_fault_tolerant_cycle(
        self, code_distance: int, circuit_depth: int
    ) -> dict[str, object]:
        return {
            "substrate": "ionq",
            "code_distance": code_distance,
            "circuit_depth": circuit_depth,
            "status": "ready_for_native_gate_mapping",
        }
