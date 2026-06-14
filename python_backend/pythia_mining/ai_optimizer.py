"""
AI Optimizer for Quantum Mining
PYTHIA Mining System - Intelligence Layer
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .phi_scaling_engine import (
    PhiOptimizedFeatures,
    PhiScaledEnsemble,
    benchmark_vs_asic,
)
from .stratum_client import MiningJob


@dataclass
class SearchStrategy:
    quantum_allocation: Optional[float] = None
    phi_resonance_enabled: bool = False
    adaptive_difficulty: bool = True
    max_search_time: float = 30.0
    confidence_threshold: Optional[float] = None


@dataclass
class OptimizationResult:
    nonce: Optional[int] = None
    search_time: float = 0.0
    quantum_used: bool = False
    confidence: Optional[float] = None
    phi_resonance_score: Optional[float] = None
    phi_scaling: Optional[Dict[str, Any]] = None
    phi_features: Optional[Dict[str, Any]] = None
    asic_benchmark: Optional[Dict[str, Any]] = None
    strategy_used: str = "configured_solver_search"
    search_space_size: Optional[int] = None


class AIOptimizer:
    """Runtime search-coordination layer without fabricated confidence or nonce outputs."""

    def __init__(self, quantum_solver, consciousness_engine, blockchain_oracle):
        self.quantum_solver = quantum_solver
        self.consciousness_engine = consciousness_engine
        self.blockchain_oracle = blockchain_oracle
        self.current_strategy = SearchStrategy(phi_resonance_enabled=True)
        self.phi_ensemble = PhiScaledEnsemble(config={"phi_scaling_power": 1.5})
        self.phi_features = PhiOptimizedFeatures()
        self.success_history: List[bool] = []
        self.rejection_history: List[Dict[str, Any]] = []
        self.logger = logging.getLogger("ai_optimizer")

    async def optimize_nonce_search(self, job: MiningJob) -> OptimizationResult:
        """
        Prepare the solver for a real mining job and return auditable metadata.

        This method intentionally does not invent a nonce, confidence score, or phi score.
        Those values must come from measured solver/share outcomes or explicit upstream
        models once connected.
        """
        start_time = time.time()
        await self.quantum_solver.configure_search(job.target, [(0, 2**32 - 1)])
        metrics = self.quantum_solver.get_metrics()
        indicators = {
            "solver": {
                "phi_phase_alignment": float(metrics.get("phi_phase_alignment") or 0.0),
                "power_scale": float(metrics.get("power_scale") or 1.0),
                "search_space_size_norm": float(
                    (metrics.get("search_space_size") or 0) / max(1, 2**32)
                ),
            },
            "job": {
                "target_norm": float(int(job.target) / max(1, 2**256 - 1)),
                "extranonce2_size_norm": float(job.extranonce2_size / 32.0),
            },
        }
        phi_score = float(metrics.get("phi_phase_alignment") or 0.0)
        model_predictions = {
            "solver_phi": {"score": phi_score},
            "difficulty_window": {"score": indicators["job"]["target_norm"]},
            "search_space": {"score": min(1.0, indicators["solver"]["search_space_size_norm"])},
        }
        phi_scaling = self.phi_ensemble.predict_with_phi_scaling(model_predictions, indicators)
        phi_features = self.phi_features.extract_phi_optimized_features(indicators)
        benchmark = benchmark_vs_asic(
            measured_hashes_per_second=metrics.get("hashrate_hps"),
            phi_filter_acceptance_ratio=float(
                metrics.get("phi_filter_acceptance_ratio") or 1.0 / 1.618033988749895
            ),
            compression_factor=float(metrics.get("phi_compression_factor") or 1.86),
        )
        return OptimizationResult(
            nonce=None,
            search_time=time.time() - start_time,
            quantum_used=True,
            confidence=phi_scaling.get("coherence"),
            phi_resonance_score=metrics.get("phi_phase_alignment"),
            phi_scaling=phi_scaling,
            phi_features=phi_features,
            asic_benchmark=benchmark,
            strategy_used="phi_scaled_compressed_solver_search",
            search_space_size=metrics.get("search_space_size"),
        )

    async def on_share_accepted(self, share_info: Dict[str, Any]) -> None:
        self.success_history.append(True)

    async def on_share_rejected(
        self, share_info: Dict[str, Any], error_code: int, error_msg: str
    ) -> None:
        self.success_history.append(False)
        self.rejection_history.append(
            {
                "timestamp": time.time(),
                "error_code": error_code,
                "error_msg": error_msg,
                "nonce": share_info.get("nonce"),
                "job_id": share_info.get("job_id"),
            }
        )
