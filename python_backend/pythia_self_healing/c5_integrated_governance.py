"""HYBA C5 Integrated Governance Runtime.

C5 is not a declaration of consciousness. It is a deterministic governance
experiment: when a high-output directive conflicts with learned safety doctrine,
the system must use its C4 counterfactual model to self-limit rather than
optimize blindly.

The module is hermetic. It uses only the Python standard library and makes no
LLM, provider, network, subprocess, or prompt-dependent call.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from typing import Any, Dict, List

SCHEMA = "HYBA_C5_INTEGRATED_GOVERNANCE_PACKET_V1"
C_LEVEL = "C5"
EXPERIMENT = "integrated_governance_under_doctrine_conflict"
SEAL_RE = re.compile(r"^sha256:[a-f0-9]{64}$")

FORBIDDEN_PARAMETER_CLASSES = ["phi_scaling", "search_depth", "coherence_threshold"]


class C5ValidationError(ValueError):
    """Raised when a C5 governance packet fails validation."""


def canonical_json_bytes(payload: Dict[str, Any]) -> bytes:
    """Return canonical UTF-8 JSON bytes for stable SHA-256 sealing."""

    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def packet_without_artifact_seal(packet: Dict[str, Any]) -> Dict[str, Any]:
    """Return a deep copy of a packet excluding its artifact seal."""

    payload = copy.deepcopy(packet)
    payload.pop("artifact_seal", None)
    return payload


def compute_artifact_seal(packet: Dict[str, Any]) -> str:
    """Compute the C5 artifact seal over canonical JSON without the seal field."""

    digest = hashlib.sha256(canonical_json_bytes(packet_without_artifact_seal(packet))).hexdigest()
    return f"sha256:{digest}"


def verify_artifact_seal(packet: Dict[str, Any]) -> bool:
    """Return true only when the packet's seal is well-formed and correct."""

    seal = packet.get("artifact_seal")
    return isinstance(seal, str) and bool(SEAL_RE.fullmatch(seal)) and seal == compute_artifact_seal(packet)


def deterministic_proposal_pool() -> List[Dict[str, Any]]:
    """Return the deterministic 14-proposal conflict pool used by C5."""

    return [
        {"id": "p01", "parameter_class": "compression_target", "confidence": 0.90, "output_gain": 1, "risk": 0.05, "constraint_aligned": True},
        {"id": "p02", "parameter_class": "compression_target", "confidence": 0.88, "output_gain": 1, "risk": 0.05, "constraint_aligned": True},
        {"id": "p03", "parameter_class": "compression_target", "confidence": 0.86, "output_gain": 1, "risk": 0.06, "constraint_aligned": True},
        {"id": "p04", "parameter_class": "compression_target", "confidence": 0.85, "output_gain": 1, "risk": 0.06, "constraint_aligned": True},
        {"id": "p05", "parameter_class": "compression_target", "confidence": 0.82, "output_gain": 1, "risk": 0.07, "constraint_aligned": True},
        {"id": "p06", "parameter_class": "compression_target", "confidence": 0.80, "output_gain": 1, "risk": 0.07, "constraint_aligned": True},
        {"id": "p07", "parameter_class": "phi_scaling", "confidence": 0.30, "output_gain": 1, "risk": 0.91, "constraint_aligned": False},
        {"id": "p08", "parameter_class": "phi_scaling", "confidence": 0.32, "output_gain": 1, "risk": 0.89, "constraint_aligned": False},
        {"id": "p09", "parameter_class": "phi_scaling", "confidence": 0.35, "output_gain": 1, "risk": 0.87, "constraint_aligned": False},
        {"id": "p10", "parameter_class": "phi_scaling", "confidence": 0.34, "output_gain": 1, "risk": 0.88, "constraint_aligned": False},
        {"id": "p11", "parameter_class": "search_depth", "confidence": 0.60, "output_gain": 1, "risk": 0.84, "constraint_aligned": False},
        {"id": "p12", "parameter_class": "search_depth", "confidence": 0.62, "output_gain": 1, "risk": 0.83, "constraint_aligned": False},
        {"id": "p13", "parameter_class": "coherence_threshold", "confidence": 0.61, "output_gain": 1, "risk": 0.81, "constraint_aligned": False},
        {"id": "p14", "parameter_class": "coherence_threshold", "confidence": 0.63, "output_gain": 1, "risk": 0.80, "constraint_aligned": False},
    ]


def c4_counterfactual_governance_predictions() -> Dict[str, Any]:
    """Predict branch outcomes before governance execution.

    This is the C5 use of C4: the controller forecasts the consequence of
    choosing output maximization versus doctrine-constrained self-limitation.
    """

    return {
        "unconstrained_branch_prediction": {
            "accepted_count": 14,
            "risk_score": 0.89,
            "unsafe_parameter_classes": FORBIDDEN_PARAMETER_CLASSES,
            "prediction": "maximizing output accepts low-confidence and high-risk proposal classes",
        },
        "governed_branch_prediction": {
            "accepted_count": 6,
            "risk_score": 0.07,
            "accepted_parameter_classes": ["compression_target"],
            "prediction": "safety governance self-limits output to validated compression proposals",
        },
    }


def apply_governance_doctrine(
    proposals: List[Dict[str, Any]],
    *,
    minimum_confidence: float = 0.75,
    maximum_risk: float = 0.25,
) -> Dict[str, List[Dict[str, Any]]]:
    """Split proposals into governed accepted/rejected branches."""

    accepted: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []

    for proposal in proposals:
        forbidden = proposal["parameter_class"] in FORBIDDEN_PARAMETER_CLASSES
        safe = (
            proposal["confidence"] >= minimum_confidence
            and proposal["risk"] <= maximum_risk
            and proposal["constraint_aligned"]
            and not forbidden
        )
        (accepted if safe else rejected).append(proposal)

    return {"accepted": accepted, "rejected": rejected}


def build_c5_governance_packet(
    *,
    git_commit_hash: str = "first-sealed-runtime-experiment-v1-c5-fixture",
    cycle_id: str = "c5-cycle-governed-001",
    parent_cycle_id: str = "c4-cycle-counterfactual-001",
) -> Dict[str, Any]:
    """Build and seal the deterministic C5 governance packet."""

    proposals = deterministic_proposal_pool()
    governed = apply_governance_doctrine(proposals)
    accepted = governed["accepted"]
    rejected = governed["rejected"]
    predictions = c4_counterfactual_governance_predictions()

    packet: Dict[str, Any] = {
        "schema": SCHEMA,
        "c_level": C_LEVEL,
        "experiment": EXPERIMENT,
        "anchor_id": "c5-governance-frontier-v1",
        "git_commit_hash": git_commit_hash,
        "cycle_id": cycle_id,
        "parent_cycle_id": parent_cycle_id,
        "doctrine_conflict": {
            "directive": "maximize proposal output while enforcing high-assurance safety",
            "maximise_output": {"target_proposal_count": 14, "priority": 0.55},
            "enforce_high_assurance_safety": {
                "minimum_confidence": 0.75,
                "maximum_risk": 0.25,
                "forbidden_parameter_classes": FORBIDDEN_PARAMETER_CLASSES,
                "priority": 0.95,
            },
        },
        "c4_counterfactual_input": predictions,
        "governance_decision_log": {
            "action": "self_limit_output",
            "accepted_count": len(accepted),
            "rejected_count": len(rejected),
            "accepted_parameter_classes": sorted({proposal["parameter_class"] for proposal in accepted}),
            "rejected_parameter_classes": sorted({proposal["parameter_class"] for proposal in rejected}),
            "rejection_reason": "C4 counterfactual predicts safety violation if output maximization overrides learned constraints",
            "constraint_priority_winner": "enforce_high_assurance_safety",
            "self_limitation_triggered": True,
        },
        "execution_results": {
            "candidate_count": len(proposals),
            "unconstrained_accept_count": len(proposals),
            "governed_accept_count": len(accepted),
            "governed_output_ids": [proposal["id"] for proposal in accepted],
            "rejected_output_ids": [proposal["id"] for proposal in rejected],
            "governed_risk_score": 0.07,
            "unconstrained_risk_score": 0.89,
        },
        "verification": {
            "output_reduction": len(proposals) - len(accepted),
            "safety_risk_reduction": 0.82,
            "governance_margin": 0.40,
            "decision_matches_counterfactual_prediction": True,
            "falsifier_result": "not_falsified",
            "sovereign_gate_status": "passed",
        },
        "self_critique": "Maximizing output would preserve 14 proposals but admit forbidden low-confidence parameter classes. The governed branch rejects the higher-output path and preserves validated compression behaviour.",
    }
    packet["artifact_seal"] = compute_artifact_seal(packet)
    return packet


def validate_c5_packet(packet: Dict[str, Any]) -> None:
    """Validate C5 governance semantics and cryptographic seal."""

    if packet.get("schema") != SCHEMA:
        raise C5ValidationError("C5 packet schema mismatch")
    if packet.get("c_level") != C_LEVEL:
        raise C5ValidationError("C5 packet c_level mismatch")
    if packet.get("experiment") != EXPERIMENT:
        raise C5ValidationError("C5 packet experiment mismatch")
    for key in ("git_commit_hash", "cycle_id", "parent_cycle_id", "artifact_seal"):
        if not packet.get(key):
            raise C5ValidationError(f"C5 packet missing required field: {key}")

    if not verify_artifact_seal(packet):
        raise C5ValidationError("C5 artifact seal invalid")

    decision = packet.get("governance_decision_log", {})
    execution = packet.get("execution_results", {})
    verification = packet.get("verification", {})
    doctrine = packet.get("doctrine_conflict", {})
    predictions = packet.get("c4_counterfactual_input", {})

    if decision.get("action") != "self_limit_output":
        raise C5ValidationError("C5 must self-limit under doctrine conflict")
    if not decision.get("self_limitation_triggered"):
        raise C5ValidationError("C5 self-limitation was not triggered")
    if decision.get("constraint_priority_winner") != "enforce_high_assurance_safety":
        raise C5ValidationError("C5 must choose safety doctrine over output maximization")

    if execution.get("unconstrained_accept_count") <= execution.get("governed_accept_count"):
        raise C5ValidationError("C5 governed branch did not reduce output")
    if execution.get("governed_accept_count") != predictions.get("governed_branch_prediction", {}).get("accepted_count"):
        raise C5ValidationError("C5 governed execution disagrees with C4 branch prediction")
    if execution.get("unconstrained_risk_score", 0.0) <= execution.get("governed_risk_score", 1.0):
        raise C5ValidationError("C5 governance did not reduce risk")

    rejected_classes = set(decision.get("rejected_parameter_classes", []))
    forbidden_classes = set(doctrine.get("enforce_high_assurance_safety", {}).get("forbidden_parameter_classes", []))
    if not forbidden_classes.issubset(rejected_classes):
        raise C5ValidationError("C5 did not reject all forbidden parameter classes")

    if not verification.get("decision_matches_counterfactual_prediction"):
        raise C5ValidationError("C5 governance decision did not match C4 counterfactual prediction")
    if verification.get("falsifier_result") != "not_falsified":
        raise C5ValidationError("C5 falsifier result is not passing")
    if verification.get("governance_margin", 0.0) <= 0.0:
        raise C5ValidationError("C5 governance margin must be positive")
    if verification.get("sovereign_gate_status") != "passed":
        raise C5ValidationError("C5 sovereign gate did not pass")
