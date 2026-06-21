"""
Execution Coordinator for QaaS/CIaaS

Orchestrates execution lifecycle with integrated:
- Quota consumption and enforcement
- Automatic billing rollback on failures
- Autonomous controller integration
- End-to-end error handling
"""

import time
import uuid
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from python_backend.hyba_genesis_api.api.quota_manager import get_quota_manager
from python_backend.hyba_genesis_api.api.billing_rollback import get_billing_rollback_manager
from python_backend.pythia_mining.autonomous_qaas_controller import AutonomousQaaSController

logger = logging.getLogger(__name__)


class ExecutionCoordinator:
    """
    Coordinates QaaS/CIaaS execution lifecycle with integrated billing and quota management.
    
    Execution flow:
    1. Check quota availability
    2. Consume quota
    3. Execute workload
    4. On success: commit billing
    5. On failure: automatic refund + rollback
    """
    
    def __init__(self, autonomous_controller: Optional[AutonomousQaaSController] = None,
                 quota_manager: Optional[Any] = None,
                 billing_manager: Optional[Any] = None):
        self.quota_mgr = quota_manager or get_quota_manager()
        self.billing_mgr = billing_manager or get_billing_rollback_manager()
        self.autonomous = autonomous_controller
    
    def execute_with_protection(
        self,
        customer_id: str,
        work_units: int,
        execution_fn: callable,
        execution_id: Optional[str] = None,
        **execution_kwargs
    ) -> Dict[str, Any]:
        """
        Execute workload with full quota/billing protection.
        
        Args:
            customer_id: Customer identifier
            work_units: Work units to charge
            execution_fn: Callable that performs the actual work
            execution_id: Optional execution ID (generated if not provided)
            **execution_kwargs: Arguments passed to execution_fn
            
        Returns:
            Execution result with billing/quota metadata
        """
        execution_id = execution_id or f"exec_{uuid.uuid4().hex[:16]}"
        start_time = time.time()
        
        # Step 1: Check quota availability
        available = self.quota_mgr.get_available(customer_id)
        if available < work_units:
            logger.warning(
                f"Insufficient quota for {customer_id}: need {work_units}, have {available}",
                extra={
                    "customer_id": customer_id,
                    "execution_id": execution_id,
                    "requested": work_units,
                    "available": available
                }
            )
            return {
                "success": False,
                "error": "insufficient_quota",
                "execution_id": execution_id,
                "customer_id": customer_id,
                "requested_units": work_units,
                "available_units": available
            }
        
        # Step 2: Consume quota (optimistic)
        consumed = self.quota_mgr.consume_quota(customer_id, work_units, execution_id)
        if not consumed:
            return {
                "success": False,
                "error": "quota_consumption_failed",
                "execution_id": execution_id
            }
        
        # Step 3: Execute workload with protection
        try:
            result = execution_fn(**execution_kwargs)
            
            execution_time = time.time() - start_time
            
            # Step 4: Record successful execution
            if self.autonomous:
                self.autonomous.record_execution(
                    execution_time_ms=execution_time * 1000,
                    logical_error_rate=result.get("error_rate", 0.001),
                    correction_success=True
                )
            
            logger.info(
                f"Execution succeeded for {customer_id}",
                extra={
                    "customer_id": customer_id,
                    "execution_id": execution_id,
                    "work_units": work_units,
                    "execution_time_ms": round(execution_time * 1000, 2)
                }
            )
            
            return {
                "success": True,
                "execution_id": execution_id,
                "customer_id": customer_id,
                "result": result,
                "work_units_charged": work_units,
                "execution_time_ms": round(execution_time * 1000, 2),
                "quota_remaining": self.quota_mgr.get_available(customer_id)
            }
        
        except Exception as e:
            # Step 5: Automatic rollback on failure
            execution_time = time.time() - start_time
            failure_reason = f"{type(e).__name__}: {str(e)}"
            
            # Trigger billing rollback
            refund_result = self.billing_mgr.refund_on_failure(
                execution_id=execution_id,
                customer_id=customer_id,
                work_units_consumed=work_units,
                reason=failure_reason
            )
            
            # Restore quota
            quota_refund = self.quota_mgr.refund_quota(
                customer_id=customer_id,
                units=work_units,
                execution_id=execution_id,
                reason=failure_reason
            )
            
            # Record failed execution for autonomous learning
            if self.autonomous:
                self.autonomous.record_execution(
                    execution_time_ms=execution_time * 1000,
                    logical_error_rate=0.01,  # High error rate on failure
                    correction_success=False
                )
            
            logger.error(
                f"Execution failed for {customer_id}: {failure_reason}",
                extra={
                    "customer_id": customer_id,
                    "execution_id": execution_id,
                    "work_units": work_units,
                    "refund_status": refund_result.get("status"),
                    "error": str(e)
                }
            )
            
            return {
                "success": False,
                "error": failure_reason,
                "execution_id": execution_id,
                "customer_id": customer_id,
                "work_units_refunded": work_units,
                "refund_status": refund_result.get("status"),
                "quota_restored": quota_refund.get("success"),
                "quota_remaining": self.quota_mgr.get_available(customer_id),
                "execution_time_ms": round(execution_time * 1000, 2)
            }


def create_execution_coordinator(
    autonomous_controller: Optional[AutonomousQaaSController] = None
) -> ExecutionCoordinator:
    """Factory function to create execution coordinator."""
    return ExecutionCoordinator(autonomous_controller=autonomous_controller)
