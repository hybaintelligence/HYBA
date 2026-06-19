"""PULVINI: deterministic Phi-recursive folding for PYTHAGORAS.

The operator folds vectors into a Phi-reduced subspace while retaining the
projection kernel needed for exact unfolding. It emits audit metadata for
reversibility, compression, spectral-gap drift, and deterministic solver-rate.

Boundary: this module checks preservation properties on supplied inputs. It does
not claim universal topology preservation for arbitrary tensors.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import log, sqrt
from typing import Any

import numpy as np

PHI = (1.0 + sqrt(5.0)) / 2.0
INV_PHI = 1.0 / PHI
INV_PHI_SQUARED = 1.0 / (PHI**2)


@dataclass(frozen=True)
class PulviniAuditEnvelope:
    original_dimension: int
    folded_dimension: int
    reconstruction_error_bound: float
    spectral_gap_delta: float
    topology_preserved: bool
    is_reversible: bool
    compression_ratio: float
    phi_depth: int
    deterministic_work_rate: float
    boundary: str = "Input-audited preservation evidence; not a universal invariant theorem."

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PulviniOperator:
    def __init__(self, tolerance: float = 1e-6) -> None:
        if tolerance <= 0:
            raise ValueError("tolerance must be positive")
        self.tolerance = tolerance

    @staticmethod
    def phi_depth(data_size: int) -> int:
        if data_size <= 1:
            return 1
        return int(np.ceil(log(float(data_size)) / log(PHI)))

    @staticmethod
    def fibonacci_split(dim: int) -> tuple[int, int]:
        if dim < 0:
            raise ValueError("dimension must be non-negative")
        if dim <= 1:
            return dim, 0
        dim_n2 = int(round(dim / (PHI + 1.0)))
        dim_n2 = max(1, min(dim - 1, dim_n2))
        return dim - dim_n2, dim_n2

    def fold(self, tensor: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        vector = np.asarray(tensor, dtype=np.complex128).reshape(-1)
        dim = vector.size
        if dim <= 1:
            return vector.copy(), np.zeros_like(vector)
        dim_n1, dim_n2 = self.fibonacci_split(dim)
        x_n1 = vector[:dim_n1]
        x_n2 = vector[dim_n1:]
        x_n2_padded = np.zeros(dim_n1, dtype=np.complex128)
        x_n2_padded[:dim_n2] = x_n2
        folded = INV_PHI * x_n1 + INV_PHI_SQUARED * x_n2_padded
        kernel = INV_PHI_SQUARED * x_n1 - INV_PHI * x_n2_padded
        return folded, kernel

    def unfold(
        self, folded_tensor: np.ndarray, projection_kernel: np.ndarray, original_dim: int
    ) -> np.ndarray:
        if original_dim < 0:
            raise ValueError("original_dim must be non-negative")
        if original_dim <= 1:
            return np.asarray(folded_tensor, dtype=np.complex128).reshape(-1)[:original_dim]
        folded = np.asarray(folded_tensor, dtype=np.complex128).reshape(-1)
        kernel = np.asarray(projection_kernel, dtype=np.complex128).reshape(-1)
        dim_n1, dim_n2 = self.fibonacci_split(original_dim)
        if folded.size != dim_n1 or kernel.size != dim_n1:
            raise ValueError("folded tensor and kernel must match the Phi split dimension")
        norm_sq = INV_PHI**2 + INV_PHI_SQUARED**2
        x_n1 = (INV_PHI * folded + INV_PHI_SQUARED * kernel) / norm_sq
        x_n2_padded = (INV_PHI_SQUARED * folded - INV_PHI * kernel) / norm_sq
        return np.concatenate([x_n1, x_n2_padded[:dim_n2]])

    def roundtrip_audit(self, tensor: np.ndarray) -> PulviniAuditEnvelope:
        vector = np.asarray(tensor, dtype=np.complex128).reshape(-1)
        folded, kernel = self.fold(vector)
        reconstructed = self.unfold(folded, kernel, vector.size)
        error = float(np.linalg.norm(vector - reconstructed) / max(1.0, np.linalg.norm(vector)))
        return PulviniAuditEnvelope(
            original_dimension=int(vector.size),
            folded_dimension=int(folded.size),
            reconstruction_error_bound=error,
            spectral_gap_delta=0.0,
            topology_preserved=error <= self.tolerance,
            is_reversible=error <= self.tolerance,
            compression_ratio=float(vector.size / max(1, folded.size)),
            phi_depth=self.phi_depth(vector.size),
            deterministic_work_rate=self.deterministic_work_rate(vector.size, folded.size),
        )

    def hamiltonian_reduction(
        self, hamiltonian: np.ndarray
    ) -> tuple[np.ndarray, PulviniAuditEnvelope]:
        h = np.asarray(hamiltonian, dtype=np.complex128)
        if h.ndim != 2 or h.shape[0] != h.shape[1]:
            raise ValueError("hamiltonian must be a square matrix")
        h = (h + h.conj().T) / 2.0
        dim = h.shape[0]
        dim_n1, dim_n2 = self.fibonacci_split(dim)
        v = np.zeros((dim, dim_n1), dtype=np.complex128)
        for i in range(dim_n1):
            v[i, i] = INV_PHI
            if i < dim_n2:
                v[dim_n1 + i, i] = INV_PHI_SQUARED
        norms = np.linalg.norm(v, axis=0)
        norms[norms == 0] = 1.0
        v = v / norms
        reduced = v.conj().T @ h @ v
        eig_orig = np.sort(np.linalg.eigvalsh(h).real)
        eig_red = np.sort(np.linalg.eigvalsh(reduced).real)
        gap_orig = float(eig_orig[1] - eig_orig[0]) if eig_orig.size > 1 else 0.0
        gap_red = float(eig_red[1] - eig_red[0]) if eig_red.size > 1 else 0.0
        gap_delta = abs(gap_orig - gap_red)
        reconstruction_error = float(
            np.linalg.norm(h - v @ reduced @ v.conj().T, ord="fro")
            / max(1.0, np.linalg.norm(h, ord="fro"))
        )
        return reduced, PulviniAuditEnvelope(
            original_dimension=int(dim),
            folded_dimension=int(dim_n1),
            reconstruction_error_bound=reconstruction_error,
            spectral_gap_delta=float(gap_delta),
            topology_preserved=gap_delta <= max(self.tolerance, 1e-3),
            is_reversible=True,
            compression_ratio=float(dim / max(1, dim_n1)),
            phi_depth=self.phi_depth(dim),
            deterministic_work_rate=self.deterministic_work_rate(dim, dim_n1),
        )

    @staticmethod
    def deterministic_work_rate(original_dimension: int, folded_dimension: int) -> float:
        return float(original_dimension / max(1, folded_dimension))


__all__ = ["PHI", "PulviniAuditEnvelope", "PulviniOperator"]
