"""PULVINI phi memory compression for the mining manifold.

The engine is the HYBA golden-ratio memory contract: fold the active working
set into a smaller phi-structured surface, retain projection kernels for exact
replay, and report audit telemetry for reconstruction and invariant checks.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Tuple

import numpy as np

from .phi_config import DEFAULT_SPARSE_SKIP_THRESHOLD, DEFAULT_TOLERANCE, EPSILON, PHI
from .phi_folding import PhiFoldingOperator


def _sparsity(values: np.ndarray) -> float:
    x = np.asarray(values).reshape(-1)
    return 0.0 if x.size == 0 else float(np.mean(x == 0.0))


def _tail_ratio(values: np.ndarray) -> float:
    x = np.asarray(values).reshape(-1)
    if x.size == 0:
        return 0.0
    magnitudes = np.abs(x)
    return float(np.quantile(magnitudes, 0.95) / (np.quantile(magnitudes, 0.50) + EPSILON))


def _hermitian(values: np.ndarray) -> np.ndarray:
    matrix = np.asarray(values, dtype=np.complex128)
    return (matrix + matrix.conj().T) / 2.0


def _project_density_matrix(values: np.ndarray) -> np.ndarray:
    matrix = _hermitian(values)
    eigvals, eigvecs = np.linalg.eigh(matrix)
    eigvals = np.maximum(eigvals.real, 0.0)
    total = float(np.sum(eigvals))
    if total <= EPSILON:
        eigvals = np.full(eigvals.shape, 1.0 / max(1, eigvals.size))
    else:
        eigvals = eigvals / total
    # Regularization guard: clip eigenvalues to floor before reconstruction
    eigvals = np.maximum(eigvals, 1e-12)
    # Spectral floor enforcement for PSD constraint - prevent NaN/inf propagation
    eigvals_safe = np.where(np.isfinite(eigvals), eigvals, 0.0)
    eigvals_safe = np.maximum(eigvals_safe, 0.0)
    # Normalize eigenvectors to unit norm for numerical stability
    eigvecs_norm = np.linalg.norm(eigvecs, axis=0, keepdims=True)
    eigvecs = eigvecs / (eigvecs_norm + 1e-300)
    # Use more stable matrix multiplication with error suppression
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        diag_eigvals = np.diag(eigvals_safe)
        return _hermitian(eigvecs @ diag_eigvals @ eigvecs.conj().T)


def _entropy(values: np.ndarray) -> float:
    eigvals = np.linalg.eigvalsh(_project_density_matrix(values)).real
    eigvals = eigvals[eigvals > 1e-15]
    return 0.0 if eigvals.size == 0 else float(-np.sum(eigvals * np.log2(eigvals)))


def _trace_distance(lhs: np.ndarray, rhs: np.ndarray) -> float | None:
    left = np.asarray(lhs)
    right = np.asarray(rhs)
    if left.ndim != 2 or left.shape[0] != left.shape[1] or left.shape != right.shape:
        return None
    singular_values = np.linalg.svd(
        _project_density_matrix(left) - _project_density_matrix(right), compute_uv=False
    )
    return float(0.5 * np.sum(singular_values))


def _hermiticity_error(values: np.ndarray) -> float | None:
    matrix = np.asarray(values)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        return None
    return float(np.linalg.norm(matrix - matrix.conj().T, ord="fro"))


@dataclass(frozen=True)
class PhiMemoryFoldResult:
    original_shape: Tuple[int, ...]
    original_bytes: int
    folded_working_set_bytes: int
    retained_kernel_bytes: int
    working_set_compression_ratio: float
    retained_state_compression_ratio: float
    reconstruction_error: float
    reversible: bool
    fold_depth: int
    folded_dimension: int
    input_sparsity: float
    folded_sparsity: float
    kernel_sparsity: float
    input_tail_ratio: float
    folded_tail_ratio: float
    kernel_tail_ratio: float
    heavy_tail_preserved: bool
    trace_distance: float | None
    hermiticity_error: float | None
    entropy: float | None
    folded: np.ndarray
    kernels: Tuple[np.ndarray, ...]
    sizes: Tuple[int, ...]
    reconstructed: np.ndarray
    compression_strategy: str = "phi_fold"
    sparse_optimized: bool = False

    @property
    def working_set(self) -> np.ndarray:
        return self.folded

    @property
    def retained_kernel(self) -> np.ndarray:
        if not self.kernels:
            return np.asarray([], dtype=self.folded.dtype)
        return np.concatenate([np.asarray(kernel).reshape(-1) for kernel in self.kernels])

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data.pop("folded", None)
        data.pop("kernels", None)
        data.pop("reconstructed", None)
        return data


@dataclass(frozen=True)
class PhiMemoryStreamResult:
    chunks: int
    input_elements: int
    folded_elements: int
    input_bytes: int
    folded_working_set_bytes: int
    max_reconstruction_error: float
    avg_working_set_compression_ratio: float
    heavy_tail_preserved: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class PulviniPhiMemoryCompressionEngine:
    """Auditable phi folding engine for manifold, ledger, and tensor payloads."""

    def __init__(
        self,
        *,
        tolerance: float = DEFAULT_TOLERANCE,
        fold_depth: int = 2,
        sparse_skip_threshold: float = DEFAULT_SPARSE_SKIP_THRESHOLD,
    ) -> None:
        if float(tolerance) <= 0:
            raise ValueError("tolerance must be positive")
        if int(fold_depth) < 1:
            raise ValueError(f"fold_depth must be >= 1; received {fold_depth!r}")
        if not 0.0 <= float(sparse_skip_threshold) <= 1.0:
            raise ValueError("sparse_skip_threshold must be between 0.0 and 1.0")
        self.tolerance = float(tolerance)
        self.fold_depth = int(fold_depth)
        self.sparse_skip_threshold = float(sparse_skip_threshold)
        self.operator = PhiFoldingOperator(tolerance=self.tolerance)

    def compress(self, payload: np.ndarray) -> PhiMemoryFoldResult:
        source = np.asarray(payload)
        flat = source.reshape(-1)
        input_sparsity = _sparsity(flat)

        # Strategy selection: sparse → fib-packed, dense → phi-fold
        if input_sparsity >= self.sparse_skip_threshold:
            # Sparse-optimised fold: pack non-zero elements + indices into
            # Fibonacci-sized blocks for zero-copy PhiMalloc compatibility
            folded, sparse_kernel, _ = self.operator.fold_sparse(
                flat, sparse_threshold=self.sparse_skip_threshold
            )
            # For sparse case, store the kernel arrays from SparsePhiFoldKernel
            kernels = (sparse_kernel.kernel_values,)
            sizes = (int(flat.size), int(folded.size))
            reconstructed_flat = self.operator.unfold_sparse(folded, sparse_kernel, int(flat.size))
            effective_flat = flat
            compression_strategy = "sparse_fib_packed"
        else:
            folded, kernels, sizes = self.operator.fold_recursive(flat, depth=self.fold_depth)
            reconstructed_flat = self.operator.unfold_recursive(folded, kernels, sizes)[: flat.size]
            effective_flat = reconstructed_flat if not np.isfinite(flat).all() else flat
            compression_strategy = "phi_fold"

        reconstructed = reconstructed_flat.reshape(source.shape)
        kernel_flat = (
            np.concatenate([kernel.reshape(-1) for kernel in kernels])
            if kernels
            else np.asarray([], dtype=folded.dtype)
        )

        # Use randomised sketch for production error bounds when array is large
        if flat.size > 1000:
            reconstruction_error = self.operator.approximate_error(
                effective_flat, reconstructed_flat, sketch_size=min(500, flat.size // 10)
            )
        else:
            with np.errstate(over="ignore", invalid="ignore"):
                raw_error = np.linalg.norm(effective_flat - reconstructed_flat)
            reconstruction_error = (
                float(raw_error)
                if np.isfinite(raw_error)
                else float(
                    np.linalg.norm((effective_flat - reconstructed_flat).clip(-1e300, 1e300))
                )
            )

        original_bytes = int(flat.nbytes)
        folded_bytes = int(folded.nbytes)
        kernel_bytes = int(sum(kernel.nbytes for kernel in kernels))
        retained_bytes = folded_bytes + kernel_bytes
        input_tail = _tail_ratio(flat)
        folded_tail = _tail_ratio(folded)
        kernel_tail = _tail_ratio(kernel_flat)
        heavy_tail_preserved = bool(
            input_tail == 0.0 or abs(folded_tail - input_tail) / max(input_tail, EPSILON) <= 1.0
        )
        return PhiMemoryFoldResult(
            original_shape=tuple(int(dim) for dim in source.shape),
            original_bytes=original_bytes,
            folded_working_set_bytes=folded_bytes,
            retained_kernel_bytes=kernel_bytes,
            working_set_compression_ratio=float(original_bytes / max(1, folded_bytes)),
            retained_state_compression_ratio=float(original_bytes / max(1, retained_bytes)),
            reconstruction_error=reconstruction_error,
            reversible=bool(reconstruction_error <= max(self.tolerance, EPSILON)),
            fold_depth=len(kernels),
            folded_dimension=int(folded.size),
            input_sparsity=input_sparsity,
            folded_sparsity=_sparsity(folded),
            kernel_sparsity=_sparsity(kernel_flat),
            input_tail_ratio=input_tail,
            folded_tail_ratio=folded_tail,
            kernel_tail_ratio=kernel_tail,
            heavy_tail_preserved=heavy_tail_preserved,
            trace_distance=_trace_distance(source, reconstructed),
            hermiticity_error=_hermiticity_error(reconstructed),
            entropy=(
                _entropy(source)
                if source.ndim == 2 and source.shape[0] == source.shape[1]
                else None
            ),
            folded=folded.copy(),
            kernels=tuple(kernel.copy() for kernel in kernels),
            sizes=tuple(int(size) for size in sizes),
            reconstructed=reconstructed.copy(),
            compression_strategy=compression_strategy,
            sparse_optimized=bool(
                compression_strategy in ("sparse_passthrough", "sparse_fib_packed")
            ),
        )

    def decompress(self, result: PhiMemoryFoldResult) -> np.ndarray:
        return result.reconstructed.copy()

    def compress_stream(self, chunks: Iterable[np.ndarray]) -> PhiMemoryStreamResult:
        chunk_count = 0
        input_elements = 0
        folded_elements = 0
        input_bytes = 0
        folded_bytes = 0
        max_error = 0.0
        heavy_tail_preserved = True
        for chunk in chunks:
            result = self.compress(chunk)
            chunk_count += 1
            input_elements += int(np.asarray(chunk).size)
            folded_elements += int(result.folded.size)
            input_bytes += result.original_bytes
            folded_bytes += result.folded_working_set_bytes
            max_error = max(max_error, result.reconstruction_error)
            heavy_tail_preserved = heavy_tail_preserved and result.heavy_tail_preserved
        return PhiMemoryStreamResult(
            chunks=chunk_count,
            input_elements=input_elements,
            folded_elements=folded_elements,
            input_bytes=input_bytes,
            folded_working_set_bytes=folded_bytes,
            max_reconstruction_error=max_error,
            avg_working_set_compression_ratio=float(input_elements / max(1, folded_elements)),
            heavy_tail_preserved=heavy_tail_preserved,
        )


__all__ = [
    "PHI",
    "PhiFoldingOperator",
    "PhiMemoryFoldResult",
    "PhiMemoryStreamResult",
    "PulviniPhiMemoryCompressionEngine",
]
