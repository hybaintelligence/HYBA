"""Commercial Computational Intelligence as a Service (CIaaS) control plane.

This router provisions admin-governed fault-tolerant virtual intelligence
computers for general computational-intelligence workloads.  It is deliberately
not coupled to mining: requests are routed through the existing HYBA
intelligence fabric and wrapped with fault-tolerance posture, tenancy,
commercial policy, audit seals, and workload metering.

Production Architecture:
- Redis-backed distributed state for horizontal scaling
- Distributed lock acquisition for multi-tenant execution isolation
- Resource metering with compute unit tracking per workload
- Automatic topology serialization on provision/start/stop
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
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
from pythia_mining.redis_state_registry import get_redis_registry
from pythia_mining.autonomous_qaas_controller import create_autonomous_controller

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


class CustomerProvisionComputationalIntelligenceRequest(BaseModel):
    """Customer-facing request to provision a commercial CIaaS virtual computer."""

    name: str = Field(min_length=3, max_length=80, pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_.-]*$")
    service_tier: ServiceTier = "developer"
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

    model_config = {"extra": "forbid"}

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


def _validate_ciaas_customer_entitlement(
    principal: CustomerPrincipal,
    request_tier: ServiceTier,
    request_tenancy: TenancyMode,
) -> None:
    """Validate customer entitlement for CIaaS tier and isolation."""
    tier = principal.tier
    sovereign_enabled = principal.metadata.get("sovereign_enabled", False)

    # Tier entitlement
    if tier == "developer":
        if request_tier != "developer":
            raise HTTPException(
                status_code=403,
                detail=f"Developer API key can only provision developer tier (requested: {request_tier})"
            )
    elif tier == "production":
        if request_tier not in ["developer", "production"]:
            raise HTTPException(
                status_code=403,
                detail=f"Production API key can only provision developer or production tier (requested: {request_tier})"
            )
    elif tier == "enterprise":
        if request_tier == "sovereign" and not sovereign_enabled:
            raise HTTPException(
                status_code=403,
                detail="Enterprise API key requires sovereign entitlement to provision sovereign tier"
            )

    # Isolation entitlement
    if tier == "developer":
        if request_tenancy != "single-tenant":
            raise HTTPException(
                status_code=403,
                detail=f"Developer API key can only request single-tenant isolation (requested: {request_tenancy})"
            )
    elif tier == "production":
        if request_tenancy not in ["single-tenant", "dedicated-control-plane"]:
            raise HTTPException(
                status_code=403,
                detail=f"Production API key can only request single-tenant or dedicated-control-plane isolation (requested: {request_tenancy})"
            )


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
        self._execution_lock = threading.RLock()
        for _ in range(request.logical_compute_units):
            self.core.initialize_logical_qubit("0")
        
        # Initialize autonomous self-healing and self-optimization
        self.autonomous = create_autonomous_controller(
            service_id=service_id,
            service_kind="ciaas",
        )

        # Serialize initial topology to Redis for distributed state
        redis_registry = get_redis_registry()
        if redis_registry.available:
            topology_data = {
                "service_id": service_id,
                "name": self.name,
                "owner": owner,
                "state": self.state,
                "created_at": now,
                "policy": self.policy,
                "workload_count": 0,
            }
            redis_registry.serialize_instance_topology(service_id, topology_data)

    def touch(self) -> None:
        self.updated_at = datetime.now(UTC).isoformat()

        # Update Redis state on every modification
        redis_registry = get_redis_registry()
        if redis_registry.available:
            topology_data = {
                "service_id": self.service_id,
                "name": self.name,
                "owner": self.owner,
                "state": self.state,
                "updated_at": self.updated_at,
                "policy": self.policy,
                "workload_count": self._workload_count,
            }
            redis_registry.serialize_instance_topology(self.service_id, topology_data)

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
        seal = hashlib.sha256(json.dumps(seal_payload, sort_keys=True).encode()).hexdigest()
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
        
        # Request-hash idempotency with mismatch rejection
        if request.idempotency_key:
            request_hash = hashlib.sha256(json.dumps(request.model_dump(), sort_keys=True).encode()).hexdigest()
            if request.idempotency_key in self._idempotency_cache:
                cached = self._idempotency_cache[request.idempotency_key]
                if cached.get("request_hash") != request_hash:
                    raise HTTPException(
                        status_code=409,
                        detail="Idempotency key reused with different request payload"
                    )
                return cached

        # Acquire per-service execution lock
        if not self._execution_lock.acquire(blocking=False):
            raise HTTPException(
                status_code=409,
                detail="Service is currently executing another workload; retry after current workload completes"
            )

        # Acquire distributed lock before execution
        redis_registry = get_redis_registry()
        lock_acquired = False
        if redis_registry.available:
            lock_acquired = redis_registry.acquire_register_lock(
                self.service_id, self.owner
            )
            if not lock_acquired:
                self._execution_lock.release()
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Service is currently executing another workload; retry after current workload completes",
                )

        try:
            # Track execution start time for metering
            exec_start = time.perf_counter()

            # Record stats before workload for delta correction_success
            stats_before = self.core.get_error_statistics()
            correction_successes_before = stats_before["correction_successes"]

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
                    "context_digest": hashlib.sha256(json.dumps(request.context, sort_keys=True).encode()).hexdigest(),
                    "commercial_policy": self.commercial_policy(),
                    "fault_tolerance": self.fault_tolerance(),
                    "claim_boundary": "CIaaS deterministic intelligence workload; no mining dependency",
                }
            else:
                result = {"substrate": get_substrate_state()}

            exec_duration = time.perf_counter() - exec_start

            # Record stats after workload for delta correction_success
            stats_after = self.core.get_error_statistics()
            correction_success = stats_after["correction_successes"] > correction_successes_before

            # Record resource consumption to Redis
            if redis_registry.available:
                context_bytes = len(repr(request.context).encode("utf-8"))
                circuit_depth_equiv = max(1, context_bytes // 1024 + 1)

                metering_result = redis_registry.record_resource_consumption(
                    instance_id=self.service_id,
                    tenant_id=self.owner,
                    metrics={
                        "defect_count": stats_after.get("last_decoder_defects", 0),
                        "pairing_weight": stats_after.get("last_decoder_weight", 1.0),
                        "circuit_depth": circuit_depth_equiv,
                    },
                )
                result["metering"] = metering_result
                result["execution_duration_ms"] = round(exec_duration * 1000, 2)
            
            # Record execution for autonomous learning with delta correction_success
            self.autonomous.record_execution(
                execution_time_ms=exec_duration * 1000,
                logical_error_rate=stats_after["logical_error_rate"],
                correction_success=correction_success,
            )
            
            # Check if autonomous healing should trigger
            metrics = self.autonomous.get_health_metrics()
            trigger = self.autonomous.should_trigger_healing(metrics)
            if trigger:
                heal_result = self.autonomous.heal(trigger)
                result["autonomous_healing"] = {
                    "triggered": True,
                    "trigger": trigger,
                    "action": heal_result.action,
                    "success": heal_result.success,
                }
            
            # Generate optimization proposals (not auto-applied)
            proposal = self.autonomous.propose_optimization(
                current_code_distance=self.policy["code_distance"],
                current_error_rate=stats["physical_error_rate"],
                metrics=metrics,
            )
            if proposal:
                result["autonomous_optimization"] = {
                    "proposal_id": proposal.proposal_id,
                    "parameter": proposal.parameter,
                    "current": proposal.current_value,
                    "proposed": proposal.proposed_value,
                    "expected_improvement": proposal.expected_improvement,
                    "confidence": proposal.confidence,
                    "status": "proposed_not_applied",
                }

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
                envelope["request_hash"] = request_hash
                self._idempotency_cache[request.idempotency_key] = envelope
            return envelope
        finally:
            # Always release locks, even if execution failed
            self._execution_lock.release()
            if lock_acquired and redis_registry.available:
                redis_registry.release_register_lock(self.service_id, self.owner)


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

                # Persist state change to Redis
                redis_registry = get_redis_registry()
                if redis_registry.available:
                    topology_data = {
                        "service_id": service.service_id,
                        "state": service.state,
                        "updated_at": service.updated_at,
                    }
                    redis_registry.serialize_instance_topology(service_id, topology_data)
                
                # Start autonomous controller
                service.autonomous.start()

            return service.response()

    def stop(self, service_id: str) -> ServiceResponse:
        with self._lock:
            service = self.get(service_id)
            
            # Stop autonomous controller and persist learned state
            service.autonomous.stop()
            
            service.state = "stopped"
            service.touch()

            # Release any held locks and persist state to Redis
            redis_registry = get_redis_registry()
            if redis_registry.available:
                redis_registry.release_register_lock(service_id, service.owner)
                topology_data = {
                    "service_id": service.service_id,
                    "state": service.state,
                    "updated_at": service.updated_at,
                }
                redis_registry.serialize_instance_topology(service_id, topology_data)

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


@router.get("/{service_id}/autonomous", response_model=Dict[str, Any])
async def get_autonomous_status(
    service_id: str,
    payload: TokenPayload = Depends(require_admin),
):
    """Get autonomous self-healing and self-optimization status."""
    service = registry.get(service_id)
    return service.autonomous.get_status()


def _ciaas_units(request: IntelligenceWorkloadRequest) -> int:
    return max(1, len(repr(request.context).encode("utf-8")) // 1024 + 1)


@public_router.post("", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def customer_provision_service(
    request: CustomerProvisionComputationalIntelligenceRequest,
    principal: CustomerPrincipal = Depends(require_customer_api_key),
):
    # Validate customer entitlement for tier and isolation
    _validate_ciaas_customer_entitlement(principal, request.service_tier, request.tenancy)
    
    # Convert customer request to admin request with admin_privileged=False
    admin_request = ProvisionComputationalIntelligenceRequest(
        name=request.name,
        service_tier=request.service_tier,
        tenancy=request.tenancy,
        code_distance=request.code_distance,
        logical_compute_units=request.logical_compute_units,
        physical_error_rate=request.physical_error_rate,
        max_workloads_per_minute=request.max_workloads_per_minute,
        max_context_bytes=request.max_context_bytes,
        admin_privileged=False,  # Force False for customer provisioning
        data_residency=request.data_residency,
        allowed_workloads=request.allowed_workloads,
    )
    
    customer_access.meter(principal, product="ciaas.provision", units=request.logical_compute_units)
    response = registry.provision(admin_request, owner=principal.customer_id)
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
