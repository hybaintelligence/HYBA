from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class EvolutionAudit:
    dimension: int
    steps: int
    norm_error: float
    passed: bool


class UnitaryEvolver:
    def __init__(self, tolerance: float = 1e-8) -> None:
        self.tolerance = float(tolerance)

    def normalize(self, vector: np.ndarray) -> np.ndarray:
        state = np.asarray(vector, dtype=np.complex128).reshape(-1)
        norm = max(float(np.linalg.norm(state)), 1e-12)
        return state / norm

    def hadamard_like(self, dimension: int) -> np.ndarray:
        if dimension <= 0:
            raise ValueError("dimension must be positive")
        matrix = np.eye(dimension, dtype=np.complex128)
        if dimension >= 2:
            h = np.array([[1, 1], [1, -1]], dtype=np.complex128) / np.sqrt(2.0)
            matrix[:2, :2] = h
        return matrix

    def evolve(self, vector: np.ndarray, operator: np.ndarray, steps: int = 1) -> tuple[np.ndarray, EvolutionAudit]:
        state = self.normalize(vector)
        op = np.asarray(operator, dtype=np.complex128)
        if op.ndim != 2 or op.shape[0] != op.shape[1] or op.shape[0] != state.size:
            raise ValueError("operator must be square and match state dimension")
        for _ in range(max(0, int(steps))):
            state = self.normalize(op @ state)
        norm_error = abs(float(np.linalg.norm(state)) - 1.0)
        return state, EvolutionAudit(int(state.size), int(steps), norm_error, norm_error <= self.tolerance)


__all__ = ["UnitaryEvolver", "EvolutionAudit"]
