"""PULVINI mathematical gate certificate helpers."""

from __future__ import annotations

from typing import Any

from .pulvini_group import adjacency_sets, compute_graph_automorphisms


def automorphism_runtime_certificate(adjacency_map: dict) -> dict:
    """
    Computes automorphism group of the RUNTIME adjacency map.
    Source of truth is the actual constant, not an idealised graph.
    Algorithm: VF2 isomorphism enumeration (networkx).
    """
    import time

    neighbors = adjacency_sets(adjacency_map)
    t0 = time.perf_counter()
    autos: list[Any]
    try:
        import networkx as nx

        G = nx.Graph()
        for node, node_neighbors in neighbors.items():
            for n in node_neighbors:
                G.add_edge(node, n)
        autos = list(nx.vf2userfeedback.isomorphisms_iter(G, G))
    except ModuleNotFoundError:
        autos = compute_graph_automorphisms(adjacency_map)
    elapsed_ms = (time.perf_counter() - t0) * 1000

    degrees = {node: len(node_neighbors) for node, node_neighbors in neighbors.items()}
    orbits: dict[int, list[int]] = {}
    for node, deg in degrees.items():
        orbits.setdefault(deg, []).append(node)

    violations = 0
    edges = {tuple(sorted((u, v))) for u, node_neighbors in neighbors.items() for v in node_neighbors}
    for sigma in autos:
        for u, v in edges:
            if isinstance(sigma, dict):
                left, right = sigma[u], sigma[v]
            else:
                left, right = sigma[u], sigma[v]
            if tuple(sorted((left, right))) not in edges:
                violations += 1

    return {
        "source": "runtime_ADJACENCY_MAP_constant",
        "algorithm": "VF2 isomorphism enumeration (networkx)",
        "computation_ms": round(elapsed_ms, 2),
        "group_order": len(autos),
        "node_orbits_by_degree": {
            deg: len(nodes) for deg, nodes in orbits.items()
        },
        "adjacency_preserved": violations == 0,
        "gate_closed": (
            len(autos) == 120
            and len(orbits.get(6, [])) == 20
            and len(orbits.get(10, [])) == 12
            and violations == 0
        )
    }


def phi_geometric_structure_certificate(
    plan: Any,
    compressor: Any,
    *,
    sample_size: int = 1_000_000,
    seed: int = 20260611,
    variance_ratio_threshold: float = 2.0,
    d_i_delta_threshold: float = 0.01,
) -> dict:
    """Empirically map phi-resonant nonce density onto PULVINI lanes.

    This certificate intentionally separates finite-sample inhomogeneity from
    statistically meaningful geometric structure. A non-zero lane variance is
    expected from sampling noise; the reported ``geometric_structure_detected``
    flag only closes when lane variance materially exceeds binomial sampling
    variance or D/I node classes diverge beyond the configured threshold.
    """
    import numpy as np

    sample_size = int(sample_size)
    if sample_size <= 0:
        raise ValueError("sample_size must be positive")

    rng = np.random.default_rng(int(seed))
    sample = rng.integers(0, 2**32, size=sample_size, dtype=np.uint64)
    phi_mask = np.fromiter(
        (compressor.phi_resonant(int(nonce)) for nonce in sample),
        dtype=bool,
        count=sample_size,
    )

    lane_stats = []
    ratios = []
    counts = []
    hits = []
    for lane_id, (start, end) in enumerate(plan.solver_ranges):
        lane_mask = (sample >= int(start)) & (sample <= int(end))
        lane_count = int(np.sum(lane_mask))
        if lane_count == 0:
            continue
        lane_hits = int(np.sum(phi_mask[lane_mask]))
        lane_ratio = float(lane_hits / lane_count)
        node_type = "D-node" if lane_id < 20 else "I-node"
        lane_stats.append({
            "lane_id": lane_id,
            "node_type": node_type,
            "start": int(start),
            "end": int(end),
            "sample_count": lane_count,
            "phi_hits": lane_hits,
            "phi_ratio": lane_ratio,
        })
        ratios.append(lane_ratio)
        counts.append(lane_count)
        hits.append(lane_hits)

    ratios_array = np.asarray(ratios, dtype=np.float64)
    counts_array = np.asarray(counts, dtype=np.float64)
    hits_array = np.asarray(hits, dtype=np.float64)
    total_hits = int(np.sum(hits_array))
    total_count = int(np.sum(counts_array))
    overall_ratio = float(total_hits / total_count)

    expected_variances = overall_ratio * (1.0 - overall_ratio) / counts_array
    expected_sampling_variance = float(np.mean(expected_variances))
    lane_variance = float(np.var(ratios_array))
    lane_stddev = float(np.std(ratios_array))
    variance_to_sampling_ratio = float(lane_variance / expected_sampling_variance)

    expected_hits = counts_array * overall_ratio
    expected_misses = counts_array * (1.0 - overall_ratio)
    misses = counts_array - hits_array
    hit_only_chi_square = float(np.sum(((hits_array - expected_hits) ** 2) / expected_hits))
    pearson_chi_square = float(np.sum(
        ((hits_array - expected_hits) ** 2) / expected_hits
        + ((misses - expected_misses) ** 2) / expected_misses
    ))
    degrees_of_freedom = max(1, len(lane_stats) - 1)
    # 95th percentile for chi-square(df=31), the lane topology test used here.
    # For any non-32-lane future topology, use the Wilson-Hilferty approximation.
    chi_square_critical_p_0_05 = 44.99 if degrees_of_freedom == 31 else float(
        degrees_of_freedom
        * (1.0 - 2.0 / (9.0 * degrees_of_freedom) + 1.6448536269514722 * (2.0 / (9.0 * degrees_of_freedom)) ** 0.5) ** 3
    )
    reject_uniform_lane_null_p_0_05 = bool(pearson_chi_square > chi_square_critical_p_0_05)

    d_ratios = ratios_array[:20]
    i_ratios = ratios_array[20:]
    d_node_avg = float(np.mean(d_ratios))
    i_node_avg = float(np.mean(i_ratios))
    d_i_delta = float(abs(d_node_avg - i_node_avg))

    non_identical_lane_measure = bool(lane_variance > 1e-9)
    geometric_structure_detected = bool(
        reject_uniform_lane_null_p_0_05
        or variance_to_sampling_ratio >= float(variance_ratio_threshold)
        or d_i_delta >= float(d_i_delta_threshold)
    )

    return {
        "sample_size": sample_size,
        "seed": int(seed),
        "lane_count": len(lane_stats),
        "overall_phi_ratio": overall_ratio,
        "manifold_mean_phi_ratio": float(np.mean(ratios_array)),
        "d_node_avg_phi_ratio": d_node_avg,
        "i_node_avg_phi_ratio": i_node_avg,
        "d_i_delta": d_i_delta,
        "lane_variance": lane_variance,
        "lane_stddev": lane_stddev,
        "expected_sampling_variance": expected_sampling_variance,
        "variance_to_sampling_ratio": variance_to_sampling_ratio,
        "lane_phi_ratio_min": float(np.min(ratios_array)),
        "lane_phi_ratio_max": float(np.max(ratios_array)),
        "lane_phi_ratio_range": float(np.max(ratios_array) - np.min(ratios_array)),
        "min_lane": int(lane_stats[int(np.argmin(ratios_array))]["lane_id"]),
        "max_lane": int(lane_stats[int(np.argmax(ratios_array))]["lane_id"]),
        "hit_only_chi_square": hit_only_chi_square,
        "pearson_chi_square": pearson_chi_square,
        "degrees_of_freedom": degrees_of_freedom,
        "chi_square_critical_p_0_05": chi_square_critical_p_0_05,
        "reject_uniform_lane_null_p_0_05": reject_uniform_lane_null_p_0_05,
        "reduced_chi_square": float(pearson_chi_square / degrees_of_freedom),
        "non_identical_lane_measure": non_identical_lane_measure,
        "geometric_structure_detected": geometric_structure_detected,
        "status": (
            "geometric_structure_detected"
            if geometric_structure_detected
            else "uniform_lane_distribution_not_rejected_p_0_05"
        ),
        "lane_stats": lane_stats,
    }


__all__ = ["automorphism_runtime_certificate", "phi_geometric_structure_certificate"]
