"""Composition layer for PULVINI memory state.

This module connects the existing Hebbian memory kernel to the PULVINI phi
compression engine so runtime memory is recorded as compressed working state
plus retained reconstruction kernels.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Sequence, Tuple

import numpy as np

from .pulvini_memory import HebbianMemoryKernel
from .pulvini_phi_memory import PulviniPhiMemoryCompressionEngine


@dataclass(frozen=True)
class PulviniMemoryFabricSnapshot:
    kernel: Dict[str, Any]
    compression: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PulviniMemoryFabric:
    """Runtime memory fabric backed by phi compression and retained kernels."""

    def __init__(
        self,
        *,
        num_nodes: int = 32,
        window: int = 64,
        fold_depth: int = 2,
        kernel: Any | None = None,
        compressor: PulviniPhiMemoryCompressionEngine | None = None,
        tolerance: float | None = None,
    ) -> None:
        self.num_nodes = int(num_nodes)
        self.kernel = (
            kernel if kernel is not None else HebbianMemoryKernel(window=window)
        )
        compressor_kwargs = {"fold_depth": fold_depth, "sparse_skip_threshold": 1.0}
        if tolerance is not None:
            compressor_kwargs["tolerance"] = float(tolerance)
        self.compressor = (
            compressor
            if compressor is not None
            else PulviniPhiMemoryCompressionEngine(**compressor_kwargs)
        )

    def record_path(self, path: Sequence[int], reward: float) -> None:
        self.kernel.record_path(self.num_nodes, path, reward)

    def record_delta(self, delta_matrix: np.ndarray) -> None:
        self.kernel.record_delta(delta_matrix)

    def compressed_kernel_snapshot(self) -> PulviniMemoryFabricSnapshot:
        matrix = self.kernel.kernel_matrix()
        if matrix.size == 0:
            matrix = np.zeros((self.num_nodes, self.num_nodes), dtype=np.float64)
        compressed = self.compressor.compress(matrix)
        return PulviniMemoryFabricSnapshot(
            kernel=self.kernel.certificate().to_dict(),
            compression=compressed.as_dict(),
        )


class EvolvingMemoryFabric(PulviniMemoryFabric):
    """Hebbian memory fabric that retains successful route reinforcement traces."""

    def __init__(self, *args: Any, hebbian_rate: float = 0.05, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.hebbian_rate = float(hebbian_rate)
        self.success_traces: Dict[Tuple[int, int], float] = {}

    def reinforce_successful_path(self, path: Sequence[int], reward: float) -> None:
        cleaned_path = [int(node_id) for node_id in path]
        bounded_reward = float(reward)
        for left, right in zip(cleaned_path, cleaned_path[1:]):
            edge = (left, right)
            self.success_traces[edge] = (
                self.success_traces.get(edge, 0.0) + bounded_reward
            )

        delta = np.zeros((self.num_nodes, self.num_nodes), dtype=np.float64)
        for (left, right), strength in self.success_traces.items():
            if 0 <= left < self.num_nodes and 0 <= right < self.num_nodes:
                delta[left, right] += self.hebbian_rate * strength
                delta[right, left] += self.hebbian_rate * strength
        self.record_delta(delta)

    def prune_weak_connections(self, threshold: float = 0.01) -> None:
        kernel_matrix = self.kernel.kernel_matrix()
        if kernel_matrix.size == 0:
            return
        pruned = kernel_matrix * (np.abs(kernel_matrix) > float(threshold))
        replacement = HebbianMemoryKernel(
            window=getattr(self.kernel, "window", 64),
            decay=getattr(self.kernel, "decay", 0.85),
        )
        replacement.record_delta(pruned)
        self.kernel = replacement
        self.success_traces = {
            edge: strength
            for edge, strength in self.success_traces.items()
            if abs(strength * self.hebbian_rate) > float(threshold)
        }


__all__ = ["EvolvingMemoryFabric", "PulviniMemoryFabric", "PulviniMemoryFabricSnapshot"]
