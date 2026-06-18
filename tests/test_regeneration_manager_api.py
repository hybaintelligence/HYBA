"""Coverage for the operator-facing regeneration manager."""

from __future__ import annotations

import asyncio

import pytest

from pythia_mining.regeneration_manager import RegenerationManager


def test_blastema_pool_reports_32_model_derived_lanes() -> None:
    manager = RegenerationManager()

    pool = manager.get_blastema_pool()

    assert len(pool) == 32
    assert pool[0]["lane_id"] == 0
    assert pool[0]["l3_residency_time_ms"] is None
    assert "no measured L3 residency" in pool[0]["evidence_source"]


def test_trigger_regeneration_records_fidelity_event() -> None:
    manager = RegenerationManager()

    event = asyncio.run(manager.trigger_regeneration(0))

    assert event.lane_id == 0
    assert event.status == "success"
    assert event.post_recovery_fidelity == pytest.approx(0.7938926261462365)
    assert event.scarring_detected is True
    assert manager.get_status()["fidelity_events"] == 1


def test_trigger_regeneration_rejects_invalid_lane() -> None:
    manager = RegenerationManager()

    with pytest.raises(ValueError, match="Invalid lane_id"):
        asyncio.run(manager.trigger_regeneration(32))
