"""Variational diagnostics for the PULVINI manifold threshold functional.

This module does not claim that the threshold functional is derived. It reports
what can be computed from the current density matrix and marks the Penrose-style
collapse gate as unresolved until a real constrained variational derivation and
an empirical mining-convergence criterion are supplied.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict

import numpy as np

_EPS = 1e-12


@dataclass(frozen=True)
class VariationalCertificate:
    functional: str
    tangent_space: str
    gradient: str
    entropy_gradient_abs: float
    coherence_norm: float
    control_energy: float
    tangent_gradient_norm: float
    stationary: bool
    closed: bool
    blocker: str
    required_derivation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def off_diagonal_part(rho: np.ndarray) -> np.ndarray:
    matrix = np.asarray(rho, dtype=np.complex128)
    return matrix - np.diag(np.diag(matrix))


def trace_zero_hermitian_projection(matrix: np.ndarray) -> np.ndarray:
    """Project a matrix onto the Hermitian trace-zero tangent space."""
    projected = (
        np.asarray(matrix, dtype=np.complex128)
        + np.asarray(matrix, dtype=np.complex128).conj().T
    ) / 2.0
    dim = projected.shape[0]
    projected = projected - (np.trace(projected) / dim) * np.eye(
        dim, dtype=np.complex128
    )
    return projected


def variational_certificate(
    rho: np.ndarray,
    entropy_gradient: float,
    *,
    tolerance: float = 1e-9,
) -> VariationalCertificate:
    """Return an honest constrained first-variation diagnostic for C(rho).

    C(rho)=|dS/dt|*||OffDiag(rho)||_F is only a candidate functional. The
    first variation is projected onto the Hermitian trace-zero tangent space of
    density matrices. This is not a Bures-metric derivation and is therefore not
    a closed mathematical certificate.
    """
    off_diag = off_diagonal_part(rho)
    coherence = float(np.linalg.norm(off_diag, ord="fro"))
    entropy_abs = abs(float(entropy_gradient))
    if coherence <= _EPS or entropy_abs <= _EPS:
        raw_gradient = np.zeros_like(off_diag, dtype=np.complex128)
    else:
        raw_gradient = entropy_abs * off_diag / coherence
    tangent_gradient = trace_zero_hermitian_projection(raw_gradient)
    tangent_gradient_norm = float(np.linalg.norm(tangent_gradient, ord="fro"))
    stationary = tangent_gradient_norm <= float(tolerance)
    return VariationalCertificate(
        functional="candidate C(rho)=|dS/dt|*||OffDiag(rho)||_F",
        tangent_space="Hermitian trace-zero density-matrix tangent space; Bures metric not yet derived",
        gradient="projected first variation of C onto trace-zero Hermitian tangent space",
        entropy_gradient_abs=entropy_abs,
        coherence_norm=coherence,
        control_energy=entropy_abs * max(coherence, _EPS),
        tangent_gradient_norm=tangent_gradient_norm,
        stationary=stationary,
        closed=False,
        blocker="candidate functional is diagnostic only; no proof that stationary point equals mining convergence optimum",
        required_derivation="derive C under a chosen density-matrix metric, preferably Bures, and calibrate stationary point against observed share/search convergence",
    )


__all__ = [
    "VariationalCertificate",
    "off_diagonal_part",
    "trace_zero_hermitian_projection",
    "variational_certificate",
]
