"""Choi complete-positivity certificate for PULVINI channel steps."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Dict, Sequence

import numpy as np

HBAR = 1.0


@dataclass(frozen=True)
class ChoiCertificate:
    min_eigenvalue: float
    positive_semidefinite: bool
    kraus_count: int
    trace_preservation_error: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _hermitian(matrix: np.ndarray) -> np.ndarray:
    matrix = np.asarray(matrix, dtype=np.complex128)
    return (matrix + matrix.conj().T) / 2.0


def kraus_operators_for_step(
    hamiltonian: np.ndarray,
    jump_operators: Sequence[np.ndarray],
    *,
    dt: float = 1.0,
) -> list[np.ndarray]:
    """Construct a small-step Kraus representation for CP verification."""
    hamiltonian = _hermitian(hamiltonian)
    dim = int(hamiltonian.shape[0])
    dt = max(float(dt), 0.0)
    identity = np.eye(dim, dtype=np.complex128)
    jumps = [np.asarray(operator, dtype=np.complex128) for operator in jump_operators]

    jump_norm = np.zeros((dim, dim), dtype=np.complex128)
    for operator in jumps:
        jump_norm += operator.conj().T @ operator

    damping_argument = _hermitian(identity - dt * jump_norm)
    damping_eigs, damping_vecs = np.linalg.eigh(damping_argument)
    damping_eigs = np.clip(damping_eigs.real, 0.0, None)
    k0_damping = damping_vecs @ np.diag(np.sqrt(damping_eigs)) @ damping_vecs.conj().T

    h_eigs, h_vecs = np.linalg.eigh(hamiltonian)
    unitary = h_vecs @ np.diag(np.exp((-1j * h_eigs * dt) / HBAR)) @ h_vecs.conj().T
    return [unitary @ k0_damping] + [math.sqrt(dt) * unitary @ operator for operator in jumps]


def choi_certificate(kraus_operators: Sequence[np.ndarray], *, tolerance: float = 1e-9) -> ChoiCertificate:
    """Return PSD and trace-preservation checks for a Kraus channel."""
    operators = [np.asarray(operator, dtype=np.complex128) for operator in kraus_operators]
    if not operators:
        return ChoiCertificate(0.0, True, 0, 0.0)

    vectors = [operator.reshape(-1, order="F") for operator in operators]
    gram = np.array([[np.vdot(left, right) for right in vectors] for left in vectors], dtype=np.complex128)
    eigenvalues = np.linalg.eigvalsh(_hermitian(gram)).real
    min_eigenvalue = float(np.min(eigenvalues)) if eigenvalues.size else 0.0

    dim = int(operators[0].shape[0])
    trace_matrix = np.zeros((dim, dim), dtype=np.complex128)
    for operator in operators:
        trace_matrix += operator.conj().T @ operator
    trace_error = float(np.linalg.norm(trace_matrix - np.eye(dim), ord="fro"))

    return ChoiCertificate(
        min_eigenvalue=min_eigenvalue,
        positive_semidefinite=bool(min_eigenvalue >= -float(tolerance)),
        kraus_count=len(operators),
        trace_preservation_error=trace_error,
    )


__all__ = ["ChoiCertificate", "choi_certificate", "kraus_operators_for_step"]
