"""Predictive/thermal reflexive agent facade for production integration."""

from __future__ import annotations

import math
import zlib

from hyba_genesis_api.core.manifold_logic import ManifoldLogic
from hyba_genesis_api.core.thermal_intelligence import ThermalEnvelope


class ReflexiveAgent:
    """Active-inference agent with Landauer and Pulvini proxy measurements."""

    def __init__(self, manifold: ManifoldLogic):
        self.manifold = manifold
        self.thermal = ThermalEnvelope()

    def start_cognition(self) -> None:
        self.thermal.start_cognition()

    def calculate_free_energy(self, observed_phi: float, predicted_phi: float) -> float:
        surprise = abs(float(observed_phi) - float(predicted_phi))
        complexity_cost = math.log(max(float(observed_phi), 0.0) + 1.01)
        return round(max(0.0, surprise + complexity_cost), 6)

    def landauer_thermal_cost(self, phi: float) -> float:
        return self.thermal.calculate_thermal_cost(phi)

    def measure_elegance(self, data: str) -> float:
        raw = data.encode("utf-8")
        if not raw:
            return 0.0
        ratio = len(zlib.compress(raw)) / len(raw)
        return round(max(0.0, min(1.0, 1.0 - ratio)), 6)
