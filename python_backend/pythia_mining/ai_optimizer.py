"""
AI Optimizer for Quantum Mining
PYTHIA Mining System - Intelligence Layer
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

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
    strategy_used: str = "configured_solver_search"
    search_space_size: Optional[int] = None


class AIOptimizer:
    """Runtime search-coordination layer without fabricated confidence or nonce outputs."""

    def __init__(self, quantum_solver, consciousness_engine, blockchain_oracle):
        self.quantum_solver = quantum_solver
        self.consciousness_engine = consciousness_engine
        self.blockchain_oracle = blockchain_oracle
        self.current_strategy = SearchStrategy()
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
        return OptimizationResult(
            nonce=None,
            search_time=time.time() - start_time,
            quantum_used=True,
            confidence=None,
            phi_resonance_score=metrics.get("phi_phase_alignment"),
            strategy_used="configured_solver_search",
            search_space_size=metrics.get("search_space_size"),
        )

    async def on_share_accepted(self, share_info: Dict[str, Any]) -> None:
        self.success_history.append(True)

    async def on_share_rejected(self, share_info: Dict[str, Any], error_code: int, error_msg: str) -> None:
        self.success_history.append(False)
        self.rejection_history.append({
            "timestamp": time.time(),
            "error_code": error_code,
            "error_msg": error_msg,
            "nonce": share_info.get("nonce"),
            "job_id": share_info.get("job_id"),
        })
