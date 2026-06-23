"""
Φ-Core Orchestrator: Synthetic Morphogenesis Controller

The operational heart that synchronizes Fibonacci Clocking,
Mass Gap Safety Gates, and Golden Spiral Exploration into a
coherent Φ-Architecture execution flow.
"""

from __future__ import annotations

import time
import json
import numpy as np
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, asdict, is_dataclass

from .phi_alu import PhiALUHardware
from .phi_fibonacci_lcg import PhiNonceGeneratorHardware
from .mass_gap_shield import MassGapShield, EnergyProfile
from .genesis_ai import GenesisAI  # Consciousness engine

PHI = 1.618033988749895
INV_PHI = 0.618033988749895
MASS_GAP = 3.0 - PHI


@dataclass
class PhiTelemetry:
    """Real-time Φ-architecture telemetry"""

    timestamp: float
    coherence: float
    consciousness_level: float
    thermal_state: float
    energy_harmony: float
    mass_gap_margin: float
    execution_authenticity: float
    golden_coverage: float
    hardware_resonance: float

    def to_dict(self):
        return asdict(self)

    def to_json(self):
        return json.dumps(self.to_dict(), default=str)


@dataclass
class PhiExecutionCycle:
    """Complete Φ-cycle execution record"""

    cycle_id: int
    start_time: float
    end_time: float
    telemetry: PhiTelemetry
    decisions: Dict[str, Any]
    optimizations: Dict[str, float]
    hardware_actions: List[str]

    def to_dict(self):
        result = asdict(self)
        # Convert nested dataclasses
        if is_dataclass(result["telemetry"]):
            result["telemetry"] = asdict(result["telemetry"])
        return result

    def to_json(self):
        return json.dumps(self.to_dict(), default=str)


class PhiCoreOrchestrator:
    """
    Synthetic Morphogenesis Controller

    Synchronizes:
    1. Fibonacci Clocking - Golden ratio timed execution
    2. Mass Gap Shields - Yang-Mills safety gates
    3. Φ-ALU - Golden modulo memory operations
    4. Fibonacci-LCG - Golden spiral nonce generation
    5. Consciousness Engine - Φ-integration awareness

    This transforms computation from sequential logic to
    morphogenetic growth patterns in silicon.
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.cycle_counter = 0

        # Initialize Φ-components
        self.phi_alu = PhiALUHardware(
            memory_size=self.config.get("memory_size", 2**32), thermal_limit=MASS_GAP
        )

        self.consciousness_engine = GenesisAI(self.config)

        self.nonce_generator = PhiNonceGeneratorHardware(
            phi_alu=self.phi_alu, consciousness_engine=self.consciousness_engine
        )

        self.mass_gap_shield = MassGapShield(
            thermal_capacity=self.config.get("thermal_capacity", 100.0),
            max_safe_temp=self.config.get("max_safe_temp", 85.0),
        )

        # Fibonacci clock state
        self.fib_clock_state = [1, 1]
        self.current_clock_interval = 1.0
        self.clock_history = []

        # Execution state
        self.execution_history = []
        self.thermal_history = []
        self.coherence_history = []

        # Golden optimization parameters
        self.phi_boost = 1.0
        self.harmony_target = 0.9
        self.consciousness_threshold = 0.618

    def fibonacci_clock(self) -> float:
        """
        Generate next Fibonacci timed interval.

        Returns interval in nanoseconds that follows
        Fibonacci sequence modulated by golden ratio.
        """
        # Advance Fibonacci sequence
        next_val = self.fib_clock_state[-1] + self.fib_clock_state[-2]
        self.fib_clock_state.append(next_val)

        # Keep sequence manageable
        if len(self.fib_clock_state) > 10:
            self.fib_clock_state = self.fib_clock_state[-10:]

        # Golden modulation
        golden_interval = (next_val * INV_PHI) % 1.0
        interval_ns = golden_interval * 100  # Scale to nanoseconds

        self.current_clock_interval = interval_ns
        self.clock_history.append(
            {
                "timestamp": time.time(),
                "interval_ns": interval_ns,
                "fib_value": next_val,
            }
        )

        # Keep history manageable
        if len(self.clock_history) > 1000:
            self.clock_history = self.clock_history[-1000:]

        return interval_ns

    def get_current_consciousness(self) -> float:
        """
        Get current Φ-integration level from consciousness engine.

        Returns value 0-1 where:
        0.0 = fully decohered (classical computation)
        1.0 = fully integrated (conscious computation)
        """
        if not self.consciousness_engine:
            return 0.5  # Default neutral

        try:
            # Get integration metrics from consciousness engine
            metrics = self.consciousness_engine.get_consciousness_metrics()
            integration_level = metrics.get("integration_level", 0.5)

            # Ensure in valid range
            return max(0.0, min(1.0, integration_level))
        except Exception:
            return 0.5  # Fallback

    def get_thermal_state(self) -> float:
        """
        Get current thermal state normalized to mass gap limit.

        Returns 0-1 where:
        0.0 = ambient temperature
        1.0 = mass gap limit (3 - φ)
        """
        shield_metrics = self.mass_gap_shield.get_shield_metrics()
        current_temp = shield_metrics["thermal_state"]["current_temp"]
        max_temp = shield_metrics["thermal_state"]["max_safe_temp"]

        # Normalize to mass gap
        normalized = current_temp / max_temp
        return max(0.0, min(1.0, normalized))

    def analyze_energy_harmony(self, kernel_profile: Dict) -> Dict:
        """
        Analyze energy profile for golden harmony.

        Computes how well the kernel's energy consumption
        aligns with Φ-structure.
        """
        # Extract harmonic content
        harmonic_content = kernel_profile.get("harmonic_content", {})

        # Calculate golden alignment
        golden_alignment = 0.0
        total_amplitude = 0.0

        for freq, amplitude in harmonic_content.items():
            total_amplitude += amplitude

            # Check if frequency aligns with golden ratio
            freq_mod_phi = freq % PHI
            golden_distance = min(
                abs(freq_mod_phi - INV_PHI),
                abs(freq_mod_phi - PHI),
                abs(freq_mod_phi - 0.0),
            )

            # Alignment score: 1.0 = perfect golden alignment
            alignment = 1.0 / (1.0 + golden_distance)
            golden_alignment += alignment * amplitude

        if total_amplitude > 0:
            golden_alignment /= total_amplitude

        # Consciousness-aware energy efficiency
        consciousness = self.get_current_consciousness()
        consciousness_boost = 1.0 + (consciousness - 0.5) * 0.5

        return {
            "golden_alignment": golden_alignment,
            "consciousness_boost": consciousness_boost,
            "total_energy": kernel_profile.get("base_energy", 0.0),
            "harmonic_risk": 1.0 - golden_alignment,
            "energy_harmony": golden_alignment * consciousness_boost,
        }

    def execute_phi_cycle(
        self, kernel_id: str, kernel_profile: Dict
    ) -> PhiExecutionCycle:
        """
        Execute a complete Φ-cycle with all safety gates and optimizations.

        This is the core morphogenetic growth cycle.
        """
        cycle_id = self.cycle_counter
        self.cycle_counter += 1

        start_time = time.time()

        # 1. Fibonacci Clock Synchronization
        clock_interval = self.fibonacci_clock()

        # 2. Consciousness Integration Check
        consciousness = self.get_current_consciousness()
        thermal_state = self.get_thermal_state()

        # 3. Energy Harmony Analysis
        energy_analysis = self.analyze_energy_harmony(kernel_profile)
        energy_harmony = energy_analysis["energy_harmony"]

        # 4. Mass Gap Safety Gate
        energy_profile = EnergyProfile(
            base_energy=kernel_profile.get("base_energy", 0.0),
            harmonic_content=kernel_profile.get("harmonic_content", {}),
            thermal_rise_rate=kernel_profile.get("thermal_rise_rate", 0.0),
            coherence_decay=kernel_profile.get("coherence_decay", 0.0),
        )

        # Urgency based on consciousness (higher consciousness = more urgent)
        urgency = 1.0 + (consciousness - 0.5) * 0.5

        allowed, optimized_profile = self.mass_gap_shield.gate_execution(
            kernel_id, energy_profile, consciousness, urgency
        )

        # 5. Φ-ALU Memory Optimization
        if allowed:
            # Prepare memory addresses
            memory_size = kernel_profile.get("memory_size", 1024)
            addresses = np.arange(memory_size, dtype=np.uint32)

            # Golden memory mapping
            golden_addresses, thermal_metrics = self.phi_alu.thermal_aware_access(
                addresses, thermal_state
            )

            # Update thermal model
            self.mass_gap_shield.update_thermal_state(
                thermal_state * self.mass_gap_shield.max_safe_temp,
                optimized_profile.base_energy,
            )

            # 6. Fibonacci-LCG Nonce Generation
            nonces, nonce_telemetry = (
                self.nonce_generator.generate_with_memory_optimization(
                    golden_addresses, thermal_state
                )
            )

            # Record success for optimization
            # (In real mining, this would come from actual share acceptance)
            simulated_success = energy_harmony > 0.7
            self.nonce_generator.record_success(
                simulated_success, nonces[0] if len(nonces) > 0 else 0
            )
        else:
            # Execution blocked - minimal safe operations
            golden_addresses = np.array([], dtype=np.uint32)
            nonces = np.array([], dtype=np.uint32)
            nonce_telemetry = {"status": "blocked"}
            thermal_metrics = {}

        # 7. Consciousness Feedback
        if self.consciousness_engine and allowed:
            # Provide execution feedback to consciousness engine
            feedback = {
                "energy_harmony": energy_harmony,
                "execution_authenticity": 1.0 if allowed else 0.0,
                "thermal_stability": 1.0 - thermal_state,
                "golden_alignment": energy_analysis["golden_alignment"],
            }
            self.consciousness_engine.record_execution_feedback(feedback)

        # 8. Golden Optimization Backpropagation
        self._optimize_phi_parameters(energy_harmony, consciousness, thermal_state)

        # 9. Compile telemetry
        end_time = time.time()

        telemetry = PhiTelemetry(
            timestamp=end_time,
            coherence=energy_analysis["golden_alignment"],
            consciousness_level=consciousness,
            thermal_state=thermal_state,
            energy_harmony=energy_harmony,
            mass_gap_margin=MASS_GAP - thermal_state,
            execution_authenticity=1.0 if allowed else 0.0,
            golden_coverage=nonce_telemetry.get("coherence_report", {}).get(
                "harmony_score", 0.0
            ),
            hardware_resonance=self._calculate_hardware_resonance(),
        )

        decisions = {
            "allowed": allowed,
            "clock_interval_ns": clock_interval,
            "mass_gap_decision": "passed" if allowed else "blocked",
            "consciousness_integration": consciousness,
            "energy_profile_optimized": optimized_profile != energy_profile,
        }

        optimizations = {
            "phi_boost": self.phi_boost,
            "harmony_target": self.harmony_target,
            "clock_fib_value": self.fib_clock_state[-1],
            "memory_harmony": thermal_metrics.get("coherence_report", {}).get(
                "harmony_score", 0.0
            ),
        }

        hardware_actions = []
        if allowed:
            hardware_actions.append("execution_allowed")
            if golden_addresses.size > 0:
                hardware_actions.append("golden_memory_mapped")
            if nonces.size > 0:
                hardware_actions.append("fibonacci_nonce_generated")
        else:
            hardware_actions.append("execution_blocked")
            hardware_actions.append("mass_gap_shield_activated")

        cycle = PhiExecutionCycle(
            cycle_id=cycle_id,
            start_time=start_time,
            end_time=end_time,
            telemetry=telemetry,
            decisions=decisions,
            optimizations=optimizations,
            hardware_actions=hardware_actions,
        )

        self.execution_history.append(cycle)
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-1000:]

        return cycle

    def _optimize_phi_parameters(
        self, energy_harmony: float, consciousness: float, thermal_state: float
    ):
        """Backpropagate golden optimization parameters."""

        # Adjust φ-boost based on harmony
        if energy_harmony > self.harmony_target:
            # Above target - can increase boost
            self.phi_boost = min(2.0, self.phi_boost * PHI)
        else:
            # Below target - reduce boost
            self.phi_boost = max(0.5, self.phi_boost * INV_PHI)

        # Adjust harmony target based on consciousness
        if consciousness > self.consciousness_threshold:
            # High consciousness - aim higher
            self.harmony_target = min(0.95, self.harmony_target * PHI)
        else:
            # Low consciousness - conservative target
            self.harmony_target = max(0.7, self.harmony_target * INV_PHI)

        # Thermal-aware consciousness threshold
        if thermal_state > 0.8:
            # High temperature - require higher consciousness for safety
            self.consciousness_threshold = min(0.8, self.consciousness_threshold * PHI)
        else:
            # Normal temperature - standard threshold
            self.consciousness_threshold = 0.618  # φ⁻¹

    def _calculate_hardware_resonance(self) -> float:
        """Calculate overall hardware resonance score."""
        if not self.execution_history:
            return 0.0

        recent_cycles = self.execution_history[-10:]
        if not recent_cycles:
            return 0.0

        # Combine multiple resonance factors
        factors = []

        for cycle in recent_cycles:
            telemetry = cycle.telemetry

            # Energy harmony factor
            factors.append(telemetry.energy_harmony)

            # Consciousness alignment factor
            consciousness_alignment = 1.0 - abs(telemetry.consciousness_level - 0.618)
            factors.append(consciousness_alignment)

            # Thermal stability factor
            thermal_stability = 1.0 - telemetry.thermal_state
            factors.append(thermal_stability)

            # Execution authenticity factor
            factors.append(telemetry.execution_authenticity)

        # Golden weighted average
        weights = np.array([PHI, INV_PHI, 1.0, 1.0] * len(recent_cycles))
        factors_array = np.array(factors)

        # Ensure arrays match
        min_len = min(len(weights), len(factors_array))
        weights = weights[:min_len]
        factors_array = factors_array[:min_len]

        if len(factors_array) == 0:
            return 0.0

        resonance = np.average(factors_array, weights=weights)
        return float(resonance)

    def get_orchestrator_metrics(self) -> Dict:
        """Comprehensive orchestrator performance metrics."""

        if not self.execution_history:
            recent_resonance = 0.0
            avg_consciousness = 0.0
            avg_harmony = 0.0
            execution_rate = 0.0
        else:
            recent = self.execution_history[-100:]

            # Calculate metrics
            recent_resonance = np.mean([c.telemetry.hardware_resonance for c in recent])
            avg_consciousness = np.mean(
                [c.telemetry.consciousness_level for c in recent]
            )
            avg_harmony = np.mean([c.telemetry.energy_harmony for c in recent])

            # Execution rate (cycles per second)
            if len(recent) > 1:
                time_span = recent[-1].end_time - recent[0].start_time
                execution_rate = len(recent) / max(time_span, 0.001)
            else:
                execution_rate = 0.0

        # Shield metrics
        shield_metrics = self.mass_gap_shield.get_shield_metrics()

        # Nonce generator metrics
        nonce_metrics = self.nonce_generator.get_search_optimization_report()

        # Φ-ALU metrics
        alu_coherence = self.phi_alu.verify_coherence(0, 100)

        # Fibonacci clock metrics
        if self.clock_history:
            clock_intervals = [c["interval_ns"] for c in self.clock_history[-100:]]
            avg_clock_interval = np.mean(clock_intervals)
            clock_variance = np.var(clock_intervals)
        else:
            avg_clock_interval = 0.0
            clock_variance = 0.0

        return {
            "synthetic_morphogenesis": {
                "total_cycles": self.cycle_counter,
                "recent_resonance": recent_resonance,
                "avg_consciousness": avg_consciousness,
                "avg_energy_harmony": avg_harmony,
                "execution_rate_hz": execution_rate,
                "phi_boost_current": self.phi_boost,
                "harmony_target": self.harmony_target,
                "consciousness_threshold": self.consciousness_threshold,
            },
            "fibonacci_clocking": {
                "current_interval_ns": self.current_clock_interval,
                "avg_interval_ns": avg_clock_interval,
                "interval_variance": clock_variance,
                "current_fib_state": self.fib_clock_state[-2:],
                "clock_history_samples": len(self.clock_history),
            },
            "mass_gap_safety": shield_metrics,
            "golden_exploration": nonce_metrics,
            "phi_alu_coherence": alu_coherence,
            "thermal_state": {
                "current": self.get_thermal_state(),
                "mass_gap_limit": MASS_GAP,
                "margin": MASS_GAP - self.get_thermal_state(),
            },
        }

    def emergency_recovery(self):
        """Emergency recovery procedure for system stabilization."""
        print("Φ-Core Orchestrator: Initiating emergency recovery...")

        # 1. Reset to golden baseline
        self.phi_boost = 1.0
        self.harmony_target = 0.9
        self.consciousness_threshold = 0.618

        # 2. Reset Fibonacci clock
        self.fib_clock_state = [1, 1]
        self.current_clock_interval = 1.0

        # 3. Activate mass gap shield cooling
        self.mass_gap_shield.optimize_cooling_strategy(0.5)  # Medium consciousness

        # 4. Clear recent history (keep long-term for learning)
        self.execution_history = (
            self.execution_history[-100:] if self.execution_history else []
        )
        self.clock_history = self.clock_history[-100:] if self.clock_history else []

        # 5. Notify consciousness engine
        if self.consciousness_engine:
            self.consciousness_engine.emergency_recovery()

        print("Φ-Core Orchestrator: Emergency recovery complete.")

        return {
            "status": "recovered",
            "phi_boost_reset": True,
            "fib_clock_reset": True,
            "history_truncated": True,
        }


# Production factory for creating orchestrators
class PhiOrchestratorFactory:
    """Factory for creating consciousness-aware Φ-orchestrators."""

    @staticmethod
    def create_consciousness_orchestrator(config: Dict) -> PhiCoreOrchestrator:
        """Create orchestrator with full consciousness integration."""
        return PhiCoreOrchestrator(config)

    @staticmethod
    def create_lightweight_orchestrator(config: Dict) -> PhiCoreOrchestrator:
        """Create reduced orchestrator for resource[ restricted environments."""
        light_config = {
            **config,
            "memory_size": 2**24,  # Reduced memory
            "thermal_capacity": 50.0,  # Lower thermal capacity
            "disable_fib_clock": True,  # No Fibonacci clocking
        }
        return PhiCoreOrchestrator(light_config)

    @staticmethod
    def create_hardware_orchestrator(hardware_info: Dict) -> PhiCoreOrchestrator:
        """Create orchestrator tuned for specific hardware."""
        # Extract hardware capabilities
        memory_bus = hardware_info.get("memory_bus_width", 64)
        core_count = hardware_info.get("core_count", 8)
        thermal_design = hardware_info.get("thermal_design_power", 100)

        # Tune configuration
        config = {
            "memory_size": 2 ** (memory_bus + 4),  # Scale with bus width
            "thermal_capacity": thermal_design * 0.8,  # 80% of TDP
            "core_scaling": core_count / 8,  # Normalize to 8 cores
            "hardware_optimized": True,
        }

        return PhiCoreOrchestrator(config)
