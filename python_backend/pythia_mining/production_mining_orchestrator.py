"""
Production Mining Orchestrator - Enterprise-Grade Pool Management

Implements multi-pool failover, health monitoring, share tracking, and
deterministic mining coordination for real-world deployment.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from pythia_mining.audit_logger import AuditEvent, AuditEventType, get_audit_logger
from pythia_mining.metrics_store import PoolMetrics, get_metrics_store
from pythia_mining.stratum_client import AllPoolsOfflineError, StratumClient, ShareResult
from pythia_mining.pool_profiles import PoolProfile


class PoolHealth(Enum):
    """Pool health status indicators."""
    HEALTHY = "healthy"           # Connected, authenticated, receiving jobs
    DEGRADED = "degraded"          # Connected but experiencing issues
    UNHEALTHY = "unhealthy"        # Connection problems but retrying
    OFFLINE = "offline"            # Connection exhausted or permanently failed
    UNKNOWN = "unknown"            # Not yet evaluated


class MiningStrategy(Enum):
    """Share submission strategy."""
    FIRST_POOL = "first_pool"      # Only submit to first pool
    FAILOVER = "failover"          # Submit to first healthy, cascade on failure
    MULTI_POOL = "multi_pool"      # Submit to all healthy pools


@dataclass
class PoolHealthStatus:
    """Health and performance metrics for a pool."""
    pool_name: str
    pool_url: str
    health: PoolHealth = PoolHealth.UNKNOWN
    last_status_check: float = field(default_factory=time.time)
    connection_state: str = "UNKNOWN"
    last_job_time: Optional[float] = None
    last_share_time: Optional[float] = None
    last_error: Optional[str] = None
    shares_submitted_total: int = 0
    shares_accepted_total: int = 0
    shares_rejected_total: int = 0
    connection_failures: int = 0
    consecutive_failures: int = 0
    avg_latency_ms: Optional[float] = None
    acceptance_rate: float = 0.0
    uptime_percentage: float = 100.0
    last_difficulty: float = 1.0
    active_jobs: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pool_name": self.pool_name,
            "pool_url": self.pool_url,
            "health": self.health.value,
            "last_status_check": self.last_status_check,
            "connection_state": self.connection_state,
            "last_job_time": self.last_job_time,
            "last_share_time": self.last_share_time,
            "last_error": self.last_error,
            "shares_submitted_total": self.shares_submitted_total,
            "shares_accepted_total": self.shares_accepted_total,
            "shares_rejected_total": self.shares_rejected_total,
            "connection_failures": self.connection_failures,
            "consecutive_failures": self.consecutive_failures,
            "avg_latency_ms": self.avg_latency_ms,
            "acceptance_rate": self.acceptance_rate,
            "uptime_percentage": self.uptime_percentage,
            "last_difficulty": self.last_difficulty,
            "active_jobs": self.active_jobs,
        }


@dataclass
class MiningStat:
    """Aggregated mining statistics."""
    total_shares_submitted: int = 0
    total_shares_accepted: int = 0
    total_shares_rejected: int = 0
    global_acceptance_rate: float = 0.0
    active_pools: int = 0
    healthy_pools: int = 0
    degraded_pools: int = 0
    offline_pools: int = 0
    total_pools: int = 0
    uptime_seconds: float = 0.0
    total_connection_attempts: int = 0
    successful_connections: int = 0
    connection_success_rate: float = 0.0
    avg_latency_ms: Optional[float] = None
    mining_strategy: str = "failover"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_shares_submitted": self.total_shares_submitted,
            "total_shares_accepted": self.total_shares_accepted,
            "total_shares_rejected": self.total_shares_rejected,
            "global_acceptance_rate": self.global_acceptance_rate,
            "active_pools": self.active_pools,
            "healthy_pools": self.healthy_pools,
            "degraded_pools": self.degraded_pools,
            "offline_pools": self.offline_pools,
            "total_pools": self.total_pools,
            "uptime_seconds": self.uptime_seconds,
            "total_connection_attempts": self.total_connection_attempts,
            "successful_connections": self.successful_connections,
            "connection_success_rate": self.connection_success_rate,
            "avg_latency_ms": self.avg_latency_ms,
            "mining_strategy": self.mining_strategy,
        }


class ProductionMiningOrchestrator:
    """
    Enterprise mining orchestrator managing multiple pools with health monitoring,
    automatic failover, and comprehensive telemetry.
    """
    
    def __init__(
        self,
        profiles: List[PoolProfile],
        mining_strategy: MiningStrategy = MiningStrategy.FAILOVER,
        health_check_interval: float = 30.0,
        max_pool_failures_before_degraded: int = 3,
        max_pool_failures_before_offline: int = 10,
    ):
        """
        Initialize the orchestrator.
        
        Args:
            profiles: List of PoolProfile objects in priority order
            mining_strategy: Strategy for share submission
            health_check_interval: Seconds between health checks
            max_pool_failures_before_degraded: Failures to mark degraded
            max_pool_failures_before_offline: Failures to mark offline
        """
        if not profiles:
            raise ValueError("At least one pool profile is required")
        
        self.profiles = profiles
        self.mining_strategy = mining_strategy
        self.health_check_interval = health_check_interval
        self.max_pool_failures_before_degraded = max_pool_failures_before_degraded
        self.max_pool_failures_before_offline = max_pool_failures_before_offline
        
        self.clients: Dict[str, StratumClient] = {}
        self.pool_health: Dict[str, PoolHealthStatus] = {}
        self.logger = logging.getLogger(__name__)
        self.audit_logger = get_audit_logger()
        self.metrics_store = get_metrics_store()
        
        self.start_time = time.time()
        self.total_connection_attempts = 0
        self.successful_connections = 0
        
        self._health_check_task: Optional[asyncio.Task] = None
        self._monitor_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Initialize pool health tracking
        for profile in profiles:
            pool_id = profile.pool_id
            self.pool_health[pool_id] = PoolHealthStatus(
                pool_name=profile.name,
                pool_url=profile.url,
            )
    
    async def initialize(self) -> None:
        """Initialize connections to all pools."""
        self.logger.info("Initializing mining orchestrator with %d pools", len(self.profiles))
        
        initialization_tasks = []
        for profile in self.profiles:
            task = self._initialize_pool(profile)
            initialization_tasks.append(task)
        
        results = await asyncio.gather(*initialization_tasks, return_exceptions=True)
        
        successful = sum(1 for r in results if r is True)
        self.logger.info("Pool initialization complete: %d/%d pools connected", 
                        successful, len(self.profiles))
        
        if successful == 0:
            raise AllPoolsOfflineError("Failed to connect to any mining pools")
    
    async def _initialize_pool(self, profile: PoolProfile) -> bool:
        """Initialize a single pool connection."""
        try:
            client = StratumClient(
                pool_url=profile.url,
                username=profile.username,
                password=profile.password,
                pool_name=profile.name,
                stratum_version=profile.stratum_version,
            )
            self.clients[profile.pool_id] = client
            self.total_connection_attempts += 1
            
            connected = await client.connect()
            if connected:
                self.successful_connections += 1
                self._update_pool_health(profile.pool_id, PoolHealth.HEALTHY)
                self.audit_logger.log_pool_initialized(
                    pool_id=profile.pool_id,
                    pool_name=profile.name,
                    pool_url=profile.url,
                    status="initialized"
                )
                return True
            else:
                self._update_pool_health(profile.pool_id, PoolHealth.UNHEALTHY)
                return False
        except Exception as e:
            self.logger.error("Failed to initialize pool %s: %s", profile.pool_id, e)
            self._update_pool_health(profile.pool_id, PoolHealth.OFFLINE, error=str(e))
            return False
    
    async def start(self) -> None:
        """Start health monitoring and mining operations."""
        if self._running:
            return
        
        self._running = True
        self.logger.info("Starting production mining orchestrator")
        
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        self._monitor_task = asyncio.create_task(self._monitoring_loop())
    
    async def stop(self) -> None:
        """Stop all operations and close connections."""
        self._running = False
        self.logger.info("Stopping production mining orchestrator")
        
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        # Close all pool connections
        close_tasks = [client.disconnect() for client in self.clients.values()]
        await asyncio.gather(*close_tasks, return_exceptions=True)
    
    async def _health_check_loop(self) -> None:
        """Periodic health checks for all pools."""
        while self._running:
            try:
                await asyncio.sleep(self.health_check_interval)
                
                # Check health of all pools
                check_tasks = []
                for pool_id, client in self.clients.items():
                    task = self._check_pool_health(pool_id, client)
                    check_tasks.append(task)
                
                await asyncio.gather(*check_tasks, return_exceptions=True)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("Health check loop error: %s", e)
    
    async def _check_pool_health(self, pool_id: str, client: StratumClient) -> None:
        """Check health of a single pool."""
        try:
            health_status = self.pool_health.get(pool_id)
            if not health_status:
                return
            
            # Poll for an event to verify connectivity
            job = await asyncio.wait_for(
                client.poll_live_event(timeout=5.0),
                timeout=10.0
            )
            
            if client.is_connected and client.is_authenticated:
                self._update_pool_health(pool_id, PoolHealth.HEALTHY)
            else:
                self._update_pool_health(pool_id, PoolHealth.DEGRADED)
                
        except asyncio.TimeoutError:
            self._record_pool_failure(pool_id)
        except Exception as e:
            self._record_pool_failure(pool_id, error=str(e))
    
    async def _monitoring_loop(self) -> None:
        """Continuous monitoring of mining statistics."""
        while self._running:
            try:
                await asyncio.sleep(60.0)  # Report stats every minute
                stats = self.get_mining_stats()
                self.logger.info("Mining stats: %s", stats.to_dict())
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("Monitoring loop error: %s", e)
    
    def _update_pool_health(
        self, 
        pool_id: str, 
        health: PoolHealth,
        error: Optional[str] = None
    ) -> None:
        """Update pool health status."""
        if pool_id not in self.pool_health:
            return
        
        health_status = self.pool_health[pool_id]
        old_health = health_status.health
        health_status.health = health
        health_status.last_status_check = time.time()
        
        if error:
            health_status.last_error = error
        
        # Reset consecutive failures on improvement
        if health in (PoolHealth.HEALTHY, PoolHealth.DEGRADED):
            health_status.consecutive_failures = 0
        
        if old_health != health:
            self.logger.info(
                "Pool %s health changed: %s -> %s",
                pool_id, old_health.value, health.value
            )
            self.audit_logger.log_pool_health_change(
                pool_id=pool_id,
                pool_name=health_status.pool_name,
                old_health=old_health.value,
                new_health=health.value,
            )
    
    def _record_pool_failure(
        self,
        pool_id: str,
        error: Optional[str] = None
    ) -> None:
        """Record a pool failure and update health."""
        if pool_id not in self.pool_health:
            return
        
        health_status = self.pool_health[pool_id]
        health_status.consecutive_failures += 1
        health_status.connection_failures += 1
        
        if error:
            health_status.last_error = error
        
        # Determine new health based on failure count
        if health_status.consecutive_failures >= self.max_pool_failures_before_offline:
            self._update_pool_health(pool_id, PoolHealth.OFFLINE, error)
        elif health_status.consecutive_failures >= self.max_pool_failures_before_degraded:
            self._update_pool_health(pool_id, PoolHealth.DEGRADED, error)
        else:
            self._update_pool_health(pool_id, PoolHealth.UNHEALTHY, error)
    
    async def submit_share(self, job: Any, nonce: int, extranonce2: Optional[str] = None) -> List[ShareResult]:
        """
        Submit a share according to the configured mining strategy.
        
        Args:
            job: Mining job from get_next_job()
            nonce: Nonce value to submit
            extranonce2: Optional extranonce2 override
            
        Returns:
            List of ShareResult objects from each pool attempt
        """
        results: List[ShareResult] = []
        
        if self.mining_strategy == MiningStrategy.FIRST_POOL:
            # Submit only to first healthy pool
            result = await self._submit_to_first_healthy_pool(job, nonce, extranonce2)
            if result:
                results.append(result)
        
        elif self.mining_strategy == MiningStrategy.FAILOVER:
            # Submit to first healthy, cascade on failure
            result = await self._submit_failover(job, nonce, extranonce2)
            if result:
                results.append(result)
        
        elif self.mining_strategy == MiningStrategy.MULTI_POOL:
            # Submit to all healthy pools
            results = await self._submit_to_all_pools(job, nonce, extranonce2)
        
        return results
    
    async def _submit_to_first_healthy_pool(
        self, 
        job: Any, 
        nonce: int, 
        extranonce2: Optional[str] = None
    ) -> Optional[ShareResult]:
        """Submit to first healthy pool."""
        healthy_pools = self._get_healthy_pools()
        
        for pool_id in healthy_pools:
            client = self.clients.get(pool_id)
            if not client:
                continue
            
            try:
                result = await client.submit_validated_share(job, nonce, extranonce2)
                self._record_share_result(pool_id, result)
                return result
            except Exception as e:
                self.logger.warning("Share submission to %s failed: %s", pool_id, e)
                self._record_pool_failure(pool_id, str(e))
        
        return None
    
    async def _submit_failover(
        self,
        job: Any,
        nonce: int,
        extranonce2: Optional[str] = None
    ) -> Optional[ShareResult]:
        """Submit with failover to next pool on rejection."""
        healthy_pools = self._get_healthy_pools()
        
        for pool_id in healthy_pools:
            client = self.clients.get(pool_id)
            if not client:
                continue
            
            try:
                result = await client.submit_validated_share(job, nonce, extranonce2)
                self._record_share_result(pool_id, result)
                
                # Accept this result
                if result.accepted:
                    self.logger.info("Share accepted by pool %s", pool_id)
                    return result
                else:
                    # Try next pool
                    self.logger.info("Share rejected by %s, trying next pool", pool_id)
                    continue
                    
            except Exception as e:
                self.logger.warning("Share submission to %s failed: %s", pool_id, e)
                self._record_pool_failure(pool_id, str(e))
        
        return None
    
    async def _submit_to_all_pools(
        self,
        job: Any,
        nonce: int,
        extranonce2: Optional[str] = None
    ) -> List[ShareResult]:
        """Submit to all healthy pools concurrently."""
        healthy_pools = self._get_healthy_pools()
        tasks = []
        
        for pool_id in healthy_pools:
            client = self.clients.get(pool_id)
            if not client:
                continue
            
            task = self._submit_to_pool_safe(pool_id, client, job, nonce, extranonce2)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if isinstance(r, ShareResult)]
    
    async def _submit_to_pool_safe(
        self,
        pool_id: str,
        client: StratumClient,
        job: Any,
        nonce: int,
        extranonce2: Optional[str] = None
    ) -> Optional[ShareResult]:
        """Safely submit share to a pool."""
        try:
            result = await client.submit_validated_share(job, nonce, extranonce2)
            self._record_share_result(pool_id, result)
            return result
        except Exception as e:
            self.logger.warning("Share submission to %s failed: %s", pool_id, e)
            self._record_pool_failure(pool_id, str(e))
            return None
    
    def _record_share_result(self, pool_id: str, result: ShareResult) -> None:
        """Record share submission result."""
        if pool_id not in self.pool_health:
            return
        
        health_status = self.pool_health[pool_id]
        health_status.shares_submitted_total += 1
        health_status.last_share_time = time.time()
        
        if result.accepted:
            health_status.shares_accepted_total += 1
            health_status.consecutive_failures = 0
            self._update_pool_health(pool_id, PoolHealth.HEALTHY)
        else:
            health_status.shares_rejected_total += 1
    
    def _get_healthy_pools(self) -> List[str]:
        """Get list of healthy pool IDs in priority order."""
        healthy = [
            pool_id for pool_id, status in self.pool_health.items()
            if status.health in (PoolHealth.HEALTHY, PoolHealth.DEGRADED)
        ]
        return healthy
    
    async def get_next_job(self) -> Optional[Any]:
        """
        Get next available mining job from healthy pools.
        
        Returns:
            Next job or None if no healthy pools with jobs
        """
        healthy_pools = self._get_healthy_pools()
        
        for pool_id in healthy_pools:
            client = self.clients.get(pool_id)
            if not client:
                continue
            
            try:
                job = await asyncio.wait_for(
                    client.poll_live_event(timeout=1.0),
                    timeout=5.0
                )
                
                if job:
                    health_status = self.pool_health.get(pool_id)
                    if health_status:
                        health_status.last_job_time = time.time()
                        health_status.active_jobs = len(client.current_jobs)
                    return job
                    
            except (asyncio.TimeoutError, Exception) as e:
                self.logger.debug("Failed to get job from %s: %s", pool_id, e)
        
        return None
    
    def get_mining_stats(self) -> MiningStat:
        """Get aggregated mining statistics."""
        stats = MiningStat(mining_strategy=self.mining_strategy.value)
        
        total_submitted = 0
        total_accepted = 0
        total_rejected = 0
        latencies = []
        
        for pool_id, health_status in self.pool_health.items():
            total_submitted += health_status.shares_submitted_total
            total_accepted += health_status.shares_accepted_total
            total_rejected += health_status.shares_rejected_total
            
            if health_status.health == PoolHealth.HEALTHY:
                stats.healthy_pools += 1
            elif health_status.health == PoolHealth.DEGRADED:
                stats.degraded_pools += 1
            elif health_status.health == PoolHealth.OFFLINE:
                stats.offline_pools += 1
            elif health_status.health != PoolHealth.UNKNOWN:
                stats.active_pools += 1
            
            if health_status.avg_latency_ms:
                latencies.append(health_status.avg_latency_ms)
        
        stats.total_pools = len(self.pool_health)
        stats.total_shares_submitted = total_submitted
        stats.total_shares_accepted = total_accepted
        stats.total_shares_rejected = total_rejected
        stats.total_connection_attempts = self.total_connection_attempts
        stats.successful_connections = self.successful_connections
        
        if self.total_connection_attempts > 0:
            stats.connection_success_rate = (
                self.successful_connections / self.total_connection_attempts
            )
        
        if total_submitted > 0:
            stats.global_acceptance_rate = total_accepted / total_submitted
        
        if latencies:
            stats.avg_latency_ms = sum(latencies) / len(latencies)
        
        stats.uptime_seconds = time.time() - self.start_time
        
        return stats
    
    def get_pool_health_status(self, pool_id: Optional[str] = None) -> Dict[str, Any]:
        """Get health status for one or all pools."""
        if pool_id:
            if pool_id in self.pool_health:
                return {pool_id: self.pool_health[pool_id].to_dict()}
            return {}
        
        return {
            pool_id: status.to_dict()
            for pool_id, status in self.pool_health.items()
        }


__all__ = [
    "PoolHealth",
    "MiningStrategy",
    "PoolHealthStatus",
    "MiningStat",
    "ProductionMiningOrchestrator",
]
