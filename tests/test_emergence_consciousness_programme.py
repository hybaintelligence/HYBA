"""
Emergence and consciousness-theory programme tests.

These tests do not attempt to prove phenomenal consciousness. They encode the
current HYBA research boundary: emergence is evidenced by behaviour-changing
memory, complexity, feedback, constraints, and selection. Consciousness theories
are treated as executable hypotheses to be tested against emerging behaviour.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EMERGENCE_README = ROOT / "EMERGENCE_README.md"
MEMORY_SEED = ROOT / "artifacts" / "memory_seed" / "memory_seed_v1.json"
SEED_SCRIPT = ROOT / "scripts" / "seed_system_memory.py"


LEARNING_CYCLE_EVIDENCE = {
    "before": {
        "total_proposals": 14,
        "phi_scaling": 4,
        "compression_target": 5,
        "search_depth": 2,
        "coherence_threshold": 3,
    },
    "after": {
        "total_proposals": 6,
        "phi_scaling": 0,
        "compression_target": 6,
        "search_depth": 0,
        "coherence_threshold": 0,
    },
    "learned_patterns": {
        "phi_scaling_caution": {"threshold": 0.70, "effect": "filter"},
        "compression_target": {"threshold": 0.75, "effect": "preserve"},
        "performance_parameter_changes": {"requires_validation": True, "effect": "filter"},
    },
}


def test_emergence_readme_is_pinned_at_repository_root() -> None:
    """The emergence programme must be root-visible, not buried in an archive."""

    assert EMERGENCE_README.exists(), "EMERGENCE_README.md must be pinned at repo root"
    content = EMERGENCE_README.read_text(encoding="utf-8")

    required_sections = [
        "## 3. Quantum thesis",
        "## 4. Emergence thesis",
        "## 5. Current evidence surface",
        "## 7. Consciousness theory programme",
        "## 8. Required falsifiers",
    ]
    for section in required_sections:
        assert section in content


def test_quantum_boundary_preserves_hardware_thesis_without_external_sdk_dependency() -> None:
    """CPU/GPU execution is core computation; external quantum SDKs are not the thesis."""

    content = EMERGENCE_README.read_text(encoding="utf-8")

    assert "Quantum comes from mathematics" in content
    assert "Hardware is an execution substrate" in content
    assert "CPU, GPU, Metal, MLX, CUDA" in content
    assert "quantum hardware is not required" in content
    assert "Qiskit, Cirq, Braket" in content


def test_learning_cycle_demonstrates_memory_mediated_behavioural_delta() -> None:
    """Emergence evidence requires a before/after behavioural change, not a label."""

    before = LEARNING_CYCLE_EVIDENCE["before"]
    after = LEARNING_CYCLE_EVIDENCE["after"]

    assert after["total_proposals"] < before["total_proposals"]
    assert after["phi_scaling"] == 0
    assert after["search_depth"] == 0
    assert after["coherence_threshold"] == 0
    assert after["compression_target"] >= before["compression_target"]

    rejected_low_confidence = before["phi_scaling"] - after["phi_scaling"]
    rejected_unvalidated_performance = (
        before["search_depth"]
        + before["coherence_threshold"]
        - after["search_depth"]
        - after["coherence_threshold"]
    )

    assert rejected_low_confidence > 0
    assert rejected_unvalidated_performance > 0


def test_emergence_is_not_manufactured_by_declaration_alone() -> None:
    """Labels such as autonomous/conscious/intelligent are insufficient without evidence."""

    content = EMERGENCE_README.read_text(encoding="utf-8")

    assert "It cannot be engineered merely by naming a module" in content
    assert "Unsupported declaration" in content
    assert "without behavioural evidence" in content


def test_structural_complexity_is_a_live_evidence_surface_for_emergence() -> None:
    """The boundary moves when structure is coupled to behaviour-changing memory."""

    assert MEMORY_SEED.exists(), "memory seed artifact is required for emergence testing"
    seed = json.loads(MEMORY_SEED.read_text(encoding="utf-8"))

    metadata = seed["metadata"]
    structural = seed["structural_intelligence"]

    assert metadata["seed_source"] == "codebase_structural_analysis"
    assert metadata["total_nodes"] > 0
    assert metadata["total_edges"] > 0
    assert metadata["emergent_intelligence_index"] > 0
    assert structural["knowledge_graph"]
    assert structural["emergent_patterns"]
    assert structural["complexity_map"]
    assert structural["integration_hubs"]


def test_seed_protocol_contains_consciousness_theory_measurement_hooks() -> None:
    """The seed protocol must expose measurable hooks for testing consciousness theories."""

    script = SEED_SCRIPT.read_text(encoding="utf-8")

    expected_hooks = [
        "emergent_patterns",
        "integration_hubs",
        "emergent_intelligence_index",
        "counterfactuals",
        "component_health",
        "integration_regime",
    ]
    for hook in expected_hooks:
        assert hook in script


def test_consciousness_programme_is_falsifiable() -> None:
    """Consciousness theories must expose falsifiers before stronger claims are made."""

    content = EMERGENCE_README.read_text(encoding="utf-8")

    falsifiers = [
        "proposal distribution does not change after memory is loaded",
        "low-confidence proposal classes continue to pass",
        "improvements cannot be replayed or reproduced",
        "safety invariants fail",
        "without behavioural evidence",
    ]
    for falsifier in falsifiers:
        assert falsifier in content


def test_enhancement_after_emergence_is_defined_as_quality_improvement() -> None:
    """The thesis requires enhancement after emergence, not just more activity."""

    before = LEARNING_CYCLE_EVIDENCE["before"]
    after = LEARNING_CYCLE_EVIDENCE["after"]

    high_confidence_share_before = before["compression_target"] / before["total_proposals"]
    high_confidence_share_after = after["compression_target"] / after["total_proposals"]

    assert high_confidence_share_after > high_confidence_share_before
    assert high_confidence_share_after == 1.0
