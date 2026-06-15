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

_YM_SCALE = 2.0 * math.pi / PHI / 255.0
CURVATURE_TABLE: Tuple[Tuple[float, ...], ...] = tuple(
    tuple(
        ((_i * _YM_SCALE) - (_j * _YM_SCALE)) ** 2
        + ((_i * _YM_SCALE) * (_j * _YM_SCALE)) ** 2
        for _j in range(256)
    )
    for _i in range(256)
)


def yang_mills_action(nonce: int) -> float:
    n = int(nonce) % UINT32_SPACE
    parts = [(n >> (8 * k)) & 0xFF for k in range(4)]
    return sum(CURVATURE_TABLE[parts[i]][parts[j]] for i in range(4) for j in range(i + 1, 4))


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
    }
