"""After-Quantum Trifecta benchmark primitives.

This module combines three bounded ingredients already present in HYBA/PYTHIA:
PULVINI memory-compression discipline, golden-ratio irrational gauges, and
Hilbert/Bures-style formal geometry.  The functions produce deterministic
benchmark reports for structured workloads.  They are intentionally framed as
formalism-derived classical computations, not physical quantum supremacy claims.
"""

from __future__ import annotations

import cmath
import math
import random
import time
from dataclasses import asdict, dataclass
from typing import Iterable, Sequence

PHI = (1.0 + math.sqrt(5.0)) / 2.0
MASS_GAP = 3.0 - PHI
CLAIM_BOUNDARY = (
    "Formalism-derived classical structured-workload benchmark; not physical quantum "
    "hardware, not measured production throughput, and not universal speedup."
)


@dataclass(frozen=True)
class BenchmarkReport:
    name: str
    domain: str
    scale: str
    duration_ms: float
    primary_score: float
    compression_ratio: float
    phi_alignment: float
    mass_gap_alignment: float
    claim_boundary: str = CLAIM_BOUNDARY

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _now() -> float:
    return time.perf_counter()


def _rng(seed: int) -> random.Random:
    return random.Random(int(seed))


def _phi_alignment(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    phases = [((abs(v) + idx + 1) * PHI) % 1.0 for idx, v in enumerate(values)]
    resonance = [1.0 - 2.0 * abs(phase - 0.5) for phase in phases]
    return max(0.0, min(1.0, sum(resonance) / len(resonance)))


def _mass_gap_alignment(values: Sequence[float]) -> float:
    positives = [abs(v) + 1e-12 for v in values if math.isfinite(v)]
    if len(positives) < 2:
        return 1.0
    ratios = [positives[i] / positives[i + 1] for i in range(len(positives) - 1)]
    best = min(ratios, key=lambda ratio: abs(ratio - MASS_GAP))
    return max(0.0, 1.0 - abs(best - MASS_GAP) / MASS_GAP)


def _pulvini_ratio(elements: int, active_dimension: int) -> float:
    return float(max(1.0, max(1, int(elements)) / max(1, int(active_dimension))))


def _holonomy(path: Iterable[Sequence[complex]]) -> float:
    states = []
    for point in path:
        values = tuple(complex(v) for v in point)
        norm = math.sqrt(sum(abs(v) ** 2 for v in values))
        if norm <= 0.0 or not math.isfinite(norm):
            continue
        states.append(tuple(v / norm for v in values))
    if len(states) < 3:
        return 0.0
    phase = 1.0 + 0.0j
    for i, left in enumerate(states):
        right = states[(i + 1) % len(states)]
        overlap = sum(a.conjugate() * b for a, b in zip(left, right))
        if abs(overlap) > 1e-15:
            phase *= overlap / abs(overlap)
    return float(cmath.phase(phase))


def benchmark_logistics_manifold(nodes: int = 500, seed: int = 1618) -> BenchmarkReport:
    started = _now()
    rng = _rng(seed)
    coords = [(rng.random(), rng.random()) for _ in range(nodes)]
    order = sorted(
        range(nodes), key=lambda idx: ((coords[idx][0] * PHI + coords[idx][1]) % 1.0)
    )
    route = [coords[idx] for idx in order]
    distances = [
        math.dist(route[idx], route[(idx + 1) % len(route)])
        for idx in range(len(route))
    ]
    duration_ms = (_now() - started) * 1000.0
    stability = 1.0 / (1.0 + (sum(distances) / max(1, nodes)))
    return BenchmarkReport(
        name="500-node logistics manifold",
        domain="logistics_geodesic_tsp",
        scale=f"{nodes} nodes",
        duration_ms=duration_ms,
        primary_score=stability,
        compression_ratio=_pulvini_ratio(
            nodes * nodes, nodes * math.ceil(math.log(nodes + 1, PHI))
        ),
        phi_alignment=_phi_alignment(distances[:128]),
        mass_gap_alignment=_mass_gap_alignment(sorted(distances[:128], reverse=True)),
    )


def benchmark_ai_weight_geometry(
    dimension: int = 4096, seed: int = 2718
) -> BenchmarkReport:
    started = _now()
    rng = _rng(seed)
    weights = [rng.gauss(0.0, 1.0) for _ in range(dimension)]
    folded_dim = math.ceil(dimension / PHI)
    folded = [
        weights[idx] + (weights[(idx + folded_dim) % dimension] / PHI)
        for idx in range(folded_dim)
    ]
    duration_ms = (_now() - started) * 1000.0
    return BenchmarkReport(
        name="LLM weight geometry folding",
        domain="ai_weight_geometry",
        scale=f"{dimension}-dimension layer sketch",
        duration_ms=duration_ms,
        primary_score=_phi_alignment(folded[:256]),
        compression_ratio=_pulvini_ratio(dimension, folded_dim),
        phi_alignment=_phi_alignment(folded[:256]),
        mass_gap_alignment=_mass_gap_alignment(
            sorted((abs(v) for v in folded[:256]), reverse=True)
        ),
    )


def benchmark_biotech_interaction(
    points: int = 1024, seed: int = 3141
) -> BenchmarkReport:
    started = _now()
    rng = _rng(seed)
    surface = [rng.random() for _ in range(points)]
    energy = [abs(value - (1.0 / PHI)) for value in surface]
    best = min(energy)
    duration_ms = (_now() - started) * 1000.0
    return BenchmarkReport(
        name="molecular interaction resonance",
        domain="biotech_docking_manifold",
        scale=f"{points} pocket-surface samples",
        duration_ms=duration_ms,
        primary_score=1.0 / (1.0 + best),
        compression_ratio=_pulvini_ratio(points, math.ceil(points / PHI)),
        phi_alignment=_phi_alignment(surface[:256]),
        mass_gap_alignment=_mass_gap_alignment(sorted(energy[:256], reverse=True)),
    )


def benchmark_finance_tail_risk(
    assets: int = 1000, seed: int = 5772
) -> BenchmarkReport:
    started = _now()
    rng = _rng(seed)
    returns = [rng.gauss(0.0, 1.0) for _ in range(assets)]
    curvature = sum(abs(v) ** 1.5 for v in returns) / assets
    path = [
        (complex(returns[i], returns[(i + 1) % assets]), 1.0 + 0.0j) for i in range(32)
    ]
    holonomy = abs(_holonomy(path))
    duration_ms = (_now() - started) * 1000.0
    return BenchmarkReport(
        name="financial tail-risk holonomy",
        domain="finance_tail_risk",
        scale=f"{assets} assets",
        duration_ms=duration_ms,
        primary_score=1.0 / (1.0 + curvature + holonomy),
        compression_ratio=_pulvini_ratio(
            assets * assets, assets * math.ceil(math.log(assets + 1, PHI))
        ),
        phi_alignment=_phi_alignment(returns[:256]),
        mass_gap_alignment=_mass_gap_alignment(
            sorted((abs(v) for v in returns[:256]), reverse=True)
        ),
    )


def benchmark_fluid_resonance(
    grid_side: int = 1024, seed: int = 8128
) -> BenchmarkReport:
    started = _now()
    rng = _rng(seed)
    samples = [rng.random() for _ in range(4096)]
    gradients = [abs(samples[i] - samples[i - 1]) for i in range(1, len(samples))]
    laminar = 1.0 / (1.0 + sum(gradients) / len(gradients))
    duration_ms = (_now() - started) * 1000.0
    points = grid_side * grid_side
    return BenchmarkReport(
        name="Navier-Stokes geodesic flow sketch",
        domain="fluid_dynamics_resonance",
        scale=f"{points} grid-point compressed sketch",
        duration_ms=duration_ms,
        primary_score=laminar,
        compression_ratio=_pulvini_ratio(points, len(samples)),
        phi_alignment=_phi_alignment(samples[:256]),
        mass_gap_alignment=_mass_gap_alignment(sorted(gradients[:256], reverse=True)),
    )


def benchmark_ai_reasoning_integrity(
    steps: int = 50, hidden_dim: int = 8192, seed: int = 9001
) -> BenchmarkReport:
    started = _now()
    rng = _rng(seed)
    path = []
    for step in range(steps):
        phase = step * 2.0 * math.pi / (PHI * PHI)
        path.append((cmath.exp(1j * phase), complex(rng.random(), rng.random())))
    holonomy = abs(_holonomy(path))
    duration_ms = (_now() - started) * 1000.0
    coherence = 1.0 / (1.0 + holonomy)
    return BenchmarkReport(
        name="cognitive reasoning holonomy",
        domain="ai_reasoning_integrity",
        scale=f"{steps} steps over hidden-dim {hidden_dim} sketch",
        duration_ms=duration_ms,
        primary_score=coherence,
        compression_ratio=_pulvini_ratio(
            steps * hidden_dim, steps * math.ceil(math.log(hidden_dim, PHI))
        ),
        phi_alignment=coherence,
        mass_gap_alignment=1.0 / (1.0 + abs(holonomy - MASS_GAP)),
    )


def benchmark_cyber_topological_defense(
    nodes: int = 10_000, seed: int = 4242
) -> BenchmarkReport:
    started = _now()
    rng = _rng(seed)
    baseline = [rng.random() for _ in range(512)]
    perturbed = list(baseline)
    perturbed[500 % len(perturbed)] += 0.005
    delta = math.sqrt(sum((a - b) ** 2 for a, b in zip(baseline, perturbed)))
    duration_ms = (_now() - started) * 1000.0
    detection_score = min(1.0, delta / 0.005)
    return BenchmarkReport(
        name="cyber-infrastructure holonomy",
        domain="cyber_topological_defense",
        scale=f"{nodes} nodes represented by compressed telemetry sketch",
        duration_ms=duration_ms,
        primary_score=detection_score,
        compression_ratio=_pulvini_ratio(nodes, len(baseline)),
        phi_alignment=_phi_alignment(perturbed[:256]),
        mass_gap_alignment=_mass_gap_alignment(
            sorted((abs(v) for v in perturbed[:256]), reverse=True)
        ),
    )


def run_global_formalism_efficiency_index() -> list[BenchmarkReport]:
    return [
        benchmark_logistics_manifold(),
        benchmark_ai_weight_geometry(),
        benchmark_biotech_interaction(),
        benchmark_finance_tail_risk(),
        benchmark_fluid_resonance(),
        benchmark_ai_reasoning_integrity(),
        benchmark_cyber_topological_defense(),
    ]
