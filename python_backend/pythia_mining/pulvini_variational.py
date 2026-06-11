"""Variational certificate for the PULVINI manifold threshold functional."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict

import numpy as np

_EPS = 1e-12


@dataclass(frozen=True)
class VariationalCertificate:
    functional: str
    gradient: str
    entropy_gradient_abs: float
    coherence_norm: float
    control_energy: float
    gradient_norm: float
    stationary: bool
    stationary_condition: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def off_diagonal_part(rho: np.ndarray) -> np.ndarray:
    matrix = np.asarray(rho, dtype=np.complex128)
    return matrix - np.diag(np.diag(matrix))


def variational_certificate(
    rho: np.ndarray,
    entropy_gradient: float,
    *,
    tolerance: float = 1e-9,
) -> VariationalCertificate:
    """Return a first-variation certificate for C(rho).

    C(rho) = |dS/dt| * ||OffDiag(rho)||_F.
    The first variation with respect to rho is proportional to
    OffDiag(rho) / ||OffDiag(rho)||_F when the off-diagonal norm is non-zero.
    """
    off_diag = off_diagonal_part(rho)
    coherence = float(np.linalg.norm(off_diag, ord="fro"))
    entropy_abs = abs(float(entropy_gradient))
    if coherence <= _EPS or entropy_abs <= _EPS:
        gradient_norm = 0.0
    else:
        gradient = entropy_abs * off_diag / coherence
        gradient_norm = float(np.linalg.norm(gradient, ord="fro"))
    return VariationalCertificate(
        functional="C(rho)=|dS/dt|*||OffDiag(rho)||_F",
        gradient="deltaC=|dS/dt|*OffDiag(rho)/||OffDiag(rho)||_F",
        entropy_gradient_abs=entropy_abs,
        coherence_norm=coherence,
        control_energy=entropy_abs * max(coherence, _EPS),
        gradient_norm=gradient_norm,
        stationary=gradient_norm <= float(tolerance),
        stationary_condition="stationary iff |dS/dt|=0 or OffDiag(rho)=0",
    )


__all__ = ["VariationalCertificate", "off_diagonal_part", "variational_certificate"]
