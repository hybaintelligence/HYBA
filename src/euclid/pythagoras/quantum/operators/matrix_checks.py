from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class MatrixCheck:
    square: bool
    norm_preserving: bool
    trace_value: complex | None
    determinant_value: complex | None
    residual: float | None


class MatrixInvariantChecker:
    def __init__(self, tolerance: float = 1e-8) -> None:
        self.tolerance = float(tolerance)

    def check(self, matrix: np.ndarray) -> MatrixCheck:
        arr = np.asarray(matrix, dtype=np.complex128)
        if arr.ndim != 2 or arr.shape[0] != arr.shape[1]:
            return MatrixCheck(False, False, None, None, None)
        identity = np.eye(arr.shape[0], dtype=np.complex128)
        residual = float(np.linalg.norm(arr.conj().T @ arr - identity))
        return MatrixCheck(
            square=True,
            norm_preserving=residual <= self.tolerance,
            trace_value=complex(np.trace(arr)),
            determinant_value=complex(np.linalg.det(arr)),
            residual=residual,
        )


__all__ = ["MatrixCheck", "MatrixInvariantChecker"]
