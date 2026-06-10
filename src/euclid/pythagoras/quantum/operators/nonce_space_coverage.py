"""
nonce_space_coverage.py — Dodecahedron + Icosahedron overlay for 32 workers.
Deterministic nonce space coverage using Platonic solid geometry linked
to the Golden Ratio (Φ).
"""

from __future__ import annotations

from typing import List, Optional

import numpy as np

PHI = (1.0 + np.sqrt(5.0)) / 2.0


class PlatonicNonceOverlay:
    """
    Production coverage of the Φ-folded nonce space using dual Platonic solids.
    Icosahedron (12 vertices) + Dodecahedron (20 vertices) = 32 coverage points
    for 32 parallel workers.
    """

    # Standardized Icosahedron vertices (normalized to unit sphere)
    ICOSAHEDRON_VERTICES = np.array([
        [0.0, 1.0, PHI], [0.0, -1.0, PHI], [0.0, 1.0, -PHI], [0.0, -1.0, -PHI],
        [1.0, PHI, 0.0], [-1.0, PHI, 0.0], [1.0, -PHI, 0.0], [-1.0, -PHI, 0.0],
        [PHI, 0.0, 1.0], [-PHI, 0.0, 1.0], [PHI, 0.0, -1.0], [-PHI, 0.0, -1.0],
    ], dtype=np.float64)

    # Standardized Dodecahedron vertices (normalized to unit sphere)
    DODECAHEDRON_VERTICES = np.array([
        [1.0, 1.0, 1.0], [1.0, 1.0, -1.0], [1.0, -1.0, 1.0], [1.0, -1.0, -1.0],
        [-1.0, 1.0, 1.0], [-1.0, 1.0, -1.0], [-1.0, -1.0, 1.0], [-1.0, -1.0, -1.0],
        [0.0, 1.0 / PHI, PHI], [0.0, -1.0 / PHI, PHI], [0.0, 1.0 / PHI, -PHI], [0.0, -1.0 / PHI, -PHI],
        [1.0 / PHI, PHI, 0.0], [-1.0 / PHI, PHI, 0.0], [1.0 / PHI, -PHI, 0.0], [-1.0 / PHI, -PHI, 0.0],
        [PHI, 0.0, 1.0 / PHI], [-PHI, 0.0, 1.0 / PHI], [PHI, 0.0, -1.0 / PHI], [-PHI, 0.0, -1.0 / PHI],
    ], dtype=np.float64)

    def __init__(self) -> None:
        # Normalize both solids to unit sphere
        icos = self.ICOSAHEDRON_VERTICES / np.linalg.norm(
            self.ICOSAHEDRON_VERTICES, axis=1, keepdims=True
        )
        dodec = self.DODECAHEDRON_VERTICES / np.linalg.norm(
            self.DODECAHEDRON_VERTICES, axis=1, keepdims=True
        )
        # Combine: 32 unique points
        self.coverage_points = np.vstack([icos, dodec])
        # Ensure exactly 32 (some coordinates may be shared)
        if self.coverage_points.shape[0] > 32:
            self.coverage_points = self.coverage_points[:32]
        elif self.coverage_points.shape[0] < 32:
            # Pad with Fibonacci sphere points
            n_extra = 32 - self.coverage_points.shape[0]
            extra = self._fibonacci_sphere(n_extra)
            self.coverage_points = np.vstack([self.coverage_points, extra])
        # Final normalization
        self.coverage_points /= np.linalg.norm(
            self.coverage_points, axis=1, keepdims=True
        )
        # Eliminate any duplicate rows (tol=1e-8)
        _, unique_idx = np.unique(
            self.coverage_points.round(8), axis=0, return_index=True
        )
        self.coverage_points = self.coverage_points[np.sort(unique_idx)]

    @staticmethod
    def _fibonacci_sphere(n: int) -> np.ndarray:
        """Generate n points on a unit sphere using Fibonacci (golden angle) lattice."""
        indices = np.arange(n, dtype=float) + 0.5
        theta = np.arccos(1.0 - 2.0 * indices / n)
        phi_angles = 2.0 * np.pi * indices / PHI
        pts = np.column_stack([
            np.sin(theta) * np.cos(phi_angles),
            np.sin(theta) * np.sin(phi_angles),
            np.cos(theta),
        ])
        pts /= np.linalg.norm(pts, axis=1, keepdims=True)
        return pts

    def get_full_coverage(self) -> np.ndarray:
        """Return the full 32-point coverage overlay (minimizes to available)."""
        return self.coverage_points[:32].copy()

    def get_worker_assignments(self, num_workers: int = 32) -> List[np.ndarray]:
        """Split points across workers for deterministic nonce space coverage."""
        points = self.get_full_coverage()
        if num_workers < 1:
            raise ValueError("num_workers must be >= 1")
        return [
            points[i :: num_workers] for i in range(min(num_workers, len(points)))
        ]


__all__ = ["PlatonicNonceOverlay"]