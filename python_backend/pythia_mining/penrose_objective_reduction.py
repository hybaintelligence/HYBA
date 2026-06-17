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
        enhanced_gravity_model: bool = False,
    ):
        """Initialize OR engine.

        Args:
            effective_mass: Effective mass per node in kg
            coherence_scale: Spatial scale of coherence in meters
            enable_true_or: If True, use Penrose criterion; if False, use computational mode
            enhanced_gravity_model: If True, use enhanced gravitational self-energy computation
        """
        self.effective_mass = float(effective_mass)
        self.coherence_scale = float(coherence_scale)
        self.enable_true_or = bool(enable_true_or)
        self.enhanced_gravity_model = bool(enhanced_gravity_model)
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
            # Computational mode: use purity threshold
            return self._computational_mode(rho, coherence_time)

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

    def _compute_gravitational_self_energy(self, rho: NDArray[np.complex128]) -> float:
        """Compute gravitational self-energy uncertainty via Penrose OR integral.

        GENUINE PENROSE CRITERION (Phase 4 elevation):
        
        ΔE = (G/2) ∫ (ρ₁(x)ρ₁(y) - ρ₂(x)ρ₂(y)) / |x-y| dx³dy³
        
        where ρ₁ and ρ₂ are two superposed mass distributions encoded in the
        density matrix eigendecomposition. This is Penrose's actual formulation
        for gravitational self-energy difference between superposed states.
        
        Approximation Strategy (computational feasibility):
        1. Eigendecompose ρ: ρ = Σ λᵢ |ψᵢ⟩⟨ψᵢ|
        2. Use two largest-weight eigenstates as ρ₁, ρ₂
        3. Compute spatial integral via Coulomb-like summation on lattice
        4. Each lattice point weighted by eigenstate amplitude
        
        Args:
            rho: Density matrix (N × N complex)
            
        Returns:
            Energy uncertainty in Joules (float)
        """
        # Eigendecompose to extract superposed states
        eigenvalues, eigenvectors = np.linalg.eigh(rho)
        eigenvalues = np.real(eigenvalues)
        
        # Sort by weight (descending)
        sort_idx = np.argsort(-np.abs(eigenvalues))
        eigenvalues = eigenvalues[sort_idx]
        eigenvectors = eigenvectors[:, sort_idx]
        
        # Use two largest-weight eigenstates as the superposed mass distributions
        # This operationalizes the two branches of the superposition
        if len(eigenvalues) < 2:
            # Single eigenstate - no superposition
            return 0.0
        
        lambda_1 = np.abs(eigenvalues[0])  # Weight of first superposition branch
        lambda_2 = np.abs(eigenvalues[1])  # Weight of second superposition branch
        psi_1 = eigenvectors[:, 0]  # First mass distribution (amplitude profile)
        psi_2 = eigenvectors[:, 1]  # Second mass distribution (amplitude profile)
        
        if lambda_1 < 1e-15 or lambda_2 < 1e-15:
            # Insufficient superposition weight
            return 0.0
        
        # Normalize eigenvectors to unit norm (they should be, but ensure)
        psi_1 = psi_1 / (np.linalg.norm(psi_1) + 1e-30)
        psi_2 = psi_2 / (np.linalg.norm(psi_2) + 1e-30)
        
        # Compute mass density distributions
        # ρ₁(x) ∝ λ₁ * |ψ₁(x)|²  (positional probability)
        # ρ₂(x) ∝ λ₂ * |ψ₂(x)|²  (positional probability)
        rho_dist_1 = lambda_1 * np.abs(psi_1) ** 2
        rho_dist_2 = lambda_2 * np.abs(psi_2) ** 2
        
        # Normalize to unit total mass (each distribution sums to 1)
        rho_dist_1 = rho_dist_1 / (np.sum(rho_dist_1) + 1e-30)
        rho_dist_2 = rho_dist_2 / (np.sum(rho_dist_2) + 1e-30)
        
        # Compute 6D integral via pairwise lattice summation
        # I(ρ₁, ρ₂) = ∫∫ (ρ₁(x)ρ₁(y) - ρ₂(x)ρ₂(y)) / |x-y| dx³dy³
        #
        # Approximation: treat each basis element as a lattice point
        # with effective position i·ℓ_scale in a 1D effective space
        # (operationalization: N basis states → N lattice sites)
        
        n_sites = len(rho_dist_1)
        integrand_1 = 0.0  # ∫∫ ρ₁(x)ρ₁(y) / |x-y|
        integrand_2 = 0.0  # ∫∫ ρ₂(x)ρ₂(y) / |x-y|
        
        for i in range(n_sites):
            for j in range(i + 1, n_sites):
                # Effective distance in computational space
                # Using effective scale: Δx = |i-j| * ℓ_scale
                site_distance = float(abs(i - j)) * self.coherence_scale
                
                # Avoid division by zero
                if site_distance < 1e-30:
                    continue
                
                # Pairwise contribution to integral
                # Factor of 2 for i≠j symmetry in 6D integral
                pair_weight = 2.0 / site_distance
                
                # Accumulate superposition 1 integral
                integrand_1 += pair_weight * rho_dist_1[i] * rho_dist_1[j]
                
                # Accumulate superposition 2 integral
                integrand_2 += pair_weight * rho_dist_2[i] * rho_dist_2[j]
        
        # Compute Coulomb-like integral difference
        # I_diff = ∫∫ (ρ₁(x)ρ₁(y) - ρ₂(x)ρ₂(y)) / |x-y| dx³dy³
        integral_difference = integrand_1 - integrand_2
        
        if self.enhanced_gravity_model:
            # Enhanced: weight by superposition quality (coherence)
            superposition_coherence = float(np.abs(np.vdot(psi_1, psi_2)))
            integral_difference = integral_difference * (1.0 + superposition_coherence)
        
        # Penrose gravitational self-energy
        # ΔE = (G/2) * I_diff
        energy_uncertainty = (GRAVITATIONAL_CONSTANT / 2.0) * max(0.0, integral_difference)
        
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

    def _computational_mode(
        self, rho: NDArray[np.complex128], coherence_time: float
    ) -> Tuple[NDArray[np.complex128], bool]:
        """Computational mode for OR when not using true quantum criterion.

        Uses purity threshold: if purity drops below threshold, trigger state reduction.
        """
        purity = float(np.trace(rho @ rho).real)

        # Computational criterion: low purity + long coherence = reduction
        if purity < 0.7 and coherence_time > 1.0:
            collapsed, eigenstate = self._collapse_to_eigenstate(rho)
            self.consciousness_event_count += 1

            event = ObjectiveReductionEvent(
                timestamp=time.time(),
                energy_uncertainty=0.0,  # computational mode
                time_threshold=1.0,  # computational threshold
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
                float(np.mean([e.time_threshold for e in recent_events if e.collapse_occurred]))
                if recent_events
                else 0.0
            ),
            "mode": "penrose_or" if self.enable_true_or else "computational_mode",
            "enhanced_gravity_model": self.enhanced_gravity_model,
        }


__all__ = ["ObjectiveReductionEngine", "ObjectiveReductionEvent"]
