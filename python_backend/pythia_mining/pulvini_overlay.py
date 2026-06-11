"""PULVINI overlay: one pool-facing worker, 32-node mathematical manifold."""

from __future__ import annotations

import time
from collections import deque
from dataclasses import asdict, dataclass, field
from threading import RLock
from typing import Any, Dict, List, Optional, Tuple

from .pulvini_manifold import PulviniManifold
from .pulvini_nonce_compression import PulviniNonceSpaceCompressor

from .pulvini_topology import (
    ADJACENCY_MAP,
    MAX_UINT32_NONCE,
    NONCE_BITS,
    NUM_NODES,
    SLICE_SIZE,
    bfs_distances,
    get_geometric_neighbors,
    graph_diameter,
    nonce_range_inclusive,
    nonce_slice,
    verify_symmetry,
)


@dataclass
class NeuralLink:
    target_id: int
    weight: float = 1.0
    _history: deque[float] = field(default_factory=lambda: deque(maxlen=10), repr=False)

    def record_trip(self, trip_seconds: float) -> None:
        self._history.append(max(float(trip_seconds), 0.0))
        avg = sum(self._history) / len(self._history)
        self.weight = 1.0 / (avg + 1e-9)

    def to_dict(self) -> Dict[str, Any]:
        return {"target_id": self.target_id, "weight": self.weight, "samples": len(self._history)}


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
