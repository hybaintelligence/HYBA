"""Production integration coverage for Salamander-gated mining."""

from __future__ import annotations

import asyncio
import inspect

from pythia_mining.regeneration_manager import RegenerationManager
from pythia_mining.salamander_mining_guard import SalamanderMiningGuard


def test_salamander_mining_guard_registers_core_mining_targets() -> None:
    manager = RegenerationManager()
    guard = SalamanderMiningGuard(manager)

    registrations = guard.register_mining_targets()

    assert len(registrations) == 3
    assert registrations[0]["module_path"].endswith("production_mining_system.py")
    assert manager.lanes[0].target_symbol == "ProductionMiningSystem"
    assert manager.lanes[1].target_symbol == "MiningExecutiveController"
    assert manager.lanes[2].target_symbol == "StratumClient"


def test_salamander_mining_guard_preflight_allows_same_day_non_strict_gate() -> None:
    manager = RegenerationManager()
    guard = SalamanderMiningGuard(manager)

    report = asyncio.run(guard.preflight(source="test_mining_preflight", strict=False))

    assert report.ready is True
    assert report.active_blastemas == 32
    assert report.target_registry_complete is True
    assert report.lanes_checked == [0, 1, 2]
    assert report.regeneration_statuses == ["success", "success", "success"]
    assert report.scar_events >= 1
    assert report.healing_proposals_staged >= report.scar_events


def test_salamander_mining_guard_strict_mode_blocks_scarred_gate() -> None:
    manager = RegenerationManager()
    guard = SalamanderMiningGuard(manager)

    report = asyncio.run(guard.preflight(source="test_strict_preflight", strict=True))

    assert report.ready is False
    assert report.blocker == "SALAMANDER_STRICT_SCAR_LOCK"


def test_mining_executive_ignition_requires_salamander_gate() -> None:
    from pythia_mining import mining_executive_controller as module

    source = inspect.getsource(module.MiningExecutiveController.ignite_manifold)

    assert "await self.salamander_guard.preflight" in source
    assert "SALAMANDER_LOCK" in source
    assert "self.last_salamander_gate" in source


def test_production_mining_harness_does_not_fabricate_live_revenue() -> None:
    from pythia_mining import production_mining_system as module

    source = inspect.getsource(module.ProductionMiningSystem)

    assert "self.estimated_revenue_btc = 0.0" in source
    assert "time.time() % 1.0" not in source
    assert "live_pool_result_only" in source
    assert "SalamanderMiningGuard" in source
    assert "prepare_for_live_mining" in source
