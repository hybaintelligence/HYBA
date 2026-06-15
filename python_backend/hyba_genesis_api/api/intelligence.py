"""φ-aware intelligence fabric API endpoints."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from hyba_genesis_api.core.audit_surface import (
    generate_fields_medal_audit,
    seal_consciousness_envelope,
)
from hyba_genesis_api.core.intelligence_fabric import SubstrateOrchestrator, explain
from hyba_genesis_api.core.recursive_closure import build_buffered_closure
from hyba_genesis_api.core.reflexive_daemon import IntelligenceHeartbeat
from hyba_genesis_api.core.reflexive_controller import ReflexiveController, default_reflexive_root

router = APIRouter(prefix="/api/v1/intelligence", tags=["intelligence"])

MEASURED_TELEMETRY_SOURCE = "measured_reflexive_controller_runtime"
MEASURED_CLAIM_BOUNDARY = (
    "Measured reflexive codebase state from the current controller step; "
    "no fabricated, simulated, fixture, or placeholder telemetry."
)


class ExplainRequest(BaseModel):
    """Request body for deterministic substrate explanation."""

    context: Dict[str, Any] = Field(default_factory=dict)
    substrates: Optional[List[str]] = Field(default=None, max_length=3)


@router.post("/explain", response_model=Dict[str, Any])
async def explain_intelligence(req: ExplainRequest) -> Dict[str, Any]:
    """Explain a context with shared substrate telemetry and governance tags."""

    return explain(req.context, req.substrates)


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
    umwelt = controller.observe_codebase()
    state = controller.fabric.map_to_complex_state(umwelt)
    phi = controller.fabric.calculate_resonance(state)
    return {
        "phi_resonance": round(phi, 6),
        "system_state": "coherent" if phi > 0.5 else "fragmented",
        "telemetry_source": MEASURED_TELEMETRY_SOURCE,
        "measurement_basis": {
            "controller_root": str(default_reflexive_root()),
            "observed_nodes": len(getattr(state, "amplitudes", []) or []),
            "umwelt_keys": sorted(umwelt.keys()),
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
    """Return the measured audit of the current reflexive state.

    This endpoint lets the system do the talking: it runs the reflexive
    controller, derives manifold/audit metrics from that measured step, and
    returns the current evidence envelope without fixture or placeholder values.

    Returns (per specification):
      - ontological_integrity: CERTIFIED or HOLES_DETECTED
      - manifold_state: RICCI_SMOOTHED or SINGULARITY_RISK
      - topology: GENUS_{genus_proxy}
      - phi_resonance: bounded in [0, 1]
      - claim_boundary: measured evidence boundary for the current audit
    """

    controller = ReflexiveController(default_reflexive_root())
    reflection = controller.step()
    chi = reflection.get("telemetry", {}).get("chi", 1)
    phi = reflection.get("telemetry", {}).get(
        "phi", reflection.get("telemetry", {}).get("phi_resonance", 0.0)
    )
    audit = generate_fields_medal_audit(reflection)
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
    audit = generate_fields_medal_audit(reflection)
    sealed = seal_consciousness_envelope({"audit": audit})
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
