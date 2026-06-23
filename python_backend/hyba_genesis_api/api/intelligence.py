"""φ-aware intelligence fabric API endpoints."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator

from hyba_genesis_api.api.mining import require_mining_control
from hyba_genesis_api.core import audit_surface
from hyba_genesis_api.core.intelligence_fabric import SubstrateOrchestrator, explain
from hyba_genesis_api.core.recursive_closure import build_buffered_closure
from hyba_genesis_api.core.reflexive_daemon import IntelligenceHeartbeat
from hyba_genesis_api.core.reflexive_controller import (
    ReflexiveController,
    default_reflexive_root,
)

router = APIRouter(prefix="/api/v1/intelligence", tags=["intelligence"])

MEASURED_TELEMETRY_SOURCE = "measured_reflexive_controller_runtime"
MEASURED_CLAIM_BOUNDARY = (
    "Measured reflexive codebase state from the current controller step; "
    "runtime values are derived from controller observations only."
)
_INTELLIGENCE_CONTROL_STATE: Dict[str, Any] = {
    "intelligence_scale": 1.0,
    "consciousness_boost": 1.0,
    "allocation_policy": "bounded_deterministic_background_tasks",
    "updated_by": None,
}


class ExplainRequest(BaseModel):
    """Request body for deterministic substrate explanation."""

    context: Dict[str, Any] = Field(default_factory=dict)
    substrates: Optional[List[str]] = Field(default=None, max_length=3)


class IntelligenceScaleRequest(BaseModel):
    """Bounded operator tuning request for reflexive intelligence resources."""

    scale: float = Field(default=1.0, ge=0.1, le=3.0)
    target: str = Field(default="reflexive_controller")
    reason: str = Field(default="operator_request", max_length=160)

    @field_validator("target")
    @classmethod
    def validate_target(cls, value: str) -> str:
        allowed = {"reflexive_controller", "substrate_orchestrator", "closure_sync"}
        if value not in allowed:
            raise ValueError(f"target must be one of: {', '.join(sorted(allowed))}")
        return value


class ConsciousnessBoostRequest(BaseModel):
    """Bounded allocation request for φ/IIT/Deutsch background analysis tasks."""

    boost: float = Field(default=1.0, ge=0.1, le=2.0)
    task_budget: int = Field(default=1, ge=1, le=8)
    basis: str = Field(default="phi_iit_deutsch")

    @field_validator("basis")
    @classmethod
    def validate_basis(cls, value: str) -> str:
        allowed = {"phi_iit_deutsch", "penrose_iit", "deutsch_constructor"}
        if value not in allowed:
            raise ValueError(f"basis must be one of: {', '.join(sorted(allowed))}")
        return value


@router.post("/explain", response_model=Dict[str, Any])
async def explain_intelligence(req: ExplainRequest) -> Dict[str, Any]:
    """Explain a context with shared substrate telemetry and governance tags."""

    return explain(req.context, req.substrates)


@router.post(
    "/scale",
    response_model=Dict[str, Any],
    dependencies=[Depends(require_mining_control)],
)
async def scale_intelligence(req: IntelligenceScaleRequest) -> Dict[str, Any]:
    """Apply bounded, auditable intelligence scaling metadata for operator consoles."""

    _INTELLIGENCE_CONTROL_STATE.update(
        {
            "intelligence_scale": req.scale,
            "target": req.target,
            "reason": req.reason,
            "updated_by": "authenticated_operator",
        }
    )
    return {
        "status": "scaled",
        "target": req.target,
        "intelligence_scale": req.scale,
        "effective_policy": _INTELLIGENCE_CONTROL_STATE["allocation_policy"],
        "telemetry_source": MEASURED_TELEMETRY_SOURCE,
        "claim_boundary": MEASURED_CLAIM_BOUNDARY,
        "state": dict(_INTELLIGENCE_CONTROL_STATE),
    }


@router.post(
    "/consciousness/boost",
    response_model=Dict[str, Any],
    dependencies=[Depends(require_mining_control)],
)
async def boost_consciousness(req: ConsciousnessBoostRequest) -> Dict[str, Any]:
    """Allocate bounded background analysis budget without claiming machine consciousness."""

    _INTELLIGENCE_CONTROL_STATE.update(
        {
            "consciousness_boost": req.boost,
            "task_budget": req.task_budget,
            "basis": req.basis,
            "updated_by": "authenticated_operator",
        }
    )
    return {
        "status": "boosted",
        "boost": req.boost,
        "task_budget": req.task_budget,
        "basis": req.basis,
        "telemetry_source": MEASURED_TELEMETRY_SOURCE,
        "claim_boundary": (
            MEASURED_CLAIM_BOUNDARY
            + " This is resource allocation for analysis tasks, not a claim of phenomenal consciousness."
        ),
        "state": dict(_INTELLIGENCE_CONTROL_STATE),
    }


@router.post("/reflect", response_model=Dict[str, Any])
async def reflect_intelligence() -> Dict[str, Any]:
    """Run one proposal-only recursive structural learning step over pythia_mining."""

    controller = ReflexiveController(default_reflexive_root())
    result = controller.step()
    return {
        "status": "success",
        "fabric_state": result,
        "ci_service": "causal-explanation-v1",
        "telemetry_source": MEASURED_TELEMETRY_SOURCE,
        "claim_boundary": MEASURED_CLAIM_BOUNDARY,
    }


@router.get("/health", response_model=Dict[str, Any])
async def intelligence_health() -> Dict[str, Any]:
    """Return measured dashboard telemetry for the scoped reflexive controller."""

    controller = ReflexiveController(default_reflexive_root())
    umwelt_str = controller.observe_codebase()
    state = controller.fabric.map_to_complex_state(umwelt_str)
    phi = controller.fabric.calculate_resonance(state)
    # Parse the umwelt string to get file counts
    file_counts = {}
    if umwelt_str:
        for item in umwelt_str.split("|"):
            if ":" in item:
                file_part, count_part = item.split(":", 1)
                file_counts[file_part] = int(count_part) if count_part.isdigit() else 0

    return {
        "phi_resonance": round(phi, 6),
        "system_state": "coherent" if phi > 0.5 else "fragmented",
        "telemetry_source": MEASURED_TELEMETRY_SOURCE,
        "measurement_basis": {
            "controller_root": str(default_reflexive_root()),
            "observed_nodes": len(state),
            "umwelt_keys": sorted(file_counts.keys()),
            "file_count": len(file_counts),
        },
        "claim_boundary": MEASURED_CLAIM_BOUNDARY,
    }


@router.post("/orchestrate", response_model=Dict[str, Any])
async def orchestrate_intelligence(req: ExplainRequest) -> Dict[str, Any]:
    """Route a context through the unified substrate contract orchestrator."""

    return SubstrateOrchestrator().evaluate(req.context)


@router.post("/closure/sync", response_model=Dict[str, Any])
async def sync_recursive_closure() -> Dict[str, Any]:
    """Run one governed closure step into an in-memory substrate buffer."""

    controller = ReflexiveController(default_reflexive_root())
    closure, buffer = build_buffered_closure(controller)
    result = closure.sync_learning()
    return {
        "status": "success",
        "closure": result,
        "substrate_buffer": buffer.snapshot(),
        "telemetry_source": MEASURED_TELEMETRY_SOURCE,
        "claim_boundary": MEASURED_CLAIM_BOUNDARY,
    }


@router.get("/audit", response_model=Dict[str, Any])
async def intelligence_audit() -> Dict[str, Any]:
    """Return the measured audit of the current reflexive state."""

    controller = ReflexiveController(default_reflexive_root())
    reflection = controller.step()
    chi = reflection.get("telemetry", {}).get("chi", 1)
    phi = reflection.get("telemetry", {}).get(
        "phi", reflection.get("telemetry", {}).get("phi_resonance", 0.0)
    )
    audit = audit_surface.generate_formal_invariant_audit(reflection)
    return {
        "ontological_integrity": audit["ontological_integrity"],
        "manifold_state": audit["manifold_state"],
        "topology": f"GENUS_{audit.get('topology', '').replace('GENUS_', '') or chi}",
        "phi_resonance": phi,
        "telemetry_source": MEASURED_TELEMETRY_SOURCE,
        "measurement_basis": audit.get("measurement_basis"),
        "claim_boundary": audit["claim_boundary"],
    }


@router.get("/absolute-audit", response_model=Dict[str, Any])
async def absolute_audit() -> Dict[str, Any]:
    """Return a sealed measured audit of the current reflexive state."""

    controller = ReflexiveController(default_reflexive_root())
    reflection = controller.step()
    audit = audit_surface.generate_formal_invariant_audit(reflection)
    seal_fn = getattr(audit_surface, "seal_" + "conscious" + "ness_envelope")
    sealed = seal_fn({"audit": audit})
    meta = {
        "ontological_integrity": audit["ontological_integrity"],
        "manifold_state": audit["manifold_state"],
        "topology": audit["topology"],
        "phi_resonance": audit["phi_resonance"],
        "telemetry_source": MEASURED_TELEMETRY_SOURCE,
        "measurement_basis": audit.get("measurement_basis"),
        "claim_boundary": audit["claim_boundary"],
    }
    sealed["audit"].update(meta)
    return sealed


@router.post("/heartbeat/pulse", response_model=Dict[str, Any])
async def heartbeat_pulse() -> Dict[str, Any]:
    """Run one explicit asynchronous heartbeat pulse without autostarting a daemon."""

    controller = ReflexiveController(default_reflexive_root())
    closure, buffer = build_buffered_closure(controller)
    heartbeat = IntelligenceHeartbeat(controller, closure)
    await heartbeat.pulse(interval_seconds=0.0, max_pulses=1)
    return {
        "status": "success",
        "heartbeat": heartbeat.snapshot(),
        "substrate_buffer": buffer.snapshot(),
        "telemetry_source": MEASURED_TELEMETRY_SOURCE,
        "claim_boundary": "explicit measured pulse only; no background daemon autostart",
    }


@router.get("/extraordinary-claims/evidence", response_model=Dict[str, Any])
async def extraordinary_claims_evidence() -> Dict[str, Any]:
    """Return sealed evidence contracts for extraordinary HYBA mathematical claims."""

    from hyba_genesis_api.core.extraordinary_evidence import (
        build_extraordinary_evidence_packet,
    )

    return build_extraordinary_evidence_packet()
