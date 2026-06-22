"""Salamander Integration for QaaS (Quantum-as-a-Service).

This module integrates the Salamander autonomous operations layer into the
HYBA QaaS system, providing self-healing, self-optimization, and economic
autonomy for quantum compute operations.

Integration Architecture:
- SalamanderCore: Observes quantum system state, detects anomalies, executes regeneration
- Evidence-Based Regeneration: Recovers quantum state from immutable audit logs
- Distributed Agent Coherence: Coordinates quantum instances without explicit messaging
- Adaptive φ-Tuning: Optimizes φ-resonance in real-time
- Self-Scaling Worker Pool: Dynamically scales quantum resources based on ROI
- Species Memory: Shares successful quantum blueprints across instances
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


class SalamanderQaaSIntegration:
    """
    Integration layer for Salamander autonomous operations in QaaS system.
    
    This class bridges the existing QaaS infrastructure with Salamander's
    autonomous capabilities, providing self-healing, self-optimization, and
    economic autonomy for quantum compute operations.
    """

    def __init__(
        self,
        qaas_system: Any,
        target_phi_resonance: float = 0.9565,
        enable_autonomy_loops: bool = True,
    ):
        """
        Initialize Salamander integration for QaaS system.
        
        Args:
            qaas_system: The existing QaaS system instance
            target_phi_resonance: Target φ-resonance for optimization
            enable_autonomy_loops: Whether to enable background autonomy loops
        """
        self.qaas_system = qaas_system
        self.target_phi_resonance = float(target_phi_resonance)
        self.enable_autonomy_loops = enable_autonomy_loops
        
        # Initialize Salamander orchestrator
        self.salamander = SalamanderOrchestrator(
            total_target_hashrate=target_phi_resonance * 100,  # Scale for quantum
        )
        
        # Initialize Salamander core for direct access
        self.salamander_core = self.salamander.salamander_core
        
        # Track QaaS-specific state
        self.quantum_instances: Dict[str, Any] = {}
        self.circuit_executions = 0
        self.phi_resonance_current = 0.0
        self.surface_code_cycles = 0
        self.quantum_errors = 0
        self.uptime_seconds = 0.0
        self.last_circuit_time = 0.0
        
        # Background tasks
        self._autonomy_task: Optional[asyncio.Task] = None
        self._phi_task: Optional[asyncio.Task] = None
        self._scaling_task: Optional[asyncio.Task] = None
        self._is_running = False

    def initialize(self) -> None:
        """
        Initialize Salamander for QaaS operations.
        
        This should be called when the QaaS system starts up.
        """
        # Initialize Salamander orchestrator
        self.salamander.initialize()
        
        # Log initialization to audit trail
        self.salamander.audit_log = self.salamander.audit_log.append(
            "qaas_salamander_initialized",
            timestamp=time(),
            target_phi_resonance=self.target_phi_resonance,
            qaas_system_type=type(self.qaas_system).__name__,
        )

    def observe_qaas_state(self) -> SystemMetrics:
        """
        Observe current QaaS system state.
        
        Returns comprehensive metrics for anomaly detection and optimization.
        """
        # Gather metrics from QaaS system
        if hasattr(self.qaas_system, 'get_metrics'):
            qaas_metrics = self.qaas_system.get_metrics()
            self.phi_resonance_current = qaas_metrics.get('phi_resonance', 0.0)
            self.surface_code_cycles = qaas_metrics.get('surface_code_cycles', 0)
            self.quantum_errors = qaas_metrics.get('quantum_errors', 0)
        
        # Get instance status
        instance_count = len(self.quantum_instances)
        active_instances = sum(
            1 for instance in self.quantum_instances.values()
            if instance.get('state') == 'running'
        )
        
        # Calculate uptime
        if self.uptime_seconds > 0:
            self.uptime_seconds += 1.0  # Increment on each observation
        
        # Get memory usage if available
        memory_used = 0.0
        memory_available = 1.0
        if hasattr(self.qaas_system, 'get_memory_usage'):
            memory_info = self.qaas_system.get_memory_usage()
            memory_used = memory_info.get('used', 0.0)
            memory_available = memory_info.get('available', 1.0)
        
        # Build instance health list
        instance_health = []
        for instance_id, instance in self.quantum_instances.items():
            instance_health.append({
                'id': instance_id,
                'state': instance.get('state', 'unknown'),
                'logical_qubits': instance.get('logical_qubits', 0),
                'code_distance': instance.get('code_distance', 7),
                'time_since_last_circuit_ms': (time() - self.last_circuit_time) * 1000,
            })
        
        # Observe system state through SalamanderCore
        metrics = self.salamander_core.observe_system_state(
            hashrate_current=self.phi_resonance_current * 100,  # Scale for quantum
            hashrate_target=self.target_phi_resonance * 100,
            memory_used=memory_used,
            memory_available=memory_available,
            agent_health=instance_health,
            worker_health=[],
        )
        
        return metrics

    def detect_qaas_anomaly(self, metrics: SystemMetrics) -> Optional[Anomaly]:
        """
        Detect QaaS-specific anomalies.
        
        Extends SalamanderCore's anomaly detection with QaaS-specific logic.
        """
        # Use SalamanderCore's built-in anomaly detection
        anomaly = self.salamander_core.detect_anomaly(metrics)
        
        if anomaly is not None:
            return anomaly
        
        # QaaS-specific anomaly detection
        
        # φ-resonance degradation
        if self.phi_resonance_current < self.target_phi_resonance * 0.9:
            return Anomaly(
                type="PHI_RESONANCE_DEGRADATION",
                severity="HIGH",
                action="optimize_phi_resonance",
                current_value=self.phi_resonance_current,
                target_value=self.target_phi_resonance,
            )
        
        # Quantum error rate too high
        error_rate = self.quantum_errors / max(self.surface_code_cycles, 1)
        if error_rate > 0.1:  # 10% error rate
            return Anomaly(
                type="HIGH_QUANTUM_ERROR_RATE",
                severity="CRITICAL",
                action="regenerate_quantum_state",
                current_value=error_rate,
                target_value=0.01,
            )
        
        # Instance stall (no circuits for extended period)
        time_since_last_circuit = time() - self.last_circuit_time
        if time_since_last_circuit > 600:  # 10 minutes
            return Anomaly(
                type="QUANTUM_INSTANCE_STALL",
                severity="HIGH",
                action="regenerate_quantum_state",
                stall_duration_ms=time_since_last_circuit * 1000,
            )
        
        return None

    def execute_qaas_regeneration(self, anomaly: Anomaly) -> RegenerationOutcome:
        """
        Execute regeneration for QaaS-specific anomalies.
        
        Extends SalamanderCore's regeneration with QaaS-specific recovery strategies.
        """
        # Log regeneration trigger
        self.salamander.audit_log = self.salamander.audit_log.append(
            "qaas_regeneration_triggered",
            timestamp=time(),
            anomaly_type=anomaly.type,
            severity=anomaly.severity,
        )
        
        # Use SalamanderCore's regeneration
        outcome = self.salamander_core.execute_regeneration(anomaly)
        
        # QaaS-specific recovery actions
        match anomaly.type:
            case "PHI_RESONANCE_DEGRADATION":
                # Trigger φ-resonance optimization
                if hasattr(self.qaas_system, 'optimize_phi_resonance'):
                    self.qaas_system.optimize_phi_resonance()
                    self.salamander.audit_log = self.salamander.audit_log.append(
                        "phi_resonance_optimization_triggered",
                        timestamp=time(),
                    )
            
            case "HIGH_QUANTUM_ERROR_RATE":
                # Regenerate quantum state
                if hasattr(self.qaas_system, 'regenerate_quantum_state'):
                    self.qaas_system.regenerate_quantum_state()
                    self.salamander.audit_log = self.salamander.audit_log.append(
                        "quantum_state_regenerated",
                        timestamp=time(),
                    )
            
            case "QUANTUM_INSTANCE_STALL":
                # Regenerate instance state
                if hasattr(self.qaas_system, 'regenerate_instance_state'):
                    self.qaas_system.regenerate_instance_state()
                    self.salamander.audit_log = self.salamander.audit_log.append(
                        "quantum_instance_state_regenerated",
                        timestamp=time(),
                    )
        
        return outcome

    def record_circuit_execution(
        self,
        instance_id: str,
        circuit_depth: int,
        shots: int,
        phi_resonance: float,
        success: bool,
        execution_time_ms: float,
    ) -> None:
        """
        Record a quantum circuit execution to the audit log.
        
        This provides evidence for regulatory compliance and species memory.
        """
        self.circuit_executions += 1
        self.last_circuit_time = time()
        
        if success:
            self.surface_code_cycles += shots
        else:
            self.quantum_errors += shots
        
        event_type = "circuit_success" if success else "circuit_failure"
        
        self.salamander.audit_log = self.salamander.audit_log.append(
            event_type,
            timestamp=time(),
            instance_id=instance_id,
            circuit_depth=circuit_depth,
            shots=shots,
            phi_resonance=phi_resonance,
            execution_time_ms=execution_time_ms,
        )

    def register_quantum_instance(
        self,
        instance_id: str,
        logical_qubits: int,
        code_distance: int,
        state: str = "provisioned",
    ) -> None:
        """
        Register a quantum instance for autonomous management.
        """
        self.quantum_instances[instance_id] = {
            'logical_qubits': logical_qubits,
            'code_distance': code_distance,
            'state': state,
            'registered_at': time(),
        }
        
        # Add agent to coherence system
        self.salamander.agent_coherence.add_agent(
            agent_id=instance_id,
            job_id=f"quantum_{instance_id}",
            timestamp=time(),
        )
        
        self.salamander.audit_log = self.salamander.audit_log.append(
            "quantum_instance_registered",
            timestamp=time(),
            instance_id=instance_id,
            logical_qubits=logical_qubits,
            code_distance=code_distance,
        )

    def get_quantum_treasury_state(self) -> Dict[str, Any]:
        """
        Get current quantum treasury state from evidence.
        
        Provides compute unit accounting for billing and regulatory compliance.
        """
        from pythia_mining.salamander_frontier import EvidenceBasedRegenerator
        
        regenerator = EvidenceBasedRegenerator(self.salamander.audit_log)
        treasury = regenerator.recover_treasury_state()
        
        return {
            "compute_units_consumed": self.circuit_executions,
            "surface_code_cycles": self.surface_code_cycles,
            "quantum_errors": self.quantum_errors,
            "error_rate": self.quantum_errors / max(self.surface_code_cycles, 1),
            "phi_resonance_current": self.phi_resonance_current,
            "phi_resonance_target": self.target_phi_resonance,
            "uptime_seconds": self.uptime_seconds,
            "transactions": treasury.transactions,
        }

    async def start_autonomy_loops(self) -> None:
        """
        Start background autonomy loops for QaaS operations.
        
        Runs Salamander's autonomous loops in parallel with quantum operations.
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
        
        # Start phi optimization loop (critical for QaaS)
        self._phi_task = asyncio.create_task(
            self.salamander.phi_optimization_loop(optimization_interval_seconds=300.0)  # 5 minutes for quantum
        )
        
        # Start scaling optimization loop
        self._scaling_task = asyncio.create_task(
            self.salamander.scaling_optimization_loop(optimization_interval_seconds=1800.0)
        )
        
        self.salamander.audit_log = self.salamander.audit_log.append(
            "qaas_autonomy_loops_started",
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
            "qaas_autonomy_loops_stopped",
            timestamp=time(),
        )

    def get_qaas_health_report(self) -> Dict[str, Any]:
        """
        Get comprehensive health report for QaaS operations.
        
        Includes Salamander observability data for regulatory compliance.
        """
        health_report = self.salamander.get_health_report()
        
        # Add QaaS-specific metrics
        health_report["qaas_specific"] = {
            "phi_resonance_current": self.phi_resonance_current,
            "phi_resonance_target": self.target_phi_resonance,
            "phi_resonance_efficiency": self.phi_resonance_current / max(self.target_phi_resonance, 1.0),
            "circuit_executions": self.circuit_executions,
            "surface_code_cycles": self.surface_code_cycles,
            "quantum_errors": self.quantum_errors,
            "error_rate": self.quantum_errors / max(self.surface_code_cycles, 1),
            "active_instances": len(self.quantum_instances),
            "uptime_seconds": self.uptime_seconds,
        }
        
        return health_report

    def share_quantum_blueprint(self) -> Dict[str, Any]:
        """
        Share successful quantum blueprint to species memory.
        
        Enables cross-instance learning for network effects.
        """
        # Get current quantum configuration
        blueprint = {
            "type": "quantum_configuration",
            "target_phi_resonance": self.target_phi_resonance,
            "phi_value": self.salamander.phi_tuning.phi_current,
            "compression_ratio": self.salamander.phi_tuning.phi_baseline_efficiency,
            "worker_count": self.salamander.worker_scaling.current_worker_count,
            "success_metrics": {
                "phi_resonance_efficiency": self.phi_resonance_current / max(self.target_phi_resonance, 1),
                "error_rate": self.quantum_errors / max(self.surface_code_cycles, 1),
            },
            "timestamp": time(),
        }
        
        # Add to species memory
        if hasattr(self.salamander, 'blueprint_library'):
            self.salamander.blueprint_library.add_blueprint(blueprint)
        
        self.salamander.audit_log = self.salamander.audit_log.append(
            "quantum_blueprint_shared",
            timestamp=time(),
            blueprint_hash=hash(str(blueprint)),
        )
        
        return blueprint


# Integration helper for existing QaaS system
def integrate_salamander_into_qaas(
    qaas_system: Any,
    target_phi_resonance: float = 0.9565,
    enable_autonomy_loops: bool = True,
) -> SalamanderQaaSIntegration:
    """
    Helper function to integrate Salamander into existing QaaS system.
    
    Args:
        qaas_system: The existing QaaS system instance
        target_phi_resonance: Target φ-resonance for optimization
        enable_autonomy_loops: Whether to enable background autonomy loops
    
    Returns:
        SalamanderQaaSIntegration instance
    """
    integration = SalamanderQaaSIntegration(
        qaas_system=qaas_system,
        target_phi_resonance=target_phi_resonance,
        enable_autonomy_loops=enable_autonomy_loops,
    )
    
    integration.initialize()
    
    return integration
