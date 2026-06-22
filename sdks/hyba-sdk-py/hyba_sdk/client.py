"""
HYBA SDK Client
Main client for interacting with HYBA QaaS/CIaaS API
"""

from typing import Optional, Dict, Any, List
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from hyba_sdk.exceptions import (
    HybaApiError,
    AuthenticationError,
    QuotaExceededError,
    ServiceNotFoundError,
    ValidationError,
    RateLimitError,
)
from hyba_sdk.connector import ConnectorConfig


class QuantumIntelligenceNamespace:
    """First-class Quantum Intelligence API namespace.

    Exposes evidence-sealed QIaaS operations under ``/api/qiaas``. Enterprise
    controls, quota enforcement, trace propagation, and claim boundaries remain
    enforced by the platform for every call.
    """

    def __init__(self, client: "HybaClient") -> None:
        self._client = client

    def query(self, query: str, context: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        payload = {"query": query, "query_type": "explain", "context": context or {}, **kwargs}
        return self._client._request("POST", "/api/qiaas/query", json=payload)

    def optimize(self, context: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        payload = {"query": "optimize", "query_type": "optimize", "context": context, **kwargs}
        return self._client._request("POST", "/api/qiaas/query", json=payload)

    def heal(self, context: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        payload = {"query": "heal", "query_type": "heal", "context": context, **kwargs}
        return self._client._request("POST", "/api/qiaas/query", json=payload)

    def metrics(self) -> Dict[str, Any]:
        return self._client._request("GET", "/api/qiaas/metrics")

    def health(self) -> Dict[str, Any]:
        return self._client._request("GET", "/api/qiaas/health")


class QuantumFinanceNamespace:
    """Enterprise-controlled Quantum Finance Intelligence helpers."""

    def __init__(self, client: "HybaClient") -> None:
        self._client = client

    def portfolio_qaoa(self, portfolio: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        payload = {
            "query": "quantum-finance portfolio_qaoa",
            "query_type": "optimize",
            "context": {"capability_family": "quantum-finance", "portfolio": portfolio, **kwargs},
        }
        return self._client._request("POST", "/api/qiaas/query", json=payload)


class HybaClient:
    """
    Main client for HYBA QaaS/CIaaS platform
    
    Example:
        >>> client = HybaClient(api_key="hyba_live_...")
        >>> service = client.provision_service(name="my-optimizer")
        >>> result = service.execute(workload="explain", context="test")
    """
    
    DEFAULT_BASE_URL = "https://api.hyba.ai"
    DEFAULT_TIMEOUT = 30  # seconds
    
    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: int = 3,
    ):
        """
        Initialize HYBA client
        
        Args:
            api_key: HYBA API key (starts with hyba_live_...)
            base_url: API base URL (default: https://api.hyba.ai)
            timeout: Request timeout in seconds (default: 30)
            max_retries: Maximum number of retries for failed requests (default: 3)
        """
        self.api_key = api_key
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        
        # Configure session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default headers
        self.session.headers.update({
            "X-API-Key": api_key,
            "Content-Type": "application/json",
            "User-Agent": f"hyba-sdk-py/1.0.0",
        })
        self.quantum_intelligence = QuantumIntelligenceNamespace(self)
        self.quantum_finance = QuantumFinanceNamespace(self)
    
    def _request(
        self,
        method: str,
        path: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make HTTP request to HYBA API
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API path (e.g., /v1/computational-intelligence-services)
            **kwargs: Additional arguments passed to requests
            
        Returns:
            Response JSON as dictionary
            
        Raises:
            HybaApiError: On API error
        """
        url = f"{self.base_url}{path}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs
            )
            
            # Handle error responses
            if response.status_code >= 400:
                self._handle_error_response(response)
            
            # Return JSON response
            return response.json()
        
        except requests.exceptions.Timeout:
            raise HybaApiError(
                f"Request timed out after {self.timeout}s",
                status_code=504
            )
        except requests.exceptions.ConnectionError:
            raise HybaApiError(
                "Failed to connect to HYBA API",
                status_code=503
            )
        except requests.exceptions.RequestException as e:
            raise HybaApiError(f"Request failed: {str(e)}")
    
    def _handle_error_response(self, response: requests.Response) -> None:
        """Handle error response from API"""
        try:
            error_data = response.json()
            message = error_data.get("detail", error_data.get("message", "Unknown error"))
        except ValueError:
            message = response.text or f"HTTP {response.status_code}"
        
        # Raise specific exception based on status code
        if response.status_code == 401:
            raise AuthenticationError(message, response=error_data)
        elif response.status_code == 404:
            raise ServiceNotFoundError(
                service_id="unknown",
                message=message,
                response=error_data
            )
        elif response.status_code == 422:
            raise ValidationError(
                message,
                validation_errors=error_data.get("errors"),
                response=error_data
            )
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            if "quota" in message.lower():
                raise QuotaExceededError(
                    message,
                    quota_info=error_data.get("quota"),
                    response=error_data
                )
            else:
                raise RateLimitError(
                    message,
                    retry_after=int(retry_after) if retry_after else None,
                    response=error_data
                )
        else:
            raise HybaApiError(
                message,
                status_code=response.status_code,
                response=error_data
            )
    
    # ===== SERVICE MANAGEMENT =====
    
    def provision_service(
        self,
        name: str,
        service_tier: str = "production",
        tenancy: str = "single-tenant",
        code_distance: int = 7,
        logical_compute_units: int = 32,
        physical_error_rate: float = 1e-3,
        max_workloads_per_minute: int = 60,
        max_context_bytes: int = 64000,
        data_residency: str = "us",
        allowed_workloads: Optional[List[str]] = None,
        connector: Optional[ConnectorConfig] = None,
        **kwargs
    ):
        # Import here to avoid circular dependency
        from hyba_sdk.service import ComputationalIntelligenceService
        """
        Provision a new CIaaS service
        
        Args:
            name: Service name (3-80 chars, alphanumeric + ._-)
            service_tier: Service tier (developer, production, sovereign)
            tenancy: Tenancy mode (single-tenant, dedicated-control-plane, sovereign-isolated)
            code_distance: Code distance for fault tolerance (3-31)
            logical_compute_units: Number of logical compute units (1-512)
            physical_error_rate: Physical error rate (0.0-0.0109)
            max_workloads_per_minute: Rate limit (1-10000)
            max_context_bytes: Max context size in bytes (1024-2000000)
            data_residency: Data residency region (2-32 chars)
            allowed_workloads: List of allowed workload types
            connector: Optional connector configuration
            
        Returns:
            ComputationalIntelligenceService instance
            
        Example:
            >>> service = client.provision_service(
            ...     name="my-optimizer",
            ...     service_tier="production",
            ...     connector=ConnectorConfig(type="sql_snowflake", ...)
            ... )
        """
        if allowed_workloads is None:
            allowed_workloads = [
                "explain",
                "orchestrate",
                "counterfactual",
                "governance_audit",
                "substrate_health",
            ]
        
        payload = {
            "name": name,
            "service_tier": service_tier,
            "tenancy": tenancy,
            "code_distance": code_distance,
            "logical_compute_units": logical_compute_units,
            "physical_error_rate": physical_error_rate,
            "max_workloads_per_minute": max_workloads_per_minute,
            "max_context_bytes": max_context_bytes,
            "data_residency": data_residency,
            "allowed_workloads": allowed_workloads,
            **kwargs
        }
        
        if connector:
            payload["connector"] = connector.to_dict()
        
        response = self._request("POST", "/api/v1/computational-intelligence-services", json=payload)
        
        # Import here to avoid circular dependency
        from hyba_sdk.service import ComputationalIntelligenceService
        # Extract service_id to avoid duplicate keyword argument
        service_id = response.pop("service_id")
        return ComputationalIntelligenceService(
            client=self,
            service_id=service_id,
            **response
        )
    
    def list_services(self) -> List["ComputationalIntelligenceService"]:
        """
        List all services for the authenticated customer
        
        Returns:
            List of ComputationalIntelligenceService instances
        """
        response = self._request("GET", "/api/v1/computational-intelligence-services")
        
        # Import here to avoid circular dependency
        from hyba_sdk.service import ComputationalIntelligenceService
        return [
            ComputationalIntelligenceService(client=self, **svc)
            for svc in response
        ]
    
    def get_service(self, service_id: str) -> "ComputationalIntelligenceService":
        """
        Get service by ID
        
        Args:
            service_id: Service ID
            
        Returns:
            ComputationalIntelligenceService instance
            
        Raises:
            ServiceNotFoundError: If service doesn't exist
        """
        response = self._request("GET", f"/api/v1/computational-intelligence-services/{service_id}")
        
        # Import here to avoid circular dependency
        from hyba_sdk.service import ComputationalIntelligenceService
        return ComputationalIntelligenceService(client=self, **response)
    
    # ===== HEALTH & STATUS =====
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check API health status
        
        Returns:
            Health status dictionary
        """
        return self._request("GET", "/api/health")
    
    def get_substrate_status(self) -> Dict[str, Any]:
        """
        Get substrate status
        
        Returns:
            Substrate status dictionary
        """
        return self._request("GET", "/api/substrate")
    
    # ===== CONTEXT MANAGERS =====
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
    
    def close(self):
        """Close HTTP session"""
        if self.session:
            self.session.close()
    
    def __repr__(self) -> str:
        return f"HybaClient(base_url={self.base_url!r})"