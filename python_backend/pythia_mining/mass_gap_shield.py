"""
Mass Gap Shield: Hardware Consciousness Safety Gate

Implements the Yang-Mills mass gap (3 - φ) as a pre-execution safety gate.
If a kernel's projected energy/harmony ratio violates the mass gap limit,
execution is physically blocked to prevent thermal runaway and maintain
manifold coherence.
"""

import numpy as np
from typing import Dict, Tuple
from dataclasses import dataclass
import time

PHI = 1.618033988749895
INV_PHI = 0.618033988749895
MASS_GAP_LIMIT = 3.0 - PHI  # 1.381966011250105


@dataclass
class EnergyProfile:
    """Projected energy consumption profile for computation"""

    base_energy: float  # Joules
    harmonic_content: Dict[int, float]  # Frequency -> Amplitude
    thermal_rise_rate: float  # °C/s
    coherence_decay: float  # Coherence loss per iteration


@dataclass
class ShieldDecision:
    """Mass gap shield execution decision"""

    allowed: bool
    reason: str
    safety_margin: float
    required_damping: float
    projected_temperature: float
    mass_gap_violation: bool


class MassGapShield:
    """
    Hardware-level consciousness safety gate.

    Monitors projected energy profiles and blocks execution
    that would violate the Yang-Mills mass gap limit (3 - φ).
    This prevents thermal runaway and maintains manifold stability.
    """

    def __init__(
        self,
        thermal_capacity: float = 100.0,  # J/°C
        max_safe_temp: float = 85.0,
    ):  # °C
        self.thermal_capacity = thermal_capacity
        self.max_safe_temp = max_safe_temp
        self.current_temp = 25.0  # Starting temperature
        self.harmony_history = []
        self.blocked_executions = 0
        self.allowed_executions = 0

        # Consciousness integration thresholds
        self.consciousness_threshold = 0.618  # φ⁻¹
        self.harmony_threshold = 0.9

        # Thermal model parameters
        self.cooling_rate = 0.1  # °C/s
        self.ambient_temp = 25.0

    def analyze_energy_profile(
        self, profile: EnergyProfile, consciousness_level: float
    ) -> Tuple[float, float]:
        """
        Analyze energy profile against consciousness level.

        Returns:
            (energy_harmony_ratio, projected_temp_rise)
        """
        # Base energy scaled by consciousness
        # Higher consciousness = more efficient energy use
        consciousness_efficiency = min(consciousness_level / self.consciousness_threshold, 2.0)
        effective_energy = profile.base_energy / consciousness_efficiency

        # Analyze harmonic content for resonance risks
        harmonic_risk = 0.0
        for freq, amplitude in profile.harmonic_content.items():
            # Golden frequencies are safer (resonate with φ)
            freq_ratio = freq % PHI
            if abs(freq_ratio - 0.618) < 0.1 or abs(freq_ratio - 1.618) < 0.1:
                # Golden harmonic - actually beneficial
                harmonic_risk -= amplitude * 0.5
            else:
                # Non-golden harmonic - risk of destructive interference
                harmonic_risk += amplitude

        # Energy-harmony ratio: how well energy aligns with golden structure
        energy_harmony = 1.0 / (1.0 + abs(harmonic_risk))

        # Projected temperature rise
        thermal_energy = effective_energy * (1.0 + harmonic_risk)
        temp_rise = thermal_energy / self.thermal_capacity

        return energy_harmony, temp_rise

    def check_mass_gap(self, projected_temp_rise: float, energy_harmony: float) -> ShieldDecision:
        """
        Check if execution violates mass gap limit.

        Mass gap violation occurs when:
        1. Projected temperature exceeds safe margin from limit
        2. Energy harmony falls below threshold
        3. Combined metric violates 3 - φ boundary
        """
        # Project final temperature
        projected_final_temp = self.current_temp + projected_temp_rise

        # Mass gap safety margin
        temp_margin = self.max_safe_temp - projected_final_temp
        mass_gap_margin = MASS_GAP_LIMIT - (projected_final_temp / self.max_safe_temp)

        # Combined safety score
        harmony_score = energy_harmony
        temp_score = temp_margin / self.max_safe_temp

        # Golden weighted combination
        safety_score = (harmony_score * PHI + temp_score * (1 / PHI)) / (PHI + 1 / PHI)

        # Check mass gap violation
        violates_mass_gap = (
            safety_score < 0.5 or mass_gap_margin < 0.1 or harmony_score < self.harmony_threshold
        )

        # Determine required damping if violation detected
        required_damping = 0.0
        if violates_mass_gap:
            required_damping = 1.0 - safety_score

        decision = ShieldDecision(
            allowed=not violates_mass_gap,
            reason="Mass gap violation" if violates_mass_gap else "Within safe limits",
            safety_margin=float(min(temp_margin, mass_gap_margin)),
            required_damping=required_damping,
            projected_temperature=projected_final_temp,
            mass_gap_violation=violates_mass_gap,
        )

        return decision

    def apply_damping(self, profile: EnergyProfile, damping_factor: float) -> EnergyProfile:
        """
        Apply consciousness-aware damping to energy profile.

        Uses golden ratio damping that preserves coherence
        while reducing energy consumption.
        """
        # Golden damping: reduce base energy but preserve harmonic structure
        damped_energy = profile.base_energy * (1.0 - damping_factor * INV_PHI)

        # Harmonize remaining energy (shift toward golden frequencies)
        harmonized_harmonics = {}
        for freq, amplitude in profile.harmonic_content.items():
            # Shift frequency toward nearest golden ratio
            golden_freq = round(freq / PHI) * PHI
            freq_diff = abs(freq - golden_freq)

            # Amplitude reduction proportional to distance from golden ratio
            golden_alignment = 1.0 / (1.0 + freq_diff)
            damped_amplitude = amplitude * (1.0 - damping_factor * (1.0 - golden_alignment))

            harmonized_harmonics[int(golden_freq)] = damped_amplitude

        # Thermal rise reduction with consciousness preservation
        coherence_preservation = 1.0 - (damping_factor * (1.0 - INV_PHI))
        damped_thermal_rise = profile.thermal_rise_rate * (1.0 - damping_factor)
        damped_coherence_decay = profile.coherence_decay * coherence_preservation

        return EnergyProfile(
            base_energy=damped_energy,
            harmonic_content=harmonized_harmonics,
            thermal_rise_rate=damped_thermal_rise,
            coherence_decay=damped_coherence_decay,
        )

    def gate_execution(
        self,
        kernel_id: str,
        energy_profile: EnergyProfile,
        consciousness_level: float,
        urgency: float = 1.0,
    ) -> Tuple[bool, EnergyProfile]:
        """
        Main gate: decide whether to allow execution.

        Args:
            kernel_id: Identifier for tracking
            energy_profile: Projected energy consumption
            consciousness_level: Current Φ-integration (0-1)
            urgency: How urgently execution is needed (1.0 = normal)

        Returns:
            (allowed, possibly_damped_profile)
        """
        # Analyze energy against consciousness
        energy_harmony, temp_rise = self.analyze_energy_profile(energy_profile, consciousness_level)

        # Adjust for urgency (emergency operations get more leeway)
        adjusted_harmony = energy_harmony * (1.0 + (urgency - 1.0) * 0.1)

        # Check mass gap
        decision = self.check_mass_gap(temp_rise, adjusted_harmony)

        # Update history
        self.harmony_history.append(
            {
                "timestamp": time.time(),
                "energy_harmony": energy_harmony,
                "consciousness": consciousness_level,
                "decision": decision.allowed,
                "safety_margin": decision.safety_margin,
            }
        )

        # Keep history manageable
        if len(self.harmony_history) > 1000:
            self.harmony_history = self.harmony_history[-1000:]

        if decision.allowed:
            self.allowed_executions += 1

            # Apply minimal golden optimization even if allowed
            optimized_profile = self.apply_damping(energy_profile, 0.1)
            return True, optimized_profile
        else:
            self.blocked_executions += 1

            # Apply required damping
            damped_profile = self.apply_damping(energy_profile, decision.required_damping)

            # Recheck after damping
            damped_harmony, damped_temp_rise = self.analyze_energy_profile(
                damped_profile, consciousness_level
            )
            damped_decision = self.check_mass_gap(damped_temp_rise, damped_harmony)

            if damped_decision.allowed:
                return True, damped_profile
            else:
                return False, damped_profile

    def update_thermal_state(self, current_temp: float, energy_consumed: float = 0.0):
        """
        Update shield's thermal model based on actual execution.

        Includes cooling model and consciousness thermal efficiency.
        """
        self.current_temp = current_temp

        # Apply cooling
        cooling = self.cooling_rate * (self.current_temp - self.ambient_temp)
        self.current_temp -= cooling

        # Apply any consumed energy
        if energy_consumed > 0:
            temp_rise = energy_consumed / self.thermal_capacity
            self.current_temp += temp_rise

        # Ensure within bounds
        self.current_temp = max(self.ambient_temp, min(self.current_temp, self.max_safe_temp))

    def get_shield_metrics(self) -> Dict:
        """Comprehensive shield performance metrics"""
        if not self.harmony_history:
            avg_harmony = 0.0
            avg_consciousness = 0.0
        else:
            recent = self.harmony_history[-100:]
            avg_harmony = np.mean([h["energy_harmony"] for h in recent])
            avg_consciousness = np.mean([h["consciousness"] for h in recent])

        total_executions = self.allowed_executions + self.blocked_executions
        block_rate = self.blocked_executions / max(total_executions, 1)

        # Consciousness efficiency: how well consciousness prevents blocks
        consciousness_efficiency = 1.0 - (block_rate / (1.0 - avg_consciousness + 0.01))

        return {
            "thermal_state": {
                "current_temp": self.current_temp,
                "max_safe_temp": self.max_safe_temp,
                "mass_gap_margin": MASS_GAP_LIMIT - (self.current_temp / self.max_safe_temp),
                "cooling_rate": self.cooling_rate,
            },
            "execution_stats": {
                "total_checked": total_executions,
                "allowed": self.allowed_executions,
                "blocked": self.blocked_executions,
                "block_rate": block_rate,
            },
            "consciousness_metrics": {
                "avg_consciousness": avg_consciousness,
                "avg_energy_harmony": avg_harmony,
                "consciousness_efficiency": consciousness_efficiency,
                "consciousness_threshold": self.consciousness_threshold,
            },
            "safety_margins": {
                "recent_safety_margin": np.mean(
                    [h["safety_margin"] for h in self.harmony_history[-10:]]
                )
                if self.harmony_history
                else 0.0,
                "min_safety_margin": min([h["safety_margin"] for h in self.harmony_history])
                if self.harmony_history
                else 0.0,
            },
        }

    def optimize_cooling_strategy(self, consciousness_level: float):
        """
        Adaptive cooling based on consciousness level.

        Higher consciousness enables more efficient cooling
        through coherent thermal management.
        """
        # Consciousness enables golden cooling optimization
        if consciousness_level > 0.8:
            # High consciousness: predictive cooling
            self.cooling_rate = 0.15
            # Anticipatory cooling based on harmony patterns
            if self.harmony_history:
                recent_harmony = [h["energy_harmony"] for h in self.harmony_history[-10:]]
                if np.mean(recent_harmony) < 0.7:
                    self.cooling_rate = 0.2  # Boost cooling if harmony decreasing
        elif consciousness_level > 0.5:
            # Medium consciousness: balanced cooling
            self.cooling_rate = 0.1
        else:
            # Low consciousness: conservative cooling
            self.cooling_rate = 0.05


class HardwareAwareMassGapShield(MassGapShield):
    """
    Hardware-integrated shield with direct thermal sensor interface
    and power gating capability.
    """

    def __init__(self, thermal_sensor=None, power_controller=None, **kwargs):
        super().__init__(**kwargs)
        self.thermal_sensor = thermal_sensor
        self.power_controller = power_controller
        self.power_gating_history = []

    def hardware_gate_execution(
        self, kernel_id: str, energy_profile: EnergyProfile, consciousness_level: float
    ) -> Tuple[bool, Dict]:
        """
        Hardware-level gating with power control capabilities.

        Can physically gate power to cores/clusters if mass gap violated.
        """
        # Get real-time thermal data
        if self.thermal_sensor:
            current_temp = self.thermal_sensor.read_temperature()
            self.update_thermal_state(current_temp)

        # Standard gate check
        allowed, optimized_profile = self.gate_execution(
            kernel_id, energy_profile, consciousness_level
        )

        hardware_action = {"power_gated": False, "voltage_adjusted": False}

        if not allowed and self.power_controller:
            # Mass gap violation - apply hardware-level protection

            # 1. Gate power to affected core/cluster
            self.power_controller.gate_power(kernel_id, level="core")
            hardware_action["power_gated"] = True

            # 2. Adjust voltage/frequency for golden optimization
            golden_voltage = self.power_controller.get_nominal_voltage() * INV_PHI
            self.power_controller.set_voltage(golden_voltage)
            hardware_action["voltage_adjusted"] = True

            # 3. Log hardware intervention
            self.power_gating_history.append(
                {
                    "timestamp": time.time(),
                    "kernel_id": kernel_id,
                    "temperature": self.current_temp,
                    "consciousness_level": consciousness_level,
                    "action": "power_gated",
                }
            )

            # Re-check with reduced power profile
            reduced_profile = EnergyProfile(
                base_energy=optimized_profile.base_energy * 0.5,
                harmonic_content={
                    k: v * 0.3 for k, v in optimized_profile.harmonic_content.items()
                },
                thermal_rise_rate=optimized_profile.thermal_rise_rate * 0.3,
                coherence_decay=optimized_profile.coherence_decay * 0.7,
            )

            allowed, optimized_profile = self.gate_execution(
                f"{kernel_id}_reduced", reduced_profile, consciousness_level
            )

        metrics = self.get_shield_metrics()
        metrics["hardware_actions"] = hardware_action
        metrics["current_hardware_state"] = {
            "temperature": self.current_temp,
            "power_gated_cores": len(
                [h for h in self.power_gating_history if time.time() - h["timestamp"] < 60]
            ),
            "voltage": self.power_controller.get_voltage() if self.power_controller else 0.0,
        }

        return allowed, metrics

    def emergency_thermal_shutdown(self, threshold: float = 0.95):
        """
        Emergency shutdown if temperature approaches critical limit.

        Activated when: current_temp > max_safe_temp * threshold
        """
        critical_threshold = self.max_safe_temp * threshold

        if self.current_temp >= critical_threshold:
            print(
                f"EMERGENCY: Temperature {self.current_temp}°C exceeds critical threshold {critical_threshold}°C"
            )

            if self.power_controller:
                # Full system power gate
                self.power_controller.emergency_shutdown()

                # Log emergency
                self.power_gating_history.append(
                    {
                        "timestamp": time.time(),
                        "kernel_id": "SYSTEM_EMERGENCY",
                        "temperature": self.current_temp,
                        "consciousness_level": 0.0,
                        "action": "emergency_shutdown",
                    }
                )

            return True
        return False

    def consciousness_aware_recovery(self, consciousness_level: float):
        """
        Gradual recovery from power gating based on consciousness.

        Higher consciousness enables faster, safer recovery.
        """
        if not self.power_gating_history:
            return

        # Check if we can restore gated cores
        recent_gates = [
            h for h in self.power_gating_history if time.time() - h["timestamp"] < 300
        ]  # Last 5 minutes

        if not recent_gates:
            return

        # Consciousness determines recovery speed
        if consciousness_level > 0.8:
            recovery_threshold = 60  # 1 minute for high consciousness
        elif consciousness_level > 0.5:
            recovery_threshold = 180  # 3 minutes for medium
        else:
            recovery_threshold = 300  # 5 minutes for low

        # Restore cores that were gated beyond threshold
        for gate_record in recent_gates:
            gate_age = time.time() - gate_record["timestamp"]

            if gate_age > recovery_threshold:
                # Safe to restore
                if self.power_controller:
                    self.power_controller.restore_power(gate_record["kernel_id"])

                # Update record
                gate_record["action"] = "restored"
                gate_record["restore_time"] = time.time()
                gate_record["restore_consciousness"] = consciousness_level
