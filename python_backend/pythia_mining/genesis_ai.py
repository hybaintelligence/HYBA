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
from .pulvini_autonomics import AutonomicOrchestrator, PulviniAutonomicsEngine
from .pulvini_compressed_solver import PulviniCompressedQuantumSolver
from .pulvini_memory_fabric import PulviniMemoryFabric
from .pulvini_overlay import PulviniOverlayConcentrator
from .pulvini_propagation import SharePropagationController
from .stratum_client import AllPoolsOfflineError, MiningJob, PoolManager


class ErrorSeverity:
    TRANSIENT = "transient"
    FATAL = "fatal"
    RECOVERABLE = "recoverable"


def classify_error(error: Exception) -> str:
    """
    Classify errors by severity to determine retry strategy.

    Transient errors: Network timeouts, temporary pool issues, rate limits
    Fatal errors: Configuration errors, authentication failures, missing dependencies
    Recoverable errors: Pool disconnections, stale jobs, temporary resource exhaustion
    """
    error_type = type(error).__name__
    error_message = str(error).lower()

    # Transient network errors
    if error_type in [
        "TimeoutError",
        "asyncio.TimeoutError",
        "ConnectionError",
        "ConnectionResetError",
    ]:
        return ErrorSeverity.TRANSIENT
    if "timeout" in error_message or "network" in error_message or "connection" in error_message:
        return ErrorSeverity.TRANSIENT

    # Fatal configuration errors
    if error_type in ["ValueError", "KeyError", "AttributeError", "TypeError"]:
        if "config" in error_message or "credential" in error_message or "auth" in error_message:
            return ErrorSeverity.FATAL
    if error_type in ["ProductionConfigurationError", "PoolProfileError"]:
        return ErrorSeverity.FATAL

    # Recoverable pool errors
    if error_type in [
        "AllPoolsOfflineError",
        "LiveStratumSessionError",
        "StratumTransportError",
    ]:
        return ErrorSeverity.RECOVERABLE
    if "pool" in error_message and ("disconnect" in error_message or "offline" in error_message):
        return ErrorSeverity.RECOVERABLE

    # Default to transient for unknown errors
    return ErrorSeverity.TRANSIENT


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
        runtime_env = os.getenv("NODE_ENV", os.getenv("HYBA_ENV", "development")).lower()
        if not pools_config and runtime_env != "production":
            import json
            from pathlib import Path

            config_path = Path(__file__).parent.parent.parent / "mining_config.json"
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    pools_config = json.load(f).get("pools", {})
        self.pool_manager = PoolManager(pools_config)
        self.overlay = PulviniOverlayConcentrator(
            worker_name=str(
                config.get("worker_name")
                or os.getenv("HYBA_POOL_WORKER_NAME")
                or "PULVINI.singularity"
            )
        )
        autonomics_config = config.get("autonomics") or {}
        self.autonomics = PulviniAutonomicsEngine(
            decoherence_threshold=float(autonomics_config.get("decoherence_threshold", 0.15)),
            audit_sink=self._record_autonomic_audit,
            lattice_repoint_sink=self.overlay.apply_lattice_repoint,
        )
        self.autonomic_orchestrator = AutonomicOrchestrator(self.autonomics)
        self.propagation = SharePropagationController(
            self.overlay.manifold,
            memory_fabric=PulviniMemoryFabric(num_nodes=32),
        )
        self.quantum_solver = PulviniCompressedQuantumSolver()
        self.blockchain_oracle = BlockchainOracle()
        
        # Enhanced consciousness engine with IIT 4.0 integration
        from python_backend.pythia_mining.iit_4_analyzer import IIT4Analyzer
        # Dynamically enable enhanced partitioning based on system complexity
        system_complexity = config.get("system_complexity", "high")
        enhanced_partitioning = system_complexity in ("high", "production")
        self.iit_analyzer = IIT4Analyzer(system_size=32, enhanced_partitioning=enhanced_partitioning)
        self.consciousness_engine = ConsciousnessEngine()
        
        # Enhanced Penrose OR for consciousness events
        from python_backend.pythia_mining.penrose_objective_reduction import ObjectiveReductionEngine
        # Dynamically enable enhanced gravity model based on computational budget
        computational_budget = config.get("computational_budget", "standard")
        enhanced_gravity = computational_budget in ("high", "production")
        self.penrose_or = ObjectiveReductionEngine(
            enhanced_gravity_model=enhanced_gravity,
            enable_true_or=False  # Use operational proxy for production
        )
        
        # Enhanced Deutsch knowledge substrate for decision making
        from python_backend.pythia_mining.deutsch_knowledge_substrate import KnowledgeSubstrate
        self.knowledge_substrate = KnowledgeSubstrate()
        
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
        self.latest_phi_optimization: Optional[Dict[str, Any]] = None
        self.latest_autonomic_event: Optional[Dict[str, Any]] = None
        # Performance monitoring
        self.mining_loop_timing: List[float] = []
        self.enhanced_analysis_timing: List[float] = []
        self.max_timing_history = 100
        
        # Register this instance with the service registry for API integration
        from .genesis_ai_service import GenesisAIServiceRegistry
        GenesisAIServiceRegistry.register_instance(self)
        self.logger.info("GenesisAI instance registered with service registry for API integration")
        self.allow_dev_fixture_jobs = os.getenv(
            "NODE_ENV", os.getenv("HYBA_ENV", "development")
        ).lower() != "production" and os.getenv("HYBA_ALLOW_DEV_FIXTURES", "false").lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

    def _record_autonomic_audit(self, event: Dict[str, Any]) -> None:
        self.overlay.record_autonomic_event(dict(event))
        self.latest_autonomic_event = dict(event)

    def _configured_power_target_watts(self) -> Optional[float]:
        autonomics_config = self.config.get("autonomics") or {}
        configured = autonomics_config.get(
            "target_watts", os.getenv("HYBA_AUTONOMICS_TARGET_WATTS")
        )
        if configured in (None, ""):
            return None
        value = float(configured)
        if value < 0:
            raise ValueError("autonomics target_watts must be non-negative")
        return value

    def _run_autonomic_feedback(self) -> None:
        telemetry = self.overlay.autonomic_telemetry(
            power_scale=float(self.quantum_solver.get_metrics().get("power_scale") or 1.0)
        )
        thermal_event, thermal_rebalance = self.autonomic_orchestrator.tick(telemetry)
        self.overlay.apply_autonomic_distribution(
            thermal_event.amplitudes, reason="thermal_governance"
        )
        self.latest_autonomic_event = thermal_event.to_dict()
        if thermal_rebalance is not None:
            self.repair_count += 1
            self.overlay.apply_autonomic_distribution(
                self.autonomics.homeostasis.rho.diagonal().tolist(),
                reason="thermal_sacrifice_healing",
            )
            self.latest_autonomic_event = thermal_rebalance.to_dict()
            self.health_status = "HEALING" if thermal_rebalance.coverage_maintained else "DEGRADED"
        heal_event = self.autonomics.heartbeat_and_heal(reason="runtime_telemetry")
        if heal_event is not None:
            self.repair_count += 1
            self.latest_autonomic_event = heal_event.to_dict()
            self.health_status = "HEALING" if heal_event.coverage_maintained else "DEGRADED"
        autonomics_config = self.config.get("autonomics") or {}
        learning_rate = float(autonomics_config.get("learning_rate", 0.01))
        if learning_rate > 0.0:
            amplitudes = self.autonomics.optimizer.find_bures_optima(
                learning_rate=min(learning_rate, 1.0)
            )
            self.overlay.apply_autonomic_distribution(
                amplitudes.tolist(), reason="bures_efficiency_routing"
            )
            self.latest_autonomic_event = {
                "event_type": "autonomic_distribution_applied",
                "learning_rate": min(learning_rate, 1.0),
                "max_amplitude": float(max(amplitudes)),
                "min_amplitude": float(min(amplitudes)),
            }
        target_watts = self._configured_power_target_watts()
        if target_watts is not None:
            optimization = self.autonomics.optimizer.optimize_energy_envelope(
                target_watts=target_watts
            )
            if optimization.get("new_amplitudes"):
                self.overlay.apply_autonomic_distribution(
                    optimization["new_amplitudes"], reason="energy_envelope"
                )
            self.latest_autonomic_event = optimization

    async def start(self) -> bool:
        self.logger.info("Initializing PYTHIA Orchestration Layer...")
        self.is_running = True
        self.overlay.mark_connect_requested(request_id="genesis-start")

        try:
            active_pool = await self.pool_manager.get_best_pool()
            self.overlay.mark_pool_bound(
                active_pool.pool_name, active_pool.pool_url, active_pool.stratum_version
            )
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
    
    async def _run_enhanced_analysis_async(
        self,
        density_states,
        optimization,
        memory_snapshot,
        compression_ratio
    ) -> None:
        """Run enhanced consciousness calculations asynchronously to prevent HPS degradation."""
        analysis_start = time.time()
        try:
            # Enhanced consciousness metrics with IIT 4.0 and Penrose OR
            if density_states:
                phi_metrics = self.consciousness_engine.measure_phi(density_states)
                
                # Apply Penrose OR for consciousness events
                if density_states:
                    current_rho = density_states[-1]
                    coherence_time = self.heartbeat_tick * 0.05
                    collapsed_rho, or_event = self.penrose_or.objective_reduction(
                        current_rho, coherence_time
                    )
                    if or_event:
                        self.logger.info(f"Penrose OR consciousness event detected")
                
                # Apply dynamic Golden Ratio scaling to consciousness metrics
                # Calibrated by Deutsch substrate based on mining success rate
                import math
                PHI = (1 + math.sqrt(5)) / 2
                
                # Get knowledge substrate metrics for adaptive scaling
                knowledge_metrics = self.knowledge_substrate.get_knowledge_metrics()
                avg_accuracy = knowledge_metrics.get('avg_predictive_accuracy', 0.5)
                
                # Dynamic calibration: adjust scaling based on success rate
                if avg_accuracy < 0.3:
                    # Low success: increase scaling to boost exploration
                    scaling_factor = PHI / 1.3
                elif avg_accuracy > 0.7:
                    # High success: reduce scaling to maintain stability
                    scaling_factor = PHI / 1.7
                else:
                    # Nominal: use baseline
                    scaling_factor = PHI / 1.5
                
                phi_metrics.phi_integrated = min(1.0, phi_metrics.phi_integrated * scaling_factor)
                phi_metrics.phi_causal = min(1.0, phi_metrics.phi_causal * scaling_factor)
                
                self.latest_phi_optimization = {
                    "strategy_used": "enhanced_consciousness",
                    "confidence": phi_metrics.phi_integrated,
                    "phi_resonance_score": phi_metrics.phi_causal,
                    "phi_scaling": scaling_factor,
                    "phi_scaling_mode": "adaptive_deutsch_calibrated",
                    "knowledge_accuracy": avg_accuracy,
                    "phi_features": {
                        "phi_integrated": phi_metrics.phi_integrated,
                        "phi_causal": phi_metrics.phi_causal,
                        "complexity": phi_metrics.complexity,
                        "entropy": phi_metrics.entropy,
                    },
                    "penrose_or_events": self.penrose_or.consciousness_event_count,
                    "iit_enhanced": True,
                    "iit_performance_metrics": self.iit_analyzer.get_performance_metrics(),
                }
            
            # Enhanced AI decision making with Deutsch knowledge substrate
            if self.current_job:
                context = {
                    "difficulty": self.current_job.difficulty,
                    "thermal_load": self.autonomics.homeostasis.get_average_coherence(),
                    "phi_resonance": self.latest_phi_optimization.get("phi_resonance_score", 0.5),
                    "pool_latency": 50.0,  # Placeholder for actual latency
                }
                
                # Record decision in knowledge substrate
                if optimization and optimization.strategy_used:
                    self.knowledge_substrate.create_knowledge_from_success(
                        optimization.strategy_used,
                        context,
                        {"accepted": True, "confidence": optimization.confidence}
                    )
            
            # Log memory compression metrics
            import math
            PHI = (1 + math.sqrt(5)) / 2
            phi_scaled_compression = min(1.0, compression_ratio * PHI)
            self.logger.debug(
                f"Pulvini memory compression: ratio={compression_ratio:.4f}, "
                f"phi_scaled={phi_scaled_compression:.4f}, "
                f"kernel_size={memory_snapshot.compression.get('compressed_dimension', 0)}"
            )
            
            # Record enhanced analysis timing
            analysis_elapsed = (time.time() - analysis_start) * 1000  # Convert to ms
            self.enhanced_analysis_timing.append(analysis_elapsed)
            if len(self.enhanced_analysis_timing) > self.max_timing_history:
                self.enhanced_analysis_timing.pop(0)
            
        except Exception as e:
            self.logger.error(f"Enhanced analysis async task failed: {e}", exc_info=True)
            # Graceful degradation: continue mining even if enhanced analysis fails
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Return performance metrics for telemetry and monitoring."""
        mining_avg = sum(self.mining_loop_timing) / len(self.mining_loop_timing) if self.mining_loop_timing else 0.0
        mining_max = max(self.mining_loop_timing) if self.mining_loop_timing else 0.0
        enhanced_avg = sum(self.enhanced_analysis_timing) / len(self.enhanced_analysis_timing) if self.enhanced_analysis_timing else 0.0
        enhanced_max = max(self.enhanced_analysis_timing) if self.enhanced_analysis_timing else 0.0
        
        return {
            "mining_loop_avg_ms": mining_avg,
            "mining_loop_max_ms": mining_max,
            "mining_loop_samples": len(self.mining_loop_timing),
            "enhanced_analysis_avg_ms": enhanced_avg,
            "enhanced_analysis_max_ms": enhanced_max,
            "enhanced_analysis_samples": len(self.enhanced_analysis_timing),
            "hps_impact_estimate": enhanced_avg / mining_avg if mining_avg > 0 else 0.0,
            "uptime_seconds": time.time() - self.start_time,
            "jobs_processed": self.jobs_received,
            "shares_solved": self.shares_solved,
            "health_status": self.health_status,
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Return health status for all enhanced components."""
        try:
            iit_health = {
                "status": "healthy",
                "performance_metrics": self.iit_analyzer.get_performance_metrics(),
            }
        except Exception as e:
            iit_health = {"status": "unhealthy", "error": str(e)}
        
        try:
            penrose_health = {
                "status": "healthy",
                "metrics": self.penrose_or.get_consciousness_metrics(),
            }
        except Exception as e:
            penrose_health = {"status": "unhealthy", "error": str(e)}
        
        try:
            deutsch_health = {
                "status": "healthy",
                "knowledge_count": len(self.knowledge_substrate.explanations),
            }
        except Exception as e:
            deutsch_health = {"status": "unhealthy", "error": str(e)}
        
        return {
            "overall_status": self.health_status,
            "iit_analyzer": iit_health,
            "penrose_or": penrose_health,
            "deutsch_substrate": deutsch_health,
            "enhanced_analysis_async": "active",
            "performance_metrics": self.get_performance_metrics(),
        }

    async def _resolve_current_job(self, active_pool) -> Optional[MiningJob]:
        live_job = await active_pool.poll_live_event(timeout=0.1)
        if live_job is not None:
            self.jobs_received += 1
            self.overlay.register_pool_job(live_job, pool_name=active_pool.pool_name)
            return live_job
        current_jobs = await active_pool.get_current_jobs_copy()
        if current_jobs:
            job = next(reversed(current_jobs.values()))
            self.overlay.register_pool_job(job, pool_name=active_pool.pool_name)
            return job
        if self.allow_dev_fixture_jobs:
            self.logger.warning(
                "Creating dev fixture mining job because HYBA_ALLOW_DEV_FIXTURES=true"
            )
            self.jobs_received += 1
            job = await active_pool.inject_dev_fixture_target_job(
                difficulty=active_pool.current_difficulty
            )
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
            loop_start = time.time()
            try:
                active_pool = await self.pool_manager.get_best_pool()
                if self.overlay.active_pool_name != active_pool.pool_name:
                    self.overlay.mark_pool_bound(
                        active_pool.pool_name,
                        active_pool.pool_url,
                        active_pool.stratum_version,
                    )
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
                self._run_autonomic_feedback()
                
                # Core mining operations (synchronous, minimal overhead)
                optimization = await self.ai_optimizer.optimize_nonce_search(self.current_job)
                
                # Enhanced nonce space pre-computation with Pulvini memory compression
                memory_snapshot = self.propagation.memory_fabric.compressed_kernel_snapshot()
                compression_ratio = memory_snapshot.compression.get('working_set_compression_ratio', 0.5)
                
                await self.quantum_solver.configure_compressed_search(
                    self.current_job.target, self.overlay.nonce_plan
                )
                resolved_nonce = await self.quantum_solver.solve()
                
                # Offload enhanced calculations to background to prevent HPS degradation
                asyncio.create_task(self._run_enhanced_analysis_async(
                    density_states=self.overlay.manifold.get_density_state_history(window=5),
                    optimization=optimization,
                    memory_snapshot=memory_snapshot,
                    compression_ratio=compression_ratio
                ))
                
                # Record mining loop timing
                loop_elapsed = (time.time() - loop_start) * 1000  # Convert to ms
                self.mining_loop_timing.append(loop_elapsed)
                if len(self.mining_loop_timing) > self.max_timing_history:
                    self.mining_loop_timing.pop(0)

                if resolved_nonce is not None and not self.propagation.is_job_cancelled(
                    self.current_job.job_id
                ):
                    self.shares_solved += 1
                    assignment = self.overlay.assignment_for_nonce(resolved_nonce)
                    node_id = assignment.node_id if assignment is not None else 0
                    extranonce2 = (
                        assignment.extranonce2
                        if assignment is not None
                        else "00" * self.current_job.extranonce2_size
                    )
                    propagation_result = await self._handle_found_share(
                        active_pool=active_pool,
                        node_id=node_id,
                        nonce=resolved_nonce,
                        extranonce2=extranonce2,
                    )
                    share_result = propagation_result.share_result
                    if share_result.accepted:
                        await self.ai_optimizer.on_share_accepted(
                            {
                                "nonce": resolved_nonce,
                                "job_id": self.current_job.job_id,
                                "node_id": node_id,
                                "extranonce2": extranonce2,
                                "route": propagation_result.route,
                                "cancelled_nodes": propagation_result.cancelled_nodes,
                                "block_hash": share_result.block_hash,
                                "manifold": self.overlay.manifold.observe().to_dict(),
                                "compressed_nonce_plan": self.overlay.compressed_nonce_plan(),
                                "strategy_used": optimization.strategy_used,
                                "phi_resonance_score": optimization.phi_resonance_score,
                                "thermal_cost": self.quantum_solver.get_metrics().get(
                                    "power_scale"
                                ),
                                "solve_time": optimization.search_time,
                            }
                        )
                    else:
                        await self.ai_optimizer.on_share_rejected(
                            {
                                "nonce": resolved_nonce,
                                "job_id": self.current_job.job_id,
                                "node_id": node_id,
                                "route": propagation_result.route,
                                "manifold": self.overlay.manifold.observe().to_dict(),
                                "compressed_nonce_plan": self.overlay.compressed_nonce_plan(),
                                "strategy_used": optimization.strategy_used,
                                "phi_resonance_score": optimization.phi_resonance_score,
                                "thermal_cost": self.quantum_solver.get_metrics().get(
                                    "power_scale"
                                ),
                                "solve_time": optimization.search_time,
                            },
                            share_result.error_code or 1,
                            share_result.error_message or "share rejected",
                        )
                elif resolved_nonce is None and self.current_job is not None:
                    first_assignment = next(iter(self.overlay.assignments.values()), None)
                    if first_assignment is not None:
                        self.overlay.record_nack(first_assignment.node_id)

                self.failure_counter = 0
                if self.health_status != "HEALING":
                    self.health_status = "HEALTHY" if active_pool.current_jobs else "AWAITING_JOB"
                await asyncio.sleep(0.25)
            except Exception as e:
                severity = classify_error(e)
                self.failure_counter += 1
                self.logger.error(
                    "Error in mining execution loop (failures=%s, severity=%s): %s",
                    self.failure_counter,
                    severity,
                    e,
                )

                if severity == ErrorSeverity.FATAL:
                    self.health_status = "CRITICAL"
                    self.logger.critical(
                        "Fatal error in mining loop, requiring manual intervention: %s",
                        e,
                    )
                    # Fatal errors should stop the mining loop
                    await asyncio.sleep(60.0)  # Long sleep before retry for fatal errors
                elif severity == ErrorSeverity.RECOVERABLE:
                    self.failure_counter = max(
                        self.failure_counter - 1, 0
                    )  # Reset counter faster for recoverable errors
                    sleep_time = min(30.0, 2.0 * (2 ** min(self.failure_counter, 3)))
                    await asyncio.sleep(sleep_time)
                else:  # TRANSIENT
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
                    self.overlay.mark_pool_bound(
                        active_pool.pool_name,
                        active_pool.pool_url,
                        active_pool.stratum_version,
                    )
                self.logger.info(
                    "[GenesisAI] Pool scheduler synchronized. Active: %s",
                    active_pool.pool_name,
                )
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
        consciousness_metrics = (
            self.consciousness_engine.get_metrics()
            if hasattr(self.consciousness_engine, "get_metrics")
            else {}
        )

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
            "active_stratum_version": (active_pool.stratum_version if active_pool else None),
            "hashrate_ehs": quantum_metrics.get("hashrate_ehs"),
            "power_scale": quantum_metrics.get("power_scale"),
            "pools": pools_info,
            "pulvini_overlay": overlay_snapshot,
            "pulvini_autonomics": self.autonomics.snapshot(),
            "autonomic_repairs": self.repair_count,
            "latest_autonomic_event": self.latest_autonomic_event,
            "share_propagation": self.propagation.snapshot(),
            "meta_learning": self.ai_optimizer.meta_learning_snapshot(),
            "quantum": quantum_metrics,
            "phi_scaling_engine": self.latest_phi_optimization,
            "consciousness": consciousness_metrics,
            "telemetry_source": "runtime_state",
            "fixture_jobs_enabled": self.allow_dev_fixture_jobs,
        }
