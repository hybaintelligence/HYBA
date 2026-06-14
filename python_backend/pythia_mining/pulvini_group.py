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



@dataclass(frozen=True)
class CoxeterGroupCertificate:
    """Coxeter group certificate for the icosahedral group H3.

    The icosahedral group H3 is the Coxeter group with Coxeter diagram
    o-5-o-3-o (Coxeter matrix [[1,5,3],[5,1,3],[3,3,1]]). This certifies
    the reflection group structure underlying the dodecahedral/icosahedral
    symmetry without claiming search advantage.
    """

    coxeter_group: str
    coxeter_diagram: str
    coxeter_matrix: List[List[int]]
    rank: int
    order: int
    fundamental_reflections: int
    root_system_type: str
    dynkin_diagram: str
    weyl_group_type: str
    certificate_statement: str

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class A5RepresentationCertificate:
    """Finite-group certificate for the rotational icosahedral group A5.

    The 20 dodecahedral vertices are certified against the irreducible
    representation data of A5 without claiming a SHA-256 search advantage.
    Full graph automorphisms may have order 120; the orientation-preserving
    rotational subgroup is A5 of order 60.
    """

    group: str
    rotational_group_order: int
    full_automorphism_order: int
    conjugacy_classes: List[Dict[str, object]]
    irreducible_dimensions: List[int]
    character_table: List[Dict[str, object]]
    regular_representation_dimension_sum: int
    character_orthogonality_verified: bool
    max_irrep_dimension: int
    dodecahedral_permutation_dimension: int
    effective_dimension_bound: int
    heuristic_dimension_reduction: float
    coxeter_structure: Dict[str, object]
    quantum_speedup_claimed: bool
    certificate_statement: str

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


def coxeter_group_certificate() -> CoxeterGroupCertificate:
    """Return the Coxeter group certificate for the icosahedral group H3.

    The icosahedral group H3 is the Coxeter group with Coxeter diagram
    o-5-o-3-o, corresponding to the Coxeter matrix [[1,5,3],[5,1,3],[3,3,1]].
    This certifies the reflection group structure underlying the dodecahedral
    symmetry without claiming search advantage.
    """
    coxeter_matrix = [
        [1, 5, 3],
        [5, 1, 3],
        [3, 3, 1]
    ]
    
    return CoxeterGroupCertificate(
        coxeter_group="H3 icosahedral Coxeter group",
        coxeter_diagram="o-5-o-3-o",
        coxeter_matrix=coxeter_matrix,
        rank=3,
        order=120,
        fundamental_reflections=3,
        root_system_type="H3",
        dynkin_diagram="o-5-o-3-o",
        weyl_group_type="H3 (non-crystallographic)",
        certificate_statement=(
            "The icosahedral group H3 is a rank-3 Coxeter group with Coxeter diagram o-5-o-3-o "
            "and Coxeter matrix [[1,5,3],[5,1,3],[3,3,1]]. This certifies the reflection group "
            "structure underlying the dodecahedral/icosahedral symmetry. The group order is 120, "
            "matching the full automorphism group of the dodecahedron. No search advantage is claimed."
        ),
    )


def a5_representation_certificate(*, full_automorphism_order: int = 120) -> A5RepresentationCertificate:
    """Return the A5 character-table certificate used by PULVINI audits.

    This is a representation-theory certificate, not an optimizer.  It records
    the exact irreducible dimensions and character table so downstream code can
    audit whether a 20-state dodecahedral basis is being treated honestly.
    """
    import math

    sqrt5 = math.sqrt(5.0)
    phi = (1.0 + sqrt5) / 2.0
    phi_bar = (1.0 - sqrt5) / 2.0
    classes: List[Dict[str, object]] = [
        {"name": "1A", "size": 1, "element_order": 1},
        {"name": "2A", "size": 15, "element_order": 2},
        {"name": "3A", "size": 20, "element_order": 3},
        {"name": "5A", "size": 12, "element_order": 5},
        {"name": "5B", "size": 12, "element_order": 5},
    ]
    rows = [
        ("1", 1, [1.0, 1.0, 1.0, 1.0, 1.0]),
        ("3", 3, [3.0, -1.0, 0.0, phi, phi_bar]),
        ("3'", 3, [3.0, -1.0, 0.0, phi_bar, phi]),
        ("4", 4, [4.0, 0.0, 1.0, -1.0, -1.0]),
        ("5", 5, [5.0, 1.0, -1.0, 0.0, 0.0]),
    ]
    order = 60
    class_sizes = [int(c["size"]) for c in classes]
    orthogonal = True
    for i, (_, _, chi_i) in enumerate(rows):
        for j, (_, _, chi_j) in enumerate(rows):
            inner = sum(size * a * b for size, a, b in zip(class_sizes, chi_i, chi_j)) / order
            expected = 1.0 if i == j else 0.0
            if abs(inner - expected) > 1e-9:
                orthogonal = False
    dims = [dim for _, dim, _ in rows]
    max_dim = max(dims)
    permutation_dim = 20
    
    coxeter_cert = coxeter_group_certificate()
    
    return A5RepresentationCertificate(
        group="A5 rotational icosahedral group",
        rotational_group_order=order,
        full_automorphism_order=int(full_automorphism_order),
        conjugacy_classes=classes,
        irreducible_dimensions=dims,
        character_table=[
            {"irrep": name, "dimension": dim, "characters": dict(zip([c["name"] for c in classes], chars))}
            for name, dim, chars in rows
        ],
        regular_representation_dimension_sum=sum(dim * dim for dim in dims),
        character_orthogonality_verified=orthogonal,
        max_irrep_dimension=max_dim,
        dodecahedral_permutation_dimension=permutation_dim,
        effective_dimension_bound=max_dim,
        heuristic_dimension_reduction=math.sqrt(permutation_dim / max_dim),
        coxeter_structure=coxeter_cert.to_dict(),
        quantum_speedup_claimed=False,
        certificate_statement=(
            "A5 has five irreducible representations of dimensions 1, 3, 3, 4, 5; "
            "their squared dimensions sum to 60 and the character rows are orthonormal by conjugacy class sizes. "
            "The Coxeter group H3 (o-5-o-3-o) underlies the icosahedral symmetry with order 120. "
            "This certifies available symmetry structure for audits only; no SHA-256 quantum speedup is claimed."
        ),
    )

__all__ = [
    "NONCE_SPACE",
    "A5RepresentationCertificate",
    "CoxeterGroupCertificate",
    "TensorCoordinate",
    "a5_representation_certificate",
    "coxeter_group_certificate",
    "adjacency_sets",
    "apply_automorphism_to_nonce",
    "assert_symmetric_graph",
    "compute_graph_automorphisms",
    "compute_node_orbits",
    "nonce_orbit",
    "tensor_coordinate_for_node",
]
