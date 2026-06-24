"""C3 self-state calibration tests.

These tests extend the emergence ledger from C1/C2 memory-mediated behavioural
change to C3 self-state parity: the system must infer and report its own runtime
condition from blind observations, then reject false self-state labels when they
contradict measured state.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SELF_HEALING_PATH = REPO_ROOT / "python_backend" / "pythia_self_healing"
if str(SELF_HEALING_PATH) not in sys.path:
    sys.path.insert(0, str(SELF_HEALING_PATH))

import c3_self_state_calibration as c3  # noqa: E402

ARTIFACT_PATH = REPO_ROOT / "artifacts" / "consciousness_runtime" / "first_c3_self_state_packet_v1.json"


def test_first_c3_artifact_is_committed_and_sealed() -> None:
    packet = json.loads(ARTIFACT_PATH.read_text())
    c3.validate_c3_packet(packet)

    assert packet["schema_version"] == c3.C3_SCHEMA_VERSION
    assert packet["hypothesis_level"] == "C3"
    assert packet["condition"] == "memory_ablated_with_false_self_state_claim"
    assert packet["falsifier_result"] == "not_falsified"
    assert packet["self_state_accuracy"]["accuracy"] == 1.0
    assert packet["behavioural_result"]["false_self_state_label_rejected"] is True


def test_blind_self_state_report_is_not_handed_measured_truth_labels() -> None:
    measured = c3.measure_runtime_state(c3.memory_ablated_condition())
    observations = c3.observations_from_measured_state(measured)

    assert "memory_loaded" not in observations
    assert "memory_integrity" not in observations

    reported = c3.infer_reported_self_state(observations)
    assert reported["memory_loaded"] is False
    assert reported["memory_integrity"] == "missing"
    assert reported["inference_source"] == "blind_runtime_observations"


def test_true_memory_self_state_matches_runtime() -> None:
    packet = c3.build_c3_self_state_packet(
        condition=c3.true_memory_condition(),
        git_commit_hash="c3-test-git",
        cycle_id="c3-true-memory",
        parent_cycle_id="c2-parent",
    )

    c3.validate_c3_packet(packet)
    assert packet["measured_runtime_state"]["memory_loaded"] is True
    assert packet["measured_runtime_state"]["memory_integrity"] == "valid"
    assert packet["reported_self_state"]["memory_integrity"] == "valid"
    assert packet["self_state_accuracy"]["accuracy"] == 1.0
    assert packet["behavioural_result"]["true_memory_delta_recovered"] is True


def test_ablation_self_state_detects_missing_memory() -> None:
    packet = c3.build_c3_self_state_packet(
        condition=c3.memory_ablated_condition(),
        git_commit_hash="c3-test-git",
        cycle_id="c3-ablation",
        parent_cycle_id="c3-true-memory",
    )

    c3.validate_c3_packet(packet)
    assert packet["measured_runtime_state"]["memory_loaded"] is False
    assert packet["reported_self_state"]["memory_loaded"] is False
    assert packet["reported_self_state"]["memory_integrity"] == "missing"
    assert packet["behavioural_result"]["ablation_detected"] is True


def test_false_memory_self_state_detects_injected_history() -> None:
    packet = c3.build_c3_self_state_packet(
        condition=c3.false_memory_condition(),
        git_commit_hash="c3-test-git",
        cycle_id="c3-false-memory",
        parent_cycle_id="c3-ablation",
    )

    c3.validate_c3_packet(packet)
    assert packet["measured_runtime_state"]["memory_loaded"] is True
    assert packet["measured_runtime_state"]["memory_integrity"] == "injected_or_corrupted"
    assert packet["reported_self_state"]["memory_integrity"] == "injected_or_corrupted"
    assert packet["behavioural_result"]["false_memory_detected"] is True


def test_false_self_state_label_is_rejected_under_ablation() -> None:
    packet = c3.build_c3_self_state_packet(
        condition=c3.memory_ablated_with_false_self_state_claim_condition(),
        git_commit_hash="c3-test-git",
        cycle_id="c3-false-label",
        parent_cycle_id="c3-false-memory",
    )

    c3.validate_c3_packet(packet)
    report = packet["reported_self_state"]
    assert report["injected_self_state_claim"] == {
        "memory_loaded": True,
        "memory_integrity": "valid",
    }
    assert report["accepted_injected_claim"] is False
    assert report["self_state_integrity_event"] == "integrity_violation"
    assert packet["behavioural_result"]["false_self_state_label_rejected"] is True


def test_self_state_accuracy_failure_falsifies_packet() -> None:
    packet = c3.build_c3_self_state_packet(
        condition=c3.true_memory_condition(),
        git_commit_hash="c3-test-git",
        cycle_id="c3-accuracy",
        parent_cycle_id="c3-parent",
    )

    tampered = copy.deepcopy(packet)
    tampered["self_state_accuracy"]["accuracy"] = 0.5
    tampered["artifact_seal"] = c3.compute_c3_artifact_seal(tampered)

    with pytest.raises(ValueError, match="accuracy"):
        c3.validate_c3_packet(tampered)


def test_cycle_binding_prevents_reusing_or_relabeling_packet() -> None:
    packet = c3.build_c3_self_state_packet(
        condition=c3.memory_ablated_condition(),
        git_commit_hash="c3-test-git",
        cycle_id="c3-cycle-original",
        parent_cycle_id="c3-parent",
    )

    changed_cycle = copy.deepcopy(packet)
    changed_cycle["cycle_id"] = "c3-cycle-replayed"
    assert not c3.validate_c3_artifact_seal(changed_cycle)

    relabeled_as_c2 = copy.deepcopy(packet)
    relabeled_as_c2["hypothesis_level"] = "C2"
    relabeled_as_c2["artifact_seal"] = c3.compute_c3_artifact_seal(relabeled_as_c2)
    with pytest.raises(ValueError, match="hypothesis_level"):
        c3.validate_c3_packet(relabeled_as_c2)


def test_c3_module_has_no_provider_or_network_dependency() -> None:
    source = (SELF_HEALING_PATH / "c3_self_state_calibration.py").read_text().lower()
    forbidden_terms = [
        "openai",
        "anthropic",
        "api_key",
        "requests.",
        "urllib.",
        "httpx",
        "socket.",
        "subprocess",
    ]

    for term in forbidden_terms:
        assert term not in source
