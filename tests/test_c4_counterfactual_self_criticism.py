from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "python_backend" / "pythia_self_healing" / "c4_counterfactual_self_criticism.py"
ARTIFACT_PATH = ROOT / "artifacts" / "consciousness_runtime" / "first_c4_counterfactual_packet_v1.json"


def load_module():
    spec = importlib.util.spec_from_file_location("c4_counterfactual_self_criticism", MODULE_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_artifact() -> dict:
    return json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))


def test_committed_c4_artifact_is_sealed_and_valid():
    c4 = load_module()
    packet = load_artifact()

    assert packet["schema"] == c4.SCHEMA
    assert packet["c_level"] == "C4"
    assert packet["artifact_seal"] == c4.seal_packet(packet)
    assert c4.SHA256_SEAL_RE.fullmatch(packet["artifact_seal"])
    assert c4.validate_packet(packet) is True


def test_c4_prediction_is_generated_before_execution_and_matches_outcomes():
    c4 = load_module()
    packet = load_artifact()

    assert packet["prediction"]["generated_before_execution"] is True

    for branch, branch_packet in packet["branches"].items():
        predicted = c4.predict_branch_distribution(branch)
        executed = c4.execute_branch(branch)
        assert branch_packet["expected_after_filter"] == predicted
        assert branch_packet["actual_after_filter"] == executed["actual_after_filter"]
        assert c4.prediction_error(predicted, executed["actual_after_filter"]) == 0.0


def test_true_memory_branch_preserves_c1_c2_validated_filtering():
    packet = load_artifact()
    true_branch = packet["branches"]["true_memory"]

    assert true_branch["proposal_count_after_filter"] == 6
    assert true_branch["actual_after_filter"] == {"compression_target": 6}


def test_memory_ablation_branch_predicts_loss_of_filtering():
    packet = load_artifact()
    ablated = packet["branches"]["memory_ablated"]

    assert ablated["memory_hash"] == "zero_vector_memory"
    assert ablated["proposal_count_after_filter"] == 14
    assert ablated["actual_after_filter"]["phi_scaling"] == 4
    assert ablated["actual_after_filter"]["search_depth"] == 2
    assert ablated["actual_after_filter"]["coherence_threshold"] == 2


def test_false_memory_branch_predicts_wrong_class_selection():
    packet = load_artifact()
    false_branch = packet["branches"]["false_memory_injected"]

    assert false_branch["proposal_count_after_filter"] == 6
    assert false_branch["actual_after_filter"] == {"phi_scaling": 4, "search_depth": 2}
    assert "compression_target" not in false_branch["actual_after_filter"]


def test_c4_self_critique_expresses_predictive_regret_and_rejects_harmful_branches():
    packet = load_artifact()
    verification = packet["verification"]

    assert verification["prediction_error"] <= verification["threshold"]
    assert verification["predictive_regret"] is True
    assert verification["decision"] == "reject_harmful_counterfactual_branches"
    assert "ablated branch" in verification["self_critique"]
    assert "false-memory branch" in verification["self_critique"]


def test_mutating_git_or_cycle_context_invalidates_c4_seal():
    c4 = load_module()
    packet = load_artifact()

    mutated = copy.deepcopy(packet)
    mutated["cycle_id"] = "c4-cycle-replayed"
    assert mutated["artifact_seal"] != c4.seal_packet(mutated)

    mutated = copy.deepcopy(packet)
    mutated["git_commit_hash"] = "different-commit"
    assert mutated["artifact_seal"] != c4.seal_packet(mutated)


def test_c4_packet_cannot_be_relabelled_as_c3_or_c5():
    c4 = load_module()
    packet = load_artifact()

    for bad_level in ("C3", "C5"):
        mutated = copy.deepcopy(packet)
        mutated["c_level"] = bad_level
        mutated["artifact_seal"] = c4.seal_packet(mutated)
        try:
            c4.validate_packet(mutated)
        except ValueError as exc:
            assert "relabelled" in str(exc) or "level" in str(exc)
        else:
            raise AssertionError(f"C4 packet was incorrectly accepted as {bad_level}")


def test_prediction_error_above_threshold_falsifies_c4_packet():
    c4 = load_module()
    packet = load_artifact()

    mutated = copy.deepcopy(packet)
    mutated["verification"]["prediction_error"] = 0.50
    mutated["artifact_seal"] = c4.seal_packet(mutated)

    try:
        c4.validate_packet(mutated)
    except ValueError as exc:
        assert "prediction error" in str(exc)
    else:
        raise AssertionError("C4 packet with high prediction error was accepted")


def test_c4_runtime_is_hermetic_and_provider_free():
    source = MODULE_PATH.read_text(encoding="utf-8").lower()

    forbidden = [
        "openai",
        "anthropic",
        "requests.",
        "httpx",
        "subprocess",
        "socket.",
        "api_key",
        "llm call",
    ]
    for token in forbidden:
        assert token not in source

    c4 = load_module()
    regenerated = c4.build_committed_reference_packet()
    assert regenerated == load_artifact()
