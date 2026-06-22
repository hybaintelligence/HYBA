"""
Quantum Intelligence as a Service (QIaaS)

Customer-facing quantum-intelligence query surface for HYBA's substrate-
independent mathematical intelligence. QIaaS is a commercial product surface;
private validation/mining telemetry is never exposed as a customer product.

CLAIM BOUNDARY:
- This IS: bounded predict/explain/optimize/heal intelligence over the HYBA substrate.
- This IS: substrate-independent quantum mathematics on classical hardware.
- This IS: API-key gated, metered, auditable QIaaS execution.
- This IS NOT: hardware quantum computing.
- This IS NOT: a claim of phenomenal consciousness.
- This IS NOT: a mining, pool, or cryptocurrency product.

The intelligence substrate composes:
1. Codebase structural complexity and explainable relationship graphs.
2. φ-substrate coherence and deterministic golden-ratio primitives.
3. PULVINI reversible memory compression and Deutsch-style knowledge substrate.
4. Salamander regeneration and bounded self-healing controls.
"""

from __future__ import annotations

import time
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from hyba_genesis_api.api.customer_access import (
    CustomerPrincipal,
    customer_access,
    require_customer_api_key,
)
from pythia_mining.consciousness_engine import ConsciousnessEngine
from pythia_mining.deutsch_knowledge_substrate import KnowledgeSubstrate
from pythia_mining.regeneration_manager import get_regeneration_manager
from pythia_mining.iit_4_analyzer import IIT4Analyzer
from pythia_mining.pulvini_phi_memory import PulviniPhiMemoryCompressionEngine


router = APIRouter(prefix="/api/qiaas", tags=["Quantum-Intelligence-as-a-Service"])


# Request/Response Models

class QIaaSQueryRequest(BaseModel):
    """Request for quantum intelligence inference."""

    query_type: str = Field(
        ...,
        description="Type of intelligence query: 'predict', 'explain', 'optimize', 'heal'"
    )
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Context data for the query"
    )
    confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for response"
    )


class QIaaSResponse(BaseModel):
    """Response from quantum intelligence."""

    intelligence_type: str
    result: Dict[str, Any]
    confidence: float
    phi_coherence: float
    emergence_index: float
    source: str
    explanation: Optional[str] = None
    timestamp: float = Field(default_factory=time.time)
    claim_boundary: str = "bounded_quantum_intelligence_on_classical_hardware"
    product_boundary: str = "qiaas_public_product_surface_not_mining"
    usage_meter: Optional[Dict[str, Any]] = None


class QIaaSMetrics(BaseModel):
    """Metrics about the quantum intelligence substrate."""

    phi_integrated: float
    emergence_index: float
    knowledge_nodes: int
    relationship_edges: int
    synaptic_pathways: int
    emergent_patterns: List[Dict[str, Any]]
    integration_regime: str
    substrate_health: str
    claim_boundary: str = "diagnostic_substrate_metrics_not_hardware_quantum_or_consciousness_claim"


# Service Implementation

class QuantumIntelligenceService:
    """Service exposing bounded quantum intelligence."""

    def __init__(self):
        self.consciousness_engine = ConsciousnessEngine()
        self.knowledge_substrate = KnowledgeSubstrate()
        self.regeneration_manager = get_regeneration_manager()
        self.iit_analyzer = IIT4Analyzer(system_size=8)
        self.memory_compression = PulviniPhiMemoryCompressionEngine()
        self.memory_seed = self._load_memory_seed()

    def _load_memory_seed(self) -> Optional[Dict[str, Any]]:
        """Load memory seed if available."""
        try:
            import json
            from pathlib import Path

            seed_path = Path(__file__).parent.parent.parent.parent / "artifacts" / "memory_seed" / "memory_seed_v1.json"
            if seed_path.exists():
                with open(seed_path, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return None

    def predict(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Use emergent intelligence to predict outcomes."""

        strategy = self.knowledge_substrate.best_explanation_for_context(context)

        if not strategy:
            return {
                "prediction": "insufficient_knowledge",
                "confidence": 0.0,
                "method": "bootstrap_required"
            }

        decision = self.knowledge_substrate.explain_decision(strategy, context)

        return {
            "predicted_strategy": strategy,
            "confidence": decision["confidence"],
            "explanation": decision["explanation"],
            "alternatives": decision["alternatives_considered"],
            "method": "deutsch_counterfactual_reasoning"
        }

    def explain(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate explanations using Deutsch epistemology."""

        strategy_id = context.get("strategy_id", "unknown")

        if strategy_id == "unknown":
            strategy_id = self.knowledge_substrate.best_explanation_for_context(context) or "unknown"

        explanation = self.knowledge_substrate.explain_decision(strategy_id, context)

        return {
            "strategy": strategy_id,
            "explanation": explanation["explanation"],
            "confidence": explanation["confidence"],
            "times_tested": explanation.get("times_tested", 0),
            "alternatives": explanation.get("alternatives_considered", []),
            "method": "popperian_conjecture_and_criticism"
        }

    def optimize(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate optimization proposals using φ-substrate."""

        current_phi = self.consciousness_engine.coherence_meter
        needs_healing = self.consciousness_engine.needs_healing

        if needs_healing:
            return {
                "optimization": "regeneration_required",
                "action": "trigger_salamander_healing",
                "current_phi": current_phi,
                "target_phi": 0.70,
                "method": "quantum_regeneration"
            }

        current_strategy = context.get("current_strategy", "baseline")
        alternative_strategy = context.get("alternative_strategy", "phi_optimized")

        counterfactual = self.knowledge_substrate.counterfactual_reasoning(
            actual_strategy=current_strategy,
            actual_outcome=context.get("current_outcome", {}),
            alternative_strategy=alternative_strategy,
            context=context
        )

        return {
            "current_strategy": current_strategy,
            "recommended_strategy": alternative_strategy,
            "predicted_improvement": counterfactual.predicted_counterfactual_outcome,
            "confidence": counterfactual.confidence,
            "phi_coherence": current_phi,
            "method": "constructor_theory_counterfactuals"
        }

    def heal(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger bounded Salamander healing for degraded components."""

        component_id = context.get("component_id", "system")

        if component_id == "system":
            status = self.regeneration_manager.get_status()
            return {
                "healing_type": "system_wide_assessment",
                "blastema_pool": status["lanes"],
                "regeneration_potential": status["regeneration_potential"],
                "phi_coherence": status["system_phi"],
                "method": "quantum_regeneration_salamander"
            }
        else:
            lane_id = int(context.get("lane_id", 0))

            try:
                import asyncio
                event = asyncio.run(self.regeneration_manager.trigger_regeneration(lane_id))

                return {
                    "healing_type": "component_regeneration",
                    "component": component_id,
                    "lane_id": lane_id,
                    "status": event.status,
                    "fidelity": event.post_recovery_fidelity,
                    "scar_free": not event.scarring_detected,
                    "method": "salamander_blastema_redifferentiation"
                }
            except Exception as e:
                return {
                    "healing_type": "regeneration_failed",
                    "error": str(e),
                    "method": "salamander_regeneration"
                }

    def get_metrics(self) -> Dict[str, Any]:
        """Get quantum intelligence substrate metrics."""

        consciousness_metrics = self.consciousness_engine.get_metrics()
        knowledge_metrics = self.knowledge_substrate.get_knowledge_metrics()

        if self.memory_seed:
            emergence_index = self.memory_seed['metadata']['emergent_intelligence_index']
            emergent_patterns = self.memory_seed['structural_intelligence']['emergent_patterns']
            total_nodes = self.memory_seed['metadata']['total_nodes']
            total_edges = self.memory_seed['metadata']['total_edges']
        else:
            emergence_index = 0.0
            emergent_patterns = []
            total_nodes = 0
            total_edges = 0

        synaptic_stats = self.consciousness_engine.get_synaptic_statistics()

        return {
            "phi_integrated": consciousness_metrics.get("integrated_information", 0.0),
            "emergence_index": emergence_index,
            "knowledge_nodes": total_nodes,
            "relationship_edges": total_edges,
            "synaptic_pathways": len(synaptic_stats.get("emergent_pathways", [])),
            "emergent_patterns": emergent_patterns,
            "integration_regime": consciousness_metrics.get("integration_regime", "UNKNOWN"),
            "substrate_health": "OPERATIONAL" if emergence_index > 1.0 else "DEGRADED",
            "total_explanations": knowledge_metrics.get("total_explanations", 0),
            "counterfactual_models": knowledge_metrics.get("counterfactual_models", 0),
            "synaptic_details": synaptic_stats
        }


# Global service instance
_service: Optional[QuantumIntelligenceService] = None


def get_qiaas_service() -> QuantumIntelligenceService:
    """Get or create QIaaS service instance."""
    global _service
    if _service is None:
        _service = QuantumIntelligenceService()
    return _service


def _qiaas_units(request: QIaaSQueryRequest) -> int:
    """Compute conservative QIaaS metering units from request context size."""
    context_bytes = len(repr(request.context).encode("utf-8"))
    return max(1, context_bytes // 1024 + 1)


def _validate_qiaas_entitlement(customer: CustomerPrincipal, query_type: str) -> None:
    """Enforce tier boundaries for sensitive QIaaS operations."""
    if query_type == "heal" and customer.tier not in {"production", "enterprise"}:
        raise HTTPException(
            status_code=403,
            detail="QIaaS healing operations require production or enterprise tier",
        )


# API Endpoints

@router.post("/query", response_model=QIaaSResponse)
async def query_quantum_intelligence(
    request: QIaaSQueryRequest,
    customer: CustomerPrincipal = Depends(require_customer_api_key),
    service: QuantumIntelligenceService = Depends(get_qiaas_service),
) -> QIaaSResponse:
    """Query the bounded quantum-intelligence substrate.

    Customer-facing QIaaS is API-key authenticated, quota-metered, and bounded by
    the claim boundary declared in this module. Mining/private-validation data is
    not exposed as a product surface.
    """

    query_type = request.query_type.lower()
    _validate_qiaas_entitlement(customer, query_type)

    if query_type == "predict":
        result = service.predict(request.context)
    elif query_type == "explain":
        result = service.explain(request.context)
    elif query_type == "optimize":
        result = service.optimize(request.context)
    elif query_type == "heal":
        result = service.heal(request.context)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown query_type: {query_type}. Must be: predict, explain, optimize, heal"
        )

    metrics = service.get_metrics()
    confidence = result.get("confidence", metrics["phi_integrated"])

    if confidence < request.confidence_threshold:
        raise HTTPException(
            status_code=409,
            detail=f"Intelligence confidence {confidence:.3f} below threshold {request.confidence_threshold}"
        )

    usage_meter = customer_access.meter(
        customer,
        product=f"qiaas.{query_type}",
        units=_qiaas_units(request),
    )

    return QIaaSResponse(
        intelligence_type=query_type,
        result=result,
        confidence=confidence,
        phi_coherence=metrics["phi_integrated"],
        emergence_index=metrics["emergence_index"],
        source="metered_quantum_intelligence_service",
        explanation=result.get("explanation"),
        usage_meter=usage_meter,
    )


@router.get("/metrics", response_model=QIaaSMetrics)
async def get_quantum_intelligence_metrics(
    customer: CustomerPrincipal = Depends(require_customer_api_key),
    service: QuantumIntelligenceService = Depends(get_qiaas_service),
) -> QIaaSMetrics:
    """Get bounded metrics about the quantum-intelligence substrate."""

    customer_access.meter(customer, product="qiaas.metrics", units=1)
    metrics = service.get_metrics()

    return QIaaSMetrics(
        phi_integrated=metrics["phi_integrated"],
        emergence_index=metrics["emergence_index"],
        knowledge_nodes=metrics["knowledge_nodes"],
        relationship_edges=metrics["relationship_edges"],
        synaptic_pathways=metrics["synaptic_pathways"],
        emergent_patterns=metrics["emergent_patterns"],
        integration_regime=metrics["integration_regime"],
        substrate_health=metrics["substrate_health"],
    )


@router.get("/health")
async def qiaas_health_check(
    service: QuantumIntelligenceService = Depends(get_qiaas_service)
) -> Dict[str, Any]:
    """Minimal public health check for QIaaS.

    Detailed QIaaS metrics require customer API-key authentication.
    """

    metrics = service.get_metrics()

    return {
        "status": "operational" if metrics["emergence_index"] > 1.0 else "degraded",
        "intelligence_available": metrics["total_explanations"] > 0,
        "claim_boundary": "bounded_quantum_intelligence_on_classical_hardware",
        "product_boundary": "qiaas_public_product_surface_not_mining",
    }


@router.post("/bootstrap")
async def bootstrap_intelligence(
    customer: CustomerPrincipal = Depends(require_customer_api_key),
) -> Dict[str, Any]:
    """Return QIaaS bootstrap boundary information.

    QIaaS bootstrapping is controlled through private validation and governed
    evidence pipelines. Customer API access does not expose mining or pool data.
    """

    customer_access.meter(customer, product="qiaas.bootstrap_status", units=1)
    return {
        "status": "controlled_bootstrap_boundary",
        "message": "QIaaS is bootstrapped from governed substrate evidence; private validation telemetry is not exposed as a product surface.",
        "requires": "governed_evidence_pipeline",
        "method": "bounded_substrate_memory_and_phi_coherence",
    }
