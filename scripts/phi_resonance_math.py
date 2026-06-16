#!/usr/bin/env python3
"""Phi resonance math helpers for HYBA_FULLSTACK elevation checks."""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Dict, Iterable, List

PHI = (1.0 + math.sqrt(5.0)) / 2.0
INV_PHI = 1.0 / PHI
CONSTANTS = {
    "phi": PHI,
    "pi": math.pi,
    "e": math.e,
    "sqrt2": math.sqrt(2.0),
    "uniform": 1.0,
}


def canonical_bytes(payload: Dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def forensic_hash(payload: Dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("forensic_sha256", None)
    return hashlib.sha256(canonical_bytes(unsigned)).hexdigest()


def normalize(values: Iterable[float]) -> List[float]:
    raw = [max(0.0, float(value)) for value in values]
    total = sum(raw)
    if total <= 0.0:
        return [1.0 / len(raw) for _ in raw]
    return [value / total for value in raw]


def inverse_power_distribution(constant: float, size: int = 13) -> List[float]:
    if abs(constant - 1.0) < 1e-12:
        return [1.0 / size for _ in range(size)]
    return normalize(constant ** (-index) for index in range(size))


def lucas_phi_ratios(count: int = 12) -> List[float]:
    lucas = [2.0, 1.0]
    while len(lucas) < count + 2:
        lucas.append(lucas[-1] + lucas[-2])
    return [lucas[index + 1] / lucas[index] for index in range(1, count + 1)]


def l1_similarity(left: Iterable[float], right: Iterable[float]) -> float:
    left_values = list(left)
    right_values = list(right)
    distance = sum(abs(a - b) for a, b in zip(left_values, right_values))
    return max(0.0, 1.0 - distance / 2.0)


def constant_scoreboard(target: List[float]) -> Dict[str, float]:
    return {
        name: l1_similarity(inverse_power_distribution(value, size=len(target)), target)
        for name, value in CONSTANTS.items()
    }


def phi_structured_scoreboard(size: int = 13) -> Dict[str, float]:
    return constant_scoreboard(inverse_power_distribution(PHI, size=size))


def uniform_noise_scoreboard(size: int = 13) -> Dict[str, float]:
    return constant_scoreboard(inverse_power_distribution(1.0, size=size))


def stable_hardware_allocation(capacities: Iterable[float]) -> List[float]:
    values = list(capacities)
    return normalize(PHI ** (-index) * values[index] for index in range(len(values)))
