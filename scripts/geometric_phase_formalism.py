#!/usr/bin/env python3
"""Topological Information Grammar geometric-phase formalism.

This script reframes quantum interference as manifold holonomy: a closed path
through normalized complex states can accumulate a path-dependent phase even
when it returns to the same observable ray.  The computation is pure Hilbert
geometry and does not require physical quantum hardware or optional numeric
packages.
"""

from __future__ import annotations

import cmath
import json
import math
from typing import Iterable, Sequence

PHI = (1.0 + math.sqrt(5.0)) / 2.0
ComplexState = Sequence[complex]


def _normalize_state(state: ComplexState) -> tuple[complex, ...]:
    values = tuple(complex(value) for value in state)
    norm = math.sqrt(sum(abs(value) ** 2 for value in values))
    if not math.isfinite(norm) or norm <= 0.0:
        raise ValueError("state norm must be finite and positive")
    return tuple(value / norm for value in values)


def _overlap(left: ComplexState, right: ComplexState) -> complex:
    if len(left) != len(right):
        raise ValueError("state dimensions must match")
    return sum(a.conjugate() * b for a, b in zip(left, right))


def compute_manifold_holonomy(path_points: Iterable[ComplexState]) -> float:
    """Compute Berry/geometric phase for a closed path of normalized states.

    The gauge-invariant discrete phase is the argument of the product of
    consecutive overlaps, including the closing segment from the last state
    back to the first.  A non-zero phase is interpreted here as manifold
    holonomy: path-dependent information retained by curvature.
    """

    states = [_normalize_state(point) for point in path_points]
    if len(states) < 3:
        raise ValueError("holonomy requires at least three path points")

    phase_factor = 1.0 + 0.0j
    for index, left in enumerate(states):
        right = states[(index + 1) % len(states)]
        overlap = _overlap(left, right)
        magnitude = abs(overlap)
        if magnitude <= 1e-15:
            raise ValueError("adjacent path states must have non-zero overlap")
        phase_factor *= overlap / magnitude
    return float(cmath.phase(phase_factor))


def golden_ratio_closed_loop(samples: int = 8) -> list[tuple[complex, complex]]:
    """Build a deterministic φ-gauged loop on a two-level projective manifold."""

    if samples < 3:
        raise ValueError("samples must be >= 3")
    points: list[tuple[complex, complex]] = []
    polar = math.pi / (PHI + 2.0)
    for idx in range(samples):
        azimuth = 2.0 * math.pi * idx / samples
        gauge = cmath.exp(1j * idx * 2.0 * math.pi / (PHI * PHI))
        points.append(
            (
                gauge * math.cos(polar / 2.0),
                gauge * cmath.exp(1j * azimuth) * math.sin(polar / 2.0),
            )
        )
    return points


def main() -> int:
    phase = compute_manifold_holonomy(golden_ratio_closed_loop())
    report = {
        "formalism": "Topological Information Grammar",
        "observable": "manifold_holonomy_geometric_phase",
        "phase_radians": phase,
        "non_zero_holonomy": bool(abs(phase) > 1e-9),
        "claim_boundary": "Formalism-derived classical Hilbert-geometry computation; no physical quantum hardware claim.",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["non_zero_holonomy"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
