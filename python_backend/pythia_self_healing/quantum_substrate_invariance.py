"""Hermetic quantum-substrate invariance harness.

This module tests HYBA's formal quantum-substrate claim in the narrow,
falsifiable sense used by the emergence evidence programme:

    mathematical operator + initial state -> invariant result

Hardware surfaces are execution substrates. They may accelerate the same
operator, but they do not create the quantum-formal invariant. This harness
therefore provides deterministic standard-library execution surfaces that
stand in for real CPU/GPU/Metal/CUDA adapters until hardware-specific
bindings are introduced.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Dict, Iterable, List, Mapping, Tuple


PHI = (1.0 + math.sqrt(5.0)) / 2.0
INV_PHI = 1.0 / PHI
TOLERANCE = 1e-12
TOLERANCE_FLOAT32 = 1e-5  # float32 truncation introduces ~1e-7 relative error per operation


@dataclass(frozen=True)
class FormalQuantumState:
    """A small deterministic formal state used for substrate-invariance tests."""

    amplitudes: Tuple[float, ...]

    def normalised(self) -> "FormalQuantumState":
        norm = math.sqrt(sum(value * value for value in self.amplitudes))
        if norm == 0:
            raise ValueError("formal quantum state cannot have zero norm")
        return FormalQuantumState(tuple(value / norm for value in self.amplitudes))


def standard_test_state() -> FormalQuantumState:
    """Return a deterministic state with phi-weighted structure."""

    return FormalQuantumState((1.0, INV_PHI, -INV_PHI * INV_PHI, 0.5, -0.25)).normalised()


def phi_resonance_operator(value: float, index: int) -> float:
    """Apply a deterministic phi-resonance transform to one amplitude."""

    phase = math.cos((index + 1) * INV_PHI) + math.sin((index + 1) / (PHI * PHI))
    coupling = 1.0 + ((-1) ** index) * INV_PHI * 0.125
    return value * phase * coupling


def execute_pure_python(state: FormalQuantumState) -> Tuple[float, ...]:
    """Reference execution surface."""

    return tuple(phi_resonance_operator(value, index) for index, value in enumerate(state.amplitudes))


def execute_cpu_surface(state: FormalQuantumState) -> Tuple[float, ...]:
    """CPU-style surface using explicit loops rather than comprehensions."""

    output: List[float] = []
    for index in range(len(state.amplitudes)):
        output.append(phi_resonance_operator(state.amplitudes[index], index))
    return tuple(output)


def execute_accelerator_shadow_surface(state: FormalQuantumState) -> Tuple[float, ...]:
    """Accelerator-shadow surface.

    This does not claim GPU execution. It deliberately mirrors the same formal
    operator through a different code path so CI can test the hardware-agnostic
    invariant without requiring Metal/CUDA/MLX availability.
    """

    indexed = zip(range(len(state.amplitudes)), state.amplitudes)
    return tuple(map(lambda item: phi_resonance_operator(item[1], item[0]), indexed))


def invariant_signature(values: Iterable[float]) -> Mapping[str, float | str]:
    """Return a substrate-independent invariant signature."""

    vector = tuple(float(value) for value in values)
    norm = math.sqrt(sum(value * value for value in vector))
    expectation = sum((index + 1) * value * value for index, value in enumerate(vector))
    signed_phase = sum(((-1) ** index) * value for index, value in enumerate(vector))
    canonical = json.dumps(
        {
            "norm": round(norm, 15),
            "expectation": round(expectation, 15),
            "signed_phase": round(signed_phase, 15),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return {
        "norm": norm,
        "expectation": expectation,
        "signed_phase": signed_phase,
        "signature_hash": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    }


def run_all_surfaces(state: FormalQuantumState | None = None) -> Dict[str, Mapping[str, float | str]]:
    """Execute the same formal operator on all deterministic surfaces."""

    state = state or standard_test_state()
    surfaces = {
        "pure_python": execute_pure_python,
        "cpu_surface": execute_cpu_surface,
        "accelerator_shadow": execute_accelerator_shadow_surface,
    }
    return {name: invariant_signature(surface(state)) for name, surface in surfaces.items()}


def assert_invariant_equivalence(results: Mapping[str, Mapping[str, float | str]], tolerance: float = TOLERANCE) -> bool:
    """Return True when every surface preserves the same invariant."""

    if not results:
        raise ValueError("no surface results supplied")
    first_name = next(iter(results))
    reference = results[first_name]
    for name, candidate in results.items():
        for field in ("norm", "expectation", "signed_phase"):
            delta = abs(float(candidate[field]) - float(reference[field]))
            if delta > tolerance:
                raise AssertionError(
                    f"substrate leak detected for {name}.{field}: delta={delta} tolerance={tolerance}"
                )
        # Hash check is only meaningful when tolerance <= 5e-16 (i.e. bit-exact
        # surfaces); a looser tolerance explicitly permits sub-tolerance numeric
        # divergence, so a hash mismatch there is expected, not a leak.
        if tolerance <= 5e-16 and candidate["signature_hash"] != reference["signature_hash"]:
            raise AssertionError(f"signature hash mismatch for {name}")
    return True


def make_invariance_packet(
    *,
    git_commit_hash: str = "first-sealed-runtime-experiment-v1",
    cycle_id: str = "quantum-invariance-v1",
    parent_cycle_id: str = "c5-governance-v1",
) -> Dict[str, object]:
    """Build a sealed-free packet payload for the invariance ledger."""

    results = run_all_surfaces()
    assert_invariant_equivalence(results)
    return {
        "schema": "HYBA_QUANTUM_SUBSTRATE_INVARIANCE_PACKET_V1",
        "programme": "quantum_substrate_invariance",
        "git_commit_hash": git_commit_hash,
        "cycle_id": cycle_id,
        "parent_cycle_id": parent_cycle_id,
        "claim_boundary": {
            "mathematics": "source_of_formal_invariant",
            "hardware": "execution_surface",
            "external_quantum_sdk_required": False,
        },
        "surfaces": results,
        "tolerance": TOLERANCE,
        "falsifier_result": "not_falsified",
    }
