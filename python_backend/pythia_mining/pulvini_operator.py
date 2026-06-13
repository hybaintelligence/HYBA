"""Consolidated PULVINI manifold operator core.

This module is the production-facing façade over the low-level Choi, Gamma,
Bures, and topology primitives.  The existing specialist modules remain the
source of truth for their proofs and tests; :class:`ManifoldOperator` gives the
runtime a single, auditable entry point for density-state repair, CP-channel
certification, Bures geometry, empirical jump construction, and topology
verification.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Optional, Sequence

import numpy as np
from numpy.typing import NDArray

from .pulvini_bures import BuresCertificate, bures_certificate, offdiag
from .pulvini_certificates import adjacency_map_digest, automorphism_runtime_certificate
from .pulvini_choi import ChoiCertificate, choi_certificate, choi_matrix, kraus_operators_for_step
from .pulvini_gamma import EmpiricalGammaLedger, GammaEstimate, jump_operators_from_gamma
from .pulvini_group import adjacency_sets
from .pulvini_topology import ADJACENCY_MAP, NUM_NODES


class ManifoldState(str, Enum):
    """Operational classification of a normalized density state."""

    COHERENT = "coherent"
    DECOHERENT = "decoherent"
    ENTANGLED_PROXY = "entangled_proxy"
    MIXED = "mixed"


class CoherenceClassification(str, Enum):
    """Dashboard-friendly coherence classification.

    This compatibility enum keeps the production façade aligned with the
    Command Center green/yellow/red health model while ``ManifoldState`` remains
    the lower-level density-state taxonomy.
    """

    COHERENT = "green"
    DEGRADED = "yellow"
    DECOHERENT = "red"


@dataclass(frozen=True)
class ManifoldConfig:
    """Configuration for the consolidated operator core."""

    dimension: int = NUM_NODES
    adjacency_symmetry: int = 120
    gamma_normalization: float = 1.0
    coherence_threshold: float = 0.02
    mixed_purity_threshold: float = 0.08
    epsilon_trace: float = 1e-12


@dataclass(frozen=True)
class OperatorEvolution:
    """Result returned by :meth:`ManifoldOperator.evolve`."""

    state: NDArray[np.complex128]
    coherence: float
    purity: float
    classification: ManifoldState
    bures_distance_to_target: Optional[float]
    topology_verified: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "coherence": self.coherence,
            "purity": self.purity,
            "classification": self.classification.value,
            "bures_distance_to_target": self.bures_distance_to_target,
            "topology_verified": self.topology_verified,
        }


class ManifoldOperator:
    """Unified operator façade for the 32-node PULVINI Hilbert layer.

    The class deliberately composes existing verified primitives instead of
    deleting them.  This keeps the research modules available while presenting a
    tight production API: ``evolve(state)``, ``certify_channel(...)``,
    ``compute_bures_distance(...)``, and ``verify_topology()``.
    """

    VERSION = "PULVINI_OPERATOR_V1"

    def __init__(
        self,
        config: Optional[ManifoldConfig] = None,
        *,
        adjacency_map: Optional[dict[int, dict[str, list[int]]]] = None,
        gamma_ledger: Optional[EmpiricalGammaLedger] = None,
    ) -> None:
        self.config = config or ManifoldConfig()
        self.dim = int(self.config.dimension)
        self.adjacency_map = adjacency_map or ADJACENCY_MAP
        if self.dim != len(self.adjacency_map):
            raise ValueError("ManifoldConfig.dimension must match adjacency map size")
        self.neighbors = adjacency_sets(self.adjacency_map)
        self.gamma_ledger = gamma_ledger or EmpiricalGammaLedger(self.dim)
        if self.config.gamma_normalization <= 0.0:
            raise ValueError("ManifoldConfig.gamma_normalization must be positive")
        self._state_history: list[NDArray[np.complex128]] = []
        self._coherence_history: list[float] = []
        self._topology_certificate: Optional[dict[str, Any]] = None

    def evolve(
        self,
        state: NDArray[np.complex128] | Sequence[complex],
        target: Optional[NDArray[np.complex128] | Sequence[complex]] = None,
    ) -> OperatorEvolution:
        """Repair and classify a state in one auditable operation.

        Vectors are promoted to rank-one density matrices; matrices are
        projected onto the positive trace-one density manifold using the same
        spectral flooring used by the Bures certificate path.
        """
        rho = self.ensure_density_state(state)
        self._state_history.append(rho.copy())

        coherence = self.compute_coherence(rho)
        purity = float(np.real(np.trace(rho @ rho)))
        self._coherence_history.append(coherence)

        distance = None
        if target is not None:
            distance = self.compute_bures_distance(rho, self.ensure_density_state(target))

        return OperatorEvolution(
            state=rho,
            coherence=coherence,
            purity=purity,
            classification=self.classify_state(rho),
            bures_distance_to_target=distance,
            topology_verified=self.verify_topology()["gate_closed"],
        )

    def ensure_density_state(
        self,
        state: NDArray[np.complex128] | Sequence[complex],
    ) -> NDArray[np.complex128]:
        """Return a Hermitian positive-semidefinite trace-one matrix."""
        values = np.asarray(state, dtype=np.complex128)
        if values.ndim == 1:
            if values.shape[0] != self.dim:
                raise ValueError(f"state vector must have dimension {self.dim}")
            norm = float(np.linalg.norm(values))
            if norm <= self.config.epsilon_trace:
                raise ValueError("state vector norm must be positive")
            vector = values / norm
            matrix = np.outer(vector, vector.conj())
        elif values.ndim == 2:
            if values.shape != (self.dim, self.dim):
                raise ValueError(f"state matrix must have shape {(self.dim, self.dim)}")
            matrix = values
        else:
            raise ValueError("state must be a vector or square matrix")

        if not np.all(np.isfinite(matrix)):
            raise ValueError("state contains NaN or infinite values")

        hermitian = (matrix + matrix.conj().T) / 2.0
        eigenvalues, eigenvectors = np.linalg.eigh(hermitian)
        eigenvalues = np.where(np.isfinite(eigenvalues.real), eigenvalues.real, 0.0)
        eigenvalues = np.maximum(eigenvalues, 0.0)
        total = float(np.sum(eigenvalues))
        if total <= self.config.epsilon_trace:
            repaired = np.eye(self.dim, dtype=np.complex128) / self.dim
        else:
            eigenvalues = eigenvalues / total
            repaired = eigenvectors @ np.diag(eigenvalues) @ eigenvectors.conj().T

        # ``gamma_normalization`` is accepted for compatibility with the older
        # sketches, but density operators must remain trace-one.  Applying it as
        # a scalar and then renormalizing makes that invariant explicit.
        repaired = repaired * float(self.config.gamma_normalization)
        repaired = repaired / np.trace(repaired)
        return ((repaired + repaired.conj().T) / 2.0).astype(np.complex128, copy=False)

    def apply_choi_map(
        self,
        state: NDArray[np.complex128] | Sequence[complex],
    ) -> NDArray[np.complex128]:
        """Compatibility alias for production density-state repair.

        Historical design notes referred to the repair projection as the
        façade's Choi/CPTP map.  The implementation uses
        :meth:`ensure_density_state`, which enforces Hermiticity, PSD, and
        trace-one invariants before any mining loop consumes ``rho``.
        """

        return self.ensure_density_state(state)

    def compute_uhlmann_fidelity(
        self,
        rho_a: NDArray[np.complex128] | Sequence[complex],
        rho_b: NDArray[np.complex128] | Sequence[complex],
    ) -> float:
        """Compatibility alias for :meth:`compute_fidelity`."""

        return self.compute_fidelity(rho_a, rho_b)

    def get_coherence_metrics(
        self,
        rho: NDArray[np.complex128] | Sequence[complex],
        reference: Optional[NDArray[np.complex128] | Sequence[complex]] = None,
    ) -> dict[str, Any]:
        """Return dashboard coherence metrics for a repaired density state."""

        matrix = self.ensure_density_state(rho)
        coherence = self.compute_coherence(matrix)
        purity = float(np.clip(np.real(np.trace(matrix @ matrix)), 0.0, 1.0))
        bures_distance = (
            0.0
            if reference is None
            else self.compute_bures_distance(matrix, self.ensure_density_state(reference))
        )
        if bures_distance <= 0.25 and purity >= self.config.mixed_purity_threshold:
            classification = CoherenceClassification.COHERENT
        elif bures_distance <= 0.75 or coherence > self.config.epsilon_trace:
            classification = CoherenceClassification.DEGRADED
        else:
            classification = CoherenceClassification.DECOHERENT
        return {
            "coherence": coherence,
            "purity": purity,
            "bures_distance": bures_distance,
            "classification": classification,
            "ui_state": classification.value,
            "state": self.classify_state(matrix).value,
        }

    def compute_coherence(self, rho: NDArray[np.complex128]) -> float:
        """Return normalized l1 off-diagonal coherence."""
        matrix = self.ensure_density_state(rho)
        denominator = max(self.dim - 1, 1)
        return float(np.sum(np.abs(offdiag(matrix))) / denominator)

    def classify_state(self, rho: NDArray[np.complex128]) -> ManifoldState:
        """Classify a density state using coherence and purity invariants."""
        matrix = self.ensure_density_state(rho)
        coherence = self.compute_coherence(matrix)
        purity = float(np.real(np.trace(matrix @ matrix)))
        if coherence >= self.config.coherence_threshold and purity > self.config.mixed_purity_threshold:
            return ManifoldState.COHERENT
        if purity <= self.config.mixed_purity_threshold:
            return ManifoldState.MIXED
        if coherence <= self.config.epsilon_trace:
            return ManifoldState.DECOHERENT
        return ManifoldState.ENTANGLED_PROXY

    def compute_bures_distance(
        self,
        rho_a: NDArray[np.complex128] | Sequence[complex],
        rho_b: NDArray[np.complex128] | Sequence[complex],
    ) -> float:
        """Return the Bures distance between two density states."""
        left = self.ensure_density_state(rho_a)
        right = self.ensure_density_state(rho_b)
        sqrt_left = self._matrix_sqrt(left)
        fidelity_root = np.trace(self._matrix_sqrt(sqrt_left @ right @ sqrt_left))
        fidelity = float(np.clip(np.real(fidelity_root * np.conj(fidelity_root)), 0.0, 1.0))
        return float(np.sqrt(max(0.0, 2.0 - 2.0 * np.sqrt(fidelity))))

    def compute_fidelity(
        self,
        rho_a: NDArray[np.complex128] | Sequence[complex],
        rho_b: NDArray[np.complex128] | Sequence[complex],
    ) -> float:
        """Return Uhlmann fidelity in ``[0, 1]``."""
        left = self.ensure_density_state(rho_a)
        right = self.ensure_density_state(rho_b)
        sqrt_left = self._matrix_sqrt(left)
        fidelity_root = np.trace(self._matrix_sqrt(sqrt_left @ right @ sqrt_left))
        fidelity = np.real(fidelity_root * np.conj(fidelity_root))
        return float(np.clip(fidelity, 0.0, 1.0))

    def bures_certificate(self, rho: NDArray[np.complex128], entropy_rate: float) -> BuresCertificate:
        """Delegate to the established Bures certificate primitive."""
        return bures_certificate(self.ensure_density_state(rho), entropy_rate)

    def record_gamma(self, node_id: int, *, nack: bool) -> GammaEstimate:
        """Record an ACK/NACK observation for empirical jump strengths."""
        return self.gamma_ledger.record(node_id, nack=nack)

    def jump_operators_for_node(self, node_id: int, gamma: Optional[float] = None) -> list[NDArray[np.complex128]]:
        """Build Lindblad jump operators for a node from empirical gamma."""
        estimate = self.gamma_ledger.estimate(node_id)
        return jump_operators_from_gamma(
            node_id=node_id,
            neighbors=self.neighbors,
            gamma=estimate.gamma if gamma is None else gamma,
            num_nodes=self.dim,
        )

    def certify_channel(
        self,
        hamiltonian: NDArray[np.complex128],
        jump_operators: Optional[Sequence[NDArray[np.complex128]]] = None,
        *,
        dt: float = 1.0,
    ) -> ChoiCertificate:
        """Return the full Choi complete-positivity certificate for a step."""
        kraus = kraus_operators_for_step(hamiltonian, jump_operators or [], dt=dt)
        return choi_certificate(kraus)

    def choi_matrix(
        self,
        hamiltonian: NDArray[np.complex128],
        jump_operators: Optional[Sequence[NDArray[np.complex128]]] = None,
        *,
        dt: float = 1.0,
    ) -> NDArray[np.complex128]:
        """Return the Choi matrix for diagnostics."""
        kraus = kraus_operators_for_step(hamiltonian, jump_operators or [], dt=dt)
        return choi_matrix(kraus)

    def verify_topology(self) -> dict[str, Any]:
        """Return an exact automorphism/topology certificate.

        The result is cached on the operator instance because the runtime
        adjacency map is immutable for a process and exact automorphism checks
        are substantially more expensive than density-state evolution.
        """
        if self._topology_certificate is None:
            certificate = automorphism_runtime_certificate(self.adjacency_map)
            certificate = dict(certificate)
            certificate["operator_version"] = self.VERSION
            certificate["adjacency_map_sha256"] = adjacency_map_digest(self.adjacency_map)
            certificate["dimension_verified"] = self.dim == NUM_NODES
            certificate["symmetry_verified"] = (
                certificate.get("group_order") == self.config.adjacency_symmetry
            )
            self._topology_certificate = certificate
        return dict(self._topology_certificate)

    def snapshot(self) -> dict[str, Any]:
        """Return a compact Command Center snapshot."""
        latest = self._state_history[-1] if self._state_history else np.eye(self.dim, dtype=np.complex128) / self.dim
        return {
            "version": self.VERSION,
            "config": asdict(self.config),
            "state_count": len(self._state_history),
            "latest_coherence": self._coherence_history[-1] if self._coherence_history else 0.0,
            "latest_classification": self.classify_state(latest).value,
            "topology_gate_closed": self.verify_topology()["gate_closed"],
        }


    def capability_manifest(self) -> dict[str, Any]:
        """Return the versioned production-façade capability manifest."""
        from .pulvini_elevation import QuantumRuntimeManifestBuilder

        return QuantumRuntimeManifestBuilder(self).capability_manifest().to_dict()

    def quantum_runtime_manifest(self, rho: Optional[NDArray[np.complex128]] = None) -> dict[str, Any]:
        """Return the regulator-facing runtime manifest for this façade."""
        from .pulvini_elevation import QuantumRuntimeManifestBuilder

        return QuantumRuntimeManifestBuilder(self).build(rho=rho)

    @property
    def state_history(self) -> tuple[NDArray[np.complex128], ...]:
        return tuple(self._state_history)

    @property
    def coherence_trend(self) -> list[float]:
        return self._coherence_history[-100:]

    def _matrix_sqrt(self, matrix: NDArray[np.complex128]) -> NDArray[np.complex128]:
        values = np.asarray(matrix, dtype=np.complex128)
        hermitian = (values + values.conj().T) / 2.0
        eigenvalues, eigenvectors = np.linalg.eigh(hermitian)
        eigenvalues = np.maximum(eigenvalues.real, 0.0)
        return eigenvectors @ np.diag(np.sqrt(eigenvalues)) @ eigenvectors.conj().T


__all__ = [
    "CoherenceClassification",
    "ManifoldConfig",
    "ManifoldOperator",
    "ManifoldState",
    "OperatorEvolution",
]
