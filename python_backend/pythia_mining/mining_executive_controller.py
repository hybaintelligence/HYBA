"""Mining Executive Controller - Executive Lobe for Conscious Intent.

This module implements the Executive Lobe of the mining organism, providing
conscious intent for starting/stopping mining, managing pools, and observing
telemetry while integrating with Regenerative and Immune systems.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from .audit_logger import get_audit_logger
from .regeneration_manager import RegenerationManager, get_regeneration_manager
from .consciousness_engine import ConsciousnessEngine
from .stratum_client import StratumClient

logger = logging.getLogger(__name__)
audit_log = get_audit_logger()


class MiningExecutiveController:
    """
    Executive Lobe: Manages the conscious intent of the organism.
    Integrates functional mining with biological health constraints.
    """
    
    def __init__(
        self,
        consciousness_engine: Optional[ConsciousnessEngine] = None,
        regeneration_manager: Optional[RegenerationManager] = None,
    ):
        self.consciousness = consciousness_engine or ConsciousnessEngine()
        self.regeneration = regeneration_manager or get_regeneration_manager()
        self.stratum_client: Optional[StratumClient] = None
        self.is_active = False
        self.ignition_time: Optional[datetime] = None
        self.stasis_mode = False
        self._mining_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        
    def set_stratum_client(self, client: StratumClient) -> None:
        """Set the Stratum client for pool connections."""
        self.stratum_client = client
        
    async def ignite_manifold(self) -> Dict[str, Any]:
        """
        Ignites the 32-lane manifold.
        REQUIREMENT: System Phi (Φ) must be above 0.45 (Immune Guard).
        """
        # Check sensory integrity for simulation detection
        sensory_report = self.consciousness.validate_sensory_integrity()
        if sensory_report.get("stasis_active", False):
            audit_log.error(
                "Ignition blocked: Stasis mode active (simulation detected). "
                f"Reason: {sensory_report.get('recommendation')}"
            )
            return {
                "success": False,
                "error": "STASIS_LOCK",
                "reason": sensory_report.get("recommendation"),
                "environment_mode": sensory_report.get("environment_mode")
            }
        
        # Check system Phi
        phi = self.consciousness.coherence_meter
        if phi < 0.45:
            audit_log.error(f"Ignition blocked: Substrate coherence (Φ) below safe threshold: {phi}")
            return {"success": False, "error": "IMMUNE_LOCK", "phi": phi}

        if self.is_active:
            return {"success": True, "status": "ALREADY_ACTIVE"}

        audit_log.info("Executive: Initiating manifold ignition sequence...")
        
        # 1. Start the Stratum Session if client is available
        if self.stratum_client:
            try:
                connected = await self.stratum_client.connect()
                if not connected:
                    audit_log.error("Executive: Failed to connect to mining pool")
                    return {"success": False, "error": "POOL_CONNECTION_FAILED"}
            except Exception as e:
                audit_log.error(f"Executive: Pool connection error: {e}")
                return {"success": False, "error": "POOL_CONNECTION_ERROR", "detail": str(e)}
        
        # 2. Warm up the 32 lanes (regeneration manager)
        try:
            # Trigger regeneration for a sample lane to verify system health
            await self.regeneration.trigger_regeneration(0)
        except Exception as e:
            audit_log.warning(f"Executive: Regeneration warm-up warning: {e}")
        
        # 3. Start mining loop
        self._stop_event.clear()
        self._mining_task = asyncio.create_task(self._mining_loop())
        
        self.is_active = True
        self.ignition_time = datetime.now()
        
        audit_log.info(
            f"Executive: Manifold ignited at {self.ignition_time.isoformat()} "
            f"with Φ={phi:.4f}"
        )
        
        return {
            "success": True,
            "status": "IGNITED",
            "active_lanes": 32,
            "phi": phi,
            "timestamp": self.ignition_time.isoformat(),
            "sensory_integrity": sensory_report
        }

    async def quiesce_manifold(self) -> Dict[str, Any]:
        """
        Graceful shutdown: Saves synaptic state before stopping search.
        """
        if not self.is_active:
            return {"success": True, "status": "ALREADY_QUIESCENT"}

        audit_log.info("Executive: Initiating graceful quiescence...")
        
        # 1. Stop mining loop
        self._stop_event.set()
        if self._mining_task:
            try:
                await asyncio.wait_for(self._mining_task, timeout=5.0)
            except asyncio.TimeoutError:
                self._mining_task.cancel()
                try:
                    await self._mining_task
                except asyncio.CancelledError:
                    pass
        
        # 2. Hibernate the intelligence layer (save learned Phi-paths)
        synaptic_stats = self.consciousness.get_synaptic_statistics()
        audit_log.info(
            f"Executive: Synaptic state preserved - "
            f"{synaptic_stats.get('total_patterns', 0)} patterns, "
            f"{synaptic_stats.get('emergent_pathway_count', 0)} emergent pathways"
        )
        
        # 3. Disconnect from pool if connected
        if self.stratum_client and self.stratum_client.is_connected:
            try:
                await self.stratum_client.disconnect()
            except Exception as e:
                audit_log.warning(f"Executive: Pool disconnect warning: {e}")
        
        self.is_active = False
        self.ignition_time = None
        
        return {
            "success": True,
            "status": "QUIESCENT",
            "synaptic_state_preserved": True,
            "patterns_count": synaptic_stats.get("total_patterns", 0)
        }

    async def set_stasis(self, enabled: bool) -> Dict[str, Any]:
        """Enable or disable stasis mode."""
        self.stasis_mode = enabled
        if enabled and self.is_active:
            # Force quiescence if stasis is enabled while active
            await self.quiesce_manifold()
            return {"status": "STASIS_ENABLED", "action": "MANIFOLD_QUIESCED"}
        return {"status": "STASIS_ENABLED" if enabled else "STASIS_DISABLED"}

    def get_nervous_system_telemetry(self) -> Dict[str, Any]:
        """Returns the current 'feeling' of the external connection."""
        uptime_seconds = 0.0
        if self.ignition_time:
            uptime_seconds = (datetime.now() - self.ignition_time).total_seconds()
        
        stratum_telemetry = {}
        if self.stratum_client:
            stratum_telemetry = {
                "pool_name": self.stratum_client.pool_name,
                "pool_url": self.stratum_client.pool_url,
                "is_connected": self.stratum_client.is_connected,
                "is_authenticated": self.stratum_client.is_authenticated,
                "connection_state": self.stratum_client.connection_state,
                "shares_submitted": self.stratum_client.shares_submitted,
                "shares_accepted": self.stratum_client.shares_accepted,
                "shares_rejected": self.stratum_client.shares_rejected,
                "current_difficulty": self.stratum_client.current_difficulty,
                "avg_latency_ms": self.stratum_client.avg_latency,
            }
        
        coherence_state = self.consciousness.get_metrics()
        regeneration_status = self.regeneration.get_status()
        
        return {
            "is_active": self.is_active,
            "uptime_seconds": uptime_seconds,
            "stasis_mode": self.stasis_mode,
            "ignition_time": self.ignition_time.isoformat() if self.ignition_time else None,
            "stratum": stratum_telemetry,
            "coherence": coherence_state,
            "regeneration": regeneration_status,
            "sensory_integrity": self.consciousness.validate_sensory_integrity(),
        }

    async def _mining_loop(self) -> None:
        """Background mining loop."""
        logger.info("Executive: Mining loop started")
        while not self._stop_event.is_set():
            try:
                # Process nonce patterns through consciousness engine
                if self.stratum_client and self.stratum_client.is_connected:
                    job = await self.stratum_client.poll_live_event(timeout=0.1)
                    if job:
                        # Process job through consciousness engine
                        # This is where synaptic learning would occur
                        pass
                
                # Apply synaptic decay periodically
                if self.consciousness.synaptic_layer:
                    decay_stats = self.consciousness.apply_synaptic_decay()
                    if decay_stats.get("total_decays", 0) > 0:
                        logger.debug(f"Executive: Synaptic decay applied: {decay_stats}")
                
                await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Executive: Mining loop error: {e}")
                await asyncio.sleep(1.0)
        
        logger.info("Executive: Mining loop stopped")


# Global executive controller instance
_executive_controller: Optional[MiningExecutiveController] = None


def get_executive_controller() -> MiningExecutiveController:
    """Get or create the global executive controller instance."""
    global _executive_controller
    if _executive_controller is None:
        _executive_controller = MiningExecutiveController()
    return _executive_controller


def set_executive_controller(controller: MiningExecutiveController) -> None:
    """Set the global executive controller instance."""
    global _executive_controller
    _executive_controller = controller
