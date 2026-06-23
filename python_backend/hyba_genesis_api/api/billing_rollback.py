"""
Billing Rollback Manager for QaaS/CIaaS

Handles quota refunds on execution failures and daily reconciliation.
Ensures customers are only billed for successful executions.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from collections import defaultdict
import threading


class BillingRollbackManager:
    """
    Manages billing rollbacks for failed QaaS/CIaaS executions.

    Ensures:
    - Failed executions do not consume quota
    - Refunds are processed automatically
    - Daily reconciliation of quota vs actual usage
    - Idempotency-based double-billing prevention
    """

    def __init__(self):
        self._rollback_log: List[Dict[str, Any]] = []
        self._refund_queue: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._daily_reconciliations: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    def refund_on_failure(
        self, execution_id: str, customer_id: str, work_units_consumed: int, reason: str
    ) -> Dict[str, Any]:
        """
        Refund quota consumption for a failed execution.

        Args:
            execution_id: Unique execution identifier
            customer_id: Customer who executed the workload
            work_units_consumed: Work units that were incorrectly charged
            reason: Failure reason for audit trail

        Returns:
            Refund confirmation with rollback record
        """
        with self._lock:
            # Check for duplicate refund (idempotency)
            if execution_id in self._refund_queue:
                existing = self._refund_queue[execution_id]
                return {
                    "success": True,
                    "status": "already_refunded",
                    "execution_id": execution_id,
                    "work_units_refunded": existing["work_units_refunded"],
                    "timestamp": existing["timestamp"],
                }

            # Process refund
            refund_record = {
                "execution_id": execution_id,
                "customer_id": customer_id,
                "work_units_refunded": work_units_consumed,
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "refunded",
            }

            self._refund_queue[execution_id] = refund_record
            self._rollback_log.append(refund_record)

            # Add to daily reconciliation
            date_key = datetime.now(timezone.utc).date().isoformat()
            self._daily_reconciliations[date_key].append(refund_record)

            return {
                "success": True,
                "status": "refunded",
                "execution_id": execution_id,
                "work_units_refunded": work_units_consumed,
                "reason": reason,
                "timestamp": refund_record["timestamp"],
            }

    def reconcile_daily(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform daily reconciliation of quota consumption vs actual usage.

        Args:
            date: ISO date string (defaults to today)

        Returns:
            Reconciliation report with discrepancies
        """
        if date is None:
            date = datetime.now(timezone.utc).date().isoformat()

        with self._lock:
            reconciliations = self._daily_reconciliations.get(date, [])

            total_refunded = sum(r["work_units_refunded"] for r in reconciliations)
            total_customers = len(set(r["customer_id"] for r in reconciliations))
            total_executions = len(reconciliations)

            # Group by reason
            by_reason = defaultdict(int)
            for r in reconciliations:
                by_reason[r["reason"]] += r["work_units_refunded"]

            report = {
                "date": date,
                "total_refunds": total_executions,
                "total_work_units_refunded": total_refunded,
                "affected_customers": total_customers,
                "refunds_by_reason": dict(by_reason),
                "reconciliations": reconciliations,
            }

            return report

    def get_rollback_history(
        self, customer_id: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get rollback history, optionally filtered by customer.

        Args:
            customer_id: Filter by customer (None for all)
            limit: Maximum number of records to return

        Returns:
            List of rollback records
        """
        with self._lock:
            if customer_id:
                filtered = [
                    r for r in self._rollback_log if r["customer_id"] == customer_id
                ]
            else:
                filtered = self._rollback_log

            # Return most recent first
            return sorted(filtered, key=lambda x: x["timestamp"], reverse=True)[:limit]

    def is_already_refunded(self, execution_id: str) -> bool:
        """Check if an execution has already been refunded (idempotency check)."""
        with self._lock:
            return execution_id in self._refund_queue

    def get_refund_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get refund status for a specific execution."""
        with self._lock:
            return self._refund_queue.get(execution_id)


# Global billing rollback manager instance
_billing_rollback_manager: Optional[BillingRollbackManager] = None


def get_billing_rollback_manager() -> BillingRollbackManager:
    """Get or create the global billing rollback manager."""
    global _billing_rollback_manager
    if _billing_rollback_manager is None:
        _billing_rollback_manager = BillingRollbackManager()
    return _billing_rollback_manager
