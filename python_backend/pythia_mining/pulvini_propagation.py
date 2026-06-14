"""PULVINI share propagation over the mathematical manifold."""

from __future__ import annotations

import hashlib
import time
import uuid
from collections import deque
from dataclasses import asdict, dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional, Set, Tuple

from .pulvini_manifold import PulviniManifold
from .pulvini_memory_fabric import PulviniMemoryFabric
from .pulvini_overlay import ADJACENCY_MAP, NUM_NODES, get_geometric_neighbors

PROXY_GATEWAY = 31
ShareSubmitter = Callable[[Any, int, str], Awaitable[Any]]


@dataclass
class ShareSignal:
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
        digest = (
            hash_bytes
            or hashlib.sha256(
                f"{job_id}:{finder_id}:{nonce}:{extranonce2}".encode("utf-8")
            ).digest()
        )
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
        result_payload = (
            self.share_result.to_dict()
            if hasattr(self.share_result, "to_dict")
            else (
                asdict(self.share_result)
                if hasattr(self.share_result, "__dataclass_fields__")
                else self.share_result
            )
        )
        return {
            "share_signal": self.share_signal.to_dict(),
            "share_result": result_payload,
            "cancel_signal": self.cancel_signal.to_dict(),
            "route": list(self.route),
            "cancelled_nodes": list(self.cancelled_nodes),
        }


class ShareRouter:
    """Unicast inbound router. Path is selected by manifold gradient weights."""

    def __init__(self, manifold: Optional[PulviniManifold] = None) -> None:
        self.manifold = manifold or PulviniManifold(ADJACENCY_MAP)

    def next_hop(self, current: int, signal: ShareSignal) -> Optional[int]:
        route = self.manifold.gradient_route_to_gateway(current, PROXY_GATEWAY)
        for node_id in route[1:]:
            if node_id not in signal.hop_trace:
                return node_id
        return None

    def route_to_proxy(self, signal: ShareSignal) -> List[int]:
        route = self.manifold.gradient_route_to_gateway(signal.finder_id, PROXY_GATEWAY)
        signal.hop_trace = list(route)
        return route


class CancelFlood:
    """Cancellation propagation ordered by learned manifold gradient weights."""

    def __init__(self, manifold: Optional[PulviniManifold] = None) -> None:
        self.manifold = manifold or PulviniManifold(ADJACENCY_MAP)

    def _hop_count_from_gateway(self, order: List[int]) -> int:
        distance = {PROXY_GATEWAY: 0}
        queue: deque[int] = deque([PROXY_GATEWAY])
        while queue:
            node_id = queue.popleft()
            for neighbor in get_geometric_neighbors(node_id):
                if neighbor not in distance:
                    distance[neighbor] = distance[node_id] + 1
                    queue.append(neighbor)
        return max(distance[node_id] for node_id in order)

    def flood(self, signal: CancelSignal) -> Tuple[List[int], int]:
        order = self.manifold.gradient_broadcast_order(PROXY_GATEWAY)
        if len(order) != NUM_NODES:
            raise RuntimeError(
                f"cancel flood reached {len(order)}/{NUM_NODES} PULVINI nodes"
            )
        max_hop = self._hop_count_from_gateway(order)
        signal.visited = order
        signal.max_hop = max_hop
        return order, max_hop


class SharePropagationController:
    """Share-found sequence: route -> submit once -> Hebbian update -> cancel."""

    def __init__(
        self,
        manifold: Optional[PulviniManifold] = None,
        memory_fabric: Optional[PulviniMemoryFabric] = None,
    ) -> None:
        self.manifold = manifold or PulviniManifold(ADJACENCY_MAP)
        self.memory_fabric = memory_fabric or PulviniMemoryFabric(num_nodes=NUM_NODES)
        self.router = ShareRouter(self.manifold)
        self.cancel_flood = CancelFlood(self.manifold)
        self.seen_shares: Set[str] = set()
        self.seen_job_nonces: Set[str] = set()  # Global deduplication by job_id + nonce
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
        # Global deduplication by job_id + nonce to prevent duplicate submissions across nodes
        job_nonce_key = f"{job.job_id}:{nonce}"
        if job_nonce_key in self.seen_job_nonces:
            # Return early with duplicate result instead of raising exception
            duplicate_signal = ShareSignal.create(
                job_id=str(job.job_id),
                finder_id=finder_id,
                nonce=nonce,
                extranonce2=extranonce2,
                hash_bytes=hash_bytes,
            )
            return PropagationResult(
                share_signal=duplicate_signal,
                share_result=type(
                    "obj",
                    (object,),
                    {"accepted": False, "error": "duplicate_share", "error_code": 421},
                ),
                cancel_signal=CancelSignal(
                    job_id=str(job.job_id),
                    reason="duplicate_share",
                    source_share_id=duplicate_signal.share_id,
                ),
                route=[finder_id],
                cancelled_nodes=[],
            )

        signal = ShareSignal.create(
            job_id=str(job.job_id),
            finder_id=finder_id,
            nonce=nonce,
            extranonce2=extranonce2,
            hash_bytes=hash_bytes,
        )
        if signal.share_id in self.seen_shares:
            raise RuntimeError(f"duplicate share signal: {signal.share_id}")

        # Mark this job_id + nonce combination as seen globally
        self.seen_job_nonces.add(job_nonce_key)
        self.seen_shares.add(signal.share_id)

        route = self.router.route_to_proxy(signal)
        share_result = await submitter(job, nonce, extranonce2)
        accepted = bool(getattr(share_result, "accepted", False))
        reward = 1.0 if accepted else -0.1
        self.manifold.hebbian_fire(
            route,
            signal_type="SHARE_FOUND" if accepted else "SHARE_REJECTED",
            reward=reward,
        )
        self.memory_fabric.record_path(route, reward=reward)
        reason = "share_accepted" if accepted else "share_rejected"
        cancel = CancelSignal(
            job_id=str(job.job_id), reason=reason, source_share_id=signal.share_id
        )
        cancelled_nodes, _max_hop = self.cancel_flood.flood(cancel)
        self.cancelled_jobs[str(job.job_id)] = cancel

        # Clean up deduplication entries for this job to prevent unbounded growth
        keys_to_remove = [
            key for key in self.seen_job_nonces if key.startswith(f"{job.job_id}:")
        ]
        for key in keys_to_remove:
            self.seen_job_nonces.remove(key)

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
            "cancelled_jobs": {
                job_id: signal.to_dict()
                for job_id, signal in self.cancelled_jobs.items()
            },
            "history": list(self.history),
            "manifold": self.manifold.snapshot(),
            "memory_fabric": self.memory_fabric.compressed_kernel_snapshot().to_dict(),
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
