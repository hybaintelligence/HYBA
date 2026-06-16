"""Thermal intelligence envelope for cost-of-cognition telemetry."""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class ThermalEnvelope:
    """Measure deterministic wall-clock cost of a cognition step."""

    start_time: float = 0.0

    def start_cognition(self) -> None:
        self.start_time = time.perf_counter()

    def calculate_thermal_cost(self, phi: float) -> float:
        """Return Φ per second as a bounded Landauer-style cost proxy."""

        duration = max(time.perf_counter() - self.start_time, 1e-9)
        return round(max(0.0, float(phi)) / duration, 6)

    def snapshot(self, phi: float) -> dict[str, float]:
        duration = max(time.perf_counter() - self.start_time, 1e-9)
        return {
            "duration_seconds": round(duration, 9),
            "thermal_cost_phi_per_second": self.calculate_thermal_cost(phi),
        }
