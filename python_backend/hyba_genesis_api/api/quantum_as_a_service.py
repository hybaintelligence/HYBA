"""Admin Quantum-as-a-Service provisioning for virtual fault-tolerant computers.

The public product surface here is a substrate-agnostic, mathematical virtual
fault-tolerant quantum computer.  Mining remains only an external stress-test
of the math; this router exposes general quantum compute provisioning and
execution semantics: topological parameters, logical-qubit allocation,
surface-code cycles, φ-resonance analysis, and intelligence-fabric routing.

Production Architecture:
- Redis-backed distributed state for horizontal scaling
- Distributed lock acquisition for multi-tenant execution isolation
- Resource metering with compute unit tracking per execution
- Automatic topology serialization on provision/start/stop
"""

from __future__ import annotations

import hashlib
import math
import threading
import time
import uuid
from datetime import UTC, datetime
from typing import Any, Dict, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from hyba_genesis_api.api.admin import require_admin
from hyba_genesis_api.api.customer_access import CustomerPrincipal, customer_access, require_customer_api_key
from hyba_genesis_api.auth.jwt_handler import TokenPayload
from hyba_genesis_api.core.intelligence_fabric import SubstrateOrchestrator, explain
from hyba_genesis_api.core.substrate import get_substrate_state, initialize_substrate
from pythia_mining.fault_tolerant_quantum_core import FaultTolerantQuantumCore, PHI
from pythia_mining.redis_state_registry import get_redis_registry

router = APIRouter(prefix="/api/admin/fault-tolerant-computers", tags=["quantum-as-a-service-admin"])
public_router = APIRouter(prefix="/api/v1/fault-tolerant-computers", tags=["quantum-as-a-service"])

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
    """Provision a commercial virtual fault-tolerant quantum computer."""

    name: str = Field(min_length=3, max_length=80, pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_.-]*$")
    tier: QaaSTier = "production"
    isolation: IsolationMode = "dedicated-control-plane"
    code_distance: int = Field(default=7, ge=3, le=31)
    logical_qubits: int = Field(default=32, ge=1, le=512)
    physical_error_rate: float = Field(default=1e-3, gt=0.0, lt=0.0109)
    phi_resonance_target: float = Field(default=0.9565, gt=0.0, le=1.0)
    max_circuit_depth: int = Field(default=1_024, ge=1, le=1_000_000)
    max_shots: int = Field(default=1_024, ge=1, le=1_000_000)
    admin_privileged: bool = Field(default=False)
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

    @field_validator("code_distance")
    @classmethod
    def code_distance_must_be_odd(cls, value: int) -> int:
        if value % 2 == 0:
            raise ValueError("code_distance must be odd for surface-code fault tolerance")
        return value

    @field_validator("allowed_operations")
    @classmethod
    def allowed_operations_must_be_unique(
        cls,
        value: list[QuantumOperation],
    ) -> list[QuantumOperation]:
        if len(set(value)) != len(value):
            raise ValueError("allowed_operations must not contain duplicates")
        return value


class QuantumWorkloadRequest(BaseModel):
    operation: QuantumOperation = "surface_code_cycle"
    logical_qubits: list[int] = Field(default_factory=list, max_length=512)
    circuit_depth: int = Field(default=1, ge=1, le=1_000_000)
    shots: int = Field(default=1, ge=1, le=1_000_000)
    context: Dict[str, Any] = Field(default_factory=dict)
    substrates: Optional[list[Literal["penrose_or", "iit_4", "deutsch"]]] = Field(
        default=None,
        max_length=3,
    )
    idempotency_key: Optional[str] = Field(default=None, max_length=128)


class FaultTolerantComputerResponse(BaseModel):
    computer_id: str
    name: str
    state: ComputerState
    tier: QaaSTier
    isolation: IsolationMode
    admin_privileged: bool
    owner: str
    created_at: str
    updated_at: str
    quantum_parameters: Dict[str, Any]
    fault_tolerance: Dict[str, Any]
    substrate: Dict[str, Any]
    evidence_seal: str
    claim_boundary: str


class _VirtualFaultTolerantQuantumComputer:
    def __init__(
        self,
        *,
        computer_id: str,
        request: ProvisionFaultTolerantComputerRequest,
        owner: str,
    ) -> None:
        now = datetime.now(UTC).isoformat()
        self.computer_id = computer_id
        self.name = request.name
        self.owner = owner
        self.state: ComputerState = "provisioned"
        self.created_at = now
        self.updated_at = now
        self.policy = request.model_dump()
        self.core = FaultTolerantQuantumCore(
            code_distance=request.code_distance,
            physical_error_rate=request.physical_error_rate,
        )
        self._executions = 0
        self._idempotency_cache: dict[str, Dict[str, Any]] = {}
        for _ in range(request.logical_qubits):
            self.core.initialize_logical_qubit("0")

        # Serialize initial topology to Redis for distributed state
        redis_registry = get_redis_registry()
        if redis_registry.available:
            topology_data = {
                "computer_id": computer_id,
                "name": self.name,
                "owner": owner,
                "state": self.state,
                "created_at": now,
                "policy": self.policy,
                "executions": 0,
            }
            redis_registry.serialize_instance_topology(computer_id, topology_data)

    def touch(self) -> None:
        self.updated_at = datetime.now(UTC).isoformat()

        # Update Redis state on every modification
        redis_registry = get_redis_registry()
        if redis_registry.available:
            topology_data = {
                "computer_id": self.computer_id,
                "name": self.name,
                "owner": self.owner,
                "state": self.state,
                "updated_at": self.updated_at,
                "policy": self.policy,
                "executions": self._executions,
            }
            redis_registry.serialize_instance_topology(self.computer_id, topology_data)

    def quantum_parameters(self) -> Dict[str, Any]:
        return {
            "code_distance": self.policy["code_distance"],
            "logical_qubits": self.policy["logical_qubits"],
            "physical_error_rate": self.policy["physical_error_rate"],
            "phi_resonance_target": self.policy["phi_resonance_target"],
            "max_circuit_depth": self.policy["max_circuit_depth"],
            "max_shots": self.policy["max_shots"],
            "allowed_operations": list(self.policy["allowed_operations"]),
            "executions": self._executions,
        }

    def fault_tolerance(self) -> Dict[str, Any]:
        stats = self.core.get_error_statistics()
        return {
            "surface_code_distance": self.core.d,
            "logical_error_rate": stats["logical_error_rate"],
            "physical_error_rate": stats["physical_error_rate"],
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
                "Syndrome corrections are derived from the local decoder model; "
                "logical error rate is an analytic surface-code projection, not "
                "measured physical hardware fault tolerance."
            ),
        }

    def response(self) -> FaultTolerantComputerResponse:
        substrate = get_substrate_state()
        seal_payload = {
            "computer_id": self.computer_id,
            "owner": self.owner,
            "state": self.state,
            "quantum_parameters": self.quantum_parameters(),
            "fault_tolerance": self.fault_tolerance(),
            "substrate_ready": substrate.get("ready"),
        }
        evidence_seal = hashlib.sha256(repr(sorted(seal_payload.items())).encode()).hexdigest()
        return FaultTolerantComputerResponse(
            computer_id=self.computer_id,
            name=self.name,
            state=self.state,
            tier=self.policy["tier"],
            isolation=self.policy["isolation"],
            admin_privileged=self.policy["admin_privileged"],
            owner=self.owner,
            created_at=self.created_at,
            updated_at=self.updated_at,
            quantum_parameters=self.quantum_parameters(),
            fault_tolerance=self.fault_tolerance(),
            substrate=substrate,
            evidence_seal=evidence_seal,
            claim_boundary="Quantum-as-a-Service virtual fault-tolerant computer; substrate-agnostic mathematical runtime; mining is not part of this API surface.",
        )

    def _validate_workload(self, request: QuantumWorkloadRequest) -> list[int]:
        if request.operation not in self.policy["allowed_operations"]:
            raise HTTPException(status_code=403, detail="operation is not allowed by computer policy")
        if request.circuit_depth > self.policy["max_circuit_depth"]:
            raise HTTPException(status_code=413, detail="circuit depth exceeds computer policy")
        if request.shots > self.policy["max_shots"]:
            raise HTTPException(status_code=413, detail="shot count exceeds computer policy")
        qubits = request.logical_qubits or list(range(min(3, len(self.core.logical_qubits))))
        if any(index < 0 or index >= len(self.core.logical_qubits) for index in qubits):
            raise HTTPException(status_code=422, detail="logical_qubits contains an out-of-range index")
        return qubits

    def execute(self, request: QuantumWorkloadRequest) -> Dict[str, Any]:
        qubits = self._validate_workload(request)
        if request.idempotency_key and request.idempotency_key in self._idempotency_cache:
            return self._idempotency_cache[request.idempotency_key]

        # Acquire distributed lock before execution
        redis_registry = get_redis_registry()
        lock_acquired = False
        if redis_registry.available:
            lock_acquired = redis_registry.acquire_register_lock(
                self.computer_id, self.owner
            )
            if not lock_acquired:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Instance is currently executing another workload; retry after current execution completes",
                )

        try:
            # Track execution start time for metering
            exec_start = time.perf_counter()

            for _ in range(request.circuit_depth):
                for qubit_idx in qubits:
                    self.core.measure_syndromes(qubit_idx)
                    self.core.measure_syndromes(qubit_idx)
                    self.core.decode_and_correct(qubit_idx)

            if request.operation == "surface_code_cycle":
                result = {
                    "logical_qubits": qubits,
                    "circuit_depth": request.circuit_depth,
                    "shots": request.shots,
                    "syndrome_rounds": self.core.get_error_statistics()["syndrome_rounds"],
                }
            elif request.operation == "phi_resonance_analysis":
                target = self.policy["phi_resonance_target"]
                result = {
                    "phi": PHI,
                    "target": target,
                    "alignment": round(max(0.0, min(1.0, 1.0 - abs(PHI / math.pi - target))), 6),
                    "analysis": explain(request.context or {"operation": request.operation}, request.substrates),
                }
            elif request.operation == "state_vector_summary":
                result = {
                    "logical_qubits": qubits,
                    "center_amplitudes": [
                        str(self.core.logical_qubits[index].physical_qubits[self.core.d // 2, self.core.d // 2])
                        for index in qubits
                    ],
                    "fault_tolerance": self.fault_tolerance(),
                }
            elif request.operation == "substrate_orchestration":
                result = SubstrateOrchestrator().evaluate(request.context)
            else:
                result = {
                    "context_digest": hashlib.sha256(repr(sorted(request.context.items())).encode()).hexdigest(),
                    "quantum_parameters": self.quantum_parameters(),
                    "fault_tolerance": self.fault_tolerance(),
                    "claim_boundary": "Governance audit for virtual QaaS runtime; no mining dependency.",
                }

            exec_duration = time.perf_counter() - exec_start

            # Record resource consumption to Redis
            if redis_registry.available:
                stats = self.core.get_error_statistics()
                metering_result = redis_registry.record_resource_consumption(
                    instance_id=self.computer_id,
                    tenant_id=self.owner,
                    metrics={
                        "defect_count": stats.get("last_decoder_defects", 0),
                        "pairing_weight": stats.get("last_decoder_weight", 1.0),
                        "circuit_depth": request.circuit_depth,
                    },
                )
                result["metering"] = metering_result
                result["execution_duration_ms"] = round(exec_duration * 1000, 2)

            self._executions += 1
            self.touch()
            envelope = {
                "computer_id": self.computer_id,
                "operation": request.operation,
                "state": self.state,
                "result": result,
                "quantum_parameters": self.quantum_parameters(),
                "fault_tolerance": self.fault_tolerance(),
                "executed_at": self.updated_at,
                "claim_boundary": "Fault-tolerant virtual quantum computer API; pure mathematical/substrate-agnostic execution surface; not a mining hypervisor.",
            }
            if request.idempotency_key:
                self._idempotency_cache[request.idempotency_key] = envelope
            return envelope
        finally:
            # Always release lock, even if execution failed
            if lock_acquired and redis_registry.available:
                redis_registry.release_register_lock(self.computer_id, self.owner)


class QuantumComputerRegistry:
    """Thread-safe registry for commercial virtual fault-tolerant quantum computers."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._computers: dict[str, _VirtualFaultTolerantQuantumComputer] = {}

    def provision(
        self,
        request: ProvisionFaultTolerantComputerRequest,
        owner: str,
    ) -> FaultTolerantComputerResponse:
        with self._lock:
            computer_id = f"qaaS-{uuid.uuid4().hex[:12]}".lower()
            computer = _VirtualFaultTolerantQuantumComputer(
                computer_id=computer_id,
                request=request,
                owner=owner,
            )
            self._computers[computer_id] = computer
            return computer.response()

    def get(self, computer_id: str) -> _VirtualFaultTolerantQuantumComputer:
        try:
            return self._computers[computer_id]
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="fault-tolerant computer not found") from exc

    def list(self, owner: str | None = None) -> list[FaultTolerantComputerResponse]:
        with self._lock:
            return [
                computer.response()
                for computer in self._computers.values()
                if owner is None or computer.owner == owner
            ]

    def start(self, computer_id: str) -> FaultTolerantComputerResponse:
        with self._lock:
            computer = self.get(computer_id)
            if computer.state != "running":
                initialize_substrate()
                computer.state = "running"
                computer.touch()

                # Persist state change to Redis
                redis_registry = get_redis_registry()
                if redis_registry.available:
                    topology_data = {
                        "computer_id": computer.computer_id,
                        "state": computer.state,
                        "updated_at": computer.updated_at,
                    }
                    redis_registry.serialize_instance_topology(computer_id, topology_data)

            return computer.response()

    def stop(self, computer_id: str) -> FaultTolerantComputerResponse:
        with self._lock:
            computer = self.get(computer_id)
            computer.state = "stopped"
            computer.touch()

            # Release any held locks and persist state to Redis
            redis_registry = get_redis_registry()
            if redis_registry.available:
                redis_registry.release_register_lock(computer_id, computer.owner)
                topology_data = {
                    "computer_id": computer.computer_id,
                    "state": computer.state,
                    "updated_at": computer.updated_at,
                }
                redis_registry.serialize_instance_topology(computer_id, topology_data)

            return computer.response()

    def execute(self, computer_id: str, request: QuantumWorkloadRequest) -> Dict[str, Any]:
        with self._lock:
            computer = self.get(computer_id)
            if computer.state != "running":
                raise HTTPException(status_code=409, detail="computer must be running before workloads execute")
            return computer.execute(request)

    def assert_owner(self, computer_id: str, owner: str) -> _VirtualFaultTolerantQuantumComputer:
        computer = self.get(computer_id)
        if computer.owner != owner:
            raise HTTPException(status_code=404, detail="fault-tolerant computer not found")
        return computer


registry = QuantumComputerRegistry()


@router.post("", response_model=FaultTolerantComputerResponse, status_code=status.HTTP_201_CREATED)
async def provision_computer(
    request: ProvisionFaultTolerantComputerRequest,
    payload: TokenPayload = Depends(require_admin),
):
    return registry.provision(request, owner=payload.username)


@router.get("", response_model=list[FaultTolerantComputerResponse])
async def list_computers(payload: TokenPayload = Depends(require_admin)):
    return registry.list()


@router.get("/{computer_id}", response_model=FaultTolerantComputerResponse)
async def get_computer(computer_id: str, payload: TokenPayload = Depends(require_admin)):
    return registry.get(computer_id).response()


@router.post("/{computer_id}/start", response_model=FaultTolerantComputerResponse)
async def start_computer(computer_id: str, payload: TokenPayload = Depends(require_admin)):
    return registry.start(computer_id)


@router.post("/{computer_id}/stop", response_model=FaultTolerantComputerResponse)
async def stop_computer(computer_id: str, payload: TokenPayload = Depends(require_admin)):
    return registry.stop(computer_id)


@router.post("/{computer_id}/execute", response_model=Dict[str, Any])
async def execute_quantum_workload(
    computer_id: str,
    request: QuantumWorkloadRequest,
    payload: TokenPayload = Depends(require_admin),
):
    return registry.execute(computer_id, request)


def _qaas_units(request: QuantumWorkloadRequest) -> int:
    return (
        max(1, request.circuit_depth)
        * max(1, request.shots)
        * max(1, len(request.logical_qubits) or 1)
    )


@public_router.post("", response_model=FaultTolerantComputerResponse, status_code=status.HTTP_201_CREATED)
async def customer_provision_computer(
    request: ProvisionFaultTolerantComputerRequest,
    principal: CustomerPrincipal = Depends(require_customer_api_key),
):
    customer_access.meter(principal, product="qaas.provision", units=request.logical_qubits)
    response = registry.provision(request, owner=principal.customer_id)
    customer_access.set_state(f"qaas:{response.computer_id}", response.model_dump())
    return response


@public_router.get("", response_model=list[FaultTolerantComputerResponse])
async def customer_list_computers(
    principal: CustomerPrincipal = Depends(require_customer_api_key),
):
    customer_access.meter(principal, product="qaas.list", units=1)
    return registry.list(owner=principal.customer_id)


@public_router.post("/{computer_id}/start", response_model=FaultTolerantComputerResponse)
async def customer_start_computer(
    computer_id: str,
    principal: CustomerPrincipal = Depends(require_customer_api_key),
):
    registry.assert_owner(computer_id, principal.customer_id)
    customer_access.meter(principal, product="qaas.lifecycle", units=1)
    return registry.start(computer_id)


@public_router.post("/{computer_id}/execute", response_model=Dict[str, Any])
async def customer_execute_quantum_workload(
    computer_id: str,
    request: QuantumWorkloadRequest,
    principal: CustomerPrincipal = Depends(require_customer_api_key),
):
    registry.assert_owner(computer_id, principal.customer_id)
    usage = customer_access.meter(principal, product="qaas.execute", units=_qaas_units(request))
    envelope = registry.execute(computer_id, request)
    envelope["usage_meter"] = usage
    return envelope
