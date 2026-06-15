"""
HENDRIX-Φ + PULVINI Unified Mining Engine REST API
===================================================

Unified Mining API provides:
  - Real-time mining engine state and coherence metrics
  - Nonce resonance analysis (batch)
  - AI optimization metrics and meta-learning feedback
  - Share result tracking and learning loop integration
  - Consciousness regime monitoring (SINGULAR/DISTRIBUTED/FRAGMENTED)
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

try:
    from pythia_mining.phi_unified_mining_engine import UnifiedMiningEngine
    from pythia_mining.consciousness_engine import ConsciousnessEngine
    from pythia_mining.ai_optimizer import AIOptimizer
except ImportError as e:
    raise RuntimeError(f"Failed to import mining engines: {e}")

# Global engine
_engine: Optional[UnifiedMiningEngine] = None

def get_engine() -> UnifiedMiningEngine:
    """Lazy-initialize unified mining engine."""
    global _engine
    if _engine is None:
        consciousness = ConsciousnessEngine()
        optimizer = AIOptimizer()
        _engine = UnifiedMiningEngine(consciousness=consciousness, optimizer=optimizer)
    return _engine

# Models
class UnifiedEngineStatus(BaseModel):
    """Current unified mining engine status."""
    timestamp: str
    consciousness_coherence: float = Field(..., ge=0.0, le=1.0)
    consciousness_regime: str
    ai_learning_rate: float
    total_iterations: int
    accepted_shares: int
    rejected_shares: int
    mean_phi_resonance: float

class NonceResonanceAnalysis(BaseModel):
    """Analysis of a single nonce."""
    nonce: int
    phi_resonance_strength: float = Field(..., ge=0.0, le=1.0)
    yang_mills_action: float
    is_mass_gate_passed: bool
    voronoi_domain: int

class BatchResonanceRequest(BaseModel):
    """Request to analyze nonces."""
    nonces: List[int] = Field(..., min_items=1, max_items=10000)

class BatchResonanceResponse(BaseModel):
    """Response with resonance analysis."""
    timestamp: str
    count: int
    mean_phi_resonance: float
    max_phi_resonance: float
    min_phi_resonance: float
    mass_gate_pass_rate: float
    analysis: List[NonceResonanceAnalysis]

class ShareResultRequest(BaseModel):
    """Report a share result."""
    nonce: int
    accepted: bool
    pool_difficulty: float = 1.0

class AIMetrics(BaseModel):
    """AI optimization metrics."""
    timestamp: str
    learning_iterations: int
    phi_guidance_effective: bool
    last_5_share_rate: float

# Router
router = APIRouter(prefix="/api/v1/unified", tags=["unified-mining"])

@router.get("/status", response_model=UnifiedEngineStatus)
async def get_unified_status() -> UnifiedEngineStatus:
    """Get current unified mining engine status."""
    engine = get_engine()
    state = engine.get_unified_state()

    return UnifiedEngineStatus(
        timestamp=datetime.now(timezone.utc).isoformat(),
        consciousness_coherence=state.get("consciousness_coherence", 0.0),
        consciousness_regime=state.get("consciousness_regime", "UNKNOWN"),
        ai_learning_rate=state.get("learning_rate", 0.0),
        total_iterations=state.get("total_iterations", 0),
        accepted_shares=state.get("accepted_shares", 0),
        rejected_shares=state.get("rejected_shares", 0),
        mean_phi_resonance=state.get("mean_phi_resonance", 0.0),
    )

@router.post("/analyze/resonance", response_model=BatchResonanceResponse)
async def analyze_batch_resonance(req: BatchResonanceRequest) -> BatchResonanceResponse:
    """Analyze phi resonance for a batch of nonces."""
    engine = get_engine()
    
    analysis: List[NonceResonanceAnalysis] = []
    for nonce in req.nonces:
        try:
            resonance = engine.analyze_nonce_resonance([nonce])
            if resonance and "nonces" in resonance:
                for item in resonance["nonces"]:
                    analysis.append(NonceResonanceAnalysis(
                        nonce=item.get("nonce", nonce),
                        phi_resonance_strength=item.get("phi_resonance", 0.0),
                        yang_mills_action=item.get("yang_mills_action", 0.0),
                        is_mass_gate_passed=item.get("mass_gate_passed", False),
                        voronoi_domain=item.get("voronoi_domain", 0),
                    ))
        except Exception:
            pass
    
    phi_scores = [a.phi_resonance_strength for a in analysis]
    mean_phi = sum(phi_scores) / len(phi_scores) if phi_scores else 0.0
    max_phi = max(phi_scores) if phi_scores else 0.0
    min_phi = min(phi_scores) if phi_scores else 0.0
    gate_pass = sum(1 for a in analysis if a.is_mass_gate_passed) / len(analysis) if analysis else 0.0

    return BatchResonanceResponse(
        timestamp=datetime.now(timezone.utc).isoformat(),
        count=len(analysis),
        mean_phi_resonance=mean_phi,
        max_phi_resonance=max_phi,
        min_phi_resonance=min_phi,
        mass_gate_pass_rate=gate_pass,
        analysis=analysis,
    )

@router.post("/share-result")
async def report_share_result(req: ShareResultRequest) -> Dict[str, Any]:
    """Report a share result for meta-learning feedback."""
    engine = get_engine()
    
    await engine.on_share_result(
        nonce=req.nonce,
        accepted=req.accepted,
        difficulty=req.pool_difficulty,
    )

    return {
        "status": "recorded",
        "nonce": req.nonce,
        "accepted": req.accepted,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

@router.get("/metrics", response_model=AIMetrics)
async def get_ai_metrics() -> AIMetrics:
    """Get AI optimization metrics."""
    engine = get_engine()
    state = engine.get_unified_state()

    return AIMetrics(
        timestamp=datetime.now(timezone.utc).isoformat(),
        learning_iterations=state.get("optimizer_iterations", 0),
        phi_guidance_effective=state.get("phi_effective", False),
        last_5_share_rate=state.get("recent_acceptance_rate", 0.0),
    )

@router.get("/health")
async def unified_health() -> Dict[str, Any]:
    """Health check for unified mining engine."""
    try:
        engine = get_engine()
        state = engine.get_unified_state()
        return {
            "status": "healthy",
            "consciousness_coherence": state.get("consciousness_coherence", 0.0),
            "consciousness_regime": state.get("consciousness_regime", "UNKNOWN"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
