"""
Genesis AI - Main Orchestrator Core
PYTHIA Mining System - Central Control Layer
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

try:
    import psutil
except ImportError:
    psutil = None

from .ai_optimizer import AIOptimizer
from .blockchain_oracle import BlockchainOracle
from .consciousness_engine import ConsciousnessEngine
from .quantum_solver import DodecahedralQuantumSolver
from .stratum_client import AllPoolsOfflineError, MiningJob, PoolManager


@dataclass
class SystemMetrics:
    timestamp: float = field(default_factory=time.time)
    mining_metrics: Dict[str, Any] = field(default_factory=dict)
    quantum_metrics: Dict[str, Any] = field(default_factory=dict)
    consciousness_metrics: Dict[str, Any] = field(default_factory=dict)
    system_health: Dict[str, Any] = field(default_factory=dict)


class GenesisAI:
    """
    Production orchestration layer.

    The daemon consumes real Stratum events, solves only known jobs, validates shares
    locally, and submits valid shares to a live pool before counting acceptance.
    Development fixtures remain opt-in and are disabled by default in production.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pool_manager = PoolManager(config.get("pools", {}))
        self.quantum_solver = DodecahedralQuantumSolver()
        self.blockchain_oracle = BlockchainOracle()
        self.consciousness_engine = ConsciousnessEngine()
        self.ai_optimizer = AIOptimizer(
            self.quantum_solver,
            self.consciousness_engine,
            self.blockchain_oracle,
        )
        self.is_running = False
        self.current_job: Optional[MiningJob] = None
        self.metrics_history: List[SystemMetrics] = []
        self.repair_count = 0
        self.start_time = time.time()
        self.logger = logging.getLogger("genesis_ai")
        self.failure_counter = 0
        self.jobs_received = 0
        self.shares_solved = 0
        self.health_status = "STARTING"
        self.allow_dev_fixture_jobs = (
            os.getenv("NODE_ENV", os.getenv("HYBA_ENV", "development")).lower() != "production"
            and os.getenv("HYBA_ALLOW_DEV_FIXTURES", "false").lower() in {"1", "true", "yes", "on"}
        )

    async def start(self) -> bool:
        self.logger.info("Initializing PYTHIA Orchestration Layer...")
        self.is_running = True

        try:
            active_pool = await self.pool_manager.get_best_pool()
            self.logger.info("Initial pool bound: %s", active_pool.pool_name)
            self.health_status = "AWAITING_JOB"
        except AllPoolsOfflineError as exc:
            self.logger.error("No live mining pool available on startup: %s", exc)
            self.health_status = "DEGRADED"

        asyncio.create_task(self._mining_loop())
        asyncio.create_task(self._pool_rotation_loop())
        self.logger.info("PYTHIA Genesis Orchestrator running without simulated production jobs.")
        return True

    async def stop(self) -> None:
        self.is_running = False
        await self.pool_manager.disconnect_all()
        self.logger.info("PYTHIA Orchestrator stopped cleanly.")

    async def _resolve_current_job(self, active_pool) -> Optional[MiningJob]:
        """Return a real current job, polling the live Stratum stream first."""
        live_job = await active_pool.poll_live_event(timeout=0.1)
        if live_job is not None:
            self.jobs_received += 1
            return live_job
        if active_pool.current_jobs:
            return next(reversed(active_pool.current_jobs.values()))
        if self.allow_dev_fixture_jobs:
            self.logger.warning("Creating dev fixture mining job because HYBA_ALLOW_DEV_FIXTURES=true")
            self.jobs_received += 1
            return active_pool.inject_simulated_target_job(difficulty=active_pool.current_difficulty)
        return None

    async def _mining_loop(self):
        """Asynchronous mining loop over real pool jobs only."""
        while self.is_running:
            try:
                active_pool = await self.pool_manager.get_best_pool()
                self.current_job = await self._resolve_current_job(active_pool)
                if self.current_job is None:
                    self.health_status = "AWAITING_JOB"
                    await asyncio.sleep(0.5)
                    continue

                await self.ai_optimizer.optimize_nonce_search(self.current_job)
                await self.quantum_solver.configure_search(self.current_job.target, [(0, 2**32 - 1)])
                resolved_nonce = await self.quantum_solver.solve()

                if resolved_nonce is not None:
                    self.shares_solved += 1
                    share_result = await active_pool.submit_validated_share(self.current_job, resolved_nonce)
                    if share_result.accepted:
                        await self.ai_optimizer.on_share_accepted({
                            "nonce": resolved_nonce,
                            "job_id": self.current_job.job_id,
                            "block_hash": share_result.block_hash,
                        })
                    else:
                        await self.ai_optimizer.on_share_rejected(
                            {"nonce": resolved_nonce, "job_id": self.current_job.job_id},
                            share_result.error_code or 1,
                            share_result.error_message or "share rejected",
                        )

                self.failure_counter = 0
                self.health_status = "HEALTHY" if active_pool.current_jobs else "AWAITING_JOB"
                await asyncio.sleep(0.25)
            except Exception as e:
                self.failure_counter += 1
                self.logger.error("Error in mining execution loop (failures=%s): %s", self.failure_counter, e)
                if self.failure_counter > 5:
                    self.health_status = "DEGRADED"
                sleep_time = min(60.0, 5.0 * (2 ** (self.failure_counter - 1)))
                await asyncio.sleep(sleep_time)

    async def _pool_rotation_loop(self):
        """Refresh the active pool without fabricating fallback pool state."""
        rotation_failures = 0
        while self.is_running:
            try:
                await asyncio.sleep(30.0)
                active_pool = await self.pool_manager.get_best_pool()
                self.logger.info("[GenesisAI] Pool scheduler synchronized. Active: %s", active_pool.pool_name)
                rotation_failures = 0
            except Exception as e:
                rotation_failures += 1
                self.logger.error("Pool scheduler failed (failures=%s): %s", rotation_failures, e)
                self.health_status = "DEGRADED"
                await asyncio.sleep(min(60.0, 10.0 * rotation_failures))

    def get_system_status(self) -> Dict[str, Any]:
        active_pool = self.pool_manager.get_active_pool()
        pools_info = self.pool_manager.get_all_pools_status()

        total_submitted = sum(p["performance"]["shares_submitted"] for p in pools_info)
        total_accepted = sum(p["performance"]["shares_accepted"] for p in pools_info)
        total_rejected = sum(p["performance"]["shares_rejected"] for p in pools_info)
        acceptance = None if total_submitted == 0 else total_accepted / total_submitted

        cpu_load = psutil.cpu_percent() if psutil else None
        quantum_metrics = self.quantum_solver.get_metrics()
        consciousness_metrics = self.consciousness_engine.get_metrics() if hasattr(self.consciousness_engine, "get_metrics") else {}

        return {
            "running": self.is_running,
            "uptime_seconds": round(time.time() - self.start_time, 3),
            "active_pool": active_pool.pool_name if active_pool else None,
            "active_pool_id": self.pool_manager.current_pool_key,
            "current_job": self.current_job.job_id if self.current_job else None,
            "jobs_received": self.jobs_received,
            "shares_solved": self.shares_solved,
            "total_shares": total_submitted,
            "accepted_shares": total_accepted,
            "rejected_shares": total_rejected,
            "acceptance_rate": None if acceptance is None else round(acceptance, 6),
            "system_health": self.health_status,
            "cpu_load": cpu_load,
            "active_stratum_version": active_pool.stratum_version if active_pool else None,
            "hashrate_ehs": quantum_metrics.get("hashrate_ehs"),
            "power_scale": quantum_metrics.get("power_scale"),
            "pools": pools_info,
            "quantum": quantum_metrics,
            "consciousness": consciousness_metrics,
            "telemetry_source": "runtime_state",
            "fixture_jobs_enabled": self.allow_dev_fixture_jobs,
        }
