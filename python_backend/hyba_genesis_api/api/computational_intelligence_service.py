"""Commercial Computational Intelligence as a Service (CIaaS) control plane.

This router provisions admin-governed fault-tolerant virtual intelligence
computers for general computational-intelligence workloads.  It is deliberately
not coupled to mining: requests are routed through the existing HYBA
intelligence fabric and wrapped with fault-tolerance posture, tenancy,
commercial policy, audit seals, and workload metering.
"""

from __future__ import annotations

import hashlib
import threading
import uuid
from datetime import UTC, datetime
from typing import Any, Dict, Literal, Mapping, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from hyba_genesis_api.api.admin import require_admin
from hyba_genesis_api.api.customer_access import CustomerPrincipal, customer_access, require_customer_api_key
from hyba_genesis_api.auth.jwt_handler import TokenPayload
from hyba_genesis_api.core.intelligence_fabric import SubstrateOrchestrator, explain
from hyba_genesis_api.core.substrate import get_substrate_state, initialize_substrate
from pythia_mining.fault_tolerant_quantum_core import FaultTolerantQuantumCore

router = APIRouter(
    prefix="/api/admin/computational-intelligence-services",
    tags=["computational-intelligence-service-admin"],
)
public_router = APIRouter(
    prefix="/api/v1/computational-intelligence-services",
    tags=["computational-intelligence-service"],
)

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
    """Admin request to provision a commercial CIaaS virtual computer."""

    name: str = Field(min_length=3, max_length=80, pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_.-]*$")
    service_tier: ServiceTier = "production"
    tenancy: TenancyMode = "single-tenant"
    code_distance: int = Field(default=7, ge=3, le=31)
    logical_compute_units: int = Field(default=32, ge=1, le=512)
    physical_error_rate: float = Field(default=1e-3, gt=0.0, lt=0.0109)
    max_workloads_per_minute: int = Field(default=60, ge=1, le=10_000)
    max_context_bytes: int = Field(default=64_000, ge=1_024, le=2_000_000)
    admin_privileged: bool = Field(default=False)
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

    @field_validator("code_distance")
    @classmethod
    def code_distance_must_be_odd(cls, value: int) -> int:
        if value % 2 == 0:
            raise ValueError("code_distance must be odd for surface-code fault tolerance")
        return value

    @field_validator("allowed_workloads")
    @classmethod
    def workloads_must_be_unique(cls, value: list[WorkloadKind]) -> list[WorkloadKind]:
        if len(set(value)) != len(value):
            raise ValueError("allowed_workloads must not contain duplicates")
        return value


class IntelligenceWorkloadRequest(BaseModel):
    workload_type: WorkloadKind = "orchestrate"
    context: Dict[str, Any] = Field(default_factory=dict)
    substrates: Optional[list[Literal["penrose_or", "iit_4", "deutsch"]]] = Field(
        default=None,
        max_length=3,
    )
    idempotency_key: Optional[str] = Field(default=None, max_length=128)


class ServiceResponse(BaseModel):
    service_id: str
    name: str
    state: ServiceState
    service_tier: ServiceTier
    tenancy: TenancyMode
    admin_privileged: bool
    owner: str
    created_at: str
    updated_at: str
    commercial_policy: Dict[str, Any]
    fault_tolerance: Dict[str, Any]
    substrate: Dict[str, Any]
    evidence_seal: str


class _CommercialIntelligenceComputer:
    def __init__(
        self,
        *,
        service_id: str,
        request: ProvisionComputationalIntelligenceRequest,
        owner: str,
    ) -> None:
        now = datetime.now(UTC).isoformat()
        self.service_id = service_id
        self.name = request.name
        self.owner = owner
        self.state: ServiceState = "provisioned"
        self.created_at = now
        self.updated_at = now
        self.policy = request.model_dump()
        self.core = FaultTolerantQuantumCore(
            code_distance=request.code_distance,
            physical_error_rate=request.physical_error_rate,
        )
        self.logical_compute_units = request.logical_compute_units
        self._workload_count = 0
        self._idempotency_cache: dict[str, Dict[str, Any]] = {}
        for _ in range(request.logical_compute_units):
            self.core.initialize_logical_qubit("0")

    def touch(self) -> None:
        self.updated_at = datetime.now(UTC).isoformat()

    def commercial_policy(self) -> Dict[str, Any]:
        return {
            "service_tier": self.policy["service_tier"],
            "max_workloads_per_minute": self.policy["max_workloads_per_minute"],
            "max_context_bytes": self.policy["max_context_bytes"],
            "data_residency": self.policy["data_residency"],
            "allowed_workloads": list(self.policy["allowed_workloads"]),
            "workloads_executed": self._workload_count,
        }

    def fault_tolerance(self) -> Dict[str, Any]:
        stats = self.core.get_error_statistics()
        return {
            "code_distance": self.core.d,
            "logical_compute_units": self.logical_compute_units,
            "physical_error_rate": stats["physical_error_rate"],
            "logical_error_rate": stats["logical_error_rate"],
            "error_threshold": stats["error_threshold"],
            "phi_reference_threshold": stats["phi_reference_threshold"],
            "fault_tolerant": stats["fault_tolerant"],
            "syndrome_rounds": stats["syndrome_rounds"],
            "correction_attempts": stats["correction_attempts"],
            "correction_successes": stats["correction_successes"],
            "logical_failures": stats["logical_failures"],
            "last_decoder_defects": stats["last_decoder_defects"],
            "last_decoder_weight": stats["last_decoder_weight"],
            "suppression_factor": stats.get("suppression_factor", 1.0),
            "logical_error_rate_basis": stats["logical_error_rate_basis"],
            "evidence_basis": "syndrome_decoder_with_modeled_logical_error_rate",
            "claim_boundary": (
                "Syndrome corrections are derived from the local decoder model for "
                "the CIaaS control plane; logical error rate is an analytic "
                "surface-code projection, not measured physical hardware fault "
                "tolerance."
            ),
        }

    def response(self) -> ServiceResponse:
        substrate = get_substrate_state()
        seal_payload = {
            "service_id": self.service_id,
            "name": self.name,
            "owner": self.owner,
            "state": self.state,
            "policy": self.commercial_policy(),
            "fault_tolerance": self.fault_tolerance(),
            "substrate_ready": substrate.get("ready"),
        }
        seal = hashlib.sha256(repr(sorted(seal_payload.items())).encode()).hexdigest()
        return ServiceResponse(
            service_id=self.service_id,
            name=self.name,
            state=self.state,
            service_tier=self.policy["service_tier"],
            tenancy=self.policy["tenancy"],
            admin_privileged=self.policy["admin_privileged"],
            owner=self.owner,
            created_at=self.created_at,
            updated_at=self.updated_at,
            commercial_policy=self.commercial_policy(),
            fault_tolerance=self.fault_tolerance(),
            substrate=substrate,
            evidence_seal=seal,
        )

    def _validate_workload(self, request: IntelligenceWorkloadRequest) -> None:
        if request.workload_type not in self.policy["allowed_workloads"]:
            raise HTTPException(status_code=403, detail="workload type is not allowed by service policy")
        context_bytes = len(repr(request.context).encode("utf-8"))
        if context_bytes > self.policy["max_context_bytes"]:
            raise HTTPException(status_code=413, detail="workload context exceeds service policy")

    def execute(self, request: IntelligenceWorkloadRequest) -> Dict[str, Any]:
        self._validate_workload(request)
        if request.idempotency_key and request.idempotency_key in self._idempotency_cache:
            return self._idempotency_cache[request.idempotency_key]

        # Run syndrome rounds across a bounded quorum of logical compute units to
        # expose measurable fault-tolerance posture for this intelligence call.
        quorum = min(3, len(self.core.logical_qubits))
        for qubit_idx in range(quorum):
            self.core.measure_syndromes(qubit_idx)
            self.core.measure_syndromes(qubit_idx)
            self.core.decode_and_correct(qubit_idx)

        if request.workload_type == "explain":
            result = explain(request.context, request.substrates)
        elif request.workload_type == "orchestrate":
            result = SubstrateOrchestrator().evaluate(request.context)
        elif request.workload_type == "counterfactual":
            explanation = explain(request.context, request.substrates)
            result = {
                "context_digest": explanation["context_digest"],
                "counterfactuals": explanation["counterfactuals"],
                "governance": explanation["governance"],
                "selected_substrate": explanation["selected_substrate"],
            }
        elif request.workload_type == "governance_audit":
            result = {
                "context_digest": hashlib.sha256(repr(sorted(request.context.items())).encode()).hexdigest(),
                "commercial_policy": self.commercial_policy(),
                "fault_tolerance": self.fault_tolerance(),
                "claim_boundary": "CIaaS deterministic intelligence workload; no mining dependency",
            }
        else:
            result = {"substrate": get_substrate_state()}

        self._workload_count += 1
        self.touch()
        envelope = {
            "service_id": self.service_id,
            "workload_type": request.workload_type,
            "state": self.state,
            "result": result,
            "fault_tolerance": self.fault_tolerance(),
            "commercial_policy": self.commercial_policy(),
            "executed_at": self.updated_at,
            "claim_boundary": "Computational Intelligence as a Service; general-purpose HYBA substrate; no mining-specific execution path.",
        }
        if request.idempotency_key:
            self._idempotency_cache[request.idempotency_key] = envelope
        return envelope


class ComputationalIntelligenceServiceRegistry:
    """Thread-safe in-process registry for commercial CIaaS computers."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._services: dict[str, _CommercialIntelligenceComputer] = {}

    def provision(
        self,
        request: ProvisionComputationalIntelligenceRequest,
        owner: str,
    ) -> ServiceResponse:
        with self._lock:
            service_id = f"cias-{uuid.uuid4().hex[:12]}"
            service = _CommercialIntelligenceComputer(
                service_id=service_id,
                request=request,
                owner=owner,
            )
            self._services[service_id] = service
            return service.response()

    def get(self, service_id: str) -> _CommercialIntelligenceComputer:
        try:
            return self._services[service_id]
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="computational intelligence service not found") from exc

    def list(self, owner: str | None = None) -> list[ServiceResponse]:
        with self._lock:
            return [
                service.response()
                for service in self._services.values()
                if owner is None or service.owner == owner
            ]

    def start(self, service_id: str) -> ServiceResponse:
        with self._lock:
            service = self.get(service_id)
            if service.state != "running":
                initialize_substrate()
                service.state = "running"
                service.touch()
            return service.response()

    def stop(self, service_id: str) -> ServiceResponse:
        with self._lock:
            service = self.get(service_id)
            service.state = "stopped"
            service.touch()
            return service.response()

    def execute(self, service_id: str, request: IntelligenceWorkloadRequest) -> Dict[str, Any]:
        with self._lock:
            service = self.get(service_id)
            if service.state != "running":
                raise HTTPException(status_code=409, detail="service must be running before workloads execute")
            return service.execute(request)

    def assert_owner(self, service_id: str, owner: str) -> _CommercialIntelligenceComputer:
        service = self.get(service_id)
        if service.owner != owner:
            raise HTTPException(status_code=404, detail="computational intelligence service not found")
        return service


registry = ComputationalIntelligenceServiceRegistry()


@router.post("", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def provision_service(
    request: ProvisionComputationalIntelligenceRequest,
    payload: TokenPayload = Depends(require_admin),
):
    return registry.provision(request, owner=payload.username)


@router.get("", response_model=list[ServiceResponse])
async def list_services(payload: TokenPayload = Depends(require_admin)):
    return registry.list()


@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service(service_id: str, payload: TokenPayload = Depends(require_admin)):
    return registry.get(service_id).response()


@router.post("/{service_id}/start", response_model=ServiceResponse)
async def start_service(service_id: str, payload: TokenPayload = Depends(require_admin)):
    return registry.start(service_id)


@router.post("/{service_id}/stop", response_model=ServiceResponse)
async def stop_service(service_id: str, payload: TokenPayload = Depends(require_admin)):
    return registry.stop(service_id)


@router.post("/{service_id}/workloads", response_model=Dict[str, Any])
async def execute_workload(
    service_id: str,
    request: IntelligenceWorkloadRequest,
    payload: TokenPayload = Depends(require_admin),
):
    return registry.execute(service_id, request)


def _ciaas_units(request: IntelligenceWorkloadRequest) -> int:
    return max(1, len(repr(request.context).encode("utf-8")) // 1024 + 1)


@public_router.post("", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def customer_provision_service(
    request: ProvisionComputationalIntelligenceRequest,
    principal: CustomerPrincipal = Depends(require_customer_api_key),
):
    customer_access.meter(principal, product="ciaas.provision", units=request.logical_compute_units)
    response = registry.provision(request, owner=principal.customer_id)
    customer_access.set_state(f"ciaas:{response.service_id}", response.model_dump())
    return response


@public_router.get("", response_model=list[ServiceResponse])
async def customer_list_services(
    principal: CustomerPrincipal = Depends(require_customer_api_key),
):
    customer_access.meter(principal, product="ciaas.list", units=1)
    return registry.list(owner=principal.customer_id)


@public_router.post("/{service_id}/start", response_model=ServiceResponse)
async def customer_start_service(
    service_id: str,
    principal: CustomerPrincipal = Depends(require_customer_api_key),
):
    registry.assert_owner(service_id, principal.customer_id)
    customer_access.meter(principal, product="ciaas.lifecycle", units=1)
    return registry.start(service_id)


@public_router.post("/{service_id}/workloads", response_model=Dict[str, Any])
async def customer_execute_workload(
    service_id: str,
    request: IntelligenceWorkloadRequest,
    principal: CustomerPrincipal = Depends(require_customer_api_key),
):
    registry.assert_owner(service_id, principal.customer_id)
    usage = customer_access.meter(principal, product="ciaas.execute", units=_ciaas_units(request))
    envelope = registry.execute(service_id, request)
    envelope["usage_meter"] = usage
    return envelope
