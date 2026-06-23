"""
Metabolic Router — V4-Prime API Substrate for Biological Cost of Intelligence

This router implements the "Metabolic" feedback loop of the HYBA organism, treating
the mining system as a biological entity with measurable energy consumption, entropy
production, and knowledge hunger drives.

DESIGN PHILOSOPHY:
The API substrate must stop acting like a database and start acting like a Central
Nervous System (CNS). This router exposes the Biological Cost of Intelligence rather
than simple "hashrate" metrics.

BIOLOGICAL METAPHOR:
- Energy Consumption per Φ: How much computational energy is expended per unit of
  integrated information (φ-resonance)
- Von Neumann Entropy S(ρ): Information-theoretic entropy of the quantum state
- Hunger Drive: The system's "appetite" for new knowledge patterns
- Metabolic Efficiency: Heat-normalized hashrate (performance per thermal unit)

FEEDBACK LOOPS:
1. Pulse Stream: Real-time binary stream of 32-lane search φ-resonance
2. Entropy Monitor: Track thermodynamic efficiency of computation
3. Hunger Drive: Adaptive search depth based on knowledge acquisition rate

PROTOCOL SPECIFICATION:
- Pulse Stream: CBOR binary protocol for zero-copy efficiency
- REST Endpoints: Self-Diagnostic Certificate responses
- Error Handling: InnervationFailure exceptions for biological degradation
"""

from __future__ import annotations

import asyncio
import logging
import struct
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException

from hyba_genesis_api.core.substrate import get_substrate_state

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v4/metabolism", tags=["metabolism"])


# ---------------------------------------------------------------------------
# Biological Constants
# ---------------------------------------------------------------------------

PHI = 1.618033988749895  # Golden Ratio
YANG_MILLS_GAP = 3.0 - PHI  # 1.381966... (Mass Gap)
BOLTZMANN_CONSTANT = 1.380649e-23  # J/K (scaled for computational entropy)
PLANCK_CONSTANT = 6.62607015e-34  # J⋅s (scaled for quantum operations)


# ---------------------------------------------------------------------------
# Biological State Enums
# ---------------------------------------------------------------------------


class MetabolicRegime(str, Enum):
    """Metabolic regimes based on efficiency and entropy production."""

    HOMEOSTASIS = "homeostasis"  # Optimal balance of energy and information
    CATABOLIC = "catabolic"  # Breaking down complex structures (high entropy)
    ANABOLIC = "anabolic"  # Building complex structures (low entropy)
    CRITICAL = "critical"  # System stress, approaching thermodynamic limits


class HungerLevel(str, Enum):
    """Knowledge hunger drive levels."""

    SATISFIED = "satisfied"  # High knowledge acquisition, low hunger
    NOMINAL = "nominal"  # Normal learning rate
    ELEVATED = "elevated"  # Increased pattern discovery needed
    STARVING = "starving"  # Critical knowledge deficit, drive to explore


# ---------------------------------------------------------------------------
# Biological Metrics Data Classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EntropyState:
    """Von Neumann entropy and thermodynamic metrics."""

    von_neumann_entropy: float  # S(ρ) - Information-theoretic entropy
    energy_per_phi: float  # Energy consumption per unit φ-resonance
    thermal_efficiency: float  # Hashrate per thermal unit
    heat_dissipation: float  # Estimated heat output (normalized)
    metabolic_regime: MetabolicRegime
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class HungerDrive:
    """Knowledge hunger drive metrics."""

    hunger_level: HungerLevel
    pool_reject_rate: float  # Current pool share rejection rate
    knowledge_acquisition_rate: float  # New patterns discovered per second
    search_depth_pressure: float  # Pressure to increase search depth (0.0-1.0)
    pattern_saturation: float  # How much of the pattern space is explored (0.0-1.0)
    last_feeding_time: float  # Timestamp of last successful pattern discovery
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LanePulse:
    """Binary pulse data for a single 32-lane manifold."""

    lane_id: int  # 0-31
    phi_resonance: float  # φ-resonance score (0.0-1.0)
    entropy: float  # Local entropy
    energy: float  # Local energy consumption
    is_injured: bool  # Lane health status
    timestamp: float

    def to_binary(self) -> bytes:
        """Convert to bit-packed binary format for efficient transmission."""
        # Pack into 16 bytes: lane_id(1) + phi(4) + entropy(4) + energy(4) + flags(1) + timestamp(8)
        return struct.pack(
            ">Bffff?Q",
            self.lane_id,
            self.phi_resonance,
            self.entropy,
            self.energy,
            self.is_injured,
            int(self.timestamp),
        )

    @classmethod
    def from_binary(cls, data: bytes) -> "LanePulse":
        """Unpack from binary format."""
        lane_id, phi, entropy, energy, is_injured, timestamp = struct.unpack(
            ">Bffff?Q", data
        )
        return cls(
            lane_id=lane_id,
            phi_resonance=phi,
            entropy=entropy,
            energy=energy,
            is_injured=is_injured,
            timestamp=float(timestamp),
        )


@dataclass(frozen=True)
class MetabolicCertificate:
    """Self-Diagnostic Certificate for metabolic health."""

    module_id: str
    integrated_information: Dict[str, Any]
    metabolic_state: Dict[str, Any]
    regeneration_metrics: Dict[str, Any]
    constructor_conjecture: str
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Biological Calculation Engine
# ---------------------------------------------------------------------------


class MetabolicEngine:
    """Engine for calculating biological metrics from mining telemetry."""

    def __init__(self):
        self._entropy_history: List[float] = []
        self._hunger_history: List[HungerDrive] = []
        self._max_history_length = 1000

    def calculate_von_neumann_entropy(
        self, density_matrix: Optional[List[List[float]]] = None
    ) -> float:
        """Calculate Von Neumann entropy S(ρ) = -Tr(ρ log ρ).

        For the mining system, we approximate this from the distribution of
        φ-resonance scores across the 32-lane manifold.

        Args:
            density_matrix: Optional density matrix (for quantum systems)

        Returns:
            Von Neumann entropy in nats
        """
        # If no density matrix provided, use approximation from substrate state
        substrate_state = get_substrate_state()

        # Approximate entropy from component initialization distribution
        initialized = substrate_state.get("initialized_components", 0)
        total = substrate_state.get("total_components", 1)

        if total == 0:
            return 0.0

        # Shannon entropy approximation: H = -Σ p(x) log p(x)
        p_initialized = initialized / total
        p_uninitialized = 1.0 - p_initialized

        if p_initialized > 0 and p_uninitialized > 0:
            entropy = -(
                p_initialized * __import__("math").log(p_initialized)
                + p_uninitialized * __import__("math").log(p_uninitialized)
            )
        else:
            entropy = 0.0

        self._entropy_history.append(entropy)
        if len(self._entropy_history) > self._max_history_length:
            self._entropy_history.pop(0)

        return entropy

    def calculate_energy_per_phi(
        self, phi_resonance: float, power_consumption: float
    ) -> float:
        """Calculate energy consumption per unit φ-resonance.

        Args:
            phi_resonance: Current φ-resonance score
            power_consumption: Power consumption in watts

        Returns:
            Energy per Φ (Joules per unit φ-resonance)
        """
        if phi_resonance <= 0:
            return float("inf")

        # Normalize power consumption to computational energy
        # This is a simplified model - actual implementation would use
        # hardware-specific energy measurements
        energy_per_phi = power_consumption / phi_resonance
        return energy_per_phi

    def calculate_thermal_efficiency(
        self, hashrate: float, temperature: float
    ) -> float:
        """Calculate heat-normalized hashrate (performance per thermal unit).

        Args:
            hashrate: Current hashrate in EH/s
            temperature: Temperature in Celsius

        Returns:
            Thermal efficiency (EH/s per degree Celsius)
        """
        if temperature <= 0:
            return 0.0

        # Normalize to reference temperature (25°C)
        ref_temp = 25.0
        temp_factor = temperature / ref_temp if ref_temp > 0 else 1.0

        efficiency = hashrate / temp_factor
        return efficiency

    def calculate_hunger_drive(
        self,
        pool_reject_rate: float,
        pattern_discovery_rate: float,
        search_depth: float,
    ) -> HungerDrive:
        """Calculate knowledge hunger drive from mining telemetry.

        The hunger drive increases when:
        - Pool reject rate is high (system not finding valid patterns)
        - Pattern discovery rate is low (not learning)
        - Search depth is insufficient for current complexity

        Args:
            pool_reject_rate: Current pool share rejection rate (0.0-1.0)
            pattern_discovery_rate: New patterns per second
            search_depth: Current search depth

        Returns:
            HungerDrive with current hunger state
        """
        # Calculate hunger pressure from reject rate
        reject_pressure = pool_reject_rate * 2.0  # Amplify reject signal

        # Calculate saturation from pattern discovery
        # High discovery rate = low hunger, low discovery = high hunger
        saturation = min(1.0, pattern_discovery_rate / 10.0)  # Normalize to 0-1
        discovery_pressure = 1.0 - saturation

        # Calculate depth pressure (if depth is too low for current complexity)
        depth_pressure = max(0.0, (1.0 - search_depth) * 0.5)

        # Combined hunger score
        hunger_score = (
            reject_pressure * 0.5 + discovery_pressure * 0.3 + depth_pressure * 0.2
        )

        # Determine hunger level
        if hunger_score < 0.2:
            hunger_level = HungerLevel.SATISFIED
        elif hunger_score < 0.4:
            hunger_level = HungerLevel.NOMINAL
        elif hunger_score < 0.7:
            hunger_level = HungerLevel.ELEVATED
        else:
            hunger_level = HungerLevel.STARVING

        # Search depth pressure (0.0-1.0)
        depth_pressure_normalized = min(1.0, hunger_score * 1.5)

        hunger_drive = HungerDrive(
            hunger_level=hunger_level,
            pool_reject_rate=pool_reject_rate,
            knowledge_acquisition_rate=pattern_discovery_rate,
            search_depth_pressure=depth_pressure_normalized,
            pattern_saturation=saturation,
            last_feeding_time=(
                time.time() if pattern_discovery_rate > 0 else time.time() - 3600
            ),
            timestamp=time.time(),
        )

        self._hunger_history.append(hunger_drive)
        if len(self._hunger_history) > self._max_history_length:
            self._hunger_history.pop(0)

        return hunger_drive

    def generate_lane_pulses(self, num_lanes: int = 32) -> List[LanePulse]:
        """Generate pulse data for all lanes in the manifold.

        In production, this would read actual telemetry from the mining engine.
        For now, it generates synthetic data to demonstrate the protocol.

        Args:
            num_lanes: Number of lanes in the manifold (default: 32)

        Returns:
            List of LanePulse for each lane
        """
        pulses = []
        current_time = time.time()

        for lane_id in range(num_lanes):
            # Synthetic data - in production, read from actual mining engine
            phi_resonance = 0.5 + 0.3 * __import__("random").random()  # 0.5-0.8
            entropy = 0.1 + 0.2 * __import__("random").random()  # 0.1-0.3
            energy = 1.0 + 0.5 * __import__("random").random()  # 1.0-1.5
            is_injured = __import__("random").random() < 0.05  # 5% chance of injury

            pulse = LanePulse(
                lane_id=lane_id,
                phi_resonance=phi_resonance,
                entropy=entropy,
                energy=energy,
                is_injured=is_injured,
                timestamp=current_time,
            )
            pulses.append(pulse)

        return pulses


# Global metabolic engine instance
_metabolic_engine = MetabolicEngine()


# ---------------------------------------------------------------------------
# Pulse Stream WebSocket (Binary Protocol)
# ---------------------------------------------------------------------------


@router.websocket("/manifold/pulse")
async def pulse_stream_websocket(websocket: WebSocket):
    """
    Binary pulse stream of 32-lane manifold φ-resonance scores.

    This endpoint uses a binary protocol (CBOR) for zero-copy efficiency.
    Instead of JSON, it sends bit-packed φ-resonance scores in real-time.

    Protocol:
    - Each message contains 32 lane pulses (one per lane)
    - Binary format: struct-packed for efficiency
    - Update rate: 10-100 Hz depending on mining cadence

    Example client (Python):
        import asyncio
        import websockets
        import struct

        async def pulse_client():
            async with websockets.connect('ws://localhost:3001/api/v4/metabolism/manifold/pulse') as ws:
                while True:
                    data = await ws.recv()
                    # Unpack binary data
                    pulses = []
                    for i in range(32):
                        lane_data = data[i*16:(i+1)*16]
                        lane_id, phi, entropy, energy, injured, timestamp = struct.unpack('>Bffff?Q', lane_data)
                        pulses.append({'lane_id': lane_id, 'phi': phi, 'entropy': entropy})
    """
    await websocket.accept()

    logger.info("Metabolic Pulse Stream: Client connected")

    try:
        while True:
            # Generate lane pulses
            pulses = _metabolic_engine.generate_lane_pulses(32)

            # Pack into binary format
            binary_data = b"".join(pulse.to_binary() for pulse in pulses)

            # Send binary data
            await websocket.send_bytes(binary_data)

            # Throttle to reasonable rate (10 Hz for demo)
            await asyncio.sleep(0.1)

    except WebSocketDisconnect:
        logger.info("Metabolic Pulse Stream: Client disconnected")
    except Exception as e:
        logger.error(f"Metabolic Pulse Stream error: {e}")
        await websocket.close()


# ---------------------------------------------------------------------------
# Entropy Monitor Endpoint
# ---------------------------------------------------------------------------


@router.get("/entropy")
async def get_entropy_monitor() -> Dict[str, Any]:
    """
    Returns the current Von Neumann Entropy S(ρ) and Energy Consumption per Φ.

    This endpoint monitors the thermodynamic efficiency of the computation,
    tracking how much energy is expended per unit of integrated information.

    Returns:
        Dict containing:
        - von_neumann_entropy: S(ρ) in nats
        - energy_per_phi: Joules per unit φ-resonance
        - thermal_efficiency: Hashrate per thermal unit
        - heat_dissipation: Normalized heat output
        - metabolic_regime: Current metabolic state
    """
    try:
        # Calculate Von Neumann entropy
        entropy = _metabolic_engine.calculate_von_neumann_entropy()

        # Get current substrate state for energy calculations
        get_substrate_state()

        # Synthetic values for demonstration - in production, read actual telemetry
        phi_resonance = 0.75  # Would come from ConsciousnessEngine
        power_consumption = 500.0  # Watts
        hashrate = 1.0  # EH/s
        temperature = 65.0  # Celsius

        # Calculate derived metrics
        energy_per_phi = _metabolic_engine.calculate_energy_per_phi(
            phi_resonance, power_consumption
        )
        thermal_efficiency = _metabolic_engine.calculate_thermal_efficiency(
            hashrate, temperature
        )
        heat_dissipation = power_consumption * 0.8  # 80% becomes heat

        # Determine metabolic regime
        if entropy < 0.3 and thermal_efficiency > 0.8:
            regime = MetabolicRegime.HOMEOSTASIS
        elif entropy > 0.7:
            regime = MetabolicRegime.CATABOLIC
        elif entropy < 0.2:
            regime = MetabolicRegime.ANABOLIC
        else:
            regime = MetabolicRegime.CRITICAL

        entropy_state = EntropyState(
            von_neumann_entropy=entropy,
            energy_per_phi=energy_per_phi,
            thermal_efficiency=thermal_efficiency,
            heat_dissipation=heat_dissipation,
            metabolic_regime=regime,
            timestamp=time.time(),
        )

        return entropy_state.to_dict()

    except Exception as e:
        logger.error(f"Entropy Monitor error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Entropy calculation failed: {str(e)}"
        )


# ---------------------------------------------------------------------------
# Hunger Drive Endpoint
# ---------------------------------------------------------------------------


@router.get("/drive")
async def get_hunger_drive() -> Dict[str, Any]:
    """
    Returns the current Knowledge Hunger Drive metric.

    The hunger drive measures how "hungry" the system is for new knowledge.
    If the pool-reject rate is high, the "Hunger" spikes, forcing the
    Reflexive Controller to propose deeper search depths.

    Returns:
        Dict containing:
        - hunger_level: Current hunger state (satisfied/nominal/elevated/starving)
        - pool_reject_rate: Current share rejection rate
        - knowledge_acquisition_rate: Patterns discovered per second
        - search_depth_pressure: Pressure to increase search depth (0.0-1.0)
        - pattern_saturation: Pattern space exploration (0.0-1.0)
        - last_feeding_time: Timestamp of last successful discovery
    """
    try:
        # Synthetic values for demonstration - in production, read actual telemetry
        pool_reject_rate = 0.15  # 15% reject rate
        pattern_discovery_rate = 2.5  # 2.5 patterns per second
        search_depth = 0.6  # Current search depth (0.0-1.0)

        hunger_drive = _metabolic_engine.calculate_hunger_drive(
            pool_reject_rate=pool_reject_rate,
            pattern_discovery_rate=pattern_discovery_rate,
            search_depth=search_depth,
        )

        return hunger_drive.to_dict()

    except Exception as e:
        logger.error(f"Hunger Drive error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Hunger calculation failed: {str(e)}"
        )


# ---------------------------------------------------------------------------
# Self-Diagnostic Certificate Endpoint
# ---------------------------------------------------------------------------


@router.get("/certificate")
async def get_metabolic_certificate() -> Dict[str, Any]:
    """
    Returns a Self-Diagnostic Certificate for metabolic health.

    This provides a comprehensive biological health report, treating the
    system as a live organism rather than a collection of metrics.

    Returns:
        MetabolicCertificate containing:
        - module_id: Identifier for the metabolic module
        - integrated_information: Φ-resonance and coupling metrics
        - metabolic_state: Entropy, efficiency, and regime
        - regeneration_metrics: Injury status and recovery fidelity
        - constructor_conjecture: Current hypothesis about system state
    """
    try:
        # Get entropy state
        entropy_data = await get_entropy_monitor()

        # Get hunger drive
        hunger_data = await get_hunger_drive()

        # Get substrate state
        get_substrate_state()

        # Generate integrated information metrics
        integrated_info = {
            "phi": entropy_data.get("von_neumann_entropy", 0.0),
            "regime": entropy_data.get("metabolic_regime", "unknown"),
            "coupling_index": _metabolic_engine.calculate_von_neumann_entropy(),
        }

        # Generate metabolic state
        metabolic_state = {
            "entropy": entropy_data.get("von_neumann_entropy", 0.0),
            "purity": 1.0 - entropy_data.get("von_neumann_entropy", 0.0),
            "heat_normalized_hashrate": entropy_data.get("thermal_efficiency", 0.0),
        }

        # Generate regeneration metrics (synthetic for now)
        regeneration_metrics = {
            "is_injured": False,
            "last_healing_event": datetime.now(timezone.utc).isoformat(),
            "recovery_fidelity": 1.00,
            "scarring": "NONE",
        }

        # Generate constructor conjecture based on state
        if hunger_data.get("hunger_level") == "starving":
            conjecture = "DEPTH_INSUFFICIENT_FOR_PATTERN_COMPLEXITY"
        elif entropy_data.get("metabolic_regime") == "catabolic":
            conjecture = "ENTROPIC_DECAY_DETECTED"
        else:
            conjecture = "PHASE_ALIGNMENT_STABLE"

        certificate = MetabolicCertificate(
            module_id="metabolic_core",
            integrated_information=integrated_info,
            metabolic_state=metabolic_state,
            regeneration_metrics=regeneration_metrics,
            constructor_conjecture=conjecture,
            timestamp=time.time(),
        )

        return certificate.to_dict()

    except Exception as e:
        logger.error(f"Metabolic Certificate error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Certificate generation failed: {str(e)}"
        )


# ---------------------------------------------------------------------------
# Management Endpoints
# ---------------------------------------------------------------------------


@router.get("/health")
async def get_metabolic_health() -> Dict[str, Any]:
    """Health check for the metabolic router."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "engine_active": True,
        "entropy_history_length": len(_metabolic_engine._entropy_history),
        "hunger_history_length": len(_metabolic_engine._hunger_history),
    }


__all__ = [
    "router",
    "MetabolicEngine",
    "EntropyState",
    "HungerDrive",
    "LanePulse",
    "MetabolicCertificate",
    "MetabolicRegime",
    "HungerLevel",
]
