"""Composition layer for PULVINI memory state.

This module connects the existing Hebbian memory kernel to the PULVINI phi
compression engine so runtime memory is recorded as compressed working state
plus retained reconstruction kernels.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Sequence

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
        self.kernel = kernel if kernel is not None else HebbianMemoryKernel(window=window)
        compressor_kwargs = {"fold_depth": fold_depth}
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


__all__ = ["PulviniMemoryFabric", "PulviniMemoryFabricSnapshot"]
