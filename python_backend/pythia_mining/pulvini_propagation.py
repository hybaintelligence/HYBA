"""
PULVINI Share Propagation Layer.

When a node finds a share, the signal path is not a broadcast. The finder emits
one inbound ShareSignal that is routed toward the H31 proxy gateway. The proxy
submits exactly once to the upstream pool, then emits an outbound CancelSignal
flood so every PULVINI node abandons the now-stale job.
"""

from __future__ import annotations

import hashlib
import time
import uuid
from collections import deque
from dataclasses import asdict, dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional, Set, Tuple

from .pulvini_overlay import NUM_NODES, get_geometric_neighbors

PROXY_GATEWAY = 31
ShareSubmitter = Callable[[Any, int, str], Awaitable[Any]]


@dataclass
class ShareSignal:
    """Inbound signal: finder -> nearest/best hub path -> H31/proxy."""

    share_id: str
    job_id: str
    finder_id: int
    nonce: int
    extranonce2: str
    hash_hex: Optional[str] = None
    timestamp: float = field(default_factory=time.monotonic)
    hop_trace: List[int] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        *,
        job_id: str,
        finder_id: int,
        nonce: int,
        extranonce2: str,
        hash_bytes: Optional[bytes] = None,
    ) -> "ShareSignal":
        digest = hash_bytes or hashlib.sha256(f"{job_id}:{finder_id}:{nonce}:{extranonce2}".encode("utf-8")).digest()
        return cls(
            share_id=str(uuid.uuid4()),
            job_id=str(job_id),
            finder_id=int(finder_id),
            nonce=int(nonce),
            extranonce2=extranonce2,
            hash_hex=digest.hex(),
            hop_trace=[int(finder_id)],
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CancelSignal:
    """Outbound signal: H31/proxy -> all nodes via BFS flood."""

    job_id: str
    reason: str
    source_share_id: str
    timestamp: float = field(default_factory=time.monotonic)
    visited: List[int] = field(default_factory=list)
    max_hop: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PropagationResult:
    share_signal: ShareSignal
    share_result: Any
    cancel_signal: CancelSignal
    route: List[int]
    cancelled_nodes: List[int]

    def to_dict(self) -> Dict[str, Any]:
        result_payload = self.share_result.to_dict() if hasattr(self.share_result, "to_dict") else asdict(self.share_result) if hasattr(self.share_result, "__dataclass_fields__") else self.share_result
        return {
            "share_signal": self.share_signal.to_dict(),
            "share_result": result_payload,
            "cancel_signal": self.cancel_signal.to_dict(),
            "route": list(self.route),
            "cancelled_nodes": list(self.cancelled_nodes),
        }


class ShareRouter:
    """Greedy unicast router for inbound share propagation."""

    def __init__(self, weights: Optional[Dict[int, Dict[int, float]]] = None) -> None:
        self.weights: Dict[int, Dict[int, float]] = weights or {
            node_id: {neighbor: 1.0 for neighbor in get_geometric_neighbors(node_id)}
            for node_id in range(NUM_NODES)
        }

    @staticmethod
    def _distance_to_gateway(start: int) -> int:
        if start == PROXY_GATEWAY:
            return 0
        distances = {start: 0}
        queue: deque[int] = deque([start])
        while queue:
            node_id = queue.popleft()
            for neighbor in get_geometric_neighbors(node_id):
                if neighbor in distances:
                    continue
                distances[neighbor] = distances[node_id] + 1
                if neighbor == PROXY_GATEWAY:
                    return distances[neighbor]
                queue.append(neighbor)
        return NUM_NODES

    def next_hop(self, current: int, signal: ShareSignal) -> Optional[int]:
        if current == PROXY_GATEWAY:
            return None
        seen = set(signal.hop_trace)
        candidates = [neighbor for neighbor in get_geometric_neighbors(current) if neighbor not in seen]
        if not candidates:
            return None

        def score(node_id: int) -> Tuple[int, int, float]:
            gateway_bonus = 100 if node_id == PROXY_GATEWAY else 0
            hub_bonus = 10 if node_id >= 20 else 0
            closeness = -self._distance_to_gateway(node_id)
            weight = self.weights.get(current, {}).get(node_id, 1.0)
            return (gateway_bonus + hub_bonus, closeness, weight)

        return max(candidates, key=score)

    def route_to_proxy(self, signal: ShareSignal) -> List[int]:
        route = [signal.finder_id]
        current = signal.finder_id
        signal.hop_trace = [signal.finder_id]
        while current != PROXY_GATEWAY:
            nxt = self.next_hop(current, signal)
            if nxt is None:
                raise RuntimeError(f"share {signal.share_id} cannot route from node {current} to proxy gateway")
            route.append(nxt)
            signal.hop_trace.append(nxt)
            current = nxt
            if len(route) > NUM_NODES:
                raise RuntimeError(f"share {signal.share_id} route loop detected")
        return route


class CancelFlood:
    """BFS cancellation flood from H31 to all internal PULVINI nodes."""

    def flood(self, signal: CancelSignal) -> Tuple[List[int], int]:
        visited: Set[int] = {PROXY_GATEWAY}
        order = [PROXY_GATEWAY]
        max_hop = 0
        queue: deque[Tuple[int, int]] = deque((neighbor, 1) for neighbor in get_geometric_neighbors(PROXY_GATEWAY))
        for neighbor in get_geometric_neighbors(PROXY_GATEWAY):
            visited.add(neighbor)

        while queue:
            node_id, hop = queue.popleft()
            order.append(node_id)
            max_hop = max(max_hop, hop)
            for neighbor in get_geometric_neighbors(node_id):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, hop + 1))

        if len(visited) != NUM_NODES:
            raise RuntimeError(f"cancel flood reached {len(visited)}/{NUM_NODES} PULVINI nodes")
        signal.visited = order
        signal.max_hop = max_hop
        return order, max_hop


class SharePropagationController:
    """Atomic share-found sequence: route -> submit once -> cancel flood -> record."""

    def __init__(self) -> None:
        self.router = ShareRouter()
        self.cancel_flood = CancelFlood()
        self.seen_shares: Set[str] = set()
        self.history: List[Dict[str, Any]] = []
        self.cancelled_jobs: Dict[str, CancelSignal] = {}

    async def handle_share_found(
        self,
        *,
        job: Any,
        finder_id: int,
        nonce: int,
        extranonce2: str,
        submitter: ShareSubmitter,
        hash_bytes: Optional[bytes] = None,
    ) -> PropagationResult:
        signal = ShareSignal.create(
            job_id=str(job.job_id),
            finder_id=finder_id,
            nonce=nonce,
            extranonce2=extranonce2,
            hash_bytes=hash_bytes,
        )
        if signal.share_id in self.seen_shares:
            raise RuntimeError(f"duplicate share signal: {signal.share_id}")
        self.seen_shares.add(signal.share_id)

        route = self.router.route_to_proxy(signal)
        share_result = await submitter(job, nonce, extranonce2)
        reason = "share_accepted" if bool(getattr(share_result, "accepted", False)) else "share_rejected"
        cancel = CancelSignal(job_id=str(job.job_id), reason=reason, source_share_id=signal.share_id)
        cancelled_nodes, _max_hop = self.cancel_flood.flood(cancel)
        self.cancelled_jobs[str(job.job_id)] = cancel

        result = PropagationResult(
            share_signal=signal,
            share_result=share_result,
            cancel_signal=cancel,
            route=route,
            cancelled_nodes=cancelled_nodes,
        )
        self.history.append(result.to_dict())
        if len(self.history) > 256:
            del self.history[: len(self.history) - 256]
        return result

    def is_job_cancelled(self, job_id: str) -> bool:
        return str(job_id) in self.cancelled_jobs

    def snapshot(self) -> Dict[str, Any]:
        return {
            "proxy_gateway": PROXY_GATEWAY,
            "seen_shares": len(self.seen_shares),
            "cancelled_jobs": {job_id: signal.to_dict() for job_id, signal in self.cancelled_jobs.items()},
            "history": list(self.history),
        }


__all__ = [
    "PROXY_GATEWAY",
    "ShareSignal",
    "CancelSignal",
    "PropagationResult",
    "ShareRouter",
    "CancelFlood",
    "SharePropagationController",
]
