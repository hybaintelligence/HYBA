"""Substrate B — non-Euclidean high-entropy execution surface.

This provides a second substrate that is structurally distinct from the
phi-resonance substrate used in quantum_substrate_invariance. While Substrate A
(quantum_substrate_invariance) uses a phi-weighted algebraic structure on R^5,
Substrate B uses a hyperbolic embedding on R^7 with a different coupling
topology.

The invariance claim under test: if the formal invariant
(mathematical operator + initial state -> invariant result) is truly
substrate-independent, then the same test_state() piped through Substrate B's
operator should produce the same invariant_class within tolerance as Substrate A.

This substrate is deliberately non-Euclidean in the sense that its amplitude
dynamics use a hyperbolic tangent phase space rather than a compact rotation,
making it a materially different execution context.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Dict, List, Mapping, Tuple

from python_backend.pythia_self_healing.quantum_substrate_invariance import (
    FormalQuantumState,
    PHI,
    INV_PHI,
    TOLERANCE,
    TOLERANCE_FLOAT32,
    invariant_signature,
    assert_invariant_equivalence,
    standard_test_state,
)


# Hyperbolic basis parameters — structurally different from phi-resonance
HYPERBOLIC_CURVATURE = -1.0 / (PHI * PHI)
HYPERBOLIC_DIMENSIONS = 7


def hyperbolic_test_state() -> FormalQuantumState:
    """Return a deterministic state on the hyperbolic substrate.

    Uses a different seed structure than standard_test_state to ensure
    the substrates are genuinely distinct.
    """
    raw: Tuple[float, ...] = (
        1.0,
        PHI * 0.5,
        -INV_PHI * 0.75,
        0.5,
        -0.25,
        PHI * 0.125,
        -INV_PHI * 0.375,
    )
    norm = math.sqrt(sum(v * v for v in raw))
    return FormalQuantumState(tuple(v / norm for v in raw))


def hyperbolic_operator(value: float, index: int) -> float:
    """Apply a hyperbolic-entangled operator to one amplitude.

    This uses tanh() for phase accumulation rather than sin/cos,
    creating a non-Euclidean response topology.
    """
    phase = math.tanh((index + 1) * HYPERBOLIC_CURVATURE) + math.atanh(
        min(0.99, (index + 1) * INV_PHI * 0.5)
    )
    coupling = 1.0 + ((-1) ** index) * 0.15 * math.tanh(index * PHI)
    return value * phase * coupling


def execute_hyperbolic_python(state: FormalQuantumState) -> Tuple[float, ...]:
    """Reference execution surface for Substrate B."""
    return tuple(hyperbolic_operator(v, i) for i, v in enumerate(state.amplitudes))


def execute_hyperbolic_cpu(state: FormalQuantumState) -> Tuple[float, ...]:
    """CPU-style loop surface for Substrate B."""
    output: List[float] = []
    for i in range(len(state.amplitudes)):
        output.append(hyperbolic_operator(state.amplitudes[i], i))
    return tuple(output)


def execute_hyperbolic_shadow(state: FormalQuantumState) -> Tuple[float, ...]:
    """Accelerator shadow surface for Substrate B."""
    indexed = zip(range(len(state.amplitudes)), state.amplitudes)
    return tuple(map(lambda item: hyperbolic_operator(item[1], item[0]), indexed))


def run_substrate_b_all_surfaces(
    state: FormalQuantumState | None = None,
) -> Dict[str, Mapping[str, float | str]]:
    """Execute Substrate B's operator on all its deterministic surfaces."""
    state = state or hyperbolic_test_state()
    surfaces = {
        "hyperbolic_python": execute_hyperbolic_python,
        "hyperbolic_cpu": execute_hyperbolic_cpu,
        "hyperbolic_shadow": execute_hyperbolic_shadow,
    }
    return {name: invariant_signature(surface(state)) for name, surface in surfaces.items()}


def run_dual_substrate_invariance_test(
    tolerance: float = TOLERANCE_FLOAT32,
) -> Dict[str, object]:
    """Run the cross-substrate invariance test.

    This proves that Substrate A (phi-resonance) and Substrate B (hyperbolic)
    produce the same invariant class for their respective states when measured
    through the same invariant_signature function.

    The invariance is checked at float32 tolerance because the two substrates
    use structurally different operators — exact bit-identity is not expected,
    but invariant equivalence (same norm, expectation, phase structure) is.
    """
    # Substrate A
    from python_backend.pythia_self_healing.quantum_substrate_invariance import (
        run_all_surfaces as run_substrate_a,
    )

    substrate_a = run_substrate_a(standard_test_state())
    substrate_b = run_substrate_b_all_surfaces(hyperbolic_test_state())

    # Within substrate: each surface must agree with itself
    a_verified = True
    try:
        assert_invariant_equivalence(substrate_a, tolerance=tolerance)
    except AssertionError:
        a_verified = False

    b_verified = True
    try:
        assert_invariant_equivalence(substrate_b, tolerance=tolerance)
    except AssertionError:
        b_verified = False

    # Cross-substrate invariance: compare the reference signatures
    a_ref = substrate_a["pure_python"]
    b_ref = substrate_b["hyperbolic_python"]

    cross_deltas = {}
    for field in ("norm", "expectation", "signed_phase"):
        cross_deltas[field] = abs(float(a_ref[field]) - float(b_ref[field]))

    cross_verified = all(
        cross_deltas[field] < tolerance for field in cross_deltas
    )

    return {
        "schema": "HYBA_DUAL_SUBSTRATE_INVARIANCE_V1",
        "programme": "cross_substrate_parity",
        "tolerance": tolerance,
        "substrate_a_self_consistent": a_verified,
        "substrate_b_self_consistent": b_verified,
        "cross_substrate_deltas": cross_deltas,
        "cross_substrate_invariant": cross_verified,
        "falsifier_result": (
            "not_falsified"
            if (a_verified and b_verified and cross_verified)
            else "falsified — cross-substrate invariant leak detected"
        ),
    }