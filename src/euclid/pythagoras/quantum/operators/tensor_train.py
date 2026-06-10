"""Tensor Train / Matrix Product State utilities for PULVINI."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

import numpy as np

PHI = (1.0 + sqrt(5.0)) / 2.0


@dataclass(frozen=True)
class TensorTrainAudit:
    original_shape: tuple[int, ...]
    tt_ranks: list[int]
    storage_original: int
    storage_reduced: int
    reduction_ratio: float
    reconstruction_error: float
    phi_guided_rank: int


class TensorTrain:
    """Small NumPy Matrix Product State / Tensor Train container."""

    def __init__(self, cores: list[np.ndarray], original_shape: tuple[int, ...]) -> None:
        self.cores = [np.asarray(core, dtype=np.complex128) for core in cores]
        self.original_shape = tuple(original_shape)
        if not self.cores:
            raise ValueError("cores must not be empty")

    @property
    def ranks(self) -> list[int]:
        ranks = [int(self.cores[0].shape[0])]
        ranks.extend(int(core.shape[-1]) for core in self.cores)
        return ranks

    @property
    def storage(self) -> int:
        return int(sum(core.size for core in self.cores))

    def reconstruct(self) -> np.ndarray:
        result = self.cores[0]
        for core in self.cores[1:]:
            result = np.tensordot(result, core, axes=([-1], [0]))
        return result.reshape(self.original_shape)

    def audit(self, original_tensor: np.ndarray, phi_guided_rank: int) -> TensorTrainAudit:
        original = np.asarray(original_tensor, dtype=np.complex128).reshape(self.original_shape)
        reconstructed = self.reconstruct()
        error = float(np.linalg.norm(original - reconstructed) / max(1.0, np.linalg.norm(original)))
        original_size = int(np.prod(self.original_shape))
        return TensorTrainAudit(
            original_shape=self.original_shape,
            tt_ranks=self.ranks,
            storage_original=original_size,
            storage_reduced=self.storage,
            reduction_ratio=float(original_size / max(1, self.storage)),
            reconstruction_error=error,
            phi_guided_rank=int(phi_guided_rank),
        )


class TensorTrainCompressor:
    def __init__(self, max_rank: int = 32, tolerance: float = 1e-8) -> None:
        self.max_rank = int(max_rank)
        self.tolerance = float(tolerance)

    def phi_guided_rank(self, physical_dimension: int) -> int:
        return max(1, min(self.max_rank, int(round(max(1, physical_dimension) / PHI))))

    def reduce(self, tensor: np.ndarray, max_rank: int | None = None) -> TensorTrain:
        arr = np.asarray(tensor, dtype=np.complex128)
        if arr.ndim == 0:
            arr = arr.reshape(1)
        shape = tuple(int(x) for x in arr.shape)
        rank_cap = int(max_rank or self.phi_guided_rank(max(shape)))
        rank_cap = max(1, min(rank_cap, self.max_rank))
        cores: list[np.ndarray] = []
        unfolding = arr.copy()
        left_rank = 1
        for mode_size in shape[:-1]:
            unfolding = unfolding.reshape(left_rank * mode_size, -1)
            u, s, vh = np.linalg.svd(unfolding, full_matrices=False)
            rank = max(1, min(rank_cap, s.size))
            cores.append(u[:, :rank].reshape(left_rank, mode_size, rank))
            unfolding = np.diag(s[:rank]) @ vh[:rank, :]
            left_rank = rank
        cores.append(unfolding.reshape(left_rank, shape[-1], 1))
        return TensorTrain(cores, shape)


__all__ = ["TensorTrain", "TensorTrainAudit", "TensorTrainCompressor"]
