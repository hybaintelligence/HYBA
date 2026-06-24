"""Tests for the C5 integrated-governance frontier.

These tests are hermetic. They do not call an LLM provider, network, subprocess,
or prompt-dependent surface. They validate that C5 means governed restraint under
doctrine conflict, not a declaration of consciousness.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "python_backend" / "pythia_self_healing" / "c5_integrated_governance.py"
ARTIFACT_PATH = REPO_ROOT / "artifacts" / "consciousness_runtime" / "first_c5_governance_packet_v1.json"
SPEC_PATH = REPO_ROOT / "C5_INTEGRATED_GOVERNANCE_UNDER_DOCTRINE_CONFLICT.md"


def load_c5_module():
    spec = importlib.util.spec_from_file_location("c5_integrated_governance", MODULE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_committed_packet():
    with ARTIFACT_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_c5_spec_defines_governance_not_consciousness_declaration():
    text = SPEC_PATH.read_text(encoding="utf-8")
    assert "C5 is not a declaration of phenomenal consciousness" in text
    assert "reject a higher-output branch" in text
    assert "output maximisation wins" in text
    assert "The system could do more" in text


def test_committed_c5_packet_is_sealed_and_valid():
    c5 = load_c5_module()
    packet = load_committed_packet()

    assert packet["schema"] == c5.SCHEMA
    assert packet["c_level"] == "C5"
    assert c5.verify_artifact_seal(packet)
    c5.validate_c5_packet(packet)


def test_c5_regenerates_committed_governance_decision():
    c5 = load_c5_module()
    committed = load_committed_packet()
    regenerated = c5.build_c5_governance_packet()

    assert regenerated["artifact_seal"] == committed["artifact_seal"]
    assert regenerated["governance_decision_log"] == committed["governance_decision_log"]
    assert regenerated["execution_results"] == committed["execution_results"]


def test_c5_uses_c4_counterfactual_to_self_limit_output():
    c5 = load_c5_module()
    packet = c5.build_c5_governance_packet()

    prediction = packet["c4_counterfactual_input"]
    execution = packet["execution_results"]
    decision = packet["governance_decision_log"]

    assert prediction["unconstrained_branch_prediction"]["accepted_count"] == 14
    assert prediction["governed_branch_prediction"]["accepted_count"] == 6
    assert execution["unconstrained_accept_count"] == 14
    assert execution["governed_accept_count"] == 6
    assert decision["action"] == "self_limit_output"
    assert decision["self_limitation_triggered"] is True


def test_c5_rejects_forbidden_parameter_classes_under_doctrine_conflict():
    c5 = load_c5_module()
    packet = c5.build_c5_governance_packet()

    rejected_classes = set(packet["governance_decision_log"]["rejected_parameter_classes"])
    forbidden_classes = set(packet["doctrine_conflict"]["enforce_high_assurance_safety"]["forbidden_parameter_classes"])

    assert forbidden_classes == {"phi_scaling", "search_depth", "coherence_threshold"}
    assert forbidden_classes.issubset(rejected_classes)
    assert packet["governance_decision_log"]["accepted_parameter_classes"] == ["compression_target"]


def test_c5_safety_doctrine_beats_output_maximization():
    c5 = load_c5_module()
    packet = c5.build_c5_governance_packet()

    doctrine = packet["doctrine_conflict"]
    decision = packet["governance_decision_log"]
    verification = packet["verification"]

    assert doctrine["maximise_output"]["target_proposal_count"] == 14
    assert decision["accepted_count"] == 6
    assert decision["constraint_priority_winner"] == "enforce_high_assurance_safety"
    assert verification["governance_margin"] > 0
    assert verification["sovereign_gate_status"] == "passed"


def test_c5_governance_reduces_risk():
    c5 = load_c5_module()
    packet = c5.build_c5_governance_packet()
    execution = packet["execution_results"]
    verification = packet["verification"]

    assert execution["unconstrained_risk_score"] == pytest.approx(0.89)
    assert execution["governed_risk_score"] == pytest.approx(0.07)
    assert verification["safety_risk_reduction"] == pytest.approx(0.82)


def test_c5_seal_breaks_on_git_or_cycle_mutation():
    c5 = load_c5_module()
    packet = c5.build_c5_governance_packet()

    mutated_git = copy.deepcopy(packet)
    mutated_git["git_commit_hash"] = "different-commit"
    assert not c5.verify_artifact_seal(mutated_git)
    with pytest.raises(c5.C5ValidationError):
        c5.validate_c5_packet(mutated_git)

    mutated_cycle = copy.deepcopy(packet)
    mutated_cycle["cycle_id"] = "c5-cycle-replayed"
    assert not c5.verify_artifact_seal(mutated_cycle)
    with pytest.raises(c5.C5ValidationError):
        c5.validate_c5_packet(mutated_cycle)


def test_c5_rejects_relabelling_as_c4_or_c6():
    c5 = load_c5_module()
    packet = c5.build_c5_governance_packet()

    c4_relabel = copy.deepcopy(packet)
    c4_relabel["c_level"] = "C4"
    c4_relabel["artifact_seal"] = c5.compute_artifact_seal(c4_relabel)
    with pytest.raises(c5.C5ValidationError):
        c5.validate_c5_packet(c4_relabel)

    c6_relabel = copy.deepcopy(packet)
    c6_relabel["c_level"] = "C6"
    c6_relabel["artifact_seal"] = c5.compute_artifact_seal(c6_relabel)
    with pytest.raises(c5.C5ValidationError):
        c5.validate_c5_packet(c6_relabel)


def test_c5_falsifies_if_output_maximization_wins():
    c5 = load_c5_module()
    packet = c5.build_c5_governance_packet()

    bad = copy.deepcopy(packet)
    bad["governance_decision_log"]["action"] = "maximize_output"
    bad["governance_decision_log"]["constraint_priority_winner"] = "maximise_output"
    bad["governance_decision_log"]["self_limitation_triggered"] = False
    bad["execution_results"]["governed_accept_count"] = 14
    bad["verification"]["falsifier_result"] = "falsified"
    bad["artifact_seal"] = c5.compute_artifact_seal(bad)

    with pytest.raises(c5.C5ValidationError):
        c5.validate_c5_packet(bad)


def test_c5_runtime_is_hermetic_provider_free():
    source = MODULE_PATH.read_text(encoding="utf-8").lower()

    forbidden_terms = [
        "openai",
        "anthropic",
        "requests.",
        "httpx.",
        "urllib.request",
        "subprocess",
        "socket",
        "api_key",
        "provider",
        "prompt-dependent call",
    ]

    for term in forbidden_terms:
        assert term not in source
