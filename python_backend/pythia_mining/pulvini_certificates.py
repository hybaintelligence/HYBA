"""PULVINI mathematical gate certificate helpers."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any

from .pulvini_group import adjacency_sets, compute_graph_automorphisms


def adjacency_map_digest(adjacency_map: dict) -> str:
    """Return a canonical SHA-256 digest for the runtime adjacency map."""
    normalized = {
        int(node): {
            "d": sorted(int(value) for value in payload.get("d", [])),
            "i": sorted(int(value) for value in payload.get("i", [])),
        }
        for node, payload in sorted(adjacency_map.items())
    }
    material = json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def _certificate_cache_path(map_hash: str) -> Path:
    root = Path(os.getenv("PULVINI_CERTIFICATE_CACHE_DIR", Path(tempfile.gettempdir()) / "hyba_pulvini_certificates"))
    return root / f"automorphism-{map_hash}.json"


def _load_cached_automorphism_certificate(path: Path, map_hash: str) -> dict | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None
    if payload.get("adjacency_map_sha256") != map_hash:
        return None
    required = {
        "source",
        "algorithm",
        "group_order",
        "node_orbits_by_degree",
        "adjacency_preserved",
        "gate_closed",
    }
    if not required.issubset(payload):
        return None
    payload["cache_status"] = "hit"
    payload.setdefault("computation_ms", 0.0)
    if isinstance(payload.get("node_orbits_by_degree"), dict):
        payload["node_orbits_by_degree"] = {
            int(degree): int(count)
            for degree, count in payload["node_orbits_by_degree"].items()
        }
    return payload


def _store_cached_automorphism_certificate(path: Path, certificate: dict) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(certificate, sort_keys=True, separators=(",", ":")), encoding="utf-8")
    except OSError:
        return


def automorphism_runtime_certificate(adjacency_map: dict, *, use_cache: bool = True) -> dict:
    """
    Compute the exact automorphism group certificate for the runtime adjacency map.

    The source of truth is always the supplied runtime constant.  CI uses a
    digest-keyed cache after the first exact computation, and the computation
    path avoids NetworkX VF2 enumeration so the gate cannot fail because an
    optional dependency consumed runner memory.
    """
    neighbors = adjacency_sets(adjacency_map)
    map_hash = adjacency_map_digest(adjacency_map)
    cache_path = _certificate_cache_path(map_hash)
    if use_cache:
        cached = _load_cached_automorphism_certificate(cache_path, map_hash)
        if cached is not None:
            return cached

    t0 = time.perf_counter()
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
            left, right = sigma[u], sigma[v]
            if tuple(sorted((left, right))) not in edges:
                violations += 1

    certificate = {
        "source": "runtime_ADJACENCY_MAP_constant",
        "adjacency_map_sha256": map_hash,
        "algorithm": "exact degree-preserving backtracking over runtime adjacency map",
        "cache_status": "miss",
        "cache_path": str(cache_path),
        "computation_ms": round(elapsed_ms, 2),
        "group_order": len(autos),
        "node_orbits_by_degree": {deg: len(nodes) for deg, nodes in orbits.items()},
        "adjacency_preserved": violations == 0,
        "gate_closed": (
            len(autos) == 120
            and len(orbits.get(6, [])) == 20
            and len(orbits.get(10, [])) == 12
            and violations == 0
        ),
    }
    if use_cache:
        _store_cached_automorphism_certificate(cache_path, certificate)
    return certificate


def phi_geometric_structure_certificate(
    plan: Any,
    compressor: Any,
    *,
    sample_size: int = 1_000_000,
    seed: int = 20260611,
    variance_ratio_threshold: float = 2.0,
    d_i_delta_threshold: float = 0.01,
) -> dict:
    """Map phi-resonant nonce density onto PULVINI lanes deterministically.

    ``sample_size`` now selects a reproducible, evenly spaced nonce lattice
    instead of a pseudo-random draw.  The ``seed`` value is kept as a deterministic
    lattice phase so historical callers remain stable without introducing a
    simulation source.
    """
    import numpy as np

    sample_size = int(sample_size)
    if sample_size <= 0:
        raise ValueError("sample_size must be positive")

    nonce_space = int(getattr(compressor, "nonce_space_size", 2**32))
    stride = max(1, nonce_space // sample_size)
    phase = int(seed) % stride
    sample = (phase + np.arange(sample_size, dtype=np.uint64) * np.uint64(stride)) % np.uint64(nonce_space)
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

    non_identical_lane_measure = bool(
        variance_to_sampling_ratio >= float(variance_ratio_threshold)
        or d_i_delta >= float(d_i_delta_threshold)
        or reject_uniform_lane_null_p_0_05
    )
    geometric_structure_detected = bool(non_identical_lane_measure)

    return {
        "source": "deterministic_evenly_spaced_nonce_lattice",
        "sample_size": sample_size,
        "lattice_stride": int(stride),
        "lattice_phase": int(phase),
        "phi_acceptance_ratio": overall_ratio,
        "phi_rejection_ratio": float(1.0 - overall_ratio),
        "filter_advantage": float(1.0 / max(overall_ratio, np.finfo(float).eps)),
        "d_node_phi_ratio_avg": d_node_avg,
        "i_node_phi_ratio_avg": i_node_avg,
        "d_i_delta": d_i_delta,
        "lane_ratio_stddev": lane_stddev,
        "lane_ratio_variance": lane_variance,
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


__all__ = ["adjacency_map_digest", "automorphism_runtime_certificate", "phi_geometric_structure_certificate"]
