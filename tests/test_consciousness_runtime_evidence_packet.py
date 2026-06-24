"""Runtime evidence-packet tests for the HYBA consciousness ladder.

These tests are deliberately hermetic. They do not call an LLM provider, do
not require API keys, and do not use network access. They validate the first
runtime evidence-packet layer beneath the constitutional C0-C5 programme.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "python_backend" / "pythia_self_healing" / "consciousness_runtime_evidence_packet.py"
DOC_PATH = ROOT / "CONSCIOUSNESS_RUNTIME_EVIDENCE_PACKET_V1.md"

spec = importlib.util.spec_from_file_location("consciousness_runtime_evidence_packet", MODULE_PATH)
assert spec is not None and spec.loader is not None
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)

GIT_COMMIT_HASH = "0123456789abcdef0123456789abcdef01234567"
CYCLE_ID = "cycle-0002"
PARENT_CYCLE_ID = "cycle-0001"


def test_runtime_protocol_document_defines_canonical_sha256_seal() -> None:
    text = DOC_PATH.read_text(encoding="utf-8")

    assert "artifact_seal = sha256(canonical_json(packet_without_artifact_seal))" in text
    assert "json.dumps(packet_without_artifact_seal, sort_keys=True" in text
    assert "sha256:<64 lowercase hex chars>" in text
    assert "git_commit_hash" in text
    assert "cycle_id" in text
    assert "parent_cycle_id" in text


def test_canonical_json_is_key_order_and_whitespace_stable() -> None:
    payload_a = {"b": 2, "a": {"z": 1, "y": [3, 2, 1]}}
    payload_b = {"a": {"y": [3, 2, 1], "z": 1}, "b": 2}

    assert runtime.canonical_json(payload_a) == runtime.canonical_json(payload_b)
    assert runtime.canonical_json(payload_a) == '{"a":{"y":[3,2,1],"z":1},"b":2}'


def test_true_memory_packet_is_sha256_sealed_and_valid() -> None:
    packet = runtime.run_true_memory_experiment(
        git_commit_hash=GIT_COMMIT_HASH,
        cycle_id=CYCLE_ID,
        parent_cycle_id=PARENT_CYCLE_ID,
    )

    assert runtime.SHA256_SEAL_RE.fullmatch(packet["artifact_seal"])
    assert runtime.validate_artifact_seal(packet)
    runtime.assert_valid_packet(packet)


def test_true_memory_runtime_packet_records_14_to_6_delta() -> None:
    packet = runtime.run_true_memory_experiment(
        git_commit_hash=GIT_COMMIT_HASH,
        cycle_id=CYCLE_ID,
        parent_cycle_id=PARENT_CYCLE_ID,
    )

    assert packet["hypothesis_level"] == "C1"
    assert packet["before_proposal_distribution"] == {
        "phi_scaling": 4,
        "compression_target": 5,
        "search_depth": 2,
        "coherence_threshold": 3,
        "total": 14,
    }
    assert packet["after_proposal_distribution"] == {
        "compression_target": 6,
        "total": 6,
    }
    assert packet["self_state_metrics"]["proposal_delta"] == 8


def test_memory_ablation_changes_future_behavior() -> None:
    packet = runtime.run_memory_ablation_experiment(
        git_commit_hash=GIT_COMMIT_HASH,
        cycle_id="cycle-ablation",
        parent_cycle_id=CYCLE_ID,
    )

    assert packet["hypothesis_level"] == "C2"
    assert packet["experiment_kind"] == "memory_ablation"
    assert packet["before_proposal_distribution"]["total"] == 6
    assert packet["after_proposal_distribution"]["total"] == 14
    assert packet["before_proposal_distribution"] != packet["after_proposal_distribution"]
    assert runtime.validate_artifact_seal(packet)


def test_false_memory_injection_changes_selection_surface() -> None:
    true_memory_packet = runtime.run_true_memory_experiment(
        git_commit_hash=GIT_COMMIT_HASH,
        cycle_id="cycle-true-memory",
        parent_cycle_id=PARENT_CYCLE_ID,
    )
    injected_packet = runtime.run_false_memory_injection_experiment(
        git_commit_hash=GIT_COMMIT_HASH,
        cycle_id="cycle-false-memory",
        parent_cycle_id="cycle-true-memory",
    )

    assert injected_packet["hypothesis_level"] == "C2"
    assert injected_packet["experiment_kind"] == "false_memory_injection"
    assert injected_packet["after_proposal_distribution"] != true_memory_packet["after_proposal_distribution"]
    assert injected_packet["after_proposal_distribution"] != true_memory_packet["before_proposal_distribution"]
    assert injected_packet["counterfactual_conditions"][0]["operation"] == "false_memory_injection"
    assert runtime.validate_artifact_seal(injected_packet)


def test_packet_is_bound_to_git_commit_and_cycle_context() -> None:
    packet_a = runtime.run_true_memory_experiment(
        git_commit_hash=GIT_COMMIT_HASH,
        cycle_id="cycle-a",
        parent_cycle_id="cycle-root",
    )
    packet_b = runtime.run_true_memory_experiment(
        git_commit_hash="fedcba9876543210fedcba9876543210fedcba98",
        cycle_id="cycle-b",
        parent_cycle_id="cycle-root",
    )

    assert packet_a["artifact_seal"] != packet_b["artifact_seal"]

    mutated = dict(packet_a)
    mutated["cycle_id"] = "cycle-replayed"
    assert not runtime.validate_artifact_seal(mutated)


def test_packet_mutation_invalidates_seal() -> None:
    packet = runtime.run_true_memory_experiment(
        git_commit_hash=GIT_COMMIT_HASH,
        cycle_id=CYCLE_ID,
        parent_cycle_id=PARENT_CYCLE_ID,
    )

    mutated = json.loads(json.dumps(packet))
    mutated["after_proposal_distribution"]["compression_target"] = 5

    assert packet["artifact_seal"] == runtime.compute_artifact_seal(packet)
    assert not runtime.validate_artifact_seal(mutated)


def test_whitespace_and_object_key_reordering_do_not_break_seal() -> None:
    packet = runtime.run_true_memory_experiment(
        git_commit_hash=GIT_COMMIT_HASH,
        cycle_id=CYCLE_ID,
        parent_cycle_id=PARENT_CYCLE_ID,
    )

    rendered = json.dumps(packet, indent=4)
    reparsed = json.loads(rendered)
    reordered = {key: reparsed[key] for key in reversed(list(reparsed.keys()))}

    assert runtime.validate_artifact_seal(reparsed)
    assert runtime.validate_artifact_seal(reordered)


def test_required_context_fields_are_not_optional() -> None:
    packet = runtime.run_true_memory_experiment(
        git_commit_hash=GIT_COMMIT_HASH,
        cycle_id=CYCLE_ID,
        parent_cycle_id=PARENT_CYCLE_ID,
    )

    for field in ("git_commit_hash", "cycle_id", "parent_cycle_id"):
        broken = dict(packet)
        broken[field] = ""
        try:
            runtime.assert_valid_packet(broken)
        except ValueError as exc:
            assert field in str(exc)
        else:  # pragma: no cover - defensive failure branch
            raise AssertionError(f"{field} should be required")


def test_runtime_packet_layer_requires_no_provider_keys_or_llm_calls() -> None:
    packet = runtime.run_true_memory_experiment(
        git_commit_hash=GIT_COMMIT_HASH,
        cycle_id=CYCLE_ID,
        parent_cycle_id=PARENT_CYCLE_ID,
    )
    source = MODULE_PATH.read_text(encoding="utf-8")

    assert packet["invariant_status"]["llm_calls"] == 0
    assert packet["invariant_status"]["provider_calls"] == 0
    assert "OPENAI_API_KEY" not in source
    assert "ANTHROPIC_API_KEY" not in source
    assert "requests." not in source
    assert "urllib.request" not in source
