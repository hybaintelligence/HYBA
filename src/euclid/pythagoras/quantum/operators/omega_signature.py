from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class OmegaSignature:
    dimension: int
    spectrum: list[float]
    stable_rank: int


class OmegaSignatureChecker:
    def __init__(self, tolerance: float = 0.08, size: int = 16) -> None:
        self.tolerance = float(tolerance)
        self.size = int(size)

    def signature(self, value: np.ndarray) -> OmegaSignature:
        arr = np.asarray(value, dtype=np.complex128).reshape(-1)
        matrix = arr.reshape(1, -1) if arr.size else np.zeros((1, 1))
        singular = np.linalg.svd(matrix, compute_uv=False).real
        singular = singular / max(float(np.linalg.norm(singular)), 1e-12)
        spectrum = np.zeros(self.size)
        spectrum[: min(self.size, singular.size)] = singular[: self.size]
        return OmegaSignature(
            int(arr.size), [float(x) for x in spectrum], int(np.sum(spectrum > 1e-8))
        )

    def is_stable(self, before: OmegaSignature, after: OmegaSignature) -> bool:
        left = np.asarray(before.spectrum, dtype=float)
        right = np.asarray(after.spectrum, dtype=float)
        n = max(left.size, right.size)
        distance = np.linalg.norm(
            np.pad(left, (0, n - left.size)) - np.pad(right, (0, n - right.size))
        )
        return bool(float(distance) <= self.tolerance)


__all__ = ["OmegaSignature", "OmegaSignatureChecker"]
