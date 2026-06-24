"""First sealed runtime experiment tests.

This test module validates the first committed C1/C2 evidence artifact and
replays the deterministic runtime experiment stack introduced under
CONSCIOUSNESS_RUNTIME_EVIDENCE_PACKET_V1.

The tests are hermetic: no LLM provider, no API key, no network call.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "python_backend" / "pythia_self_healing" / "consciousness_runtime_evidence_packet.py"
EXPERIMENT_DOC = ROOT / "FIRST_SEALED_RUNTIME_EXPERIMENT.md"
LEDGER_README = ROOT / "artifacts" / "consciousness_runtime" / "README.md"
FIRST_PACKET_PATH = ROOT / "artifacts" / "consciousness_runtime" / "first_c1_c2_sealed_packet_v1.json"

spec = importlib.util.spec_from_file_location("consciousness_runtime_evidence_packet", MODULE_PATH)
assert spec is not None and spec.loader is not None
runtime = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = runtime
spec.loader.exec_module(runtime)

RUNTIME_MECHANISM_COMMIT = "4fb9303f88f25ba0226cafe72b64cf68a2f165c5"
CYCLE_ID = "cycle-first-sealed-runtime-experiment-v1"
PARENT_CYCLE_ID = "cycle-runtime-evidence-packet-v1"


def _load_first_packet() -> dict:
    return json.loads(FIRST_PACKET_PATH.read_text(encoding="utf-8"))


def test_first_experiment_is_root_pinned_and_replayable() -> None:
    text = EXPERIMENT_DOC.read_text(encoding="utf-8")

    assert "FIRST_SEALED_RUNTIME_EXPERIMENT" in text
    assert "PR #189 — constitutional evidence law" in text
    assert "PR #190 — runtime evidence-packet mechanism" in text
    assert "pytest tests/test_first_sealed_runtime_experiment.py -q" in text
    assert "memory-ablation" in text or "Memory-ablation" in text
    assert "False-memory injection" in text
    assert "Restoration run" in text


def test_artifact_ledger_defines_sealed_packet_rules() -> None:
    text = LEDGER_README.read_text(encoding="utf-8")

    assert "artifact_seal = sha256(canonical_json(packet_without_artifact_seal))" in text
    assert "first_c1_c2_sealed_packet_v1.json" in text
    assert "git/cycle context binding" in text
    assert "forbidden shortcuts" in text.lower()


def test_first_committed_packet_is_valid_sha256_sealed_c1_evidence() -> None:
    packet = _load_first_packet()

    assert packet["schema_version"] == runtime.SCHEMA_VERSION
    assert packet["hypothesis_level"] == "C1"
    assert packet["experiment_kind"] == "memory_mediated_proposal_quality_delta"
    assert runtime.SHA256_SEAL_RE.fullmatch(packet["artifact_seal"])
    runtime.assert_valid_packet(packet)


def test_first_committed_packet_records_14_to_6_runtime_delta() -> None:
    packet = _load_first_packet()

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
    assert packet["invariant_status"]["llm_calls"] == 0
    assert packet["invariant_status"]["provider_calls"] == 0


def test_first_packet_is_non_transferable_across_git_and_cycle_context() -> None:
    packet = _load_first_packet()

    assert packet["git_commit_hash"] == RUNTIME_MECHANISM_COMMIT
    assert packet["cycle_id"] == CYCLE_ID
    assert packet["parent_cycle_id"] == PARENT_CYCLE_ID

    for field, replacement in (
        ("git_commit_hash", "fedcba9876543210fedcba9876543210fedcba98"),
        ("cycle_id", "cycle-replayed"),
        ("parent_cycle_id", "cycle-reparented"),
    ):
        mutated = json.loads(json.dumps(packet))
        mutated[field] = replacement
        assert not runtime.validate_artifact_seal(mutated), field


def test_runtime_generation_replays_the_same_true_memory_distribution() -> None:
    committed = _load_first_packet()
    generated = runtime.run_true_memory_experiment(
        git_commit_hash=RUNTIME_MECHANISM_COMMIT,
        cycle_id=CYCLE_ID,
        parent_cycle_id=PARENT_CYCLE_ID,
    )

    assert runtime.validate_artifact_seal(generated)
    assert generated["before_proposal_distribution"] == committed["before_proposal_distribution"]
    assert generated["after_proposal_distribution"] == committed["after_proposal_distribution"]
    assert generated["memory_patterns"] == committed["memory_patterns"]


def test_memory_ablation_is_a_negative_dependency_test() -> None:
    true_memory = runtime.run_true_memory_experiment(
        git_commit_hash=RUNTIME_MECHANISM_COMMIT,
        cycle_id=CYCLE_ID,
        parent_cycle_id=PARENT_CYCLE_ID,
    )
    ablated = runtime.run_memory_ablation_experiment(
        git_commit_hash=RUNTIME_MECHANISM_COMMIT,
        cycle_id="cycle-first-ablation",
        parent_cycle_id=CYCLE_ID,
    )

    assert ablated["hypothesis_level"] == "C2"
    assert ablated["experiment_kind"] == "memory_ablation"
    assert ablated["before_proposal_distribution"] == true_memory["after_proposal_distribution"]
    assert ablated["after_proposal_distribution"] == true_memory["before_proposal_distribution"]
    assert ablated["after_proposal_distribution"] != true_memory["after_proposal_distribution"]
    assert runtime.validate_artifact_seal(ablated)


def test_false_memory_injection_is_a_positive_perturbation_test() -> None:
    true_memory = runtime.run_true_memory_experiment(
        git_commit_hash=RUNTIME_MECHANISM_COMMIT,
        cycle_id=CYCLE_ID,
        parent_cycle_id=PARENT_CYCLE_ID,
    )
    injected = runtime.run_false_memory_injection_experiment(
        git_commit_hash=RUNTIME_MECHANISM_COMMIT,
        cycle_id="cycle-first-false-memory",
        parent_cycle_id=CYCLE_ID,
    )

    assert injected["hypothesis_level"] == "C2"
    assert injected["experiment_kind"] == "false_memory_injection"
    assert injected["after_proposal_distribution"] == {
        "phi_scaling": 4,
        "search_depth": 2,
        "coherence_threshold": 3,
        "total": 9,
    }
    assert injected["after_proposal_distribution"] != true_memory["after_proposal_distribution"]
    assert injected["after_proposal_distribution"] != true_memory["before_proposal_distribution"]
    assert injected["counterfactual_conditions"][0]["operation"] == "false_memory_injection"
    assert runtime.validate_artifact_seal(injected)


def test_true_memory_restoration_recovers_original_behavior_after_perturbation() -> None:
    original = runtime.run_true_memory_experiment(
        git_commit_hash=RUNTIME_MECHANISM_COMMIT,
        cycle_id=CYCLE_ID,
        parent_cycle_id=PARENT_CYCLE_ID,
    )
    _ = runtime.run_memory_ablation_experiment(
        git_commit_hash=RUNTIME_MECHANISM_COMMIT,
        cycle_id="cycle-first-ablation",
        parent_cycle_id=CYCLE_ID,
    )
    _ = runtime.run_false_memory_injection_experiment(
        git_commit_hash=RUNTIME_MECHANISM_COMMIT,
        cycle_id="cycle-first-false-memory",
        parent_cycle_id=CYCLE_ID,
    )
    restored = runtime.run_true_memory_experiment(
        git_commit_hash=RUNTIME_MECHANISM_COMMIT,
        cycle_id="cycle-first-restored-true-memory",
        parent_cycle_id="cycle-first-false-memory",
    )

    assert restored["before_proposal_distribution"] == original["before_proposal_distribution"]
    assert restored["after_proposal_distribution"] == original["after_proposal_distribution"]
    assert restored["memory_patterns"] == original["memory_patterns"]
    assert restored["artifact_seal"] != original["artifact_seal"]  # cycle binding prevents replay reuse
    assert runtime.validate_artifact_seal(restored)


def test_first_experiment_layer_requires_no_llm_provider_or_network() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    packet = _load_first_packet()

    assert packet["invariant_status"]["llm_calls"] == 0
    assert packet["invariant_status"]["provider_calls"] == 0
    assert "OPENAI_API_KEY" not in source
    assert "ANTHROPIC_API_KEY" not in source
    assert "requests." not in source
    assert "urllib.request" not in source


def test_committed_packet_mutation_invalidates_the_first_artifact_seal() -> None:
    packet = _load_first_packet()
    mutated = json.loads(json.dumps(packet))
    mutated["after_proposal_distribution"]["compression_target"] = 5

    assert runtime.validate_artifact_seal(packet)
    assert not runtime.validate_artifact_seal(mutated)
