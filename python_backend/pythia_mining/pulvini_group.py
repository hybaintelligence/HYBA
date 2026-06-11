"""PULVINI graph automorphism and nonce-orbit utilities."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, List, Optional, Sequence, Set, Tuple

NONCE_SPACE = 2 ** 32


@dataclass(frozen=True)
class TensorCoordinate:
    node_id: int
    orbit_id: int
    orbit_size: int
    nonce_residue: int
    nonce_stride: int
    cardinality: int
    legacy_range: Tuple[int, int]
    amplitude: float = 0.0
    phase: float = 0.0

    def to_dict(self) -> Dict[str, object]:
        payload = asdict(self)
        payload["legacy_range"] = list(self.legacy_range)
        return payload


def adjacency_sets(adjacency_map: Dict[int, Dict[str, List[int]]]) -> Dict[int, Set[int]]:
    return {
        node_id: set(payload.get("d", []) + payload.get("i", []))
        for node_id, payload in adjacency_map.items()
    }


def assert_symmetric_graph(neighbors: Dict[int, Set[int]]) -> None:
    for node_id, node_neighbors in neighbors.items():
        for neighbor in node_neighbors:
            if node_id not in neighbors.get(neighbor, set()):
                raise ValueError(f"asymmetric graph edge: {node_id}->{neighbor}")


def compute_graph_automorphisms(
    adjacency_map: Dict[int, Dict[str, List[int]]],
    *,
    max_count: Optional[int] = None,
) -> List[Tuple[int, ...]]:
    """Enumerate graph automorphisms exactly with degree-preserving backtracking."""
    neighbors = adjacency_sets(adjacency_map)
    assert_symmetric_graph(neighbors)
    nodes = list(range(len(adjacency_map)))
    degree = {node_id: len(neighbors[node_id]) for node_id in nodes}
    candidates = {
        node_id: {other for other in nodes if degree[other] == degree[node_id]}
        for node_id in nodes
    }
    mapping: Dict[int, int] = {}
    used: Set[int] = set()
    automorphisms: List[Tuple[int, ...]] = []

    def feasible_targets(source: int) -> List[int]:
        result = []
        for target in candidates[source]:
            if target in used:
                continue
            ok = True
            for mapped_source, mapped_target in mapping.items():
                if (mapped_source in neighbors[source]) != (mapped_target in neighbors[target]):
                    ok = False
                    break
            if ok:
                result.append(target)
        return result

    def choose_source() -> Tuple[Optional[int], List[int]]:
        best_source: Optional[int] = None
        best_targets: List[int] = []
        for source in nodes:
            if source in mapping:
                continue
            targets = feasible_targets(source)
            if best_source is None or len(targets) < len(best_targets):
                best_source = source
                best_targets = targets
                if not targets:
                    break
        return best_source, best_targets

    def backtrack() -> None:
        if max_count is not None and len(automorphisms) >= max_count:
            return
        if len(mapping) == len(nodes):
            automorphisms.append(tuple(mapping[i] for i in nodes))
            return
        source, targets = choose_source()
        if source is None or not targets:
            return
        for target in targets:
            mapping[source] = target
            used.add(target)
            backtrack()
            used.remove(target)
            del mapping[source]

    backtrack()
    if not automorphisms:
        raise RuntimeError("automorphism enumeration returned no identity mapping")
    return automorphisms


def compute_node_orbits(num_nodes: int, automorphisms: Sequence[Tuple[int, ...]]) -> List[List[int]]:
    unseen = set(range(num_nodes))
    orbits: List[List[int]] = []
    while unseen:
        seed = min(unseen)
        orbit = sorted({permutation[seed] for permutation in automorphisms})
        orbits.append(orbit)
        unseen -= set(orbit)
    return orbits


def apply_automorphism_to_nonce(nonce: int, automorphism: Sequence[int], num_nodes: int = 32) -> int:
    """Action on Z_2^32 represented as sigma(q*N+r)=q*N+sigma(r)."""
    nonce = int(nonce) % NONCE_SPACE
    residue = nonce % num_nodes
    quotient = nonce // num_nodes
    return (quotient * num_nodes + int(automorphism[residue])) % NONCE_SPACE


def nonce_orbit(nonce: int, automorphisms: Sequence[Tuple[int, ...]], num_nodes: int = 32) -> List[int]:
    return sorted({apply_automorphism_to_nonce(nonce, sigma, num_nodes) for sigma in automorphisms})


def tensor_coordinate_for_node(
    node_id: int,
    *,
    num_nodes: int,
    node_orbits: Sequence[Sequence[int]],
    node_to_orbit: Dict[int, int],
    amplitude: float,
    phase: float,
) -> TensorCoordinate:
    node_id = int(node_id)
    orbit_id = node_to_orbit[node_id]
    orbit = node_orbits[orbit_id]
    residue = node_id
    cardinality = (NONCE_SPACE - 1 - residue) // num_nodes + 1
    contiguous_size = NONCE_SPACE // num_nodes
    legacy_start = node_id * contiguous_size
    legacy_end = legacy_start + contiguous_size - 1
    return TensorCoordinate(
        node_id=node_id,
        orbit_id=orbit_id,
        orbit_size=len(orbit),
        nonce_residue=residue,
        nonce_stride=num_nodes,
        cardinality=cardinality,
        legacy_range=(legacy_start, legacy_end),
        amplitude=float(amplitude),
        phase=float(phase),
    )


__all__ = [
    "NONCE_SPACE",
    "TensorCoordinate",
    "adjacency_sets",
    "apply_automorphism_to_nonce",
    "assert_symmetric_graph",
    "compute_graph_automorphisms",
    "compute_node_orbits",
    "nonce_orbit",
    "tensor_coordinate_for_node",
]
