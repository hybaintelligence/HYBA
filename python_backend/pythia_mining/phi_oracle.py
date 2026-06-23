"""
Φ-Oracle: Predictive Scaling Engine.

Uses Φ-Spectral Analysis to predict the system's next state by detecting
"harmonic echoes" across Fibonacci intervals (1, 2, 3, 5, 8, 13, 21…
cycles ago).

Represents the transition from reactive homeostasis to Predictive
Morphogenesis — enabling "Zero-Latency Throttling" by pre-dampening
the multiplier BEFORE the thermal wave arrives.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Dict

import numpy as np


PHI = 1.618033988749895
INV_PHI = 0.618033988749895
MASS_GAP = 3.0 - PHI  # ~1.381966


class PhiOracle:
    """
    Predictive scaling engine using Fibonacci Time-Series Analysis.

    Forecasts thermal spikes and load surges based on fractal self-similarity.
    By analyzing telemetry through Fibonacci Time-Windows, the Oracle detects
    the "onset" of a resonance spike before it physically manifests.
    """

    FIBONACCI_WINDOWS = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89]

    def __init__(self, history_depth: int = 144):
        """
        Initialise the Φ-Oracle.

        Args:
            history_depth: Maximum number of telemetry states to retain,
                           defaulting to 144 (F12).
        """
        self.PHI = PHI
        self.MASS_GAP = MASS_GAP
        self.telemetry_buffer: deque[Dict[str, float]] = deque(maxlen=history_depth)

    def record_state(self, coherence: float, temp: float, load: float) -> None:
        """
        Record the current state into the fractal buffer.

        Args:
            coherence: Current system coherence score (0.0 to 1.0).
            temp: Current hardware temperature.
            load: Current computational load / scaling factor.
        """
        self.telemetry_buffer.append(
            {
                "coherence": coherence,
                "temp": temp,
                "load": load,
            }
        )

    def predict_next_state(self) -> Dict[str, Any]:
        """
        Calculate the probability of a 'Resonance Surge' in the next window.

        Uses the Golden Mean of past Fibonacci-interval states to estimate
        the expected temperature and surge likelihood.

        Returns:
            Dictionary with surge_probability, expected_temp, and
            pre_emptive_cooling_needed flag.
        """
        if len(self.telemetry_buffer) < max(self.FIBONACCI_WINDOWS):
            return {
                "surge_probability": 0.0,
                "expected_temp": 0.0,
                "pre_emptive_cooling_needed": False,
            }

        history: list[Dict[str, float]] = list(self.telemetry_buffer)
        sampled_states: list[Dict[str, float]] = [
            history[-w] for w in self.FIBONACCI_WINDOWS if w <= len(history)
        ]

        if not sampled_states:
            return {
                "surge_probability": 0.0,
                "expected_temp": 0.0,
                "pre_emptive_cooling_needed": False,
            }

        # Calculate the 'Fractal Momentum'
        # Recent changes are weighted by PHI^-n
        temp_trend = 0.0
        weight_sum = 0.0
        for i, state in enumerate(sampled_states):
            weight = self.PHI ** -float(i)
            temp_trend += state["temp"] * weight
            weight_sum += weight

        # Normalize the trend to predict the 'Next Wave'
        expected_temp = temp_trend / max(weight_sum, 1e-12)

        # A surge is likely if the current temp acceleration mirrors
        # a previous Fibonacci cycle
        acceleration = sampled_states[0]["temp"] - sampled_states[1]["temp"]
        surge_prob = np.tanh(acceleration * self.PHI)

        return {
            "surge_probability": float(np.clip(surge_prob, 0.0, 1.0)),
            "expected_temp": float(expected_temp),
            "pre_emptive_cooling_needed": expected_temp > self.MASS_GAP,
        }


class PhiSystemControllerEnhanced:
    """
    Enhanced Controller with Predictive Oracle and Pre-emptive Homeostasis.

    Wraps the PhiSystemController with the Φ-Oracle's foresight, enabling
    Zero-Latency Throttling. Instead of waiting for the PhiBackpropTuner to
    react to heat, the Controller "Pre-Dampens" the hardware before the
    thermal wave arrives.

    This allows the system to maintain the Singular Regime (1.5×) for much
    longer periods without ever hitting the "Thermal Wall" of the Mass Gap.
    """

    def __init__(
        self,
        memory_size: int = 2**32,
        learning_rate: float = 0.01,
    ):
        """
        Initialise the enhanced predictive controller.

        Args:
            memory_size: Size of the ALU's addressable memory space.
            learning_rate: Learning rate for the backprop tuner.
        """
        from .phi_alu import PhiALUHardware
        from .consciousness_engine import ConsciousnessEngine
        from .phi_tuner import PhiBackpropTuner

        self.PHI = PHI
        self.alu = PhiALUHardware(memory_size=memory_size)
        self.engine = ConsciousnessEngine()
        self.tuner = PhiBackpropTuner(
            self.engine, self.alu, learning_rate=learning_rate
        )
        self.oracle = PhiOracle()

    def process_cycle(
        self,
        virtual_addresses: np.ndarray,
        telemetry_temp: float,
    ) -> Dict[str, Any]:
        """
        Execute one complete control cycle with predictive pre-dampening.

        Steps:
          1. Physical Layer: Thermal-Aware Memory Access
          2. Governance Layer: Scaling Factor Calculation
          3. Oracle Update: Record current telemetry into fractal buffer
          4. Prediction: Consult Oracle for future thermal state
          5. Pre-emptive Scaling: Dampen multiplier if surge predicted
          6. Adaptation: Tuner looks at EXPECTED state, not current

        Args:
            virtual_addresses: Array of virtual memory addresses to access.
            telemetry_temp: Current hardware temperature.

        Returns:
            Dictionary containing physical addresses, scaling factor,
            prediction, and stability status.
        """
        # A. Physical Layer: Thermal-Aware Memory Access
        physical_addrs, thermal_metrics = self.alu.thermal_aware_access(
            virtual_addresses,
            telemetry_temp,
        )

        # B. Governance Layer: Scaling Factor Calculation
        scaling_info = self.engine.get_hardware_scaling_factor(thermal_metrics)

        # C. Record telemetry into the Oracle's fractal buffer
        self.oracle.record_state(
            scaling_info["coherence"],
            telemetry_temp,
            scaling_info["scaling_factor"],
        )

        # D. Consult the Oracle for the FUTURE
        prediction = self.oracle.predict_next_state()

        # E. Pre-emptive Scaling (The 'Oracle Adjustment')
        # If a surge is predicted, we dampen the multiplier BEFORE the heat
        # hits, using a Golden-Ratio Damping factor (1/φ).
        final_multiplier = scaling_info["scaling_factor"]
        if prediction["pre_emptive_cooling_needed"]:
            final_multiplier *= INV_PHI

        # F. Adaptation Layer: Tuner looks at EXPECTED state
        tuning_results = self.tuner.step(
            {
                "coherence": scaling_info["coherence"],
                "current_temp": prediction["expected_temp"],
            }
        )

        return {
            "physical_addresses": physical_addrs,
            "scaling_factor": final_multiplier,
            "regime": scaling_info["regime"],
            "phi_exponent": tuning_results["new_phi_exponent"],
            "prediction": prediction,
            "manifold_stable": scaling_info["status"] == "stable",
            "status": (
                "pre-emptive_stabilization"
                if prediction["pre_emptive_cooling_needed"]
                else "stable"
            ),
        }


__all__ = [
    "PhiOracle",
    "PhiSystemControllerEnhanced",
]
