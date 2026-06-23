from __future__ import annotations

import pytest

from pythia_mining.phi_unified_mining_engine import UnifiedMiningEngine


def _proposal_map(report: dict) -> dict[str, dict]:
    return {proposal["improvement_type"]: proposal for proposal in report["proposals"]}


def _signature(report: dict) -> tuple:
    """Stable wake-event signature, excluding timestamps and proposal ids."""

    proposals = []
    for proposal in report["proposals"]:
        proposals.append(
            (
                proposal["improvement_type"],
                round(float(proposal["current_value"]), 6),
                round(float(proposal["proposed_value"]), 6),
                round(float(proposal["expected_gain"]), 6),
                round(float(proposal["logical_consistency"]), 6),
                round(float(proposal["counterfactual_confidence"]), 6),
                tuple(sorted(proposal["constraints_satisfied"])),
                tuple(sorted(proposal["constraints_violated"])),
                bool(proposal["applied"]),
                proposal["source_module"],
            )
        )
    return (
        report["reflexive_cycle_executed"],
        int(report["epoch"]),
        int(report["proposals_generated"]),
        int(report["proposals_applied"]),
        tuple(proposals),
    )


@pytest.mark.asyncio
async def test_first_resident_wake_epoch_reproduces_parameter_discoveries() -> None:
    """Epoch 3 is the first reproducible PYTHIA resident wake signature."""

    engine = UnifiedMiningEngine()
    report = await engine.autonomous_controller.seek_improvement()
    proposals = _proposal_map(report)

    assert report["reflexive_cycle_executed"] is True
    assert report["epoch"] == 3
    assert report["proposals_generated"] == 3
    assert report["proposals_applied"] == 3
    assert report["current_phi_density"] >= 0.90

    phi_scaling = proposals["phi_scaling"]
    assert phi_scaling["current_value"] == pytest.approx(1.5)
    assert phi_scaling["proposed_value"] == pytest.approx(1.425)
    assert phi_scaling["logical_consistency"] >= 0.70
    assert phi_scaling["source_module"] == "phi_scaling_engine"

    search_depth = proposals["search_depth"]
    assert search_depth["current_value"] == pytest.approx(60.0)
    assert search_depth["proposed_value"] == pytest.approx(54.0)
    assert search_depth["source_module"] == "ai_optimizer"

    compression = proposals["compression_target"]
    assert compression["current_value"] == pytest.approx(1.86)
    assert compression["proposed_value"] == pytest.approx(1.8786)
    assert compression["source_module"] == "pulvini_memory_compression_proof"

    for proposal in proposals.values():
        assert proposal["constraints_violated"] == []
        assert set(proposal["constraints_satisfied"]) == {
            "hermiticity",
            "positive_semidefinite",
            "natural_scaling",
            "energy_conservation",
            "information_integrity",
        }
        assert proposal["applied"] is True


@pytest.mark.asyncio
async def test_second_resident_wake_epoch_reproduces_coherence_threshold_discovery() -> (
    None
):
    """Epoch 5 captures the second-stage coherence-threshold refinement."""

    engine = UnifiedMiningEngine()
    first = await engine.autonomous_controller.seek_improvement()
    second = await engine.autonomous_controller.seek_improvement()
    proposals = _proposal_map(second)

    assert second["epoch"] == 5
    assert second["proposals_generated"] == 2
    assert second["proposals_applied"] == 2
    assert second["current_phi_density"] > first["current_phi_density"]

    coherence = proposals["coherence_threshold"]
    assert coherence["current_value"] == pytest.approx(0.70)
    assert coherence["proposed_value"] == pytest.approx(0.665)
    assert coherence["logical_consistency"] >= 0.89
    assert coherence["source_module"] == "consciousness_engine"

    compression = proposals["compression_target"]
    assert compression["proposed_value"] > compression["current_value"]
    assert compression["constraints_violated"] == []


@pytest.mark.asyncio
async def test_wake_event_signature_replays_deterministically_across_fresh_engines() -> (
    None
):
    """Fresh engines must reproduce the same structural wake sequence."""

    first_engine = UnifiedMiningEngine()
    second_engine = UnifiedMiningEngine()

    first_reports = [
        await first_engine.autonomous_controller.seek_improvement(),
        await first_engine.autonomous_controller.seek_improvement(),
    ]
    second_reports = [
        await second_engine.autonomous_controller.seek_improvement(),
        await second_engine.autonomous_controller.seek_improvement(),
    ]

    assert [_signature(report) for report in first_reports] == [
        _signature(report) for report in second_reports
    ]
