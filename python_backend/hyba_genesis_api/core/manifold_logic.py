"""Compatibility facade for topological/geometric manifold logic."""

from __future__ import annotations

from typing import Sequence

from hyba_genesis_api.core.intelligence_manifold import IntelligenceManifold


class ManifoldLogic(IntelligenceManifold):
    """Production facade exposing the requested manifold-method names."""

    def calculate_euler_characteristic(self, nodes: int, edges: int) -> int:
        return self.compute_euler_characteristic(nodes, edges)

    def calculate_fisher_curvature(self, state_vector: Sequence[complex]) -> float:  # type: ignore[override]
        magnitudes = [abs(value) for value in state_vector]
        return super().calculate_fisher_curvature(magnitudes)

    def ricci_flow_smoothing(self, curvature: float, complexity: float) -> float:
        smoothed = super().calculate_ricci_flow(curvature)
        return self.stabilizer.preserve_volume(smoothed, complexity)
