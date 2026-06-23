"""HYBA Autonomy Fabric core contract.

This module makes autonomy a production contract rather than isolated product
copy.  Every client-facing autonomous surface is represented through the same
observe -> reason -> recommend -> simulate -> approve -> execute -> audit ->
learn grammar, with evidence seals and explicit approval boundaries.

The implementation is deliberately deterministic and dependency-light so it can
be imported by API routes, tests, docs tooling, and offline sovereign/customer
review workflows without starting PYTHIA daemons or contacting external systems.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

AUTONOMY_CHAIN: Tuple[str, ...] = (
    "observe",
    "reason",
    "recommend",
    "simulate",
    "approve",
    "execute",
    "audit",
    "learn",
)

PLATFORM_BOUNDARY = {
    "name": "HYBA_FULLSTACK",
    "posture": "ubiquitous_bounded_autonomy",
    "client_promise": "HYBA continuously observes, reasons, recommends, simulates, requests approval where required, executes safe actions, audits outcomes, and learns from evidence.",
    "risk_rule": "High-impact or externally material actions must be approval-gated; low-risk read-only or advisory actions may run autonomously but still emit audit evidence.",
}

RISK_APPROVAL_MATRIX: Dict[str, Dict[str, Any]] = {
    "low": {
        "approval_required": False,
        "execution_mode": "autonomous_with_audit",
        "examples": ["refresh telemetry", "summarise evidence", "draft advisory brief"],
    },
    "medium": {
        "approval_required": True,
        "execution_mode": "approval_gated",
        "examples": ["change optimisation weights", "rebalance non-destructive workflow priorities"],
    },
    "high": {
        "approval_required": True,
        "execution_mode": "dual_control_or_operator_approval",
        "examples": ["start/stop production mining", "privileged admin mutation", "customer data export"],
    },
}


@dataclass(frozen=True)
class AutonomySurface:
    """One domain where HYBA intelligence must be visible and useful."""

    surface_id: str
    domain: str
    client_value: str
    state: str
    observation: str
    insight: str
    recommendation: str
    risk: str
    confidence: float
    available_actions: Tuple[str, ...]
    approval_required: bool
    evidence: Tuple[str, ...]
    audit_event: str
    fallback_state: str = "fail_closed_with_evidence_gap_visible"

    def __post_init__(self) -> None:
        if self.risk not in RISK_APPROVAL_MATRIX:
            raise ValueError(f"unsupported risk tier: {self.risk}")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        expected_approval = bool(RISK_APPROVAL_MATRIX[self.risk]["approval_required"])
        if self.approval_required != expected_approval:
            raise ValueError(
                f"approval boundary mismatch for {self.surface_id}: "
                f"risk={self.risk} requires approval={expected_approval}"
            )
        if not self.available_actions:
            raise ValueError(f"surface {self.surface_id} must expose at least one action")
        if not self.evidence:
            raise ValueError(f"surface {self.surface_id} must expose evidence")

    def to_dict(self) -> Dict[str, Any]:
        payload = {
            "surface_id": self.surface_id,
            "domain": self.domain,
            "client_value": self.client_value,
            "state": self.state,
            "observation": self.observation,
            "insight": self.insight,
            "recommendation": self.recommendation,
            "risk": self.risk,
            "confidence": self.confidence,
            "available_actions": list(self.available_actions),
            "approval_required": self.approval_required,
            "execution_mode": RISK_APPROVAL_MATRIX[self.risk]["execution_mode"],
            "evidence": list(self.evidence),
            "audit_event": self.audit_event,
            "fallback_state": self.fallback_state,
        }
        payload["evidence_seal"] = _seal(payload)
        return payload


SURFACES: Tuple[AutonomySurface, ...] = (
    AutonomySurface(
        surface_id="client_onboarding_diagnostic",
        domain="client_success",
        client_value="Compresses discovery from weeks of interviews into an evidence-backed operating diagnostic.",
        state="ready",
        observation="Client context, sector, data source posture, deployment constraints, and governance needs are normalized into one onboarding map.",
        insight="HYBA can identify the fastest credible path from raw client state to verifiable value.",
        recommendation="Run onboarding diagnostic, then generate an executive opportunity brief and integration backlog.",
        risk="low",
        confidence=0.93,
        available_actions=("run_onboarding_diagnostic", "draft_client_brief", "map_data_sources"),
        approval_required=False,
        evidence=("hyba_ciaas.ingestion.DataSourceSpec", "docs/CENTRAL_DATA_INGESTION.md", "tests/test_central_data_ingestion.py"),
        audit_event="autonomy.client_onboarding.diagnostic_ready",
    ),
    AutonomySurface(
        surface_id="opportunity_scan",
        domain="client_value_creation",
        client_value="Finds cost, risk, revenue, and operational leverage opportunities before a human analyst has built the first spreadsheet.",
        state="ready",
        observation="Telemetry, ingestion quality, runtime health, and product-boundary proof windows can be scanned together.",
        insight="HYBA is strongest when recommendations cite both business impact and proof evidence.",
        recommendation="Produce ranked next-best-actions with risk, confidence, expected impact, and proof references.",
        risk="low",
        confidence=0.91,
        available_actions=("rank_next_best_actions", "generate_evidence_backed_brief", "prepare_roi_hypotheses"),
        approval_required=False,
        evidence=("python_backend/hyba_genesis_api/core/proof_surfaces.py", "docs/evidence/VERIFICATION_SURFACES.md"),
        audit_event="autonomy.client_value.opportunity_scan_ready",
    ),
    AutonomySurface(
        surface_id="sovereign_runtime_controls",
        domain="deployment_governance",
        client_value="Lets regulated clients run HYBA in cloud, private-cloud, on-prem, sovereign-site, or air-gapped modes without changing the intelligence contract.",
        state="approval_gated",
        observation="Deployment posture, data residency, source restrictions, usage quotas, and admin mutations are policy-evaluated locally.",
        insight="Sovereign deployment credibility depends on local enforcement and append-only evidence, not vendor promises.",
        recommendation="Require operator approval for privileged mutations and preserve local audit seals for every decision.",
        risk="high",
        confidence=0.89,
        available_actions=("evaluate_policy", "ingest_with_controls", "export_audit_chain"),
        approval_required=True,
        evidence=("python_backend/hyba_ciaas/sovereign_runtime.py", "tests/test_sovereign_deployment_control_plane.py"),
        audit_event="autonomy.deployment_governance.policy_gate_ready",
    ),
    AutonomySurface(
        surface_id="proof_and_claim_interrogation",
        domain="buyer_confidence",
        client_value="Turns extraordinary claims into queryable endpoints, invariants, tests, artifacts, and evidence seals.",
        state="ready",
        observation="Proof windows expose platform surfaces, runtime evidence, invariants, claim tiers, and executable commands.",
        insight="The correct sales motion is not belief; it is interrogation and reproducibility.",
        recommendation="Expose proof status beside every material recommendation and fail closed when evidence is unavailable.",
        risk="low",
        confidence=0.96,
        available_actions=("open_proof_window", "summarise_evidence_packet", "emit_evidence_seal"),
        approval_required=False,
        evidence=("/api/proofs", "/api/proofs/audit-ledger", "/api/v1/intelligence/extraordinary-claims/evidence"),
        audit_event="autonomy.buyer_confidence.proof_window_ready",
    ),
    AutonomySurface(
        surface_id="production_execution_guardrails",
        domain="operations",
        client_value="Allows HYBA to recommend and simulate operational changes while preventing silent high-risk execution.",
        state="approval_gated",
        observation="Production mining, admin mutations, funding disbursement, security shield, and autonomous control calls are destructive or high-impact command families.",
        insight="Market-grade autonomy means useful action, not uncontrolled action.",
        recommendation="Simulate first, require explicit approval for high-risk commands, then audit outcome and rollback metadata.",
        risk="high",
        confidence=0.9,
        available_actions=("simulate_operational_change", "request_operator_approval", "execute_after_approval", "record_audit_event"),
        approval_required=True,
        evidence=("artifacts/frontend_api_command_manifest.json", "tests/test_apiClient_intelligence_autonomy.test.ts", "tests/e2e/command-safety.spec.ts"),
        audit_event="autonomy.operations.guardrail_ready",
    ),
    AutonomySurface(
        surface_id="pythia_self_optimization",
        domain="intelligence_runtime",
        client_value="Keeps HYBA improving itself inside bounded startup/runtime loops while preserving operator evidence.",
        state="bounded_runtime_ready",
        observation="Startup self-healing and reflexive heartbeat can activate bounded boot-time improvement cycles.",
        insight="Self-optimization is valuable when every proposal, application, and cooldown is traceable.",
        recommendation="Keep self-healing bounded by environment flags, persist reports, and surface recommendations to clients as evidence-backed advisories.",
        risk="medium",
        confidence=0.88,
        available_actions=("boot_self_heal_and_optimize", "persist_autonomy_report", "summarise_reflexive_proposals"),
        approval_required=True,
        evidence=("hyba_genesis_api.main._activate_startup_self_healing", "hyba_genesis_api.core.autonomy_persistence", "tests/test_local_launch_script_contract.py"),
        audit_event="autonomy.intelligence_runtime.self_optimization_bounded",
    ),
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical(value: Mapping[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _seal(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _surface_index() -> Dict[str, AutonomySurface]:
    return {surface.surface_id: surface for surface in SURFACES}


def list_autonomy_surfaces() -> List[Dict[str, Any]]:
    """Return every production autonomy surface as a sealed dictionary."""

    return [surface.to_dict() for surface in SURFACES]


def build_autonomy_fabric_snapshot(context: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    """Return the canonical market-facing autonomy fabric snapshot."""

    context = dict(context or {})
    surfaces = list_autonomy_surfaces()
    surface_count = len(surfaces)
    approval_gated = [surface for surface in surfaces if surface["approval_required"]]
    autonomous = [surface for surface in surfaces if not surface["approval_required"]]
    invariant_results = {
        "operating_chain_complete": tuple(AUTONOMY_CHAIN) == ("observe", "reason", "recommend", "simulate", "approve", "execute", "audit", "learn"),
        "surface_count_minimum_met": surface_count >= 6,
        "every_surface_has_client_value": all(bool(surface["client_value"]) for surface in surfaces),
        "every_surface_has_recommendation": all(bool(surface["recommendation"]) for surface in surfaces),
        "every_surface_has_action": all(bool(surface["available_actions"]) for surface in surfaces),
        "every_surface_has_evidence": all(bool(surface["evidence"]) for surface in surfaces),
        "high_risk_actions_approval_gated": all(
            surface["approval_required"] for surface in surfaces if surface["risk"] == "high"
        ),
        "low_risk_actions_can_run_autonomously": all(
            not surface["approval_required"] for surface in surfaces if surface["risk"] == "low"
        ),
        "confidence_values_bounded": all(0 <= float(surface["confidence"]) <= 1 for surface in surfaces),
    }
    snapshot: Dict[str, Any] = {
        "schema_version": "hyba.autonomy_fabric.v1",
        "generated_at": _utc_now(),
        "platform_boundary": dict(PLATFORM_BOUNDARY),
        "operating_chain": list(AUTONOMY_CHAIN),
        "risk_approval_matrix": RISK_APPROVAL_MATRIX,
        "surface_count": surface_count,
        "autonomous_surface_count": len(autonomous),
        "approval_gated_surface_count": len(approval_gated),
        "surfaces": surfaces,
        "client_service_loop": {
            "observe": "collect client context, telemetry, evidence, and constraints",
            "reason": "classify opportunity, risk, confidence, and proof boundaries",
            "recommend": "produce next-best-actions tied to client value",
            "simulate": "estimate impact and failure modes before action",
            "approve": "gate high-impact actions through explicit operator or dual control",
            "execute": "perform safe actions or approved high-risk actions only",
            "audit": "emit evidence seals and immutable audit metadata",
            "learn": "feed outcomes into bounded PYTHIA/self-optimization loops",
        },
        "invariant_results": invariant_results,
        "all_invariants_passed": all(invariant_results.values()),
        "context": context,
    }
    snapshot["evidence_seal"] = _seal({k: v for k, v in snapshot.items() if k != "evidence_seal"})
    return snapshot


def simulate_autonomy_action(surface_id: str, action: str, context: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    """Deterministically simulate an autonomy action before execution."""

    surfaces = _surface_index()
    if surface_id not in surfaces:
        raise KeyError(f"unknown autonomy surface: {surface_id}")
    surface = surfaces[surface_id]
    if action not in surface.available_actions:
        raise ValueError(f"action {action!r} is not available for {surface_id}")
    context = dict(context or {})
    payload: Dict[str, Any] = {
        "schema_version": "hyba.autonomy_simulation.v1",
        "generated_at": _utc_now(),
        "surface_id": surface_id,
        "action": action,
        "risk": surface.risk,
        "approval_required": surface.approval_required,
        "execution_mode": RISK_APPROVAL_MATRIX[surface.risk]["execution_mode"],
        "expected_client_value": surface.client_value,
        "recommendation": surface.recommendation,
        "evidence": list(surface.evidence),
        "audit_event": f"{surface.audit_event}.simulation",
        "will_execute_without_approval": not surface.approval_required,
        "context": context,
    }
    payload["evidence_seal"] = _seal(payload)
    return payload


def request_autonomy_execution(
    surface_id: str,
    action: str,
    *,
    approval_id: Optional[str] = None,
    context: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Return an execution decision; high-risk actions fail closed without approval."""

    simulation = simulate_autonomy_action(surface_id, action, context=context)
    approved = bool(approval_id)
    if simulation["approval_required"] and not approved:
        decision = "approval_required"
        executable = False
    else:
        decision = "approved_for_execution" if approved else "autonomous_execution_allowed"
        executable = True
    payload: Dict[str, Any] = {
        "schema_version": "hyba.autonomy_execution_decision.v1",
        "generated_at": _utc_now(),
        "surface_id": surface_id,
        "action": action,
        "decision": decision,
        "executable": executable,
        "approval_id": approval_id,
        "simulation": simulation,
        "audit_event": simulation["audit_event"].replace(".simulation", ".execution_decision"),
    }
    payload["evidence_seal"] = _seal(payload)
    return payload


def build_client_intelligence_brief(client_name: str = "client") -> Dict[str, Any]:
    """Return a board-safe brief showing how HYBA AI serves a client."""

    snapshot = build_autonomy_fabric_snapshot({"client_name": client_name})
    ranked = sorted(snapshot["surfaces"], key=lambda surface: surface["confidence"], reverse=True)
    payload: Dict[str, Any] = {
        "schema_version": "hyba.client_intelligence_brief.v1",
        "generated_at": _utc_now(),
        "client_name": client_name,
        "bluf": "HYBA serves clients by converting data, telemetry, evidence, and governance constraints into approval-safe autonomous recommendations and audited actions.",
        "top_recommendations": [
            {
                "surface_id": surface["surface_id"],
                "client_value": surface["client_value"],
                "recommendation": surface["recommendation"],
                "risk": surface["risk"],
                "approval_required": surface["approval_required"],
                "evidence_seal": surface["evidence_seal"],
            }
            for surface in ranked[:5]
        ],
        "snapshot_seal": snapshot["evidence_seal"],
        "audit_posture": "Every recommendation is tied to evidence and every execution path emits an audit decision.",
    }
    payload["evidence_seal"] = _seal(payload)
    return payload


def assert_autonomy_ubiquity(snapshot: Mapping[str, Any]) -> None:
    """Raise when the autonomy fabric is not market-ready."""

    invariants = dict(snapshot.get("invariant_results") or {})
    failed = sorted(name for name, passed in invariants.items() if not passed)
    if failed:
        raise AssertionError(f"autonomy fabric invariant failure: {', '.join(failed)}")
    if not snapshot.get("all_invariants_passed"):
        raise AssertionError("autonomy fabric did not pass all invariants")


__all__ = [
    "AUTONOMY_CHAIN",
    "PLATFORM_BOUNDARY",
    "RISK_APPROVAL_MATRIX",
    "AutonomySurface",
    "assert_autonomy_ubiquity",
    "build_autonomy_fabric_snapshot",
    "build_client_intelligence_brief",
    "list_autonomy_surfaces",
    "request_autonomy_execution",
    "simulate_autonomy_action",
]
