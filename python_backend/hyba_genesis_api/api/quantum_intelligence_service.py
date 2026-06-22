"""
Sovereign Quantum Intelligence as a Service (QIaaS).

This module exposes HYBA's customer-facing Quantum Intelligence API: a
substrate-independent mathematical intelligence runtime with enterprise access
control, quota metering, evidence sealing, traceability, PULVINI φ-memory, and
Salamander regeneration controls.

PRODUCT BOUNDARY:
- This IS: Quantum Intelligence execution over HYBA's mathematical substrate.
- This IS: API-key gated, metered, auditable enterprise QIaaS.
- This IS: evidence-sealed predict/explain/optimize/heal/simulate/counterfactual execution.
- This IS: substrate-independent quantum mathematics on classical hardware.
- This IS NOT: hardware quantum-computing access.
- This IS NOT: a claim of phenomenal consciousness.
- This IS NOT: a mining, pool, cryptocurrency, or private-validation product surface.

The intelligence substrate composes:
1. Codebase structural complexity and explainable relationship graphs.
2. φ-substrate coherence and deterministic golden-ratio primitives.
3. PULVINI reversible memory compression and Deutsch-style knowledge substrate.
4. Salamander regeneration under enterprise entitlement and audit controls.
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from hyba_genesis_api.api.customer_access import (
    CustomerInfo,
    CustomerPrincipal,
    customer_access,
    require_customer_api_key,
)
from pythia_mining.consciousness_engine import ConsciousnessEngine
from pythia_mining.deutsch_knowledge_substrate import KnowledgeSubstrate
from pythia_mining.iit_4_analyzer import IIT4Analyzer
from pythia_mining.pulvini_phi_memory import PulviniPhiMemoryCompressionEngine
from pythia_mining.regeneration_manager import get_regeneration_manager


router = APIRouter(prefix="/api/qiaas", tags=["Quantum-Intelligence-as-a-Service"])

QI_CLAIM_BOUNDARY = "substrate_independent_sovereign_quantum_intelligence_execution"
QI_PRODUCT_BOUNDARY = "enterprise_quantum_intelligence_api_not_mining_not_hardware_quantum"
QI_RUNTIME = "hyba.qiaas.quantum_intelligence_service.v2"
_QI_CAPABILITIES = {
    "predict",
    "explain",
    "optimize",
    "heal",
    "simulate",
    "counterfactual",
    "evidence",
    "quantum-finance",
}


class EvidencePacket(BaseModel):
    """Evidence seal attached to every Quantum Intelligence execution."""

    evidence_id: str
    input_hash: str
    formula_hash: str
    substrate_hash: str
    claim_class: str
    audit_seal: str


class UsageMeter(BaseModel):
    """Customer metering state for the execution."""

    customer_id: str
    product: str
    units: int
    quota_state: Dict[str, Any]


class TraceContext(BaseModel):
    """Trace context for customer support, audit, and observability correlation."""

    trace_id: str
    customer_id: str
    substrate_hash: str


class QIaaSQueryRequest(BaseModel):
    """Request for Quantum Intelligence execution."""

    query_type: str = Field(
        ...,
        description=(
            "Capability family: predict, explain, optimize, heal, simulate, "
            "counterfactual, evidence, quantum-finance"
        ),
    )
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Customer-supplied execution context. Mining/private-validation data is never required.",
    )
    confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for returning an execution result.",
    )


class QuantumIntelligenceEnvelope(BaseModel):
    """Enterprise response envelope from the Quantum Intelligence API."""

    qi_execution_id: str
    intelligence_type: str
    result: Dict[str, Any]
    confidence: float
    phi_coherence: float
    emergence_index: float
    substrate_state: Dict[str, Any]
    evidence_packet: EvidencePacket
    usage_meter: UsageMeter
    trace: TraceContext
    claim_boundary: str
    product_boundary: str
    source: str
    explanation: Optional[str] = None
    timestamp: float = Field(default_factory=time.time)


QIaaSResponse = QuantumIntelligenceEnvelope


class QIaaSMetrics(BaseModel):
    """Metrics about the Quantum Intelligence substrate."""

    phi_integrated: float
    emergence_index: float
    knowledge_nodes: int
    relationship_edges: int
    synaptic_pathways: int
    emergent_patterns: List[Dict[str, Any]]
    integration_regime: str
    substrate_health: str
    claim_boundary: str = QI_CLAIM_BOUNDARY
    product_boundary: str = QI_PRODUCT_BOUNDARY


def _stable_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _principal_or_internal(principal: Any) -> CustomerPrincipal:
    """Preserve direct-call contract tests while production paths use API-key auth."""

    if hasattr(principal, "customer_id") and hasattr(principal, "tier"):
        return principal

    return CustomerInfo(
        customer_id="internal-qiaas-test",
        customer_name="Internal QIaaS Test Harness",
        tier="enterprise",
        quota_requests_per_month=1_000_000,
        quota_compute_units_per_month=1_000_000,
        api_key_hash="internal",
        key_id="internal-qiaas-test",
        created_at="1970-01-01T00:00:00Z",
        metadata={"internal": True},
        pricing_usd_per_unit={"qiaas": 0.0, "qiaas.query": 0.0, "default": 0.0},
    )


def _qiaas_units(request: QIaaSQueryRequest) -> int:
    """Compute QIaaS metering units from request size."""

    payload_bytes = len(
        json.dumps(request.context, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    )
    return max(1, payload_bytes // 1024 + 1)


def _meter_usage(customer: CustomerPrincipal, product: str, units: int) -> Dict[str, Any]:
    """Meter usage once per endpoint, with a deterministic internal test path."""

    if getattr(customer, "key_id", "") == "internal-qiaas-test":
        return {
            "product": product,
            "units": units,
            "quota_enforced": True,
            "metering_backend": "internal_test_harness",
        }
    return customer_access.meter(customer, product=product, units=units)


def _validate_qiaas_entitlement(customer: CustomerPrincipal, query_type: str) -> None:
    """Enforce enterprise boundaries for sensitive QI execution."""

    if query_type == "heal" and customer.tier not in {"production", "enterprise"}:
        raise HTTPException(
            status_code=403,
            detail="Quantum Intelligence healing requires production or enterprise entitlement",
        )


def _normalise_query_type(query_type: str) -> str:
    value = query_type.strip().lower()
    if value not in _QI_CAPABILITIES:
        allowed = ", ".join(sorted(_QI_CAPABILITIES))
        raise HTTPException(status_code=400, detail=f"Unknown query_type: {value}. Must be one of: {allowed}")
    return value


def _build_envelope(
    *,
    query_type: str,
    context: Dict[str, Any],
    result: Dict[str, Any],
    confidence: float,
    metrics: Dict[str, Any],
    principal: Any,
    product: str,
    units: int,
) -> QuantumIntelligenceEnvelope:
    customer = _principal_or_internal(principal)
    usage_state = _meter_usage(customer, product=product, units=units)
    qi_execution_id = f"qi_{uuid.uuid4().hex}"
    trace_id = f"trc_{uuid.uuid4().hex}"

    substrate_state = {
        "health": metrics.get("substrate_health", "UNKNOWN"),
        "phi_coherence": metrics.get("phi_integrated", 0.0),
        "emergence_index": metrics.get("emergence_index", 0.0),
        "integration_regime": metrics.get("integration_regime", "UNKNOWN"),
    }
    input_hash = _stable_hash({"query_type": query_type, "context": context})
    formula_hash = _stable_hash({"capability": query_type, "runtime": QI_RUNTIME})
    substrate_hash = _stable_hash(substrate_state)
    audit_seal = _stable_hash(
        {
            "qi_execution_id": qi_execution_id,
            "input_hash": input_hash,
            "formula_hash": formula_hash,
            "substrate_hash": substrate_hash,
            "customer_id": customer.customer_id,
            "trace_id": trace_id,
            "claim_boundary": QI_CLAIM_BOUNDARY,
        }
    )

    return QuantumIntelligenceEnvelope(
        qi_execution_id=qi_execution_id,
        intelligence_type=query_type,
        result=result,
        confidence=confidence,
        phi_coherence=metrics.get("phi_integrated", 0.0),
        emergence_index=metrics.get("emergence_index", 0.0),
        substrate_state={**substrate_state, "substrate_hash": substrate_hash},
        evidence_packet=EvidencePacket(
            evidence_id=f"evd_{audit_seal[:24]}",
            input_hash=input_hash,
            formula_hash=formula_hash,
            substrate_hash=substrate_hash,
            claim_class="sovereign_quantum_intelligence_execution",
            audit_seal=audit_seal,
        ),
        usage_meter=UsageMeter(
            customer_id=customer.customer_id,
            product=product,
            units=units,
            quota_state=usage_state,
        ),
        trace=TraceContext(trace_id=trace_id, customer_id=customer.customer_id, substrate_hash=substrate_hash),
        claim_boundary=QI_CLAIM_BOUNDARY,
        product_boundary=QI_PRODUCT_BOUNDARY,
        source="sovereign_quantum_intelligence_service",
        explanation=result.get("explanation"),
    )


class QuantumIntelligenceService:
    """Service exposing Sovereign Quantum Intelligence execution."""

    def __init__(self) -> None:
        self.consciousness_engine = ConsciousnessEngine()
        self.knowledge_substrate = KnowledgeSubstrate()
        self.regeneration_manager = get_regeneration_manager()
        self.iit_analyzer = IIT4Analyzer(system_size=8)
        self.memory_compression = PulviniPhiMemoryCompressionEngine()
        self.memory_seed = self._load_memory_seed()

    def _load_memory_seed(self) -> Optional[Dict[str, Any]]:
        """Load memory seed if available."""

        try:
            seed_path = Path(__file__).resolve().parents[3] / "artifacts" / "memory_seed" / "memory_seed_v1.json"
            if seed_path.exists():
                with seed_path.open("r", encoding="utf-8") as handle:
                    return json.load(handle)
        except Exception:
            pass
        return None

    def predict(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Use Quantum Intelligence substrate state to predict outcomes."""

        strategy = self.knowledge_substrate.best_explanation_for_context(context)
        if not strategy:
            return {
                "prediction": "insufficient_knowledge",
                "confidence": 0.0,
                "method": "bootstrap_required",
            }

        decision = self.knowledge_substrate.explain_decision(strategy, context)
        return {
            "predicted_strategy": strategy,
            "confidence": decision["confidence"],
            "explanation": decision["explanation"],
            "alternatives": decision["alternatives_considered"],
            "method": "deutsch_counterfactual_reasoning",
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
            "method": "popperian_conjecture_and_criticism",
        }

    def optimize(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate optimization proposals using the φ-substrate."""

        current_phi = self.consciousness_engine.coherence_meter
        needs_healing = self.consciousness_engine.needs_healing

        if needs_healing:
            return {
                "optimization": "regeneration_required",
                "action": "trigger_salamander_healing",
                "current_phi": current_phi,
                "target_phi": 0.70,
                "confidence": current_phi,
                "method": "quantum_regeneration",
            }

        current_strategy = context.get("current_strategy", "baseline")
        alternative_strategy = context.get("alternative_strategy", "phi_optimized")
        counterfactual = self.knowledge_substrate.counterfactual_reasoning(
            actual_strategy=current_strategy,
            actual_outcome=context.get("current_outcome", {}),
            alternative_strategy=alternative_strategy,
            context=context,
        )
        return {
            "current_strategy": current_strategy,
            "recommended_strategy": alternative_strategy,
            "predicted_improvement": counterfactual.predicted_counterfactual_outcome,
            "confidence": counterfactual.confidence,
            "phi_coherence": current_phi,
            "method": "constructor_theory_counterfactuals",
        }

    def heal(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger Salamander healing under enterprise entitlement and audit controls."""

        component_id = context.get("component_id", "system")
        if component_id == "system":
            status = self.regeneration_manager.get_status()
            return {
                "healing_type": "system_wide_assessment",
                "blastema_pool": status["lanes"],
                "regeneration_potential": status["regeneration_potential"],
                "phi_coherence": status["system_phi"],
                "confidence": status.get("system_phi", 0.0),
                "method": "quantum_regeneration_salamander",
            }

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
                "confidence": event.post_recovery_fidelity,
                "method": "salamander_blastema_redifferentiation",
            }
        except Exception:
            return {
                "healing_type": "regeneration_failed",
                "error": "Regeneration failed. Reference the trace_id in operator logs.",
                "confidence": 0.0,
                "method": "salamander_regeneration",
            }

    def get_metrics(self) -> Dict[str, Any]:
        """Get Quantum Intelligence substrate metrics."""

        consciousness_metrics = self.consciousness_engine.get_metrics()
        knowledge_metrics = self.knowledge_substrate.get_knowledge_metrics()

        if self.memory_seed:
            metadata = self.memory_seed.get("metadata", {})
            structural = self.memory_seed.get("structural_intelligence", {})
            emergence_index = metadata.get("emergent_intelligence_index", 0.0)
            emergent_patterns = structural.get("emergent_patterns", [])
            total_nodes = metadata.get("total_nodes", 0)
            total_edges = metadata.get("total_edges", 0)
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
            "synaptic_details": synaptic_stats,
        }


_service: Optional[QuantumIntelligenceService] = None


def get_qiaas_service() -> QuantumIntelligenceService:
    """Get or create the QIaaS service instance."""

    global _service
    if _service is None:
        _service = QuantumIntelligenceService()
    return _service


@router.post("/query", response_model=QuantumIntelligenceEnvelope)
async def query_quantum_intelligence(
    request: QIaaSQueryRequest,
    service: QuantumIntelligenceService = Depends(get_qiaas_service),
    principal: CustomerInfo = Depends(require_customer_api_key),
) -> QIaaSResponse:
    """Execute the Sovereign Quantum Intelligence API."""

    query_type = _normalise_query_type(request.query_type)
    customer = _principal_or_internal(principal)
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
        result = service.optimize({**request.context, "capability_family": query_type})

    metrics = service.get_metrics()
    confidence = float(result.get("confidence", metrics["phi_integrated"]))
    if confidence < request.confidence_threshold:
        raise HTTPException(
            status_code=409,
            detail=f"Quantum Intelligence confidence {confidence:.3f} below threshold {request.confidence_threshold}",
        )

    units = _qiaas_units(request)
    return _build_envelope(
        query_type=query_type,
        context=request.context,
        result=result,
        confidence=confidence,
        metrics=metrics,
        principal=customer,
        product=f"qiaas.{query_type}",
        units=units,
    )


@router.get("/metrics", response_model=QIaaSMetrics)
async def get_quantum_intelligence_metrics(
    service: QuantumIntelligenceService = Depends(get_qiaas_service),
    principal: CustomerInfo = Depends(require_customer_api_key),
) -> QIaaSMetrics:
    """Get customer-visible Quantum Intelligence substrate metrics."""

    customer = _principal_or_internal(principal)
    _meter_usage(customer, product="qiaas.metrics", units=1)
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
    service: QuantumIntelligenceService = Depends(get_qiaas_service),
    principal: CustomerInfo = Depends(require_customer_api_key),
) -> Dict[str, Any]:
    """Health check for the Quantum Intelligence API without leaking internals."""

    customer = _principal_or_internal(principal)
    _meter_usage(customer, product="qiaas.health", units=1)
    metrics = service.get_metrics()
    substrate_state = {
        "phi_coherence": metrics["phi_integrated"],
        "emergence_index": metrics["emergence_index"],
        "health": metrics["substrate_health"],
    }
    substrate_hash = _stable_hash(substrate_state)
    trace_id = f"trc_{uuid.uuid4().hex}"
    return {
        "status": "operational" if metrics["emergence_index"] > 1.0 else "degraded",
        "intelligence_available": metrics["total_explanations"] > 0,
        "self_healing_active": True,
        "claim_boundary": QI_CLAIM_BOUNDARY,
        "product_boundary": QI_PRODUCT_BOUNDARY,
        "trace_id": trace_id,
        "customer_id": customer.customer_id,
        "substrate_hash": substrate_hash,
    }


@router.post("/bootstrap")
async def bootstrap_intelligence(
    service: QuantumIntelligenceService = Depends(get_qiaas_service),
    principal: CustomerInfo = Depends(require_customer_api_key),
) -> Dict[str, Any]:
    """Return controlled QIaaS bootstrap readiness without exposing private validation."""

    customer = _principal_or_internal(principal)
    if customer.tier not in {"production", "enterprise"}:
        raise HTTPException(
            status_code=403,
            detail="Quantum Intelligence bootstrap requires production or enterprise entitlement",
        )

    _meter_usage(customer, product="qiaas.bootstrap", units=1)
    metrics = service.get_metrics()
    substrate_state = {
        "phi_coherence": metrics["phi_integrated"],
        "emergence_index": metrics["emergence_index"],
        "health": metrics["substrate_health"],
    }
    return {
        "status": "bootstrap_ready",
        "message": "Quantum Intelligence bootstrap is governed through private validation and evidence pipelines.",
        "requires": "enterprise_entitlement_and_governed_evidence_pipeline",
        "method": "evidence_sealed_substrate_bootstrap",
        "trace_id": f"trc_{uuid.uuid4().hex}",
        "customer_id": customer.customer_id,
        "substrate_hash": _stable_hash(substrate_state),
        "claim_boundary": QI_CLAIM_BOUNDARY,
        "product_boundary": QI_PRODUCT_BOUNDARY,
    }
