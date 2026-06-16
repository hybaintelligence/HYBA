"""Outcome-driven strategy weighting for the PYTHIA optimizer.

The meta optimizer only learns from observed share outcomes and solver telemetry.
It does not synthesize nonces, accepted shares, or production telemetry.
"""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
from typing import Any, Deque, Dict, Iterable, Optional

import numpy as np


@dataclass(frozen=True)
class StrategyPerformance:
    strategy_id: str
    shares_attempted: int
    shares_accepted: int
    avg_phi_resonance: float
    avg_solve_time: float
    thermal_cost: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MetaLearningOptimizer:
    """Bounded gradient-style weighting over observed mining strategies."""

    def __init__(
        self,
        *,
        learning_rate: float = 0.01,
        initial_strategies: Optional[Iterable[str]] = None,
        min_weight: float = 0.05,
        max_weight: float = 20.0,
        rng_seed: Optional[int] = 0,
    ) -> None:
        self.learning_rate = float(learning_rate)
        self.min_weight = float(min_weight)
        self.max_weight = float(max_weight)
        self.strategy_weights: Dict[str, float] = {}
        self.performance_history: Deque[Dict[str, Any]] = deque(maxlen=1000)
        self.thermal_memory: Deque[float] = deque(maxlen=100)
        self._selection_offset = int(rng_seed or 0)
        for strategy_id in initial_strategies or ():
            self.ensure_strategy(strategy_id)

    def ensure_strategy(self, strategy_id: str) -> None:
        strategy_key = str(strategy_id or "configured_solver_search")
        self.strategy_weights.setdefault(strategy_key, 1.0)

    def update_from_outcome(
        self,
        *,
        strategy_id: str,
        accepted: bool,
        phi_resonance: Optional[float],
        thermal_cost: Optional[float],
        solve_time: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Update a strategy weight from a real accepted/rejected share outcome."""
        strategy_key = str(strategy_id or "configured_solver_search")
        self.ensure_strategy(strategy_key)
        phi = float(phi_resonance or 0.0)
        thermal = max(0.0, float(thermal_cost or 0.0))
        reward = (1.0 if accepted else -0.5) + phi - (thermal * 0.1)
        gradient = reward * self.strategy_weights[strategy_key]
        updated = self.strategy_weights[strategy_key] + self.learning_rate * gradient
        self.strategy_weights[strategy_key] = float(
            np.clip(updated, self.min_weight, self.max_weight)
        )
        self.thermal_memory.append(thermal)
        event = {
            "strategy": strategy_key,
            "accepted": bool(accepted),
            "reward": float(reward),
            "weight": self.strategy_weights[strategy_key],
            "phi_resonance": phi,
            "thermal_cost": thermal,
            "solve_time": None if solve_time is None else float(solve_time),
        }
        self.performance_history.append(event)
        return dict(event)

    def strategy_probabilities(self) -> Dict[str, float]:
        if not self.strategy_weights:
            return {}
        strategies = list(self.strategy_weights)
        weights = np.asarray([self.strategy_weights[s] for s in strategies], dtype=float)
        weights = weights - np.max(weights)
        exp_weights = np.exp(weights)
        probabilities = exp_weights / np.sum(exp_weights)
        return {s: float(p) for s, p in zip(strategies, probabilities)}

    def select_strategy(self, job_features: Optional[Dict[str, Any]] = None) -> str:
        """Select a known strategy deterministically from softmax probabilities.

        ``job_features`` is accepted for future feature-conditioned policies; current
        weighting remains outcome-only and auditable.
        """
        del job_features
        if not self.strategy_weights:
            return "golden_ratio_baseline"
        probabilities = self.strategy_probabilities()
        ranked = sorted(probabilities.items(), key=lambda item: (-item[1], item[0]))
        top_probability = ranked[0][1]
        top_strategies = [
            strategy
            for strategy, probability in ranked
            if abs(probability - top_probability) < 1e-12
        ]
        tie_break_index = (self._selection_offset + len(self.performance_history)) % len(
            top_strategies
        )
        return str(top_strategies[tie_break_index])

    def snapshot(self) -> Dict[str, Any]:
        return {
            "learning_rate": self.learning_rate,
            "strategy_weights": dict(self.strategy_weights),
            "strategy_probabilities": self.strategy_probabilities(),
            "recent_performance": list(self.performance_history)[-20:],
            "thermal_memory_size": len(self.thermal_memory),
        }


__all__ = ["MetaLearningOptimizer", "StrategyPerformance"]
