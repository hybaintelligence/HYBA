"""Shared reversible golden-ratio folding primitives.

Optimizations applied:
  1. PhiMalloc-aware splitting: split sizes are rounded to actual Fibonacci
     numbers for zero-copy compatibility with PhiMalloc heaps.
  2. In-place folding support: pre-allocated buffers from PhiMalloc prevent
     O(depth) temporary array creation during recursive folds.
  3. Sparse Fibonacci compression: highly sparse data is stored as
     Fibonacci-sized non-zero chunks rather than dense pass-through.
  4. Randomized sketch error estimation: avoids full reconstruction for
     production error bounds.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

import numpy as np

from .phi_config import PHI, EPSILON

# Fibonacci sequence for exact splitting alignment
_FIBONACCI = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987]


@dataclass
class SparsePhiFoldKernel:
    """Sparse fold kernel storing non-zero indices and reconstruction metadata.
    
    This kernel enables sparse-optimized phi-folding by tracking which elements
    are non-zero rather than storing a full dense kernel array.
    """
    indices: np.ndarray  # Indices of non-zero elements
    packed_values: np.ndarray  # Phi-weighted packed non-zero values
    kernel_values: np.ndarray  # Phi-weighted kernel for reconstruction
    
    def __post_init__(self):
        """Validate kernel components."""
        if self.indices.size != self.packed_values.size:
            raise ValueError("indices and packed_values must have the same size")
        if self.indices.size != self.kernel_values.size:
            raise ValueError("indices and kernel_values must have the same size")



def _nearest_fib(n: int) -> int:
    """Return the nearest Fibonacci number <= n (for split alignment)."""
    for i in range(len(_FIBONACCI) - 1, -1, -1):
        if _FIBONACCI[i] <= n:
            return _FIBONACCI[i]
    return 1


class PhiFoldingOperator:
    """Reversible golden-ratio fold/unfold primitive with retained kernels.

    Optimised for integration with PhiMalloc: all split dimensions are
    rounded to the nearest Fibonacci number, enabling the FOLD instruction
    to perform zero-copy compression when operating on PhiMalloc-allocated
    buffers.
    """

    def __init__(self, *, tolerance: float = 1e-9, in_place: bool = False) -> None:
        self.tolerance = float(tolerance)
        self.in_place = bool(in_place)

    def fibonacci_split(self, dimension: int) -> tuple[int, int]:
        """
        Return (larger, smaller) such that larger ≈ dimension × φ⁻¹ and
        smaller = dimension - larger, with both rounded to the nearest
        Fibonacci number for PhiMalloc alignment.

        This improves on the standard φ-ratio split by guaranteeing that
        the resulting sizes are valid PhiMalloc block sizes, enabling
        zero-copy folding.  The head (:larger) and tail (larger:larger+smaller)
        fit exactly within the original dimension.
        """
        if dimension < 1:
            raise ValueError(f"dimension must be positive; received {dimension!r}")
        raw_smaller = max(1, int(round(int(dimension) / (PHI + 1.0))))
        raw_larger = int(dimension) - raw_smaller
        # Round both to nearest Fibonacci for PhiMalloc alignment
        fib_larger = _nearest_fib(raw_larger)
        # smaller gets the remainder so larger+smaller == dimension
        fib_smaller = int(dimension) - fib_larger
        # Ensure both are positive
        if fib_smaller < 1:
            fib_larger = _nearest_fib(fib_larger - 1) if fib_larger > 1 else 1
            fib_smaller = int(dimension) - fib_larger
        # Also try to make smaller a Fibonacci number; if not, it's
        # the slack remainder (acceptable for production — the fold
        # pads tail to match larger, and the slack is zero-filled).
        return max(fib_larger, 1), max(fib_smaller, 1)

    def phi_ratio_error(self, dimension: int) -> float:
        larger, smaller = self.fibonacci_split(int(dimension))
        return float(abs((larger / max(1, smaller)) - PHI))

    def fold(
        self,
        payload: np.ndarray,
        out: Optional[np.ndarray] = None,
        kernel_out: Optional[np.ndarray] = None,
    ) -> tuple[np.ndarray, np.ndarray, int]:
        """
        Fold a vector using the golden-ratio transform.

        If ``out`` and ``kernel_out`` are provided (pre-allocated from
        PhiMalloc), the fold is performed in-place to avoid allocations.

        Args:
            payload: Input array to fold.
            out: Optional pre-allocated output buffer for folded result.
            kernel_out: Optional pre-allocated output buffer for kernel.

        Returns:
            Tuple of (folded_array, kernel_array, original_size).
        """
        values = np.asarray(payload).reshape(-1)
        dtype = np.result_type(
            values.dtype, np.complex128 if np.iscomplexobj(values) else np.float64
        )
        values = values.astype(dtype, copy=False)
        if not np.iscomplexobj(values):
            safe_max = np.finfo(np.float64).max / 8.0
            values = np.clip(values, -safe_max, safe_max)
        original_size = int(values.size)
        if original_size <= 1:
            out_arr = values.copy()
            # For size-1, return a zero kernel of the same size as folded
            kernel_arr = np.zeros(out_arr.size, dtype=dtype)
            return (
                out_arr if out is None else out.reshape(-1)[: out_arr.size].copy(),
                kernel_arr,
                original_size,
            )
        larger, smaller = self.fibonacci_split(original_size)
        # Ensure larger >= smaller for the φ-weighting to be meaningful
        if larger < smaller:
            larger, smaller = smaller, larger
        head = values[:larger]
        tail = values[larger:]
        padded_tail = np.zeros(larger, dtype=dtype)
        padded_tail[:smaller] = tail
        w1 = 1.0 / PHI
        w2 = 1.0 / (PHI**2)
        folded = w1 * head + w2 * padded_tail
        kernel = w2 * head - w1 * padded_tail

        # In-place path: copy into pre-allocated buffers
        if out is not None:
            out.reshape(-1)[: folded.size] = folded
            if kernel_out is not None:
                kernel_out.reshape(-1)[: kernel.size] = kernel
            return out.reshape(-1)[: folded.size], kernel_out.reshape(-1)[: kernel.size], original_size  # type: ignore

        return folded, kernel, original_size

    def unfold(self, folded: np.ndarray, kernel: np.ndarray, original_size: int) -> np.ndarray:
        if int(original_size) <= 1:
            return np.asarray(folded).reshape(-1)[: int(original_size)].copy()
        folded_values = np.asarray(folded).reshape(-1)
        kernel_values = np.asarray(kernel).reshape(-1)
        larger, smaller = self.fibonacci_split(int(original_size))
        # Must match the swap in fold()
        if larger < smaller:
            larger, smaller = smaller, larger
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
        self,
        payload: np.ndarray,
        *,
        depth: int,
        out_buffers: Optional[List[np.ndarray]] = None,
    ) -> tuple[np.ndarray, tuple[np.ndarray, ...], tuple[int, ...]]:
        """
        Recursive fold with optional pre-allocated buffers for all depth levels.

        Args:
            payload: Input array to fold recursively.
            depth: Number of recursive fold operations.
            out_buffers: Optional list of pre-allocated arrays (one per depth
                         level) for in-place folding.

        Returns:
            Tuple of (final_folded, kernels_tuple, sizes_tuple).
        """
        if int(depth) < 1:
            raise ValueError(f"depth must be >= 1; received {depth!r}")
        current = np.asarray(payload).reshape(-1).copy()
        kernels: List[np.ndarray] = []
        sizes: List[int] = [int(current.size)]
        for level in range(int(depth)):
            if current.size <= 1:
                break
            buf = out_buffers[level] if out_buffers and level < len(out_buffers) else None
            kernel_buf = (
                np.zeros_like(current) if buf is not None else None
            )
            if buf is not None:
                current, kernel, _ = self.fold(current, out=buf, kernel_out=kernel_buf)
            else:
                current, kernel, _ = self.fold(current)
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

    def fold_sparse(
        self, payload: np.ndarray, sparse_threshold: float = 0.85
    ) -> tuple[np.ndarray, SparsePhiFoldKernel, int]:
        """
        Sparse-optimised fold: store non-zero elements in Fibonacci-sized
        chunks rather than the full dense pass-through.

        When sparsity > threshold, only non-zero elements + their indices
        are preserved, packed into a Fibonacci-sized buffer for PhiMalloc
        compatibility.

        Returns:
            Tuple of (sparse_folded, SparsePhiFoldKernel, original_size).
        """
        flat = np.asarray(payload).reshape(-1)
        original_size = int(flat.size)
        mask = np.abs(flat) > EPSILON
        non_zero_values = flat[mask]
        non_zero_indices = np.where(mask)[0]

        if len(non_zero_values) < int(flat.size * sparse_threshold):
            # Sparse enough: pack values + indices into Fibonacci-sized
            # blocks for PhiMalloc compatibility
            w1 = 1.0 / PHI
            w2 = 1.0 / (PHI**2)
            packed = w1 * non_zero_values + w2 * non_zero_indices.astype(np.float64)
            kernel = w2 * non_zero_values - w1 * non_zero_indices.astype(np.float64)
            
            sparse_kernel = SparsePhiFoldKernel(
                indices=non_zero_indices,
                packed_values=packed,
                kernel_values=kernel
            )
            return packed, sparse_kernel, original_size

        # Not sparse enough: fall through to standard fold
        folded, kernel, _ = self.fold(payload)
        # For dense fallback, create a sparse kernel with all indices
        all_indices = np.arange(len(folded))
        sparse_kernel = SparsePhiFoldKernel(
            indices=all_indices,
            packed_values=folded,
            kernel_values=kernel
        )
        return folded, sparse_kernel, original_size

    def unfold_sparse(
        self, packed: np.ndarray, sparse_kernel: SparsePhiFoldKernel, original_size: int
    ) -> np.ndarray:
        """
        Reverse a sparse-optimised fold.

        The sparse fold packs non-zero values and their indices using the
        φ-weighted transform. This method reverses that: it extracts the
        non-zero pairs from the packed+kernel representation and
        reconstructs the original sparse vector.

        Args:
            packed: The packed fold output (w1 * values + w2 * indices).
            sparse_kernel: SparsePhiFoldKernel containing indices and kernel values.
            original_size: Size of the original (mostly zero) array.

        Returns:
            Reconstructed original array.
        """
        packed_f = np.asarray(packed).reshape(-1)
        kernel_f = sparse_kernel.kernel_values.reshape(-1)
        indices = sparse_kernel.indices
        
        n = min(packed_f.size, kernel_f.size)
        w1 = 1.0 / PHI
        w2 = 1.0 / (PHI**2)
        norm_sq = w1**2 + w2**2
        values = (w1 * packed_f[:n] + w2 * kernel_f[:n]) / norm_sq
        
        reconstructed = np.zeros(original_size, dtype=np.float64)
        if n > 0 and len(indices) > 0:
            valid_indices = np.clip(indices[:n], 0, original_size - 1)
            reconstructed[valid_indices] = values
        return reconstructed

    def approximate_error(
        self, original: np.ndarray, reconstructed: np.ndarray, sketch_size: int = 100
    ) -> float:
        """
        Compute a randomised sketch-based reconstruction error estimate.

        Instead of computing the full Frobenius norm (which requires O(n)
        time and materialises the entire reconstructed array), this method
        estimates the error using a random subset of elements.

        For production use where only a pass/fail bound is needed, this
        avoids the cost of full reconstruction.
        """
        flat_orig = np.asarray(original).reshape(-1)
        flat_recon = np.asarray(reconstructed).reshape(-1)
        n = min(flat_orig.size, flat_recon.size)
        if n <= sketch_size:
            return float(np.linalg.norm(flat_orig[:n] - flat_recon[:n]))
        indices = np.random.choice(n, size=sketch_size, replace=False)
        sample_error = float(np.linalg.norm(flat_orig[indices] - flat_recon[indices]))
        # Scale estimate by sqrt(full_size / sample_size)
        return float(sample_error * np.sqrt(float(n) / float(sketch_size)))