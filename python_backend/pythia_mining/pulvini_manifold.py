"""PULVINI mathematical manifold control layer.

The 32 PULVINI nodes are represented as a single substrate-agnostic
mathematical state. The control objects are a complex state vector, density
matrix, Hermitian Hamiltonian, graph automorphism action, Hebbian edge weights,
Lindblad back-action channels, and a shared-memory blackboard.
"""

from __future__ import annotations

import hashlib
import math
import time
from dataclasses import asdict, dataclass, field
from multiprocessing import shared_memory
from threading import RLock
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

from .pulvini_group import (
    NONCE_SPACE,
    TensorCoordinate,
    adjacency_sets,
    apply_automorphism_to_nonce,
    compute_graph_automorphisms,
    compute_node_orbits,
    nonce_orbit,
    tensor_coordinate_for_node,
)

HBAR = 1.0
EPSILON = 1e-12


@dataclass
class ManifoldObservation:
    job_id: Optional[str]
    probabilities: List[float]
    phases: List[float]
    von_neumann_entropy: float
    coherence_norm: float
    state_norm: float
    density_trace: float
    hamiltonian_hermitian: bool
    density_hermitian: bool
    density_positive_semidefinite: bool
    automorphism_order: int
    node_orbits: List[List[int]]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BackActionEvent:
    event_type: str
    node_id: int
    job_id: Optional[str]
    strength: float
    affected_nodes: List[int]
    entropy_before: float
    entropy_after: float
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SharedManifoldBlackboard:
    """Zero-copy shared memory surface for the complex 32-node state vector."""

    def __init__(self, *, name: Optional[str] = None, num_nodes: int = 32, create: bool = True):
        self.num_nodes = int(num_nodes)
        self.size = self.num_nodes * 2 * 8
        self.shm = shared_memory.SharedMemory(name=name, create=create, size=self.size)
        self.name = self.shm.name

    def write_state(self, psi: np.ndarray) -> None:
        psi = np.asarray(psi, dtype=np.complex128)
        if psi.shape != (self.num_nodes,):
            raise ValueError(f"psi must have shape ({self.num_nodes},)")
        view = np.ndarray((self.num_nodes, 2), dtype=np.float64, buffer=self.shm.buf)
        view[:, 0] = psi.real
        view[:, 1] = psi.imag

    def read_state(self) -> np.ndarray:
        view = np.ndarray((self.num_nodes, 2), dtype=np.float64, buffer=self.shm.buf)
        return view[:, 0].copy() + 1j * view[:, 1].copy()

    def close(self) -> None:
        self.shm.close()

    def unlink(self) -> None:
        self.shm.unlink()


class PulviniManifold:
    """Mathematical control substrate for the PULVINI 32-node topology."""

    def __init__(
        self,
        adjacency_map: Dict[int, Dict[str, List[int]]],
        *,
        coupling: float = 0.05,
        learning_rate: float = 0.08,
        phi_threshold: float = 0.5,
    ) -> None:
        self.adjacency_map = adjacency_map
        self.num_nodes = len(adjacency_map)
        self.nodes = list(range(self.num_nodes))
        self.neighbors = adjacency_sets(adjacency_map)
        self.coupling = float(coupling)
        self.learning_rate = float(learning_rate)
        self.phi_threshold = float(phi_threshold)
        self.current_job_id: Optional[str] = None
        self.current_target: Optional[int] = None
        self._lock = RLock()
        self.blackboard: Optional[SharedManifoldBlackboard] = None

        self.automorphisms = compute_graph_automorphisms(adjacency_map)
        self.node_orbits = compute_node_orbits(self.num_nodes, self.automorphisms)
        self.node_to_orbit = {
            node_id: orbit_id
            for orbit_id, orbit in enumerate(self.node_orbits)
            for node_id in orbit
        }

        self.synaptic_matrix = self._initial_synaptic_matrix()
        self.node_energy = np.ones(self.num_nodes, dtype=np.float64)
        self.psi = self._initial_state_vector()
        self.rho = self._density_from_state(self.psi)
        self.hamiltonian = self._build_hamiltonian()
        self.previous_entropy = self.von_neumann_entropy()
        self.entropy_gradient = 0.0
        self.backaction_ledger: List[BackActionEvent] = []
        self.constructor_memory: List[Dict[str, Any]] = []
        self.assert_invariants()

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
                phase = 2.0 * math.pi * (node_id + 1) / self.num_nodes
                psi[node_id] = math.sqrt(per_node_probability) * np.exp(1j * phase)
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
        rho = PulviniManifold._hermitian(rho)
        eigenvalues, eigenvectors = np.linalg.eigh(rho)
        eigenvalues = np.clip(eigenvalues.real, 0.0, None)
        total = float(np.sum(eigenvalues))
        if not math.isfinite(total) or total <= EPSILON:
            dim = rho.shape[0]
            return np.eye(dim, dtype=np.complex128) / dim
        return PulviniManifold._hermitian(eigenvectors @ np.diag(eigenvalues / total) @ eigenvectors.conj().T)

    def _build_hamiltonian(self) -> np.ndarray:
        diagonal = np.diag(self.node_energy.astype(np.complex128))
        off_diagonal = self.coupling * self.synaptic_matrix.astype(np.complex128)
        return self._hermitian(diagonal + off_diagonal)

    def _refresh_hamiltonian(self) -> None:
        self.synaptic_matrix = ((self.synaptic_matrix + self.synaptic_matrix.T) / 2.0).real
        self.hamiltonian = self._build_hamiltonian()

    def attach_blackboard(self, blackboard: SharedManifoldBlackboard) -> None:
        self.blackboard = blackboard
        self._write_blackboard()

    def _write_blackboard(self) -> None:
        if self.blackboard is not None:
            self.blackboard.write_state(self.psi)

    def assert_invariants(self) -> None:
        if not np.allclose(self.hamiltonian, self.hamiltonian.conj().T, atol=1e-10):
            raise RuntimeError("hamiltonian_not_hermitian")
        if not np.isclose(float(np.linalg.norm(self.psi)), 1.0, atol=1e-10):
            raise RuntimeError("state_vector_not_normalized")
        if not np.allclose(self.rho, self.rho.conj().T, atol=1e-10):
            raise RuntimeError("density_matrix_not_hermitian")
        if not np.isclose(float(np.trace(self.rho).real), 1.0, atol=1e-10):
            raise RuntimeError("density_trace_not_one")
        if float(np.min(np.linalg.eigvalsh(self.rho).real)) < -1e-9:
            raise RuntimeError("density_matrix_not_positive_semidefinite")

    def begin_job(self, job_id: str, target: int) -> None:
        with self._lock:
            self.current_job_id = str(job_id)
            self.current_target = int(target)
            self.psi = self._initial_state_vector()
            self.rho = self._density_from_state(self.psi)
            self.node_energy = np.ones(self.num_nodes, dtype=np.float64)
            self._refresh_hamiltonian()
            self.previous_entropy = self.von_neumann_entropy()
            self.entropy_gradient = 0.0
            self.constructor_memory.append({
                "event": "begin_job",
                "job_id": self.current_job_id,
                "target": self.current_target,
                "automorphism_order": len(self.automorphisms),
                "timestamp": time.time(),
            })
            self.assert_invariants()
            self._write_blackboard()

    def work_distribution(self) -> np.ndarray:
        distribution = np.real(np.diag(self.rho))
        total = float(np.sum(distribution))
        if total <= EPSILON or not math.isfinite(total):
            return np.ones(self.num_nodes) / self.num_nodes
        return distribution / total

    def coherence_norm(self) -> float:
        diagonal = np.diag(np.diag(self.rho))
        return float(np.linalg.norm(self.rho - diagonal, ord="fro"))

    def von_neumann_entropy(self) -> float:
        eigenvalues = np.linalg.eigvalsh(self.rho).real
        eigenvalues = eigenvalues[eigenvalues > 1e-15]
        if eigenvalues.size == 0:
            return 0.0
        return -float(np.sum(eigenvalues * np.log2(eigenvalues)))

    def control_collapse_energy(self) -> float:
        return abs(float(self.entropy_gradient)) * max(self.coherence_norm(), EPSILON)

    def evolve_closed_system(self, dt: float = 1.0) -> np.ndarray:
        with self._lock:
            self._refresh_hamiltonian()
            before = self.von_neumann_entropy()
            eigenvalues, eigenvectors = np.linalg.eigh(self.hamiltonian)
            unitary = eigenvectors @ np.diag(np.exp((-1j * eigenvalues * float(dt)) / HBAR)) @ eigenvectors.conj().T
            if not np.allclose(unitary.conj().T @ unitary, np.eye(self.num_nodes), atol=1e-9):
                raise RuntimeError("unitary_operator_invariant_failed")
            self.psi = self._normalize_state(unitary @ self.psi)
            self.rho = self._density_from_state(self.psi)
            after = self.von_neumann_entropy()
            self.entropy_gradient = after - before
            self.previous_entropy = after
            self.assert_invariants()
            self._write_blackboard()
            return self.psi.copy()

    def lindblad_step(self, jump_operators: Sequence[np.ndarray], dt: float = 1.0) -> np.ndarray:
        with self._lock:
            self._refresh_hamiltonian()
            before = self.von_neumann_entropy()
            commutator = self.hamiltonian @ self.rho - self.rho @ self.hamiltonian
            derivative = (-1j / HBAR) * commutator
            for operator in jump_operators:
                l_op = np.asarray(operator, dtype=np.complex128)
                ldag_l = l_op.conj().T @ l_op
                derivative += l_op @ self.rho @ l_op.conj().T - 0.5 * (ldag_l @ self.rho + self.rho @ ldag_l)
            self.rho = self._density_projector(self.rho + float(dt) * derivative)
            eigenvalues, eigenvectors = np.linalg.eigh(self.rho)
            self.psi = self._normalize_state(eigenvectors[:, int(np.argmax(eigenvalues.real))])
            after = self.von_neumann_entropy()
            self.entropy_gradient = after - before
            self.previous_entropy = after
            self.assert_invariants()
            self._write_blackboard()
            return self.rho.copy()

    def jump_operators_from_node(self, node_id: int, strength: float = 0.2) -> List[np.ndarray]:
        node_id = int(node_id)
        targets = sorted(self.neighbors[node_id])
        if not targets:
            return []
        scale = math.sqrt(max(float(strength), 0.0) / len(targets))
        jumps: List[np.ndarray] = []
        for target in targets:
            op = np.zeros((self.num_nodes, self.num_nodes), dtype=np.complex128)
            op[target, node_id] = scale
            jumps.append(op)
        return jumps

    def nack_slice(self, node_id: int, job_id: str, nonce_start: int, nonce_end: int, strength: float = 0.2) -> BackActionEvent:
        before = self.von_neumann_entropy()
        self.lindblad_step(self.jump_operators_from_node(node_id, strength), dt=1.0)
        after = self.von_neumann_entropy()
        event = BackActionEvent(
            event_type="nack_slice_exhausted",
            node_id=int(node_id),
            job_id=str(job_id),
            strength=float(strength),
            affected_nodes=sorted(self.neighbors[int(node_id)]),
            entropy_before=before,
            entropy_after=after,
        )
        self.backaction_ledger.append(event)
        self.constructor_memory.append({
            **event.to_dict(),
            "nonce_start": int(nonce_start),
            "nonce_end": int(nonce_end),
        })
        return event

    def observe_high_difficulty_hash(self, node_id: int, difficulty_score: float) -> None:
        with self._lock:
            node_id = int(node_id)
            self.node_energy[node_id] = max(self.node_energy[node_id], 1.0 + float(difficulty_score))
            self.psi[node_id] *= np.exp(1j * min(float(difficulty_score), math.pi))
            self.psi = self._normalize_state(self.psi)
            self.rho = self._density_from_state(self.psi)
            self._refresh_hamiltonian()
            self.constructor_memory.append({
                "event": "high_difficulty_observation",
                "node_id": node_id,
                "difficulty_score": float(difficulty_score),
                "job_id": self.current_job_id,
                "timestamp": time.time(),
            })
            self.assert_invariants()
            self._write_blackboard()

    def collapse_if_threshold(self, found_node: int, critical_value: float) -> bool:
        with self._lock:
            if self.control_collapse_energy() < float(critical_value):
                return False
            psi = np.zeros(self.num_nodes, dtype=np.complex128)
            psi[int(found_node)] = 1.0 + 0.0j
            self.psi = psi
            self.rho = self._density_from_state(self.psi)
            self.constructor_memory.append({
                "event": "threshold_projection",
                "node_id": int(found_node),
                "control_energy": self.control_collapse_energy(),
                "critical_value": float(critical_value),
                "job_id": self.current_job_id,
                "timestamp": time.time(),
            })
            self.assert_invariants()
            self._write_blackboard()
            return True

    def phi_resonance_score(self, nonce: int, job_id: Optional[str] = None) -> float:
        material = f"{job_id or self.current_job_id or 'job'}:{int(nonce) % NONCE_SPACE}".encode("utf-8")
        digest = hashlib.blake2b(material, digest_size=8).digest()
        sample = int.from_bytes(digest, "big") / float(2 ** 64)
        phi = (1.0 + math.sqrt(5.0)) / 2.0
        return 1.0 - abs(0.5 - ((sample * phi) % 1.0)) * 2.0

    def apply_phi_projection_operator(self, nonces: Iterable[int], threshold: Optional[float] = None, job_id: Optional[str] = None) -> List[int]:
        cutoff = self.phi_threshold if threshold is None else float(threshold)
        return [int(nonce) for nonce in nonces if self.phi_resonance_score(int(nonce), job_id=job_id) >= cutoff]

    def calibrate_phi_projection(self, nonces: Iterable[int], threshold: Optional[float] = None, job_id: Optional[str] = None) -> Dict[str, Any]:
        sample = list(nonces)
        accepted = self.apply_phi_projection_operator(sample, threshold=threshold, job_id=job_id)
        return {
            "sample_size": len(sample),
            "accepted": len(accepted),
            "acceptance_ratio": 0.0 if not sample else len(accepted) / len(sample),
            "threshold": self.phi_threshold if threshold is None else float(threshold),
        }

    def hebbian_fire(self, path: Sequence[int], signal_type: str = "SHARE_FOUND", reward: Optional[float] = None) -> None:
        if len(path) < 2:
            return
        reward_value = float(reward if reward is not None else (1.0 if signal_type == "SHARE_FOUND" else -0.1))
        with self._lock:
            for left, right in zip(path, path[1:]):
                if int(right) not in self.neighbors[int(left)]:
                    raise ValueError(f"non_adjacent_path_edge:{left}->{right}")
                new_weight = max(0.0, float(self.synaptic_matrix[int(left), int(right)]) + self.learning_rate * reward_value)
                self.synaptic_matrix[int(left), int(right)] = new_weight
                self.synaptic_matrix[int(right), int(left)] = new_weight
            self._refresh_hamiltonian()
            self.constructor_memory.append({
                "event": "hebbian_fire",
                "path": list(map(int, path)),
                "signal_type": signal_type,
                "reward": reward_value,
                "timestamp": time.time(),
            })
            self.assert_invariants()

    def edge_weight(self, left: int, right: int) -> float:
        return float(self.synaptic_matrix[int(left), int(right)])

    def route_probabilities(self, node_id: int) -> Dict[int, float]:
        weights = {neighbor: max(self.edge_weight(node_id, neighbor), 0.0) for neighbor in self.neighbors[int(node_id)]}
        total = sum(weights.values())
        if total <= EPSILON:
            return {neighbor: 1.0 / len(weights) for neighbor in weights}
        return {neighbor: weight / total for neighbor, weight in weights.items()}

    def _hop_distance(self, start: int, end: int) -> int:
        if start == end:
            return 0
        queue = [(start, 0)]
        seen = {start}
        index = 0
        while index < len(queue):
            node, distance = queue[index]
            index += 1
            for neighbor in self.neighbors[node]:
                if neighbor == end:
                    return distance + 1
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append((neighbor, distance + 1))
        return self.num_nodes

    def gradient_route_to_gateway(self, finder_id: int, gateway_id: int = 31) -> List[int]:
        route = [int(finder_id)]
        seen = {int(finder_id)}
        current = int(finder_id)
        while current != int(gateway_id):
            candidates = [node for node in self.neighbors[current] if node not in seen]
            if not candidates:
                raise RuntimeError(f"no_route_to_gateway:{finder_id}->{gateway_id}")
            candidates.sort(key=lambda node: (self._hop_distance(node, int(gateway_id)), -self.edge_weight(current, node)))
            current = candidates[0]
            route.append(current)
            seen.add(current)
            if len(route) > self.num_nodes:
                raise RuntimeError("gradient_route_loop")
        return route

    def gradient_broadcast_order(self, gateway_id: int = 31) -> List[int]:
        order = [int(gateway_id)]
        seen = {int(gateway_id)}
        frontier = [int(gateway_id)]
        while frontier:
            next_frontier: List[int] = []
            for node in frontier:
                candidates = [neighbor for neighbor in self.neighbors[node] if neighbor not in seen]
                candidates.sort(key=lambda neighbor: self.edge_weight(node, neighbor), reverse=True)
                for neighbor in candidates:
                    seen.add(neighbor)
                    order.append(neighbor)
                    next_frontier.append(neighbor)
            frontier = next_frontier
        if len(order) != self.num_nodes:
            raise RuntimeError(f"gradient_broadcast_incomplete:{len(order)}/{self.num_nodes}")
        return order

    def phase_heartbeat(self, job_id: str, tick: int) -> List[float]:
        with self._lock:
            phases = []
            for node_id in self.nodes:
                orbit_id = self.node_to_orbit[node_id]
                phase = 2.0 * math.pi * ((int(tick) + node_id + orbit_id) % self.num_nodes) / self.num_nodes
                self.psi[node_id] = abs(self.psi[node_id]) * np.exp(1j * phase)
                phases.append(float(phase))
            self.psi = self._normalize_state(self.psi)
            self.rho = self._density_from_state(self.psi)
            self.constructor_memory.append({"event": "phase_heartbeat", "job_id": str(job_id), "tick": int(tick), "timestamp": time.time()})
            self.assert_invariants()
            self._write_blackboard()
            return phases

    def manifold_drift_extranonce2(self, node_id: int, job_id: str, extranonce2_size: int) -> str:
        coord = self.tensor_coordinate_for_node(node_id)
        material = f"{job_id}:{coord.orbit_id}:{coord.node_id}:{len(self.automorphisms)}".encode("utf-8")
        digest = hashlib.blake2b(material, digest_size=max(int(extranonce2_size), 1)).digest()
        return digest.hex()[: max(int(extranonce2_size), 1) * 2]

    def tensor_coordinate_for_node(self, node_id: int) -> TensorCoordinate:
        distribution = self.work_distribution()
        phase = float(np.angle(self.psi[int(node_id)]))
        return tensor_coordinate_for_node(
            int(node_id),
            num_nodes=self.num_nodes,
            node_orbits=self.node_orbits,
            node_to_orbit=self.node_to_orbit,
            amplitude=float(distribution[int(node_id)]),
            phase=phase,
        )

    def tensor_coordinates(self) -> List[TensorCoordinate]:
        return [self.tensor_coordinate_for_node(node_id) for node_id in self.nodes]

    def nonce_orbit(self, nonce: int) -> List[int]:
        return nonce_orbit(int(nonce), self.automorphisms, self.num_nodes)

    def apply_automorphism_to_nonce(self, nonce: int, automorphism: Sequence[int]) -> int:
        return apply_automorphism_to_nonce(int(nonce), automorphism, self.num_nodes)

    def observe(self) -> ManifoldObservation:
        density_eigs = np.linalg.eigvalsh(self.rho).real
        return ManifoldObservation(
            job_id=self.current_job_id,
            probabilities=[float(value) for value in self.work_distribution()],
            phases=[float(np.angle(value)) for value in self.psi],
            von_neumann_entropy=self.von_neumann_entropy(),
            coherence_norm=self.coherence_norm(),
            state_norm=float(np.linalg.norm(self.psi)),
            density_trace=float(np.trace(self.rho).real),
            hamiltonian_hermitian=bool(np.allclose(self.hamiltonian, self.hamiltonian.conj().T, atol=1e-10)),
            density_hermitian=bool(np.allclose(self.rho, self.rho.conj().T, atol=1e-10)),
            density_positive_semidefinite=bool(float(np.min(density_eigs)) >= -1e-9),
            automorphism_order=len(self.automorphisms),
            node_orbits=[list(orbit) for orbit in self.node_orbits],
        )

    def snapshot(self) -> Dict[str, Any]:
        payload = self.observe().to_dict()
        payload.update({
            "control_collapse_energy": self.control_collapse_energy(),
            "automorphism_group": {
                "order": len(self.automorphisms),
                "node_orbits": [list(orbit) for orbit in self.node_orbits],
                "nonce_action": "sigma(q*N+r)=q*N+sigma(r)",
            },
            "tensor_coordinates": [coordinate.to_dict() for coordinate in self.tensor_coordinates()],
            "backaction_ledger": [event.to_dict() for event in self.backaction_ledger[-32:]],
            "constructor_memory_tail": list(self.constructor_memory[-32:]),
        })
        return payload


__all__ = [
    "BackActionEvent",
    "ManifoldObservation",
    "PulviniManifold",
    "SharedManifoldBlackboard",
    "TensorCoordinate",
]
