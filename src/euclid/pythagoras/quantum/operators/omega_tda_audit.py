"""
Production-grade Ω-Signature Topological Data Analysis audit utilities.

This module is deliberately substrate-agnostic. It does not claim to prove that
an arbitrary compression preserves all topology; instead it creates an auditable,
deterministic contract for comparing pre/post compression topological signatures.

Design goals:
- deterministic output for enterprise reproducibility;
- no mandatory heavy TDA dependency;
- optional persistent-homology support when ripser is installed;
- strict input validation for adversarial / malformed payloads;
- stable JSON-serialisable audit envelopes.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

try:  # Optional dependency. Tests do not require it.
    from ripser import ripser  # type: ignore
    _RIPSER_AVAILABLE = True
except Exception:  # pragma: no cover - environment dependent
    ripser = None  # type: ignore
    _RIPSER_AVAILABLE = False


_EPS = 1e-12


class OmegaAuditError(ValueError):
    """Raised when Ω-Signature inputs are invalid or unsafe."""


@dataclass(frozen=True)
class PersistenceSummary:
    """Compact, deterministic summary of a persistence diagram."""

    dimension: int
    feature_count: int
    finite_feature_count: int
    max_lifetime: float
    total_persistence: float
    entropy: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OmegaSignature:
    """Serializable Ω-Signature envelope."""

    sample_count: int
    feature_dimension: int
    singular_spectrum: List[float]
    laplacian_spectrum: List[float]
    betti_proxy: Dict[str, int]
    persistence: List[PersistenceSummary]
    method: str

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["persistence"] = [p.to_dict() for p in self.persistence]
        return data


@dataclass(frozen=True)
class OmegaAuditResult:
    """Result of comparing two Ω-Signatures."""

    stable: bool
    score: float
    threshold: float
    singular_distance: float
    laplacian_distance: float
    betti_delta: Dict[str, int]
    reference: OmegaSignature
    candidate: OmegaSignature
    notes: List[str]

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["reference"] = self.reference.to_dict()
        data["candidate"] = self.candidate.to_dict()
        return data


def _as_2d_points(data: Any, *, max_points: int = 512) -> np.ndarray:
    """Convert tensors / TT cores / nested arrays into a bounded point cloud."""

    if isinstance(data, (list, tuple)) and data and all(hasattr(x, "shape") for x in data):
        flat = [np.asarray(x, dtype=float).reshape(-1) for x in data]
        max_len = max((x.size for x in flat), default=0)
        if max_len == 0:
            raise OmegaAuditError("Cannot audit empty TT/MPS cores")
        padded = np.zeros((len(flat), max_len), dtype=float)
        for i, core in enumerate(flat):
            padded[i, : core.size] = core
        arr = padded
    else:
        arr = np.asarray(data, dtype=float)

    if arr.size == 0:
        raise OmegaAuditError("Cannot audit empty tensor")
    if not np.all(np.isfinite(arr)):
        raise OmegaAuditError("Ω-Signature input contains NaN or infinite values")

    if arr.ndim == 1:
        # Delay embedding creates a tiny point cloud while preserving ordering.
        if arr.size < 2:
            arr = np.array([[float(arr[0]), 0.0]])
        else:
            arr = np.column_stack([arr[:-1], arr[1:]])
    else:
        arr = arr.reshape(arr.shape[0], -1)

    # Deterministic downsampling: evenly spaced indices, not random sampling.
    if arr.shape[0] > max_points:
        idx = np.linspace(0, arr.shape[0] - 1, max_points).round().astype(int)
        arr = arr[idx]

    # Standardise features to make distances scale-robust.
    mean = arr.mean(axis=0, keepdims=True)
    std = arr.std(axis=0, keepdims=True)
    arr = (arr - mean) / np.where(std < _EPS, 1.0, std)
    return arr.astype(float, copy=False)


def _pairwise_distances(points: np.ndarray) -> np.ndarray:
    diffs = points[:, None, :] - points[None, :, :]
    dist = np.sqrt(np.maximum(np.sum(diffs * diffs, axis=-1), 0.0))
    np.fill_diagonal(dist, 0.0)
    return dist


def _spectral_entropy(values: np.ndarray) -> float:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values) & (values > _EPS)]
    if values.size == 0:
        return 0.0
    probs = values / values.sum()
    return float(-np.sum(probs * np.log(probs + _EPS)))


def _laplacian_spectrum(dist: np.ndarray, k: int) -> np.ndarray:
    if dist.shape[0] <= 1:
        return np.zeros(k, dtype=float)
    sigma = np.median(dist[dist > 0]) if np.any(dist > 0) else 1.0
    weights = np.exp(-(dist ** 2) / (2.0 * max(float(sigma), _EPS) ** 2))
    np.fill_diagonal(weights, 0.0)
    degree = np.diag(weights.sum(axis=1))
    lap = degree - weights
    vals = np.linalg.eigvalsh(lap)
    vals = np.sort(np.real(vals))
    if vals.size < k:
        vals = np.pad(vals, (0, k - vals.size))
    return vals[:k]


def _persistence_summary(diagram: np.ndarray, dimension: int) -> PersistenceSummary:
    if diagram.size == 0:
        return PersistenceSummary(dimension, 0, 0, 0.0, 0.0, 0.0)
    births = diagram[:, 0]
    deaths = diagram[:, 1]
    finite = np.isfinite(deaths)
    lifetimes = np.maximum(deaths[finite] - births[finite], 0.0)
    return PersistenceSummary(
        dimension=dimension,
        feature_count=int(diagram.shape[0]),
        finite_feature_count=int(np.sum(finite)),
        max_lifetime=float(lifetimes.max()) if lifetimes.size else 0.0,
        total_persistence=float(lifetimes.sum()) if lifetimes.size else 0.0,
        entropy=_spectral_entropy(lifetimes),
    )


def compute_omega_signature(
    data: Any,
    *,
    max_points: int = 512,
    spectrum_size: int = 16,
    max_homology_dimension: int = 1,
) -> OmegaSignature:
    """Compute a deterministic Ω-Signature for a tensor or TT/MPS cores.

    The signature combines algebraic spectra with persistent homology when ripser
    is available. Without ripser, it falls back to a Laplacian/Betti proxy that is
    deterministic and cheap enough for CI.
    """

    if max_points < 8:
        raise OmegaAuditError("max_points must be >= 8")
    if spectrum_size < 4:
        raise OmegaAuditError("spectrum_size must be >= 4")

    points = _as_2d_points(data, max_points=max_points)
    dist = _pairwise_distances(points)

    _, singular, _ = np.linalg.svd(points, full_matrices=False)
    singular = singular[:spectrum_size]
    if singular.size < spectrum_size:
        singular = np.pad(singular, (0, spectrum_size - singular.size))

    lap = _laplacian_spectrum(dist, spectrum_size)
    zero_modes = int(np.sum(lap < 1e-7))
    spectral_gap = float(lap[zero_modes]) if zero_modes < lap.size else 0.0

    persistence: List[PersistenceSummary] = []
    method = "laplacian_proxy"
    betti_proxy = {"b0": max(1, zero_modes), "b1": int(max(0, np.sum(lap < 1e-3) - zero_modes)), "spectral_gap_scaled": int(round(spectral_gap * 1_000_000))}

    if _RIPSER_AVAILABLE:
        try:  # pragma: no cover - depends on optional package
            diagrams = ripser(points, maxdim=max_homology_dimension)["dgms"]
            persistence = [_persistence_summary(np.asarray(d), dim) for dim, d in enumerate(diagrams)]
            method = "ripser_persistent_homology"
            if persistence:
                betti_proxy["b0"] = persistence[0].feature_count
            if len(persistence) > 1:
                betti_proxy["b1"] = persistence[1].finite_feature_count
        except Exception:
            persistence = []
            method = "laplacian_proxy_after_ripser_failure"

    if not persistence:
        persistence = [
            PersistenceSummary(0, betti_proxy["b0"], betti_proxy["b0"], float(lap[0]) if lap.size else 0.0, float(np.sum(lap[:3])), _spectral_entropy(lap[:3])),
            PersistenceSummary(1, betti_proxy["b1"], betti_proxy["b1"], float(spectral_gap), float(np.sum(lap[1:4])), _spectral_entropy(lap[1:4])),
        ]

    return OmegaSignature(
        sample_count=int(points.shape[0]),
        feature_dimension=int(points.shape[1]),
        singular_spectrum=[float(x) for x in singular],
        laplacian_spectrum=[float(x) for x in lap],
        betti_proxy=betti_proxy,
        persistence=persistence,
        method=method,
    )


def compare_omega_signatures(
    reference: Any,
    candidate: Any,
    *,
    threshold: float = 0.15,
    max_points: int = 512,
    spectrum_size: int = 16,
) -> OmegaAuditResult:
    """Compare two tensors/cores and determine Ω-stability.

    Score is a weighted relative distance of singular and Laplacian spectra plus
    a bounded Betti-proxy penalty. Lower is better.
    """

    if not (0.0 < threshold < 1.0):
        raise OmegaAuditError("threshold must be between 0 and 1")

    sig_a = compute_omega_signature(reference, max_points=max_points, spectrum_size=spectrum_size)
    sig_b = compute_omega_signature(candidate, max_points=max_points, spectrum_size=spectrum_size)

    s_a = np.asarray(sig_a.singular_spectrum)
    s_b = np.asarray(sig_b.singular_spectrum)
    l_a = np.asarray(sig_a.laplacian_spectrum)
    l_b = np.asarray(sig_b.laplacian_spectrum)

    singular_distance = float(np.linalg.norm(s_a - s_b) / (np.linalg.norm(s_a) + _EPS))
    laplacian_distance = float(np.linalg.norm(l_a - l_b) / (np.linalg.norm(l_a) + _EPS))

    betti_delta = {
        key: int(abs(sig_a.betti_proxy.get(key, 0) - sig_b.betti_proxy.get(key, 0)))
        for key in sorted(set(sig_a.betti_proxy) | set(sig_b.betti_proxy))
    }
    betti_penalty = min(1.0, sum(betti_delta.values()) / 10.0)
    score = float(0.45 * singular_distance + 0.45 * laplacian_distance + 0.10 * betti_penalty)

    notes: List[str] = []
    if sig_a.method != sig_b.method:
        notes.append(f"Different signature methods used: {sig_a.method} vs {sig_b.method}")
    if score >= threshold:
        notes.append("Ω-Signature drift exceeded threshold")

    return OmegaAuditResult(
        stable=bool(score < threshold),
        score=score,
        threshold=float(threshold),
        singular_distance=singular_distance,
        laplacian_distance=laplacian_distance,
        betti_delta=betti_delta,
        reference=sig_a,
        candidate=sig_b,
        notes=notes,
    )


__all__ = [
    "OmegaAuditError",
    "PersistenceSummary",
    "OmegaSignature",
    "OmegaAuditResult",
    "compute_omega_signature",
    "compare_omega_signatures",
]
