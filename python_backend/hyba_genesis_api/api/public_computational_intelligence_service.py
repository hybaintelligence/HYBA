"""Public customer-facing CIaaS API for computational intelligence services.

Secured by X-API-Key authentication with tenant isolation, lifecycle metering,
workload metering, and quota enforcement.
"""

from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from hyba_genesis_api.api.computational_intelligence_service import (
    IntelligenceWorkloadRequest,
    ServiceResponse,
    _CommercialIntelligenceComputer,
    registry as admin_ciaas_registry,
)
from hyba_genesis_api.api.customer_access import (
    CustomerInfo,
    UsageMetrics,
    customer_registry,
    require_api_key,
)

router = APIRouter(prefix="/api/v1/computational-intelligence-services", tags=["public-ciaas"])

ServiceState = Literal["provisioned", "running", "stopped"]
ServiceTier = Literal["developer", "production", "sovereign"]
TenancyMode = Literal["single-tenant", "dedicated-control-plane", "sovereign-isolated"]
WorkloadKind = Literal[
    "explain",
    "orchestrate",
    "counterfactual",
    "governance_audit",
    "substrate_health",
]


class ProvisionComputationalIntelligenceRequest(BaseModel):
    """Customer request to provision a CIaaS virtual computer."""

    name: str = Field(min_length=3, max_length=80, pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_.-]*$")
    service_tier: ServiceTier = "production"
    tenancy: TenancyMode = "single-tenant"
    code_distance: int = Field(default=7, ge=3, le=31)
    logical_compute_units: int = Field(default=32, ge=1, le=512)
    physical_error_rate: float = Field(default=1e-3, gt=0.0, lt=0.0109)
    max_workloads_per_minute: int = Field(default=60, ge=1, le=10_000)
    max_context_bytes: int = Field(default=64_000, ge=1_024, le=2_000_000)
    data_residency: str = Field(default="us", min_length=2, max_length=32)
    allowed_workloads: list[WorkloadKind] = Field(
        default_factory=lambda: [
            "explain",
            "orchestrate",
            "counterfactual",
            "governance_audit",
            "substrate_health",
        ],
        min_length=1,
        max_length=5,
    )


class PublicServiceResponse(BaseModel):
    service_id: str
    name: str
    state: ServiceState
    service_tier: ServiceTier
    tenancy: TenancyMode
    owner: str
    created_at: str
    updated_at: str
    commercial_policy: Dict[str, Any]
    fault_tolerance: Dict[str, Any]
    substrate: Dict[str, Any]
    evidence_seal: str
    claim_boundary: str
    usage: UsageMetrics


class _CustomerCIAASRegistry:
    """Customer-scoped CIaaS registry with tenant isolation."""

    def __init__(self) -> None:
        self._customer_services: Dict[str, Dict[str, _CommercialIntelligenceComputer]] = {}

    def provision(
        self,
        customer: CustomerInfo,
        request: ProvisionComputationalIntelligenceRequest,
    ) -> PublicServiceResponse:
        customer_id = customer.customer_id
        if customer_id not in self._customer_services:
            self._customer_services[customer_id] = {}

        # Create service using admin registry infrastructure
        from hyba_genesis_api.api.computational_intelligence_service import (
            ProvisionComputationalIntelligenceRequest as AdminRequest,
        )

        admin_request = AdminRequest(
            name=request.name,
            service_tier=request.service_tier,
            tenancy=request.tenancy,
            code_distance=request.code_distance,
            logical_compute_units=request.logical_compute_units,
            physical_error_rate=request.physical_error_rate,
            max_workloads_per_minute=request.max_workloads_per_minute,
            max_context_bytes=request.max_context_bytes,
            admin_privileged=False,
            data_residency=request.data_residency,
            allowed_workloads=request.allowed_workloads,
        )

        response = admin_ciaas_registry.provision(admin_request, owner=customer_id)
        service_id = response.service_id

        # Track ownership
        self._customer_services[customer_id][service_id] = admin_ciaas_registry.get(service_id)

        # Add usage metrics
        usage = customer_registry.get_usage_metrics(customer)
        return PublicServiceResponse(
            service_id=response.service_id,
            name=response.name,
            state=response.state,
            service_tier=response.service_tier,
            tenancy=response.tenancy,
            owner=response.owner,
            created_at=response.created_at,
            updated_at=response.updated_at,
            commercial_policy=response.commercial_policy,
            fault_tolerance=response.fault_tolerance,
            substrate=response.substrate,
            evidence_seal=response.evidence_seal,
            claim_boundary=response.claim_boundary,
            usage=usage,
        )

    def get(self, customer: CustomerInfo, service_id: str) -> _CommercialIntelligenceComputer:
        customer_id = customer.customer_id
        if customer_id not in self._customer_services:
            raise HTTPException(status_code=404, detail="Service not found")
        if service_id not in self._customer_services[customer_id]:
            raise HTTPException(status_code=404, detail="Service not found")
        return self._customer_services[customer_id][service_id]

    def list(self, customer: CustomerInfo) -> list[PublicServiceResponse]:
        customer_id = customer.customer_id
        if customer_id not in self._customer_services:
            return []

        usage = customer_registry.get_usage_metrics(customer)
        return [
            PublicServiceResponse(
                service_id=svc.response().service_id,
                name=svc.response().name,
                state=svc.response().state,
                service_tier=svc.response().service_tier,
                tenancy=svc.response().tenancy,
                owner=svc.response().owner,
                created_at=svc.response().created_at,
                updated_at=svc.response().updated_at,
                commercial_policy=svc.response().commercial_policy,
                fault_tolerance=svc.response().fault_tolerance,
                substrate=svc.response().substrate,
                evidence_seal=svc.response().evidence_seal,
                claim_boundary=svc.response().claim_boundary,
                usage=usage,
            )
            for svc in self._customer_services[customer_id].values()
        ]

    def start(self, customer: CustomerInfo, service_id: str) -> PublicServiceResponse:
        computer = self.get(customer, service_id)
        response = admin_ciaas_registry.start(service_id)
        usage = customer_registry.get_usage_metrics(customer)
        return PublicServiceResponse(
            service_id=response.service_id,
            name=response.name,
            state=response.state,
            service_tier=response.service_tier,
            tenancy=response.tenancy,
            owner=response.owner,
            created_at=response.created_at,
            updated_at=response.updated_at,
            commercial_policy=response.commercial_policy,
            fault_tolerance=response.fault_tolerance,
            substrate=response.substrate,
            evidence_seal=response.evidence_seal,
            claim_boundary=response.claim_boundary,
            usage=usage,
        )

    def stop(self, customer: CustomerInfo, service_id: str) -> PublicServiceResponse:
        computer = self.get(customer, service_id)
        response = admin_ciaas_registry.stop(service_id)
        usage = customer_registry.get_usage_metrics(customer)
        return PublicServiceResponse(
            service_id=response.service_id,
            name=response.name,
            state=response.state,
            service_tier=response.service_tier,
            tenancy=response.tenancy,
            owner=response.owner,
            created_at=response.created_at,
            updated_at=response.updated_at,
            commercial_policy=response.commercial_policy,
            fault_tolerance=response.fault_tolerance,
            substrate=response.substrate,
            evidence_seal=response.evidence_seal,
            claim_boundary=response.claim_boundary,
            usage=usage,
        )

    def execute(
        self,
        customer: CustomerInfo,
        service_id: str,
        request: IntelligenceWorkloadRequest,
    ) -> Dict[str, Any]:
        computer = self.get(customer, service_id)

        # Check quota and meter accepted work before execution.
        context_size = len(str(request.context))
        usage_meter = customer_registry.meter(customer, product="ciaas.execute", units=context_size)

        result = admin_ciaas_registry.execute(service_id, request)
        usage = customer_registry.get_usage_metrics(customer)
        result["usage"] = usage.model_dump()
        result["usage_meter"] = usage_meter
        return result


customer_registry_ciaas = _CustomerCIAASRegistry()


@router.post("", response_model=PublicServiceResponse, status_code=status.HTTP_201_CREATED)
async def provision_service(
    request: ProvisionComputationalIntelligenceRequest,
    customer: CustomerInfo = Depends(require_api_key),
):
    """Customer endpoint to provision a CIaaS service."""
    return customer_registry_ciaas.provision(customer, request)


@router.get("", response_model=list[PublicServiceResponse])
async def list_services(customer: CustomerInfo = Depends(require_api_key)):
    """Customer endpoint to list their CIaaS services."""
    return customer_registry_ciaas.list(customer)


@router.get("/{service_id}", response_model=PublicServiceResponse)
async def get_service(
    service_id: str,
    customer: CustomerInfo = Depends(require_api_key),
):
    """Customer endpoint to get a specific CIaaS service."""
    computer = customer_registry_ciaas.get(customer, service_id)
    usage = customer_registry.get_usage_metrics(customer)
    response = computer.response()
    return PublicServiceResponse(
        service_id=response.service_id,
        name=response.name,
        state=response.state,
        service_tier=response.service_tier,
        tenancy=response.tenancy,
        owner=response.owner,
        created_at=response.created_at,
        updated_at=response.updated_at,
        commercial_policy=response.commercial_policy,
        fault_tolerance=response.fault_tolerance,
        substrate=response.substrate,
        evidence_seal=response.evidence_seal,
        claim_boundary=response.claim_boundary,
        usage=usage,
    )


@router.post("/{service_id}/start", response_model=PublicServiceResponse)
async def start_service(
    service_id: str,
    customer: CustomerInfo = Depends(require_api_key),
):
    """Customer endpoint to start a CIaaS service."""
    return customer_registry_ciaas.start(customer, service_id)


@router.post("/{service_id}/stop", response_model=PublicServiceResponse)
async def stop_service(
    service_id: str,
    customer: CustomerInfo = Depends(require_api_key),
):
    """Customer endpoint to stop a CIaaS service."""
    return customer_registry_ciaas.stop(customer, service_id)


@router.post("/{service_id}/execute", response_model=Dict[str, Any])
async def execute_intelligence_workload(
    service_id: str,
    request: IntelligenceWorkloadRequest,
    customer: CustomerInfo = Depends(require_api_key),
):
    """Customer endpoint to execute an intelligence workload."""
    return customer_registry_ciaas.execute(customer, service_id, request)
