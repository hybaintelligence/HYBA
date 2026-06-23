"""Finite folded-space probability amplification for PYTHAGORAS.

This is a deterministic mathematical primitive over a bounded folded space. It
supports enterprise auditability and repeatable solver capacity estimates.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Sequence
import numpy as np

_EPS = 1e-12


class FoldedAmplifierError(ValueError):
    pass


@dataclass(frozen=True)
class FoldedAmplifierResult:
    best_index: int
    best_probability: float
    iterations: int
    dimension: int
    deterministic_capacity: float
    probabilities: List[float]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _norm(values: Any) -> np.ndarray:
    vec = np.asarray(values, dtype=float).reshape(-1)
    if vec.size == 0:
        raise FoldedAmplifierError("empty vector")
    if not np.all(np.isfinite(vec)):
        raise FoldedAmplifierError("vector contains non-finite values")
    n = np.linalg.norm(vec)
    if n < _EPS:
        raise FoldedAmplifierError("zero norm vector")
    return vec / n


def uniform_vector(dimension: int) -> np.ndarray:
    if dimension <= 0:
        raise FoldedAmplifierError("dimension must be positive")
    return np.ones(int(dimension), dtype=float) / np.sqrt(float(dimension))


def mark(values: Any, indices: Sequence[int]) -> np.ndarray:
    vector = _norm(values)
    out = vector.copy()
    for raw in indices:
        idx = int(raw)
        if idx < 0 or idx >= out.size:
            raise FoldedAmplifierError("index out of range")
        out[idx] *= -1.0
    return out


def reflect_about_mean(values: Any) -> np.ndarray:
    vector = _norm(values)
    return _norm((2.0 * float(np.mean(vector))) - vector)


def amplification_step(values: Any, indices: Sequence[int]) -> np.ndarray:
    return reflect_about_mean(mark(values, indices))


def recommended_steps(dimension: int, target_count: int = 1) -> int:
    if dimension <= 0 or target_count <= 0 or target_count > dimension:
        raise FoldedAmplifierError("invalid dimensions")
    return max(
        1, int(round((np.pi / 4.0) * np.sqrt(float(dimension) / float(target_count))))
    )


def run_amplifier(
    dimension: int,
    indices: Sequence[int],
    *,
    initial: Optional[Any] = None,
    iterations: Optional[int] = None,
) -> FoldedAmplifierResult:
    if dimension <= 0:
        raise FoldedAmplifierError("dimension must be positive")
    idxs = tuple(int(x) for x in indices)
    if not idxs:
        raise FoldedAmplifierError("at least one index is required")
    if any(i < 0 or i >= dimension for i in idxs):
        raise FoldedAmplifierError("index out of range")
    vector = uniform_vector(dimension) if initial is None else _norm(initial)
    if vector.size != dimension:
        raise FoldedAmplifierError("dimension mismatch")
    steps = (
        recommended_steps(dimension, len(idxs))
        if iterations is None
        else int(iterations)
    )
    if steps < 0:
        raise FoldedAmplifierError("iterations cannot be negative")
    for _ in range(steps):
        vector = amplification_step(vector, idxs)
    probs = vector * vector
    best = int(np.argmax(probs))
    return FoldedAmplifierResult(
        best,
        float(probs[best]),
        steps,
        int(dimension),
        float(dimension / max(1, steps)),
        [float(x) for x in probs],
    )


__all__ = [
    "FoldedAmplifierError",
    "FoldedAmplifierResult",
    "uniform_vector",
    "mark",
    "reflect_about_mean",
    "amplification_step",
    "recommended_steps",
    "run_amplifier",
]
