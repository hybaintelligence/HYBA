"""
Quota Manager for QaaS/CIaaS

Manages customer quota consumption, refunds, and enforcement.
Integrates with BillingRollbackManager for automatic refunds on failures.
"""

import threading
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class QuotaManager:
    """
    Manages customer quotas for QaaS/CIaaS services.
    
    Provides:
    - Quota consumption tracking
    - Automatic refunds on execution failures
    - Customer-specific quota pools
    - Thread-safe operations
    - Usage analytics
    """
    
    def __init__(self):
        self._quotas: Dict[str, int] = {}
        self._consumed: Dict[str, int] = defaultdict(int)
        self._lock = threading.RLock()
        self._usage_history: Dict[str, list] = defaultdict(list)
    
    def provision_quota(self, customer_id: str, units: int) -> Dict[str, Any]:
        """Provision quota for a customer."""
        with self._lock:
            current = self._quotas.get(customer_id, 0)
            self._quotas[customer_id] = current + units
            
            logger.info(
                f"Provisioned {units} units for customer {customer_id}",
                extra={"customer_id": customer_id, "units": units, "total": current + units}
            )
            
            return {
                "success": True,
                "customer_id": customer_id,
                "units_provisioned": units,
                "total_quota": current + units,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def consume_quota(self, customer_id: str, units: int, execution_id: str) -> bool:
        """Attempt to consume quota for an execution."""
        with self._lock:
            available = self.get_available(customer_id)
            
            if available < units:
                logger.warning(
                    f"Insufficient quota for customer {customer_id}",
                    extra={"customer_id": customer_id, "requested": units, "available": available}
                )
                return False
            
            self._consumed[customer_id] += units
            self._usage_history[customer_id].append({
                "execution_id": execution_id,
                "units": units,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": "consumption"
            })
            
            return True
    
    def refund_quota(self, customer_id: str, units: int, execution_id: str, reason: str) -> Dict[str, Any]:
        """Refund quota for a failed execution."""
        with self._lock:
            if customer_id not in self._consumed:
                return {"success": False, "error": "no_consumption_recorded"}
            
            self._consumed[customer_id] = max(0, self._consumed[customer_id] - units)
            self._usage_history[customer_id].append({
                "execution_id": execution_id,
                "units": units,
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": "refund"
            })
            
            logger.info(f"Refunded {units} units for {customer_id}: {reason}")
            
            return {
                "success": True,
                "customer_id": customer_id,
                "units_refunded": units,
                "reason": reason,
                "available_after_refund": self.get_available(customer_id),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def get_available(self, customer_id: str) -> int:
        """Get available quota for a customer."""
        with self._lock:
            total = self._quotas.get(customer_id, 0)
            consumed = self._consumed.get(customer_id, 0)
            return max(0, total - consumed)
    
    def get_status(self, customer_id: str) -> Dict[str, Any]:
        """Get comprehensive quota status for a customer."""
        with self._lock:
            total = self._quotas.get(customer_id, 0)
            consumed = self._consumed.get(customer_id, 0)
            available = max(0, total - consumed)
            
            history = self._usage_history.get(customer_id, [])
            consumptions = [h for h in history if h["type"] == "consumption"]
            refunds = [h for h in history if h["type"] == "refund"]
            
            return {
                "customer_id": customer_id,
                "total_quota": total,
                "consumed": consumed,
                "available": available,
                "utilization_percent": round((consumed / total * 100) if total > 0 else 0, 2),
                "statistics": {
                    "total_executions": len(consumptions),
                    "total_refunds": len(refunds),
                    "refund_rate": round((len(refunds) / len(consumptions) * 100) if consumptions else 0, 2)
                }
            }
    
    def get_usage_history(self, customer_id: str, limit: int = 100) -> list:
        """Get usage history for a customer."""
        with self._lock:
            history = self._usage_history.get(customer_id, [])
            return sorted(history, key=lambda x: x["timestamp"], reverse=True)[:limit]


# Global singleton
_quota_manager: Optional[QuotaManager] = None

def get_quota_manager() -> QuotaManager:
    global _quota_manager
    if _quota_manager is None:
        _quota_manager = QuotaManager()
    return _quota_manager
