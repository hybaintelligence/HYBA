"""PULVINI overlay: one pool-facing worker, 32-node mathematical manifold."""

from __future__ import annotations

import math
import time
from collections import deque
from dataclasses import asdict, dataclass, field
from threading import RLock
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from .pulvini_manifold import PulviniManifold
from .pulvini_nonce_compression import PulviniNonceSpaceCompressor

from .pulvini_topology import ADJACENCY_MAP, MAX_UINT32_NONCE, NONCE_BITS, NUM_NODES, SLICE_SIZE

if TYPE_CHECKING:
    from .pulvini_autonomics import NodeTelemetry

def get_geometric_neighbors(node_id: int) -> List[int]:
    if node_id not in ADJACENCY_MAP:
        raise ValueError(f"unknown PULVINI node_id: {node_id}")
    payload = ADJACENCY_MAP[node_id]
    return list(payload.get("d", [])) + list(payload.get("i", []))


def nonce_slice(node_id: int) -> Tuple[int, int]:
    if not 0 <= node_id < NUM_NODES:
        raise ValueError(f"node_id must be in [0, {NUM_NODES - 1}]")
    start = node_id * SLICE_SIZE
    return start, start + SLICE_SIZE


def nonce_range_inclusive(node_id: int) -> Tuple[int, int]:
    start, end = nonce_slice(node_id)
    return start, end - 1


def verify_symmetry() -> bool:
    for node_id in range(NUM_NODES):
        for neighbor in get_geometric_neighbors(node_id):
            if node_id not in get_geometric_neighbors(neighbor):
                return False
    return True


def bfs_distances(start: int) -> Dict[int, int]:
    distances = {start: 0}
    queue: deque[int] = deque([start])
    while queue:
        node_id = queue.popleft()
        for neighbor in get_geometric_neighbors(node_id):
            if neighbor not in distances:
                distances[neighbor] = distances[node_id] + 1
                queue.append(neighbor)
    return distances


def graph_diameter() -> int:
    return max(max(bfs_distances(node_id).values()) for node_id in range(NUM_NODES))


@dataclass
class NeuralLink:
    target_id: int
    weight: float = 1.0
    _history: deque[float] = field(default_factory=lambda: deque(maxlen=10), repr=False)

    def record_trip(self, trip_seconds: float) -> None:
        self._history.append(max(float(trip_seconds), 0.0))
        avg = sum(self._history) / len(self._history)
        self.weight = 1.0 / (avg + 1e-9)

    def average_trip_seconds(self) -> Optional[float]:
        if not self._history:
            return None
        return sum(self._history) / len(self._history)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_id": self.target_id,
            "weight": self.weight,
            "samples": len(self._history),
            "average_trip_seconds": self.average_trip_seconds(),
        }


@dataclass
class NodeAssignment:
    node_id: int
    job_id: str
    nonce_start: int
    nonce_end: int
    extranonce2: str
    role: str
    neighbors: List[int]
    tensor_coordinate: Dict[str, Any]
    compressed_coordinate: Dict[str, Any]
    healing_ranges: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class NodeRuntimeState:
    node_id: int
    role: str
    phase: str = "idle"
    active_job_id: Optional[str] = None
    nonce_start: Optional[int] = None
    nonce_end: Optional[int] = None
    current_nonce: Optional[int] = None
    hashes: int = 0
    best_diff: int = 0
    shares_found: int = 0
    shares_submitted: int = 0
    shares_accepted: int = 0
    shares_rejected: int = 0
    last_update: float = field(default_factory=time.time)
    best_neighbor: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class GlobalMiningState:
    """Thread-safe shared state surface for the 32-node overlay."""

    def __init__(self) -> None:
        self._lock = RLock()
        self.current_job_id: Optional[str] = None
        self.target: Optional[int] = None
        self.best_diff_observed = 0
        self.total_hashes = 0
        self.node_progress: Dict[int, int] = {node_id: 0 for node_id in range(NUM_NODES)}

    def activate_job(self, job_id: str, target: int) -> None:
        with self._lock:
            self.current_job_id = job_id
            self.target = int(target)
            self.node_progress = {node_id: 0 for node_id in range(NUM_NODES)}

    def update_best_diff(self, candidate: int) -> bool:
        with self._lock:
            if int(candidate) > self.best_diff_observed:
                self.best_diff_observed = int(candidate)
                return True
            return False

    def increment_hashes(self, count: int) -> None:
        with self._lock:
            self.total_hashes += max(int(count), 0)

    def set_node_progress(self, node_id: int, nonce: int) -> None:
        with self._lock:
            self.node_progress[int(node_id)] = int(nonce)

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "current_job_id": self.current_job_id,
                "target": self.target,
                "best_diff_observed": self.best_diff_observed,
                "total_hashes": self.total_hashes,
                "node_progress": dict(self.node_progress),
            }


class PulviniOverlayConcentrator:
    """Pool-facing singleton backed by the PULVINI mathematical manifold."""

    def __init__(self, worker_name: str = "PULVINI.singularity", manifold: Optional[PulviniManifold] = None) -> None:
        if not verify_symmetry():
            raise RuntimeError("PULVINI adjacency map must be symmetric before production mining starts")
        self.worker_name = worker_name
        self.manifold = manifold or PulviniManifold(ADJACENCY_MAP)
        self.nonce_compressor = PulviniNonceSpaceCompressor(lanes=NUM_NODES, nonce_space_size=1 << NONCE_BITS)
        self.nonce_plan = self.nonce_compressor.build_plan()
        self.state = GlobalMiningState()
        self.job_epoch = 0
        self.active_job_id: Optional[str] = None
        self.active_pool_name: Optional[str] = None
        self.assignments: Dict[int, NodeAssignment] = {}
        self.nodes = {
            node_id: NodeRuntimeState(node_id=node_id, role="hub" if node_id >= 20 else "worker")
            for node_id in range(NUM_NODES)
        }
        self.links = {
            node_id: {neighbor: NeuralLink(neighbor) for neighbor in get_geometric_neighbors(node_id)}
            for node_id in range(NUM_NODES)
        }
        self.lifecycle: List[Dict[str, Any]] = []
        self.share_ledger: List[Dict[str, Any]] = []
        self.healing_routes: List[Dict[str, Any]] = []
        self.autonomic_ledger: List[Dict[str, Any]] = []
        self._lock = RLock()

    @property
    def topology_report(self) -> Dict[str, Any]:
        return {
            "nodes": NUM_NODES,
            "worker_nodes": list(range(0, 20)),
            "hub_nodes": list(range(20, 32)),
            "diameter_hops": graph_diameter(),
            "symmetric": verify_symmetry(),
            "nonce_slice_size": SLICE_SIZE,
            "nonce_space": 1 << NONCE_BITS,
            "pool_identity": self.worker_name,
            "pool_visible_workers": 1,
            "internal_workers": NUM_NODES,
            "automorphism_order": len(self.manifold.automorphisms),
            "node_orbits": [list(orbit) for orbit in self.manifold.node_orbits],
            "nonce_working_set_dimension": self.nonce_plan.working_set_dimension,
            "nonce_working_set_compression_ratio": self.nonce_plan.working_set_compression_ratio,
            "nonce_complete_coverage": self.nonce_plan.complete_coverage,
        }

    def _append_event(self, phase: str, **payload: Any) -> None:
        self.lifecycle.append({"phase": phase, "timestamp": time.time(), **payload})
        if len(self.lifecycle) > 256:
            del self.lifecycle[: len(self.lifecycle) - 256]

    def mark_connect_requested(self, request_id: Optional[str] = None) -> None:
        with self._lock:
            self._append_event("connect_requested", request_id=request_id)

    def mark_pool_bound(self, pool_name: str, pool_url: str, stratum_version: int) -> None:
        with self._lock:
            self.active_pool_name = pool_name
            self._append_event("pool_bound", pool_name=pool_name, pool_url=pool_url, stratum_version=stratum_version)
            self._append_event("subscribed_authorized", pool_name=pool_name)
            self._append_event("awaiting_job", pool_name=pool_name)

    def _extranonce2_for_node(self, node_id: int, job_id: str, extranonce2_size: int) -> str:
        return self.manifold.manifold_drift_extranonce2(node_id, job_id, extranonce2_size)

    def register_pool_job(self, job: Any, pool_name: Optional[str] = None) -> Dict[int, NodeAssignment]:
        with self._lock:
            if self.active_job_id == job.job_id and self.assignments:
                return dict(self.assignments)
            self.job_epoch += 1
            self.active_job_id = str(job.job_id)
            self.state.activate_job(str(job.job_id), int(job.target))
            self.manifold.begin_job(str(job.job_id), int(job.target))
            self.nonce_plan = self.nonce_compressor.build_plan()
            self.assignments = {}
            for node_id, segment in enumerate(self.nonce_plan.coverage_segments):
                coordinate = self.manifold.tensor_coordinate_for_node(node_id)
                compressed_coordinate = self.nonce_plan.coordinate_for_nonce(segment.start)
                assignment = NodeAssignment(
                    node_id=node_id,
                    job_id=str(job.job_id),
                    nonce_start=segment.start,
                    nonce_end=segment.end,
                    extranonce2=self._extranonce2_for_node(node_id, str(job.job_id), getattr(job, "extranonce2_size", 4)),
                    role="hub" if node_id >= 20 else "worker",
                    neighbors=get_geometric_neighbors(node_id),
                    tensor_coordinate=coordinate.to_dict(),
                    compressed_coordinate=compressed_coordinate.to_dict() if compressed_coordinate else {},
                )
                self.assignments[node_id] = assignment
                node = self.nodes[node_id]
                node.phase = "assigned"
                node.active_job_id = str(job.job_id)
                node.nonce_start = segment.start
                node.nonce_end = segment.end
                node.current_nonce = segment.start
                node.last_update = time.time()
                node.best_neighbor = self.best_neighbor(node_id)
            self._append_event("job_received", job_id=str(job.job_id), pool_name=pool_name, epoch=self.job_epoch)
            self._append_event(
                "work_configured",
                job_id=str(job.job_id),
                assignments=NUM_NODES,
                nonce_slice_size=SLICE_SIZE,
                nonce_working_set_dimension=self.nonce_plan.working_set_dimension,
                nonce_complete_coverage=self.nonce_plan.complete_coverage,
            )
            return dict(self.assignments)

    def nonce_ranges(self) -> List[Tuple[int, int]]:
        return [(assignment.nonce_start, assignment.nonce_end) for assignment in self.assignments.values()]

    def compressed_nonce_plan(self) -> Dict[str, Any]:
        return self.nonce_plan.to_dict()

    def tensor_coordinates(self) -> List[Dict[str, Any]]:
        return [coordinate.to_dict() for coordinate in self.manifold.tensor_coordinates()]

    def assignment_for_nonce(self, nonce: int) -> Optional[NodeAssignment]:
        nonce = int(nonce)
        for route in reversed(self.healing_routes):
            start, end = route["nonce_range"]
            if int(start) <= nonce <= int(end):
                recipient = self.assignments.get(int(route["recipient_node"]))
                if recipient is not None:
                    return recipient
        for assignment in self.assignments.values():
            if assignment.nonce_start <= nonce <= assignment.nonce_end:
                return assignment
        return None

    def compressed_coordinate_for_nonce(self, nonce: int) -> Optional[Dict[str, Any]]:
        coordinate = self.nonce_plan.coordinate_for_nonce(nonce)
        return coordinate.to_dict() if coordinate else None

    def record_node_progress(self, node_id: int, nonce: int, hashes: int = 0, best_diff: Optional[int] = None) -> None:
        with self._lock:
            node = self.nodes[node_id]
            node.phase = "searching"
            node.current_nonce = int(nonce)
            node.hashes += max(int(hashes), 0)
            node.last_update = time.time()
            self.state.set_node_progress(node_id, nonce)
            self.state.increment_hashes(hashes)
            if best_diff is not None:
                self.manifold.observe_high_difficulty_hash(node_id, float(best_diff))
                if self.state.update_best_diff(best_diff):
                    node.best_diff = int(best_diff)

    def record_nack(self, node_id: int) -> None:
        assignment = self.assignments[node_id]
        event = self.manifold.nack_slice(node_id, assignment.job_id, assignment.nonce_start, assignment.nonce_end)
        self._append_event("nack_backaction", node_id=node_id, affected_nodes=event.affected_nodes)

    def record_share_candidate(self, node_id: int, nonce: int) -> None:
        with self._lock:
            node = self.nodes[node_id]
            node.phase = "candidate_evaluated"
            node.current_nonce = int(nonce)
            node.shares_found += 1
            node.last_update = time.time()
            self._append_event("candidate_evaluated", node_id=node_id, job_id=self.active_job_id, nonce=int(nonce))

    def record_share_outcome(self, node_id: int, nonce: int, result: Any) -> Dict[str, Any]:
        with self._lock:
            node = self.nodes[node_id]
            node.shares_submitted += 1
            accepted = bool(getattr(result, "accepted", False))
            if accepted:
                node.shares_accepted += 1
                node.phase = "share_accepted"
            else:
                node.shares_rejected += 1
                node.phase = "share_rejected"
            node.last_update = time.time()
            payload = {
                "node_id": node_id,
                "job_id": getattr(result, "job_id", self.active_job_id),
                "nonce": int(nonce),
                "accepted": accepted,
                "error_code": getattr(result, "error_code", None),
                "error_message": getattr(result, "error_message", None),
                "block_hash": getattr(result, "block_hash", None),
                "route": self.route_for_share(node_id),
                "compressed_coordinate": self.compressed_coordinate_for_nonce(nonce),
                "timestamp": time.time(),
            }
            self.share_ledger.append(payload)
            if len(self.share_ledger) > 256:
                del self.share_ledger[: len(self.share_ledger) - 256]
            self._append_event("share_submitted", node_id=node_id, job_id=payload["job_id"], nonce=int(nonce))
            self._append_event("share_outcome_recorded", node_id=node_id, accepted=accepted, error_code=payload["error_code"])
            return payload

    def best_neighbor(self, node_id: int) -> Optional[int]:
        route = self.manifold.gradient_route_to_gateway(node_id)
        return route[1] if len(route) > 1 else None

    def record_autonomic_event(self, event: Dict[str, Any]) -> None:
        with self._lock:
            payload = {"timestamp": time.time(), **dict(event)}
            self.autonomic_ledger.append(payload)
            if len(self.autonomic_ledger) > 256:
                del self.autonomic_ledger[: len(self.autonomic_ledger) - 256]
            self._append_event("autonomic_event", event_type=payload.get("event_type"), node_id=payload.get("node_id"))

    def apply_lattice_repoint(self, command: Dict[str, Any]) -> None:
        with self._lock:
            failed_node = int(command["failed_node"])
            recipient_node = int(command["recipient_node"])
            nonce_start, nonce_end = [int(value) for value in command["nonce_range"]]
            route = {
                "failed_node": failed_node,
                "recipient_node": recipient_node,
                "nonce_range": [nonce_start, nonce_end],
                "source_nonce_range": list(command.get("source_nonce_range", [nonce_start, nonce_end])),
                "partition_index": int(command.get("partition_index", 0)),
                "partition_count": int(command.get("partition_count", 1)),
                "fraction": float(command["fraction"]),
                "timestamp": time.time(),
            }
            route_key = (failed_node, recipient_node, nonce_start, nonce_end)
            self.healing_routes = [
                existing for existing in self.healing_routes
                if (int(existing["failed_node"]), int(existing["recipient_node"]), int(existing["nonce_range"][0]), int(existing["nonce_range"][1])) != route_key
            ]
            self.healing_routes.append(route)
            if len(self.healing_routes) > 512:
                del self.healing_routes[: len(self.healing_routes) - 512]
            if recipient_node in self.assignments:
                assignment = self.assignments[recipient_node]
                assignment.healing_ranges = [
                    existing for existing in assignment.healing_ranges
                    if (int(existing["failed_node"]), int(existing["recipient_node"]), int(existing["nonce_range"][0]), int(existing["nonce_range"][1])) != route_key
                ]
                assignment.healing_ranges.append(route)
            if failed_node in self.nodes:
                self.nodes[failed_node].phase = "autonomic_repointed"
                self.nodes[failed_node].last_update = time.time()
            if recipient_node in self.nodes:
                self.nodes[recipient_node].phase = "autonomic_healing"
                self.nodes[recipient_node].last_update = time.time()
            self._append_event(
                "lattice_repointed",
                failed_node=failed_node,
                recipient_node=recipient_node,
                nonce_range=[nonce_start, nonce_end],
                fraction=float(command["fraction"]),
            )

    def healing_ranges_overlap_free(self) -> bool:
        ranges_by_recipient: Dict[int, List[Tuple[int, int]]] = {}
        for route in self.healing_routes:
            recipient = int(route["recipient_node"])
            ranges_by_recipient.setdefault(recipient, []).append((int(route["nonce_range"][0]), int(route["nonce_range"][1])))
        for recipient, assignment in self.assignments.items():
            ranges_by_recipient.setdefault(recipient, []).append((int(assignment.nonce_start), int(assignment.nonce_end)))
        for ranges in ranges_by_recipient.values():
            ordered = sorted(ranges)
            for left, right in zip(ordered, ordered[1:]):
                if left[1] >= right[0]:
                    return False
        return True

    def record_link_latency(self, source_id: int, target_id: int, trip_seconds: float) -> None:
        if target_id not in self.links.get(source_id, {}):
            raise ValueError(f"nodes {source_id}->{target_id} are not adjacent in PULVINI topology")
        self.links[source_id][target_id].record_trip(trip_seconds)
        reward = 1.0 / (max(float(trip_seconds), 0.0) + 1e-9)
        self.manifold.hebbian_fire([source_id, target_id], signal_type="LATENCY_REWARD", reward=min(reward, 1.0))
        self.nodes[source_id].best_neighbor = self.best_neighbor(source_id)

    def route_for_share(self, node_id: int) -> List[int]:
        best = self.best_neighbor(node_id)
        return [int(node_id)] if best is None else [int(node_id), int(best)]

    def gradient_cancel_order(self) -> List[int]:
        return self.manifold.gradient_broadcast_order()

    def autonomic_telemetry(self, *, power_scale: float = 1.0) -> List["NodeTelemetry"]:
        from .pulvini_autonomics import NodeTelemetry

        with self._lock:
            now = time.time()
            observation = self.manifold.observe()
            probabilities = observation.probabilities
            phases = observation.phases
            telemetry: List[NodeTelemetry] = []
            for node_id, node in self.nodes.items():
                sampled_latencies = [
                    link.average_trip_seconds()
                    for link in self.links.get(node_id, {}).values()
                    if link.average_trip_seconds() is not None
                ]
                if sampled_latencies:
                    tres = 1_000.0 * (sum(sampled_latencies) / len(sampled_latencies))
                elif self.active_job_id and node.phase not in {"idle", "assigned"}:
                    tres = min(10_000.0, max(0.0, now - node.last_update) * 1_000.0)
                else:
                    tres = 0.0

                submitted = max(node.shares_submitted, 0)
                phi_eff = 1.0 if submitted == 0 else node.shares_accepted / max(submitted, 1)
                neighbors = get_geometric_neighbors(node_id)
                if neighbors:
                    phase_alignment = [
                        (1.0 + math.cos(float(phases[node_id]) - float(phases[neighbor]))) / 2.0
                        for neighbor in neighbors
                    ]
                    chi_sync = sum(phase_alignment) / len(phase_alignment)
                else:
                    chi_sync = 1.0
                thermal_pressure = float(self.manifold.node_energy[node_id]) * max(float(power_scale), 1e-9)
                thermal_entropy = max(0.0, min(1.0, 0.30 * thermal_pressure))
                hash_rate = max(float(node.hashes), float(probabilities[node_id]) * max(self.state.total_hashes, 1))
                telemetry.append(NodeTelemetry(
                    node_id=node_id,
                    tres=tres,
                    phi_eff=max(0.0, min(1.0, phi_eff)),
                    chi_sync=max(0.0, min(1.0, chi_sync)),
                    thermal_entropy=thermal_entropy,
                    hash_rate=hash_rate,
                    timestamp=now,
                ))
            return telemetry

    def apply_autonomic_distribution(self, amplitudes: List[float], *, reason: str = "autonomic_optimization") -> List[float]:
        distribution = self.manifold.apply_work_distribution(amplitudes, reason=reason)
        self._append_event(
            "autonomic_distribution_applied",
            reason=reason,
            min_probability=float(min(distribution)),
            max_probability=float(max(distribution)),
        )
        return [float(value) for value in distribution]

    def phase_heartbeat(self, tick: int) -> List[float]:
        if not self.active_job_id:
            return []
        return self.manifold.phase_heartbeat(self.active_job_id, tick)

    def node_knows(self, node_id: int) -> Dict[str, Any]:
        neighbors = get_geometric_neighbors(node_id)
        return {
            "self": self.nodes[node_id].to_dict(),
            "assignment": self.assignments.get(node_id).to_dict() if node_id in self.assignments else None,
            "neighbors": [self.nodes[neighbor].to_dict() for neighbor in neighbors],
            "best_neighbor": self.best_neighbor(node_id),
            "active_job_id": self.active_job_id,
            "shared_state": self.state.snapshot(),
            "manifold_observation": self.manifold.observe().to_dict(),
            "compressed_nonce_plan": self.compressed_nonce_plan(),
        }

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            totals = {
                "shares_found": sum(node.shares_found for node in self.nodes.values()),
                "shares_submitted": sum(node.shares_submitted for node in self.nodes.values()),
                "shares_accepted": sum(node.shares_accepted for node in self.nodes.values()),
                "shares_rejected": sum(node.shares_rejected for node in self.nodes.values()),
            }
            return {
                "topology": self.topology_report,
                "worker_name": self.worker_name,
                "pool_visible_workers": 1,
                "internal_nodes": NUM_NODES,
                "active_pool_name": self.active_pool_name,
                "active_job_id": self.active_job_id,
                "job_epoch": self.job_epoch,
                "nonce_compression_plan": self.compressed_nonce_plan(),
                "assignments": {node_id: assignment.to_dict() for node_id, assignment in self.assignments.items()},
                "nodes": {node_id: node.to_dict() for node_id, node in self.nodes.items()},
                "shared_state": self.state.snapshot(),
                "manifold": self.manifold.snapshot(),
                "lifecycle": list(self.lifecycle),
                "share_ledger": list(self.share_ledger),
                "healing_routes": list(self.healing_routes),
                "autonomic_ledger": list(self.autonomic_ledger),
                "healing_ranges_overlap_free": self.healing_ranges_overlap_free(),
                "totals": totals,
            }


__all__ = [
    "ADJACENCY_MAP",
    "NUM_NODES",
    "SLICE_SIZE",
    "GlobalMiningState",
    "NeuralLink",
    "NodeAssignment",
    "NodeRuntimeState",
    "PulviniOverlayConcentrator",
    "get_geometric_neighbors",
    "nonce_slice",
    "nonce_range_inclusive",
    "verify_symmetry",
    "graph_diameter",
]
