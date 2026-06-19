"""Behavioral tests for AutonomousMiningController boot path.

These tests close the Layer 1/Layer 2 gap identified in the audit:
substring checks confirmed the right *names* exist — these tests confirm
the methods *execute* and return data with the required shape.

All tests use a temp persistence_dir and a minimal fake engine so no
real hardware, network, or pool connections are exercised.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Minimal fake engine — satisfies the duck-type surface AutonomousMiningController
# touches during boot.  No real mining, no network.
# ---------------------------------------------------------------------------

class _FakeEngine:
    """Minimal duck-type stand-in for UnifiedMiningEngine."""

    phi_density: float = 0.55

    # Attributes accessed by seek_improvement / reflexive cycle / apply_self_optimization.
    # Set to None so the "if self.engine.x is not None" guards in apply_self_optimization
    # skip the real mutations without raising AttributeError.
    current_job = None
    stratum_client = None
    phi_ensemble = None
    optimizer = None
    solver = None
    consciousness = None

    def get_hashrate(self) -> float:
        return 0.0

    def get_phi_density(self) -> float:
        return self.phi_density

    def get_state(self) -> dict:
        return {"status": "idle"}

    # Phi scaling engine proxy used by reflexive cycle
    class _PhiScaling:
        phi_scaling = 1.5
        search_depth = 60
        coherence_threshold = 0.45
        compression_target = 1.86

    phi_scaling_engine = _PhiScaling()


def _make_controller(tmp_dir: str):
    """Instantiate a real AutonomousMiningController wired to the fake engine."""
    # Import here so test collection never fails if deps are missing
    from pythia_mining.autonomous_mining_controller import (
        AutonomousConfig,
        AutonomyLevel,
        AutonomousMiningController,
    )
    from pythia_mining.autonomous_audit_persistence import AuditJournal, AutonomousAuditLogger
    from pythia_mining.autonomous_escalation import AutonomousEscalationEngine

    config = AutonomousConfig(
        autonomy_level=AutonomyLevel.SUPERVISED,
        persistence_enabled=True,
        persistence_dir=tmp_dir,
        reflexive_loop_enabled=True,
        compression_drive_enabled=False,  # keep test fast
        max_proposals_per_cycle=1,
        virtual_session_horizon=0.01,  # 10 ms — minimal simulation
    )
    ctrl = AutonomousMiningController(_FakeEngine(), config=config)
    # Replace the default audit logger (backed by the shared 490 MB dir) with an
    # isolated one so flush() completes instantly and tests are hermetic.
    audit_dir = os.path.join(tmp_dir, "audit")
    ctrl._persistent_audit_logger = AutonomousAuditLogger(
        journal=AuditJournal(journal_dir=audit_dir)
    )
    ctrl._escalation_engine = AutonomousEscalationEngine(
        audit_logger=ctrl._persistent_audit_logger,
        escalation_callback=lambda level: ctrl.set_autonomy_level(
            AutonomyLevel(level)
        ),
        degradation_callback=lambda reason: ctrl.degrade_autonomy_level(reason).value,
    )
    return ctrl


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_boot_self_heal_returns_required_keys():
    """boot_self_heal_and_optimize must complete and return a dict with the
    fields the lifespan hook and governance doc reference."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)
        report = await ctrl.boot_self_heal_and_optimize()

    assert isinstance(report, dict), "boot_self_heal_and_optimize must return a dict"
    assert report.get("startup_self_healing_executed") is True, (
        "startup_self_healing_executed must be True on a clean boot (no circuit-breaker)"
    )
    assert "duration_ms" in report, "duration_ms must be present for SLO tracking"
    assert "before" in report, "before snapshot must be present"
    assert "after" in report, "after snapshot must be present"
    assert "reflexive_report" in report, "reflexive_report must be present"


@pytest.mark.asyncio
async def test_boot_self_heal_duration_is_positive():
    """duration_ms must be a positive number — sanity check the clock path."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)
        report = await ctrl.boot_self_heal_and_optimize()

    assert isinstance(report["duration_ms"], (int, float))
    assert report["duration_ms"] > 0


@pytest.mark.asyncio
async def test_boot_self_heal_reflexive_report_shape():
    """reflexive_report must contain the fields the contract test grep for."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)
        report = await ctrl.boot_self_heal_and_optimize()

    rr = report["reflexive_report"]
    assert rr.get("reflexive_cycle_executed") is True
    assert "proposals_generated" in rr
    assert "proposals_applied" in rr
    assert isinstance(rr["proposals_generated"], int)
    assert isinstance(rr["proposals_applied"], int)
    assert rr["proposals_applied"] <= rr["proposals_generated"]


@pytest.mark.asyncio
async def test_seek_improvement_returns_before_timeout():
    """seek_improvement must resolve in well under 5 s (virtual_session_horizon=10 ms)."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)
        t0 = time.monotonic()
        result = await ctrl.seek_improvement()
        elapsed = time.monotonic() - t0

    assert result.get("reflexive_cycle_executed") is True
    assert elapsed < 5.0, f"seek_improvement took {elapsed:.2f}s — exceeds 5s guard"


# ---------------------------------------------------------------------------
# Stale lock tests — behavioural, not grep
# ---------------------------------------------------------------------------


def test_clean_stale_lock_removes_dead_pid_lock():
    """A lock file whose embedded PID is dead must be removed on boot."""
    with tempfile.TemporaryDirectory() as tmp:
        from pythia_mining.autonomous_mining_controller import (
            AutonomousConfig,
            AutonomyLevel,
            AutonomousMiningController,
        )

        # Write a stale lock with a PID that cannot exist (PID 0)
        lock_path = Path(tmp) / "reflexive_state.lock"
        lock_path.write_text(json.dumps({"pid": 0, "ts": time.time() - 9999}), encoding="utf-8")
        assert lock_path.exists(), "pre-condition: lock file must exist before boot"

        config = AutonomousConfig(
            persistence_enabled=True,
            persistence_dir=tmp,
            reflexive_loop_enabled=False,
        )
        # Constructing the controller triggers _clean_stale_lock_on_boot
        ctrl = AutonomousMiningController(_FakeEngine(), config=config)

        assert not lock_path.exists(), "stale lock must be removed after boot"
        assert ctrl._stale_state_lock_recoveries == 1, (
            "_stale_state_lock_recoveries counter must be incremented"
        )


def test_clean_stale_lock_preserves_live_pid_lock():
    """A lock file whose embedded PID is the current process must NOT be removed."""
    with tempfile.TemporaryDirectory() as tmp:
        from pythia_mining.autonomous_mining_controller import (
            AutonomousConfig,
            AutonomyLevel,
            AutonomousMiningController,
        )

        # Use os.getpid() — this PID is definitely alive
        live_pid = os.getpid()
        lock_path = Path(tmp) / "reflexive_state.lock"
        lock_path.write_text(json.dumps({"pid": live_pid, "ts": time.time()}), encoding="utf-8")

        config = AutonomousConfig(
            persistence_enabled=True,
            persistence_dir=tmp,
            reflexive_loop_enabled=False,
        )
        ctrl = AutonomousMiningController(_FakeEngine(), config=config)

        assert lock_path.exists(), "lock with a live PID must be preserved"
        assert ctrl._stale_state_lock_recoveries == 0


def test_clean_stale_lock_handles_corrupt_lock_file():
    """A lock file with corrupt content (not valid JSON) must be removed safely."""
    with tempfile.TemporaryDirectory() as tmp:
        from pythia_mining.autonomous_mining_controller import (
            AutonomousConfig,
            AutonomousMiningController,
        )

        lock_path = Path(tmp) / "reflexive_state.lock"
        lock_path.write_text("not-json-{{{", encoding="utf-8")

        config = AutonomousConfig(
            persistence_enabled=True,
            persistence_dir=tmp,
            reflexive_loop_enabled=False,
        )
        # Must not raise — corrupt lock treated as PID=0 (dead), removed
        ctrl = AutonomousMiningController(_FakeEngine(), config=config)
        assert not lock_path.exists(), "corrupt lock must be cleaned on boot"
