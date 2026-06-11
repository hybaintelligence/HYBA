"""Memory-kernel diagnostics for PULVINI open-system updates.

When Hebbian weights are active, the environment is memory-bearing. This module
prevents the runtime from claiming a memoryless Markov model unless the measured
memory kernel is effectively zero.
"""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
from typing import Any, Deque, Dict, Iterable, List, Sequence

import numpy as np


@dataclass(frozen=True)
class MemoryKernelCertificate:
    model: str
    markovian: bool
    kernel_norm: float
    memory_events: int
    blocker: str | None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class HebbianMemoryKernel:
    """Finite-memory kernel for synaptic updates and NACK/share events."""

    def __init__(self, *, window: int = 64, decay: float = 0.85) -> None:
        self.window = int(window)
        self.decay = float(decay)
        self.events: Deque[np.ndarray] = deque(maxlen=self.window)

    def record_delta(self, delta_matrix: np.ndarray) -> None:
        self.events.append(np.asarray(delta_matrix, dtype=np.float64))

    def record_path(self, num_nodes: int, path: Sequence[int], reward: float) -> None:
        delta = np.zeros((int(num_nodes), int(num_nodes)), dtype=np.float64)
        for left, right in zip(path, path[1:]):
            delta[int(left), int(right)] += float(reward)
            delta[int(right), int(left)] += float(reward)
        self.record_delta(delta)

    def kernel_matrix(self) -> np.ndarray:
        if not self.events:
            return np.zeros((0, 0), dtype=np.float64)
        result = np.zeros_like(self.events[-1], dtype=np.float64)
        for index, event in enumerate(reversed(self.events)):
            result += (self.decay ** index) * event
        return result

    def certificate(self, *, tolerance: float = 1e-12) -> MemoryKernelCertificate:
        kernel = self.kernel_matrix()
        norm = float(np.linalg.norm(kernel, ord="fro")) if kernel.size else 0.0
        markovian = norm <= float(tolerance)
        return MemoryKernelCertificate(
            model="non_markovian_memory_kernel" if not markovian else "markovian_limit",
            markovian=markovian,
            kernel_norm=norm,
            memory_events=len(self.events),
            blocker=None if markovian else "Hebbian memory is active; use memory-kernel diagnostics, not a memoryless Lindblad-only claim",
        )


__all__ = ["HebbianMemoryKernel", "MemoryKernelCertificate"]
