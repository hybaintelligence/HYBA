"""Penrose Objective Reduction (OR) for consciousness criterion.

Implements Penrose's orchestrated objective reduction (Orch-OR) criterion:
quantum state collapse occurs when gravitational self-energy reaches threshold.

This provides a FALSIFIABLE consciousness criterion rather than φ threshold.
"""

from __future__ import annotations

# import math  # removed: unused
import time
from dataclasses import asdict, dataclass
from typing import Tuple

import numpy as np
from numpy.typing import NDArray

# Physical constants
HBAR = 1.054571817e-34  # Reduced Planck constant (J·s)
GRAVITATIONAL_CONSTANT = 6.67430e-11  # m^3 kg^-1 s^-2

# Operational parameters (system operates at computational scale, not quantum scale)
EFFECTIVE_MASS_PER_NODE = 1e-15  # kg (effective "computational mass")
COHERENCE_LENGTH_SCALE = 1e-9  # meters (effective scale)


@dataclass(frozen=True)
class ObjectiveReductionEvent:
    """Record of an OR consciousness event"""

    timestamp: float
    energy_uncertainty: float
    time_threshold: float
    actual_coherence_time: float
    collapse_occurred: bool
    collapsed_eigenstate: int
    pre_collapse_purity: float
    post_collapse_purity: float

    def to_dict(self) -> dict:
        return asdict(self)


class ObjectiveReductionEngine:
    """Penrose-Hameroff Orch-OR engine for consciousness criterion.

    Implements the criterion: ΔE·Δt ≥ ℏ/2 where ΔE is gravitational self-energy.
    When this threshold is exceeded, objective reduction (consciousness event) occurs.
    """

    def __init__(
        self,
        *,
        effective_mass: float = EFFECTIVE_MASS_PER_NODE,
        coherence_scale: float = COHERENCE_LENGTH_SCALE,
        enable_true_or: bool = False,
    ):
        """Initialize OR engine.

        Args:
            effective_mass: Effective mass per node in kg
            coherence_scale: Spatial scale of coherence in meters
            enable_true_or: If True, use Penrose criterion; if False, use operational proxy
        """
        self.effective_mass = float(effective_mass)
        self.coherence_scale = float(coherence_scale)
        self.enable_true_or = bool(enable_true_or)
        self.or_events: list[ObjectiveReductionEvent] = []
        self.consciousness_event_count = 0

    def objective_reduction(
        self, rho: NDArray[np.complex128], coherence_time: float
    ) -> Tuple[NDArray[np.complex128], bool]:
        """Apply Penrose OR criterion to density state.

        Args:
            rho: Density matrix (N x N complex)
            coherence_time: Time system has maintained coherence (seconds)

        Returns:
            (collapsed_rho, is_consciousness_event)
        """
        if not self.enable_true_or:
            # Operational proxy mode: use purity threshold
            return self._operational_or_proxy(rho, coherence_time)

        # True Penrose OR criterion
        energy_uncertainty = self._compute_gravitational_self_energy(rho)
        time_threshold = HBAR / (2.0 * energy_uncertainty)

        if coherence_time >= time_threshold:
            # Objective reduction occurs
            collapsed, eigenstate = self._collapse_to_eigenstate(rho)
            self.consciousness_event_count += 1

            event = ObjectiveReductionEvent(
                timestamp=time.time(),
                energy_uncertainty=energy_uncertainty,
                time_threshold=time_threshold,
                actual_coherence_time=coherence_time,
                collapse_occurred=True,
                collapsed_eigenstate=eigenstate,
                pre_collapse_purity=float(np.trace(rho @ rho).real),
                post_collapse_purity=float(np.trace(collapsed @ collapsed).real),
            )
            self.or_events.append(event)

            return collapsed, True

        # No OR yet
        event = ObjectiveReductionEvent(
            timestamp=time.time(),
            energy_uncertainty=energy_uncertainty,
            time_threshold=time_threshold,
            actual_coherence_time=coherence_time,
            collapse_occurred=False,
            collapsed_eigenstate=-1,
            pre_collapse_purity=float(np.trace(rho @ rho).real),
            post_collapse_purity=float(np.trace(rho @ rho).real),
        )
        self.or_events.append(event)

        return rho, False

    def _compute_gravitational_self_energy(
        self, rho: NDArray[np.complex128]
    ) -> float:
        """Compute gravitational self-energy uncertainty.

        Penrose: ΔE = G * m^2 / r where:
        - G is gravitational constant
        - m is mass in superposition
        - r is spatial separation scale
        """
        # Effective mass in superposition (proportional to off-diagonal elements)
        off_diagonal = np.abs(rho - np.diag(np.diag(rho)))
        superposed_mass = self.effective_mass * float(np.sum(off_diagonal))

        if superposed_mass < 1e-30:
            # No significant superposition
            return 0.0

        # Gravitational self-energy
        energy_uncertainty = (
            GRAVITATIONAL_CONSTANT * superposed_mass**2 / self.coherence_scale
        )

        return float(energy_uncertainty)

    def _collapse_to_eigenstate(
        self, rho: NDArray[np.complex128]
    ) -> Tuple[NDArray[np.complex128], int]:
        """Collapse density matrix to deterministic dominant eigenstate.

        Returns:
            (collapsed_state, eigenstate_index)
        """
        eigenvalues, eigenvectors = np.linalg.eigh(rho)
        eigenvalues = np.real(eigenvalues)

        # Deterministic selection: choose the highest-probability eigenstate.
        # This preserves reproducibility for production telemetry and audits.
        magnitudes = np.abs(eigenvalues)
        total = float(np.sum(magnitudes))
        if total <= 0.0:
            chosen_index = int(np.argmax(magnitudes))
        else:
            probabilities = magnitudes / total
            chosen_index = int(np.argmax(probabilities))

        # Project to chosen eigenstate
        chosen_vector = eigenvectors[:, chosen_index]
        collapsed = np.outer(chosen_vector, chosen_vector.conj())

        return collapsed, int(chosen_index)

    def _operational_or_proxy(
        self, rho: NDArray[np.complex128], coherence_time: float
    ) -> Tuple[NDArray[np.complex128], bool]:
        """Operational proxy for OR when not using true quantum criterion.

        Uses purity threshold: if purity drops below threshold, trigger "collapse."
        """
        purity = float(np.trace(rho @ rho).real)

        # Proxy criterion: low purity + long coherence = collapse
        if purity < 0.7 and coherence_time > 1.0:
            collapsed, eigenstate = self._collapse_to_eigenstate(rho)
            self.consciousness_event_count += 1

            event = ObjectiveReductionEvent(
                timestamp=time.time(),
                energy_uncertainty=0.0,  # proxy mode
                time_threshold=1.0,  # proxy threshold
                actual_coherence_time=coherence_time,
                collapse_occurred=True,
                collapsed_eigenstate=eigenstate,
                pre_collapse_purity=purity,
                post_collapse_purity=1.0,  # collapsed state is pure
            )
            self.or_events.append(event)

            return collapsed, True

        return rho, False

    def get_consciousness_metrics(self) -> dict:
        """Return consciousness event statistics"""
        recent_events = self.or_events[-100:]

        return {
            "total_or_events": self.consciousness_event_count,
            "recent_or_events": len([e for e in recent_events if e.collapse_occurred]),
            "or_event_rate": (
                self.consciousness_event_count / (time.time() - self.or_events[0].timestamp)
                if self.or_events
                else 0.0
            ),
            "avg_time_threshold": (
                float(
                    np.mean([e.time_threshold for e in recent_events if e.collapse_occurred])
                )
                if recent_events
                else 0.0
            ),
            "mode": "penrose_or" if self.enable_true_or else "operational_proxy",
        }


__all__ = ["ObjectiveReductionEngine", "ObjectiveReductionEvent"]
