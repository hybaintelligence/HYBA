"""Shared reversible golden-ratio folding primitives.

The operator supports four production surfaces:

* reversible dense fold/unfold with retained kernels;
* in-place dense folding via caller-provided buffers;
* sparse Fibonacci packing for high-sparsity tensors;
* randomized sketch error estimation for large-array audit paths.

These are software primitives. They do not claim hardware acceleration, accepted
shares, or revenue by themselves; they provide the memory-folding substrate used
by PULVINI and the Φ-Architecture evidence gates.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

import numpy as np

from .phi_config import PHI


@dataclass(frozen=True)
class SparsePhiFoldKernel:
    """Kernel needed to reconstruct a sparse Φ-folded payload."""

    original_size: int
    indices: np.ndarray
    dtype: str


class PhiFoldingOperator:
    """Reversible golden-ratio fold/unfold primitive with retained kernels."""

    def __init__(self, *, tolerance: float = 1e-9) -> None:
        self.tolerance = float(tolerance)

    def fibonacci_split(self, dimension: int) -> tuple[int, int]:
        """Split a dimension into larger/smaller φ-proportional surfaces.

        The split always sums to ``dimension`` and keeps the first return value
        large enough to hold the tail during reversible folding. For Fibonacci
        dimensions the ratio converges tightly to φ; for arbitrary dimensions it
        is a φ-guided operational split, not a claim that both terms are exact
        Fibonacci numbers.
        """

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

    def fold(
        self,
        payload: np.ndarray,
        *,
        out: np.ndarray | None = None,
        kernel_out: np.ndarray | None = None,
    ) -> tuple[np.ndarray, np.ndarray, int]:
        """Fold a dense payload, optionally reusing caller-provided buffers."""

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
            folded_single = values.copy()
            empty_kernel = np.zeros(0, dtype=dtype)
            if out is not None:
                target = np.asarray(out).reshape(-1)
                if target.size < folded_single.size:
                    raise ValueError("out buffer is too small for folded payload")
                target[: folded_single.size] = folded_single
                folded_single = target[: folded_single.size]
            if kernel_out is not None and np.asarray(kernel_out).size < 0:
                raise ValueError("kernel_out buffer is invalid")
            return folded_single, empty_kernel, original_size

        larger, smaller = self.fibonacci_split(original_size)
        head = values[:larger]
        tail = values[larger:]
        padded_tail = np.zeros(larger, dtype=dtype)
        padded_tail[:smaller] = tail
        w1 = 1.0 / PHI
        w2 = 1.0 / (PHI**2)
        folded_values = w1 * head + w2 * padded_tail
        kernel_values = w2 * head - w1 * padded_tail

        if out is not None:
            out_values = np.asarray(out).reshape(-1)
            if out_values.size < larger:
                raise ValueError(
                    f"out buffer is too small: need {larger}, got {out_values.size}"
                )
            out_values[:larger] = folded_values
            folded_values = out_values[:larger]
        else:
            folded_values = folded_values.copy()

        if kernel_out is not None:
            kernel_values_out = np.asarray(kernel_out).reshape(-1)
            if kernel_values_out.size < larger:
                raise ValueError(
                    "kernel_out buffer is too small: "
                    f"need {larger}, got {kernel_values_out.size}"
                )
            kernel_values_out[:larger] = kernel_values
            kernel_values = kernel_values_out[:larger]
        else:
            kernel_values = kernel_values.copy()

        return folded_values, kernel_values, original_size

    def unfold(self, folded: np.ndarray, kernel: np.ndarray, original_size: int) -> np.ndarray:
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

    def fold_sparse(
        self,
        payload: np.ndarray,
    ) -> tuple[np.ndarray, SparsePhiFoldKernel, int]:
        """Pack non-zero values and their indices for sparse Fibonacci surfaces."""

        values = np.asarray(payload).reshape(-1)
        indices = np.flatnonzero(values)
        packed = values[indices].copy()
        kernel = SparsePhiFoldKernel(
            original_size=int(values.size),
            indices=indices.astype(np.int64, copy=True),
            dtype=str(values.dtype),
        )
        return packed, kernel, int(values.size)

    def unfold_sparse(
        self,
        packed: np.ndarray,
        kernel: SparsePhiFoldKernel,
        original_size: int | None = None,
    ) -> np.ndarray:
        """Reconstruct a sparse payload from values plus sparse kernel."""

        size = int(kernel.original_size if original_size is None else original_size)
        if size != int(kernel.original_size):
            raise ValueError(
                "sparse kernel original_size mismatch: "
                f"kernel={kernel.original_size}, requested={size}"
            )
        packed_values = np.asarray(packed).reshape(-1)
        indices = np.asarray(kernel.indices, dtype=np.int64).reshape(-1)
        if packed_values.size != indices.size:
            raise ValueError(
                "packed sparse values and index kernel length mismatch: "
                f"packed={packed_values.size}, indices={indices.size}"
            )
        dtype = np.dtype(kernel.dtype)
        reconstructed = np.zeros(size, dtype=dtype)
        if indices.size:
            if np.any(indices < 0) or np.any(indices >= size):
                raise ValueError("sparse kernel contains out-of-range indices")
            reconstructed[indices] = packed_values.astype(dtype, copy=False)
        return reconstructed

    def approximate_error(
        self,
        reference: np.ndarray,
        candidate: np.ndarray,
        *,
        sketch_size: int = 512,
        seed: int = 161803398,
    ) -> float:
        """Estimate L2 reconstruction error with a deterministic random sketch.

        The estimator samples a bounded number of coordinates and rescales the
        sampled norm by ``sqrt(n / sample_size)``. It is intended for large-array
        production telemetry where full exact error is too expensive. For exact
        proof gates, callers should still compute the full reconstruction error.
        """

        left = np.asarray(reference).reshape(-1)
        right = np.asarray(candidate).reshape(-1)
        if left.size != right.size:
            raise ValueError(
                f"reference and candidate size mismatch: {left.size} vs {right.size}"
            )
        n = int(left.size)
        if n == 0:
            return 0.0
        sample_size = int(max(1, min(int(sketch_size), n)))
        rng = np.random.default_rng(int(seed))
        indices = rng.choice(n, size=sample_size, replace=False)
        delta = left[indices] - right[indices]
        return float(np.linalg.norm(delta) * np.sqrt(n / sample_size))

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


__all__ = [
    "PhiFoldingOperator",
    "SparsePhiFoldKernel",
]
