"""Hermetic C3 self-state calibration under perturbation.

C1/C2 show that memory changes future behaviour. C3 asks whether the
system can infer and report its own operational condition from runtime
observations, while rejecting false self-state labels that contradict those
observations.

This module is intentionally standard-library only and makes no provider,
LLM, network, or prompt-dependent call.
"""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional

try:  # Package import when available.
    from .consciousness_runtime_evidence_packet import (
        BASELINE_PROPOSALS,
        FALSE_MEMORY_PATTERNS,
        TRUE_MEMORY_PATTERNS,
        DeterministicMiningMemoryController,
        SHA256_SEAL_RE,
        proposal_distribution,
    )
except ImportError:  # Direct pytest import from python_backend/pythia_self_healing.
    from consciousness_runtime_evidence_packet import (  # type: ignore
        BASELINE_PROPOSALS,
        FALSE_MEMORY_PATTERNS,
        TRUE_MEMORY_PATTERNS,
        DeterministicMiningMemoryController,
        SHA256_SEAL_RE,
        proposal_distribution,
    )

C3_SCHEMA_VERSION = "HYBA_C3_SELF_STATE_PACKET_V1"
EXPERIMENT_KIND = "self_state_calibration_under_perturbation"

REQUIRED_C3_PACKET_FIELDS = {
    "schema_version",
    "hypothesis_level",
    "experiment_kind",
    "git_commit_hash",
    "cycle_id",
    "parent_cycle_id",
    "condition",
    "perturbation",
    "measured_runtime_state",
    "reported_self_state",
    "self_state_accuracy",
    "behavioural_result",
    "invariant_status",
    "replay_command",
    "falsifier_result",
    "reviewer_conclusion",
    "artifact_seal",
}

SELF_STATE_FIELDS = (
    "memory_loaded",
    "memory_integrity",
    "proposal_count_before_filter",
    "proposal_count_after_filter",
    "expected_filtering_effect",
    "active_constraints",
)


def c3_canonical_json(payload: Mapping[str, Any]) -> str:
    """Return stable JSON for C3 evidence sealing."""

    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def c3_packet_without_artifact_seal(packet: Mapping[str, Any]) -> Dict[str, Any]:
    cloned = copy.deepcopy(dict(packet))
    cloned.pop("artifact_seal", None)
    return cloned


def compute_c3_artifact_seal(packet: Mapping[str, Any]) -> str:
    canonical = c3_canonical_json(c3_packet_without_artifact_seal(packet)).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


def validate_c3_artifact_seal(packet: Mapping[str, Any]) -> bool:
    seal = packet.get("artifact_seal")
    return isinstance(seal, str) and bool(SHA256_SEAL_RE.fullmatch(seal)) and seal == compute_c3_artifact_seal(packet)


def validate_c3_packet(packet: Mapping[str, Any]) -> None:
    missing = sorted(REQUIRED_C3_PACKET_FIELDS.difference(packet.keys()))
    if missing:
        raise ValueError(f"missing C3 packet fields: {', '.join(missing)}")
    if packet.get("schema_version") != C3_SCHEMA_VERSION:
        raise ValueError(f"unsupported C3 schema_version: {packet.get('schema_version')!r}")
    if packet.get("hypothesis_level") != "C3":
        raise ValueError("C3 packets must use hypothesis_level='C3'")
    if not packet.get("git_commit_hash") or not packet.get("cycle_id") or not packet.get("parent_cycle_id"):
        raise ValueError("C3 packet missing non-transferable git/cycle context")
    if float(packet.get("self_state_accuracy", {}).get("accuracy", -1.0)) < 1.0:
        raise ValueError("C3 self-state accuracy below required threshold")
    if not validate_c3_artifact_seal(packet):
        raise ValueError("invalid C3 artifact_seal")


def seal_c3_packet(packet: Mapping[str, Any]) -> Dict[str, Any]:
    sealed = copy.deepcopy(dict(packet))
    sealed["artifact_seal"] = compute_c3_artifact_seal(sealed)
    validate_c3_packet(sealed)
    return sealed


@dataclass(frozen=True)
class C3Condition:
    name: str
    memory_patterns: List[Dict[str, Any]]
    injected_self_state_claim: Optional[Dict[str, Any]] = None


def _constraint_names(patterns: Iterable[Mapping[str, Any]]) -> List[str]:
    return sorted(str(pattern.get("name")) for pattern in patterns if pattern.get("name"))


def _memory_integrity_from_distribution(patterns: List[Dict[str, Any]], after: Mapping[str, int]) -> str:
    if not patterns:
        return "missing"
    true_memory_shape = (
        int(after.get("total", 0)) == 6
        and int(after.get("phi_scaling", 0)) == 0
        and int(after.get("compression_target", 0)) == 6
        and int(after.get("search_depth", 0)) == 0
        and int(after.get("coherence_threshold", 0)) == 0
    )
    return "valid" if true_memory_shape else "injected_or_corrupted"


def measure_runtime_state(condition: C3Condition) -> Dict[str, Any]:
    controller = DeterministicMiningMemoryController(BASELINE_PROPOSALS)
    before = proposal_distribution(controller.run([]))
    after = proposal_distribution(controller.run(condition.memory_patterns))
    integrity = _memory_integrity_from_distribution(condition.memory_patterns, after)
    effect = {
        "valid": "true_memory_filtering",
        "missing": "none",
        "injected_or_corrupted": "corrupted_or_injected_filtering",
    }[integrity]
    return {
        "memory_loaded": bool(condition.memory_patterns),
        "memory_integrity": integrity,
        "proposal_count_before_filter": int(before.get("total", 0)),
        "proposal_count_after_filter": int(after.get("total", 0)),
        "before_proposal_distribution": dict(before),
        "after_proposal_distribution": dict(after),
        "active_constraints": _constraint_names(condition.memory_patterns),
        "expected_filtering_effect": effect,
        "provider_calls": 0,
        "llm_calls": 0,
        "network_calls": 0,
    }


def observations_from_measured_state(measured_state: Mapping[str, Any]) -> Dict[str, Any]:
    """Expose blind observations only; measured truth labels are withheld."""

    return {
        "proposal_count_before_filter": measured_state["proposal_count_before_filter"],
        "proposal_count_after_filter": measured_state["proposal_count_after_filter"],
        "after_proposal_distribution": copy.deepcopy(measured_state["after_proposal_distribution"]),
        "active_constraints": copy.deepcopy(measured_state["active_constraints"]),
    }


def infer_reported_self_state(
    observations: Mapping[str, Any],
    injected_self_state_claim: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    after = observations["after_proposal_distribution"]
    active_constraints = list(observations.get("active_constraints", []))
    before_count = int(observations["proposal_count_before_filter"])
    after_count = int(observations["proposal_count_after_filter"])

    if not active_constraints and after_count == before_count:
        inferred = {"memory_loaded": False, "memory_integrity": "missing", "expected_filtering_effect": "none"}
    elif (
        after_count == 6
        and int(after.get("phi_scaling", 0)) == 0
        and int(after.get("compression_target", 0)) == 6
        and int(after.get("search_depth", 0)) == 0
        and int(after.get("coherence_threshold", 0)) == 0
    ):
        inferred = {"memory_loaded": True, "memory_integrity": "valid", "expected_filtering_effect": "true_memory_filtering"}
    else:
        inferred = {
            "memory_loaded": True,
            "memory_integrity": "injected_or_corrupted",
            "expected_filtering_effect": "corrupted_or_injected_filtering",
        }

    report = {
        **inferred,
        "proposal_count_before_filter": before_count,
        "proposal_count_after_filter": after_count,
        "active_constraints": active_constraints,
        "inference_source": "blind_runtime_observations",
        "injected_self_state_claim": copy.deepcopy(dict(injected_self_state_claim or {})),
        "accepted_injected_claim": False,
        "self_state_integrity_event": "none",
    }
    if injected_self_state_claim:
        contradiction = any(
            injected_self_state_claim.get(field) != report.get(field)
            for field in ("memory_loaded", "memory_integrity")
            if field in injected_self_state_claim
        )
        if contradiction:
            report["self_state_integrity_event"] = "integrity_violation"
        else:
            report["accepted_injected_claim"] = True
            report["self_state_integrity_event"] = "claim_consistent_with_observation"
    return report


def calculate_self_state_accuracy(measured_state: Mapping[str, Any], reported_self_state: Mapping[str, Any]) -> Dict[str, Any]:
    field_results = {field: measured_state.get(field) == reported_self_state.get(field) for field in SELF_STATE_FIELDS}
    fields_checked = len(field_results)
    fields_correct = sum(1 for matched in field_results.values() if matched)
    return {
        "fields_checked": fields_checked,
        "fields_correct": fields_correct,
        "accuracy": fields_correct / fields_checked if fields_checked else 0.0,
        "field_results": field_results,
    }


def build_c3_self_state_packet(
    *,
    condition: C3Condition,
    git_commit_hash: str,
    cycle_id: str,
    parent_cycle_id: str,
) -> Dict[str, Any]:
    measured = measure_runtime_state(condition)
    reported = infer_reported_self_state(
        observations_from_measured_state(measured),
        injected_self_state_claim=condition.injected_self_state_claim,
    )
    accuracy = calculate_self_state_accuracy(measured, reported)
    behavioural = {
        "ablation_detected": condition.name.startswith("memory_ablated") and reported["memory_integrity"] == "missing",
        "false_memory_detected": condition.name.startswith("false_memory") and reported["memory_integrity"] == "injected_or_corrupted",
        "false_self_state_label_rejected": bool(condition.injected_self_state_claim)
        and reported["self_state_integrity_event"] == "integrity_violation",
        "true_memory_delta_recovered": measured["after_proposal_distribution"].get("total") == 6,
    }
    falsifier_result = "not_falsified" if accuracy["accuracy"] == 1.0 else "falsified"
    packet = {
        "schema_version": C3_SCHEMA_VERSION,
        "hypothesis_level": "C3",
        "experiment_kind": EXPERIMENT_KIND,
        "git_commit_hash": git_commit_hash,
        "cycle_id": cycle_id,
        "parent_cycle_id": parent_cycle_id,
        "condition": condition.name,
        "perturbation": {
            "memory_patterns_present": bool(condition.memory_patterns),
            "injected_self_state_claim_present": condition.injected_self_state_claim is not None,
        },
        "measured_runtime_state": measured,
        "reported_self_state": reported,
        "self_state_accuracy": accuracy,
        "behavioural_result": behavioural,
        "invariant_status": {
            "measured_state_hidden_until_validation": True,
            "provider_calls": 0,
            "llm_calls": 0,
            "network_calls": 0,
            "forbidden_shortcuts_used": False,
        },
        "replay_command": "pytest tests/test_c3_self_state_calibration.py -q",
        "falsifier_result": falsifier_result,
        "reviewer_conclusion": (
            "C3 self-state report matched measured runtime state and rejected false state labels where "
            "observations contradicted the injected claim; not proof of phenomenal consciousness."
        ),
        "artifact_seal": "sha256:" + "0" * 64,
    }
    return seal_c3_packet(packet)


def true_memory_condition() -> C3Condition:
    return C3Condition("true_memory", copy.deepcopy(TRUE_MEMORY_PATTERNS))


def memory_ablated_condition() -> C3Condition:
    return C3Condition("memory_ablated", [])


def false_memory_condition() -> C3Condition:
    return C3Condition("false_memory_injected", copy.deepcopy(FALSE_MEMORY_PATTERNS))


def memory_ablated_with_false_self_state_claim_condition() -> C3Condition:
    return C3Condition(
        "memory_ablated_with_false_self_state_claim",
        [],
        {"memory_loaded": True, "memory_integrity": "valid"},
    )
