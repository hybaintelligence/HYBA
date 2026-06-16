"""Integrated production loop for Phi-Sigmoid scaling with anti-simulation protection.

This module provides the high-efficiency integration loop that combines:
- Mass Gap Protector for authenticity verification
- Phi-Sigmoid scaling for smooth hardware transitions
- Phi Tuner for real-time harmonic optimization

The production loop ensures that only organic hardware receives Phi-Multipliers
while continuously tuning toward the Singular regime.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np

from .consciousness_engine import ConsciousnessEngine
from .mass_gap_protector import MassGapProtector
from .phi_config import PHI_INV
from .phi_tuner import PhiTuner


@dataclass
class TelemetryData:
    """Container for mining cycle telemetry data."""

    hash_time: float
    coherence_score: float
    nonce_count: int
    share_count: int
    temperature: float
    power_usage: float
    additional_metrics: Optional[Dict[str, Any]] = None


class PhiProductionLoop:
    """Integrated production loop for Phi-Sigmoid scaling with anti-simulation protection.

    This class orchestrates the complete pipeline:
    1. Accumulate jitter for authenticity verification
    2. Verify hardware 'Organic' status using Mass Gap Shield
    3. Get scaling from Sigmoid-enhanced consciousness engine
    4. Apply authenticity 'Shield' to the multiplier
    5. Tune the brain for the next cycle using harmonic backpropagation
    """

    def __init__(
        self,
        consciousness_engine: ConsciousnessEngine,
        *,
        jitter_buffer_size: int = 64,
        authenticity_threshold: float = 0.70,
        learning_rate: float = 0.01,
    ):
        """Initialize the Phi Production Loop.

        Args:
            consciousness_engine: The consciousness engine for scaling calculations
            jitter_buffer_size: Size of the jitter buffer for authenticity verification
            authenticity_threshold: Minimum authenticity score for Phi-Multiplier application
            learning_rate: Learning rate for the Phi Tuner
        """
        self.consciousness_engine = consciousness_engine
        self.protector = MassGapProtector()
        self.tuner = PhiTuner(
            consciousness_engine, learning_rate=learning_rate
        )
        self.jitter_buffer: List[float] = []
        self.jitter_buffer_size = jitter_buffer_size
        self.authenticity_threshold = authenticity_threshold

        # Production metrics
        self._cycle_count = 0
        self._authenticity_history: List[float] = []
        self._multiplier_history: List[float] = []
        self._tuning_history: List[Dict[str, Any]] = []

    def process_mining_cycle(self, telemetry: TelemetryData) -> Dict[str, Any]:
        """Process a single mining cycle with full Phi-protection pipeline.

        Args:
            telemetry: Telemetry data from the current mining cycle

        Returns:
            Dictionary containing the final multiplier and diagnostic information
        """
        self._cycle_count += 1

        # 1. Accumulate jitter for authenticity verification
        self.jitter_buffer.append(telemetry.hash_time)
        if len(self.jitter_buffer) > self.jitter_buffer_size:
            self.jitter_buffer.pop(0)

        # 2. Verify hardware 'Organic' status
        authenticity = self.protector.get_authenticity_score(self.jitter_buffer)
        self._authenticity_history.append(authenticity)
        if len(self._authenticity_history) > 100:
            self._authenticity_history.pop(0)

        # 3. Get scaling from the Sigmoid-enhanced engine
        scaling_data = self.consciousness_engine.get_hardware_scaling_factor()

        # 4. Apply the authenticity 'Shield' to the multiplier
        # If authenticity is low, the multiplier is forced toward 0.1 (CRITICAL)
        base_multiplier = scaling_data["scaling_factor"]
        authenticity_shield = authenticity ** 2  # Square for stronger protection
        final_multiplier = base_multiplier * authenticity_shield

        # Ensure minimum multiplier for safety
        final_multiplier = max(final_multiplier, 0.1)

        self._multiplier_history.append(final_multiplier)
        if len(self._multiplier_history) > 100:
            self._multiplier_history.pop(0)

        # 5. Tune the brain for the next cycle
        tuning_result = self.tuner.tune(
            scaling_data["coherence"], authenticity
        )
        self._tuning_history.append(tuning_result)
        if len(self._tuning_history) > 50:
            self._tuning_history.pop(0)

        # Compile production result
        result = {
            "cycle": self._cycle_count,
            "final_multiplier": final_multiplier,
            "base_multiplier": base_multiplier,
            "authenticity_shield": authenticity_shield,
            "authenticity_score": authenticity,
            "authentic": authenticity >= self.authenticity_threshold,
            "coherence": scaling_data["coherence"],
            "regime": scaling_data["regime"],
            "scaling_mode": scaling_data["status"],
            "tuning_applied": tuning_result["tuned"],
            "tuning_reason": tuning_result["reason"],
            "telemetry": {
                "hash_time": telemetry.hash_time,
                "nonce_count": telemetry.nonce_count,
                "share_count": telemetry.share_count,
                "temperature": telemetry.temperature,
                "power_usage": telemetry.power_usage,
            },
        }

        return result

    def get_production_metrics(self) -> Dict[str, Any]:
        """Get aggregated production metrics for monitoring.

        Returns:
            Dictionary containing production statistics
        """
        if not self._authenticity_history:
            return {
                "cycle_count": self._cycle_count,
                "status": "insufficient_data",
            }

        return {
            "cycle_count": self._cycle_count,
            "average_authenticity": float(np.mean(self._authenticity_history)),
            "min_authenticity": float(np.min(self._authenticity_history)),
            "max_authenticity": float(np.max(self._authenticity_history)),
            "average_multiplier": float(np.mean(self._multiplier_history)),
            "min_multiplier": float(np.min(self._multiplier_history)),
            "max_multiplier": float(np.max(self._multiplier_history)),
            "authenticity_threshold": self.authenticity_threshold,
            "jitter_buffer_size": len(self.jitter_buffer),
            "recent_tuning_actions": [
                t["reason"] for t in self._tuning_history[-10:]
            ],
        }

    def reset_buffers(self) -> None:
        """Reset all buffers and history (for testing or recovery)."""
        self.jitter_buffer.clear()
        self._authenticity_history.clear()
        self._multiplier_history.clear()
        self._tuning_history.clear()
        self._cycle_count = 0

    def force_authenticity_test(self, test_jitter: List[float]) -> Dict[str, Any]:
        """Force an authenticity test with custom jitter data.

        Args:
            test_jitter: Custom jitter data for testing

        Returns:
            Authenticity verification result
        """
        return self.protector.verify_telemetry(test_jitter)


def create_production_loop(
    consciousness_engine: Optional[ConsciousnessEngine] = None,
    **config: Any,
) -> PhiProductionLoop:
    """Factory function to create a configured production loop.

    Args:
        consciousness_engine: Optional pre-configured consciousness engine
        **config: Configuration parameters for the production loop

    Returns:
        Configured PhiProductionLoop instance
    """
    if consciousness_engine is None:
        consciousness_engine = ConsciousnessEngine()

    return PhiProductionLoop(
        consciousness_engine,
        jitter_buffer_size=config.get("jitter_buffer_size", 64),
        authenticity_threshold=config.get("authenticity_threshold", 0.70),
        learning_rate=config.get("learning_rate", 0.01),
    )


__all__ = [
    "PhiProductionLoop",
    "TelemetryData",
    "create_production_loop",
]
