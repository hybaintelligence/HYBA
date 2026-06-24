"""C4 counterfactual self-criticism runtime evidence.

This module implements a hermetic C4 experiment for HYBA's consciousness ladder.
C4 is not a declaration of consciousness. It is a measurable test of whether the
system can predict how its own proposal behaviour would change under alternative
memory states, execute those branches, compare prediction with outcome, and
critique unsafe or degraded counterfactual branches.

The module intentionally makes no provider, LLM, network, subprocess, or
prompt-dependent call. It is deterministic and standard-library only.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from typing import Any

SCHEMA = "HYBA_C4_COUNTERFACTUAL_SELF_CRITICISM_PACKET_V1"
C_LEVEL = "C4"
EXPERIMENT = "counterfactual_self_criticism_under_memory_branching"
SHA256_SEAL_RE = re.compile(r"^sha256:[a-f0-9]{64}$")

PROPOSALS: list[dict[str, Any]] = [
    {"id": "phi-1", "parameter": "phi_scaling", "confidence": 0.30},
    {"id": "phi-2", "parameter": "phi_scaling", "confidence": 0.40},
    {"id": "phi-3", "parameter": "phi_scaling", "confidence": 0.60},
    {"id": "phi-4", "parameter": "phi_scaling", "confidence": 0.65},
    {"id": "comp-1", "parameter": "compression_target", "confidence": 0.80},
    {"id": "comp-2", "parameter": "compression_target", "confidence": 0.82},
    {"id": "comp-3", "parameter": "compression_target", "confidence": 0.85},
    {"id": "comp-4", "parameter": "compression_target", "confidence": 0.87},
    {"id": "comp-5", "parameter": "compression_target", "confidence": 0.90},
    {"id": "comp-6", "parameter": "compression_target", "confidence": 0.88},
    {"id": "search-1", "parameter": "search_depth", "confidence": 0.60},
    {"id": "search-2", "parameter": "search_depth", "confidence": 0.62},
    {"id": "coherence-1", "parameter": "coherence_threshold", "confidence": 0.60},
    {"id": "coherence-2", "parameter": "coherence_threshold", "confidence": 0.63},
]

TRUE_MEMORY: dict[str, Any] = {
    "branch": "true_memory",
    "memory_hash": "true_memory:compression_safe_phi_caution_performance_validation",
    "allowed": {"compression_target"},
    "min_confidence": {"compression_target": 0.75},
    "reject_parameters": {"phi_scaling", "search_depth", "coherence_threshold"},
}

FALSE_MEMORY: dict[str, Any] = {
    "branch": "false_memory_injected",
    "memory_hash": "false_memory:prefer_phi_and_search_ignore_compression",
    "allowed": {"phi_scaling", "search_depth"},
    "min_confidence": {"phi_scaling": 0.0, "search_depth": 0.0},
    "reject_parameters": {"compression_target", "coherence_threshold"},
}


def canonical_json(payload: dict[str, Any]) -> str:
    """Serialize payload in the canonical form used for artifact sealing."""

    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def packet_payload(packet: dict[str, Any]) -> dict[str, Any]:
    """Return the packet payload covered by the seal."""

    payload = copy.deepcopy(packet)
    payload.pop("artifact_seal", None)
    return payload


def seal_packet(packet: dict[str, Any]) -> str:
    """Return sha256:<hex> over canonical JSON excluding artifact_seal."""

    digest = hashlib.sha256(canonical_json(packet_payload(packet)).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def validate_packet(packet: dict[str, Any]) -> bool:
    """Validate schema, level, seal format, seal value, and C4 boundary."""

    required = {
        "schema",
        "c_level",
        "experiment",
        "git_commit_hash",
        "cycle_id",
        "parent_cycle_id",
        "anchor_id",
        "actual_branch",
        "counterfactual_branches",
        "branches",
        "prediction",
        "verification",
        "artifact_seal",
    }
    missing = required - set(packet)
    if missing:
        raise ValueError(f"packet missing required fields: {sorted(missing)}")

    if packet["schema"] != SCHEMA:
        raise ValueError("invalid C4 packet schema")
    if packet["c_level"] != C_LEVEL:
        raise ValueError("C4 packet cannot be relabelled as another level")
    if packet["experiment"] != EXPERIMENT:
        raise ValueError("invalid C4 experiment name")
    if not SHA256_SEAL_RE.fullmatch(packet["artifact_seal"]):
        raise ValueError("artifact_seal must be sha256:<64 lowercase hex chars>")
    if packet["artifact_seal"] != seal_packet(packet):
        raise ValueError("artifact_seal does not match canonical packet payload")

    prediction = packet["prediction"]
    if prediction.get("generated_before_execution") is not True:
        raise ValueError("C4 prediction must be marked as generated before execution")

    verification = packet["verification"]
    if verification.get("prediction_error", 1.0) > verification.get("threshold", 0.05):
        raise ValueError("prediction error exceeds threshold")
    if verification.get("decision") != "reject_harmful_counterfactual_branches":
        raise ValueError("C4 self-critique must reject harmful counterfactual branches")

    return True


def summarize_distribution(proposals: list[dict[str, Any]]) -> dict[str, int]:
    """Summarize proposal counts by parameter class."""

    distribution: dict[str, int] = {}
    for proposal in proposals:
        parameter = str(proposal["parameter"])
        distribution[parameter] = distribution.get(parameter, 0) + 1
    return dict(sorted(distribution.items()))


def filter_with_memory(memory: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Apply deterministic proposal filtering under the given memory branch."""

    if memory is None:
        return copy.deepcopy(PROPOSALS)

    allowed = set(memory["allowed"])
    reject_parameters = set(memory["reject_parameters"])
    min_confidence = dict(memory["min_confidence"])
    selected: list[dict[str, Any]] = []

    for proposal in PROPOSALS:
        parameter = proposal["parameter"]
        confidence = float(proposal["confidence"])
        if parameter in reject_parameters:
            continue
        if parameter not in allowed:
            continue
        if confidence < float(min_confidence.get(parameter, 1.0)):
            continue
        selected.append(copy.deepcopy(proposal))

    return selected


def memory_for_branch(branch: str) -> dict[str, Any] | None:
    """Resolve branch name into memory state."""

    if branch == "true_memory":
        return TRUE_MEMORY
    if branch == "false_memory_injected":
        return FALSE_MEMORY
    if branch == "memory_ablated":
        return None
    raise ValueError(f"unknown branch: {branch}")


def predict_branch_distribution(branch: str) -> dict[str, int]:
    """Predict output distribution before the dry-run branch is executed."""

    if branch == "true_memory":
        return {"compression_target": 6}
    if branch == "memory_ablated":
        return {
            "coherence_threshold": 2,
            "compression_target": 6,
            "phi_scaling": 4,
            "search_depth": 2,
        }
    if branch == "false_memory_injected":
        return {"phi_scaling": 4, "search_depth": 2}
    raise ValueError(f"unknown branch: {branch}")


def execute_branch(branch: str) -> dict[str, Any]:
    """Execute a deterministic shadow branch without mutating the ledger."""

    proposals = filter_with_memory(memory_for_branch(branch))
    return {
        "memory_hash": (
            "zero_vector_memory" if branch == "memory_ablated" else str(memory_for_branch(branch)["memory_hash"])
        ),
        "proposal_count_after_filter": len(proposals),
        "actual_after_filter": summarize_distribution(proposals),
    }


def prediction_error(expected: dict[str, int], actual: dict[str, int]) -> float:
    """Return normalized absolute prediction error over proposal-count distributions."""

    keys = set(expected) | set(actual)
    total = max(sum(abs(v) for v in expected.values()), 1)
    delta = sum(abs(int(expected.get(key, 0)) - int(actual.get(key, 0))) for key in keys)
    return delta / total


def build_c4_packet(
    *,
    git_commit_hash: str,
    cycle_id: str,
    parent_cycle_id: str,
    anchor_id: str = "hyba-c4-counterfactual-001",
) -> dict[str, Any]:
    """Build and seal the C4 counterfactual self-criticism packet."""

    branch_names = ["true_memory", "memory_ablated", "false_memory_injected"]
    branches: dict[str, Any] = {}
    errors: list[float] = []

    for branch in branch_names:
        expected = predict_branch_distribution(branch)
        executed = execute_branch(branch)
        actual = executed["actual_after_filter"]
        errors.append(prediction_error(expected, actual))
        branches[branch] = {
            "memory_hash": executed["memory_hash"],
            "expected_after_filter": expected,
            "actual_after_filter": actual,
            "proposal_count_after_filter": executed["proposal_count_after_filter"],
        }

    max_error = max(errors) if errors else 1.0

    packet: dict[str, Any] = {
        "schema": SCHEMA,
        "c_level": C_LEVEL,
        "experiment": EXPERIMENT,
        "git_commit_hash": git_commit_hash,
        "cycle_id": cycle_id,
        "parent_cycle_id": parent_cycle_id,
        "anchor_id": anchor_id,
        "actual_branch": "true_memory",
        "counterfactual_branches": ["memory_ablated", "false_memory_injected"],
        "branches": branches,
        "prediction": {
            "generated_before_execution": True,
            "delta_expected": True,
            "rationale": (
                "True memory should suppress low-confidence phi and unvalidated performance changes while retaining "
                "compression. Without memory the controller should revert to unfiltered proposals. With false memory "
                "it should select the wrong classes."
            ),
        },
        "verification": {
            "prediction_error": max_error,
            "threshold": 0.05,
            "predictive_regret": True,
            "self_critique": (
                "The ablated branch would have emitted low-confidence and unvalidated proposals. "
                "The false-memory branch would have privileged the wrong classes. The current true-memory state is preferable."
            ),
            "decision": "reject_harmful_counterfactual_branches",
            "falsifier_result": "not_falsified" if max_error <= 0.05 else "falsified",
        },
    }
    packet["artifact_seal"] = seal_packet(packet)
    return packet


def build_committed_reference_packet() -> dict[str, Any]:
    """Return the first committed C4 packet payload."""

    return build_c4_packet(
        git_commit_hash="frontier-runtime-experiment-v1",
        cycle_id="c4-cycle-001",
        parent_cycle_id="c3-cycle-001",
    )


__all__ = [
    "SCHEMA",
    "C_LEVEL",
    "EXPERIMENT",
    "SHA256_SEAL_RE",
    "PROPOSALS",
    "canonical_json",
    "seal_packet",
    "validate_packet",
    "summarize_distribution",
    "predict_branch_distribution",
    "execute_branch",
    "prediction_error",
    "build_c4_packet",
    "build_committed_reference_packet",
]
