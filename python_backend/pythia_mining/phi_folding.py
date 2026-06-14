"""Shared reversible golden-ratio folding primitives."""

from __future__ import annotations

from typing import List, Sequence

import numpy as np

from .phi_config import PHI


class PhiFoldingOperator:
    """Reversible golden-ratio fold/unfold primitive with retained kernels."""

    def __init__(self, *, tolerance: float = 1e-9) -> None:
        self.tolerance = float(tolerance)

    def fibonacci_split(self, dimension: int) -> tuple[int, int]:
        if dimension < 1:
            raise ValueError(f"dimension must be positive; received {dimension!r}")
        smaller = max(1, int(round(int(dimension) / (PHI + 1.0))))
        larger = int(dimension) - smaller
        if larger < smaller and dimension > 1:
            larger, smaller = smaller, larger
        return larger, smaller

    def phi_ratio_error(self, dimension: int) -> float:
        larger, smaller = self.fibonacci_split(int(dimension))
        return float(abs((larger / max(1, smaller)) - PHI))

    def fold(self, payload: np.ndarray) -> tuple[np.ndarray, np.ndarray, int]:
        values = np.asarray(payload).reshape(-1)
        dtype = np.result_type(
            values.dtype, np.complex128 if np.iscomplexobj(values) else np.float64
        )
        values = values.astype(dtype, copy=False)
        # Clamp real-valued inputs to a safe range to prevent overflow through
        # phi weight multiplications (w1 = 1/phi ~0.618, w2 = 1/phi^2 ~0.382).
        # The unfold path multiplies by (w1^2 + w2^2)^-1 ~2.618, so values above
        # finfo.max / 4 can overflow. Complex inputs are left unclamped.
        if not np.iscomplexobj(values):
            safe_max = np.finfo(np.float64).max / 8.0
            values = np.clip(values, -safe_max, safe_max)
        original_size = int(values.size)
        if original_size <= 1:
            return values.copy(), np.zeros(0, dtype=dtype), original_size
        larger, smaller = self.fibonacci_split(original_size)
        head = values[:larger]
        tail = values[larger:]
        padded_tail = np.zeros(larger, dtype=dtype)
        padded_tail[:smaller] = tail
        w1 = 1.0 / PHI
        w2 = 1.0 / (PHI**2)
        folded = w1 * head + w2 * padded_tail
        kernel = w2 * head - w1 * padded_tail
        return folded, kernel, original_size

    def unfold(
        self, folded: np.ndarray, kernel: np.ndarray, original_size: int
    ) -> np.ndarray:
        if int(original_size) <= 1:
            return np.asarray(folded).reshape(-1)[: int(original_size)].copy()
        folded_values = np.asarray(folded).reshape(-1)
        kernel_values = np.asarray(kernel).reshape(-1)
        larger, smaller = self.fibonacci_split(int(original_size))
        if folded_values.size != larger or kernel_values.size != larger:
            raise ValueError(
                "folded payload and kernel do not match original size: "
                f"expected {larger} elements for original_size={original_size}, "
                f"got folded={folded_values.size}, kernel={kernel_values.size}"
            )
        w1 = 1.0 / PHI
        w2 = 1.0 / (PHI**2)
        norm_sq = w1**2 + w2**2
        head = (w1 * folded_values + w2 * kernel_values) / norm_sq
        tail_padded = (w2 * folded_values - w1 * kernel_values) / norm_sq
        return np.concatenate([head, tail_padded[:smaller]])

    def fold_recursive(
        self, payload: np.ndarray, *, depth: int
    ) -> tuple[np.ndarray, tuple[np.ndarray, ...], tuple[int, ...]]:
        if int(depth) < 1:
            raise ValueError(f"depth must be >= 1; received {depth!r}")
        current = np.asarray(payload).reshape(-1).copy()
        kernels: List[np.ndarray] = []
        sizes: List[int] = [int(current.size)]
        for _ in range(int(depth)):
            if current.size <= 1:
                break
            current, kernel, _original_size = self.fold(current)
            kernels.append(kernel.copy())
            sizes.append(int(current.size))
        return current, tuple(kernels), tuple(sizes)

    def unfold_recursive(
        self, folded: np.ndarray, kernels: Sequence[np.ndarray], sizes: Sequence[int]
    ) -> np.ndarray:
        current = np.asarray(folded).reshape(-1).copy()
        if len(sizes) != len(kernels) + 1:
            raise ValueError(
                "sizes must contain initial size plus one size per kernel: "
                f"len(sizes)={len(sizes)}, len(kernels)={len(kernels)}"
            )
        for kernel, original_size in zip(reversed(kernels), reversed(sizes[:-1])):
            current = self.unfold(current, kernel, int(original_size))
        return current
