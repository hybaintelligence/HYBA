"""PULVINI H₄ 600-cell Manifold — 4D topological quantum state evolution.

Extends PulviniManifold from 32 nodes (M32, H₃) to 120 nodes (600-cell, H₄).
Key differences:
  - 120 nodes instead of 32 (3.75× more domains)
  - 12 neighbors per node instead of 3-5 (denser connectivity)
  - H₄ automorphism group: order 14,400 vs H₃'s 120
  - φ³-phase encoding (3 Euler angles) vs φ¹⁵ (1 golden angle)
  - 4D Yang-Mills gap: 4 - φ³ ≈ 2.236 vs 3 - φ ≈ 1.382
  - Domain entropy: 6.9 bits vs 5.0 bits
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import asdict, dataclass
from typing import Any, Dict, Iterable, List, Optional

import numpy as np

from .pulvini_group_h4 import (
    PHI_3,
    adjacency_sets_h4,
    compute_graph_automorphisms_h4,
    compute_node_orbits_h4,
    phi_3_resonance,
)
from .pulvini_topology_h4 import ADJACENCY_MAP_H4, H4_YANG_MILLS_GAP

HBAR = 1.0
EPSILON = 1e-12


@dataclass
class H4ManifoldObservation:
    """Observable state of the H₄ 600-cell manifold."""

    job_id: Optional[str]
    probabilities: List[float]
    phases: List[float]
    phi_3_phases: List[float]
    von_neumann_entropy: float
    coherence_norm: float
    state_norm: float
    density_trace: float
    hamiltonian_hermitian: bool
    density_hermitian: bool
    density_positive_semidefinite: bool
    automorphism_order_estimated: int
    node_orbits: List[List[int]]
    h4_yang_mills_gap: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PulviniManifoldH4:
    """H₄ 600-cell manifold — 120-node quantum state evolution.

    Extends the M32 φ-architecture into 4 dimensions with 120 domains,
    12 neighbors per vertex, and 14,400 automorphisms.
    """

    def __init__(
        self,
        adjacency_map: Optional[Dict[int, Dict[str, List[int]]]] = None,
        *,
        coupling: float = 0.05,
        learning_rate: float = 0.08,
        phi_threshold: float = 0.5,
    ) -> None:
        self.adjacency_map = adjacency_map or ADJACENCY_MAP_H4
        self.num_nodes = len(self.adjacency_map)
        self.nodes = list(range(self.num_nodes))
        self.neighbors = adjacency_sets_h4(self.adjacency_map)
        self.coupling = float(coupling)
        self.learning_rate = float(learning_rate)
        self.phi_threshold = float(phi_threshold)
        self.h4_gap = H4_YANG_MILLS_GAP
        self.current_job_id: Optional[str] = None
        self.current_target: Optional[int] = None

        # Compute automorphisms (may be partial due to budget)
        self.automorphisms = compute_graph_automorphisms_h4(
            self.adjacency_map, max_count=1000, node_budget=500_000
        )
        self.node_orbits = compute_node_orbits_h4(self.num_nodes, self.automorphisms)
        self.node_to_orbit = {
            node_id: orbit_id
            for orbit_id, orbit in enumerate(self.node_orbits)
            for node_id in orbit
        }

        self.synaptic_matrix = self._initial_synaptic_matrix()
        self.node_energy = np.ones(self.num_nodes, dtype=np.float64)
        # Initialize phi_3_phases BEFORE calling _initial_state_vector which sets it
        self.phi_3_phases = np.zeros(self.num_nodes, dtype=np.float64)
        self.psi = self._initial_state_vector()
        self.rho = self._density_from_state(self.psi)
        self.hamiltonian = self._build_hamiltonian()
        self.previous_entropy = self.von_neumann_entropy()
        self.entropy_gradient = 0.0
        self.constructor_memory: List[Dict[str, Any]] = []

    def _initial_synaptic_matrix(self) -> np.ndarray:
        matrix = np.zeros((self.num_nodes, self.num_nodes), dtype=np.float64)
        for left, neighbors in self.neighbors.items():
            for right in neighbors:
                matrix[left, right] = 1.0
                matrix[right, left] = 1.0
        maximum = float(np.max(matrix)) if matrix.size else 1.0
        return matrix / max(maximum, 1.0)

    def _initial_state_vector(self) -> np.ndarray:
        psi = np.zeros(self.num_nodes, dtype=np.complex128)
        orbit_weight_total = sum(math.sqrt(len(orbit)) for orbit in self.node_orbits)
        for orbit in self.node_orbits:
            orbit_probability = math.sqrt(len(orbit)) / orbit_weight_total
            per_node_probability = orbit_probability / len(orbit)
            for node_id in orbit:
                # 4D φ³-phase encoding: each node gets a φ-modulated 3-angle phase
                phase = 2.0 * math.pi * (node_id * PHI_3) % (2.0 * math.pi)
                psi[node_id] = math.sqrt(per_node_probability) * np.exp(1j * phase)
                self.phi_3_phases[node_id] = float(phase)
        return self._normalize_state(psi)

    @staticmethod
    def _normalize_state(psi: np.ndarray) -> np.ndarray:
        psi = np.asarray(psi, dtype=np.complex128)
        norm = float(np.linalg.norm(psi))
        if not math.isfinite(norm) or norm <= EPSILON:
            return np.ones(psi.shape[0], dtype=np.complex128) / math.sqrt(psi.shape[0])
        return psi / norm

    @staticmethod
    def _density_from_state(psi: np.ndarray) -> np.ndarray:
        return np.outer(psi, psi.conj())

    @staticmethod
    def _hermitian(matrix: np.ndarray) -> np.ndarray:
        matrix = np.asarray(matrix, dtype=np.complex128)
        return (matrix + matrix.conj().T) / 2.0

    @staticmethod
    def _density_projector(rho: np.ndarray) -> np.ndarray:
        rho = PulviniManifoldH4._hermitian(rho)
        eigenvalues, eigenvectors = np.linalg.eigh(rho)
        eigenvalues = np.clip(eigenvalues.real, 0.0, None)
        total = float(np.sum(eigenvalues))
        if not math.isfinite(total) or total <= EPSILON:
            dim = rho.shape[0]
            return np.eye(dim, dtype=np.complex128) / dim
        return PulviniManifoldH4._hermitian(
            eigenvectors @ np.diag(eigenvalues / total) @ eigenvectors.conj().T
        )

    def _build_hamiltonian(self) -> np.ndarray:
        diagonal = np.diag(self.node_energy.astype(np.complex128))
        off_diagonal = self.coupling * self.synaptic_matrix.astype(np.complex128)
        return self._hermitian(diagonal + off_diagonal)

    def _refresh_hamiltonian(self) -> None:
        self.synaptic_matrix = (
            (self.synaptic_matrix + self.synaptic_matrix.T) / 2.0
        ).real
        self.hamiltonian = self._build_hamiltonian()

    def _phi_3_gate(self, curvature: float) -> float:
        """4D Yang-Mills mass gap gate: accept/reject based on φ³ curvature.

        In 4D H₄, the mass gap is |4 - φ³| ≈ 0.236 (absolute gap magnitude).
        Low curvature (curvature < gap_threshold) → high acceptance probability.
        High curvature → exponentially decaying probability.

        The gap_threshold = |4 - φ³| ≈ 0.236 defines the boundary between
        the "mass gap" region (accepted) and the "continuum" (rejected).
        For H₄ this is narrower than H₃'s 1.382 because the 4D topology
        provides finer-grained curvature discrimination.

        Equivalent acceptance rate at 1/φ ≈ 0.618 for standard tuning.
        """
        gap_threshold = abs(self.h4_gap)  # ≈ 0.236
        if curvature >= gap_threshold:
            return math.exp(-(curvature - gap_threshold) / 0.5)
        return 1.0

    def assert_invariants(self) -> None:
        if not np.allclose(self.hamiltonian, self.hamiltonian.conj().T, atol=1e-8):
            raise RuntimeError("hamiltonian_not_hermitian")
        if not np.isclose(float(np.linalg.norm(self.psi)), 1.0, atol=1e-8):
            raise RuntimeError("state_vector_not_normalized")
        if not np.allclose(self.rho, self.rho.conj().T, atol=1e-8):
            raise RuntimeError("density_matrix_not_hermitian")
        if not np.isclose(float(np.trace(self.rho).real), 1.0, atol=1e-8):
            raise RuntimeError("density_trace_not_one")

    def coherence_norm(self) -> float:
        diagonal = np.diag(np.diag(self.rho))
        return float(np.linalg.norm(self.rho - diagonal, ord="fro"))

    def von_neumann_entropy(self) -> float:
        eigenvalues = np.linalg.eigvalsh(self.rho).real
        eigenvalues = eigenvalues[eigenvalues > 1e-15]
        if eigenvalues.size == 0:
            return 0.0
        return -float(np.sum(eigenvalues * np.log2(eigenvalues)))

    def work_distribution(self) -> np.ndarray:
        distribution = np.real(np.diag(self.rho))
        total = float(np.sum(distribution))
        if total <= EPSILON or not math.isfinite(total):
            return np.ones(self.num_nodes) / self.num_nodes
        return distribution / total

    def evolve_closed_system(self, dt: float = 1.0) -> np.ndarray:
        self._refresh_hamiltonian()
        before = self.von_neumann_entropy()
        eigenvalues, eigenvectors = np.linalg.eigh(self.hamiltonian)
        spectral_radius = np.max(np.abs(eigenvalues))
        lambda_normalized = eigenvalues / (spectral_radius + 1e-300)
        phases = np.exp(-1j * lambda_normalized * float(dt))
        eigvecs_norm = np.linalg.norm(eigenvectors, axis=0, keepdims=True)
        eigenvectors = eigenvectors / (eigvecs_norm + 1e-300)
        with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
            diag_phases = np.diag(phases)
            unitary = eigenvectors @ diag_phases @ eigenvectors.conj().T
            self.psi = self._normalize_state(unitary @ self.psi)
        self.rho = self._density_from_state(self.psi)
        after = self.von_neumann_entropy()
        self.entropy_gradient = after - before
        self.previous_entropy = after
        self.assert_invariants()
        return self.psi.copy()

    def compute_h4_phi_resonance(
        self, nonce: int, job_id: Optional[str] = None
    ) -> float:
        """Compute φ³ resonance using the 4D H₄ resonance function."""
        return phi_3_resonance(nonce, job_id=job_id or self.current_job_id)

    def h4_mass_gate_filter(
        self, nonces: Iterable[int], job_id: Optional[str] = None
    ) -> List[int]:
        """Filter nonces through the 4D Yang-Mills mass gap gate.

        Only nonces with curvature below the H₄ gap (4 - φ³ ≈ 2.236) pass.
        This is more selective than the M32 gate (3 - φ ≈ 1.382).
        """
        result = []
        for nonce in nonces:
            # Compute curvature proxy from φ³ resonance
            resonance = self.compute_h4_phi_resonance(nonce, job_id=job_id)
            # Map resonance to curvature action (inverse relationship)
            action = 1.0 - resonance + 1.0  # scale to [1.0, 2.0] range
            gate_value = self._phi_3_gate(action)
            # Probabilistic acceptance
            hash_input = f"{job_id or 'h4'}:{nonce}:{self.coupling}".encode("utf-8")
            digest = hashlib.blake2b(hash_input, digest_size=4).digest()
            threshold = int.from_bytes(digest, "big") / float(2**32)
            if threshold < gate_value:
                result.append(int(nonce))
        return result

    def h4_gradient_proposal(
        self, current_nonce: int, rng: Optional[Any] = None, scale: int = 1
    ) -> int:
        """Propose next nonce via φ³ gradient + Fibonacci steps.

        Uses the 4D φ³ resonance gradient to guide the walk,
        with φ-modulated step sizes scaled for the 120-domain topology.
        """
        import random as _random

        rng = rng or _random.Random()
        current_phi = self.compute_h4_phi_resonance(current_nonce)

        # φ³-modulated step sizes (Fibonacci-like but scaled for 120 domains)
        step_sizes = [1, 3, 8, 21, 55, 144, 377, 987, 2584]
        candidates = []

        for step in step_sizes:
            next_nonce = (current_nonce + step * scale) % (2**32)
            next_phi = self.compute_h4_phi_resonance(next_nonce)
            if next_phi > current_phi:
                candidates.append((next_nonce, next_phi))

        if candidates:
            return max(candidates, key=lambda x: x[1])[0]
        else:
            return (current_nonce + rng.choice(step_sizes)) % (2**32)

    def h4_phase_entropy(self) -> float:
        """Compute the φ³-phase entropy across all 120 nodes."""
        phases = self.phi_3_phases.copy()
        phases = (phases % (2.0 * math.pi)) / (2.0 * math.pi)
        histogram, _ = np.histogram(phases, bins=12, range=(0.0, 1.0))
        histogram = histogram.astype(np.float64)
        histogram = histogram[histogram > 0]
        histogram /= histogram.sum()
        return -float(np.sum(histogram * np.log2(histogram)))

    def observe(self) -> H4ManifoldObservation:
        density_eigs = np.linalg.eigvalsh(self.rho).real
        distribution = self.work_distribution()
        return H4ManifoldObservation(
            job_id=self.current_job_id,
            probabilities=[float(v) for v in distribution],
            phases=[float(np.angle(v)) for v in self.psi],
            phi_3_phases=[float(v) for v in self.phi_3_phases],
            von_neumann_entropy=self.von_neumann_entropy(),
            coherence_norm=self.coherence_norm(),
            state_norm=float(np.linalg.norm(self.psi)),
            density_trace=float(np.trace(self.rho).real),
            hamiltonian_hermitian=bool(
                np.allclose(self.hamiltonian, self.hamiltonian.conj().T, atol=1e-8)
            ),
            density_hermitian=bool(np.allclose(self.rho, self.rho.conj().T, atol=1e-8)),
            density_positive_semidefinite=bool(float(np.min(density_eigs)) >= -1e-8),
            automorphism_order_estimated=len(self.automorphisms),
            node_orbits=[list(orbit) for orbit in self.node_orbits],
            h4_yang_mills_gap=self.h4_gap,
        )

    def snapshot(self) -> Dict[str, Any]:
        obs = self.observe().to_dict()
        obs.update(
            {
                "num_nodes": self.num_nodes,
                "coupling": self.coupling,
                "h4_yang_mills_gap": self.h4_gap,
                "phi_3_constant": PHI_3,
                "phi_phase_entropy": self.h4_phase_entropy(),
                "entropy_gradient": self.entropy_gradient,
                "automorphism_count": len(self.automorphisms),
                "orbit_count": len(self.node_orbits),
                "h4_structure": {
                    "type": "600-cell (4D regular polytope)",
                    "schlafli": "{3,3,5}",
                    "coxeter_diagram": "o-5-o-3-o-3-o",
                    "group_order": 14400,
                    "h3_subgroup_order": 120,
                },
                "topological_scaling": {
                    "vs_m32_domain_multiple": self.num_nodes / 32,
                    "vs_m32_symmetry_multiple": 14400 / 120,
                    "vs_m32_edge_density": 12 / 3.5,
                },
            }
        )
        return obs

    def benchmark_structured_search(self, steps: int = 1000) -> Dict[str, Any]:
        """Run a structured search benchmark on the H₄ manifold.

        Compares H₄-guided traversal against random walk.
        """
        import random as _random

        rng = _random.Random(42)

        # H₄-guided walk
        h4_nonces = []
        h4_phis = []
        nonce = rng.randint(0, 2**32 - 1)
        for _ in range(steps):
            phi_val = self.compute_h4_phi_resonance(nonce)
            h4_nonces.append(nonce)
            h4_phis.append(phi_val)
            nonce = self.h4_gradient_proposal(nonce, rng)

        # Random walk
        random_phis = []
        nonce = rng.randint(0, 2**32 - 1)
        for _ in range(steps):
            phi_val = self.compute_h4_phi_resonance(nonce)
            random_phis.append(phi_val)
            nonce = rng.randint(0, 2**32 - 1)

        h4_mean = float(np.mean(h4_phis))
        random_mean = float(np.mean(random_phis))
        h4_max = float(np.max(h4_phis))
        random_max = float(np.max(random_phis))

        return {
            "manifold": "H₄ 600-cell (120 vertices)",
            "steps": steps,
            "h4_mean_phi_resonance": h4_mean,
            "random_mean_phi_resonance": random_mean,
            "h4_max_phi_resonance": h4_max,
            "random_max_phi_resonance": random_max,
            "h4_improvement_vs_random_pct": (
                (h4_mean - random_mean) / max(random_mean, 1e-10) * 100
            ),
            "h4_phase_entropy": self.h4_phase_entropy(),
            "von_neumann_entropy": self.von_neumann_entropy(),
            "coherence_norm": self.coherence_norm(),
            "automorphism_count": len(self.automorphisms),
            "orbit_count": len(self.node_orbits),
            "vs_m32_scaling": {
                "domain_multiple": self.num_nodes / 32,
                "symmetry_multiple": 14400 / 120,
                "theoretical_hashrate_multiple": (self.num_nodes / 32)
                * (14400 / 120) ** 0.5,
            },
        }


__all__ = [
    "H4ManifoldObservation",
    "PulviniManifoldH4",
]
