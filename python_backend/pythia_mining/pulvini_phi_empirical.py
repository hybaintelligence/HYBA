"""Empirical phi-resonance sampling gate for PULVINI.

This module records a measured datapoint only. It does not claim search advantage.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Iterable, Protocol


class PhiScorer(Protocol):
    def phi_resonance_score(self, nonce: int, job_id: str | None = None) -> float: ...


@dataclass(frozen=True)
class PhiSampleResult:
    job_id: str | None
    threshold: float
    sample_size: int
    accepted: int
    acceptance_ratio: float
    baseline_uniform_ratio: float
    deviation_from_baseline: float
    claim: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def measure_phi_acceptance(
    scorer: PhiScorer,
    nonces: Iterable[int],
    *,
    threshold: float = 0.5,
    job_id: str | None = None,
) -> PhiSampleResult:
    values = [int(nonce) for nonce in nonces]
    accepted = sum(1 for nonce in values if scorer.phi_resonance_score(nonce, job_id=job_id) >= float(threshold))
    sample_size = len(values)
    ratio = 0.0 if sample_size == 0 else accepted / sample_size
    baseline = max(0.0, min(1.0, 1.0 - float(threshold)))
    return PhiSampleResult(
        job_id=job_id,
        threshold=float(threshold),
        sample_size=sample_size,
        accepted=accepted,
        acceptance_ratio=ratio,
        baseline_uniform_ratio=baseline,
        deviation_from_baseline=ratio - baseline,
        claim="measured_datapoint_only_no_search_advantage_claim",
    )


__all__ = ["PhiSampleResult", "measure_phi_acceptance"]
