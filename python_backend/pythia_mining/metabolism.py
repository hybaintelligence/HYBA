"""Metabolism - Energy-to-intelligence conversion rate monitoring."""

import logging
import random
from typing import Dict, Any
from datetime import datetime, timezone


LOGGER = logging.getLogger(__name__)


class Metabolism:
    """Measures and optimizes the energy-to-intelligence conversion rate."""

    def __init__(self):
        self.energy_per_phi_baseline = 1.0  # Baseline: 1 unit energy per phi
        self.current_flux = {
            "energy_per_phi": self.energy_per_phi_baseline,
            "hashrate_normalized_entropy": 0.5,
            "hunger_level": 0.3,
            "metabolic_rate": "ACTIVE"
        }

    def get_current_flux(self) -> Dict[str, Any]:
        """
        Get current metabolic flux measurements.
        
        Returns energy efficiency metrics and metabolic state.
        """
        # Simulate real-time measurements - in production this would use actual telemetry
        energy_per_phi = self.energy_per_phi_baseline * random.uniform(0.9, 1.1)
        hashrate_entropy = random.uniform(0.4, 0.6)
        hunger_level = random.uniform(0.2, 0.4)
        
        # Determine metabolic rate based on hunger and efficiency
        if hunger_level > 0.35:
            metabolic_rate = "HYPER"
        elif hunger_level > 0.25:
            metabolic_rate = "ACTIVE"
        else:
            metabolic_rate = "QUIESCENT"
        
        self.current_flux = {
            "energy_per_phi": energy_per_phi,
            "hashrate_normalized_entropy": hashrate_entropy,
            "hunger_level": hunger_level,
            "metabolic_rate": metabolic_rate
        }
        
        LOGGER.debug(
            f"Metabolic flux: energy_per_phi={energy_per_phi:.4f}, "
            f"metabolic_rate={metabolic_rate}"
        )
        
        return self.current_flux

    def adjust_metabolism(self, target_rate: str) -> Dict[str, Any]:
        """
        Adjust the metabolic rate based on system demands.
        
        Args:
            target_rate: One of "QUIESCENT", "ACTIVE", "HYPER"
        """
        valid_rates = ["QUIESCENT", "ACTIVE", "HYPER"]
        if target_rate not in valid_rates:
            LOGGER.warning(f"Invalid metabolic rate: {target_rate}")
            return {"error": "Invalid metabolic rate", "valid_rates": valid_rates}
        
        old_rate = self.current_flux["metabolic_rate"]
        self.current_flux["metabolic_rate"] = target_rate
        
        # Adjust energy efficiency based on metabolic rate
        if target_rate == "HYPER":
            self.current_flux["energy_per_phi"] = self.energy_per_phi_baseline * 1.2
            self.current_flux["hunger_level"] = 0.4
        elif target_rate == "ACTIVE":
            self.current_flux["energy_per_phi"] = self.energy_per_phi_baseline
            self.current_flux["hunger_level"] = 0.3
        else:  # QUIESCENT
            self.current_flux["energy_per_phi"] = self.energy_per_phi_baseline * 0.8
            self.current_flux["hunger_level"] = 0.2
        
        LOGGER.info(f"Metabolic rate adjusted: {old_rate} -> {target_rate}")
        
        return {
            "action": "ADJUSTED",
            "old_rate": old_rate,
            "new_rate": target_rate,
            "energy_per_phi": self.current_flux["energy_per_phi"]
        }
