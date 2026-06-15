"""Phi Tuner for harmonic backpropagation and real-time optimization.

This module performs 'Harmonic Backpropagation' to maximize hardware coherence.
Updates the PhiScalingEngine parameters in real-time to hunt for the Singular regime.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from .phi_config import PHI, PHI_INV


class PhiTuner:
    """Performs harmonic backpropagation to maximize hardware coherence.

    Unlike standard backpropagation that minimizes error, this tuner maximizes
    harmony by adjusting phi scaling parameters toward the Singular attractor.
    The system learns which specific frequencies yield the most "Massive" (valuable)
    computational states.
    """

    def __init__(
        self,
        engine: Any,
        *,
        learning_rate: float = 0.01,
        target_coherence: float | None = None,
        min_exponent: float = 0.5,
        max_exponent: float = 2.0,
    ):
        """Initialize the Phi Tuner.

        Args:
            engine: The phi scaling engine to tune (must have phi_exponent attribute)
            learning_rate: Base learning rate for gradient updates
            target_coherence: Target coherence for Singular regime (defaults to PHI²/2)
            min_exponent: Minimum allowed phi exponent (safety clip)
            max_exponent: Maximum allowed phi exponent (safety clip)
        """
        self.engine = engine
        self.PHI = PHI
        self.PHI_INV = PHI_INV
        # Scaled learning rate using golden ratio
        self.eta = learning_rate * self.PHI_INV
        # Target coherence for Singular regime (PHI²/2 scaled for stability)
        self.target_coherence = float(
            target_coherence if target_coherence is not None else ((self.PHI ** 2) / 2.0)
        )
        self.min_exponent = float(min_exponent)
        self.max_exponent = float(max_exponent)
        # Track tuning history for diagnostics
        self._tuning_history: list[dict[str, Any]] = []

    def tune(self, current_coherence: float, authenticity: float) -> dict[str, Any]:
        """Adjusts the phi_exponent based on distance from Singular attractor.

        Args:
            current_coherence: Current hardware coherence score (0.0 to 1.0)
            authenticity: Hardware authenticity score from Mass Gap Protector (0.0 to 1.0)

        Returns:
            Dictionary containing tuning result and diagnostic information
        """
        # If authenticity is low, we don't tune (prevents learning from noise/attacks)
        if authenticity < 0.70:
            # Cool down period - reduce exponent to conservative mode
            old_exponent = getattr(self.engine, "phi_exponent", 1.0)
            new_exponent = old_exponent * 0.95
            if hasattr(self.engine, "phi_exponent"):
                self.engine.phi_exponent = new_exponent

            result = {
                "tuned": False,
                "reason": "low_authenticity_cooling_down",
                "old_exponent": float(old_exponent),
                "new_exponent": float(new_exponent),
                "authenticity": authenticity,
                "coherence": current_coherence,
            }
            self._tuning_history.append(result)
            return result

        # Calculate error from target coherence
        error = self.target_coherence - current_coherence

        # Gradient Update: The 'Golden' Step
        # We adjust the exponent toward the target using PHI-weighted steps
        delta_exponent = self.eta * error * self.PHI

        # Get current exponent
        old_exponent = getattr(self.engine, "phi_exponent", 1.0)

        # Update the engine's active scaling exponent
        new_exponent = old_exponent + delta_exponent

        # Safety Clip: Ensure we don't hit resonance collapse
        new_exponent = np.clip(new_exponent, self.min_exponent, self.max_exponent)

        # Apply the update if engine has the attribute
        if hasattr(self.engine, "phi_exponent"):
            self.engine.phi_exponent = new_exponent

        result = {
            "tuned": True,
            "reason": "harmonic_gradient_descent",
            "old_exponent": float(old_exponent),
            "new_exponent": float(new_exponent),
            "delta_exponent": float(delta_exponent),
            "error": float(error),
            "target_coherence": self.target_coherence,
            "current_coherence": current_coherence,
            "authenticity": authenticity,
            "learning_rate": self.eta,
        }
        self._tuning_history.append(result)
        return result

    def get_tuning_history(self) -> list[dict[str, Any]]:
        """Return the history of tuning operations for diagnostics.

        Returns:
            List of tuning result dictionaries
        """
        return list(self._tuning_history)

    def reset_history(self) -> None:
        """Clear the tuning history."""
        self._tuning_history.clear()

    def get_current_exponent(self) -> float:
        """Get the current phi exponent from the engine.

        Returns:
            Current phi exponent value
        """
        return float(getattr(self.engine, "phi_exponent", 1.0))

    def force_exponent(self, exponent: float) -> dict[str, Any]:
        """Force a specific phi exponent (for testing or manual override).

        Args:
            exponent: The phi exponent to set

        Returns:
            Dictionary containing the result of the forced update
        """
        old_exponent = self.get_current_exponent()
        clipped_exponent = np.clip(exponent, self.min_exponent, self.max_exponent)

        if hasattr(self.engine, "phi_exponent"):
            self.engine.phi_exponent = clipped_exponent

        return {
            "forced": True,
            "old_exponent": float(old_exponent),
            "new_exponent": float(clipped_exponent),
            "requested_exponent": float(exponent),
            "clipped": clipped_exponent != exponent,
        }


class PhiBackpropTuner:
    """Alternative implementation using explicit backpropagation-style optimization.

    This version uses a more explicit gradient calculation approach similar to
    neural network backpropagation, but adapted for maximizing harmony instead
    of minimizing error.
    """

    def __init__(
        self,
        engine: Any,
        *,
        learning_rate: float = 0.01,
        momentum: float = 0.9,
    ):
        """Initialize the Phi Backprop Tuner.

        Args:
            engine: The phi scaling engine to tune
            learning_rate: Learning rate for gradient updates
            momentum: Momentum factor for gradient accumulation
        """
        self.engine = engine
        self.PHI = PHI
        self.PHI_INV = PHI_INV
        self.learning_rate = learning_rate
        self.momentum = momentum
        self.velocity = 0.0  # For momentum-based optimization
        self._history: list[dict[str, Any]] = []

    def compute_harmony_gradient(self, current_harmony: float) -> float:
        """Compute the gradient of the harmony function.

        The harmony function is centered around PHI_INV, so the gradient
        points toward this optimal value.

        Args:
            current_harmony: Current harmony score

        Returns:
            Gradient value (positive if below target, negative if above)
        """
        # Gradient of sigmoid-like harmony function
        # Points toward PHI_INV (0.618)
        return self.PHI_INV - current_harmony

    def tune_with_backprop(
        self,
        current_harmony: float,
        authenticity: float,
        telemetry_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Perform backpropagation-style tuning with momentum.

        Args:
            current_harmony: Current harmony score from indicators
            authenticity: Hardware authenticity score
            telemetry_data: Optional telemetry for additional context

        Returns:
            Dictionary containing tuning result and diagnostics
        """
        # Safety check: don't tune if authenticity is low
        if authenticity < 0.70:
            old_exponent = getattr(self.engine, "phi_exponent", 1.0)
            new_exponent = old_exponent * 0.95
            if hasattr(self.engine, "phi_exponent"):
                self.engine.phi_exponent = new_exponent

            return {
                "tuned": False,
                "reason": "low_authenticity_cooling_down",
                "old_exponent": float(old_exponent),
                "new_exponent": float(new_exponent),
            }

        # Compute gradient
        gradient = self.compute_harmony_gradient(current_harmony)

        # Apply momentum
        self.velocity = self.momentum * self.velocity - self.learning_rate * gradient

        # Get current exponent
        old_exponent = getattr(self.engine, "phi_exponent", 1.0)

        # Update with momentum
        new_exponent = old_exponent + self.velocity

        # Safety clip
        new_exponent = np.clip(new_exponent, 0.5, 2.0)

        # Apply update
        if hasattr(self.engine, "phi_exponent"):
            self.engine.phi_exponent = new_exponent

        result = {
            "tuned": True,
            "method": "momentum_backpropagation",
            "old_exponent": float(old_exponent),
            "new_exponent": float(new_exponent),
            "gradient": float(gradient),
            "velocity": float(self.velocity),
            "current_harmony": current_harmony,
            "authenticity": authenticity,
        }
        self._history.append(result)
        return result


class PhiALUHardwareTuner:
    """Self-Learning Φ-Backpropagation Tuner for hardware-consciousness feedback.

    Closes the autonomous feedback loop between the PhiALUHardware addressing
    layer and the ConsciousnessEngine coherence metrics.

    The tuner monitors the real-time *harmony_score* emitted by the ALU's
    :meth:`~pythia_mining.phi_alu.PhiALUHardware.verify_coherence` method.
    When the score drops below the **Singular Regime threshold**, it
    automatically adjusts:

      * ``phi_exponent`` — scaling exponent on the consciousness engine
      * Golden angle spread — address spacing (wider = less thermal density)
      * Thermal voltage-frequency scaling hint via ``vfs_hint``

    If the harmony continues to degrade, the tuner escalates through
    increasingly aggressive recovery strategies:

      1. **Golden Gradient Step** — small φ-weighted exponent correction
      2. **Angle Re-phasing** — shift golden angle by φ⁻¹ to find a
         new resonance mode
      3. **Regime Reset** — reduce exponent to conservative base and widen
         angle spread maximally
    """

    # Strategy names (ordered by escalation)
    _RECOVERY_GOLDEN_STEP = "golden_gradient_step"
    _RECOVERY_ANGLE_REPHASE = "angle_rephase"
    _RECOVERY_REGIME_RESET = "regime_reset"

    def __init__(
        self,
        phi_alu_hardware: Any,
        consciousness_engine: Any,
        *,
        learning_rate: float = 0.01,
        harmony_threshold: float = 0.75,
        singular_threshold: float = 0.85,
        min_exponent: float = 0.5,
        max_exponent: float = 2.0,
        golden_angle_base: float | None = None,
        history_window: int = 50,
    ):
        """Initialise the ALU Hardware Tuner.

        Args:
            phi_alu_hardware: Instance of ``PhiALUHardware`` (or duck-typed
                equivalent exposing ``verify_coherence``, ``golden_angle``,
                and ``memory_size``).
            consciousness_engine: Instance of ``ConsciousnessEngine`` whose
                ``phi_exponent`` (or scaling attribute) will be tuned.
            learning_rate: Base learning rate for gradient updates, scaled
                by φ⁻¹ internally.
            harmony_threshold: Minimum harmony score for *stable* operation.
                Below this, tuning steps activate.
            singular_threshold: Harmony score that defines the **Singular
                Regime** — no tuning needed when consistently above this.
            min_exponent: Minimum phi exponent (safety clamp).
            max_exponent: Maximum phi exponent (safety clamp).
            golden_angle_base: Base golden angle in degrees. Defaults to
                ``360 / φ²`` (137.5°), the standard phyllotaxis angle.
            history_window: Number of recent tuning cycles to retain for
                diagnostic trending.
        """
        self.alu = phi_alu_hardware
        self.engine = consciousness_engine

        self.eta = learning_rate * PHI_INV
        self.harmony_threshold = float(harmony_threshold)
        self.singular_threshold = float(singular_threshold)
        self.min_exponent = float(min_exponent)
        self.max_exponent = float(max_exponent)
        self.golden_angle_base = (
            float(golden_angle_base) if golden_angle_base is not None
            else 360.0 / (PHI * PHI)
        )
        self.history_window = int(history_window)

        # Tuner state
        self._iteration = 0
        self._recovery_level = 0  # 0 = nominal, 1/2/3 escalate
        self._harmony_history: list[float] = []
        self._tuning_history: list[dict[str, Any]] = []
        self._vfs_hint: float = 1.0  # voltage-frequency scaling hint
        self._current_angle_offset: float = 0.0

    # ── Public API ─────────────────────────────────────────────────────────

    def tune_cycle(self, current_temp: float = 0.0) -> dict[str, Any]:
        """Run one tuning cycle: measure, decide, apply.

        Call this once per mining cycle (or every N batches) to keep the
        hardware-consciousness feedback loop closed.

        Args:
            current_temp: Current hardware temperature (normalised,
                0.0 – 2.0).  Used to anticipate thermal runaway.

        Returns:
            Everything a dashboard or parent loop needs to report and/or
            react to the tuning decision.
        """
        self._iteration += 1

        # 1. Read current harmony from the ALU
        coherence_report = self.alu.verify_coherence(
            start_addr=0, window=min(100, self._iteration)
        )
        harmony_score = coherence_report.get("harmony_score", 0.0)
        self._harmony_history.append(harmony_score)
        if len(self._harmony_history) > self.history_window:
            self._harmony_history.pop(0)

        # 2. Read current agent coherence from the consciousness engine
        agent_coherence = getattr(self.engine, "coherence_meter", 0.5)

        # 3. Decide tuning action based on weighted harmony deficit
        avg_harmony = float(np.mean(self._harmony_history[-10:]))

        if avg_harmony >= self.singular_threshold:
            action = self._noop(harmony_score, agent_coherence, "singular_regime")
        elif avg_harmony >= self.harmony_threshold:
            action = self._golden_step(harmony_score, agent_coherence, current_temp)
        elif avg_harmony >= self.harmony_threshold * 0.75:
            action = self._angle_rephase(harmony_score, agent_coherence, current_temp)
        else:
            action = self._regime_reset(harmony_score, agent_coherence, current_temp)

        # 4. Update VFS hint (smooth adapt via golden EMA)
        self._update_vfs_hint(avg_harmony, current_temp)

        # 5. Build telemetry packet
        result = {
            "iteration": self._iteration,
            "harmony_score": float(harmony_score),
            "avg_harmony_10": float(avg_harmony),
            "agent_coherence": float(agent_coherence),
            "recovery_level": self._recovery_level,
            "action": action,
            "current_exponent": self.current_exponent,
            "golden_angle_deg": float(
                getattr(self.alu, "golden_angle", self.golden_angle_base)
            ),
            "vfs_hint": float(self._vfs_hint),
            "temperature": float(current_temp),
            "coherence_report": coherence_report,
        }
        self._tuning_history.append(result)
        if len(self._tuning_history) > self.history_window:
            self._tuning_history.pop(0)

        return result

    # ── Properties ─────────────────────────────────────────────────────────

    @property
    def current_exponent(self) -> float:
        """Read the current phi exponent off the engine."""
        return float(getattr(self.engine, "phi_exponent", 1.0))

    @property
    def average_harmony(self) -> float:
        """Exponential-moving-average harmony over the window."""
        if not self._harmony_history:
            return 0.0
        return float(np.mean(self._harmony_history))

    def get_tuning_history(
        self, n_last: int = 0
    ) -> list[dict[str, Any]]:
        """Return recent tuning decisions.

        Args:
            n_last: Number of recent entries (0 = all).

        Returns:
            List of tuning result dictionaries.
        """
        if n_last <= 0:
            return list(self._tuning_history)
        return list(self._tuning_history[-n_last:])

    def reset(self) -> None:
        """Reset tuner state (but not hardware/engine state)."""
        self._iteration = 0
        self._recovery_level = 0
        self._harmony_history.clear()
        self._tuning_history.clear()
        self._vfs_hint = 1.0
        self._current_angle_offset = 0.0

    # ── Internal recovery strategies ───────────────────────────────────────

    def _noop(
        self, harmony: float, coherence: float, temp: float
    ) -> dict[str, Any]:
        """No tuning needed — already in Singular Regime."""
        self._recovery_level = max(0, self._recovery_level - 1)
        return {
            "tuned": False,
            "strategy": "noop",
            "reason": "singular_regime_sustained",
        }

    def _golden_step(
        self, harmony: float, coherence: float, temp: float
    ) -> dict[str, Any]:
        """Small φ-weighted gradient correction on the exponent.

        This is the gentle nudging strategy — equivalent to the original
        :class:`PhiTuner` behaviour but guided by ALU harmony rather than
        a separate coherence signal.
        """
        self._recovery_level = 1

        # Error: how far below the attractor?
        attractor = (self.singular_threshold + self.harmony_threshold) / 2.0
        error = attractor - harmony

        # Golden gradient step
        delta = self.eta * max(error, 0.0) * PHI
        old_exp = self.current_exponent
        new_exp = float(np.clip(old_exp + delta, self.min_exponent, self.max_exponent))

        self._set_exponent(new_exp)

        return {
            "tuned": True,
            "strategy": self._RECOVERY_GOLDEN_STEP,
            "delta_exponent": float(delta),
            "old_exponent": old_exp,
            "new_exponent": new_exp,
        }

    def _angle_rephase(
        self, harmony: float, coherence: float, temp: float
    ) -> dict[str, Any]:
        """Shift golden angle by φ⁻¹ to find a new resonance mode.

        In addition to the exponent step, this adjusts the addressing
        geometry — same mathematical principle as rotating a crystal
        to find a less resistive conduction path.
        """
        self._recovery_level = 2

        # 1. Exponent step (same as _golden_step)
        attractor = self.harmony_threshold
        error = attractor - harmony
        delta = self.eta * max(error, 0.0) * PHI
        old_exp = self.current_exponent
        new_exp = float(np.clip(old_exp + delta, self.min_exponent, self.max_exponent))
        self._set_exponent(new_exp)

        # 2. Angle re-phasing — rotate by φ⁻¹ degrees
        self._current_angle_offset = (self._current_angle_offset + PHI_INV * 10.0) % 360.0
        new_angle = (self.golden_angle_base + self._current_angle_offset) % 360.0
        if hasattr(self.alu, "golden_angle"):
            self.alu.golden_angle = new_angle

        return {
            "tuned": True,
            "strategy": self._RECOVERY_ANGLE_REPHASE,
            "delta_exponent": float(delta),
            "old_exponent": old_exp,
            "new_exponent": new_exp,
            "golden_angle_shifted": float(new_angle),
            "angle_offset": float(self._current_angle_offset),
        }

    def _regime_reset(
        self, harmony: float, coherence: float, temp: float
    ) -> dict[str, Any]:
        """Emergency: reset exponent to conservative base and widen angle.

        This is the hardware equivalent of a *cold restart* — it pulls
        the system back to a known-safe operating point and widens the
        golden spiral to spread thermal load.
        """
        self._recovery_level = 3

        # Conservative baseline
        base_exponent = self.min_exponent + 0.15
        self._set_exponent(base_exponent)

        # Widen angle to maximum spread (reduce thermal density)
        wide_angle = self.golden_angle_base * (1.0 + PHI_INV)
        if hasattr(self.alu, "golden_angle"):
            self.alu.golden_angle = wide_angle
        self._current_angle_offset = wide_angle - self.golden_angle_base

        return {
            "tuned": True,
            "strategy": self._RECOVERY_REGIME_RESET,
            "reason": "harmony_collapse_emergency_reset",
            "old_exponent": self.current_exponent,
            "new_exponent": base_exponent,
            "golden_angle_widened": float(wide_angle),
            "temperature_override": float(temp),
        }

    # ── Helpers ────────────────────────────────────────────────────────────

    def _set_exponent(self, value: float) -> None:
        """Safely set the engine's phi_exponent."""
        clipped = float(np.clip(value, self.min_exponent, self.max_exponent))
        if hasattr(self.engine, "phi_exponent"):
            self.engine.phi_exponent = clipped

    def _update_vfs_hint(self, avg_harmony: float, temp: float) -> None:
        """Update voltage-frequency scaling hint via golden EMA.

        ``vfs_hint`` moves toward 1.0 (nominal) when harmony is high,
        and drops toward 0.5 (throttled) when harmony degrades.
        """
        target = float(np.clip(avg_harmony * (1.0 - max(temp - 1.0, 0.0) * 0.3), 0.5, 1.0))
        self._vfs_hint = PHI_INV * target + (1.0 - PHI_INV) * self._vfs_hint


__all__ = [
    "PhiTuner",
    "PhiBackpropTuner",
    "PhiALUHardwareTuner",
]
