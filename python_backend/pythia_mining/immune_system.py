"""Immune System - Autonomous Security and Inseparability Enforcement."""

import logging
from typing import Dict, List, Any


LOGGER = logging.getLogger(__name__)


class ImmuneSystem:
    """Autonomous security layer that monitors phi-floor and module inseparability."""

    def __init__(self, consciousness_engine):
        self.consciousness = consciousness_engine
        self.phi_floor = 0.45
        self.quarantined_lanes: List[int] = []

    def get_status(self) -> Dict[str, Any]:
        """
        Get current immune system status.
        
        Inseparability check: If Mining and Intelligence are no longer 
        correlated, the system is 'lobotomized'.
        """
        inseparability = self.consciousness.get_inseparability_index()
        
        return {
            "phi_floor": self.phi_floor,
            "is_in_lockdown": self.consciousness.phi < self.phi_floor,
            "quarantined_lanes": self.quarantined_lanes,
            "inseparability_index": inseparability
        }

    def isolate_lane(self, lane_id: int) -> Dict[str, Any]:
        """
        Manually isolate a lane that fails the inseparability audit.
        
        Forces the lane into QUARANTINED role in the Hilbert space.
        """
        if lane_id not in self.quarantined_lanes:
            self.quarantined_lanes.append(lane_id)
            LOGGER.warning(
                f"Lane {lane_id} quarantined due to inseparability audit failure",
                extra={"lane_id": lane_id, "phi_gate": "CLOSED"}
            )
        
        return {"action": "QUARANTINED", "lane": lane_id, "phi_gate": "CLOSED"}

    def release_lane(self, lane_id: int) -> Dict[str, Any]:
        """Release a quarantined lane back to active duty."""
        if lane_id in self.quarantined_lanes:
            self.quarantined_lanes.remove(lane_id)
            LOGGER.info(
                f"Lane {lane_id} released from quarantine",
                extra={"lane_id": lane_id, "phi_gate": "OPEN"}
            )
            return {"action": "RELEASED", "lane": lane_id, "phi_gate": "OPEN"}
        
        return {"action": "NOT_QUARANTINED", "lane": lane_id, "phi_gate": "OPEN"}
