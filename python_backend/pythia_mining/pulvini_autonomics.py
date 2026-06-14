"""Standalone PULVINI autonomics engine.

This module intentionally has no dependency on the HYBA web API runtime.  It is
safe to import from tests, workers, OVID/MCP tools, and the runtime mining orchestrator.
The engine models the 32-node PULVINI D/I compound as a density-state controller
with three feedback loops:

* homeostasis: telemetry -> coherence scores -> critical-node detection
* autopoietic healing: failed nonce slices -> geometric live-neighbor repair
* synaptic plasticity: Bures/Hellinger routing toward efficient live nodes

The topology is derived from ``pulvini_topology.ADJACENCY_MAP`` using only the
D<->I incidence edges.  The existing overlay graph also contains intra-D and
intra-I operational links; autonomic recovery deliberately uses the bipartite
compound so the formal degree profile remains 20*3 + 12*5 = 120.
"""

from __future__ import annotations

import math
import time
from collections import deque
from dataclasses import asdict, dataclass, field
from enum import Enum
from threading import RLock
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Protocol,
    Sequence,
    Set,
    Tuple,
)

import numpy as np

from .pulvini_group import compute_graph_automorphisms
from .pulvini_topology import ADJACENCY_MAP, MAX_UINT32_NONCE, NUM_NODES, SLICE_SIZE

EPSILON = 1e-12
DEFAULT_DECOHERENCE_THRESHOLD = 0.15
MAX_AUTONOMIC_FAILURES = 5


class NodeType(Enum):
    """Node class in the D/I compound."""

    DODECAHEDRON = "D"
    ICOSAHEDRON = "I"


class AuditSink(Protocol):
    """Minimal audit callback surface for THEMIS or another governance layer."""

    def __call__(self, event: Mapping[str, Any]) -> None: ...


class LatticeRepointSink(Protocol):
    """Minimal callback surface for the PYTHAGORAS lattice re-point bridge."""

    def __call__(self, command: Mapping[str, Any]) -> None: ...


@dataclass(frozen=True)
class NodeTelemetry:
    """Real-time metrics for one PULVINI node.

    ``tres`` is response latency in milliseconds. ``phi_eff`` and ``chi_sync``
    are normalized [0, 1] success/coherence values. ``thermal_entropy`` is the
    positive power/heat envelope used for hash-per-watt routing.
    """

    node_id: int
    tres: float
    phi_eff: float
    chi_sync: float
    thermal_entropy: float
    hash_rate: float
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if not 0 <= int(self.node_id) < NUM_NODES:
            raise ValueError(f"node_id must be in [0, {NUM_NODES - 1}]")
        for name in (
            "tres",
            "phi_eff",
            "chi_sync",
            "thermal_entropy",
            "hash_rate",
            "timestamp",
        ):
            value = float(getattr(self, name))
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite")
        if self.tres < 0:
            raise ValueError("tres must be non-negative")
        if not 0.0 <= self.phi_eff <= 1.0:
            raise ValueError("phi_eff must be in [0, 1]")
        if not 0.0 <= self.chi_sync <= 1.0:
            raise ValueError("chi_sync must be in [0, 1]")
        if self.thermal_entropy < 0:
            raise ValueError("thermal_entropy must be non-negative")
        if self.hash_rate < 0:
            raise ValueError("hash_rate must be non-negative")

    def coherence_score(
        self, weights: Tuple[float, float, float] = (0.33, 0.33, 0.34)
    ) -> float:
        """Return ``Si = w1*Tres + w2*phi_eff + w3*chi_sync`` in [0, 1]."""

        if len(weights) != 3:
            raise ValueError("weights must contain exactly three coefficients")
        total = float(sum(weights))
        if total <= EPSILON or any(weight < 0 for weight in weights):
            raise ValueError("weights must be non-negative and sum to a positive value")
        normalized_weights = tuple(float(weight) / total for weight in weights)
        tres_norm = max(0.0, 1.0 - min(float(self.tres) / 100.0, 1.0))
        score = (
            normalized_weights[0] * tres_norm
            + normalized_weights[1] * float(self.phi_eff)
            + normalized_weights[2] * float(self.chi_sync)
        )
        return float(min(max(score, 0.0), 1.0))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DodecahedronIcosahedronCompound:
    """Bipartite D/I autonomic topology over the 32 PULVINI runtime nodes."""

    def __init__(
        self, adjacency_map: Mapping[int, Mapping[str, Sequence[int]]] = ADJACENCY_MAP
    ) -> None:
        self.adjacency_map = adjacency_map
        self.num_nodes = NUM_NODES
        self.node_types: Dict[int, NodeType] = {
            node_id: NodeType.DODECAHEDRON if node_id < 20 else NodeType.ICOSAHEDRON
            for node_id in range(NUM_NODES)
        }
        self.adjacency = self._build_bipartite_adjacency()
        self.bipartite_adjacency_map = self._build_bipartite_adjacency_map()
        self.degrees = np.sum(self.adjacency, axis=1).astype(int)
        self.total_degree = int(np.sum(self.degrees))
        self.redundancy_factor = float(self.total_degree / self.num_nodes)
        self.automorphisms = compute_graph_automorphisms(self.bipartite_adjacency_map)
        self.automorphism_group_size = len(self.automorphisms)
        self._validate()

    def _build_bipartite_adjacency(self) -> np.ndarray:
        matrix = np.zeros((NUM_NODES, NUM_NODES), dtype=np.int8)
        for node_id in range(NUM_NODES):
            cross_key = "i" if node_id < 20 else "d"
            for neighbor in self.adjacency_map[node_id].get(cross_key, []):
                if (node_id < 20 <= int(neighbor)) or (int(neighbor) < 20 <= node_id):
                    matrix[node_id, int(neighbor)] = 1
                    matrix[int(neighbor), node_id] = 1
        return matrix

    def _build_bipartite_adjacency_map(self) -> Dict[int, Dict[str, List[int]]]:
        adjacency_map: Dict[int, Dict[str, List[int]]] = {}
        for node_id in range(NUM_NODES):
            cross_key = "i" if node_id < 20 else "d"
            adjacency_map[node_id] = {"d": [], "i": []}
            adjacency_map[node_id][cross_key] = [
                int(value) for value in np.where(self.adjacency[node_id] == 1)[0]
            ]
        return adjacency_map

    def _validate(self) -> None:
        if self.adjacency.shape != (NUM_NODES, NUM_NODES):
            raise ValueError("D/I adjacency matrix must be 32x32")
        if not np.array_equal(self.adjacency, self.adjacency.T):
            raise ValueError("D/I adjacency matrix must be symmetric")
        if np.any(np.diag(self.adjacency) != 0):
            raise ValueError("D/I adjacency matrix must not contain self loops")
        d_degrees = self.degrees[:20]
        i_degrees = self.degrees[20:]
        if not np.all(d_degrees == 3):
            raise ValueError(
                f"D-node degree profile must be exactly 3, got {d_degrees.tolist()}"
            )
        if not np.all(i_degrees == 5):
            raise ValueError(
                f"I-node degree profile must be exactly 5, got {i_degrees.tolist()}"
            )

    def neighbors(
        self, node_id: int, *, live_nodes: Optional[Set[int]] = None
    ) -> List[int]:
        self._validate_node_id(node_id)
        values = np.where(self.adjacency[int(node_id)] == 1)[0].astype(int).tolist()
        if live_nodes is not None:
            values = [neighbor for neighbor in values if neighbor in live_nodes]
        return values

    def node_type(self, node_id: int) -> NodeType:
        self._validate_node_id(node_id)
        return self.node_types[int(node_id)]

    def get_node_type(self, node_id: int) -> NodeType:
        """Compatibility alias for the original delivery-summary API."""

        return self.node_type(node_id)

    def healing_capacity(self, node_id: int) -> float:
        """Return the uniform direct-neighbor repair fraction for a node."""

        neighbors = self.neighbors(node_id)
        return 1.0 / float(len(neighbors))

    def nonce_range(self, node_id: int) -> Tuple[int, int]:
        self._validate_node_id(node_id)
        start = int(node_id) * SLICE_SIZE
        end = (
            MAX_UINT32_NONCE
            if int(node_id) == NUM_NODES - 1
            else start + SLICE_SIZE - 1
        )
        return start, end

    def healing_candidates(
        self, failed_node: int, failed_nodes: Iterable[int] = ()
    ) -> List[int]:
        """Return live repair nodes, expanding by BFS if direct neighbors failed.

        Direct geometric neighbors are always preferred.  If a clustered failure
        removes all direct neighbors, the method expands over the D/I graph until
        it finds a live frontier.  This keeps the engine deterministic for edge
        cases without overstating the Phase-1 guarantee.
        """

        self._validate_node_id(failed_node)
        failed: Set[int] = {int(node) for node in failed_nodes}
        failed.add(int(failed_node))
        direct = self.neighbors(
            int(failed_node), live_nodes=set(range(NUM_NODES)) - failed
        )
        if direct:
            return direct

        visited = {int(failed_node)}
        queue: deque[int] = deque([int(failed_node)])
        while queue:
            current = queue.popleft()
            frontier: List[int] = []
            for neighbor in self.neighbors(current):
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                if neighbor in failed:
                    queue.append(neighbor)
                else:
                    frontier.append(neighbor)
            if frontier:
                return sorted(frontier)
        return []

    def redundancy_proof(self) -> Dict[str, Any]:
        return {
            "nodes": self.num_nodes,
            "d_nodes": 20,
            "i_nodes": 12,
            "d_degree": 3,
            "i_degree": 5,
            "total_degree": self.total_degree,
            "redundancy_factor": self.redundancy_factor,
            "min_required_redundancy_factor": 3.0,
            "max_phase1_failures": MAX_AUTONOMIC_FAILURES,
            "verified": bool(self.redundancy_factor >= 3.0),
            "automorphism_group_size": self.automorphism_group_size,
            "automorphism_verified": bool(self.automorphism_group_size == 120),
            "bipartite": bool(
                np.sum(self.adjacency[:20, :20]) == 0
                and np.sum(self.adjacency[20:, 20:]) == 0
            ),
        }

    def get_redundancy_proof(self) -> Dict[str, Any]:
        """Compatibility alias for the original delivery-summary API."""

        return self.redundancy_proof()

    @staticmethod
    def _validate_node_id(node_id: int) -> None:
        if not 0 <= int(node_id) < NUM_NODES:
            raise ValueError(f"node_id must be in [0, {NUM_NODES - 1}]")


@dataclass
class ReducedDensityMatrix:
    """Positive-semidefinite, trace-one 32x32 density state."""

    rho: np.ndarray = field(
        default_factory=lambda: np.eye(NUM_NODES, dtype=np.complex128) / NUM_NODES
    )
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        self.rho = self._project_density(self.rho)

    @staticmethod
    def _project_density(matrix: np.ndarray) -> np.ndarray:
        values = np.asarray(matrix, dtype=np.complex128)
        if values.shape != (NUM_NODES, NUM_NODES):
            raise ValueError(f"rho must have shape ({NUM_NODES}, {NUM_NODES})")
        hermitian = (values + values.conj().T) / 2.0
        eigenvalues, eigenvectors = np.linalg.eigh(hermitian)
        eigenvalues = np.clip(eigenvalues.real, 0.0, None)
        total = float(np.sum(np.abs(eigenvalues)))
        if total <= EPSILON or not math.isfinite(total):
            return np.eye(NUM_NODES, dtype=np.complex128) / NUM_NODES
        # Guard total against near-zero to prevent division by zero
        total_safe = max(total, 1e-300)
        # Spectral floor enforcement and eigenvector normalization for numerical stability
        eigenvalues_safe = np.where(np.isfinite(eigenvalues), eigenvalues, 0.0)
        eigenvalues_safe = np.maximum(eigenvalues_safe, 0.0)
        eigvecs_norm = np.linalg.norm(eigenvectors, axis=0, keepdims=True)
        eigenvectors = eigenvectors / (eigvecs_norm + 1e-300)
        # Use more stable matrix multiplication with error suppression
        with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
            projected = (
                eigenvectors
                @ np.diag(eigenvalues_safe / total_safe)
                @ eigenvectors.conj().T
            )
        return (projected + projected.conj().T) / 2.0

    def diagonal(self) -> np.ndarray:
        return np.real(np.diag(self.rho)).astype(np.float64)

    def set_amplitudes(self, amplitudes: Sequence[float]) -> None:
        values = np.asarray(amplitudes, dtype=np.float64)
        if values.shape != (NUM_NODES,):
            raise ValueError(f"amplitudes must have shape ({NUM_NODES},)")
        if not np.all(np.isfinite(values)):
            raise ValueError("amplitudes must be finite")
        if np.any(values < -EPSILON):
            raise ValueError("amplitudes must be non-negative")
        values = np.clip(values, 0.0, None)
        total = float(np.sum(values))
        if total <= EPSILON:
            raise ValueError("at least one amplitude must be positive")
        probabilities = values / total
        # Preserve the manifold as a pure search state: amplitudes are the
        # diagonal probabilities, while off-diagonal terms retain coherence.
        psi = np.sqrt(probabilities).astype(np.complex128)
        self.rho = np.outer(psi, psi.conj())
        self.timestamp = time.time()

    def trace(self) -> float:
        return float(np.trace(self.rho).real)

    def purity(self) -> float:
        return float(np.trace(self.rho @ self.rho).real)

    def coherence(self, left: int, right: int) -> float:
        return float(abs(self.rho[int(left), int(right)]))

    def assert_invariants(self) -> None:
        if not np.allclose(self.rho, self.rho.conj().T, atol=1e-10):
            raise AssertionError("rho must be Hermitian")
        if not math.isclose(self.trace(), 1.0, rel_tol=0.0, abs_tol=1e-10):
            raise AssertionError("rho must have trace one")
        if float(np.min(np.linalg.eigvalsh(self.rho).real)) < -1e-10:
            raise AssertionError("rho must be positive semidefinite")


@dataclass(frozen=True)
class RebalanceEvent:
    timestamp: float
    failed_nodes: List[int]
    redistribution: Dict[int, Dict[int, float]]
    lattice_commands: List[Dict[str, Any]]
    coverage_maintained: bool
    rho_trace: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ThermalNodeState:
    node_id: int
    thermal_entropy: float
    zone: str
    fade_factor: float
    amplitude_before: float
    amplitude_after: float
    redistributed_amplitude: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ThermalGovernanceEvent:
    timestamp: float
    node_states: List[ThermalNodeState]
    sacrificed_nodes: List[int]
    faded_nodes: List[int]
    redistributed_amplitude: float
    rho_trace: float
    rho_purity: float
    amplitudes: List[float]

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["node_states"] = [state.to_dict() for state in self.node_states]
        return payload


class ThermalGovernor:
    """Continuous thermal fade governor for the PULVINI density state.

    Thermal entropy is interpreted as a normalized hardware pressure in [0, 1].
    Values below warning retain full amplitude, warning values fade linearly,
    critical values fade exponentially, and sacrifice values are reduced to zero
    so the geometric rebalancer can silently repartition their lattice.
    """

    STABLE_ZONE = "stable"
    WARNING_ZONE = "warning"
    CRITICAL_ZONE = "critical"
    SACRIFICE_ZONE = "sacrifice"

    def __init__(
        self,
        *,
        warning_temp: float = 0.70,
        critical_temp: float = 0.95,
        critical_fade_start: float = 0.85,
    ) -> None:
        if not 0.0 <= warning_temp < critical_fade_start < critical_temp <= 1.0:
            raise ValueError(
                "thermal thresholds must satisfy 0 <= warning < critical_fade_start < critical <= 1"
            )
        self.warning_temp = float(warning_temp)
        self.critical_fade_start = float(critical_fade_start)
        self.critical_temp = float(critical_temp)

    def thermal_zone(self, thermal_entropy: float) -> str:
        st = self._normalized_entropy(thermal_entropy)
        if st < self.warning_temp:
            return self.STABLE_ZONE
        if st < self.critical_fade_start:
            return self.WARNING_ZONE
        if st < self.critical_temp:
            return self.CRITICAL_ZONE
        return self.SACRIFICE_ZONE

    def calculate_fade_factor(self, thermal_entropy: float) -> float:
        st = self._normalized_entropy(thermal_entropy)
        if st < self.warning_temp:
            return 1.0
        if st < self.critical_fade_start:
            width = self.critical_fade_start - self.warning_temp
            return float(max(0.0, 1.0 - ((st - self.warning_temp) / width)))
        if st < self.critical_temp:
            return float(math.exp(-10.0 * (st - self.critical_fade_start)))
        return 0.0

    def apply_thermal_governance(
        self,
        rho: ReducedDensityMatrix | np.ndarray,
        telemetry: Sequence[NodeTelemetry] | Mapping[int, NodeTelemetry],
    ) -> Tuple[np.ndarray, ThermalGovernanceEvent]:
        matrix = (
            rho.rho
            if isinstance(rho, ReducedDensityMatrix)
            else np.asarray(rho, dtype=np.complex128)
        )
        if matrix.shape != (NUM_NODES, NUM_NODES):
            raise ValueError(f"rho must have shape ({NUM_NODES}, {NUM_NODES})")
        ordered = self._ordered_telemetry(telemetry)
        before = np.real(np.diag(matrix)).astype(np.float64)
        total_before = float(np.sum(before))
        if total_before <= EPSILON:
            before = np.ones(NUM_NODES, dtype=np.float64) / NUM_NODES
        else:
            before = np.clip(before, 0.0, None) / total_before

        after = before.copy()
        node_states: List[ThermalNodeState] = []
        sacrificed: List[int] = []
        faded: List[int] = []
        lost_by_node = np.zeros(NUM_NODES, dtype=np.float64)

        for node_id, item in enumerate(ordered):
            fade = self.calculate_fade_factor(item.thermal_entropy)
            zone = self.thermal_zone(item.thermal_entropy)
            original = float(after[node_id])
            after[node_id] = original * fade
            lost = max(0.0, original - float(after[node_id]))
            lost_by_node[node_id] = lost
            if zone == self.SACRIFICE_ZONE:
                sacrificed.append(node_id)
            elif lost > EPSILON:
                faded.append(node_id)
            node_states.append(
                ThermalNodeState(
                    node_id=node_id,
                    thermal_entropy=self._normalized_entropy(item.thermal_entropy),
                    zone=zone,
                    fade_factor=fade,
                    amplitude_before=original,
                    amplitude_after=float(after[node_id]),
                    redistributed_amplitude=lost,
                )
            )

        redistributed = float(np.sum(lost_by_node))
        if redistributed > EPSILON:
            after = self.redistribute_to_coolest(after, ordered, redistributed)

        after = self._normalize_amplitudes(after)
        evolved = self.reconstruct_rho(matrix, after)
        event = ThermalGovernanceEvent(
            timestamp=time.time(),
            node_states=node_states,
            sacrificed_nodes=sacrificed,
            faded_nodes=faded,
            redistributed_amplitude=redistributed,
            rho_trace=float(np.trace(evolved).real),
            rho_purity=float(np.trace(evolved @ evolved).real),
            amplitudes=after.tolist(),
        )
        return evolved, event

    def redistribute_to_coolest(
        self, amplitudes: np.ndarray, telemetry: Sequence[NodeTelemetry], amount: float
    ) -> np.ndarray:
        weights = np.zeros(NUM_NODES, dtype=np.float64)
        for item in telemetry:
            node_id = int(item.node_id)
            st = self._normalized_entropy(item.thermal_entropy)
            if st < self.warning_temp:
                weights[node_id] = 1.0 / max(st + 0.1, EPSILON)
        total = float(np.sum(weights))
        if total <= EPSILON:
            weights = np.ones(NUM_NODES, dtype=np.float64) / NUM_NODES
        else:
            weights /= total
        return np.asarray(amplitudes, dtype=np.float64) + weights * float(amount)

    def reconstruct_rho(
        self, reference_rho: np.ndarray, amplitudes: Sequence[float]
    ) -> np.ndarray:
        values = self._normalize_amplitudes(np.asarray(amplitudes, dtype=np.float64))
        phases = self._phases_from_reference(reference_rho)
        psi = np.sqrt(values).astype(np.complex128) * np.exp(1j * phases)
        norm = float(np.linalg.norm(psi))
        if norm <= EPSILON or not math.isfinite(norm):
            psi = np.ones(NUM_NODES, dtype=np.complex128) / math.sqrt(NUM_NODES)
        else:
            psi = psi / norm
        rho = np.outer(psi, psi.conj())
        return (rho + rho.conj().T) / 2.0

    @staticmethod
    def _normalized_entropy(value: float) -> float:
        parsed = float(value)
        if not math.isfinite(parsed) or parsed < 0.0:
            raise ValueError("thermal_entropy must be finite and non-negative")
        if parsed <= 1.0:
            return parsed
        # Backwards-compatible hardware mode: legacy telemetry may report watts.
        # Treat 1kW/node as the normalized breakdown envelope.
        return min(parsed / 1_000.0, 1.0)

    @staticmethod
    def _normalize_amplitudes(amplitudes: np.ndarray) -> np.ndarray:
        values = np.asarray(amplitudes, dtype=np.float64)
        if values.shape != (NUM_NODES,):
            raise ValueError(f"amplitudes must have shape ({NUM_NODES},)")
        values = np.clip(values, 0.0, None)
        total = float(np.sum(values))
        if total <= EPSILON or not math.isfinite(total):
            return np.ones(NUM_NODES, dtype=np.float64) / NUM_NODES
        return values / total

    @staticmethod
    def _ordered_telemetry(
        telemetry: Sequence[NodeTelemetry] | Mapping[int, NodeTelemetry],
    ) -> List[NodeTelemetry]:
        if isinstance(telemetry, Mapping):
            ordered = [telemetry[node_id] for node_id in range(NUM_NODES)]
        else:
            by_node = {int(item.node_id): item for item in telemetry}
            ordered = [by_node[node_id] for node_id in range(NUM_NODES)]
        if len(ordered) != NUM_NODES:
            raise ValueError(
                f"thermal governance requires telemetry for {NUM_NODES} nodes"
            )
        return ordered

    @staticmethod
    def _phases_from_reference(reference_rho: np.ndarray) -> np.ndarray:
        phases = np.zeros(NUM_NODES, dtype=np.float64)
        diagonal = np.real(np.diag(reference_rho))
        anchor = int(np.argmax(diagonal)) if diagonal.size else 0
        for node_id in range(NUM_NODES):
            value = reference_rho[node_id, anchor]
            phases[node_id] = float(np.angle(value)) if abs(value) > EPSILON else 0.0
        return phases


class ManifoldHomeostasis:
    """Telemetry monitor and health ledger for the autonomic density state."""

    def __init__(
        self,
        compound: DodecahedronIcosahedronCompound,
        *,
        decoherence_threshold: float = DEFAULT_DECOHERENCE_THRESHOLD,
        audit_sink: Optional[AuditSink] = None,
    ) -> None:
        if not 0.0 <= decoherence_threshold <= 1.0:
            raise ValueError("decoherence_threshold must be in [0, 1]")
        self.compound = compound
        self.threshold = float(decoherence_threshold)
        self.audit_sink = audit_sink
        self.rho = ReducedDensityMatrix()
        self.telemetry: Dict[int, NodeTelemetry] = {}
        self.coherence_history: List[Tuple[float, Dict[int, float]]] = []
        self.failure_log: List[Dict[str, Any]] = []
        self._lock = RLock()

    def update_telemetry(self, node_id: int, telemetry: NodeTelemetry) -> None:
        if int(node_id) != int(telemetry.node_id):
            raise ValueError("node_id must match telemetry.node_id")
        self.compound._validate_node_id(node_id)
        with self._lock:
            self.telemetry[int(node_id)] = telemetry

    def bulk_update(self, telemetry: Iterable[NodeTelemetry]) -> None:
        for item in telemetry:
            self.update_telemetry(item.node_id, item)

    def health_matrix(self) -> Dict[int, float]:
        with self._lock:
            return {
                node_id: item.coherence_score()
                for node_id, item in self.telemetry.items()
            }

    def live_nodes(self) -> Set[int]:
        health = self.health_matrix()
        return {
            node_id
            for node_id in range(NUM_NODES)
            if health.get(node_id, 1.0) >= self.threshold
        }

    def monitor_heartbeat(self) -> List[int]:
        health = self.health_matrix()
        critical = sorted(
            node_id for node_id, score in health.items() if score < self.threshold
        )
        with self._lock:
            self.coherence_history.append((time.time(), health))
            if len(self.coherence_history) > 512:
                del self.coherence_history[: len(self.coherence_history) - 512]
        if critical:
            self._audit(
                {
                    "event_type": "autonomic_critical_nodes_detected",
                    "critical_nodes": critical,
                    "health": health,
                }
            )
        return critical

    def log_failure(
        self, node_id: int, reason: str, cascade: Sequence[int]
    ) -> Dict[str, Any]:
        event = {
            "timestamp": time.time(),
            "event_type": "autonomic_node_failure",
            "node_id": int(node_id),
            "reason": reason,
            "secondary_at_risk": list(cascade),
            "rho_purity": self.rho.purity(),
            "avg_coherence": (
                float(np.mean(list(self.health_matrix().values())))
                if self.telemetry
                else 1.0
            ),
        }
        with self._lock:
            self.failure_log.append(event)
            if len(self.failure_log) > 512:
                del self.failure_log[: len(self.failure_log) - 512]
        self._audit(event)
        return event

    def detect_failure_cascade(self, node_id: int) -> List[int]:
        at_risk = []
        health = self.health_matrix()
        for neighbor in self.compound.neighbors(node_id):
            if (
                health.get(neighbor, 1.0) < 0.3
                and self.rho.coherence(node_id, neighbor) > 0.5
            ):
                at_risk.append(neighbor)
        return sorted(at_risk)

    def _audit(self, event: Mapping[str, Any]) -> None:
        if self.audit_sink is not None:
            self.audit_sink(event)


class GeometricRebalancer:
    """Redistribute failed node amplitude and nonce slices to live D/I neighbors."""

    def __init__(
        self,
        compound: DodecahedronIcosahedronCompound,
        homeostasis: ManifoldHomeostasis,
        *,
        lattice_repoint_sink: Optional[LatticeRepointSink] = None,
    ) -> None:
        self.compound = compound
        self.homeostasis = homeostasis
        self.lattice_repoint_sink = lattice_repoint_sink
        self.rebalance_log: List[RebalanceEvent] = []
        self._lock = RLock()

    def redistribution_for(
        self, failed_node: int, failed_nodes: Iterable[int] = ()
    ) -> Dict[int, float]:
        candidates = self.compound.healing_candidates(failed_node, failed_nodes)
        if not candidates:
            return {}
        fraction = 1.0 / float(len(candidates))
        return {candidate: fraction for candidate in candidates}

    def rebalance_lattice_topology(
        self, failed_nodes: int | Iterable[int], *, reason: str = "decoherence"
    ) -> RebalanceEvent:
        failed = self._normalize_failed_nodes(failed_nodes)
        old_amplitudes = self.homeostasis.rho.diagonal()
        new_amplitudes = old_amplitudes.copy()
        redistribution: Dict[int, Dict[int, float]] = {}
        commands: List[Dict[str, Any]] = []

        for node_id in failed:
            cascade = self.homeostasis.detect_failure_cascade(node_id)
            self.homeostasis.log_failure(node_id, reason, cascade)
            transfer = self.redistribution_for(node_id, failed)
            redistribution[node_id] = transfer
            failed_amplitude = new_amplitudes[node_id]
            new_amplitudes[node_id] = 0.0
            nonce_partitions = self._partition_nonce_range(
                self.compound.nonce_range(node_id), len(transfer)
            )
            for partition_index, (neighbor, fraction) in enumerate(transfer.items()):
                new_amplitudes[neighbor] += failed_amplitude * fraction
                command = {
                    "command": "lattice_repoint",
                    "failed_node": node_id,
                    "recipient_node": neighbor,
                    "fraction": fraction,
                    "nonce_range": nonce_partitions[partition_index],
                    "source_nonce_range": self.compound.nonce_range(node_id),
                    "partition_index": partition_index,
                    "partition_count": len(transfer),
                    "node_type": self.compound.node_type(node_id).value,
                }
                commands.append(command)
                if self.lattice_repoint_sink is not None:
                    self.lattice_repoint_sink(command)

        self.homeostasis.rho.set_amplitudes(new_amplitudes)
        event = RebalanceEvent(
            timestamp=time.time(),
            failed_nodes=failed,
            redistribution=redistribution,
            lattice_commands=commands,
            coverage_maintained=self.verify_coverage(failed),
            rho_trace=self.homeostasis.rho.trace(),
        )
        with self._lock:
            self.rebalance_log.append(event)
            if len(self.rebalance_log) > 512:
                del self.rebalance_log[: len(self.rebalance_log) - 512]
        return event

    @staticmethod
    def _partition_nonce_range(
        nonce_range: Tuple[int, int], partitions: int
    ) -> List[Tuple[int, int]]:
        if partitions <= 0:
            return []
        start, end = int(nonce_range[0]), int(nonce_range[1])
        if end < start:
            raise ValueError("nonce_range end must be greater than or equal to start")
        width = end - start + 1
        base = width // partitions
        remainder = width % partitions
        ranges: List[Tuple[int, int]] = []
        cursor = start
        for index in range(partitions):
            size = base + (1 if index < remainder else 0)
            part_end = cursor + size - 1
            ranges.append((cursor, part_end))
            cursor = part_end + 1
        return ranges

    def verify_coverage(self, failed_nodes: Iterable[int] = ()) -> bool:
        amplitudes = self.homeostasis.rho.diagonal()
        failed = {int(node) for node in failed_nodes}
        if not math.isclose(float(np.sum(amplitudes)), 1.0, rel_tol=0.0, abs_tol=1e-10):
            return False
        if any(amplitudes[node] > 1e-12 for node in failed):
            return False
        return bool(np.all(amplitudes >= -1e-12))

    @staticmethod
    def _normalize_failed_nodes(failed_nodes: int | Iterable[int]) -> List[int]:
        if isinstance(failed_nodes, int):
            failed = [failed_nodes]
        else:
            failed = sorted({int(node) for node in failed_nodes})
        if not failed:
            raise ValueError("at least one failed node is required")
        for node in failed:
            DodecahedronIcosahedronCompound._validate_node_id(node)
        return failed


class BuresOptimizer:
    """Bures/Hellinger natural routing over diagonal density amplitudes."""

    def __init__(
        self,
        compound: DodecahedronIcosahedronCompound,
        homeostasis: ManifoldHomeostasis,
    ) -> None:
        self.compound = compound
        self.homeostasis = homeostasis
        self.optimization_log: List[Dict[str, Any]] = []

    def efficiency_manifold(
        self, *, include_critical: bool = False
    ) -> Dict[int, float]:
        health = self.homeostasis.health_matrix()
        raw: Dict[int, float] = {}
        governor = ThermalGovernor()
        for node_id, telemetry in self.homeostasis.telemetry.items():
            thermal_fade = governor.calculate_fade_factor(telemetry.thermal_entropy)
            if (
                not include_critical
                and health.get(node_id, 1.0) < self.homeostasis.threshold
            ) or thermal_fade <= EPSILON:
                raw[node_id] = 0.0
                continue
            denominator = max(float(telemetry.thermal_entropy), EPSILON)
            raw[node_id] = (
                max(float(telemetry.hash_rate), 0.0) / denominator
            ) * thermal_fade
        maximum = max(raw.values(), default=0.0)
        if maximum <= EPSILON:
            return {node_id: 0.0 for node_id in raw}
        return {node_id: value / maximum for node_id, value in raw.items()}

    def target_distribution(self) -> np.ndarray:
        efficiencies = self.efficiency_manifold()
        target = np.zeros(NUM_NODES, dtype=np.float64)
        for node_id, value in efficiencies.items():
            target[node_id] = max(float(value), 0.0)
        total = float(np.sum(target))
        if total <= EPSILON:
            live = sorted(self.homeostasis.live_nodes())
            if not live:
                return np.ones(NUM_NODES, dtype=np.float64) / NUM_NODES
            target[live] = 1.0 / len(live)
            return target
        return target / total

    def find_bures_optima(self, *, learning_rate: float = 0.01) -> np.ndarray:
        """Step along the diagonal Bures geodesic toward efficient nodes."""

        if not 0.0 <= learning_rate <= 1.0:
            raise ValueError("learning_rate must be in [0, 1]")
        current = self.homeostasis.rho.diagonal()
        current = current / max(float(np.sum(current)), EPSILON)
        target = self.target_distribution()
        sqrt_step = (1.0 - learning_rate) * np.sqrt(current) + learning_rate * np.sqrt(
            target
        )
        stepped = np.square(sqrt_step)
        total = float(np.sum(stepped))
        if total <= EPSILON:
            return np.ones(NUM_NODES, dtype=np.float64) / NUM_NODES
        return stepped / total

    def optimize_energy_envelope(
        self, target_watts: float, *, learning_rate: float = 0.05
    ) -> Dict[str, Any]:
        if target_watts < 0 or not math.isfinite(float(target_watts)):
            raise ValueError("target_watts must be finite and non-negative")
        total_thermal = float(
            sum(item.thermal_entropy for item in self.homeostasis.telemetry.values())
        )
        if total_thermal <= float(target_watts):
            event = {
                "timestamp": time.time(),
                "action": "no_action",
                "current_watts": total_thermal,
                "target_watts": float(target_watts),
            }
            self.optimization_log.append(event)
            return event
        new_amplitudes = self.find_bures_optima(learning_rate=learning_rate)
        self.homeostasis.rho.set_amplitudes(new_amplitudes)
        event = {
            "timestamp": time.time(),
            "action": "energy_constraint_triggered",
            "current_watts": total_thermal,
            "target_watts": float(target_watts),
            "overage": total_thermal - float(target_watts),
            "new_amplitudes": new_amplitudes.tolist(),
        }
        self.optimization_log.append(event)
        return event


class PulviniAutonomicsEngine:
    """Production facade for the standalone autonomic feedback loops."""

    def __init__(
        self,
        *,
        decoherence_threshold: float = DEFAULT_DECOHERENCE_THRESHOLD,
        audit_sink: Optional[AuditSink] = None,
        lattice_repoint_sink: Optional[LatticeRepointSink] = None,
    ) -> None:
        self.compound = DodecahedronIcosahedronCompound()
        self.homeostasis = ManifoldHomeostasis(
            self.compound,
            decoherence_threshold=decoherence_threshold,
            audit_sink=audit_sink,
        )
        self.rebalancer = GeometricRebalancer(
            self.compound,
            self.homeostasis,
            lattice_repoint_sink=lattice_repoint_sink,
        )
        self.optimizer = BuresOptimizer(self.compound, self.homeostasis)
        self.thermal_governor = ThermalGovernor()
        self.thermal_log: List[Dict[str, Any]] = []
        self.sacrificed_nodes: Set[int] = set()

    def ingest_telemetry(
        self, telemetry: NodeTelemetry | Iterable[NodeTelemetry]
    ) -> None:
        if isinstance(telemetry, NodeTelemetry):
            self.homeostasis.update_telemetry(telemetry.node_id, telemetry)
        else:
            self.homeostasis.bulk_update(telemetry)

    def heartbeat_and_heal(
        self, *, reason: str = "decoherence"
    ) -> Optional[RebalanceEvent]:
        critical = self.homeostasis.monitor_heartbeat()
        if not critical:
            return None
        return self.rebalancer.rebalance_lattice_topology(critical, reason=reason)

    def thermal_tick(
        self, telemetry: Optional[Iterable[NodeTelemetry]] = None
    ) -> Tuple[ThermalGovernanceEvent, Optional[RebalanceEvent]]:
        if telemetry is not None:
            self.ingest_telemetry(telemetry)
        if len(self.homeostasis.telemetry) != NUM_NODES:
            raise ValueError(
                f"thermal_tick requires telemetry for all {NUM_NODES} nodes"
            )
        evolved_rho, event = self.thermal_governor.apply_thermal_governance(
            self.homeostasis.rho.rho,
            self.homeostasis.telemetry,
        )
        self.homeostasis.rho = ReducedDensityMatrix(evolved_rho)
        event_payload = event.to_dict()
        self.thermal_log.append(event_payload)
        if len(self.thermal_log) > 512:
            del self.thermal_log[: len(self.thermal_log) - 512]
        newly_sacrificed = [
            node_id
            for node_id in event.sacrificed_nodes
            if node_id not in self.sacrificed_nodes
        ]
        rebalance = None
        if newly_sacrificed:
            self.sacrificed_nodes.update(newly_sacrificed)
            rebalance = self.rebalancer.rebalance_lattice_topology(
                newly_sacrificed, reason="thermal_sacrifice"
            )
        return event, rebalance

    def snapshot(self) -> Dict[str, Any]:
        self.homeostasis.rho.assert_invariants()
        return {
            "status": "ok",
            "topology": self.compound.redundancy_proof(),
            "health": self.homeostasis.health_matrix(),
            "rho": {
                "trace": self.homeostasis.rho.trace(),
                "purity": self.homeostasis.rho.purity(),
                "diagonal": self.homeostasis.rho.diagonal().tolist(),
            },
            "failures": list(self.homeostasis.failure_log),
            "rebalances": [event.to_dict() for event in self.rebalancer.rebalance_log],
            "optimizations": list(self.optimizer.optimization_log),
            "thermal": list(self.thermal_log),
            "sacrificed_nodes": sorted(self.sacrificed_nodes),
        }


class AutonomicOrchestrator:
    """Bridge thermal governance to geometric healing for the live engine."""

    def __init__(self, engine: PulviniAutonomicsEngine) -> None:
        self.engine = engine

    @property
    def sacrificed_set(self) -> Set[int]:
        return self.engine.sacrificed_nodes

    def tick(
        self, telemetry: Iterable[NodeTelemetry]
    ) -> Tuple[ThermalGovernanceEvent, Optional[RebalanceEvent]]:
        return self.engine.thermal_tick(telemetry)

    def initiate_silent_healing(self, node_id: int) -> RebalanceEvent:
        if int(node_id) in self.engine.sacrificed_nodes:
            existing = self.engine.rebalancer.rebalance_log[-1:]
            if existing and int(node_id) in existing[0].failed_nodes:
                return existing[0]
        self.engine.sacrificed_nodes.add(int(node_id))
        return self.engine.rebalancer.rebalance_lattice_topology(
            int(node_id), reason="orchestrator_silent_healing"
        )

    def get_manifold_purity(self) -> float:
        return self.engine.homeostasis.rho.purity()


__all__ = [
    "AutonomicOrchestrator",
    "BuresOptimizer",
    "DEFAULT_DECOHERENCE_THRESHOLD",
    "DodecahedronIcosahedronCompound",
    "GeometricRebalancer",
    "ManifoldHomeostasis",
    "MAX_AUTONOMIC_FAILURES",
    "NodeTelemetry",
    "NodeType",
    "PulviniAutonomicsEngine",
    "RebalanceEvent",
    "ReducedDensityMatrix",
    "ThermalGovernanceEvent",
    "ThermalGovernor",
    "ThermalNodeState",
]
