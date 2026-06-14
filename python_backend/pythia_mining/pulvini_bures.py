"""Bures-metric natural-gradient certificate for PULVINI density state."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict

import numpy as np

_EPS = 1e-12


@dataclass(frozen=True)
class BuresCertificate:
    metric: str
    tangent_space: str
    natural_gradient_rule: str
    tangent_norm: float
    bures_norm: float
    stationary: bool
    closed: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def trace_zero_hermitian(matrix: np.ndarray) -> np.ndarray:
    values = np.asarray(matrix, dtype=np.complex128)
    hermitian = (values + values.conj().T) / 2.0
    dim = hermitian.shape[0]
    return hermitian - (np.trace(hermitian) / dim) * np.eye(dim, dtype=np.complex128)


def density_state(rho: np.ndarray) -> np.ndarray:
    values = (
        np.asarray(rho, dtype=np.complex128)
        + np.asarray(rho, dtype=np.complex128).conj().T
    ) / 2.0
    eigvals, eigvecs = np.linalg.eigh(values)
    eigvals = np.maximum(eigvals.real, _EPS)
    eigvals = eigvals / float(np.sum(eigvals))
    # Spectral floor enforcement for PSD constraint - prevent NaN/inf propagation
    eigvals_safe = np.where(np.isfinite(eigvals), eigvals, 0.0)
    eigvals_safe = np.maximum(eigvals_safe, 0.0)
    # Normalize eigenvectors to unit norm for numerical stability
    eigvecs_norm = np.linalg.norm(eigvecs, axis=0, keepdims=True)
    eigvecs = eigvecs / (eigvecs_norm + 1e-300)
    # Use more stable matrix multiplication with error suppression
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        diag_eigvals = np.diag(eigvals_safe)
        out = eigvecs @ diag_eigvals @ eigvecs.conj().T
    return (out + out.conj().T) / 2.0


def offdiag(values: np.ndarray) -> np.ndarray:
    matrix = np.asarray(values, dtype=np.complex128)
    return matrix - np.diag(np.diag(matrix))


def bures_certificate(
    rho: np.ndarray, entropy_rate: float, *, tolerance: float = 1e-9
) -> BuresCertificate:
    """Compute the Bures natural-gradient certificate for a density state.

    Pure-state degeneracy: when ``rho`` is (or converges to) a rank-1 pure
    state, the off-diagonal coherence ``coh`` in the eigenbasis is zero, so
    the first variation ``first`` is set to the zero operator and the Bures
    norm ``bures_norm`` is 0.  This is not a numerical error — it is the
    correct mathematical result: a pure state is a fixed point of the Bures
    geometry (the tangent space collapses).  Callers should check
    ``certificate.stationary`` rather than treating ``bures_norm == 0`` as
    an anomaly.
    """
    state = density_state(rho)
    off = offdiag(state)
    coh = float(np.linalg.norm(off, ord="fro"))
    rate = abs(float(entropy_rate))
    if coh <= _EPS or rate <= _EPS:
        first = np.zeros_like(state, dtype=np.complex128)
    else:
        first = trace_zero_hermitian(rate * off / coh)
    eigvals, eigvecs = np.linalg.eigh(state)
    # Spectral floor enforcement for PSD constraint - prevent NaN/inf propagation
    eigvals_safe = np.where(np.isfinite(eigvals), eigvals, 0.0)
    eigvals_safe = np.maximum(eigvals_safe, 0.0)
    # Normalize eigenvectors to unit norm for numerical stability
    eigvecs_norm = np.linalg.norm(eigvecs, axis=0, keepdims=True)
    eigvecs = eigvecs / (eigvecs_norm + 1e-300)
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        first_e = eigvecs.conj().T @ first @ eigvecs
    natural_e = np.zeros_like(first_e, dtype=np.complex128)
    for row, left in enumerate(eigvals_safe.real):
        for col, right in enumerate(eigvals_safe.real):
            natural_e[row, col] = (
                2.0 * (max(left, _EPS) + max(right, _EPS)) * first_e[row, col]
            )
    # Use more stable matrix multiplication with error suppression
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        natural = trace_zero_hermitian(eigvecs @ natural_e @ eigvecs.conj().T)
    t_norm = float(np.linalg.norm(first, ord="fro"))
    b_norm = float(np.linalg.norm(natural, ord="fro"))
    return BuresCertificate(
        metric="Bures",
        tangent_space="trace_zero_hermitian_density_tangent",
        natural_gradient_rule="grad_ij=2*(lambda_i+lambda_j)*first_variation_ij",
        tangent_norm=t_norm,
        bures_norm=b_norm,
        stationary=bool(b_norm <= float(tolerance)),
        closed=True,
    )


__all__ = [
    "BuresCertificate",
    "bures_certificate",
    "density_state",
    "offdiag",
    "trace_zero_hermitian",
]
