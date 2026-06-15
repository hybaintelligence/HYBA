"""
HENDRIX-Φ + PULVINI Unified Mining Engine REST API.

This route is an evidence/control surface over the canonical
``pythia_mining.phi_unified_mining_engine.UnifiedMiningEngine``. It must not
invent telemetry, simulate share acceptance, or use stale field names. The
engine owns the mining state; this module adapts that state into stable API
responses.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from hyba_genesis_api.api.mining import require_mining_control, require_mining_read
from hyba_genesis_api.auth.jwt_handler import TokenPayload
from pythia_mining.hendrix_phi_solver import (
    phi_resonance,
    soft_mass_gap_gate,
    voronoi_domain,
    yang_mills_action,
)
from pythia_mining.phi_unified_mining_engine import UnifiedMiningEngine


_engine: Optional[UnifiedMiningEngine] = None


def get_engine() -> UnifiedMiningEngine:
    """Lazy-initialize the canonical unified mining engine."""

    global _engine
    if _engine is None:
        _engine = UnifiedMiningEngine()
    return _engine


class UnifiedEngineStatus(BaseModel):
    """Current unified mining engine status."""

    timestamp: str
    engine: str
    version: str
    consciousness_coherence: float = Field(..., ge=0.0, le=1.0)
    consciousness_regime: str
    accepted_shares: int
    rejected_shares: int
    effective_search_dim_bits: float
    m32_domains_covered: int
    working_set_compression: float
    verifier_backend: str
    verifier_metal_available: bool
    telemetry_source: str


class NonceResonanceAnalysis(BaseModel):
    """Analysis of a single nonce."""

    nonce: int
    phi_resonance_strength: float = Field(..., ge=0.0, le=1.0)
    yang_mills_action: float
    is_mass_gate_passed: bool
    voronoi_domain: int


class BatchResonanceRequest(BaseModel):
    """Request to analyze nonces."""

    nonces: List[int] = Field(..., min_length=1, max_length=10000)


class BatchResonanceResponse(BaseModel):
    """Response with resonance analysis."""

    timestamp: str
    count: int
    mean_phi_resonance: float
    max_phi_resonance: float
    min_phi_resonance: float
    mass_gate_pass_rate: float
    analysis: List[NonceResonanceAnalysis]
    telemetry_source: str


class ShareResultRequest(BaseModel):
    """Report a share result into the meta-learning feedback loop."""

    nonce: int
    accepted: bool
    job_id: str = "manual-report"
    pool_difficulty: float = 1.0
    strategy_used: str = "phi_scaled_compressed_solver_search"
    phi_resonance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    error_code: Optional[int] = None
    error_msg: Optional[str] = None


class AIMetrics(BaseModel):
    """AI optimization and feedback metrics."""

    timestamp: str
    accepted_shares: int
    rejected_shares: int
    phi_guidance_effective: bool
    meta_learning_event_present: bool
    current_strategy: str
    telemetry_source: str


router = APIRouter(prefix="/api/v1/unified", tags=["unified-mining"])


def _state_view(engine: UnifiedMiningEngine) -> Dict[str, Any]:
    state = engine.get_unified_state()
    return state


@router.get(
    "/status",
    response_model=UnifiedEngineStatus,
    dependencies=[Depends(require_mining_read)],
)
async def get_unified_status() -> UnifiedEngineStatus:
    """Get current unified mining engine status from measured engine state."""

    state = _state_view(get_engine())
    runtime_state = state.get("state", {}) or {}
    consciousness = state.get("consciousness", {}) or {}
    return UnifiedEngineStatus(
        timestamp=datetime.now(timezone.utc).isoformat(),
        engine=str(state.get("engine", "PYTHIA/PULVINI Unified Mining Engine")),
        version=str(state.get("version", "unknown")),
        consciousness_coherence=float(runtime_state.get("phi_coherence") or 0.0),
        consciousness_regime=str(
            runtime_state.get("integration_regime")
            or consciousness.get("integration_regime")
            or "unknown"
        ),
        accepted_shares=int(runtime_state.get("accepted_shares") or 0),
        rejected_shares=int(runtime_state.get("rejected_shares") or 0),
        effective_search_dim_bits=float(runtime_state.get("effective_search_dim_bits") or 0.0),
        m32_domains_covered=int(runtime_state.get("m32_domains_covered") or 0),
        working_set_compression=float(runtime_state.get("working_set_compression") or 0.0),
        verifier_backend=str(runtime_state.get("verifier_backend") or "unknown"),
        verifier_metal_available=bool(runtime_state.get("verifier_metal_available")),
        telemetry_source="canonical_unified_engine_state",
    )


@router.post(
    "/analyze/resonance",
    response_model=BatchResonanceResponse,
    dependencies=[Depends(require_mining_read)],
)
async def analyze_batch_resonance(req: BatchResonanceRequest) -> BatchResonanceResponse:
    """Analyze φ resonance for a batch of candidate nonces."""

    analysis: List[NonceResonanceAnalysis] = []
    for nonce in req.nonces:
        candidate = int(nonce) % (2**32)
        action = yang_mills_action(candidate)
        analysis.append(
            NonceResonanceAnalysis(
                nonce=candidate,
                phi_resonance_strength=phi_resonance(candidate),
                yang_mills_action=action,
                is_mass_gate_passed=soft_mass_gap_gate(action),
                voronoi_domain=voronoi_domain(candidate),
            )
        )

    phi_scores = [a.phi_resonance_strength for a in analysis]
    gate_pass = sum(1 for a in analysis if a.is_mass_gate_passed) / len(analysis)
    return BatchResonanceResponse(
        timestamp=datetime.now(timezone.utc).isoformat(),
        count=len(analysis),
        mean_phi_resonance=sum(phi_scores) / len(phi_scores),
        max_phi_resonance=max(phi_scores),
        min_phi_resonance=min(phi_scores),
        mass_gate_pass_rate=gate_pass,
        analysis=analysis,
        telemetry_source="hendrix_phi_solver_primitives",
    )


@router.post("/share-result", dependencies=[Depends(require_mining_control)])
async def report_share_result(
    req: ShareResultRequest,
    _payload: TokenPayload = Depends(require_mining_control),
) -> Dict[str, Any]:
    """Report a pool share result for meta-learning feedback.

    This endpoint records an operator/pool-sourced share outcome. It does not
    claim pool-side acceptance unless the caller reports it from the live pool
    evidence surface.
    """

    engine = get_engine()
    await engine.on_share_result(
        {
            "nonce": req.nonce,
            "job_id": req.job_id,
            "pool_difficulty": req.pool_difficulty,
            "strategy_used": req.strategy_used,
            "phi_resonance_score": req.phi_resonance_score,
            "error_code": req.error_code,
            "error_msg": req.error_msg,
        },
        accepted=req.accepted,
    )
    state = engine.get_unified_state().get("state", {}) or {}
    return {
        "status": "recorded",
        "nonce": req.nonce,
        "accepted": req.accepted,
        "accepted_shares": state.get("accepted_shares", 0),
        "rejected_shares": state.get("rejected_shares", 0),
        "telemetry_source": "canonical_unified_engine_feedback_loop",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get(
    "/metrics",
    response_model=AIMetrics,
    dependencies=[Depends(require_mining_read)],
)
async def get_ai_metrics() -> AIMetrics:
    """Get AI optimization metrics from canonical engine state."""

    state = _state_view(get_engine()).get("state", {}) or {}
    accepted = int(state.get("accepted_shares") or 0)
    rejected = int(state.get("rejected_shares") or 0)
    return AIMetrics(
        timestamp=datetime.now(timezone.utc).isoformat(),
        accepted_shares=accepted,
        rejected_shares=rejected,
        phi_guidance_effective=str(state.get("strategy", "")).startswith("phi"),
        meta_learning_event_present=state.get("meta_learning_event") is not None,
        current_strategy=str(state.get("strategy") or "unknown"),
        telemetry_source="canonical_unified_engine_state",
    )


@router.get("/health", dependencies=[Depends(require_mining_read)])
async def unified_health() -> Dict[str, Any]:
    """Health check for unified mining engine."""

    try:
        state = _state_view(get_engine())
        runtime_state = state.get("state", {}) or {}
        return {
            "status": "healthy",
            "engine": state.get("engine"),
            "consciousness_coherence": runtime_state.get("phi_coherence", 0.0),
            "consciousness_regime": runtime_state.get("integration_regime", "unknown"),
            "verifier_backend": runtime_state.get("verifier_backend", "unknown"),
            "telemetry_source": "canonical_unified_engine_state",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
