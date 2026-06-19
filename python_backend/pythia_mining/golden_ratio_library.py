"""Deterministic golden-ratio math primitives."""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Iterable, List

PHI: float = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV: float = PHI - 1.0
PHI_INV_2: float = PHI**-2
PHI_INV_3: float = PHI**-3
PHI_INV_4: float = PHI**-4
PHI_WEIGHT_NORM: float = PHI_INV_2 + PHI_INV_3 + PHI_INV_4

FIBONACCI: tuple[int, ...] = (
    1,
    2,
    3,
    5,
    8,
    13,
    21,
    34,
    55,
    89,
    144,
    233,
    377,
    610,
    987,
    1597,
    2584,
    4181,
    6765,
    10946,
    17711,
    28657,
    46368,
    75025,
    121393,
    196418,
)

LUCAS: tuple[int, ...] = (
    2,
    1,
    3,
    4,
    7,
    11,
    18,
    29,
    47,
    76,
    123,
    199,
    322,
    521,
    843,
    1364,
    2207,
    3571,
    5778,
    9349,
    15127,
    24476,
    39603,
    64079,
    103682,
)

CONTROL_CONSTANTS: tuple[float, ...] = (PHI, math.pi, math.e, math.sqrt(2.0), 1.0)


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def canonical_sha256(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def normalize(values: Iterable[float]) -> List[float]:
    raw = [max(0.0, float(value)) for value in values]
    total = sum(raw)
    if total <= 0.0:
        raise ValueError("cannot normalize an all-zero vector")
    return [value / total for value in raw]


def inverse_phi_distribution(size: int) -> List[float]:
    if size <= 0:
        raise ValueError("size must be positive")
    return normalize(PHI**-idx for idx in range(size))


def lucas_ratio_tail(length: int = 10) -> List[float]:
    if length <= 0 or length >= len(LUCAS):
        raise ValueError("length must be between 1 and len(LUCAS)-1")
    start = len(LUCAS) - length - 1
    return [LUCAS[i + 1] / LUCAS[i] for i in range(start, len(LUCAS) - 1)]
