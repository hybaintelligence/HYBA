"""Salamander Integration for CIaaS (Computational Intelligence as a Service).

This module integrates the Salamander autonomous operations layer into the
HYBA CIaaS system, providing self-healing, self-optimization, and economic
autonomy for computational intelligence operations.

Integration Architecture:
- SalamanderCore: Observes intelligence system state, detects anomalies, executes regeneration
- Evidence-Based Regeneration: Recovers intelligence state from immutable audit logs
- Distributed Agent Coherence: Coordinates intelligence agents without explicit messaging
- Adaptive φ-Tuning: Optimizes compression ratios in real-time
- Self-Scaling Worker Pool: Dynamically scales intelligence resources based on ROI
- Species Memory: Shares successful intelligence blueprints across instances
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List, Optional

from pythia_mining.salamander_frontier import (
    SalamanderCore,
    SalamanderOrchestrator,
    SystemMetrics,
    Anomaly,
    RegenerationOutcome,
    ImmutableEvidenceLog,
)


class SalamanderCIaaSIntegration:
    """
    Integration layer for Salamander autonomous operations in CIaaS system.
    
    This class bridges the existing CIaaS infrastructure with Salamander's
    autonomous capabilities, providing self-healing, self-optimization, and
    economic autonomy for computational intelligence operations.
    """

    def __init__(
        self,
        ciaas_system: Any,
        target_optimization_score: float = 0.95,
        enable_autonomy_loops: bool = True,
    ):
        """
        Initialize Salamander integration for CIaaS system.
        
        Args:
            ciaas_system: The existing CIaaS system instance
            target_optimization_score: Target optimization score for intelligence workloads
            enable_autonomy_loops: Whether to enable background autonomy loops
        """
        self.ciaas_system = ciaas_system
        self.target_optimization_score = float(target_optimization_score)
        self.enable_autonomy_loops = enable_autonomy_loops
        
        # Initialize Salamander orchestrator
        self.salamander = SalamanderOrchestrator(
            total_target_hashrate=target_optimization_score * 100,  # Scale for intelligence
        )
        
        # Initialize Salamander core for direct access
        self.salamander_core = self.salamander.salamander_core
        
        # Track CIaaS-specific state
        self.intelligence_services: Dict[str, Any] = {}
        self.workload_executions = 0
        self.optimization_score_current = 0.0
        self.compression_ratio = 1.0
        self.intelligence_errors = 0
        self.uptime_seconds = 0.0
        self.last_workload_time = 0.0
        self.data_processed_bytes = 0
        
        # Background tasks
        self._autonomy_task: Optional[asyncio.Task] = None
        self._phi_task: Optional[asyncio.Task] = None
        self._scaling_task: Optional[asyncio.Task] = None
        self._is_running = False

    def initialize(self) -> None:
        """
        Initialize Salamander for CIaaS operations.
        
        This should be called when the CIaaS system starts up.
        """
        # Initialize Salamander orchestrator
        self.salamander.initialize()
        
        # Log initialization to audit trail
        self.salamander.audit_log = self.salamander.audit_log.append(
            "ciaas_salamander_initialized",
            timestamp=time(),
            target_optimization_score=self.target_optimization_score,
            ciaas_system_type=type(self.ciaas_system).__name__,
        )

    def observe_ciaas_state(self) -> SystemMetrics:
        """
        Observe current CIaaS system state.
        
        Returns comprehensive metrics for anomaly detection and optimization.
        """
        # Gather metrics from CIaaS system
        if hasattr(self.ciaas_system, 'get_metrics'):
            ciaas_metrics = self.ciaas_system.get_metrics()
            self.optimization_score_current = ciaas_metrics.get('optimization_score', 0.0)
            self.compression_ratio = ciaas_metrics.get('compression_ratio', 1.0)
            self.intelligence_errors = ciaas_metrics.get('intelligence_errors', 0)
        
        # Get service status
        service_count = len(self.intelligence_services)
        active_services = sum(
            1 for service in self.intelligence_services.values()
            if service.get('state') == 'running'
        )
        
        # Calculate uptime
        if self.uptime_seconds > 0:
            self.uptime_seconds += 1.0  # Increment on each observation
        
        # Get memory usage if available
        memory_used = 0.0
        memory_available = 1.0
        if hasattr(self.ciaas_system, 'get_memory_usage'):
            memory_info = self.ciaas_system.get_memory_usage()
            memory_used = memory_info.get('used', 0.0)
            memory_available = memory_info.get('available', 1.0)
        
        # Build service health list
        service_health = []
        for service_id, service in self.intelligence_services.items():
            service_health.append({
                'id': service_id,
                'state': service.get('state', 'unknown'),
                'logical_compute_units': service.get('logical_compute_units', 0),
                'code_distance': service.get('code_distance', 7),
                'time_since_last_workload_ms': (time() - self.last_workload_time) * 1000,
            })
        
        # Observe system state through SalamanderCore
        metrics = self.salamander_core.observe_system_state(
            hashrate_current=self.optimization_score_current * 100,  # Scale for intelligence
            hashrate_target=self.target_optimization_score * 100,
            memory_used=memory_used,
            memory_available=memory_available,
            agent_health=service_health,
            worker_health=[],
        )
        
        return metrics

    def detect_ciaas_anomaly(self, metrics: SystemMetrics) -> Optional[Anomaly]:
        """
        Detect CIaaS-specific anomalies.
        
        Extends SalamanderCore's anomaly detection with CIaaS-specific logic.
        """
        # Use SalamanderCore's built-in anomaly detection
        anomaly = self.salamander_core.detect_anomaly(metrics)
        
        if anomaly is not None:
            return anomaly
        
        # CIaaS-specific anomaly detection
        
        # Optimization score degradation
        if self.optimization_score_current < self.target_optimization_score * 0.9:
            return Anomaly(
                type="OPTIMIZATION_SCORE_DEGRADATION",
                severity="HIGH",
                action="optimize_intelligence_parameters",
                current_value=self.optimization_score_current,
                target_value=self.target_optimization_score,
            )
        
        # Intelligence error rate too high
        error_rate = self.intelligence_errors / max(self.workload_executions, 1)
        if error_rate > 0.1:  # 10% error rate
            return Anomaly(
                type="HIGH_INTELLIGENCE_ERROR_RATE",
                severity="CRITICAL",
                action="regenerate_intelligence_state",
                current_value=error_rate,
                target_value=0.01,
            )
        
        # Service stall (no workloads for extended period)
        time_since_last_workload = time() - self.last_workload_time
        if time_since_last_workload > 600:  # 10 minutes
            return Anomaly(
                type="INTELLIGENCE_SERVICE_STALL",
                severity="HIGH",
                action="regenerate_intelligence_state",
                stall_duration_ms=time_since_last_workload * 1000,
            )
        
        # Compression ratio degradation
        if self.compression_ratio < 1.5:  # Below 1.5x compression
            return Anomaly(
                type="COMPRESSION_RATIO_DEGRADATION",
                severity="MEDIUM",
                action="optimize_compression_parameters",
                current_value=self.compression_ratio,
                target_value=2.0,
            )
        
        return None

    def execute_ciaas_regeneration(self, anomaly: Anomaly) -> RegenerationOutcome:
        """
        Execute regeneration for CIaaS-specific anomalies.
        
        Extends SalamanderCore's regeneration with CIaaS-specific recovery strategies.
        """
        # Log regeneration trigger
        self.salamander.audit_log = self.salamander.audit_log.append(
            "ciaas_regeneration_triggered",
            timestamp=time(),
            anomaly_type=anomaly.type,
            severity=anomaly.severity,
        )
        
        # Use SalamanderCore's regeneration
        outcome = self.salamander_core.execute_regeneration(anomaly)
        
        # CIaaS-specific recovery actions
        match anomaly.type:
            case "OPTIMIZATION_SCORE_DEGRADATION":
                # Trigger optimization parameter tuning
                if hasattr(self.ciaas_system, 'optimize_parameters'):
                    self.ciaas_system.optimize_parameters()
                    self.salamander.audit_log = self.salamander.audit_log.append(
                        "intelligence_parameters_optimized",
                        timestamp=time(),
                    )
            
            case "HIGH_INTELLIGENCE_ERROR_RATE":
                # Regenerate intelligence state
                if hasattr(self.ciaas_system, 'regenerate_intelligence_state'):
                    self.ciaas_system.regenerate_intelligence_state()
                    self.salamander.audit_log = self.salamander.audit_log.append(
                        "intelligence_state_regenerated",
                        timestamp=time(),
                    )
            
            case "INTELLIGENCE_SERVICE_STALL":
                # Regenerate service state
                if hasattr(self.ciaas_system, 'regenerate_service_state'):
                    self.ciaas_system.regenerate_service_state()
                    self.salamander.audit_log = self.salamander.audit_log.append(
                        "intelligence_service_state_regenerated",
                        timestamp=time(),
                    )
            
            case "COMPRESSION_RATIO_DEGRADATION":
                # Optimize compression parameters
                if hasattr(self.ciaas_system, 'optimize_compression'):
                    self.ciaas_system.optimize_compression()
                    self.salamander.audit_log = self.salamander.audit_log.append(
                        "compression_parameters_optimized",
                        timestamp=time(),
                    )
        
        return outcome

    def record_workload_execution(
        self,
        service_id: str,
        workload_kind: str,
        data_size_bytes: int,
        optimization_score: float,
        compression_ratio: float,
        success: bool,
        execution_time_ms: float,
    ) -> None:
        """
        Record a computational intelligence workload execution to the audit log.
        
        This provides evidence for regulatory compliance and species memory.
        """
        self.workload_executions += 1
        self.last_workload_time = time()
        self.data_processed_bytes += data_size_bytes
        
        if success:
            self.optimization_score_current = optimization_score
            self.compression_ratio = compression_ratio
        else:
            self.intelligence_errors += 1
        
        event_type = "workload_success" if success else "workload_failure"
        
        self.salamander.audit_log = self.salamander.audit_log.append(
            event_type,
            timestamp=time(),
            service_id=service_id,
            workload_kind=workload_kind,
            data_size_bytes=data_size_bytes,
            optimization_score=optimization_score,
            compression_ratio=compression_ratio,
            execution_time_ms=execution_time_ms,
        )

    def register_intelligence_service(
        self,
        service_id: str,
        logical_compute_units: int,
        code_distance: int,
        state: str = "provisioned",
    ) -> None:
        """
        Register a computational intelligence service for autonomous management.
        """
        self.intelligence_services[service_id] = {
            'logical_compute_units': logical_compute_units,
            'code_distance': code_distance,
            'state': state,
            'registered_at': time(),
        }
        
        # Add agent to coherence system
        self.salamander.agent_coherence.add_agent(
            agent_id=service_id,
            job_id=f"intelligence_{service_id}",
            timestamp=time(),
        )
        
        self.salamander.audit_log = self.salamander.audit_log.append(
            "intelligence_service_registered",
            timestamp=time(),
            service_id=service_id,
            logical_compute_units=logical_compute_units,
            code_distance=code_distance,
        )

    def get_intelligence_treasury_state(self) -> Dict[str, Any]:
        """
        Get current intelligence treasury state from evidence.
        
        Provides compute unit accounting for billing and regulatory compliance.
        """
        from pythia_mining.salamander_frontier import EvidenceBasedRegenerator
        
        regenerator = EvidenceBasedRegenerator(self.salamander.audit_log)
        treasury = regenerator.recover_treasury_state()
        
        return {
            "compute_units_consumed": self.workload_executions,
            "data_processed_bytes": self.data_processed_bytes,
            "intelligence_errors": self.intelligence_errors,
            "error_rate": self.intelligence_errors / max(self.workload_executions, 1),
            "optimization_score_current": self.optimization_score_current,
            "optimization_score_target": self.target_optimization_score,
            "compression_ratio": self.compression_ratio,
            "uptime_seconds": self.uptime_seconds,
            "transactions": treasury.transactions,
        }

    async def start_autonomy_loops(self) -> None:
        """
        Start background autonomy loops for CIaaS operations.
        
        Runs Salamander's autonomous loops in parallel with intelligence operations.
        """
        if not self.enable_autonomy_loops:
            return
        
        if self._is_running:
            return
        
        self._is_running = True
        
        # Start main autonomy loop
        self._autonomy_task = asyncio.create_task(
            self.salamander.main_autonomy_loop(observation_interval_seconds=5.0)
        )
        
        # Start phi optimization loop (critical for compression)
        self._phi_task = asyncio.create_task(
            self.salamander.phi_optimization_loop(optimization_interval_seconds=600.0)  # 10 minutes for intelligence
        )
        
        # Start scaling optimization loop
        self._scaling_task = asyncio.create_task(
            self.salamander.scaling_optimization_loop(optimization_interval_seconds=1800.0)
        )
        
        self.salamander.audit_log = self.salamander.audit_log.append(
            "ciaas_autonomy_loops_started",
            timestamp=time(),
        )

    async def stop_autonomy_loops(self) -> None:
        """
        Stop background autonomy loops.
        """
        if not self._is_running:
            return
        
        self._is_running = False
        self.salamander.stop()
        
        # Cancel background tasks
        if self._autonomy_task:
            self._autonomy_task.cancel()
        if self._phi_task:
            self._phi_task.cancel()
        if self._scaling_task:
            self._scaling_task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(
            self._autonomy_task,
            self._phi_task,
            self._scaling_task,
            return_exceptions=True,
        )
        
        self.salamander.audit_log = self.salamander.audit_log.append(
            "ciaas_autonomy_loops_stopped",
            timestamp=time(),
        )

    def get_ciaas_health_report(self) -> Dict[str, Any]:
        """
        Get comprehensive health report for CIaaS operations.
        
        Includes Salamander observability data for regulatory compliance.
        """
        health_report = self.salamander.get_health_report()
        
        # Add CIaaS-specific metrics
        health_report["ciaas_specific"] = {
            "optimization_score_current": self.optimization_score_current,
            "optimization_score_target": self.target_optimization_score,
            "optimization_efficiency": self.optimization_score_current / max(self.target_optimization_score, 1.0),
            "workload_executions": self.workload_executions,
            "data_processed_bytes": self.data_processed_bytes,
            "intelligence_errors": self.intelligence_errors,
            "error_rate": self.intelligence_errors / max(self.workload_executions, 1),
            "compression_ratio": self.compression_ratio,
            "active_services": len(self.intelligence_services),
            "uptime_seconds": self.uptime_seconds,
        }
        
        return health_report

    def share_intelligence_blueprint(self) -> Dict[str, Any]:
        """
        Share successful intelligence blueprint to species memory.
        
        Enables cross-instance learning for network effects.
        """
        # Get current intelligence configuration
        blueprint = {
            "type": "intelligence_configuration",
            "target_optimization_score": self.target_optimization_score,
            "phi_value": self.salamander.phi_tuning.phi_current,
            "compression_ratio": self.salamander.phi_tuning.phi_baseline_efficiency,
            "worker_count": self.salamander.worker_scaling.current_worker_count,
            "success_metrics": {
                "optimization_efficiency": self.optimization_score_current / max(self.target_optimization_score, 1),
                "error_rate": self.intelligence_errors / max(self.workload_executions, 1),
                "compression_ratio": self.compression_ratio,
            },
            "timestamp": time(),
        }
        
        # Add to species memory
        if hasattr(self.salamander, 'blueprint_library'):
            self.salamander.blueprint_library.add_blueprint(blueprint)
        
        self.salamander.audit_log = self.salamander.audit_log.append(
            "intelligence_blueprint_shared",
            timestamp=time(),
            blueprint_hash=hash(str(blueprint)),
        )
        
        return blueprint


# Integration helper for existing CIaaS system
def integrate_salamander_into_ciaas(
    ciaas_system: Any,
    target_optimization_score: float = 0.95,
    enable_autonomy_loops: bool = True,
) -> SalamanderCIaaSIntegration:
    """
    Helper function to integrate Salamander into existing CIaaS system.
    
    Args:
        ciaas_system: The existing CIaaS system instance
        target_optimization_score: Target optimization score for intelligence workloads
        enable_autonomy_loops: Whether to enable background autonomy loops
    
    Returns:
        SalamanderCIaaSIntegration instance
    """
    integration = SalamanderCIaaSIntegration(
        ciaas_system=ciaas_system,
        target_optimization_score=target_optimization_score,
        enable_autonomy_loops=enable_autonomy_loops,
    )
    
    integration.initialize()
    
    return integration
