from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

import numpy as np

from .omega_signature import OmegaSignatureChecker
from .pulvini_scaling import PulviniOperator
from .tensor_train import TensorTrain, TensorTrainCompressor

PHI = (1.0 + sqrt(5.0)) / 2.0


@dataclass(frozen=True)
class PulviniHybridResult:
    status: str
    folded_dimension: int
    tt_ranks: list[int]
    reduction_ratio: float
    roundtrip_error: float
    omega_stable: bool
    deterministic_work_rate: float


class PulviniHybridPipeline:
    def __init__(self, max_rank: int = 32, tolerance: float = 1e-6) -> None:
        self.pulvini = PulviniOperator(tolerance=tolerance)
        self.tt = TensorTrainCompressor(max_rank=max_rank, tolerance=max(tolerance, 1e-10))
        self.omega = OmegaSignatureChecker(tolerance=0.12)
        self.tolerance = tolerance

    def reduce(self, tensor: np.ndarray) -> tuple[TensorTrain, PulviniHybridResult]:
        arr = np.asarray(tensor, dtype=np.complex128)
        flat = arr.reshape(-1)
        before_sig = self.omega.signature(flat)
        folded, kernel = self.pulvini.fold(flat)
        reconstructed = self.pulvini.unfold(folded, kernel, flat.size)
        roundtrip_error = float(
            np.linalg.norm(flat - reconstructed) / max(1.0, np.linalg.norm(flat))
        )

        target_shape = self._balanced_shape(folded.size)
        folded_tensor = folded[: int(np.prod(target_shape))].reshape(target_shape)
        train = self.tt.reduce(folded_tensor)
        after_sig = self.omega.signature(train.reconstruct().reshape(-1))
        omega_stable = self.omega.is_stable(before_sig, after_sig)
        ratio = float(flat.size / max(1, train.storage))
        work_rate = self.pulvini.deterministic_work_rate(flat.size, folded.size)
        status = "ready" if roundtrip_error <= self.tolerance else "review_required"
        return train, PulviniHybridResult(
            status=status,
            folded_dimension=int(folded.size),
            tt_ranks=train.ranks,
            reduction_ratio=ratio,
            roundtrip_error=roundtrip_error,
            omega_stable=omega_stable,
            deterministic_work_rate=work_rate,
        )

    @staticmethod
    def _balanced_shape(size: int) -> tuple[int, int]:
        if size <= 1:
            return (1, 1)
        rows = max(1, int(np.sqrt(size)))
        while rows > 1 and size % rows != 0:
            rows -= 1
        return rows, int(size / rows)


__all__ = ["PulviniHybridPipeline", "PulviniHybridResult"]
