"""
Example integration of DistributedLockManager into HYBA system components.

This module demonstrates best practices for using the distributed lock manager
across key HYBA subsystems for state coordination and synchronization.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from distributed_lock_manager import (
    DistributedLockManager,
    LockAcquisitionError,
    LockReleaseError,
)

logger = logging.getLogger(__name__)


@dataclass
class StateFileUpdate:
    """Represents a state file update operation."""

    timestamp: float
    update_data: Dict[str, Any]
    pod_id: str
    operation: str  # "update", "merge", "replace"


class StateFileManager:
    """
    Manages reflexive state file locking and synchronization.

    Ensures only one pod updates the state file at a time, preventing
    corruption and race conditions.
    """

    def __init__(
        self,
        lock_manager: DistributedLockManager,
        state_file_path: Path,
        lock_ttl: int = 30,
    ):
        """
        Initialize state file manager.

        Args:
            lock_manager: DistributedLockManager instance
            state_file_path: Path to state file
            lock_ttl: Lock time-to-live in seconds
        """
        self.lock_manager = lock_manager
        self.state_file_path = state_file_path
        self.lock_ttl = lock_ttl
        self.pod_id = self._get_pod_id()

    def _get_pod_id(self) -> str:
        """Get pod identifier from environment or hostname."""
        import os
        import socket

        return os.getenv("HYBA_POD_ID", socket.gethostname())

    async def read_state(self) -> Dict[str, Any]:
        """
        Read current state from file.

        This operation doesn't require a lock as reads are idempotent.

        Returns:
            dict: Current state
        """
        try:
            if self.state_file_path.exists():
                with open(self.state_file_path, "r") as f:
                    return json.load(f)
        except Exception as exc:
            logger.error(
                "Failed to read state file",
                exc_info=True,
                extra={"path": str(self.state_file_path), "error": str(exc)},
            )

        return {}

    async def write_state(
        self,
        state: Dict[str, Any],
        operation: str = "replace",
    ) -> bool:
        """
        Write state to file with distributed lock.

        Acquires lock, updates state atomically, and releases lock.
        Ensures no race conditions across pod replicas.

        Args:
            state: State dictionary to write
            operation: Operation type ("replace", "merge", "update")

        Returns:
            bool: True if write was successful

        Raises:
            LockAcquisitionError: If lock cannot be acquired
            Exception: If file write fails
        """
        try:
            async with self.lock_manager.with_lock(
                "state_file_lock",
                ttl=self.lock_ttl,
            ) as token:
                # Read current state
                current_state = await self.read_state()

                # Apply operation
                if operation == "merge":
                    current_state.update(state)
                elif operation == "update":
                    for key, value in state.items():
                        if key in current_state:
                            if isinstance(current_state[key], dict):
                                current_state[key].update(value)
                            else:
                                current_state[key] = value
                        else:
                            current_state[key] = value
                else:  # replace
                    current_state = state

                # Write atomically
                self.state_file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.state_file_path, "w") as f:
                    json.dump(current_state, f, indent=2, default=str)

                logger.info(
                    "State file updated successfully",
                    extra={
                        "pod_id": self.pod_id,
                        "operation": operation,
                        "lock_holder": token.holder_id[:8],
                    },
                )

                return True

        except LockAcquisitionError as exc:
            logger.error(
                "Failed to acquire lock for state file update",
                extra={
                    "pod_id": self.pod_id,
                    "error": str(exc),
                    "lock_ttl": self.lock_ttl,
                },
            )
            raise

    async def atomic_update(
        self,
        update_fn,
        operation: str = "merge",
    ) -> Any:
        """
        Perform atomic update using provided function.

        Acquires lock, reads state, applies update function, writes result.
        Useful for complex update logic.

        Args:
            update_fn: Async function that takes current state and returns updated state
            operation: Operation type

        Returns:
            Result of update function
        """
        async with self.lock_manager.with_lock(
            "state_file_lock",
            ttl=self.lock_ttl,
        ):
            current_state = await self.read_state()
            result = await update_fn(current_state)
            await self.write_state(result, operation=operation)
            return result


@dataclass
class PoolResponse:
    """A pool response record."""

    pool_id: str
    timestamp: float
    response_data: Dict[str, Any]
    worker_id: str


class PoolResponseHistorySynchronizer:
    """
    Synchronizes pool response history across pod replicas.

    Coordinates writes to shared response history to prevent duplicates
    and maintain consistency.
    """

    def __init__(
        self,
        lock_manager: DistributedLockManager,
        history_file_path: Path,
        lock_ttl: int = 60,
        max_history_size: int = 10000,
    ):
        """
        Initialize pool response history synchronizer.

        Args:
            lock_manager: DistributedLockManager instance
            history_file_path: Path to history file
            lock_ttl: Lock time-to-live in seconds
            max_history_size: Maximum history entries to keep
        """
        self.lock_manager = lock_manager
        self.history_file_path = history_file_path
        self.lock_ttl = lock_ttl
        self.max_history_size = max_history_size

    async def add_responses(
        self,
        responses: List[PoolResponse],
    ) -> bool:
        """
        Add pool responses to synchronized history.

        Acquires lock, loads history, deduplicates, appends new responses,
        and saves. Maintains ordering and size limits.

        Args:
            responses: List of PoolResponse objects to add

        Returns:
            bool: True if addition was successful
        """
        try:
            async with self.lock_manager.with_lock(
                "pool_history_lock",
                ttl=self.lock_ttl,
            ):
                # Load existing history
                history = await self._load_history()

                # Convert to serializable format
                new_entries = [
                    {
                        "pool_id": r.pool_id,
                        "timestamp": r.timestamp,
                        "response_data": r.response_data,
                        "worker_id": r.worker_id,
                    }
                    for r in responses
                ]

                # Deduplicate based on timestamp and pool_id
                existing_keys = {(h["pool_id"], h["timestamp"]) for h in history}
                unique_new = [
                    e
                    for e in new_entries
                    if (e["pool_id"], e["timestamp"]) not in existing_keys
                ]

                # Append new unique entries
                history.extend(unique_new)

                # Trim history if needed
                if len(history) > self.max_history_size:
                    history = history[-self.max_history_size :]

                # Save history
                await self._save_history(history)

                logger.info(
                    "Pool responses added to history",
                    extra={
                        "count": len(unique_new),
                        "total_history": len(history),
                    },
                )

                return True

        except LockAcquisitionError as exc:
            logger.error(
                "Failed to acquire lock for pool history update",
                extra={"error": str(exc)},
            )
            raise

    async def get_responses(
        self,
        pool_id: Optional[str] = None,
        since_timestamp: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve pool responses from history.

        Optionally filter by pool_id and/or timestamp.

        Args:
            pool_id: Optional pool identifier to filter
            since_timestamp: Optional start timestamp

        Returns:
            List of matching response records
        """
        history = await self._load_history()

        if pool_id:
            history = [h for h in history if h["pool_id"] == pool_id]

        if since_timestamp:
            history = [h for h in history if h["timestamp"] >= since_timestamp]

        return history

    async def _load_history(self) -> List[Dict[str, Any]]:
        """Load history from file."""
        try:
            if self.history_file_path.exists():
                with open(self.history_file_path, "r") as f:
                    return json.load(f)
        except Exception as exc:
            logger.warning(
                "Failed to load pool history",
                extra={"error": str(exc)},
            )

        return []

    async def _save_history(self, history: List[Dict[str, Any]]) -> None:
        """Save history to file."""
        self.history_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.history_file_path, "w") as f:
            json.dump(history, f, indent=2, default=str)


@dataclass
class BanditStatistics:
    """Bandit algorithm statistics."""

    arm_counts: Dict[str, int]  # How many times each arm was selected
    arm_rewards: Dict[str, float]  # Total reward for each arm
    total_iterations: int
    last_update: float


class BanditStatisticsCoordinator:
    """
    Coordinates bandit algorithm statistics updates.

    Ensures consistent bandit state across replicas by synchronizing
    updates through distributed locking.
    """

    def __init__(
        self,
        lock_manager: DistributedLockManager,
        stats_file_path: Path,
        lock_ttl: int = 45,
    ):
        """
        Initialize bandit statistics coordinator.

        Args:
            lock_manager: DistributedLockManager instance
            stats_file_path: Path to statistics file
            lock_ttl: Lock time-to-live in seconds
        """
        self.lock_manager = lock_manager
        self.stats_file_path = stats_file_path
        self.lock_ttl = lock_ttl

    async def update_statistics(
        self,
        arm_id: str,
        reward: float,
    ) -> BanditStatistics:
        """
        Update bandit statistics with arm selection and reward.

        Thread-safe update across all replicas.

        Args:
            arm_id: Identifier of selected arm
            reward: Reward value for this iteration

        Returns:
            Updated BanditStatistics

        Raises:
            LockAcquisitionError: If lock cannot be acquired
        """
        async with self.lock_manager.with_lock(
            "bandit_stats_lock",
            ttl=self.lock_ttl,
        ):
            # Load current statistics
            stats = await self._load_statistics()

            # Update arm counts and rewards
            if arm_id not in stats.arm_counts:
                stats.arm_counts[arm_id] = 0
                stats.arm_rewards[arm_id] = 0.0

            stats.arm_counts[arm_id] += 1
            stats.arm_rewards[arm_id] += reward
            stats.total_iterations += 1
            stats.last_update = datetime.now().timestamp()

            # Save updated statistics
            await self._save_statistics(stats)

            logger.debug(
                "Bandit statistics updated",
                extra={
                    "arm_id": arm_id,
                    "reward": reward,
                    "total_iterations": stats.total_iterations,
                },
            )

            return stats

    async def get_statistics(self) -> BanditStatistics:
        """Get current bandit statistics."""
        return await self._load_statistics()

    async def get_arm_expected_value(self, arm_id: str) -> float:
        """Calculate expected value for an arm."""
        stats = await self._load_statistics()

        if arm_id not in stats.arm_counts or stats.arm_counts[arm_id] == 0:
            return 0.0

        return stats.arm_rewards[arm_id] / stats.arm_counts[arm_id]

    async def _load_statistics(self) -> BanditStatistics:
        """Load statistics from file."""
        try:
            if self.stats_file_path.exists():
                with open(self.stats_file_path, "r") as f:
                    data = json.load(f)
                    return BanditStatistics(
                        arm_counts=data.get("arm_counts", {}),
                        arm_rewards=data.get("arm_rewards", {}),
                        total_iterations=data.get("total_iterations", 0),
                        last_update=data.get("last_update", 0.0),
                    )
        except Exception as exc:
            logger.warning(
                "Failed to load bandit statistics",
                extra={"error": str(exc)},
            )

        return BanditStatistics(
            arm_counts={},
            arm_rewards={},
            total_iterations=0,
            last_update=0.0,
        )

    async def _save_statistics(self, stats: BanditStatistics) -> None:
        """Save statistics to file."""
        self.stats_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.stats_file_path, "w") as f:
            json.dump(
                {
                    "arm_counts": stats.arm_counts,
                    "arm_rewards": stats.arm_rewards,
                    "total_iterations": stats.total_iterations,
                    "last_update": stats.last_update,
                },
                f,
                indent=2,
            )


@dataclass
class ApprovalRequest:
    """Operator approval request."""

    request_id: str
    timestamp: float
    description: str
    requester_pod_id: str
    status: str = "pending"  # pending, approved, rejected


class OperatorApprovalQueueManager:
    """
    Manages operator approval request queuing.

    Coordinates approval requests across replicas using distributed locking
    to ensure fair ordering and prevent race conditions.
    """

    def __init__(
        self,
        lock_manager: DistributedLockManager,
        queue_file_path: Path,
        lock_ttl: int = 20,
    ):
        """
        Initialize approval queue manager.

        Args:
            lock_manager: DistributedLockManager instance
            queue_file_path: Path to queue file
            lock_ttl: Lock time-to-live in seconds
        """
        self.lock_manager = lock_manager
        self.queue_file_path = queue_file_path
        self.lock_ttl = lock_ttl

    async def queue_request(self, request: ApprovalRequest) -> bool:
        """
        Queue an approval request.

        Acquires lock, adds request to queue, releases lock.

        Args:
            request: ApprovalRequest to queue

        Returns:
            bool: True if queuing was successful

        Raises:
            LockAcquisitionError: If lock cannot be acquired
        """
        try:
            async with self.lock_manager.with_lock(
                "approval_queue_lock",
                ttl=self.lock_ttl,
            ):
                # Load current queue
                queue = await self._load_queue()

                # Add new request
                queue.append(
                    {
                        "request_id": request.request_id,
                        "timestamp": request.timestamp,
                        "description": request.description,
                        "requester_pod_id": request.requester_pod_id,
                        "status": request.status,
                    }
                )

                # Save updated queue
                await self._save_queue(queue)

                logger.info(
                    "Approval request queued",
                    extra={
                        "request_id": request.request_id,
                        "queue_size": len(queue),
                    },
                )

                return True

        except LockAcquisitionError as exc:
            logger.error(
                "Failed to queue approval request",
                extra={"request_id": request.request_id, "error": str(exc)},
            )
            raise

    async def get_pending_requests(self) -> List[ApprovalRequest]:
        """Get all pending approval requests."""
        queue = await self._load_queue()
        return [
            ApprovalRequest(
                request_id=r["request_id"],
                timestamp=r["timestamp"],
                description=r["description"],
                requester_pod_id=r["requester_pod_id"],
                status=r["status"],
            )
            for r in queue
            if r["status"] == "pending"
        ]

    async def update_request_status(
        self,
        request_id: str,
        status: str,
    ) -> bool:
        """
        Update request status.

        Args:
            request_id: Request identifier
            status: New status ("approved" or "rejected")

        Returns:
            bool: True if update was successful
        """
        async with self.lock_manager.with_lock(
            "approval_queue_lock",
            ttl=self.lock_ttl,
        ):
            queue = await self._load_queue()

            # Find and update request
            for req in queue:
                if req["request_id"] == request_id:
                    req["status"] = status
                    break

            await self._save_queue(queue)

            logger.info(
                "Approval request status updated",
                extra={
                    "request_id": request_id,
                    "status": status,
                },
            )

            return True

    async def _load_queue(self) -> List[Dict[str, Any]]:
        """Load approval queue from file."""
        try:
            if self.queue_file_path.exists():
                with open(self.queue_file_path, "r") as f:
                    return json.load(f)
        except Exception as exc:
            logger.warning(
                "Failed to load approval queue",
                extra={"error": str(exc)},
            )

        return []

    async def _save_queue(self, queue: List[Dict[str, Any]]) -> None:
        """Save approval queue to file."""
        self.queue_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.queue_file_path, "w") as f:
            json.dump(queue, f, indent=2, default=str)


# Example usage in FastAPI app
async def initialize_coordinators(app_state):
    """Initialize all coordinators with distributed lock manager."""
    lock_manager = DistributedLockManager(
        redis_url="redis://redis-service:6379",
        default_ttl=30,
        enable_metrics=True,
    )

    state_manager = StateFileManager(
        lock_manager,
        Path("/data/hyba_state.json"),
    )

    history_sync = PoolResponseHistorySynchronizer(
        lock_manager,
        Path("/data/pool_response_history.json"),
    )

    bandit_coordinator = BanditStatisticsCoordinator(
        lock_manager,
        Path("/data/bandit_stats.json"),
    )

    approval_queue = OperatorApprovalQueueManager(
        lock_manager,
        Path("/data/approval_queue.json"),
    )

    return {
        "lock_manager": lock_manager,
        "state_manager": state_manager,
        "history_sync": history_sync,
        "bandit_coordinator": bandit_coordinator,
        "approval_queue": approval_queue,
    }
