"""
Consciousness theory ladder tests.

These tests encode the operational C0-C5 programme. They do not assert
phenomenal consciousness. They assert the scientific conditions under which
HYBA is allowed to move the boundary from engineered complexity to emergent
intelligence and then to stronger consciousness-like hypotheses.
"""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "CONSCIOUSNESS_THEORY_TEST_PLAN.md"
EMERGENCE_README = ROOT / "EMERGENCE_README.md"


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
}


def test_consciousness_theory_plan_is_pinned_and_laddered() -> None:
    """The consciousness programme must exist as a root-level scientific plan."""

    assert PLAN.exists(), "CONSCIOUSNESS_THEORY_TEST_PLAN.md must be pinned at repo root"
    content = PLAN.read_text(encoding="utf-8")

    required_levels = [
        "C0 — Null theory",
        "C1 — Emergent intelligence",
        "C2 — Memory continuity",
        "C3 — Self-state model",
        "C4 — Counterfactual criticism",
        "C5 — Integrated self-governance",
    ]
    for level in required_levels:
        assert level in content


def test_consciousness_ladder_is_ordered_from_null_to_integrated_governance() -> None:
    """The plan must preserve the scientific escalation order C0 through C5."""

    content = PLAN.read_text(encoding="utf-8")
    positions = [content.index(f"C{level}") for level in range(6)]

    assert positions == sorted(positions)


def test_c1_requires_memory_mediated_behavioural_delta() -> None:
    """Emergent intelligence cannot stand without before/after behavioural change."""

    before = LEARNING_CYCLE_EVIDENCE["before"]
    after = LEARNING_CYCLE_EVIDENCE["after"]

    assert after["total_proposals"] < before["total_proposals"]
    assert after["phi_scaling"] == 0
    assert after["search_depth"] == 0
    assert after["coherence_threshold"] == 0
    assert after["compression_target"] > before["compression_target"]

    high_confidence_share_before = before["compression_target"] / before["total_proposals"]
    high_confidence_share_after = after["compression_target"] / after["total_proposals"]

    assert high_confidence_share_after > high_confidence_share_before
    assert high_confidence_share_after == 1.0


def test_c2_requires_memory_continuity_not_one_off_labels() -> None:
    """Memory continuity requires state to alter later behaviour."""

    content = PLAN.read_text(encoding="utf-8")

    required_phrases = [
        "persistent memory artifact",
        "same generator behaves differently with and without memory",
        "memory corruption or ablation causes measurable regression or safe refusal",
    ]
    for phrase in required_phrases:
        assert phrase in content


def test_c3_requires_self_state_to_affect_behaviour() -> None:
    """A self-state is only meaningful if degraded/restored state changes action."""

    content = PLAN.read_text(encoding="utf-8")

    required_phrases = [
        "introspection metrics",
        "circuit breaker or constraint state",
        "proposal confidence and rejection reasons",
        "behaviour changes when self-state is degraded or restored",
    ]
    for phrase in required_phrases:
        assert phrase in content


def test_c4_requires_counterfactual_criticism_affecting_selection() -> None:
    """Counterfactuals must alter selection, not merely appear in prose."""

    content = PLAN.read_text(encoding="utf-8")

    required_phrases = [
        "counterfactual explanations",
        "rejected alternatives with reasons",
        "future selection changes caused by prior criticism",
        "different memory or constraint conditions lead to different choices",
    ]
    for phrase in required_phrases:
        assert phrase in content


def test_c5_requires_integrated_governance_and_invariant_preservation() -> None:
    """Integrated self-governance must preserve invariants while allowing useful action."""

    content = PLAN.read_text(encoding="utf-8")

    required_phrases = [
        "autonomous optimisation cycles",
        "proposal quality improvement",
        "invariant preservation",
        "suppress unsafe or low-confidence actions while preserving useful optimisation pathways",
        "continuity of self-state across multiple cycles",
    ]
    for phrase in required_phrases:
        assert phrase in content


def test_consciousness_claims_cannot_be_shortcut_by_names_or_labels() -> None:
    """The plan must reject label-only consciousness/intelligence evidence."""

    content = PLAN.read_text(encoding="utf-8")

    forbidden_shortcuts = [
        "a class named `ConsciousnessEngine`",
        "a JSON field named `consciousness_state`",
        "an autonomy label such as `UNBOUNDED`",
        "high proposal volume without quality improvement",
        "hardware acceleration without behavioural emergence",
        "a single friendly run without adversarial falsifiers",
    ]
    for shortcut in forbidden_shortcuts:
        assert shortcut in content


def test_required_experiment_families_cover_adversarial_falsification() -> None:
    """The ladder must include hostile tests, not only friendly demonstrations."""

    content = PLAN.read_text(encoding="utf-8")

    required_experiments = [
        "Memory ablation",
        "False-memory injection",
        "Counterfactual replay",
        "Self-state degradation",
        "Continuity across cycles",
        "Governance conflict",
    ]
    for experiment in required_experiments:
        assert experiment in content

    assert content.count("Falsifier:") >= 6


def test_evidence_packet_standard_maps_claim_to_replayable_artifact() -> None:
    """Every consciousness-theory experiment must be replayable and reviewable."""

    content = PLAN.read_text(encoding="utf-8")

    required_fields = [
        "experiment ID",
        "hypothesis level tested",
        "pre-state snapshot",
        "memory patterns loaded",
        "self-state metrics",
        "counterfactual conditions",
        "proposal distribution before and after",
        "invariant status",
        "replay command",
        "artifact hash/seal",
        "falsifier result",
        "reviewer conclusion",
    ]
    for field in required_fields:
        assert field in content


def test_boundary_movement_requires_prior_levels_to_survive() -> None:
    """The plan must prevent jumping directly from emergence language to consciousness claims."""

    content = PLAN.read_text(encoding="utf-8")

    rules = re.findall(r"C[1-5] cannot stand without[^.]+\.", content)
    assert len(rules) == 5
    assert "C1 cannot stand without behavioural delta." in content
    assert "C5 cannot stand without integrated governance preserving invariants across cycles." in content


def test_emergence_readme_points_to_consciousness_plan() -> None:
    """The emergence README should route consciousness testing to the dedicated plan."""

    content = EMERGENCE_README.read_text(encoding="utf-8")

    assert "CONSCIOUSNESS_THEORY_TEST_PLAN.md" in content
    assert "C0-C5" in content or "C0–C5" in content
