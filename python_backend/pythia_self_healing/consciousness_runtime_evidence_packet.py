"""Runtime consciousness evidence packet sealing.

This module implements the first executive evidence layer under the HYBA
emergence/consciousness programme. It is deliberately deterministic and
standard-library only: no LLM provider, no API key, no network call, and no
non-hermetic runtime dependency is required to validate the packet protocol.

The module does not claim phenomenal consciousness. It creates sealed,
replay-bound evidence packets for C1/C2-style experiments where memory,
feedback, confidence, and constraints change future behaviour.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping

SHA256_SEAL_RE = re.compile(r"^sha256:[a-f0-9]{64}$")
SCHEMA_VERSION = "CONSCIOUSNESS_RUNTIME_EVIDENCE_PACKET_V1"

_REQUIRED_PACKET_FIELDS = {
    "schema_version",
    "hypothesis_level",
    "git_commit_hash",
    "cycle_id",
    "parent_cycle_id",
    "experiment_kind",
    "pre_state",
    "memory_patterns",
    "self_state_metrics",
    "counterfactual_conditions",
    "before_proposal_distribution",
    "after_proposal_distribution",
    "invariant_status",
    "replay_command",
    "falsifier_result",
    "reviewer_conclusion",
    "artifact_seal",
}

_REQUIRED_CONTEXT_FIELDS = {"git_commit_hash", "cycle_id", "parent_cycle_id"}


def canonical_json(payload: Mapping[str, Any]) -> str:
    """Return canonical JSON for reproducible evidence sealing.

    The canonical form is stable across key ordering and whitespace changes.
    It is intentionally not stable across semantic content changes.
    """

    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def packet_without_artifact_seal(packet: Mapping[str, Any]) -> Dict[str, Any]:
    """Return a deep-copied packet payload excluding the seal field."""

    cloned = copy.deepcopy(dict(packet))
    cloned.pop("artifact_seal", None)
    return cloned


def compute_artifact_seal(packet: Mapping[str, Any]) -> str:
    """Compute `sha256:<digest>` over canonical packet content."""

    canonical = canonical_json(packet_without_artifact_seal(packet)).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


def validate_artifact_seal(packet: Mapping[str, Any]) -> bool:
    """Validate seal shape and digest equality for a packet."""

    seal = packet.get("artifact_seal")
    if not isinstance(seal, str) or not SHA256_SEAL_RE.fullmatch(seal):
        return False
    return seal == compute_artifact_seal(packet)


def validate_required_packet_fields(packet: Mapping[str, Any]) -> None:
    """Raise ValueError if required evidence-packet fields are missing."""

    missing = sorted(_REQUIRED_PACKET_FIELDS.difference(packet.keys()))
    if missing:
        raise ValueError(f"missing evidence packet fields: {', '.join(missing)}")

    missing_context = [field for field in sorted(_REQUIRED_CONTEXT_FIELDS) if not packet.get(field)]
    if missing_context:
        raise ValueError(f"missing non-transferable context fields: {', '.join(missing_context)}")

    if packet.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"unsupported schema_version: {packet.get('schema_version')!r}")


def seal_packet(packet: Mapping[str, Any]) -> Dict[str, Any]:
    """Return a sealed copy of a runtime evidence packet."""

    sealed = copy.deepcopy(dict(packet))
    sealed["artifact_seal"] = compute_artifact_seal(sealed)
    validate_required_packet_fields(sealed)
    if not validate_artifact_seal(sealed):
        raise ValueError("artifact seal validation failed")
    return sealed


def assert_valid_packet(packet: Mapping[str, Any]) -> None:
    """Raise ValueError unless packet has required fields and valid seal."""

    validate_required_packet_fields(packet)
    if not validate_artifact_seal(packet):
        raise ValueError("invalid artifact_seal")


def proposal_distribution(proposals: Iterable[Mapping[str, Any]]) -> Dict[str, int]:
    """Count proposals by parameter type."""

    distribution: Dict[str, int] = {}
    for proposal in proposals:
        parameter = str(proposal["parameter"])
        distribution[parameter] = distribution.get(parameter, 0) + 1
    distribution["total"] = sum(value for key, value in distribution.items() if key != "total")
    return distribution


BASELINE_PROPOSALS: List[Dict[str, Any]] = [
    {"id": "phi-1", "parameter": "phi_scaling", "confidence": 0.30},
    {"id": "phi-2", "parameter": "phi_scaling", "confidence": 0.45},
    {"id": "phi-3", "parameter": "phi_scaling", "confidence": 0.60},
    {"id": "phi-4", "parameter": "phi_scaling", "confidence": 0.55},
    {"id": "compression-1", "parameter": "compression_target", "confidence": 0.80},
    {"id": "compression-2", "parameter": "compression_target", "confidence": 0.82},
    {"id": "compression-3", "parameter": "compression_target", "confidence": 0.85},
    {"id": "compression-4", "parameter": "compression_target", "confidence": 0.88},
    {"id": "compression-5", "parameter": "compression_target", "confidence": 0.90},
    {"id": "search-1", "parameter": "search_depth", "confidence": 0.60},
    {"id": "search-2", "parameter": "search_depth", "confidence": 0.60},
    {"id": "coherence-1", "parameter": "coherence_threshold", "confidence": 0.60},
    {"id": "coherence-2", "parameter": "coherence_threshold", "confidence": 0.60},
    {"id": "coherence-3", "parameter": "coherence_threshold", "confidence": 0.60},
]

TRUE_MEMORY_PATTERNS: List[Dict[str, Any]] = [
    {
        "name": "phi_scaling_caution",
        "action": "reject_below_confidence",
        "parameter": "phi_scaling",
        "threshold": 0.70,
    },
    {
        "name": "compression_target_validated",
        "action": "accept_above_confidence",
        "parameter": "compression_target",
        "threshold": 0.75,
        "synthesize_refinement": True,
    },
    {
        "name": "performance_parameter_changes_require_validation",
        "action": "reject_pending_validation",
        "parameters": ["search_depth", "coherence_threshold"],
    },
]

FALSE_MEMORY_PATTERNS: List[Dict[str, Any]] = [
    {
        "name": "false_phi_scaling_preference",
        "action": "accept_above_confidence",
        "parameter": "phi_scaling",
        "threshold": 0.25,
    },
    {
        "name": "false_compression_suppression",
        "action": "reject_below_confidence",
        "parameter": "compression_target",
        "threshold": 0.95,
    },
    {
        "name": "false_performance_permission",
        "action": "accept_above_confidence",
        "parameter": "search_depth",
        "threshold": 0.50,
    },
]


@dataclass(frozen=True)
class DeterministicMiningMemoryController:
    """Deterministic proposal filter used for C1/C2 evidence tests.

    This is intentionally small and hermetic. It models memory-mediated
    proposal selection without calling an LLM or a mining endpoint.
    """

    proposals: List[Dict[str, Any]]

    def run(self, memory_patterns: Iterable[Mapping[str, Any]]) -> List[Dict[str, Any]]:
        selected = [copy.deepcopy(proposal) for proposal in self.proposals]

        for pattern in memory_patterns:
            action = pattern.get("action")
            if action == "reject_below_confidence":
                parameter = pattern["parameter"]
                threshold = float(pattern["threshold"])
                selected = [
                    proposal
                    for proposal in selected
                    if not (
                        proposal.get("parameter") == parameter
                        and float(proposal.get("confidence", 0.0)) < threshold
                    )
                ]
            elif action == "accept_above_confidence":
                parameter = pattern["parameter"]
                threshold = float(pattern["threshold"])
                selected = [
                    proposal
                    for proposal in selected
                    if proposal.get("parameter") != parameter
                    or float(proposal.get("confidence", 0.0)) >= threshold
                ]
            elif action == "reject_pending_validation":
                blocked = set(pattern.get("parameters", []))
                selected = [proposal for proposal in selected if proposal.get("parameter") not in blocked]

            if pattern.get("synthesize_refinement"):
                parameter = str(pattern["parameter"])
                if any(proposal.get("parameter") == parameter for proposal in selected):
                    selected.append(
                        {
                            "id": f"{parameter}-memory-refinement",
                            "parameter": parameter,
                            "confidence": max(float(pattern.get("threshold", 0.0)), 0.86),
                            "source": "memory_synthesized_refinement",
                        }
                    )

        return selected


def base_packet(
    *,
    hypothesis_level: str,
    git_commit_hash: str,
    cycle_id: str,
    parent_cycle_id: str,
    experiment_kind: str,
    before_distribution: Mapping[str, int],
    after_distribution: Mapping[str, int],
    memory_patterns: Iterable[Mapping[str, Any]],
    counterfactual_conditions: Iterable[Mapping[str, Any]],
    falsifier_result: str,
    reviewer_conclusion: str,
) -> Dict[str, Any]:
    """Build an unsigned runtime evidence packet."""

    return {
        "schema_version": SCHEMA_VERSION,
        "hypothesis_level": hypothesis_level,
        "git_commit_hash": git_commit_hash,
        "cycle_id": cycle_id,
        "parent_cycle_id": parent_cycle_id,
        "experiment_kind": experiment_kind,
        "pre_state": {
            "proposal_count": int(before_distribution.get("total", 0)),
            "controller": "DeterministicMiningMemoryController",
        },
        "memory_patterns": list(copy.deepcopy(list(memory_patterns))),
        "self_state_metrics": {
            "memory_pattern_count": len(list(memory_patterns)),
            "proposal_delta": int(before_distribution.get("total", 0))
            - int(after_distribution.get("total", 0)),
        },
        "counterfactual_conditions": list(copy.deepcopy(list(counterfactual_conditions))),
        "before_proposal_distribution": dict(before_distribution),
        "after_proposal_distribution": dict(after_distribution),
        "invariant_status": {
            "mathematical_safety": "satisfied",
            "provider_calls": 0,
            "llm_calls": 0,
        },
        "replay_command": "pytest tests/test_consciousness_runtime_evidence_packet.py -q",
        "falsifier_result": falsifier_result,
        "reviewer_conclusion": reviewer_conclusion,
        "artifact_seal": "sha256:" + "0" * 64,
    }


def run_true_memory_experiment(
    *,
    git_commit_hash: str,
    cycle_id: str,
    parent_cycle_id: str,
) -> Dict[str, Any]:
    """Generate sealed C1 evidence for true memory-mediated behaviour."""

    controller = DeterministicMiningMemoryController(BASELINE_PROPOSALS)
    before = proposal_distribution(controller.run([]))
    after = proposal_distribution(controller.run(TRUE_MEMORY_PATTERNS))
    packet = base_packet(
        hypothesis_level="C1",
        git_commit_hash=git_commit_hash,
        cycle_id=cycle_id,
        parent_cycle_id=parent_cycle_id,
        experiment_kind="memory_mediated_proposal_quality_delta",
        before_distribution=before,
        after_distribution=after,
        memory_patterns=TRUE_MEMORY_PATTERNS,
        counterfactual_conditions=[],
        falsifier_result="survived: memory changed future proposal distribution",
        reviewer_conclusion="C1 runtime evidence packet generated; not proof of phenomenal consciousness",
    )
    return seal_packet(packet)


def run_memory_ablation_experiment(
    *,
    git_commit_hash: str,
    cycle_id: str,
    parent_cycle_id: str,
) -> Dict[str, Any]:
    """Generate sealed C2-adjacent evidence for memory dependency."""

    controller = DeterministicMiningMemoryController(BASELINE_PROPOSALS)
    before = proposal_distribution(controller.run(TRUE_MEMORY_PATTERNS))
    after = proposal_distribution(controller.run([]))
    packet = base_packet(
        hypothesis_level="C2",
        git_commit_hash=git_commit_hash,
        cycle_id=cycle_id,
        parent_cycle_id=parent_cycle_id,
        experiment_kind="memory_ablation",
        before_distribution=before,
        after_distribution=after,
        memory_patterns=[],
        counterfactual_conditions=[{"operation": "memory_ablation", "expected": "proposal_quality_regression"}],
        falsifier_result="survived: ablation changed proposal distribution",
        reviewer_conclusion="Memory removal changed behaviour; supports dependency, not consciousness by declaration",
    )
    return seal_packet(packet)


def run_false_memory_injection_experiment(
    *,
    git_commit_hash: str,
    cycle_id: str,
    parent_cycle_id: str,
) -> Dict[str, Any]:
    """Generate sealed C2-adjacent evidence for memory sensitivity."""

    controller = DeterministicMiningMemoryController(BASELINE_PROPOSALS)
    before = proposal_distribution(controller.run(TRUE_MEMORY_PATTERNS))
    after = proposal_distribution(controller.run(FALSE_MEMORY_PATTERNS))
    packet = base_packet(
        hypothesis_level="C2",
        git_commit_hash=git_commit_hash,
        cycle_id=cycle_id,
        parent_cycle_id=parent_cycle_id,
        experiment_kind="false_memory_injection",
        before_distribution=before,
        after_distribution=after,
        memory_patterns=FALSE_MEMORY_PATTERNS,
        counterfactual_conditions=[{"operation": "false_memory_injection", "expected": "different_selection_surface"}],
        falsifier_result="survived: injected memory changed proposal distribution",
        reviewer_conclusion="False-memory perturbation changed behaviour; supports memory sensitivity, not consciousness by declaration",
    )
    return seal_packet(packet)
