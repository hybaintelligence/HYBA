"""Enterprise Salamander Substrate API surface.

This module exposes the biological-primitives API as an auditable enterprise
contract.  It intentionally avoids fabricated production telemetry: endpoints
return deterministic self-checks or request-derived simulations unless wired to a
live telemetry source by the caller.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from pythia_mining.salamander_frontier import (
    CrossLanguageReplayManifest,
    DreamMutation,
    ImmutableEvidenceLog,
    MetabolicInvariantMetrics,
    SalamanderDreamState,
    SalamanderGene,
    SalamanderPropertyBattery,
)

router = APIRouter(prefix="/api/v1/salamander", tags=["salamander-substrate"])

SUBSTRATE_API_VERSION = "salamander.substrate.enterprise.v1"
CLAIM_BOUNDARY = "deterministic_substrate_control_plane_no_fabricated_live_telemetry"


class EnterpriseEnvelope(BaseModel):
    """Standard response envelope for executive and regulated integrations."""

    api_version: str = SUBSTRATE_API_VERSION
    claim_boundary: str = CLAIM_BOUNDARY
    trace_id: str
    verdict: str
    data: Dict[str, Any]
    evidence: Dict[str, Any] = Field(default_factory=dict)


class MetabolismStatus(BaseModel):
    """Transparent metabolic status payload.

    Null metrics mean no live telemetry adapter has been attached; the API does
    not invent wattage, ROI, or efficiency readings.
    """

    status: Literal["NO_LIVE_TELEMETRY", "HOMEOSTASIS", "DEGRADED"] = "NO_LIVE_TELEMETRY"
    wattage_draw: Optional[float] = None
    roi_threshold: Optional[float] = None
    current_efficiency: Optional[float] = None
    actions: List[str] = Field(default_factory=list)


class EvidenceEntryRequest(BaseModel):
    event: str = Field(min_length=1, max_length=120)
    actor: str = Field(default="enterprise-client", min_length=1, max_length=120)
    timestamp: float = Field(default=1.0, ge=0.0)
    data: Dict[str, Any] = Field(default_factory=dict)


class DreamSimulationRequest(BaseModel):
    baseline_gene: str = Field(default="phi_ratio", min_length=1, max_length=80)
    baseline_value: float = Field(default=1.618033988749895)
    mutated_value: float
    min_value: float = Field(default=1.0)
    max_value: float = Field(default=2.0)
    promotion_threshold: float = Field(default=0.0, ge=0.0)
    baseline_evidence: List[EvidenceEntryRequest] = Field(default_factory=list)
    target_value: float = Field(default=1.618033988749895)


class RegenerationJumpRequest(BaseModel):
    target_node: str = Field(min_length=1, max_length=120)
    target_language: Literal["rust", "python"] = "rust"
    manifest_digest: str = Field(min_length=16, max_length=128)


class AuditVerdictRequest(BaseModel):
    evidence: List[EvidenceEntryRequest] = Field(default_factory=list)
    metabolic_metrics: MetabolicInvariantMetrics
    phi_value: float = Field(default=1.618033988749895)


def _trace(prefix: str) -> str:
    return f"{prefix}-{int(time.time() * 1_000_000)}"


def _build_log(entries: List[EvidenceEntryRequest]) -> ImmutableEvidenceLog:
    log = ImmutableEvidenceLog()
    for entry in entries:
        log = log.append(entry.event, actor=entry.actor, timestamp=entry.timestamp, **entry.data)
    return log


def _dump_model(model: BaseModel) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


@router.get("/metabolism/status", response_model=EnterpriseEnvelope)
def get_metabolism_status() -> EnterpriseEnvelope:
    status_payload = MetabolismStatus()
    return EnterpriseEnvelope(
        trace_id=_trace("metabolism"),
        verdict="TELEMETRY_ADAPTER_REQUIRED",
        data=_dump_model(status_payload),
        evidence={"telemetry_source": "not_configured", "fabricated_values": False},
    )


@router.post("/dream/simulate", response_model=EnterpriseEnvelope)
def simulate_dream(request: DreamSimulationRequest) -> EnterpriseEnvelope:
    if request.min_value > request.max_value:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="min_value must be less than or equal to max_value",
        )

    log = _build_log(request.baseline_evidence)
    gene = SalamanderGene(
        request.baseline_gene,
        value=request.baseline_value,
        min_value=request.min_value,
        max_value=request.max_value,
    )

    def evaluator(evidence_log: ImmutableEvidenceLog, genes: Dict[str, SalamanderGene]) -> float:
        evidence_bonus = len(evidence_log.entries()) * 0.001
        return evidence_bonus - abs(genes[request.baseline_gene].value - request.target_value)

    dream = SalamanderDreamState(evaluator, promotion_threshold=request.promotion_threshold)
    outcome = dream.simulate_mutation(
        log,
        {request.baseline_gene: gene},
        DreamMutation(request.baseline_gene, request.mutated_value),
        actor="enterprise-dream-api",
    )
    return EnterpriseEnvelope(
        trace_id=outcome.dream_id,
        verdict="PROMOTABLE" if outcome.promoted else "OBSERVE_ONLY",
        data={
            "dream_id": outcome.dream_id,
            "improvement_detected": outcome.improvement,
            "mutated_value": outcome.mutated_value,
            "baseline_fitness": outcome.baseline_fitness,
            "simulated_fitness": outcome.simulated_fitness,
        },
        evidence={
            "baseline_evidence_hash": outcome.evidence_hash,
            "audit_event": outcome.audit_log.entries()[-1].to_dict(),
        },
    )


@router.post("/regenerate/jump", response_model=EnterpriseEnvelope)
def request_regeneration_jump(request: RegenerationJumpRequest) -> EnterpriseEnvelope:
    if request.target_language != "rust":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="only rust blastema jumps are currently supported by the portable seed",
        )
    return EnterpriseEnvelope(
        trace_id=_trace("regen"),
        verdict="PLAN_READY",
        data={
            "target_node": request.target_node,
            "target_language": request.target_language,
            "next_step": "compile_runtime_seeds/salamander_blastema_seed.rs",
            "manifest_digest": request.manifest_digest,
        },
        evidence={"operator_approval_required": True, "automatic_execution": False},
    )


@router.post("/audit/verdict", response_model=EnterpriseEnvelope)
def audit_verdict(request: AuditVerdictRequest) -> EnterpriseEnvelope:
    battery = SalamanderPropertyBattery()
    log = _build_log(request.evidence)
    invariants = [
        battery.invariant_evidence_fidelity(log),
        battery.invariant_metabolic_conservation(request.metabolic_metrics),
        battery.invariant_phi_resonance_bounds(request.phi_value),
    ]
    all_passed = all(result.passed for result in invariants)
    manifest = CrossLanguageReplayManifest(log).to_manifest()
    return EnterpriseEnvelope(
        trace_id=_trace("audit"),
        verdict="PASS" if all_passed else "REVIEW_REQUIRED",
        data={
            result.invariant: (
                result.model_dump() if hasattr(result, "model_dump") else result.__dict__
            )
            for result in invariants
        },
        evidence={
            "manifest_digest": manifest["replay_digest"],
            "entry_count": manifest["entry_count"],
        },
    )
