"""
Stratum Idempotency Integration - Production Mining Orchestrator Integration

Shows how to integrate IdempotencyTracker into ProductionMiningOrchestrator
to prevent double-spending attacks with atomic, race-condition-free semantics.

This module provides both the integration pattern and a reference implementation
that can be directly used.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

from pythia_mining.stratum_client import StratumClient, ShareResult
from pythia_mining.stratum_idempotency_tracker import (
    IdempotencyTracker,
    StratumSubmissionRecord,
    SubmissionStatus,
)

logger = logging.getLogger(__name__)


class IdempotentStratumSubmissionMixin:
    """
    Mixin for ProductionMiningOrchestrator to add idempotency tracking.
    
    Integration pattern:
    
    1. Initialize in __init__:
        self.idempotency_tracker = IdempotencyTracker(
            redis_client=self.redis_client,  # Reuse existing Redis connection
            ttl_seconds=120,
            enable_metrics=True,
        )
    
    2. Start periodic cleanup task in start():
        asyncio.create_task(self._idempotency_cleanup_loop())
    
    3. Wrap submissions in _submit_to_pool_safe():
        result = await self._submit_with_idempotency_check(
            pool_id, client, job, nonce, extranonce2
        )
    """
    
    async def _submit_with_idempotency_check(
        self,
        pool_id: str,
        client: StratumClient,
        job: Any,
        nonce: int,
        extranonce2: Optional[str] = None,
    ) -> Optional[ShareResult]:
        """
        Submit share to pool with idempotency checking.
        
        Flow:
        1. Check if (pool_id, nonce) already submitted
        2. If duplicate and was accepted: REJECT (DUP_NONCE)
        3. If duplicate and was rejected: ALLOW RETRY
        4. Record new submission
        5. Submit to pool
        6. Mark result
        
        Args:
            pool_id: Target pool identifier
            client: StratumClient for submission
            job: Mining job object
            nonce: Share nonce value
            extranonce2: Optional extranonce2 value
        
        Returns:
            ShareResult with acceptance status, or None on error
        """
        try:
            # Step 1: Check for previous submission
            tracker = self.idempotency_tracker  # Assumes initialized
            previous_record = await tracker.check_duplicate(pool_id, nonce)
            
            if previous_record:
                tracker.record_duplicate_attempt(
                    pool_id, nonce, previous_record.status
                )
                
                # Step 2-3: Decision based on previous status
                if previous_record.status == SubmissionStatus.ACCEPTED.value:
                    # Share was already accepted, reject duplicate
                    logger.warning(
                        "Duplicate nonce rejection",
                        extra={
                            "pool_id": pool_id,
                            "nonce": nonce,
                            "previous_submission_id": previous_record.submission_id,
                            "previous_status": SubmissionStatus.ACCEPTED.value,
                        },
                    )
                    return ShareResult(
                        accepted=False,
                        error_code=22,  # Stratum duplicate share code
                        error_message="DUP_NONCE - Share already submitted and accepted",
                        job_id=getattr(job, "job_id", ""),
                        nonce=nonce,
                    )
                elif previous_record.status == SubmissionStatus.REJECTED.value:
                    # Previous was rejected, allow retry
                    logger.info(
                        "Duplicate nonce retry allowed",
                        extra={
                            "pool_id": pool_id,
                            "nonce": nonce,
                            "previous_submission_id": previous_record.submission_id,
                            "rejection_reason": previous_record.reason,
                        },
                    )
                    # Continue with submission below
            
            # Step 4: Record this submission attempt
            record = await tracker.record_submission(pool_id, nonce)
            
            # Step 5: Submit to pool
            try:
                result = await client.submit_validated_share(job, nonce, extranonce2)
                
                # Step 6: Mark result
                await tracker.mark_result(
                    record.submission_id,
                    pool_id,
                    nonce,
                    accepted=result.accepted,
                    reason=result.error_message,
                )
                
                logger.debug(
                    "Share submitted with idempotency tracking",
                    extra={
                        "submission_id": record.submission_id,
                        "pool_id": pool_id,
                        "nonce": nonce,
                        "accepted": result.accepted,
                    },
                )
                
                return result
            
            except Exception as e:
                # Mark as rejected with error reason
                await tracker.mark_result(
                    record.submission_id,
                    pool_id,
                    nonce,
                    accepted=False,
                    reason=f"submission_error: {str(e)}",
                )
                raise
        
        except Exception as e:
            logger.error(
                "Idempotency check failed during submission",
                extra={
                    "pool_id": pool_id,
                    "nonce": nonce,
                    "error": str(e),
                },
            )
            # Fall back to direct submission on tracker failure
            try:
                result = await client.submit_validated_share(job, nonce, extranonce2)
                return result
            except Exception as fallback_error:
                logger.error(
                    "Fallback submission also failed",
                    extra={
                        "pool_id": pool_id,
                        "nonce": nonce,
                        "error": str(fallback_error),
                    },
                )
                return None
    
    async def _idempotency_cleanup_loop(self) -> None:
        """
        Periodic cleanup task to remove expired in-memory entries.
        
        Should be started as:
            asyncio.create_task(self._idempotency_cleanup_loop())
        
        Runs cleanup every 60 seconds.
        """
        cleanup_interval = 60  # seconds
        
        while True:
            try:
                await asyncio.sleep(cleanup_interval)
                
                tracker = self.idempotency_tracker
                cleaned = await tracker.cleanup_expired()
                
                if cleaned > 0:
                    logger.info(
                        "Idempotency tracker cleanup",
                        extra={"entries_cleaned": cleaned},
                    )
            
            except Exception as e:
                logger.error(
                    "Idempotency cleanup failed",
                    extra={"error": str(e)},
                )
    
    async def get_idempotency_metrics(self) -> Dict[str, Any]:
        """
        Get idempotency tracker metrics for monitoring.
        
        Returns:
            Dict with tracking metrics including:
            - duplicate_attempts: Submissions with duplicate nonce
            - retry_successes: Failed shares that were retried successfully
            - false_positives: Race condition indicators
            - submissions_recorded: Total tracked submissions
            - redis_available: Whether Redis is connected
        """
        tracker = self.idempotency_tracker
        return await tracker.get_metrics()


class StratumIdempotencyDashboard:
    """
    Monitoring dashboard for idempotency tracking.
    
    Provides insights into double-spending prevention effectiveness and
    can detect both legitimate retries and potential attack patterns.
    """
    
    def __init__(self, tracker: IdempotencyTracker):
        """Initialize dashboard with tracker reference."""
        self._tracker = tracker
    
    async def get_health_status(self) -> Dict[str, Any]:
        """
        Get current health of idempotency tracking.
        
        Returns:
            Health report with status indicators
        """
        metrics = await self._tracker.get_metrics()
        
        total_submissions = metrics.get("submissions_recorded", 0)
        accepted = metrics.get("accepted_submissions", 0)
        rejected = metrics.get("rejected_submissions", 0)
        duplicates = metrics.get("duplicate_attempts", 0)
        retries = metrics.get("retry_successes", 0)
        false_positives = metrics.get("false_positives", 0)
        
        # Calculate acceptance rate
        acceptance_rate = (
            accepted / total_submissions * 100
            if total_submissions > 0
            else 0.0
        )
        
        # Calculate duplicate rate
        duplicate_rate = (
            duplicates / total_submissions * 100
            if total_submissions > 0
            else 0.0
        )
        
        # Assess health
        health_status = "healthy"
        health_warnings = []
        
        if false_positives > 0:
            health_warnings.append(
                f"Detected {false_positives} race conditions (submission ID mismatches)"
            )
            health_status = "degraded"
        
        if duplicate_rate > 5.0:
            health_warnings.append(
                f"High duplicate rate: {duplicate_rate:.2f}% (may indicate mining issues)"
            )
            health_status = "degraded"
        
        if duplicate_rate > 10.0:
            health_status = "unhealthy"
        
        return {
            "status": health_status,
            "total_submissions": total_submissions,
            "accepted_shares": accepted,
            "rejected_shares": rejected,
            "duplicate_attempts": duplicates,
            "retry_successes": retries,
            "false_positives": false_positives,
            "acceptance_rate": acceptance_rate,
            "duplicate_rate": duplicate_rate,
            "redis_available": metrics.get("redis_available", False),
            "warnings": health_warnings,
        }
    
    async def get_duplicate_analysis(self) -> Dict[str, Any]:
        """
        Analyze duplicate patterns to detect anomalies.
        
        Returns:
            Analysis of duplicate activity
        """
        metrics = await self._tracker.get_metrics()
        
        duplicates = metrics.get("duplicate_attempts", 0)
        retries = metrics.get("retry_successes", 0)
        
        # Calculate ratios
        retry_success_rate = (
            retries / duplicates * 100 if duplicates > 0 else 0.0
        )
        
        return {
            "duplicate_attempts": duplicates,
            "successful_retries": retries,
            "failed_retries": duplicates - retries,
            "retry_success_rate": retry_success_rate,
            "indicates_attack": false_positives > duplicates * 0.1,  # Heuristic
        }


# Integration example for ProductionMiningOrchestrator
INTEGRATION_EXAMPLE = """
# In ProductionMiningOrchestrator.__init__():

from pythia_mining.stratum_idempotency_tracker import IdempotencyTracker

# Get Redis client (should already exist in orchestrator)
redis_client = self.redis_client  

# Initialize tracker
self.idempotency_tracker = IdempotencyTracker(
    redis_client=redis_client,
    ttl_seconds=120,
    enable_metrics=True,
)

# In ProductionMiningOrchestrator.start():

# Start periodic cleanup
self._cleanup_task = asyncio.create_task(
    self._idempotency_cleanup_loop()
)

# In ProductionMiningOrchestrator._submit_to_pool_safe():

async def _submit_to_pool_safe(
    self,
    pool_id: str,
    client: StratumClient,
    job: Any,
    nonce: int,
    extranonce2: Optional[str] = None,
) -> Optional[ShareResult]:
    \"\"\"Safely submit share to a pool with idempotency checking.\"\"\"
    try:
        # Use idempotent submission
        result = await self._submit_with_idempotency_check(
            pool_id, client, job, nonce, extranonce2
        )
        
        if result:
            self._record_share_result(pool_id, result)
        
        return result
    
    except Exception as e:
        self.logger.warning("Share submission to %s failed: %s", pool_id, e)
        self._record_pool_failure(pool_id, str(e))
        return None

# Add the mixin methods to ProductionMiningOrchestrator:
# - _submit_with_idempotency_check()
# - _idempotency_cleanup_loop()
# - get_idempotency_metrics()
"""

__all__ = [
    "IdempotentStratumSubmissionMixin",
    "StratumIdempotencyDashboard",
    "INTEGRATION_EXAMPLE",
]
