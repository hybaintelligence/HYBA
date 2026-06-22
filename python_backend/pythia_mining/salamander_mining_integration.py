"""Salamander Integration for Mining System (First Priority).

This module integrates the Salamander autonomous operations layer into the
HYBA mining system, providing self-healing, self-optimization, and economic
autonomy for mining operations.

Integration Architecture:
- SalamanderCore: Observes mining system state, detects anomalies, executes regeneration
- Evidence-Based Regeneration: Recovers mining state from immutable audit logs
- Distributed Agent Coherence: Coordinates mining agents without explicit messaging
- Adaptive φ-Tuning: Optimizes compression ratios in real-time
- Self-Scaling Worker Pool: Dynamically scales mining workers based on ROI
- Species Memory: Shares successful mining blueprints across mining instances
"""

from __future__ import annotations

import asyncio
from time import time as time_time
from typing import Any, Dict, List, Optional

from .salamander_frontier import (
    SalamanderCore,
    SalamanderOrchestrator,
    SystemMetrics,
    Anomaly,
    RegenerationOutcome,
    ImmutableEvidenceLog,
)


class SalamanderMiningIntegration:
    """
    Integration layer for Salamander autonomous operations in mining system.
    
    This class bridges the existing mining infrastructure with Salamander's
    autonomous capabilities, providing self-healing, self-optimization, and
    economic autonomy without requiring architectural changes to the mining system.
    """

    def __init__(
        self,
        mining_system: Any,
        target_hashrate: float = 150.0,
        enable_autonomy_loops: bool = True,
    ):
        """
        Initialize Salamander integration for mining system.
        
        Args:
            mining_system: The existing mining system instance
            target_hashrate: Target hashrate for optimization
            enable_autonomy_loops: Whether to enable background autonomy loops
        """
        self.mining_system = mining_system
        self.target_hashrate = float(target_hashrate)
        self.enable_autonomy_loops = enable_autonomy_loops
        
        # Initialize Salamander orchestrator
        self.salamander = SalamanderOrchestrator(
            total_target_hashrate=self.target_hashrate,
        )
        
        # Initialize Salamander core for direct access
        self.salamander_core = self.salamander.salamander_core
        
        # Track mining-specific state
        self.mining_iteration_count = 0
        self.current_hashrate = 0.0
        self.shares_submitted = 0
        self.shares_accepted = 0
        self.shares_rejected = 0
        self.pool_connected = False
        self.last_share_time = 0.0
        
        # Background tasks
        self._autonomy_task: Optional[asyncio.Task] = None
        self._phi_task: Optional[asyncio.Task] = None
        self._scaling_task: Optional[asyncio.Task] = None
        self._is_running = False

    def initialize(self) -> None:
        """
        Initialize Salamander for mining operations.
        
        This should be called when the mining system starts up.
        """
        # Initialize Salamander orchestrator
        self.salamander.initialize()
        
        # Log initialization to audit trail
        self.salamander.audit_log = self.salamander.audit_log.append(
            "mining_salamander_initialized",
            timestamp=time_time(),
            target_hashrate=self.target_hashrate,
            mining_system_type=type(self.mining_system).__name__,
        )

    def observe_mining_state(self) -> SystemMetrics:
        """
        Observe current mining system state.
        
        Returns comprehensive metrics for anomaly detection and optimization.
        """
        # Gather metrics from mining system
        if hasattr(self.mining_system, 'controller') and self.mining_system.controller:
            # Get metrics from autonomous controller
            if hasattr(self.mining_system.controller, 'get_metrics'):
                controller_metrics = self.mining_system.controller.get_metrics()
                self.current_hashrate = controller_metrics.get('hashrate', 0.0)
            else:
                self.current_hashrate = self.mining_system.controller.get('hashrate', 0.0)
        
        # Get pool connection status
        if hasattr(self.mining_system, 'stratum_client') and self.mining_system.stratum_client:
            self.pool_connected = self.mining_system.stratum_client.is_connected()
        
        # Calculate share acceptance rate
        total_shares = max(self.shares_submitted, 1)
        acceptance_rate = self.shares_accepted / total_shares
        rejection_rate = self.shares_rejected / total_shares
        
        # Get memory usage if available
        memory_used = 0.0
        memory_available = 1.0
        if hasattr(self.mining_system, 'get_memory_usage'):
            memory_info = self.mining_system.get_memory_usage()
            memory_used = memory_info.get('used', 0.0)
            memory_available = memory_info.get('available', 1.0)
        
        # Build agent health list
        agent_health = []
        if hasattr(self.mining_system, 'get_agent_status'):
            agents = self.mining_system.get_agent_status()
            for agent_id, status in agents.items():
                agent_health.append({
                    'id': agent_id,
                    'status': status.get('status', 'unknown'),
                    'time_since_last_job_ms': status.get('time_since_last_job_ms', 0),
                })
        
        # Build worker health list
        worker_health = []
        if hasattr(self.mining_system, 'get_worker_status'):
            workers = self.mining_system.get_worker_status()
            for worker_id, status in workers.items():
                worker_health.append({
                    'id': worker_id,
                    'status': status.get('status', 'unknown'),
                    'hashrate': status.get('hashrate', 0.0),
                })
        
        # Observe system state through SalamanderCore
        metrics = self.salamander_core.observe_system_state(
            hashrate_current=self.current_hashrate,
            hashrate_target=self.target_hashrate,
            memory_used=memory_used,
            memory_available=memory_available,
            agent_health=agent_health,
            worker_health=worker_health,
        )
        
        return metrics

    def detect_mining_anomaly(self, metrics: SystemMetrics) -> Optional[Anomaly]:
        """
        Detect mining-specific anomalies.
        
        Extends SalamanderCore's anomaly detection with mining-specific logic.
        """
        # Use SalamanderCore's built-in anomaly detection
        anomaly = self.salamander_core.detect_anomaly(metrics)
        
        if anomaly is not None:
            return anomaly
        
        # Mining-specific anomaly detection
        
        # Pool connection loss
        if not self.pool_connected and self.shares_submitted > 0:
            return Anomaly(
                type="POOL_CONNECTION_LOST",
                severity="CRITICAL",
                action="reconnect_to_pool",
                current_value=0.0,
                target_value=1.0,
            )
        
        # Stale mining (no shares for extended period)
        time_since_last_share = time_time() - self.last_share_time
        if time_since_last_share > 300:  # 5 minutes
            return Anomaly(
                type="MINING_STALL",
                severity="HIGH",
                action="regenerate_mining_state",
                stall_duration_ms=time_since_last_share * 1000,
            )
        
        # Share rejection rate too high
        if metrics.share_acceptance_rate < 0.8:
            return Anomaly(
                type="HIGH_REJECTION_RATE",
                severity="MEDIUM",
                action="optimize_mining_parameters",
                current_value=metrics.share_acceptance_rate,
                target_value=0.95,
            )
        
        return None

    def execute_mining_regeneration(self, anomaly: Anomaly) -> RegenerationOutcome:
        """
        Execute regeneration for mining-specific anomalies.
        
        Extends SalamanderCore's regeneration with mining-specific recovery strategies.
        """
        # Log regeneration trigger
        self.salamander.audit_log = self.salamander.audit_log.append(
            "mining_regeneration_triggered",
            timestamp=time_time(),
            anomaly_type=anomaly.type,
            severity=anomaly.severity,
        )
        
        # Use SalamanderCore's regeneration
        outcome = self.salamander_core.execute_regeneration(anomaly)
        
        # Mining-specific recovery actions
        match anomaly.type:
            case "POOL_CONNECTION_LOST":
                # Trigger pool reconnection
                if hasattr(self.mining_system, 'reconnect_to_pool'):
                    self.mining_system.reconnect_to_pool()
                    self.salamander.audit_log = self.salamander.audit_log.append(
                        "pool_reconnection_attempted",
                        timestamp=time_time(),
                    )
            
            case "MINING_STALL":
                # Regenerate mining state
                if hasattr(self.mining_system, 'regenerate_state'):
                    self.mining_system.regenerate_state()
                    self.salamander.audit_log = self.salamander.audit_log.append(
                        "mining_state_regenerated",
                        timestamp=time_time(),
                    )
            
            case "HIGH_REJECTION_RATE":
                # Optimize mining parameters
                if hasattr(self.mining_system, 'optimize_parameters'):
                    self.mining_system.optimize_parameters()
                    self.salamander.audit_log = self.salamander.audit_log.append(
                        "mining_parameters_optimized",
                        timestamp=time_time(),
                    )
        
        return outcome

    def record_share_submission(
        self,
        job_id: str,
        nonce: int,
        difficulty: float,
        accepted: bool,
        revenue_btc: float = 0.0,
    ) -> None:
        """
        Record a share submission to the audit log.
        
        This provides evidence for treasury state recovery and regulatory compliance.
        """
        self.shares_submitted += 1
        self.last_share_time = time_time()
        
        if accepted:
            self.shares_accepted += 1
            event_type = "share_accepted"
        else:
            self.shares_rejected += 1
            event_type = "share_rejected"
        
        self.salamander.audit_log = self.salamander.audit_log.append(
            event_type,
            timestamp=time_time(),
            job_id=job_id,
            nonce=nonce,
            difficulty=difficulty,
            pool_reward_btc=revenue_btc if accepted else 0.0,
        )

    def get_treasury_state(self) -> Dict[str, Any]:
        """
        Get current treasury state from evidence.
        
        Provides financial state recovery for regulatory compliance.
        """
        from .salamander_frontier import EvidenceBasedRegenerator
        
        regenerator = EvidenceBasedRegenerator(self.salamander.audit_log)
        treasury = regenerator.recover_treasury_state()
        
        return {
            "balance_btc": treasury.balance_btc,
            "total_shares_submitted": treasury.total_shares_submitted,
            "total_shares_accepted": treasury.total_shares_accepted,
            "total_shares_rejected": treasury.total_shares_rejected,
            "acceptance_rate": treasury.total_shares_accepted / max(treasury.total_shares_submitted, 1),
            "transactions": treasury.transactions,
        }

    async def start_autonomy_loops(self) -> None:
        """
        Start background autonomy loops for mining operations.
        
        Runs Salamander's autonomous loops in parallel with mining operations.
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
        
        # Start phi optimization loop
        self._phi_task = asyncio.create_task(
            self.salamander.phi_optimization_loop(optimization_interval_seconds=600.0)
        )
        
        # Start scaling optimization loop
        self._scaling_task = asyncio.create_task(
            self.salamander.scaling_optimization_loop(optimization_interval_seconds=1800.0)
        )
        
        self.salamander.audit_log = self.salamander.audit_log.append(
            "mining_autonomy_loops_started",
            timestamp=time_time(),
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
            "mining_autonomy_loops_stopped",
            timestamp=time_time(),
        )

    def get_mining_health_report(self) -> Dict[str, Any]:
        """
        Get comprehensive health report for mining operations.
        
        Includes Salamander observability data for regulatory compliance.
        """
        health_report = self.salamander.get_health_report()
        
        # Add mining-specific metrics
        health_report["mining_specific"] = {
            "current_hashrate": self.current_hashrate,
            "target_hashrate": self.target_hashrate,
            "hashrate_efficiency": self.current_hashrate / max(self.target_hashrate, 1.0),
            "shares_submitted": self.shares_submitted,
            "shares_accepted": self.shares_accepted,
            "shares_rejected": self.shares_rejected,
            "pool_connected": self.pool_connected,
            "time_since_last_share_seconds": time_time() - self.last_share_time,
        }
        
        return health_report

    def share_mining_blueprint(self) -> Dict[str, Any]:
        """
        Share successful mining blueprint to species memory.
        
        Enables cross-instance learning for network effects.
        """
        # Get current mining configuration
        blueprint = {
            "type": "mining_configuration",
            "target_hashrate": self.target_hashrate,
            "phi_value": self.salamander.phi_tuning.phi_current,
            "compression_ratio": self.salamander.phi_tuning.phi_baseline_efficiency,
            "worker_count": self.salamander.worker_scaling.current_worker_count,
            "success_metrics": {
                "hashrate_efficiency": self.current_hashrate / max(self.target_hashrate, 1.0),
                "share_acceptance_rate": self.shares_accepted / max(self.shares_submitted, 1),
            },
            "timestamp": time_time(),
        }
        
        # Add to species memory
        if hasattr(self.salamander, 'blueprint_library'):
            self.salamander.blueprint_library.add_blueprint(blueprint)
        
        self.salamander.audit_log = self.salamander.audit_log.append(
            "mining_blueprint_shared",
            timestamp=time_time(),
            blueprint_hash=hash(str(blueprint)),
        )
        
        return blueprint


# Integration helper for existing mining system
def integrate_salamander_into_mining(
    mining_system: Any,
    target_hashrate: float = 150.0,
    enable_autonomy_loops: bool = True,
) -> SalamanderMiningIntegration:
    """
    Helper function to integrate Salamander into existing mining system.
    
    Args:
        mining_system: The existing mining system instance
        target_hashrate: Target hashrate for optimization
        enable_autonomy_loops: Whether to enable background autonomy loops
    
    Returns:
        SalamanderMiningIntegration instance
    """
    integration = SalamanderMiningIntegration(
        mining_system=mining_system,
        target_hashrate=target_hashrate,
        enable_autonomy_loops=enable_autonomy_loops,
    )
    
    integration.initialize()
    
    return integration
