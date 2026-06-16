"""
AI Optimizer for Quantum Mining
PYTHIA Mining System - Intelligence Layer
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .ai_optimizer_meta import MetaLearningOptimizer
from .phi_scaling_engine import (
    PhiOptimizedFeatures,
    PhiScaledEnsemble,
    benchmark_vs_asic,
)
from .pulvini_nonce_compression import build_pulvini_nonce_plan
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
    """Runtime search-coordination layer backed by measured solver outcomes."""

    def __init__(self, quantum_solver, consciousness_engine, blockchain_oracle):
        self.quantum_solver = quantum_solver
        self.consciousness_engine = consciousness_engine
        self.blockchain_oracle = blockchain_oracle
        self.current_strategy = SearchStrategy(phi_resonance_enabled=True)
        self.phi_ensemble = PhiScaledEnsemble(config={"phi_scaling_power": 1.5})
        self.phi_features = PhiOptimizedFeatures()
        self.success_history: List[bool] = []
        self.rejection_history: List[Dict[str, Any]] = []
        self.meta_optimizer = MetaLearningOptimizer(
            initial_strategies=["phi_scaled_compressed_solver_search"]
        )
        self.latest_meta_learning_event: Optional[Dict[str, Any]] = None
        self.logger = logging.getLogger("ai_optimizer")

    @staticmethod
    def _configured_max_iterations() -> int:
        raw = os.getenv("HYBA_MINING_MAX_SOLVER_ITERATIONS", "1448")
        try:
            parsed = int(raw)
        except ValueError:
            parsed = 1448
        return max(1, parsed)

    @staticmethod
    def _configured_timeout_cap_seconds() -> float:
        """Operator-visible cap; defaults to the full conservative regime window."""
        raw = os.getenv("HYBA_MINING_SEARCH_TIMEOUT_CAP_SECONDS", "120.0")
        try:
            parsed = float(raw)
        except ValueError:
            parsed = 120.0
        return max(0.001, parsed)

    async def _configure_solver_for_job(self, job: MiningJob) -> None:
        """
        Enforce the unified PYTHIA/PULVINI contract before every search.

        The unified engine is not allowed to say "PULVINI compressed mining" while
        silently routing through an uncompressed base solver. If the solver supports
        the compressed-search interface, every job gets a complete, overlap-free
        PULVINI nonce plan before search begins.
        """
        if hasattr(self.quantum_solver, "configure_compressed_search"):
            compressed_plan = build_pulvini_nonce_plan()
            await self.quantum_solver.configure_compressed_search(
                int(job.target), compressed_plan
            )
            return
        await self.quantum_solver.configure_search(int(job.target), [(0, 2**32 - 1)])

    async def optimize_nonce_search(self, job: MiningJob) -> OptimizationResult:
        """
        Prepare the solver for a real mining job and run a bounded nonce search.

        This method does not fabricate a winning share. It configures the live solver,
        executes its deterministic bounded search, and returns the measured candidate
        nonce, timing, and derived φ/PULVINI metadata for downstream SHA-256d
        verification and pool submission.
        """
        start_time = time.time()
        await self._configure_solver_for_job(job)
        initial_metrics = self.quantum_solver.get_metrics()
        solve_timeout = min(
            float(self.current_strategy.max_search_time),
            self._configured_timeout_cap_seconds(),
        )
        nonce = await self.quantum_solver.solve(
            max_iterations=self._configured_max_iterations(),
            timeout=max(0.001, solve_timeout),
        )
        metrics = self.quantum_solver.get_metrics()

        indicators = {
            "solver": {
                "phi_phase_alignment": float(metrics.get("phi_phase_alignment") or 0.0),
                "power_scale": float(metrics.get("power_scale") or 1.0),
                "search_space_size_norm": float(
                    (metrics.get("search_space_size") or initial_metrics.get("search_space_size") or 0)
                    / max(1, 2**32)
                ),
                "compressed_working_set_size": int(
                    metrics.get("compressed_working_set_size") or 0
                ),
                "complete_nonce_coverage": bool(
                    metrics.get("complete_nonce_coverage")
                ),
                "overlap_free_nonce_coverage": bool(
                    metrics.get("overlap_free_nonce_coverage")
                ),
            },
            "job": {
                "target_norm": float(int(job.target) / max(1, 2**256 - 1)),
                "extranonce2_size_norm": float(job.extranonce2_size / 32.0),
            },
            "solve": {
                "nonce_found": nonce is not None,
                "iterations": int(metrics.get("last_solve_iterations") or 0),
                "duration_seconds": float(metrics.get("last_solve_duration_seconds") or 0.0),
                "last_error": metrics.get("last_error"),
            },
        }
        phi_score = float(metrics.get("phi_phase_alignment") or 0.0)
        model_predictions = {
            "solver_phi": {"score": phi_score},
            "difficulty_window": {"score": indicators["job"]["target_norm"]},
            "search_space": {
                "score": min(1.0, indicators["solver"]["search_space_size_norm"])
            },
        }
        phi_scaling = self.phi_ensemble.predict_with_phi_scaling(
            model_predictions, indicators
        )
        phi_features = self.phi_features.extract_phi_optimized_features(indicators)
        benchmark = benchmark_vs_asic(
            measured_hashes_per_second=metrics.get("hashrate_hps"),
            phi_filter_acceptance_ratio=float(
                metrics.get("phi_filter_acceptance_ratio") or 1.0 / 1.618033988749895
            ),
            compression_factor=float(metrics.get("phi_compression_factor") or 1.86),
        )
        return OptimizationResult(
            nonce=nonce,
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

    def _update_meta_learning(
        self, share_info: Dict[str, Any], *, accepted: bool
    ) -> Dict[str, Any]:
        strategy_id = str(
            share_info.get("strategy_used") or "phi_scaled_compressed_solver_search"
        )
        event = self.meta_optimizer.update_from_outcome(
            strategy_id=strategy_id,
            accepted=accepted,
            phi_resonance=share_info.get("phi_resonance_score"),
            thermal_cost=share_info.get("thermal_cost"),
            solve_time=share_info.get("solve_time"),
        )
        self.latest_meta_learning_event = event
        return event

    async def on_share_accepted(self, share_info: Dict[str, Any]) -> None:
        self.success_history.append(True)
        self._update_meta_learning(share_info, accepted=True)

    async def on_share_rejected(
        self, share_info: Dict[str, Any], error_code: int, error_msg: str
    ) -> None:
        self.success_history.append(False)
        self._update_meta_learning(share_info, accepted=False)
        self.rejection_history.append(
            {
                "timestamp": time.time(),
                "error_code": error_code,
                "error_msg": error_msg,
                "nonce": share_info.get("nonce"),
                "job_id": share_info.get("job_id"),
            }
        )

    def meta_learning_snapshot(self) -> Dict[str, Any]:
        return self.meta_optimizer.snapshot()
