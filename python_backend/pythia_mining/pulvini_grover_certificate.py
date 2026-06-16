"""Grover search scope certificate for PULVINI.

This module provides a mathematically precise certificate that documents exactly
what the Grover iteration operates on — the 20-state dodecahedral basis — versus
the full uint32 nonce space (2^32 states). This prevents confusion between
"quantum speedup over classical brute force" (which this is not) and
"structurally-guided basis selection with deterministic projection"
(which this is).

The key contract:

    Grover amplifies over N=20 basis states (dodecahedron vertices).
    The marked state index is a deterministic function of target ^ range_fingerprint.
    The measured basis index is projected back into configured nonce ranges.
    No quantum speedup over SHA-256 preimage search is claimed or implied.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple

DODECAHEDRON_VERTICES = 20
NONCE_SPACE = 2**32
GROVER_THEORETICAL_STEPS_FACTOR = 4.0  # floor(pi/4 * sqrt(N/M))


@dataclass(frozen=True)
class GroverScopeCertificate:
    """Precise documentation of what the Grover iteration covers.

    Attributes:
        basis_dimension: Number of basis states in the dodecahedral search space.
        nonce_space_size: Total uint32 nonce space (2^32).
        search_space_size: Configured nonce search subrange (<= 2^32).
        basis_to_nonce_ratio: nonce_space_size / basis_dimension.
        grover_theoretical_steps: floor(pi/4 * sqrt(basis_dimension / marked_states)).
        actual_iterations: Number of Grover iterations actually run.
        basis_selection_method: How the 20 marked basis states are resolved.
        projection_method: How basis index maps to a nonce.
        quantum_speedup_claimed: False — no quantum speedup over SHA-256.
        deterministic_behavior: True — same config yields same nonce candidate.
        scope_statement: Human-readable summary of what the certificate means.
    """

    basis_dimension: int
    nonce_space_size: int
    search_space_size: int
    basis_to_nonce_ratio: float
    grover_theoretical_steps: int
    actual_iterations: int
    basis_selection_method: str
    projection_method: str
    quantum_speedup_claimed: bool
    deterministic_behavior: bool
    scope_statement: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def grover_scope_certificate(
    target: int,
    nonce_ranges: List[Tuple[int, int]],
    *,
    basis_dimension: int = DODECAHEDRON_VERTICES,
    marked_states: int = 1,
    actual_iterations: Optional[int] = None,
) -> GroverScopeCertificate:
    """Return a scope certificate for the Grover search configuration.

    Args:
        target: The pool target (determines marked state index).
        nonce_ranges: Configured nonce ranges.
        basis_dimension: Number of basis states (default 20).
        marked_states: Number of marked states (default 1).
        actual_iterations: Actual iterations run (None = use theoretical).

    Returns:
        A GroverScopeCertificate documenting exact search scope.
    """
    import math

    search_space_size = sum((end - start + 1) for start, end in nonce_ranges)
    basis_to_nonce_ratio = float(NONCE_SPACE) / float(basis_dimension)
    theoretical_steps = int(
        math.floor((math.pi / 4.0) * math.sqrt(float(basis_dimension) / max(1, marked_states)))
    )
    if actual_iterations is None:
        actual_iterations = min(100, theoretical_steps)

    # How the marked state index is derived
    range_fingerprint = sum((start * 31 + end * 17) for start, end in nonce_ranges)
    marked_index = int((target ^ range_fingerprint) % basis_dimension)

    scope_statement = (
        f"Grover amplification operates on {basis_dimension}-state dodecahedral basis. "
        f"Marked state index {marked_index} is a deterministic function of target and nonce-ranges. "
        f"Theoretical optimal iterations = {theoretical_steps}, actual = {actual_iterations}. "
        f"Measured basis index is projected into {search_space_size} nonce candidates. "
        f"No quantum speedup over SHA-256 preimage search is claimed. "
        f"This is a structurally-guided nonce selection mechanism, not a brute-force accelerator."
    )

    return GroverScopeCertificate(
        basis_dimension=basis_dimension,
        nonce_space_size=NONCE_SPACE,
        search_space_size=search_space_size,
        basis_to_nonce_ratio=basis_to_nonce_ratio,
        grover_theoretical_steps=theoretical_steps,
        actual_iterations=actual_iterations,
        basis_selection_method=(
            f"Deterministic marked state: index = (target ^ sum((start*31 + end*17))) % {basis_dimension}"
        ),
        projection_method=(
            "Basis index resolves to nonce via offset % search_space_size, "
            "then iterates nonce_ranges to find containing range."
        ),
        quantum_speedup_claimed=False,
        deterministic_behavior=True,
        scope_statement=scope_statement,
    )


def grover_efficiency_report(
    basis_dimension: int = DODECAHEDRON_VERTICES,
    nonce_space_size: int = NONCE_SPACE,
) -> Dict[str, Any]:
    """Return a side-by-side efficiency comparison framed honestly.

    This prevents any reader from thinking the N=20 Grover loop
    provides a meaningful advantage over 2^32 brute force.
    """
    import math

    grover_steps_20 = int(math.floor((math.pi / 4.0) * math.sqrt(20.0)))
    grover_steps_full = int(math.floor((math.pi / 4.0) * math.sqrt(float(nonce_space_size))))
    classical_steps_full = nonce_space_size

    return {
        "analysis_type": "grover_efficiency_comparison",
        "basis_dimension": basis_dimension,
        "grover_theoretical_steps_for_basis": grover_steps_20,
        "grover_theoretical_steps_for_full_2_32": grover_steps_full,
        "classical_brute_force_steps_for_full_2_32": classical_steps_full,
        "grover_basis_to_full_steps_ratio": f"1:{max(1, grover_steps_full // max(1, grover_steps_20))}",
        "grover_basis_to_classical_ratio": f"1:{max(1, classical_steps_full // max(1, grover_steps_20))}",
        "interpretation": (
            f"Grover on N=20 requires ~{grover_steps_20} iterations. "
            f"Grover on N=2^32 would require ~{grover_steps_full} iterations. "
            f"Classical brute force requires ~{classical_steps_full} steps. "
            f"The PULVINI system uses N=20 basis states, which is a ~"
            f"{max(1, grover_steps_full // max(1, grover_steps_20))}x step reduction versus "
            f"full Grover — but this is a BASIS SELECTION mechanism, not a SHA-256 acceleration. "
            f"The actual hash verification (double-SHA256) is still performed classically."
        ),
        "honest_claim": (
            "Structurally-guided nonce selection using dodecahedral symmetry. "
            "No quantum speedup over SHA-256 preimage search."
        ),
    }


__all__ = [
    "GroverScopeCertificate",
    "grover_scope_certificate",
    "grover_efficiency_report",
]
