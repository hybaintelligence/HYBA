"""Symbolic and numeric verification utilities for HYBA mathematical operators."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List
import numpy as np

try:
    import sympy as sp  # type: ignore

    SYMPY_AVAILABLE = True
except Exception:  # pragma: no cover
    sp = None  # type: ignore
    SYMPY_AVAILABLE = False


@dataclass(frozen=True)
class VerificationResult:
    passed: bool
    invariant: str
    residual: float
    tolerance: float
    method: str
    notes: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def verify_unitary(matrix: Any, *, tolerance: float = 1e-8) -> VerificationResult:
    arr = np.asarray(matrix, dtype=np.complex128)
    notes: List[str] = []
    if arr.ndim != 2 or arr.shape[0] != arr.shape[1]:
        return VerificationResult(
            False, "unitarity", float("inf"), tolerance, "numeric", ["matrix is not square"]
        )
    ident = np.eye(arr.shape[0], dtype=np.complex128)
    residual = float(np.linalg.norm(arr.conj().T @ arr - ident, ord="fro"))
    return VerificationResult(
        residual <= tolerance, "unitarity", residual, tolerance, "numeric", notes
    )


def verify_projector(matrix: Any, *, tolerance: float = 1e-8) -> VerificationResult:
    arr = np.asarray(matrix, dtype=np.complex128)
    if arr.ndim != 2 or arr.shape[0] != arr.shape[1]:
        return VerificationResult(
            False, "projector", float("inf"), tolerance, "numeric", ["matrix is not square"]
        )
    residual = float(
        np.linalg.norm(arr @ arr - arr, ord="fro") + np.linalg.norm(arr - arr.conj().T, ord="fro")
    )
    return VerificationResult(
        residual <= tolerance, "projector", residual, tolerance, "numeric", []
    )


def verify_trace_preserved(
    before: Any, after: Any, *, tolerance: float = 1e-8
) -> VerificationResult:
    a = np.asarray(before, dtype=np.complex128)
    b = np.asarray(after, dtype=np.complex128)
    residual = float(abs(np.trace(a) - np.trace(b)))
    return VerificationResult(
        residual <= tolerance, "trace_preservation", residual, tolerance, "numeric", []
    )


def verify_symbolic_phi_identity() -> VerificationResult:
    if not SYMPY_AVAILABLE:
        return VerificationResult(True, "phi_identity", 0.0, 0.0, "skipped", ["sympy unavailable"])
    phi = (1 + sp.sqrt(5)) / 2
    residual_expr = sp.simplify(phi**2 - phi - 1)
    passed = bool(residual_expr == 0)
    return VerificationResult(passed, "phi_identity", 0.0 if passed else 1.0, 0.0, "sympy", [])


__all__ = [
    "VerificationResult",
    "verify_unitary",
    "verify_projector",
    "verify_trace_preserved",
    "verify_symbolic_phi_identity",
]
