"""
HYBA SDK Service
Computational Intelligence Service wrapper
"""

from typing import Dict, Any, Optional, List
import time

from hyba_sdk.client import HybaClient
from hyba_sdk.exceptions import (
    HybaApiError,
    ServiceStateError,
    ServiceNotFoundError,
    ValidationError,
)


class ComputationalIntelligenceService:
    """
    Represents a provisioned CIaaS service
    
    Example:
        >>> service = client.provision_service(name="my-optimizer")
        >>> service.start()
        >>> result = service.execute(workload="explain", context="test")
        >>> service.stop()
    """
    
    def __init__(
        self,
        client: HybaClient,
        service_id: str,
        name: str,
        state: str,
        service_tier: str,
        tenancy: str,
        owner: str,
        created_at: str,
        updated_at: str,
        commercial_policy: Dict[str, Any],
        fault_tolerance: Dict[str, Any],
        substrate: Dict[str, Any],
        evidence_seal: str,
        claim_boundary: str,
        usage: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        Initialize service (usually called by HybaClient)
        
        Args:
            client: HybaClient instance
            service_id: Unique service ID
            name: Service name
            state: Current state (provisioned, running, stopped)
            service_tier: Service tier (developer, production, sovereign)
            tenancy: Tenancy mode
            owner: Owner customer ID
            created_at: Creation timestamp
            updated_at: Last update timestamp
            commercial_policy: Commercial policy configuration
            fault_tolerance: Fault tolerance settings
            substrate: Substrate configuration
            evidence_seal: Evidence seal hash
            claim_boundary: Claim boundary string
            usage: Usage metrics
        """
        self._client = client
        self.service_id = service_id
        self.name = name
        self.state = state
        self.service_tier = service_tier
        self.tenancy = tenancy
        self.owner = owner
        self.created_at = created_at
        self.updated_at = updated_at
        self.commercial_policy = commercial_policy
        self.fault_tolerance = fault_tolerance
        self.substrate = substrate
        self.evidence_seal = evidence_seal
        self.claim_boundary = claim_boundary
        self.usage = usage or {}
    
    def start(self) -> "ComputationalIntelligenceService":
        """
        Start the service
        
        Returns:
            Updated service instance
            
        Raises:
            ServiceStateError: If service cannot be started
        """
        if self.state not in ["provisioned", "stopped"]:
            raise ServiceStateError(
                service_id=self.service_id,
                current_state=self.state,
                operation="start"
            )
        
        response = self._client._request(
            "POST",
            f"/api/v1/computational-intelligence-services/{self.service_id}/start"
        )
        
        return self._update_from_response(response)
    
    def stop(self) -> "ComputationalIntelligenceService":
        """
        Stop the service
        
        Returns:
            Updated service instance
            
        Raises:
            ServiceStateError: If service cannot be stopped
        """
        if self.state != "running":
            raise ServiceStateError(
                service_id=self.service_id,
                current_state=self.state,
                operation="stop"
            )
        
        response = self._client._request(
            "POST",
            f"/api/v1/computational-intelligence-services/{self.service_id}/stop"
        )
        
        return self._update_from_response(response)
    
    def execute(
        self,
        workload: str,
        context: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute an intelligence workload
        
        Args:
            workload: Workload type (explain, orchestrate, counterfactual, etc.)
            context: Workload context/input
            **kwargs: Additional workload parameters
            
        Returns:
            Workload result dictionary
            
        Raises:
            ServiceStateError: If service is not running
            ValidationError: If workload parameters are invalid
            QuotaExceededError: If quota is exceeded
            
        Example:
            >>> result = service.execute(
            ...     workload="explain",
            ...     context="Portfolio optimization strategy"
            ... )
            >>> print(result["result"])
        """
        if self.state != "running":
            raise ServiceStateError(
                service_id=self.service_id,
                current_state=self.state,
                operation="execute"
            )
        
        payload = {
            "workload_type": workload,
            "context": context,
            **kwargs
        }
        
        response = self._client._request(
            "POST",
            f"/api/v1/computational-intelligence-services/{self.service_id}/execute",
            json=payload
        )
        
        return response
    
    def explain(self, context: str, **kwargs) -> Dict[str, Any]:
        """
        Explain a context with shared substrate telemetry
        
        Args:
            context: Context to explain
            **kwargs: Additional parameters
            
        Returns:
            Explanation result
        """
        return self.execute(workload="explain", context=context, **kwargs)
    
    def orchestrate(self, context: str, **kwargs) -> Dict[str, Any]:
        """
        Route a context through the unified substrate contract orchestrator
        
        Args:
            context: Context to orchestrate
            **kwargs: Additional parameters
            
        Returns:
            Orchestration result
        """
        return self.execute(workload="orchestrate", context=context, **kwargs)
    
    def counterfactual(self, context: str, **kwargs) -> Dict[str, Any]:
        """
        Generate counterfactual analysis
        
        Args:
            context: Context for counterfactual analysis
            **kwargs: Additional parameters
            
        Returns:
            Counterfactual result
        """
        return self.execute(workload="counterfactual", context=context, **kwargs)
    
    def governance_audit(self, context: str, **kwargs) -> Dict[str, Any]:
        """
        Perform governance audit
        
        Args:
            context: Context to audit
            **kwargs: Additional parameters
            
        Returns:
            Audit result
        """
        return self.execute(workload="governance_audit", context=context, **kwargs)
    
    def substrate_health(self, **kwargs) -> Dict[str, Any]:
        """
        Check substrate health
        
        Args:
            **kwargs: Additional parameters
            
        Returns:
            Health status
        """
        return self.execute(workload="substrate_health", context="", **kwargs)
    
    def refresh(self) -> "ComputationalIntelligenceService":
        """
        Refresh service metadata from API
        
        Returns:
            Updated service instance
        """
        response = self._client._request(
            "GET",
            f"/api/v1/computational-intelligence-services/{self.service_id}"
        )
        
        return self._update_from_response(response)
    
    def delete(self) -> bool:
        """
        Delete the service
        
        Returns:
            True if deleted successfully
            
        Raises:
            HybaApiError: If deletion fails
        """
        response = self._client._request(
            "DELETE",
            f"/api/v1/computational-intelligence-services/{self.service_id}"
        )
        
        return response.get("deleted", False)
    
    def _update_from_response(self, response: Dict[str, Any]) -> "ComputationalIntelligenceService":
        """Update service attributes from API response"""
        self.state = response.get("state", self.state)
        self.updated_at = response.get("updated_at", self.updated_at)
        self.usage = response.get("usage", self.usage)
        
        # Update other attributes if present
        for attr in [
            "name", "service_tier", "tenancy", "commercial_policy",
            "fault_tolerance", "substrate", "evidence_seal", "claim_boundary"
        ]:
            if attr in response:
                setattr(self, attr, response[attr])
        
        return self
    
    def __repr__(self) -> str:
        return (
            f"ComputationalIntelligenceService("
            f"id={self.service_id!r}, "
            f"name={self.name!r}, "
            f"state={self.state!r})"
        )
    
    def __str__(self) -> str:
        return f"{self.name} ({self.service_id}) - {self.state}"