"""Runtime causal tracer for emergence complexity-gradient perturbations.

This module implements observable-effect-free tracing of how local
perturbations in the quantum substrate propagate into macroscopic changes
in the complexity gradient. It uses the existing deterministic surfaces and
seal infrastructure so that tracing never introduces observer effects that
violate quantum_substrate_invariance invariants.

The core insight: if a perturbation of the phi-resonance operator at one
surface changes the complexity-gradient emergence_index by delta, and that
same perturbation applied at a different surface produces the same delta
within tolerance, then the substrate is causally transparent to that
perturbation.
"""

from __future__ import annotations

import json
import math
from typing import Dict, List, Mapping, Tuple

from python_backend.pythia_self_healing.complexity_gradient import (
    sweep_complexity,
    find_criticality_threshold,
)
from python_backend.pythia_self_healing.quantum_substrate_invariance import (
    FormalQuantumState,
    PHI,
    INV_PHI,
    standard_test_state,
    phi_resonance_operator,
    execute_pure_python,
    execute_cpu_surface,
    execute_accelerator_shadow_surface,
    invariant_signature,
    TOLERANCE,
)


def perturbed_phi_resonance(
    value: float, index: int, epsilon: float = 0.0
) -> float:
    """Apply phi-resonance with a controlled perturbation epsilon.

    When epsilon=0, this is identical to phi_resonance_operator.
    Perturbation is applied to the phase term only, preserving the
    algebraic structure of the operator.
    """
    phase = math.cos((index + 1) * INV_PHI) + math.sin((index + 1) / (PHI * PHI))
    phase += epsilon * math.sin((index + 1) * PHI)
    coupling = 1.0 + ((-1) ** index) * INV_PHI * 0.125
    return value * phase * coupling


def execute_perturbed_surfaces(
    state: FormalQuantumState | None = None,
    epsilon: float = 0.0,
) -> Dict[str, Mapping[str, float | str]]:
    """Execute all surfaces with a controlled perturbation applied to each.

    Returns surface signatures identical in structure to run_all_surfaces
    but with the perturbation active.
    """
    state = state or standard_test_state()

    def _perturbed_pure_python(s: FormalQuantumState) -> Tuple[float, ...]:
        return tuple(
            perturbed_phi_resonance(v, i, epsilon) for i, v in enumerate(s.amplitudes)
        )

    def _perturbed_cpu_surface(s: FormalQuantumState) -> Tuple[float, ...]:
        output: List[float] = []
        for i in range(len(s.amplitudes)):
            output.append(perturbed_phi_resonance(s.amplitudes[i], i, epsilon))
        return tuple(output)

    def _perturbed_accelerator_shadow(s: FormalQuantumState) -> Tuple[float, ...]:
        indexed = zip(range(len(s.amplitudes)), s.amplitudes)
        return tuple(
            map(lambda item: perturbed_phi_resonance(item[1], item[0], epsilon), indexed)
        )

    surfaces = {
        "pure_python": _perturbed_pure_python,
        "cpu_surface": _perturbed_cpu_surface,
        "accelerator_shadow": _perturbed_accelerator_shadow,
    }
    return {name: invariant_signature(surface(state)) for name, surface in surfaces.items()}


def trace_perturbation_propagation(
    epsilon: float = 0.01,
    reference_surface: str = "pure_python",
) -> Dict[str, object]:
    """Trace how a perturbation propagates across all surfaces.

    Returns a causal mapping showing delta in invariant signatures and
    complexity-gradient metrics for each surface.
    """
    # Baseline (unperturbed) signatures
    from python_backend.pythia_self_healing.quantum_substrate_invariance import run_all_surfaces

    baseline_surfaces = run_all_surfaces()
    perturbed_surfaces = execute_perturbed_surfaces(epsilon=epsilon)

    surface_deltas: Dict[str, Dict[str, float]] = {}
    for name in baseline_surfaces:
        delta: Dict[str, float] = {}
        for field in ("norm", "expectation", "signed_phase"):
            delta[field] = abs(
                float(perturbed_surfaces[name][field])
                - float(baseline_surfaces[name][field])
            )
        surface_deltas[name] = delta

    # Complexity-gradient effect of the perturbation
    from python_backend.pythia_self_healing.complexity_gradient import score_profile

    baseline_profile = {"memory_depth": 4, "graph_density": 0.35, "constraint_count": 3, "feedback_history": 2}
    baseline_scored = score_profile(baseline_profile)

    # Apply perturbation as a small shift to the profile parameters
    perturbed_profile = {
        "memory_depth": 4,
        "graph_density": min(0.35 + epsilon, 1.0),
        "constraint_count": 3,
        "feedback_history": 2,
    }
    perturbed_scored = score_profile(perturbed_profile)

    gradient_deltas: Dict[str, float] = {}
    for metric in baseline_scored:
        gradient_deltas[metric] = abs(
            perturbed_scored[metric] - baseline_scored[metric]
        )

    # Determine causal transparency: all surfaces should see the same delta
    # within tolerance
    norms = [surface_deltas[name]["norm"] for name in surface_deltas]
    transparent = max(norms) - min(norms) < TOLERANCE

    return {
        "schema": "HYBA_RUNTIME_CAUSAL_TRACE_V1",
        "programme": "runtime_causal_tracer",
        "epsilon": epsilon,
        "reference_surface": reference_surface,
        "surface_invariant_deltas": surface_deltas,
        "complexity_gradient_deltas": gradient_deltas,
        "causally_transparent": transparent,
        "causality_verdict": (
            "not_falsified"
            if transparent
            else "falsified — perturbation leaked across surfaces inconsistently"
        ),
    }


def trace_complexity_shift(
    depth_shift: int = 1,
) -> Dict[str, object]:
    """Trace how a memory_depth shift in the complexity gradient changes
    criticality threshold.

    This is a causal probe: does changing one parameter in the profile move
    the criticality point in a predictable, continuous way?
    """
    baseline_sweep = sweep_complexity(range(1, 21))
    baseline_threshold = find_criticality_threshold(baseline_sweep)

    shifted_sweep = sweep_complexity(range(1 + depth_shift, 21 + depth_shift))
    shifted_threshold = find_criticality_threshold(shifted_sweep)

    threshold_shift = int(shifted_threshold.get("criticality_threshold_at_depth", 0)) - int(
        baseline_threshold.get("criticality_threshold_at_depth", 0)
    )

    return {
        "schema": "HYBA_COMPLEXITY_TRACE_V1",
        "programme": "runtime_causal_tracer",
        "depth_shift": depth_shift,
        "baseline_threshold": baseline_threshold,
        "shifted_threshold": shifted_threshold,
        "threshold_shift": threshold_shift,
        "continuous": threshold_shift > 0,
        "trace_verdict": (
            "not_falsified — criticality tracks depth monotonically"
            if threshold_shift > 0
            else "falsified — criticality does not respond monotonically to depth"
        ),
    }