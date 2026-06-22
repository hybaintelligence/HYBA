"""Fields-rigour tests for Salamander organism-level autonomics.

These tests prove the next frontier above the lane-level math and SHR:
CLRI, TRM, predictive healing, hierarchical rewiring, benchmark evolution,
Pulvini handshake metadata, regulator evidence sealing, immutable invariant
guards, and adversarial rejection. Every output is proposal/evidence only and
remains sovereign-gated.
"""

from __future__ import annotations

import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PY_BACKEND = ROOT / "python_backend"
if str(PY_BACKEND) not in sys.path:
    sys.path.insert(0, str(PY_BACKEND))

from pythia_mining.regeneration_manager import RegenerationEventRecord, RegenerationManager
from pythia_self_healing import (
    AutonomicInvariantError,
    CrossLaneRegenerationIntelligence,
    ImmutableInvariantGuard,
    PredictiveRegenerationEngine,
    PulviniAutonomicHandshake,
    RegulatorEvidenceEngine,
    SalamanderOrganismGovernor,
    TemporalRegenerationMemory,
)
from pythia_self_healing.autonomic_organism_governor import OrganismSignal


def _event(
    lane_id: int,
    *,
    fidelity: float = 0.75,
    scarring: bool = True,
    status: str = "malformed_quarantined",
    phi: float = 1.61803398875,
) -> RegenerationEventRecord:
    return RegenerationEventRecord(
        timestamp=datetime.now(timezone.utc),
        lane_id=lane_id,
        module_id=f"lane_{lane_id:02d}_phi_primary",
        pre_injury_phi=phi,
        post_recovery_fidelity=fidelity,
        scarring_detected=scarring,
        recovery_duration_ms=10.0 + lane_id,
        status=status,
        collapsed_role="malformed" if status != "success" else "healthy_specialized",
        trace={"status": status},
    )


def _packet(lane_id: int, target: str = "target") -> dict:
    return {
        "status": "HEALING_PROPOSAL_STAGED",
        "target": target,
        "action": "ESCALATE_TO_SOVEREIGN_HUMAN",
        "sovereign_human_gate": True,
        "auto_apply": False,
        "packet": {"packet_id": f"PKT-{lane_id}", "seal": f"seal-{lane_id}"},
        "governance_envelope": {
            "lane_id": lane_id,
            "stability_impact": "SCARRING_RISK",
            "architecture_impact": "LOCAL_LIMB",
        },
    }


def test_clri_detects_correlated_scarring_and_multi_limb_sequence() -> None:
    signals = [
        OrganismSignal.from_event(_event(1)),
        OrganismSignal.from_event(_event(2)),
        OrganismSignal.from_event(_event(3, fidelity=0.995)),
    ]

    report = CrossLaneRegenerationIntelligence().analyse(
        signals,
        phi_floor=0.45,
        scar_free_fidelity_floor=0.999,
    )

    finding_types = {finding["finding_type"] for finding in report["findings"]}
    assert "correlated_scarring" in finding_types
    assert "shared_regeneration_status_anomaly" in finding_types
    assert report["collapse_validation_scope"] == "multi_lane"
    assert [item["lane_id"] for item in report["multi_limb_regeneration_sequence"]][:2] == [1, 2]
    assert report["sovereign_human_gate"] is True
    assert report["auto_apply"] is False


def test_clri_properties_are_deterministic_bounded_and_deduplicate_lanes() -> None:
    engine = CrossLaneRegenerationIntelligence()
    signals = [
        OrganismSignal.from_event(_event(2, fidelity=0.80)),
        OrganismSignal.from_event(_event(2, fidelity=0.78)),
        OrganismSignal.from_event(_event(1, fidelity=0.90)),
    ]

    first = engine.analyse(signals, phi_floor=0.45, scar_free_fidelity_floor=0.999)
    second = engine.analyse(list(reversed(signals)), phi_floor=0.45, scar_free_fidelity_floor=0.999)

    assert first["analysis_id"] == second["analysis_id"]
    assert 0.0 <= first["minimum_fidelity"] <= first["mean_fidelity"] <= 1.0
    correlated = next(f for f in first["findings"] if f["finding_type"] == "correlated_scarring")
    assert correlated["lanes"] == [1, 2]
    assert all(item["auto_apply"] is False for item in first["multi_limb_regeneration_sequence"])


def test_temporal_regeneration_memory_is_append_only_and_detects_recurrence() -> None:
    memory = TemporalRegenerationMemory()
    first = memory.record(_packet(4, target="alpha"))
    second = memory.record(_packet(4, target="alpha"))

    summary = memory.summarise()

    assert first["previous_hash"] == "GENESIS"
    assert second["previous_hash"] == first["chain_hash"]
    assert summary["chain_valid"] is True
    assert summary["recurring_lanes"] == [4]
    assert summary["recurring_targets"] == ["alpha"]
    assert summary["auto_apply"] is False


def test_temporal_memory_export_is_immutable_and_private_tampering_is_detected() -> None:
    memory = TemporalRegenerationMemory()
    memory.record(_packet(1))
    exported = memory.records

    with pytest.raises(TypeError):
        exported[0]["target"] = "mutated"  # type: ignore[index]

    assert memory.validate_chain() is True
    memory._records[0]["target"] = "mutated"  # deliberate adversarial internal tamper
    assert memory.validate_chain() is False
    with pytest.raises(AutonomicInvariantError):
        memory.assert_chain_valid()


def test_temporal_memory_rejects_auto_apply_packets() -> None:
    memory = TemporalRegenerationMemory()
    hostile = _packet(9)
    hostile["auto_apply"] = True

    with pytest.raises(AutonomicInvariantError):
        memory.record(hostile)


def test_predictive_regeneration_uses_clri_and_temporal_memory() -> None:
    signal = OrganismSignal.from_event(_event(5, fidelity=0.91, scarring=True))
    clri_report = {
        "findings": [
            {
                "finding_type": "correlated_scarring",
                "severity": "elevated",
                "lanes": [5, 6],
                "evidence": {},
                "recommendation": "stage multi-limb proposal",
            }
        ]
    }
    temporal_summary = {"recurring_lanes": [5]}

    forecast = PredictiveRegenerationEngine().forecast(
        [signal],
        temporal_summary=temporal_summary,
        clri_report=clri_report,
        scar_free_fidelity_floor=0.999,
    )

    assert forecast["status"] == "PRE_DAMAGE_PROPOSALS_AVAILABLE"
    assert forecast["predictions"][0]["lane_id"] == 5
    assert "temporal_recurrence" in forecast["predictions"][0]["drivers"]
    assert "cross_lane_correlation" in forecast["predictions"][0]["drivers"]
    assert forecast["predictions"][0]["risk_band"] in {"watch", "elevated", "critical"}
    assert 0.0 <= forecast["predictions"][0]["risk_score"] <= 1.0
    assert forecast["auto_apply"] is False


def test_organism_signal_rejects_invalid_metrics() -> None:
    with pytest.raises(AutonomicInvariantError):
        OrganismSignal(
            lane_id=1,
            module_id="lane_01",
            pre_injury_phi=math.inf,
            post_recovery_fidelity=0.9,
            scarring_detected=False,
            recovery_duration_ms=1.0,
            status="success",
        )
    with pytest.raises(AutonomicInvariantError):
        OrganismSignal(
            lane_id=1,
            module_id="lane_01",
            pre_injury_phi=1.0,
            post_recovery_fidelity=1.5,
            scarring_detected=False,
            recovery_duration_ms=1.0,
            status="success",
        )


def test_invariant_guard_rejects_nested_auto_apply_and_direct_deploy_actions() -> None:
    guard = ImmutableInvariantGuard()
    with pytest.raises(AutonomicInvariantError):
        guard.assert_proposal_only({"outer": {"auto_apply": True}}, context="hostile nested packet")
    with pytest.raises(AutonomicInvariantError):
        guard.assert_proposal_only({"action": "DEPLOY", "auto_apply": False}, context="hostile action")


def test_pulvini_handshake_rejects_hostile_candidate_exchange() -> None:
    with pytest.raises(AutonomicInvariantError):
        PulviniAutonomicHandshake().stage(
            clri_report={"analysis_id": "CLRI-test", "findings": []},
            pulvini_state={"algorithmic_alternatives": [{"name": "unsafe", "auto_apply": True}]},
        )


def test_manager_emits_organism_level_governance_report_with_regulator_evidence() -> None:
    manager = RegenerationManager()
    manager.fidelity_history.extend([
        _event(1, fidelity=0.80),
        _event(2, fidelity=0.82),
        _event(3, fidelity=0.997),
    ])
    manager.healing_proposals.extend([_packet(1), _packet(2)])

    report = manager.analyse_organism_governance(
        pulvini_state={"algorithmic_alternatives": [{"name": "phi_memory_rebalance", "status": "candidate"}]}
    )

    assert report["status"] == "ORGANISM_GOVERNANCE_STAGED"
    assert report["sovereign_human_gate"] is True
    assert report["auto_apply"] is False
    assert report["stable_core_guard"] is True
    assert report["source_modified"] is False
    assert report["stable_core_modified"] is False
    assert report["clri"]["collapse_validation_scope"] == "multi_lane"
    assert report["predictive_regeneration"]["status"] == "PRE_DAMAGE_PROPOSALS_AVAILABLE"
    assert report["hierarchical_rewiring"]["tier"] in {"REGIONAL_ORGAN", "GLOBAL_ORGANISM"}
    assert report["benchmark_evolution"]["proposed_tests"]
    assert report["pulvini_handshake"]["candidate_exchange"] == [{"name": "phi_memory_rebalance", "status": "candidate"}]
    evidence = report["regulator_evidence"]
    assert evidence["evidence_id"].startswith("SALAMANDER-ORGANISM-EVIDENCE-")
    assert evidence["sovereign_human_gate"] is True
    assert evidence["auto_apply"] is False
    assert evidence["seal"]
    assert RegulatorEvidenceEngine().verify(evidence, {k: v for k, v in report.items() if k != "regulator_evidence"}) is True


def test_regulator_evidence_verification_rejects_tampered_report() -> None:
    engine = RegulatorEvidenceEngine()
    report = {"status": "ORGANISM_GOVERNANCE_STAGED", "auto_apply": False, "sovereign_human_gate": True}
    evidence = engine.seal(report)
    tampered = dict(report)
    tampered["status"] = "MUTATED"

    assert engine.verify(evidence, report) is True
    assert engine.verify(evidence, tampered) is False


def test_governor_direct_entrypoint_preserves_non_deploying_contract() -> None:
    manager = RegenerationManager()
    manager.fidelity_history.append(_event(8, fidelity=0.76))
    governor = SalamanderOrganismGovernor()

    report = governor.analyse_manager(manager)

    assert report["status"] == "ORGANISM_GOVERNANCE_STAGED"
    assert report["hierarchical_rewiring"]["action"] == "ESCALATE_TO_SOVEREIGN_HUMAN"
    assert report["hierarchical_rewiring"]["auto_apply"] is False
    assert report["benchmark_evolution"]["auto_apply"] is False
    assert report["benchmark_evolution"]["benchmark_committed"] is False
    assert report["pulvini_handshake"]["auto_apply"] is False
    assert report["regulator_evidence"]["invariant_claims"][-1] == "temporal_memory_chain_valid"
