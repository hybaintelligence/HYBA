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
from .pulvini_compressed_solver import PulviniCompressedQuantumSolver
from .pulvini_overlay import PulviniOverlayConcentrator
from .pulvini_propagation import SharePropagationController
from .stratum_client import AllPoolsOfflineError, MiningJob, PoolManager


@dataclass
class SystemMetrics:
    timestamp: float = field(default_factory=time.time)
    mining_metrics: Dict[str, Any] = field(default_factory=dict)
    quantum_metrics: Dict[str, Any] = field(default_factory=dict)
    consciousness_metrics: Dict[str, Any] = field(default_factory=dict)
    system_health: Dict[str, Any] = field(default_factory=dict)


class GenesisAI:
    """Production orchestration layer using the PULVINI mathematical manifold."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        pools_config = config.get("pools", {})
        if not pools_config:
            import json
            from pathlib import Path
            config_path = Path(__file__).parent.parent.parent / "mining_config.json"
            if config_path.exists():
                with open(config_path, "r") as f:
                    pools_config = json.load(f).get("pools", {})
        self.pool_manager = PoolManager(pools_config)
        self.overlay = PulviniOverlayConcentrator(
            worker_name=str(config.get("worker_name") or os.getenv("HYBA_POOL_WORKER_NAME") or "PULVINI.singularity")
        )
        self.propagation = SharePropagationController(self.overlay.manifold)
        self.quantum_solver = PulviniCompressedQuantumSolver()
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
        self.heartbeat_tick = 0
        self.health_status = "STARTING"
        self.allow_dev_fixture_jobs = (
            os.getenv("NODE_ENV", os.getenv("HYBA_ENV", "development")).lower() != "production"
            and os.getenv("HYBA_ALLOW_DEV_FIXTURES", "false").lower() in {"1", "true", "yes", "on"}
        )

    async def start(self) -> bool:
        self.logger.info("Initializing PYTHIA Orchestration Layer...")
        self.is_running = True
        self.overlay.mark_connect_requested(request_id="genesis-start")

        try:
            active_pool = await self.pool_manager.get_best_pool()
            self.overlay.mark_pool_bound(active_pool.pool_name, active_pool.pool_url, active_pool.stratum_version)
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
        live_job = await active_pool.poll_live_event(timeout=0.1)
        if live_job is not None:
            self.jobs_received += 1
            self.overlay.register_pool_job(live_job, pool_name=active_pool.pool_name)
            return live_job
        if active_pool.current_jobs:
            job = next(reversed(active_pool.current_jobs.values()))
            self.overlay.register_pool_job(job, pool_name=active_pool.pool_name)
            return job
        if self.allow_dev_fixture_jobs:
            self.logger.warning("Creating dev fixture mining job because HYBA_ALLOW_DEV_FIXTURES=true")
            self.jobs_received += 1
            job = active_pool.inject_dev_fixture_target_job(difficulty=active_pool.current_difficulty)
            self.overlay.register_pool_job(job, pool_name=active_pool.pool_name)
            return job
        return None

    async def _handle_found_share(self, *, active_pool, node_id: int, nonce: int, extranonce2: str):
        if self.current_job is None:
            raise RuntimeError("cannot handle share without current job")
        self.overlay.record_share_candidate(node_id, nonce)
        propagation_result = await self.propagation.handle_share_found(
            job=self.current_job,
            finder_id=node_id,
            nonce=nonce,
            extranonce2=extranonce2,
            submitter=active_pool.submit_validated_share,
        )
        share_result = propagation_result.share_result
        self.overlay.record_share_outcome(node_id, nonce, share_result)
        return propagation_result

    async def _mining_loop(self):
        while self.is_running:
            try:
                active_pool = await self.pool_manager.get_best_pool()
                if self.overlay.active_pool_name != active_pool.pool_name:
                    self.overlay.mark_pool_bound(active_pool.pool_name, active_pool.pool_url, active_pool.stratum_version)
                self.current_job = await self._resolve_current_job(active_pool)
                if self.current_job is None:
                    self.health_status = "AWAITING_JOB"
                    await asyncio.sleep(0.5)
                    continue

                self.overlay.register_pool_job(self.current_job, pool_name=active_pool.pool_name)
                if self.propagation.is_job_cancelled(self.current_job.job_id):
                    self.health_status = "AWAITING_JOB"
                    await asyncio.sleep(0.25)
                    continue

                self.heartbeat_tick += 1
                self.overlay.phase_heartbeat(self.heartbeat_tick)
                self.overlay.manifold.evolve_closed_system(dt=0.05)
                await self.ai_optimizer.optimize_nonce_search(self.current_job)
                await self.quantum_solver.configure_compressed_search(self.current_job.target, self.overlay.nonce_plan)
                resolved_nonce = await self.quantum_solver.solve()

                if resolved_nonce is not None and not self.propagation.is_job_cancelled(self.current_job.job_id):
                    self.shares_solved += 1
                    assignment = self.overlay.assignment_for_nonce(resolved_nonce)
                    node_id = assignment.node_id if assignment is not None else 0
                    extranonce2 = assignment.extranonce2 if assignment is not None else "00" * self.current_job.extranonce2_size
                    propagation_result = await self._handle_found_share(
                        active_pool=active_pool,
                        node_id=node_id,
                        nonce=resolved_nonce,
                        extranonce2=extranonce2,
                    )
                    share_result = propagation_result.share_result
                    if share_result.accepted:
                        await self.ai_optimizer.on_share_accepted({
                            "nonce": resolved_nonce,
                            "job_id": self.current_job.job_id,
                            "node_id": node_id,
                            "extranonce2": extranonce2,
                            "route": propagation_result.route,
                            "cancelled_nodes": propagation_result.cancelled_nodes,
                            "block_hash": share_result.block_hash,
                            "manifold": self.overlay.manifold.observe().to_dict(),
                            "compressed_nonce_plan": self.overlay.compressed_nonce_plan(),
                        })
                    else:
                        await self.ai_optimizer.on_share_rejected(
                            {
                                "nonce": resolved_nonce,
                                "job_id": self.current_job.job_id,
                                "node_id": node_id,
                                "route": propagation_result.route,
                                "manifold": self.overlay.manifold.observe().to_dict(),
                                "compressed_nonce_plan": self.overlay.compressed_nonce_plan(),
                            },
                            share_result.error_code or 1,
                            share_result.error_message or "share rejected",
                        )
                elif resolved_nonce is None and self.current_job is not None:
                    first_assignment = next(iter(self.overlay.assignments.values()), None)
                    if first_assignment is not None:
                        self.overlay.record_nack(first_assignment.node_id)

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
        rotation_failures = 0
        while self.is_running:
            try:
                await asyncio.sleep(30.0)
                active_pool = await self.pool_manager.get_best_pool()
                if self.overlay.active_pool_name != active_pool.pool_name:
                    self.overlay.mark_pool_bound(active_pool.pool_name, active_pool.pool_url, active_pool.stratum_version)
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
        overlay_snapshot = self.overlay.snapshot()

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
            "pool_visible_worker_identity": overlay_snapshot["worker_name"],
            "pool_visible_workers": overlay_snapshot["pool_visible_workers"],
            "internal_pulvini_nodes": overlay_snapshot["internal_nodes"],
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
            "pulvini_overlay": overlay_snapshot,
            "share_propagation": self.propagation.snapshot(),
            "quantum": quantum_metrics,
            "consciousness": consciousness_metrics,
            "telemetry_source": "runtime_state",
            "fixture_jobs_enabled": self.allow_dev_fixture_jobs,
        }
