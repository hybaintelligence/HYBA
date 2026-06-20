"""Public customer-facing QaaS API for fault-tolerant quantum computers.

Secured by X-API-Key authentication with tenant ownership checks,
per-workload usage meters, and quota enforcement.
"""

from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from hyba_genesis_api.api.customer_access import (
    CustomerInfo,
    UsageMetrics,
    customer_registry,
    require_api_key,
)
from hyba_genesis_api.api.quantum_as_a_service import (
    QuantumComputerRegistry,
    QuantumWorkloadRequest,
    _VirtualFaultTolerantQuantumComputer,
    registry as admin_registry,
)

router = APIRouter(prefix="/api/v1/fault-tolerant-computers", tags=["public-qaas"])

ComputerState = Literal["provisioned", "running", "stopped"]
QaaSTier = Literal["developer", "production", "sovereign"]
IsolationMode = Literal["single-tenant", "dedicated-control-plane", "sovereign-isolated"]
QuantumOperation = Literal[
    "surface_code_cycle",
    "phi_resonance_analysis",
    "state_vector_summary",
    "substrate_orchestration",
    "governance_audit",
]


class ProvisionFaultTolerantComputerRequest(BaseModel):
    """Customer request to provision a virtual fault-tolerant quantum computer."""

    name: str = Field(min_length=3, max_length=80, pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_.-]*$")
    tier: QaaSTier = "production"
    isolation: IsolationMode = "dedicated-control-plane"
    code_distance: int = Field(default=7, ge=3, le=31)
    logical_qubits: int = Field(default=32, ge=1, le=512)
    physical_error_rate: float = Field(default=1e-3, gt=0.0, lt=0.0109)
    phi_resonance_target: float = Field(default=0.9565, gt=0.0, le=1.0)
    max_circuit_depth: int = Field(default=1_024, ge=1, le=1_000_000)
    max_shots: int = Field(default=1_024, ge=1, le=1_000_000)
    data_residency: str = Field(default="us", min_length=2, max_length=32)
    allowed_operations: list[QuantumOperation] = Field(
        default_factory=lambda: [
            "surface_code_cycle",
            "phi_resonance_analysis",
            "state_vector_summary",
            "substrate_orchestration",
            "governance_audit",
        ],
        min_length=1,
        max_length=5,
    )

    @classmethod
    def code_distance_must_be_odd(cls, value: int) -> int:
        if value % 2 == 0:
            raise ValueError("code_distance must be odd for surface-code fault tolerance")
        return value

    @classmethod
    def allowed_operations_must_be_unique(
        cls,
        value: list[QuantumOperation],
    ) -> list[QuantumOperation]:
        if len(set(value)) != len(value):
            raise ValueError("allowed_operations must not contain duplicates")
        return value


class FaultTolerantComputerResponse(BaseModel):
    computer_id: str
    name: str
    state: ComputerState
    tier: QaaSTier
    isolation: IsolationMode
    owner: str
    created_at: str
    updated_at: str
    quantum_parameters: Dict[str, Any]
    fault_tolerance: Dict[str, Any]
    substrate: Dict[str, Any]
    evidence_seal: str
    claim_boundary: str
    usage: UsageMetrics


class _CustomerQuantumComputerRegistry:
    """Customer-scoped quantum computer registry with tenant isolation."""

    def __init__(self) -> None:
        self._customer_computers: Dict[str, Dict[str, _VirtualFaultTolerantQuantumComputer]] = {}

    def provision(
        self,
        customer: CustomerInfo,
        request: ProvisionFaultTolerantComputerRequest,
    ) -> FaultTolerantComputerResponse:
        customer_id = customer.customer_id
        if customer_id not in self._customer_computers:
            self._customer_computers[customer_id] = {}

        # Create computer using admin registry infrastructure
        from hyba_genesis_api.api.quantum_as_a_service import ProvisionFaultTolerantComputerRequest as AdminRequest

        admin_request = AdminRequest(
            name=request.name,
            tier=request.tier,
            isolation=request.isolation,
            code_distance=request.code_distance,
            logical_qubits=request.logical_qubits,
            physical_error_rate=request.physical_error_rate,
            phi_resonance_target=request.phi_resonance_target,
            max_circuit_depth=request.max_circuit_depth,
            max_shots=request.max_shots,
            admin_privileged=False,
            data_residency=request.data_residency,
            allowed_operations=request.allowed_operations,
        )

        response = admin_registry.provision(admin_request, owner=customer_id)
        computer_id = response.computer_id

        # Track ownership
        self._customer_computers[customer_id][computer_id] = admin_registry.get(computer_id)

        # Add usage metrics
        usage = customer_registry.get_usage_metrics(customer)
        return FaultTolerantComputerResponse(
            computer_id=response.computer_id,
            name=response.name,
            state=response.state,
            tier=response.tier,
            isolation=response.isolation,
            owner=response.owner,
            created_at=response.created_at,
            updated_at=response.updated_at,
            quantum_parameters=response.quantum_parameters,
            fault_tolerance=response.fault_tolerance,
            substrate=response.substrate,
            evidence_seal=response.evidence_seal,
            claim_boundary=response.claim_boundary,
            usage=usage,
        )

    def get(self, customer: CustomerInfo, computer_id: str) -> _VirtualFaultTolerantQuantumComputer:
        customer_id = customer.customer_id
        if customer_id not in self._customer_computers:
            raise HTTPException(status_code=404, detail="Computer not found")
        if computer_id not in self._customer_computers[customer_id]:
            raise HTTPException(status_code=404, detail="Computer not found")
        return self._customer_computers[customer_id][computer_id]

    def list(self, customer: CustomerInfo) -> list[FaultTolerantComputerResponse]:
        customer_id = customer.customer_id
        if customer_id not in self._customer_computers:
            return []

        usage = customer_registry.get_usage_metrics(customer)
        return [
            FaultTolerantComputerResponse(
                computer_id=comp.response().computer_id,
                name=comp.response().name,
                state=comp.response().state,
                tier=comp.response().tier,
                isolation=comp.response().isolation,
                owner=comp.response().owner,
                created_at=comp.response().created_at,
                updated_at=comp.response().updated_at,
                quantum_parameters=comp.response().quantum_parameters,
                fault_tolerance=comp.response().fault_tolerance,
                substrate=comp.response().substrate,
                evidence_seal=comp.response().evidence_seal,
                claim_boundary=comp.response().claim_boundary,
                usage=usage,
            )
            for comp in self._customer_computers[customer_id].values()
        ]

    def start(self, customer: CustomerInfo, computer_id: str) -> FaultTolerantComputerResponse:
        computer = self.get(customer, computer_id)
        response = admin_registry.start(computer_id)
        usage = customer_registry.get_usage_metrics(customer)
        return FaultTolerantComputerResponse(
            computer_id=response.computer_id,
            name=response.name,
            state=response.state,
            tier=response.tier,
            isolation=response.isolation,
            owner=response.owner,
            created_at=response.created_at,
            updated_at=response.updated_at,
            quantum_parameters=response.quantum_parameters,
            fault_tolerance=response.fault_tolerance,
            substrate=response.substrate,
            evidence_seal=response.evidence_seal,
            claim_boundary=response.claim_boundary,
            usage=usage,
        )

    def stop(self, customer: CustomerInfo, computer_id: str) -> FaultTolerantComputerResponse:
        computer = self.get(customer, computer_id)
        response = admin_registry.stop(computer_id)
        usage = customer_registry.get_usage_metrics(customer)
        return FaultTolerantComputerResponse(
            computer_id=response.computer_id,
            name=response.name,
            state=response.state,
            tier=response.tier,
            isolation=response.isolation,
            owner=response.owner,
            created_at=response.created_at,
            updated_at=response.updated_at,
            quantum_parameters=response.quantum_parameters,
            fault_tolerance=response.fault_tolerance,
            substrate=response.substrate,
            evidence_seal=response.evidence_seal,
            claim_boundary=response.claim_boundary,
            usage=usage,
        )

    def execute(
        self,
        customer: CustomerInfo,
        computer_id: str,
        request: QuantumWorkloadRequest,
    ) -> Dict[str, Any]:
        computer = self.get(customer, computer_id)

        # Check and increment usage before execution
        compute_cost = request.circuit_depth * len(request.logical_qubits or [0])
        customer_registry.check_and_increment_usage(customer, request_cost=1, compute_cost=compute_cost)

        result = admin_registry.execute(computer_id, request)
        usage = customer_registry.get_usage_metrics(customer)
        result["usage"] = usage.model_dump()
        return result


customer_registry_qaas = _CustomerQuantumComputerRegistry()


@router.post("", response_model=FaultTolerantComputerResponse, status_code=status.HTTP_201_CREATED)
async def provision_computer(
    request: ProvisionFaultTolerantComputerRequest,
    customer: CustomerInfo = Depends(require_api_key),
):
    """Customer endpoint to provision a fault-tolerant quantum computer."""
    return customer_registry_qaas.provision(customer, request)


@router.get("", response_model=list[FaultTolerantComputerResponse])
async def list_computers(customer: CustomerInfo = Depends(require_api_key)):
    """Customer endpoint to list their fault-tolerant quantum computers."""
    return customer_registry_qaas.list(customer)


@router.get("/{computer_id}", response_model=FaultTolerantComputerResponse)
async def get_computer(
    computer_id: str,
    customer: CustomerInfo = Depends(require_api_key),
):
    """Customer endpoint to get a specific fault-tolerant quantum computer."""
    computer = customer_registry_qaas.get(customer, computer_id)
    usage = customer_registry.get_usage_metrics(customer)
    response = computer.response()
    return FaultTolerantComputerResponse(
        computer_id=response.computer_id,
        name=response.name,
        state=response.state,
        tier=response.tier,
        isolation=response.isolation,
        owner=response.owner,
        created_at=response.created_at,
        updated_at=response.updated_at,
        quantum_parameters=response.quantum_parameters,
        fault_tolerance=response.fault_tolerance,
        substrate=response.substrate,
        evidence_seal=response.evidence_seal,
        claim_boundary=response.claim_boundary,
        usage=usage,
    )


@router.post("/{computer_id}/start", response_model=FaultTolerantComputerResponse)
async def start_computer(
    computer_id: str,
    customer: CustomerInfo = Depends(require_api_key),
):
    """Customer endpoint to start a fault-tolerant quantum computer."""
    return customer_registry_qaas.start(customer, computer_id)


@router.post("/{computer_id}/stop", response_model=FaultTolerantComputerResponse)
async def stop_computer(
    computer_id: str,
    customer: CustomerInfo = Depends(require_api_key),
):
    """Customer endpoint to stop a fault-tolerant quantum computer."""
    return customer_registry_qaas.stop(customer, computer_id)


@router.post("/{computer_id}/execute", response_model=Dict[str, Any])
async def execute_quantum_workload(
    computer_id: str,
    request: QuantumWorkloadRequest,
    customer: CustomerInfo = Depends(require_api_key),
):
    """Customer endpoint to execute a quantum workload."""
    return customer_registry_qaas.execute(customer, computer_id, request)
