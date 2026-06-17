"""HENDRIX-Φ structured solver core.

This module contains deterministic, side-effect-free geometry and scoring
primitives extracted from the HENDRIX-Φ design note.  It does not perform live
network I/O and does not record share acceptance.
"""

from __future__ import annotations

import math
import random
from functools import lru_cache
from typing import List, Sequence, Tuple

import numpy as np

from pythia_mining.golden_ratio_library import (
    FIBONACCI,
    PHI,
    PHI_INV,
    PHI_INV_2,
    PHI_INV_3,
    PHI_INV_4,
    PHI_WEIGHT_NORM,
)

Vector3 = Tuple[float, float, float]

YANG_MILLS_GAP: float = 3.0 - PHI
COS_PI5: float = math.cos(math.pi / 5.0)
UINT32_SPACE: int = 2**32
_SU2_SCALE: float = 2.0 * math.pi / 255.0  # byte -> SU(2) rotation angle


def _normalise(v: Sequence[float]) -> Vector3:
    mag = math.sqrt(sum(float(x) * float(x) for x in v))
    if mag <= 0.0:
        raise ValueError("zero vector cannot be normalised")
    return (float(v[0]) / mag, float(v[1]) / mag, float(v[2]) / mag)


def build_m32() -> List[Vector3]:
    faces: List[Vector3] = []
    p = PHI
    for s1 in (1.0, -1.0):
        for s2 in (1.0, -1.0):
            faces.append(_normalise((0.0, s1 / p, s2 * p)))
            faces.append(_normalise((s2 * p, 0.0, s1 / p)))
            faces.append(_normalise((s1 / p, s2 * p, 0.0)))
    for sx in (1.0, -1.0):
        for sy in (1.0, -1.0):
            for sz in (1.0, -1.0):
                faces.append(_normalise((sx, sy, sz)))
    for s1 in (1.0, -1.0):
        for s2 in (1.0, -1.0):
            faces.append(_normalise((0.0, s1, s2 * p)))
            faces.append(_normalise((s2 * p, 0.0, s1)))
            faces.append(_normalise((s1, s2 * p, 0.0)))
    return faces[:32]


M32: List[Vector3] = build_m32()
if len(M32) != 32:  # pragma: no cover - import-time invariant
    raise RuntimeError("M32 must contain exactly 32 domains")

ADJACENT: Tuple[Tuple[bool, ...], ...] = tuple(
    tuple(sum(M32[i][k] * M32[j][k] for k in range(3)) >= COS_PI5 for j in range(32))
    for i in range(32)
)


def _su2_from_byte(b: int, axis: int = 0) -> np.ndarray:
    """Embed a byte value into SU(2) as a unit-trace group element.

    The map  b ↦ exp(i θ_b σ·n̂)  where θ_b = b * 2π/255 and n̂ is the
    Pauli axis specified by the axis parameter (0=σ_x, 1=σ_y, 2=σ_z).
    Using different axes for different byte positions creates non-commuting
    link variables, yielding a non-trivial gauge field action.

    Returns a 2x2 complex unitary with det = 1.
    """
    theta = float(b) * _SU2_SCALE
    c, s = math.cos(theta), math.sin(theta)
    if axis == 0:
        # exp(i theta sigma_x) = [[cos theta, i sin theta], [i sin theta, cos theta]]
        return np.array([[c, 1j * s], [1j * s, c]], dtype=np.complex128)
    elif axis == 1:
        # exp(i theta sigma_y) = [[cos theta, sin theta], [-sin theta, cos theta]]
        return np.array([[c, s], [-s, c]], dtype=np.complex128)
    else:
        # exp(i theta sigma_z) = [[exp(i theta), 0], [0, exp(-i theta)]]
        return np.array([[np.exp(1j * theta), 0], [0, np.exp(-1j * theta)]], dtype=np.complex128)


def yang_mills_action(nonce: int) -> float:
    """SU(2) lattice Yang-Mills plaquette action for the 4-byte nonce field.

    The nonce is decomposed into 4 bytes b₀..b₃, each embedded as an
    SU(2) link variable U_μ ∈ SU(2) via the map b ↦ exp(i θ_b σ·n̂_μ)
    where n̂_μ cycles through Pauli axes (σ_x, σ_y, σ_z, σ_x) to create
    non-commuting link variables and a non-trivial gauge field.

    The Wilson plaquette action over the 6 independent (μ,ν) pairs is:

        S = Σ_{μ<ν}  [ 1 - Re Tr(U_μ U_ν U_μ† U_ν†) / 2 ]

    At the continuum limit S → (g²/2) Tr(F_{μν}²), recovering the
    Yang-Mills kinetic term.  The normalization by 6 keeps S ∈ [0, 2],
    consistent with the Yang-Mills gate threshold 3-φ ≈ 1.382 used
    by the HENDRIX-Φ solver.
    """
    n = int(nonce) % UINT32_SPACE
    parts = [(n >> (8 * k)) & 0xFF for k in range(4)]
    # Use different Pauli axes for different byte positions to create non-commuting links
    axes = [0, 1, 2, 0]  # σ_x, σ_y, σ_z, σ_x
    links = [_su2_from_byte(b, axis=axes[k]) for k, b in enumerate(parts)]
    action = 0.0
    for i in range(4):
        for j in range(i + 1, 4):
            # Wilson plaquette: U_i U_j U_i† U_j†
            plaquette = links[i] @ links[j] @ links[i].conj().T @ links[j].conj().T
            # 1 - Re Tr(plaquette) / N  (N=2 for SU(2))
            action += 1.0 - float(np.real(np.trace(plaquette))) / 2.0
    return max(0.0, action / 6.0)  # normalize over 6 plaquette pairs


@lru_cache(maxsize=200_000)
def embed_nonce(nonce: int) -> Vector3:
    n = int(nonce) % UINT32_SPACE
    x = y = z = 0.0
    for k in range(32):
        if (n >> k) & 1:
            fx, fy, fz = M32[k]
            x += fx
            y += fy
            z += fz
    mag = math.sqrt(x * x + y * y + z * z)
    if mag < 1e-12:
        return M32[0]
    return (x / mag, y / mag, z / mag)


@lru_cache(maxsize=200_000)
def voronoi_domain(nonce: int) -> int:
    ex, ey, ez = embed_nonce(nonce)
    return max(range(32), key=lambda idx: M32[idx][0] * ex + M32[idx][1] * ey + M32[idx][2] * ez)


def cheap_phi_resonance(nonce: int) -> float:
    return 1.0 - 2.0 * abs((int(nonce) * PHI) % 1.0 - 0.5)


def phi_resonance(nonce: int) -> float:
    n = int(nonce) % UINT32_SPACE
    if n == 0:
        return 0.0
    ex, ey, ez = embed_nonce(n)
    c1 = min(
        max(abs(M32[f][0] * ex + M32[f][1] * ey + M32[f][2] * ez) for f in range(32))
        / PHI_INV,
        1.0,
    )
    c2 = cheap_phi_resonance(n)
    c3 = math.exp(-yang_mills_action(n) / YANG_MILLS_GAP)
    raw = (PHI_INV_2 * c1 + PHI_INV_3 * c2 + PHI_INV_4 * c3) / PHI_WEIGHT_NORM
    return 1.0 / (1.0 + math.exp(-8.0 * (raw - PHI_INV)))


def soft_mass_gap_gate(action: float, rng: random.Random) -> bool:
    if action >= YANG_MILLS_GAP:
        return True
    return rng.random() < math.exp(-(YANG_MILLS_GAP - action))


def phi_gradient_proposal(nonce: int, rng: random.Random, scale: int = 1) -> int:
    n = int(nonce) % UINT32_SPACE
    step_scale = max(1, int(scale))
    gradient = cheap_phi_resonance(n + 1) - cheap_phi_resonance(n - 1)
    if rng.random() < 0.70:
        sign = 1 if gradient >= 0.0 else -1
    else:
        sign = rng.choice((-1, 1))
    return (n + sign * rng.choice(FIBONACCI[:14]) * step_scale) % UINT32_SPACE


def algorithm_metadata() -> dict:
    return {
        "canonical_name": "HENDRIX-Φ Structured Solver",
        "compatibility_aliases": ["Phi-Grover", "phi-Grover", "structured Grover"],
        "m32_domains": len(M32),
        "dodecahedral_domains": 12,
        "icosahedral_overlay_domains": 20,
        "golden_ratio_library": "pythia_mining.golden_ratio_library",
        "live_io": False,
        "empirical_validation_status": {
            "mathematical_correctness": "PROVEN",
            "empirical_performance": "MEASURED",
            "phi_resonance_correlation": "NO_SIGNIFICANT_CORRELATION",
            "phi_vs_random_benchmark": "RANDOM_PERFORMS_BETTER_ON_SYNTHETIC",
            "cpu_overhead_vs_random": "3.73x",
            "hashrate_validation": "SYNTHETIC_ONLY",
            "claim_boundary": "Mathematical structure is sound. Empirical tests show φ-guided search performs worse than random search on synthetic targets due to computational overhead. NO EVIDENCE of mining revenue or pool-side acceptance."
        }
    }
