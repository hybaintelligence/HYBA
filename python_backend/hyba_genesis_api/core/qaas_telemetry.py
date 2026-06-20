"""QaaS-specific telemetry and observability for commercial service.

Exports production-grade metrics for:
- Provision operations (tier, isolation, status)
- Execute operations (operation type, tier, status)
- Rejection/error reasons
- Compute unit consumption
- Idempotency/concurrency conflicts
- Entitlement denial events
- Evidence seal operations
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ProvisionStatus(Enum):
    """Status of provision operation."""

    SUCCESS = "success"
    REJECTED_QUOTA = "rejected_quota"
    REJECTED_ENTITLEMENT = "rejected_entitlement"
    REJECTED_WORKLOAD = "rejected_workload"
    ERROR = "error"


class ExecuteStatus(Enum):
    """Status of execute operation."""

    SUCCESS = "success"
    REJECTED_QUOTA = "rejected_quota"
    REJECTED_VALIDATION = "rejected_validation"
    CONFLICT_CONCURRENT = "conflict_concurrent"
    CONFLICT_IDEMPOTENCY = "conflict_idempotency"
    EXECUTION_FAILED = "execution_failed"
    ERROR = "error"


class RejectionReason(Enum):
    """Reason for workload rejection."""

    WORKLOAD_TOO_LARGE = "workload_too_large"
    QUOTA_INSUFFICIENT = "quota_insufficient"
    CODE_DISTANCE_TOO_HIGH = "code_distance_too_high"
    VALIDATION_FAILED = "validation_failed"
    ENTITLEMENT_DENIED = "entitlement_denied"


@dataclass
class QaaSProvisionMetrics:
    """Metrics for provision operation."""

    timestamp: float = field(default_factory=time.time)
    tier: str = "basic"
    isolation: str = "process"
    status: str = "success"
    duration_ms: float = 0.0
    customer_id: Optional[str] = None
    qpu_id: Optional[str] = None

    def to_prometheus(self) -> str:
        """Format as Prometheus metric."""
        labels = f'tier="{self.tier}",isolation="{self.isolation}",status="{self.status}"'
        return f"hyba_qaas_provision_total{{{labels}}} 1"


@dataclass
class QaaSExecuteMetrics:
    """Metrics for execute operation."""

    timestamp: float = field(default_factory=time.time)
    operation: str = "state_vector_summary"
    tier: str = "basic"
    status: str = "success"
    duration_ms: float = 0.0
    compute_units_billed: float = 0.0
    customer_id: Optional[str] = None
    qpu_id: Optional[str] = None

    def to_prometheus(self) -> str:
        """Format as Prometheus metrics (duration + billing)."""
        metrics = []
        labels = f'operation="{self.operation}",tier="{self.tier}",status="{self.status}"'
        metrics.append(f"hyba_qaas_execute_total{{{labels}}} 1")
        metrics.append(
            f"hyba_qaas_execute_duration_seconds_bucket{{le=\"+Inf\",{labels}}} 1"
        )
        metrics.append(
            f"hyba_qaas_compute_units_total{{operation=\"{self.operation}\",tier=\"{self.tier}\"}} {self.compute_units_billed}"
        )
        return "\n".join(metrics)


@dataclass
class QaaSRejectionMetrics:
    """Metrics for rejected workload."""

    timestamp: float = field(default_factory=time.time)
    reason: str = "workload_too_large"
    tier: str = "basic"
    customer_id: Optional[str] = None
    estimated_units: float = 0.0
    tier_limit: float = 0.0

    def to_prometheus(self) -> str:
        """Format as Prometheus metric."""
        return f'hyba_qaas_rejected_total{{reason="{self.reason}",tier="{self.tier}"}} 1'


@dataclass
class QaaSIdempotencyMetrics:
    """Metrics for idempotency operations."""

    timestamp: float = field(default_factory=time.time)
    operation_type: str = "replay"  # "replay" or "conflict"
    customer_id: Optional[str] = None
    qpu_id: Optional[str] = None
    quota_saved: float = 0.0  # Units saved by idempotency

    def to_prometheus(self) -> str:
        """Format as Prometheus metric."""
        metric_name = (
            "hyba_qaas_idempotency_replay_total"
            if self.operation_type == "replay"
            else "hyba_qaas_idempotency_conflict_total"
        )
        return f"{metric_name} 1"


@dataclass
class QaaSLockConflictMetrics:
    """Metrics for lock/concurrency conflicts."""

    timestamp: float = field(default_factory=time.time)
    qpu_id: str = ""
    conflict_type: str = "concurrent_execute"  # or "timeout"
    customer_id: Optional[str] = None

    def to_prometheus(self) -> str:
        """Format as Prometheus metric."""
        return f'hyba_qaas_lock_conflict_total{{qpu="{self.qpu_id}",type="{self.conflict_type}"}} 1'


@dataclass
class QaaSEntitlementMetrics:
    """Metrics for entitlement denial."""

    timestamp: float = field(default_factory=time.time)
    denial_reason: str = "insufficient_tier"  # or "sovereign_denied", "quota_exhausted"
    requested_tier: str = "exclusive"
    customer_tier: str = "basic"
    customer_id: Optional[str] = None

    def to_prometheus(self) -> str:
        """Format as Prometheus metric."""
        return f'hyba_qaas_entitlement_denial_total{{reason="{self.denial_reason}"}} 1'


@dataclass
class QaaSEvidenceSealMetrics:
    """Metrics for evidence seal operations."""

    timestamp: float = field(default_factory=time.time)
    seal_type: str = "execution"  # or "provision", "deletion"
    result: str = "success"  # or "failure"
    customer_id: Optional[str] = None
    duration_ms: float = 0.0

    def to_prometheus(self) -> str:
        """Format as Prometheus metric."""
        return f'hyba_qaas_evidence_seal_total{{type="{self.seal_type}",result="{self.result}"}} 1'


class QaaSMetricsCollector:
    """Collects and exports QaaS telemetry.

    Usage:
        collector = QaaSMetricsCollector()
        collector.record_provision(tier="basic", isolation="process", status="success")
        collector.emit_prometheus() -> list of metric strings
    """

    def __init__(self):
        """Initialize collector."""
        self.provision_metrics: List[QaaSProvisionMetrics] = []
        self.execute_metrics: List[QaaSExecuteMetrics] = []
        self.rejection_metrics: List[QaaSRejectionMetrics] = []
        self.idempotency_metrics: List[QaaSIdempotencyMetrics] = []
        self.lock_conflict_metrics: List[QaaSLockConflictMetrics] = []
        self.entitlement_metrics: List[QaaSEntitlementMetrics] = []
        self.evidence_seal_metrics: List[QaaSEvidenceSealMetrics] = []

    def record_provision(
        self,
        tier: str,
        isolation: str,
        status: str,
        duration_ms: float = 0.0,
        customer_id: Optional[str] = None,
        qpu_id: Optional[str] = None,
    ) -> None:
        """Record provision operation."""
        metric = QaaSProvisionMetrics(
            tier=tier,
            isolation=isolation,
            status=status,
            duration_ms=duration_ms,
            customer_id=customer_id,
            qpu_id=qpu_id,
        )
        self.provision_metrics.append(metric)

    def record_execute(
        self,
        operation: str,
        tier: str,
        status: str,
        duration_ms: float = 0.0,
        compute_units_billed: float = 0.0,
        customer_id: Optional[str] = None,
        qpu_id: Optional[str] = None,
    ) -> None:
        """Record execute operation."""
        metric = QaaSExecuteMetrics(
            operation=operation,
            tier=tier,
            status=status,
            duration_ms=duration_ms,
            compute_units_billed=compute_units_billed,
            customer_id=customer_id,
            qpu_id=qpu_id,
        )
        self.execute_metrics.append(metric)

    def record_rejection(
        self,
        reason: str,
        tier: str,
        estimated_units: float = 0.0,
        tier_limit: float = 0.0,
        customer_id: Optional[str] = None,
    ) -> None:
        """Record workload rejection."""
        metric = QaaSRejectionMetrics(
            reason=reason,
            tier=tier,
            estimated_units=estimated_units,
            tier_limit=tier_limit,
            customer_id=customer_id,
        )
        self.rejection_metrics.append(metric)

    def record_idempotency(
        self,
        operation_type: str,
        quota_saved: float = 0.0,
        customer_id: Optional[str] = None,
        qpu_id: Optional[str] = None,
    ) -> None:
        """Record idempotency operation (replay or conflict)."""
        metric = QaaSIdempotencyMetrics(
            operation_type=operation_type,
            quota_saved=quota_saved,
            customer_id=customer_id,
            qpu_id=qpu_id,
        )
        self.idempotency_metrics.append(metric)

    def record_lock_conflict(
        self,
        qpu_id: str,
        conflict_type: str = "concurrent_execute",
        customer_id: Optional[str] = None,
    ) -> None:
        """Record lock/concurrency conflict."""
        metric = QaaSLockConflictMetrics(
            qpu_id=qpu_id,
            conflict_type=conflict_type,
            customer_id=customer_id,
        )
        self.lock_conflict_metrics.append(metric)

    def record_entitlement_denial(
        self,
        denial_reason: str,
        requested_tier: str,
        customer_tier: str,
        customer_id: Optional[str] = None,
    ) -> None:
        """Record entitlement denial."""
        metric = QaaSEntitlementMetrics(
            denial_reason=denial_reason,
            requested_tier=requested_tier,
            customer_tier=customer_tier,
            customer_id=customer_id,
        )
        self.entitlement_metrics.append(metric)

    def record_evidence_seal(
        self,
        seal_type: str,
        result: str = "success",
        duration_ms: float = 0.0,
        customer_id: Optional[str] = None,
    ) -> None:
        """Record evidence seal operation."""
        metric = QaaSEvidenceSealMetrics(
            seal_type=seal_type,
            result=result,
            duration_ms=duration_ms,
            customer_id=customer_id,
        )
        self.evidence_seal_metrics.append(metric)

    def emit_prometheus(self) -> List[str]:
        """Emit all metrics in Prometheus format."""
        lines = ["# QaaS Metrics"]

        # Provision metrics
        if self.provision_metrics:
            lines.append("# HELP hyba_qaas_provision_total Provision operations")
            lines.append("# TYPE hyba_qaas_provision_total counter")
            for m in self.provision_metrics:
                lines.append(m.to_prometheus())

        # Execute metrics
        if self.execute_metrics:
            lines.append("# HELP hyba_qaas_execute_total Execute operations")
            lines.append("# TYPE hyba_qaas_execute_total counter")
            for m in self.execute_metrics:
                for line in m.to_prometheus().split("\n"):
                    lines.append(line)

        # Rejection metrics
        if self.rejection_metrics:
            lines.append("# HELP hyba_qaas_rejected_total Rejected workloads")
            lines.append("# TYPE hyba_qaas_rejected_total counter")
            for m in self.rejection_metrics:
                lines.append(m.to_prometheus())

        # Idempotency metrics
        if self.idempotency_metrics:
            lines.append("# HELP hyba_qaas_idempotency_total Idempotency events")
            lines.append("# TYPE hyba_qaas_idempotency_total counter")
            for m in self.idempotency_metrics:
                lines.append(m.to_prometheus())

        # Lock conflict metrics
        if self.lock_conflict_metrics:
            lines.append("# HELP hyba_qaas_lock_conflict_total Lock conflicts")
            lines.append("# TYPE hyba_qaas_lock_conflict_total counter")
            for m in self.lock_conflict_metrics:
                lines.append(m.to_prometheus())

        # Entitlement metrics
        if self.entitlement_metrics:
            lines.append("# HELP hyba_qaas_entitlement_denial_total Entitlement denials")
            lines.append("# TYPE hyba_qaas_entitlement_denial_total counter")
            for m in self.entitlement_metrics:
                lines.append(m.to_prometheus())

        # Evidence seal metrics
        if self.evidence_seal_metrics:
            lines.append("# HELP hyba_qaas_evidence_seal_total Evidence seals")
            lines.append("# TYPE hyba_qaas_evidence_seal_total counter")
            for m in self.evidence_seal_metrics:
                lines.append(m.to_prometheus())

        return lines

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of metrics collected."""
        return {
            "provision_count": len(self.provision_metrics),
            "execute_count": len(self.execute_metrics),
            "rejection_count": len(self.rejection_metrics),
            "idempotency_count": len(self.idempotency_metrics),
            "lock_conflict_count": len(self.lock_conflict_metrics),
            "entitlement_denial_count": len(self.entitlement_metrics),
            "evidence_seal_count": len(self.evidence_seal_metrics),
        }


__all__ = [
    "QaaSMetricsCollector",
    "QaaSProvisionMetrics",
    "QaaSExecuteMetrics",
    "QaaSRejectionMetrics",
    "QaaSIdempotencyMetrics",
    "QaaSLockConflictMetrics",
    "QaaSEntitlementMetrics",
    "QaaSEvidenceSealMetrics",
    "ProvisionStatus",
    "ExecuteStatus",
    "RejectionReason",
]
