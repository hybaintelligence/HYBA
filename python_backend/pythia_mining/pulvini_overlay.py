"""
PULVINI Mining Overlay — pool-facing singleton, 32-node internal mesh.

The upstream Stratum pool sees one worker identity. Internally HYBA presents that
single job to 32 coordinated PULVINI nodes over a dodecahedron/icosahedron dual
compound. This module owns the deterministic nonce/extranonce2 partitioning and
shared knowledge surface used by GenesisAI, MIDAS telemetry, and tests.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import asdict, dataclass, field
from threading import RLock
from typing import Any, Dict, Iterable, List, Optional, Tuple

NUM_NODES = 32
NONCE_BITS = 32
MAX_UINT32_NONCE = (1 << NONCE_BITS) - 1
SLICE_SIZE = (1 << NONCE_BITS) // NUM_NODES

ADJACENCY_MAP: Dict[int, Dict[str, List[int]]] = {
    0: {"d": [1, 4, 5], "i": [20, 21, 22]},
    1: {"d": [0, 2, 7], "i": [20, 22, 23]},
    2: {"d": [1, 3, 9], "i": [20, 23, 24]},
    3: {"d": [2, 4, 11], "i": [20, 24, 25]},
    4: {"d": [3, 0, 13], "i": [20, 25, 21]},
    5: {"d": [0, 6, 14], "i": [21, 22, 26]},
    6: {"d": [5, 7, 15], "i": [22, 26, 27]},
    7: {"d": [1, 6, 8], "i": [22, 23, 27]},
    8: {"d": [7, 9, 16], "i": [23, 27, 28]},
    9: {"d": [2, 8, 10], "i": [23, 24, 28]},
    10: {"d": [9, 11, 17], "i": [24, 28, 29]},
    11: {"d": [3, 10, 12], "i": [24, 25, 29]},
    12: {"d": [11, 13, 18], "i": [25, 29, 30]},
    13: {"d": [4, 12, 14], "i": [25, 21, 30]},
    14: {"d": [5, 13, 19], "i": [21, 26, 30]},
    15: {"d": [6, 16, 19], "i": [26, 27, 31]},
    16: {"d": [8, 15, 17], "i": [27, 28, 31]},
    17: {"d": [10, 16, 18], "i": [28, 29, 31]},
    18: {"d": [12, 17, 19], "i": [29, 30, 31]},
    19: {"d": [14, 15, 18], "i": [26, 30, 31]},
    20: {"i": [21, 22, 23, 24, 25], "d": [0, 1, 2, 3, 4]},
    21: {"i": [20, 22, 26, 30, 25], "d": [0, 4, 13, 14, 5]},
    22: {"i": [20, 21, 26, 27, 23], "d": [0, 5, 6, 7, 1]},
    23: {"i": [20, 22, 27, 28, 24], "d": [1, 7, 8, 9, 2]},
    24: {"i": [20, 23, 28, 29, 25], "d": [2, 9, 10, 11, 3]},
    25: {"i": [20, 24, 29, 30, 21], "d": [3, 11, 12, 13, 4]},
    26: {"i": [21, 22, 27, 31, 30], "d": [5, 6, 15, 19, 14]},
    27: {"i": [22, 23, 28, 31, 26], "d": [6, 7, 8, 16, 15]},
    28: {"i": [23, 24, 29, 31, 27], "d": [8, 9, 10, 17, 16]},
    29: {"i": [24, 25, 30, 31, 28], "d": [10, 11, 12, 18, 17]},
    30: {"i": [21, 25, 29, 31, 26], "d": [12, 13, 14, 19, 18]},
    31: {"i": [26, 27, 28, 29, 30], "d": [15, 16, 17, 18, 19]},
}


def get_geometric_neighbors(node_id: int) -> List[int]:
    if node_id not in ADJACENCY_MAP:
        raise ValueError(f"unknown PULVINI node_id: {node_id}")
    mapping = ADJACENCY_MAP[node_id]
    return list(mapping.get("d", [])) + list(mapping.get("i", []))


def nonce_slice(node_id: int) -> Tuple[int, int]:
    if not 0 <= node_id < NUM_NODES:
        raise ValueError(f"node_id must be in [0, {NUM_NODES - 1}]")
    start = node_id * SLICE_SIZE
    end_exclusive = start + SLICE_SIZE
    return start, end_exclusive


def nonce_range_inclusive(node_id: int) -> Tuple[int, int]:
    start, end_exclusive = nonce_slice(node_id)
    return start, end_exclusive - 1


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
    """Thread-safe logical shared state for the 32-node concentrator overlay."""

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
            if candidate > self.best_diff_observed:
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
    """
    Single pool-facing concentrator for 32 internal PULVINI nodes.

    The pool receives one worker identity and one Stratum share stream. Internally,
    every node receives a deterministic assignment and writes knowledge into the
    shared overlay state. The mesh makes every node's phase/progress visible to the
    whole runtime without broadcasting every hash attempt upstream.
    """

    def __init__(self, worker_name: str = "PULVINI.singularity") -> None:
        if not verify_symmetry():
            raise RuntimeError("PULVINI adjacency map must be symmetric before production mining starts")
        self.worker_name = worker_name
        self.state = GlobalMiningState()
        self.job_epoch = 0
        self.active_job_id: Optional[str] = None
        self.active_pool_name: Optional[str] = None
        self.assignments: Dict[int, NodeAssignment] = {}
        self.nodes: Dict[int, NodeRuntimeState] = {
            node_id: NodeRuntimeState(node_id=node_id, role="hub" if node_id >= 20 else "worker")
            for node_id in range(NUM_NODES)
        }
        self.links: Dict[int, Dict[int, NeuralLink]] = {
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

    def _extranonce2_for_node(self, node_id: int, extranonce2_size: int) -> str:
        size = max(int(extranonce2_size), 1)
        return int(node_id).to_bytes(size, byteorder="big", signed=False).hex()

    def register_pool_job(self, job: Any, pool_name: Optional[str] = None) -> Dict[int, NodeAssignment]:
        with self._lock:
            if self.active_job_id == job.job_id and self.assignments:
                return dict(self.assignments)
            self.job_epoch += 1
            self.active_job_id = str(job.job_id)
            self.state.activate_job(str(job.job_id), int(job.target))
            self.assignments = {}
            for node_id in range(NUM_NODES):
                start, end = nonce_range_inclusive(node_id)
                assignment = NodeAssignment(
                    node_id=node_id,
                    job_id=str(job.job_id),
                    nonce_start=start,
                    nonce_end=end,
                    extranonce2=self._extranonce2_for_node(node_id, getattr(job, "extranonce2_size", 4)),
                    role="hub" if node_id >= 20 else "worker",
                    neighbors=get_geometric_neighbors(node_id),
                )
                self.assignments[node_id] = assignment
                node = self.nodes[node_id]
                node.phase = "assigned"
                node.active_job_id = str(job.job_id)
                node.nonce_start = start
                node.nonce_end = end
                node.current_nonce = start
                node.last_update = time.time()
                node.best_neighbor = self.best_neighbor(node_id)
            self._append_event("job_received", job_id=str(job.job_id), pool_name=pool_name, epoch=self.job_epoch)
            self._append_event("work_configured", job_id=str(job.job_id), assignments=NUM_NODES, nonce_slice_size=SLICE_SIZE)
            return dict(self.assignments)

    def nonce_ranges(self) -> List[Tuple[int, int]]:
        return [(assignment.nonce_start, assignment.nonce_end) for assignment in self.assignments.values()]

    def assignment_for_nonce(self, nonce: int) -> Optional[NodeAssignment]:
        for assignment in self.assignments.values():
            if assignment.nonce_start <= nonce <= assignment.nonce_end:
                return assignment
        return None

    def record_node_progress(self, node_id: int, nonce: int, hashes: int = 0, best_diff: Optional[int] = None) -> None:
        with self._lock:
            node = self.nodes[node_id]
            node.phase = "searching"
            node.current_nonce = int(nonce)
            node.hashes += max(int(hashes), 0)
            node.last_update = time.time()
            self.state.set_node_progress(node_id, nonce)
            self.state.increment_hashes(hashes)
            if best_diff is not None and self.state.update_best_diff(best_diff):
                node.best_diff = int(best_diff)

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
                "timestamp": time.time(),
            }
            self.share_ledger.append(payload)
            if len(self.share_ledger) > 256:
                del self.share_ledger[: len(self.share_ledger) - 256]
            self._append_event("share_submitted", node_id=node_id, job_id=payload["job_id"], nonce=int(nonce))
            self._append_event("share_outcome_recorded", node_id=node_id, accepted=accepted, error_code=payload["error_code"])
            return payload

    def best_neighbor(self, node_id: int) -> Optional[int]:
        links = self.links.get(node_id, {})
        if not links:
            return None
        return max(links, key=lambda neighbor: links[neighbor].weight)

    def record_link_latency(self, source_id: int, target_id: int, trip_seconds: float) -> None:
        if target_id not in self.links.get(source_id, {}):
            raise ValueError(f"nodes {source_id}->{target_id} are not adjacent in PULVINI topology")
        self.links[source_id][target_id].record_trip(trip_seconds)
        self.nodes[source_id].best_neighbor = self.best_neighbor(source_id)

    def route_for_share(self, node_id: int) -> List[int]:
        """Return a deterministic neighbour-aware route from node to concentrator."""
        if node_id >= 20:
            return [node_id]
        first_hop = self.best_neighbor(node_id)
        if first_hop is None:
            return [node_id]
        if first_hop >= 20:
            return [node_id, first_hop]
        hub_neighbors = [neighbor for neighbor in get_geometric_neighbors(first_hop) if neighbor >= 20]
        return [node_id, first_hop] + ([hub_neighbors[0]] if hub_neighbors else [])

    def node_knows(self, node_id: int) -> Dict[str, Any]:
        node = self.nodes[node_id]
        neighbors = get_geometric_neighbors(node_id)
        return {
            "self": node.to_dict(),
            "assignment": self.assignments.get(node_id).to_dict() if node_id in self.assignments else None,
            "neighbors": [self.nodes[neighbor].to_dict() for neighbor in neighbors],
            "best_neighbor": self.best_neighbor(node_id),
            "active_job_id": self.active_job_id,
            "shared_state": self.state.snapshot(),
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
                "assignments": {node_id: assignment.to_dict() for node_id, assignment in self.assignments.items()},
                "nodes": {node_id: node.to_dict() for node_id, node in self.nodes.items()},
                "shared_state": self.state.snapshot(),
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
