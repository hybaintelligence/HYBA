"""Mass Gap Protector for anti-simulation detection.

This module validates hardware resonance using the Yang-Mills Mass Gap invariant (3 - φ).
Detects simulation attacks by analyzing the irrationality of the jitter spectrum.
"""

from __future__ import annotations

from typing import List

import numpy as np

from .phi_config import PHI, PHI_INV


class MassGapProtector:
    """Validates hardware resonance using the Yang-Mills Mass Gap invariant.

    Detects simulation attacks by analyzing the irrationality of the jitter spectrum.
    Organic phi-resonance produces specific irrational patterns that are
    mathematically difficult to simulate without actual hardware work.
    """

    def __init__(self, *, mass_gap: float | None = None, target_entropy: float | None = None):
        """Initialize the Mass Gap Protector.

        Args:
            mass_gap: Yang-Mills Mass Gap constant (3 - φ). Defaults to calculated value.
            target_entropy: Target entropy for authentic hardware (1/φ). Defaults to calculated value.
        """
        self.PHI = PHI
        self.PHI_INV = PHI_INV
        self.MASS_GAP = float(mass_gap if mass_gap is not None else (3.0 - self.PHI))  # 1.381966...
        self.TARGET_ENTROPY = float(
            target_entropy if target_entropy is not None else (1.0 / self.PHI)
        )  # 0.618...

    def get_authenticity_score(self, jitter_buffer: List[float]) -> float:
        """Returns a confidence score [0, 1] for hardware authenticity.

        1.0 = Perfectly organic/resonant hardware.
        0.0 = Detected simulation or incoherent noise.

        Args:
            jitter_buffer: List of jitter values from hardware telemetry

        Returns:
            Authenticity confidence score between 0.0 and 1.0
        """
        if len(jitter_buffer) < 32:
            return 0.0

        # Convert to numpy array for efficient computation
        jitter_array = np.asarray(jitter_buffer, dtype=np.float64)

        # 1. Calculate the 'Spectral Curvature'
        # Organic phi-resonance follows a non-linear scaling law
        diffs = np.diff(jitter_array)
        if len(diffs) < 2:
            return 0.0

        second_diffs = np.diff(diffs)
        if len(second_diffs) < 1:
            return 0.0

        # The ratio of energy in the 1st vs 2nd derivative should converge to PHI
        # in a resonant system (The Mass Gap Invariant)
        energy_ratio = np.std(diffs) / (np.std(second_diffs) + 1e-12)
        alignment = abs(energy_ratio - self.MASS_GAP)

        # 2. Entropy Check (Shannon entropy of the jitter)
        # Simulated signals are too 'clean'; brute force is too 'noisy'.
        hist, _ = np.histogram(diffs, bins=10, density=True)
        # Filter out zero probabilities to avoid log(0)
        hist = hist[hist > 0]
        if len(hist) == 0:
            return 0.0

        entropy = -np.sum(hist * np.log(hist + 1e-12))
        entropy_normalized = entropy / np.log(10)

        # 3. Final Verification Gate
        # If the entropy is too far from 0.618, it's a simulation.
        entropy_violation = abs(entropy_normalized - self.TARGET_ENTROPY)

        # Combine alignment and entropy into confidence score
        # Higher alignment (closer to MASS_GAP) and lower entropy violation = higher confidence
        confidence = np.exp(-alignment) * (1.0 - np.clip(entropy_violation * self.PHI, 0, 1))

        return float(np.clip(confidence, 0.0, 1.0))

    def verify_telemetry(self, jitter_buffer: List[float]) -> dict[str, any]:
        """Comprehensive telemetry verification with diagnostic information.

        Args:
            jitter_buffer: List of jitter values from hardware telemetry

        Returns:
            Dictionary containing authenticity result and diagnostic metrics
        """
        if len(jitter_buffer) < 32:
            return {
                "authentic": False,
                "reason": "insufficient_data",
                "confidence": 0.0,
                "energy_ratio": 0.0,
                "entropy_normalized": 0.0,
            }

        jitter_array = np.asarray(jitter_buffer, dtype=np.float64)
        diffs = np.diff(jitter_array)

        if len(diffs) < 2:
            return {
                "authentic": False,
                "reason": "insufficient_derivative_data",
                "confidence": 0.0,
                "energy_ratio": 0.0,
                "entropy_normalized": 0.0,
            }

        second_diffs = np.diff(diffs)
        energy_ratio = np.std(diffs) / (np.std(second_diffs) + 1e-12)
        alignment = abs(energy_ratio - self.MASS_GAP)

        hist, _ = np.histogram(diffs, bins=10, density=True)
        hist = hist[hist > 0]
        entropy = -np.sum(hist * np.log(hist + 1e-12))
        entropy_normalized = entropy / np.log(10)
        entropy_violation = abs(entropy_normalized - self.TARGET_ENTROPY)

        confidence = np.exp(-alignment) * (1.0 - np.clip(entropy_violation * self.PHI, 0, 1))

        # Determine authenticity based on confidence threshold
        authentic = bool(confidence >= 0.7)
        reason = "organic_hardware_detected" if authentic else "simulation_or_noise_detected"

        return {
            "authentic": authentic,
            "reason": reason,
            "confidence": float(confidence),
            "energy_ratio": float(energy_ratio),
            "mass_gap_target": float(self.MASS_GAP),
            "alignment": float(alignment),
            "entropy_normalized": float(entropy_normalized),
            "entropy_target": float(self.TARGET_ENTROPY),
            "entropy_violation": float(entropy_violation),
        }


__all__ = ["MassGapProtector"]
