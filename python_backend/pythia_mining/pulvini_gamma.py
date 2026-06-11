"""Empirical gamma estimates for PULVINI Lindblad jump strengths."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Set

import numpy as np

_EPS = 1e-12


@dataclass(frozen=True)
class GammaEstimate:
    node_id: int
    nack_count: int
    observation_count: int
    alpha_prior: float
    beta_prior: float
    gamma: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EmpiricalGammaLedger:
    """Beta-binomial estimator for per-node NACK rate gamma_k."""

    def __init__(self, num_nodes: int, *, alpha_prior: float = 1.0, beta_prior: float = 31.0) -> None:
        self.num_nodes = int(num_nodes)
        self.alpha_prior = float(alpha_prior)
        self.beta_prior = float(beta_prior)
        self.nack_counts = np.zeros(self.num_nodes, dtype=np.float64)
        self.observation_counts = np.zeros(self.num_nodes, dtype=np.float64)

    def record(self, node_id: int, *, nack: bool) -> GammaEstimate:
        node_id = int(node_id)
        self.observation_counts[node_id] += 1.0
        if nack:
            self.nack_counts[node_id] += 1.0
        return self.estimate(node_id)

    def estimate(self, node_id: int) -> GammaEstimate:
        node_id = int(node_id)
        observations = float(self.observation_counts[node_id])
        nacks = float(self.nack_counts[node_id])
        denominator = observations + self.alpha_prior + self.beta_prior
        gamma = (nacks + self.alpha_prior) / max(denominator, _EPS)
        return GammaEstimate(
            node_id=node_id,
            nack_count=int(nacks),
            observation_count=int(observations),
            alpha_prior=self.alpha_prior,
            beta_prior=self.beta_prior,
            gamma=float(gamma),
        )

    def snapshot(self) -> List[Dict[str, Any]]:
        return [self.estimate(node_id).to_dict() for node_id in range(self.num_nodes)]


def jump_operators_from_gamma(
    *,
    node_id: int,
    neighbors: Dict[int, Set[int]],
    gamma: float,
    num_nodes: int,
) -> List[np.ndarray]:
    """Build neighbour jump operators using empirical gamma_k."""
    node_id = int(node_id)
    targets = sorted(neighbors[node_id])
    if not targets:
        return []
    bounded_gamma = min(max(float(gamma), 0.0), 0.95)
    scale = math.sqrt(bounded_gamma / len(targets))
    operators: List[np.ndarray] = []
    for target in targets:
        op = np.zeros((int(num_nodes), int(num_nodes)), dtype=np.complex128)
        op[int(target), node_id] = scale
        operators.append(op)
    return operators


__all__ = ["EmpiricalGammaLedger", "GammaEstimate", "jump_operators_from_gamma"]
