"""Deterministic density-matrix healing primitives for mining autonomy.

This module intentionally implements the "quantum healing" layer as classical
linear algebra over density matrices.  It is an optional self-repair component:
callers can inspect :class:`HealingResult` for measured purity/entropy changes
without depending on physical quantum hardware or external services.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import time
from typing import Tuple

import numpy as np

PHI = (1.0 + 5.0**0.5) / 2.0
PHI_INV = 1.0 / PHI
PURITY_COLLAPSE_THRESHOLD = 0.72


@dataclass(frozen=True)
class HealingResult:
    pre_heal_purity: float
    pre_heal_entropy: float
    pre_heal_phi_density: float
    post_heal_purity: float
    post_heal_entropy: float
    post_heal_phi_density: float
    or_collapse_fired: bool
    dominant_eigenvalue: float
    candidates_superposed: int
    lanes_healed: int
    purity_gain: float
    entropy_reduction: float
    duration_ms: float
    tunnelling_used: bool = False
    annealing_used: bool = False
    swarming_used: bool = False
    interference_used: bool = False
    tunnelling_amplitude: float = 0.0
    annealing_temperature: float = 0.0
    swarm_consensus_purity: float = 0.0
    interference_gain: float = 0.0

    def to_dict(self) -> dict[str, float | int | bool]:
        return asdict(self)


class QuantumHealingSwarm:
    """Classical density-matrix repair model used by performance recovery."""

    def __init__(
        self,
        num_candidates: int = 8,
        num_lanes: int = 32,
        *,
        enable_tunnelling: bool = True,
        enable_annealing: bool = True,
        enable_swarming: bool = True,
        enable_interference: bool = True,
    ) -> None:
        if num_candidates < 2:
            raise ValueError("num_candidates must be >= 2")
        self.num_candidates = int(num_candidates)
        self.num_lanes = int(num_lanes)
        self.enable_tunnelling = enable_tunnelling
        self.enable_annealing = enable_annealing
        self.enable_swarming = enable_swarming
        self.enable_interference = enable_interference
        self.heal_count = 0
        self._persistent_superposition: np.ndarray | None = None
        self._superposition_age = 0

    def _phi_basis_vector(self, n: int) -> np.ndarray:
        weights = np.array([PHI_INV**i for i in range(n)], dtype=float)
        return weights / np.linalg.norm(weights)

    def _normalise_density(self, rho: np.ndarray) -> np.ndarray:
        rho = (rho + rho.conj().T) / 2.0
        vals, vecs = np.linalg.eigh(rho)
        vals = np.clip(vals.real, 0.0, None)
        if vals.sum() <= 0:
            vals = np.ones(len(vals)) / len(vals)
        else:
            vals = vals / vals.sum()
        return vecs @ np.diag(vals) @ vecs.conj().T

    def _form_degraded_density_matrix(
        self, phi_density: float, consecutive_failures: int, degrade_factor: float = 1.0
    ) -> np.ndarray:
        phi_density = float(np.clip(phi_density, 0.0, 1.0))
        degradation = float(
            np.clip(
                (1.0 - phi_density) * degrade_factor + consecutive_failures * 0.015,
                0.0,
                0.95,
            )
        )
        n = self.num_candidates
        basis = self._phi_basis_vector(n)
        pure = np.outer(basis, basis.conj())
        mixed = np.eye(n) / n
        return self._normalise_density((1.0 - degradation) * pure + degradation * mixed)

    def _purity(self, rho: np.ndarray) -> float:
        return float(np.real(np.trace(rho @ rho)))

    def _von_neumann_entropy(self, rho: np.ndarray) -> float:
        eigvals = np.clip(np.linalg.eigvalsh(rho).real, 1e-15, 1.0)
        return float(-np.sum(eigvals * np.log2(eigvals)))

    def _phi_projection(self, rho: np.ndarray) -> float:
        v = self._phi_basis_vector(rho.shape[0])
        return float(np.clip(np.real(v.conj().T @ rho @ v), 0.0, 1.0))

    def _superpose_repair_candidates(
        self, rho: np.ndarray, phi_density: float
    ) -> Tuple[np.ndarray, int]:
        target = np.outer(
            self._phi_basis_vector(rho.shape[0]), self._phi_basis_vector(rho.shape[0])
        )
        strength = 0.35 + 0.45 * (1.0 - float(np.clip(phi_density, 0.0, 1.0)))
        return (
            self._normalise_density((1.0 - strength) * rho + strength * target),
            self.num_candidates,
        )

    def _or_collapse(self, rho: np.ndarray) -> Tuple[np.ndarray, bool]:
        purity = self._purity(rho)
        if purity >= PURITY_COLLAPSE_THRESHOLD:
            return rho, False
        vals, vecs = np.linalg.eigh(rho)
        dominant = vecs[:, int(np.argmax(vals.real))]
        return self._normalise_density(np.outer(dominant, dominant.conj())), True

    def _wkb_tunnel(
        self, rho: np.ndarray, phi_density: float
    ) -> Tuple[np.ndarray, float]:
        barrier = max(0.0, 1.0 - self._purity(rho))
        amplitude = float(np.exp(-PHI * barrier) * np.clip(phi_density, 0.0, 1.0))
        target = np.outer(
            self._phi_basis_vector(rho.shape[0]), self._phi_basis_vector(rho.shape[0])
        )
        return (
            self._normalise_density(
                (1.0 - amplitude * 0.25) * rho + amplitude * 0.25 * target
            ),
            amplitude,
        )

    def _phi_anneal(
        self, rho: np.ndarray, pre_entropy: float, phi_density: float
    ) -> Tuple[float, np.ndarray, bool]:
        temp = max(0.1, min(1.0, PHI ** (-self.heal_count / 8.0)))
        target = np.outer(
            self._phi_basis_vector(rho.shape[0]), self._phi_basis_vector(rho.shape[0])
        )
        candidate = self._normalise_density(
            (1.0 - 0.2 * temp) * rho + 0.2 * temp * target
        )
        accepted = (
            self._von_neumann_entropy(candidate) <= pre_entropy
            or np.random.random() < temp * 0.05
        )
        return float(temp), candidate if accepted else rho, bool(accepted)

    def _swarm_consensus(
        self, rho: np.ndarray, phi_density: float
    ) -> Tuple[np.ndarray, float]:
        target = np.outer(
            self._phi_basis_vector(rho.shape[0]), self._phi_basis_vector(rho.shape[0])
        )
        weights = np.array(
            [PHI_INV**i for i in range(self.num_candidates)], dtype=float
        )
        strength = float(weights.mean() / weights.max()) * 0.35
        consensus = self._normalise_density((1.0 - strength) * rho + strength * target)
        return consensus, self._purity(consensus)

    def _interference_accumulate(
        self, rho: np.ndarray, phi_density: float
    ) -> Tuple[np.ndarray, float]:
        if self._persistent_superposition is None:
            self._persistent_superposition = rho.copy()
            self._superposition_age = 1
            return rho, 0.0
        previous = self._purity(rho)
        combined = self._normalise_density(
            PHI_INV * rho + (1.0 - PHI_INV) * self._persistent_superposition
        )
        gain = self._purity(combined) - previous
        self._persistent_superposition = combined.copy()
        self._superposition_age += 1
        if self._superposition_age > 10:
            self._persistent_superposition = None
            self._superposition_age = 0
        return combined, float(gain)

    def heal(
        self, phi_density: float, consecutive_failures: int, degrade_factor: float = 1.0
    ) -> HealingResult:
        started = time.perf_counter()
        rho = self._form_degraded_density_matrix(
            phi_density, consecutive_failures, degrade_factor
        )
        pre_purity = self._purity(rho)
        pre_entropy = self._von_neumann_entropy(rho)
        pre_phi = self._phi_projection(rho)
        tunnelling_used = False
        tunnelling_amplitude = 0.0
        if self.enable_tunnelling and pre_purity < 0.5 and consecutive_failures > 10:
            rho, tunnelling_amplitude = self._wkb_tunnel(rho, phi_density)
            tunnelling_used = True
        annealing_temperature = 0.0
        if self.enable_annealing:
            annealing_temperature, rho, _ = self._phi_anneal(
                rho, self._von_neumann_entropy(rho), phi_density
            )
        swarm_consensus_purity = 0.0
        if self.enable_swarming:
            rho, swarm_consensus_purity = self._swarm_consensus(rho, phi_density)
        interference_gain = 0.0
        if self.enable_interference:
            rho, interference_gain = self._interference_accumulate(rho, phi_density)
        rho, candidates = self._superpose_repair_candidates(rho, phi_density)
        rho, collapsed = self._or_collapse(rho)
        post_purity = self._purity(rho)
        post_entropy = self._von_neumann_entropy(rho)
        post_phi = max(pre_phi, self._phi_projection(rho))
        dominant = float(np.max(np.linalg.eigvalsh(rho).real))
        self.heal_count += 1
        degradation = max(0.0, 1.0 - float(np.clip(phi_density, 0.0, 1.0)))
        lanes_healed = int(
            round(self.num_lanes * min(1.0, degradation + consecutive_failures * 0.03))
        )
        return HealingResult(
            pre_purity,
            pre_entropy,
            pre_phi,
            post_purity,
            post_entropy,
            post_phi,
            collapsed,
            dominant,
            candidates,
            lanes_healed,
            post_purity - pre_purity,
            pre_entropy - post_entropy,
            (time.perf_counter() - started) * 1000.0,
            tunnelling_used,
            self.enable_annealing,
            self.enable_swarming,
            self.enable_interference,
            tunnelling_amplitude,
            annealing_temperature,
            swarm_consensus_purity,
            interference_gain,
        )
