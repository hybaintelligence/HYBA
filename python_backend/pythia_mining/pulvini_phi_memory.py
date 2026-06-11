"""PULVINI phi memory compression for the mining manifold.

The engine is the HYBA golden-ratio memory contract: fold the active working
set into a smaller phi-structured surface, retain projection kernels for exact
replay, and report audit telemetry for reconstruction and invariant checks.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Iterable, List, Sequence, Tuple

import numpy as np

PHI = (1.0 + math.sqrt(5.0)) / 2.0
EPSILON = 1e-12


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
    return _hermitian(eigvecs @ np.diag(eigvals) @ eigvecs.conj().T)


def _entropy(values: np.ndarray) -> float:
    eigvals = np.linalg.eigvalsh(_project_density_matrix(values)).real
    eigvals = eigvals[eigvals > 1e-15]
    return 0.0 if eigvals.size == 0 else float(-np.sum(eigvals * np.log2(eigvals)))


def _trace_distance(lhs: np.ndarray, rhs: np.ndarray) -> float | None:
    left = np.asarray(lhs)
    right = np.asarray(rhs)
    if left.ndim != 2 or left.shape[0] != left.shape[1] or left.shape != right.shape:
        return None
    singular_values = np.linalg.svd(_project_density_matrix(left) - _project_density_matrix(right), compute_uv=False)
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


class PhiFoldingOperator:
    """Reversible golden-ratio fold/unfold primitive with retained kernels."""

    def __init__(self, *, tolerance: float = 1e-9) -> None:
        self.tolerance = float(tolerance)

    def fibonacci_split(self, dimension: int) -> tuple[int, int]:
        if dimension < 1:
            raise ValueError("dimension must be positive")
        smaller = max(1, int(round(dimension / (PHI + 1.0))))
        larger = int(dimension) - smaller
        if larger < smaller and dimension > 1:
            larger, smaller = smaller, larger
        return larger, smaller

    def phi_ratio_error(self, dimension: int) -> float:
        larger, smaller = self.fibonacci_split(int(dimension))
        return float(abs((larger / max(1, smaller)) - PHI))

    def fold(self, payload: np.ndarray) -> tuple[np.ndarray, np.ndarray, int]:
        values = np.asarray(payload).reshape(-1)
        dtype = np.result_type(values.dtype, np.complex128 if np.iscomplexobj(values) else np.float64)
        values = values.astype(dtype, copy=False)
        original_size = int(values.size)
        if original_size <= 1:
            return values.copy(), np.zeros(0, dtype=dtype), original_size
        larger, smaller = self.fibonacci_split(original_size)
        head = values[:larger]
        tail = values[larger:]
        padded_tail = np.zeros(larger, dtype=dtype)
        padded_tail[:smaller] = tail
        w1 = 1.0 / PHI
        w2 = 1.0 / (PHI ** 2)
        folded = w1 * head + w2 * padded_tail
        kernel = w2 * head - w1 * padded_tail
        return folded, kernel, original_size

    def unfold(self, folded: np.ndarray, kernel: np.ndarray, original_size: int) -> np.ndarray:
        if int(original_size) <= 1:
            return np.asarray(folded).reshape(-1)[: int(original_size)].copy()
        folded_values = np.asarray(folded).reshape(-1)
        kernel_values = np.asarray(kernel).reshape(-1)
        larger, smaller = self.fibonacci_split(int(original_size))
        if folded_values.size != larger or kernel_values.size != larger:
            raise ValueError("folded payload and kernel do not match original size")
        w1 = 1.0 / PHI
        w2 = 1.0 / (PHI ** 2)
        norm_sq = w1**2 + w2**2
        head = (w1 * folded_values + w2 * kernel_values) / norm_sq
        tail_padded = (w2 * folded_values - w1 * kernel_values) / norm_sq
        return np.concatenate([head, tail_padded[:smaller]])

    def fold_recursive(self, payload: np.ndarray, *, depth: int) -> tuple[np.ndarray, tuple[np.ndarray, ...], tuple[int, ...]]:
        if int(depth) < 1:
            raise ValueError("depth must be >= 1")
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

    def unfold_recursive(self, folded: np.ndarray, kernels: Sequence[np.ndarray], sizes: Sequence[int]) -> np.ndarray:
        current = np.asarray(folded).reshape(-1).copy()
        if len(sizes) != len(kernels) + 1:
            raise ValueError("sizes must contain initial size plus one size per kernel")
        for kernel, original_size in zip(reversed(kernels), reversed(sizes[:-1])):
            current = self.unfold(current, kernel, int(original_size))
        return current


class PulviniPhiMemoryCompressionEngine:
    """Auditable phi folding engine for manifold, ledger, and tensor payloads."""

    def __init__(self, *, tolerance: float = 1e-9, fold_depth: int = 2) -> None:
        if int(fold_depth) < 1:
            raise ValueError("fold_depth must be >= 1")
        self.tolerance = float(tolerance)
        self.fold_depth = int(fold_depth)
        self.operator = PhiFoldingOperator(tolerance=self.tolerance)

    def compress(self, payload: np.ndarray) -> PhiMemoryFoldResult:
        source = np.asarray(payload)
        flat = source.reshape(-1)
        folded, kernels, sizes = self.operator.fold_recursive(flat, depth=self.fold_depth)
        reconstructed_flat = self.operator.unfold_recursive(folded, kernels, sizes)[: flat.size]
        reconstructed = reconstructed_flat.reshape(source.shape)
        kernel_flat = np.concatenate([kernel.reshape(-1) for kernel in kernels]) if kernels else np.asarray([], dtype=folded.dtype)
        reconstruction_error = float(np.linalg.norm(flat - reconstructed_flat))
        original_bytes = int(flat.nbytes)
        folded_bytes = int(folded.nbytes)
        kernel_bytes = int(sum(kernel.nbytes for kernel in kernels))
        retained_bytes = folded_bytes + kernel_bytes
        input_tail = _tail_ratio(flat)
        folded_tail = _tail_ratio(folded)
        kernel_tail = _tail_ratio(kernel_flat)
        heavy_tail_preserved = bool(input_tail == 0.0 or abs(folded_tail - input_tail) / max(input_tail, EPSILON) <= 1.0)
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
            input_sparsity=_sparsity(flat),
            folded_sparsity=_sparsity(folded),
            kernel_sparsity=_sparsity(kernel_flat),
            input_tail_ratio=input_tail,
            folded_tail_ratio=folded_tail,
            kernel_tail_ratio=kernel_tail,
            heavy_tail_preserved=heavy_tail_preserved,
            trace_distance=_trace_distance(source, reconstructed),
            hermiticity_error=_hermiticity_error(reconstructed),
            entropy=_entropy(source) if source.ndim == 2 and source.shape[0] == source.shape[1] else None,
            folded=folded.copy(),
            kernels=tuple(kernel.copy() for kernel in kernels),
            sizes=tuple(int(size) for size in sizes),
            reconstructed=reconstructed.copy(),
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
