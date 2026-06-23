"""Sovereign SelfHealingReactor tests.

These tests cover only the gap layer above the existing Salamander math:
DamageReport -> code target -> sealed proposal -> governance envelope. They also
verify that the lane manager can route scarring/fidelity events into SHR without
auto-applying code.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY_BACKEND = ROOT / "python_backend"
if str(PY_BACKEND) not in sys.path:
    sys.path.insert(0, str(PY_BACKEND))

from pythia_mining.regeneration_manager import (
    RegenerationEventRecord,
    RegenerationManager,
)
from pythia_self_healing import DamageReport, SalamanderRegenerator, SelfHealingReactor


def _write_module(tmp_path: Path, body: str) -> Path:
    module = tmp_path / "target_module.py"
    module.write_text(body, encoding="utf-8")
    return module


def test_reactor_stages_sovereign_packet_with_governance_envelope(
    tmp_path: Path,
) -> None:
    module = _write_module(
        tmp_path,
        "def target():\n" "    # TODO: restore invariant\n" "    return 1\n",
    )
    reactor = SelfHealingReactor(SalamanderRegenerator())
    report = DamageReport(
        {
            "needs_repair": True,
            "lane_id": 7,
            "issues": ["scarring/fidelity anomaly detected in Salamander lane"],
            "blastema_state": {"entropy": 0.42},
            "progenitor_state": {"progenitor_id": "PROG_07_GEN_0001"},
            "metrics_before": {"post_recovery_fidelity": 0.91},
            "metrics_target": {"minimum_fidelity": 0.999},
            "performance_impact": "LANE_LOCAL",
            "stability_impact": "SCARRING_RISK",
        }
    )

    staged = reactor.heal_damage(report, str(module), "target")

    assert staged["status"] == "HEALING_PROPOSAL_STAGED"
    assert staged["action"] == "ESCALATE_TO_SOVEREIGN_HUMAN"
    assert staged["sovereign_human_gate"] is True
    assert staged["small_limb_rule_enforced"] is True
    assert staged["auto_apply"] is False
    assert staged["packet"]["guards"]["human_sovereign_required"] is True
    assert staged["packet"]["guards"]["auto_apply"] is False
    envelope = staged["governance_envelope"]
    assert envelope["lane_id"] == 7
    assert envelope["before_metrics"] == {"post_recovery_fidelity": 0.91}
    assert envelope["after_metrics_expected"] == {"minimum_fidelity": 0.999}
    assert envelope["stability_impact"] == "SCARRING_RISK"
    assert "heal" in envelope["protocol_steps"]
    assert "benchmark" in envelope["protocol_steps"]


def test_reactor_optimise_hot_path_reuses_sovereign_guard_pipeline(
    tmp_path: Path,
) -> None:
    module = _write_module(
        tmp_path,
        "def target(value):\n" "    return value * 2\n",
    )
    reactor = SelfHealingReactor(SalamanderRegenerator())
    staged = reactor.optimise_hot_path(
        DamageReport({"needs_repair": True, "issues": ["latency variance detected"]}),
        str(module),
        "target",
    )

    assert staged["status"] == "OPTIMISATION_PROPOSAL_STAGED"
    assert staged["protocol_step"] == "optimise"
    assert staged["sovereign_human_gate"] is True
    assert staged["packet"]["action"] == "ESCALATE_TO_SOVEREIGN_HUMAN"
    assert (
        "performance" in staged["packet"]["improvement_goal"].lower()
        or "latency" in staged["packet"]["improvement_goal"].lower()
    )


def test_reactor_escalates_structural_damage_to_rewiring_orchestrator(
    tmp_path: Path,
) -> None:
    module = _write_module(
        tmp_path,
        "def target():\n" "    return 'ok'\n",
    )
    reactor = SelfHealingReactor(SalamanderRegenerator())
    staged = reactor.heal_damage(
        DamageReport(
            {
                "needs_repair": True,
                "issues": ["structural dependency graph brittleness requires rewire"],
            }
        ),
        str(module),
        "target",
    )

    assert staged["action"] == "ESCALATE_TO_REWIRING_ORCHESTRATOR"
    assert staged["governance_envelope"]["architecture_impact"] == "LOCAL_LIMB"
    assert staged["auto_apply"] is False


def test_reactor_rejects_oversized_limb(tmp_path: Path) -> None:
    body = (
        "def target():\n"
        + "\n".join(f"    x_{i} = {i}" for i in range(130))
        + "\n    return 1\n"
    )
    module = _write_module(tmp_path, body)
    reactor = SelfHealingReactor(
        SalamanderRegenerator(max_limb_size=120), max_limb_size=120
    )

    staged = reactor.heal_damage(
        DamageReport({"needs_repair": True, "issues": ["technical debt"]}),
        str(module),
        "target",
    )

    assert staged["status"] == "HEALING_REJECTED"
    assert staged["action"] == "NO_CHANGE_APPLIED"
    assert staged["small_limb_rule_enforced"] is False
    assert "small-limb" in staged["packet"]["reason"]


def test_regeneration_manager_routes_lane_event_to_reactor_without_auto_apply(
    tmp_path: Path,
) -> None:
    module = _write_module(
        tmp_path,
        "def lane_target():\n" "    return 'healthy'\n",
    )
    manager = RegenerationManager()
    manager.register_lane_target(3, str(module), "lane_target")
    event = RegenerationEventRecord(
        timestamp=datetime.now(timezone.utc),
        lane_id=3,
        module_id="lane_03_phi_primary",
        pre_injury_phi=manager.system_phi,
        post_recovery_fidelity=0.75,
        scarring_detected=True,
        recovery_duration_ms=12.0,
        status="malformed_quarantined",
        collapsed_role="malformed",
        trace={"status": "malformed_quarantined"},
    )

    staged = manager.stage_self_healing_for_lane(3, str(module), "lane_target", event)

    assert staged["status"] == "HEALING_PROPOSAL_STAGED"
    assert staged["deployable_without_approval"] is False
    assert staged["sovereign_human_gate"] is True
    assert staged["governance_envelope"]["lane_id"] == 3
    assert manager.healing_proposals[-1] is staged
    status = manager.get_status()
    assert status["healing_proposals_staged"] == 1
    assert status["lanes"][3]["target_registered"] is True
