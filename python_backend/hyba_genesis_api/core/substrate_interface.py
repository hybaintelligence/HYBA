"""Unified substrate contract for HYBA intelligence adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class SubstrateContract(ABC):
    """Shared interface: context -> telemetry -> explanation -> counterfactuals -> governance."""

    @abstractmethod
    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a substrate-specific context into a semantic telemetry envelope."""

    def create_telemetry_envelope(
        self,
        phi: float,
        explanation: str,
        counterfactuals: List[str],
    ) -> Dict[str, Any]:
        """Create a bounded semantic telemetry envelope for substrate output."""

        bounded_phi = max(0.0, float(phi))
        return {
            "phi_resonance": bounded_phi,
            "phi_density": bounded_phi / (1.0 + bounded_phi),
            "explanation": explanation,
            "counterfactuals": list(counterfactuals),
            "governance_tags": self._generate_tags(bounded_phi),
            "thermal_envelope": "stable",
            "claim_boundary": "Measured classical substrate coherence envelope",
        }

    def _generate_tags(self, phi: float) -> List[str]:
        if phi > 1.618:
            return ["HIGH_COHERENCE", "RECURSIVE_STABILITY"]
        return ["LOW_RESONANCE", "FRAGMENTATION_RISK"]
