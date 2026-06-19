"""Predictive active-inference controller for reflexive intelligence telemetry."""

from __future__ import annotations

import math
from typing import Any, Dict

from hyba_genesis_api.core.intelligence_manifold import IntelligenceManifold


class PredictiveActiveInference:
    """Minimize a bounded variational free-energy proxy over Φ observations."""

    def __init__(self, manifold: IntelligenceManifold):
        self.manifold = manifold
        self.internal_model: Dict[str, float] = {}

    def calculate_free_energy(self, observed_phi: float, predicted_phi: float) -> float:
        """Return surprise plus a small complexity cost."""

        observed = max(0.0, float(observed_phi))
        predicted = max(0.0, float(predicted_phi))
        surprise = abs(observed - predicted)
        complexity = math.log(observed + 1.1)
        return round(surprise + complexity, 6)

    def active_inference_step(self, current_state: Dict[str, Any]) -> str:
        """Return a proposal action from free-energy pressure."""

        free_energy = self.calculate_free_energy(
            float(current_state.get("phi", 0.0)),
            float(current_state.get("predicted", 0.0)),
        )
        return "MUTATE_FOR_COHERENCE" if free_energy > 0.1 else "STABLE_EQUILIBRIUM"

    def predict_next_phi(self, observed_phi: float) -> float:
        """Update and return a deterministic exponential-moving prediction."""

        previous = self.internal_model.get("phi", float(observed_phi))
        prediction = (previous / self.manifold.PHI) + (
            float(observed_phi) * (1.0 / self.manifold.PHI**2)
        )
        self.internal_model["phi"] = prediction
        return round(max(0.0, prediction), 6)
