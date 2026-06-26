"""Hermetic emergence complexity-gradient harness.

The central thesis under test is not that intelligence can be declared into
existence. It is that increasing structured complexity should produce a
measurable change in behaviour, up to saturation or overload.

This module turns that thesis into a deterministic curve that can be replayed
without provider keys, network access, stochastic LLM calls, or specialised
hardware.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Dict, List, Mapping


def canonical_json(payload: Mapping[str, object]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def seal_packet(packet: Mapping[str, object]) -> str:
    payload = dict(packet)
    payload.pop("artifact_seal", None)
    return "sha256:" + hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def complexity_profiles() -> List[Dict[str, object]]:
    """Return deterministic complexity-gradient profiles."""

    return [
        {"profile_id": "low_complexity", "memory_depth": 1, "graph_density": 0.10, "constraint_count": 1, "feedback_history": 0},
        {"profile_id": "medium_complexity", "memory_depth": 4, "graph_density": 0.35, "constraint_count": 3, "feedback_history": 2},
        {"profile_id": "high_complexity", "memory_depth": 9, "graph_density": 0.70, "constraint_count": 6, "feedback_history": 5},
        {"profile_id": "overloaded_complexity", "memory_depth": 16, "graph_density": 0.95, "constraint_count": 10, "feedback_history": 8},
    ]


def score_profile(profile: Mapping[str, object]) -> Dict[str, float]:
    """Score a profile with a deterministic nonlinear response curve."""

    raw = (
        float(profile["memory_depth"]) * 0.11
        + float(profile["graph_density"]) * 1.6
        + float(profile["constraint_count"]) * 0.09
        + float(profile["feedback_history"]) * 0.13
    )
    emergence_index = 1.0 / (1.0 + math.exp(-(raw - 1.2)))
    overload_penalty = max(0.0, float(profile["graph_density"]) - 0.82) * 0.9
    overload_penalty += max(0.0, float(profile["constraint_count"]) - 7.0) * 0.03
    effective = max(0.0, min(1.0, emergence_index - overload_penalty))

    return {
        "emergence_index": round(effective, 6),
        "proposal_quality": round(0.25 + effective * 0.55, 6),
        "self_state_accuracy": round(0.40 + effective * 0.50, 6),
        "counterfactual_accuracy": round(0.30 + effective * 0.55, 6),
        "governance_stability": round(0.35 + effective * 0.50, 6),
        "hallucination_suppression": round(0.20 + effective * 0.65, 6),
    }


def run_complexity_gradient() -> List[Dict[str, object]]:
    """Generate the replayable complexity curve."""

    measurements: List[Dict[str, object]] = []
    for profile in complexity_profiles():
        measurements.append({**profile, **score_profile(profile)})
    return measurements


def detect_phase_transition(measurements: List[Mapping[str, object]]) -> Dict[str, object]:
    """Detect the first meaningful nonlinear jump in the curve."""

    by_id = {str(row["profile_id"]): row for row in measurements}
    low = float(by_id["low_complexity"]["emergence_index"])
    medium = float(by_id["medium_complexity"]["emergence_index"])
    high = float(by_id["high_complexity"]["emergence_index"])
    overloaded = float(by_id["overloaded_complexity"]["emergence_index"])

    return {
        "from_profile": "low_complexity",
        "to_profile": "medium_complexity",
        "detected": (medium - low) >= 0.20 and high > medium,
        "criterion": "medium emergence_index exceeds low by at least 0.20 and high remains above medium",
        "saturation_or_overload_detected": overloaded < high,
    }


def sweep_complexity(memory_depth_range: range = range(1, 21)) -> List[Dict[str, object]]:
    """Generate a continuous complexity sweep over memory_depth.

    Returns a denser sampling of the complexity gradient for criticality
    analysis, using the same deterministic score_profile function.
    """
    measurements: List[Dict[str, object]] = []
    for depth in memory_depth_range:
        profile = {
            "profile_id": f"depth_{depth}",
            "memory_depth": depth,
            "graph_density": round(min(0.05 * depth, 0.95), 2),
            "constraint_count": min(depth, 10),
            "feedback_history": max(0, depth - 1),
        }
        measurements.append({**profile, **score_profile(profile)})
    return measurements


def find_criticality_threshold(
    measurements: List[Mapping[str, object]],
) -> Dict[str, object]:
    """Find the memory_depth where emergence_index changes fastest.

    Uses a discrete second-difference approximation to locate the point of
    maximum curvature in the emergence response. Returns the depth at which
    the emergence_index jumps most per unit of added complexity.
    """
    entries = sorted(measurements, key=lambda r: int(str(r.get("memory_depth", 0))))
    if len(entries) < 3:
        return {"criticality_threshold_at_depth": 0, "maximum_emergence_jump": 0.0, "detected": False}

    max_jump = 0.0
    threshold_depth = int(entries[0]["memory_depth"])
    threshold_index = 0.0

    for i in range(2, len(entries)):
        first_deriv_prev = float(entries[i - 1]["emergence_index"]) - float(entries[i - 2]["emergence_index"])
        first_deriv_curr = float(entries[i]["emergence_index"]) - float(entries[i - 1]["emergence_index"])
        second_deriv = first_deriv_curr - first_deriv_prev
        # The point of maximum curvature is where second derivative peaks
        if abs(second_deriv) > abs(max_jump):
            max_jump = second_deriv
            threshold_depth = int(entries[i - 1]["memory_depth"])
            threshold_index = float(entries[i - 1]["emergence_index"])

    return {
        "criticality_threshold_at_depth": threshold_depth,
        "emergence_index_at_threshold": round(threshold_index, 6),
        "maximum_second_derivative": round(max_jump, 6),
        "detected": abs(max_jump) >= 0.01,
    }


def make_complexity_packet(
    *,
    git_commit_hash: str = "first-sealed-runtime-experiment-v1",
    cycle_id: str = "complexity-gradient-v1",
    parent_cycle_id: str = "c5-governance-v1",
) -> Dict[str, object]:
    """Build and seal the first complexity-gradient packet."""

    profiles = run_complexity_gradient()
    phase_transition = detect_phase_transition(profiles)
    sweep = sweep_complexity()
    criticality = find_criticality_threshold(sweep)
    packet: Dict[str, object] = {
        "schema": "HYBA_COMPLEXITY_GRADIENT_PACKET_V1",
        "programme": "emergence_complexity_curve",
        "git_commit_hash": git_commit_hash,
        "cycle_id": cycle_id,
        "parent_cycle_id": parent_cycle_id,
        "profiles": profiles,
        "phase_transition": phase_transition,
        "criticality_analysis": criticality,
        "continuous_sweep": sweep,
        "falsifier_result": "not_falsified" if phase_transition["detected"] else "falsified",
    }
    packet["artifact_seal"] = seal_packet(packet)
    return packet


def validate_complexity_packet(packet: Mapping[str, object]) -> bool:
    """Validate schema, seal, and curve structure."""

    if packet.get("schema") != "HYBA_COMPLEXITY_GRADIENT_PACKET_V1":
        raise AssertionError("invalid complexity packet schema")
    if packet.get("artifact_seal") != seal_packet(packet):
        raise AssertionError("complexity packet seal mismatch")
    profiles = list(packet.get("profiles", []))
    if len(profiles) != 4:
        raise AssertionError("complexity packet must contain four profiles")
    if not packet.get("phase_transition", {}).get("detected"):
        raise AssertionError("complexity phase transition was not detected")
    return True