"""Behavioral tests for the circuit breaker and continuous autonomy monitor.

Answers two open questions from the audit:

1. Circuit breaker (boot_self_heal_and_optimize > 5 heals):
   - Is it the *same* mechanism as the escalation engine? No — it is separate.
     The escalation engine (autonomous_escalation.py) governs autonomy-level
     progression (ADVISORY→SUPERVISED→AUTONOMOUS) based on phi/acceptance metrics.
     The circuit breaker lives in boot_self_heal_and_optimize and counts raw heal
     attempts in a 10-minute sliding window; at >5 it calls
     _switch_to_backup_infrastructure() instead of running seek_improvement().
     They share zero code paths.

2. _continuous_autonomy_monitor:
   - Exception in one iteration is swallowed, loop continues.
   - Double-start is guarded (second call is a no-op).
   - stop_continuous_monitor() cancels cleanly with no CancelledError leak.

3. _seek_improvement_with_resource_awareness:
   - load > 90 → intensity decremented (ResourceThrottle recorded).
   - load < 40 with headroom → intensity incremented (ResourceExpansion recorded).
   - load in 40–90 band → neither event recorded.

4. platform_interface_get_cpu_load:
   - psutil branch returns its value when psutil is present.
   - ImportError branch falls through to os.getloadavg / _system_load fallback.
"""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers shared with the boot behavioral test file
# ---------------------------------------------------------------------------


class _FakeEngine:
    phi_density: float = 0.55
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

    class _PhiScaling:
        phi_scaling = 1.5
        search_depth = 60
        coherence_threshold = 0.45
        compression_target = 1.86

    phi_scaling_engine = _PhiScaling()


def _make_controller(tmp_dir: str, *, reflexive: bool = True):
    from pythia_mining.autonomous_mining_controller import (
        AutonomousConfig,
        AutonomyLevel,
        AutonomousMiningController,
    )
    from pythia_mining.autonomous_audit_persistence import (
        AuditJournal,
        AutonomousAuditLogger,
    )

    config = AutonomousConfig(
        autonomy_level=AutonomyLevel.SUPERVISED,
        persistence_enabled=True,
        persistence_dir=tmp_dir,
        reflexive_loop_enabled=reflexive,
        compression_drive_enabled=False,
        max_proposals_per_cycle=1,
        virtual_session_horizon=0.01,
    )
    ctrl = AutonomousMiningController(_FakeEngine(), config=config)
    # Replace the default audit logger (which loads from the shared 490 MB dir) with
    # one backed by the temp dir so flush() is fast and tests are hermetic.
    audit_dir = os.path.join(tmp_dir, "audit")
    ctrl._persistent_audit_logger = AutonomousAuditLogger(
        journal=AuditJournal(journal_dir=audit_dir)
    )
    # Re-wire the escalation engine to use the same isolated logger
    from pythia_mining.autonomous_escalation import AutonomousEscalationEngine

    ctrl._escalation_engine = AutonomousEscalationEngine(
        audit_logger=ctrl._persistent_audit_logger,
        escalation_callback=lambda level: ctrl.set_autonomy_level(
            __import__(
                "pythia_mining.autonomous_mining_controller", fromlist=["AutonomyLevel"]
            ).AutonomyLevel(level)
        ),
        degradation_callback=lambda reason: ctrl.degrade_autonomy_level(reason).value,
    )
    return ctrl


# ============================================================
# 1. CIRCUIT BREAKER — distinct from escalation engine
# ============================================================


@pytest.mark.asyncio
async def test_circuit_breaker_triggers_at_6_heal_attempts():
    """With 6 pre-existing heal attempts in the window, boot must take the
    circuit-breaker path and return startup_self_healing_executed=False."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)
        # Inject 6 timestamps inside the 10-min window
        now = time.time()
        ctrl._heal_attempt_window = [now - i * 10 for i in range(6)]

        report = await ctrl.boot_self_heal_and_optimize()

    assert report.get("startup_self_healing_executed") is False
    assert report.get("circuit_breaker_triggered") is True
    assert report.get("heal_attempts") == 6


@pytest.mark.asyncio
async def test_circuit_breaker_does_not_trigger_at_5_heal_attempts():
    """Exactly 5 attempts must NOT trigger the circuit breaker (threshold is > 5)."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)
        now = time.time()
        ctrl._heal_attempt_window = [now - i * 10 for i in range(5)]

        report = await ctrl.boot_self_heal_and_optimize()

    assert report.get("startup_self_healing_executed") is True
    assert not report.get("circuit_breaker_triggered", False)


@pytest.mark.asyncio
async def test_circuit_breaker_reset_after_window_expires():
    """Attempts older than 600 s must be pruned; stale window must not trip breaker."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)
        stale = time.time() - 700  # outside the 10-min window
        ctrl._heal_attempt_window = [stale] * 10  # 10 stale entries

        report = await ctrl.boot_self_heal_and_optimize()

    # All 10 entries are stale; window prunes to 0 before the >5 check
    assert report.get("startup_self_healing_executed") is True
    assert not report.get("circuit_breaker_triggered", False)


@pytest.mark.asyncio
async def test_circuit_breaker_fires_backup_infrastructure_event():
    """_switch_to_backup_infrastructure must be called when the breaker fires,
    resetting consecutive_failures and circuit_open_until."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)
        ctrl._consecutive_failures = 3
        ctrl._circuit_open_until = time.time() + 9999
        now = time.time()
        ctrl._heal_attempt_window = [now - i * 5 for i in range(6)]

        await ctrl.boot_self_heal_and_optimize()

    # _switch_to_backup_infrastructure resets both fields
    assert ctrl._consecutive_failures == 0
    assert ctrl._circuit_open_until == 0.0


# ============================================================
# 2. CONTINUOUS MONITOR — exception survival, double-start, clean cancel
# ============================================================


@pytest.mark.asyncio
async def test_monitor_survives_exception_in_one_iteration(caplog):
    """An exception raised inside one monitor iteration must be caught, written
    to the tamper-evident audit log, and not propagate out of the loop.

    The monitor except branch now calls _log_audit_event (structured chain) AND
    _log_event (Python logger), so we assert both sinks receive the event.
    """
    import logging

    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp, reflexive=False)

        async def _raises_once() -> None:
            ctrl.is_running = False
            raise RuntimeError("simulated transient monitor error")

        ctrl._seek_improvement_with_resource_awareness = _raises_once

        original_snapshot = ctrl.get_metrics_snapshot

        def _healthy_snapshot():
            snap = original_snapshot()
            snap["phi_density"] = 0.9
            return snap

        ctrl.get_metrics_snapshot = _healthy_snapshot

        with caplog.at_level(logging.ERROR, logger="pythia.autonomy.monitor"):
            await ctrl.start_continuous_monitor()
            for _ in range(10):
                await asyncio.sleep(0)
            await ctrl.stop_continuous_monitor()

    # 1. Python logger received the ERROR
    error_records = [
        r
        for r in caplog.records
        if r.levelno == logging.ERROR
        and "simulated transient monitor error" in r.message
    ]
    assert (
        len(error_records) == 1
    ), f"Expected 1 ERROR log for the swallowed exception, got {len(error_records)}"

    # 2. The tamper-evident audit_log also has the event (chain completeness)
    monitor_error_entries = [
        e for e in ctrl.audit_log if e.event_type == "monitor_error"
    ]
    assert len(monitor_error_entries) == 1, (
        f"Expected 1 monitor_error AuditLogEntry, got {len(monitor_error_entries)} "
        "(exception must land in the tamper-evident chain, not only the ephemeral logger)"
    )


@pytest.mark.asyncio
async def test_monitor_double_start_is_no_op():
    """Calling start_continuous_monitor twice must not spawn a second task."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp, reflexive=False)

        # Block the loop at the resource-check step so it never reaches asyncio.sleep(60)
        hold = asyncio.Event()

        async def _blocking_resource_check() -> None:
            await hold.wait()

        ctrl._seek_improvement_with_resource_awareness = _blocking_resource_check

        await ctrl.start_continuous_monitor()
        # Yield so the task enters _blocking_resource_check
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        first_task = ctrl._monitor_task

        # Second start — must be a no-op
        await ctrl.start_continuous_monitor()
        second_task = ctrl._monitor_task

        await ctrl.stop_continuous_monitor()

    assert (
        first_task is second_task
    ), "second start_continuous_monitor must reuse the existing task"


@pytest.mark.asyncio
async def test_monitor_stop_does_not_leak_cancelled_error():
    """stop_continuous_monitor must cancel the task and not let CancelledError propagate.

    Strategy: replace _seek_improvement_with_resource_awareness with a coroutine
    that blocks on an Event.  The monitor loop reaches that await, suspends, and
    stop_continuous_monitor() can then cancel it cleanly — without patching
    asyncio.sleep globally (which would also block the test body).
    """
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp, reflexive=False)

        # Make the loop body block on an event rather than completing immediately
        hold = asyncio.Event()

        async def _blocking_resource_check() -> None:
            await hold.wait()  # suspends here; cancelled by stop_continuous_monitor

        ctrl._seek_improvement_with_resource_awareness = _blocking_resource_check

        await ctrl.start_continuous_monitor()
        # Yield to let the monitor task run until it hits hold.wait()
        await asyncio.sleep(0)
        await asyncio.sleep(0)

        # stop must cancel the blocked task without raising
        await ctrl.stop_continuous_monitor()

    assert ctrl._monitor_task is None
    assert ctrl.is_running is False


# ============================================================
# 3. RESOURCE AWARENESS — throttle, expand, neutral band
# ============================================================


@pytest.mark.asyncio
async def test_resource_awareness_throttles_above_90_percent():
    """system_load > 90 must decrement intensity and record ResourceThrottle."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp, reflexive=False)
        ctrl._current_intensity = 7
        ctrl.platform_interface_get_cpu_load = lambda: 95.0

        await ctrl._seek_improvement_with_resource_awareness()

    assert ctrl._current_intensity == 6  # decremented by 1
    throttle_events = [
        e for e in ctrl._autonomy_journal if e.get("event_type") == "ResourceThrottle"
    ]
    assert len(throttle_events) == 1
    assert throttle_events[0]["data"]["system_load"] == 95.0


@pytest.mark.asyncio
async def test_resource_awareness_expands_below_40_percent():
    """system_load < 40 with intensity headroom must increment intensity and
    record ResourceExpansion."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp, reflexive=False)
        ctrl._current_intensity = 5  # < 10, so there is headroom
        ctrl.platform_interface_get_cpu_load = lambda: 25.0

        await ctrl._seek_improvement_with_resource_awareness()

    assert ctrl._current_intensity == 6
    expansion_events = [
        e for e in ctrl._autonomy_journal if e.get("event_type") == "ResourceExpansion"
    ]
    assert len(expansion_events) == 1


@pytest.mark.asyncio
async def test_resource_awareness_neutral_band_no_event():
    """system_load in the 40–90 band must not record Throttle or Expansion."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp, reflexive=False)
        initial_intensity = ctrl._current_intensity
        ctrl.platform_interface_get_cpu_load = lambda: 60.0

        await ctrl._seek_improvement_with_resource_awareness()

    assert ctrl._current_intensity == initial_intensity
    neutral_events = [
        e
        for e in ctrl._autonomy_journal
        if e.get("event_type") in ("ResourceThrottle", "ResourceExpansion")
    ]
    assert len(neutral_events) == 0


@pytest.mark.asyncio
async def test_resource_awareness_does_not_exceed_intensity_floor():
    """Intensity must not drop below 1 even under repeated throttle calls."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp, reflexive=False)
        ctrl._current_intensity = 1
        ctrl.platform_interface_get_cpu_load = lambda: 99.0

        await ctrl._seek_improvement_with_resource_awareness()

    assert ctrl._current_intensity == 1  # floor enforced


@pytest.mark.asyncio
async def test_resource_awareness_does_not_exceed_intensity_ceiling():
    """Intensity must not rise above 10 even under repeated expansion calls."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp, reflexive=False)
        ctrl._current_intensity = 10
        ctrl.platform_interface_get_cpu_load = lambda: 5.0

        await ctrl._seek_improvement_with_resource_awareness()

    assert ctrl._current_intensity == 10  # ceiling enforced


# ============================================================
# 4. platform_interface_get_cpu_load — branch coverage
# ============================================================


def test_cpu_load_psutil_branch():
    """When psutil is importable, its cpu_percent value must be returned."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp, reflexive=False)

        fake_psutil = MagicMock()
        fake_psutil.cpu_percent.return_value = 42.5

        with patch.dict("sys.modules", {"psutil": fake_psutil}):
            # Re-invoke so the import inside the method picks up our mock
            result = ctrl.platform_interface_get_cpu_load()

    assert result == 42.5


# ============================================================
# 5. AuditJournal rotation — init cost bounded, disk pruned
# ============================================================


def test_audit_journal_init_loads_only_recent_segments():
    """Constructing AuditJournal against a directory with many segments must
    load only the most recent _LOAD_SEGMENTS_LIMIT segments into memory,
    not the full history.  This is the regression test for the 490 MB
    unbounded-load bug."""
    from pythia_mining.autonomous_audit_persistence import (
        AuditJournal,
        ImmutableAuditEntry,
        _LOAD_SEGMENTS_LIMIT,
        _MAX_SEGMENTS_ON_DISK,
    )

    with tempfile.TemporaryDirectory() as tmp:
        # Write _LOAD_SEGMENTS_LIMIT + 3 synthetic segments, each with 2 entries
        total_segments = _LOAD_SEGMENTS_LIMIT + 3
        for i in range(total_segments):
            seg_id = 1000000000000 + i  # ascending timestamps
            seg_path = Path(tmp) / f"audit_segment_{seg_id}.json"
            entry = {
                "entry_id": f"e{i}",
                "timestamp": float(i),
                "event_type": f"seg_{i}",
                "autonomy_level": "advisory",
                "decision_id": None,
                "action": "",
                "outcome": "",
                "constraints_checked": [],
                "constraints_violated": [],
                "operator_id": None,
                "operator_action": None,
                "state_diff": {},
                "checksum_sha256": "",
                "previous_entry_checksum": "",
            }
            payload = json.dumps([entry], indent=2, sort_keys=True)
            seg_path.write_text(payload, encoding="utf-8")
            import hashlib as _hl

            seg_path.with_suffix(".json.sha256").write_text(
                _hl.sha256(payload.encode()).hexdigest(), encoding="utf-8"
            )

        journal = AuditJournal(journal_dir=tmp)

    # Only the most recent _LOAD_SEGMENTS_LIMIT segments × 1 entry each
    assert journal.count() == _LOAD_SEGMENTS_LIMIT, (
        f"Expected {_LOAD_SEGMENTS_LIMIT} entries (hot-window load), "
        f"got {journal.count()} — old segments are leaking into memory"
    )


def test_audit_journal_flush_prunes_old_segments_on_disk():
    """After enough flushes, segments beyond _MAX_SEGMENTS_ON_DISK must be
    deleted from disk so total on-disk count stays bounded."""
    from pythia_mining.autonomous_audit_persistence import (
        AuditJournal,
        _MAX_SEGMENTS_ON_DISK,
    )

    with tempfile.TemporaryDirectory() as tmp:
        journal = AuditJournal(journal_dir=tmp)
        journal._segment_size = 1  # flush after every single entry

        # Write enough entries to create _MAX_SEGMENTS_ON_DISK + 3 segments
        for i in range(_MAX_SEGMENTS_ON_DISK + 3):
            journal.append("test_event", "advisory", action=f"a{i}", outcome="ok")

        journal.flush()

        seg_files = list(Path(tmp).glob("audit_segment_*.json"))

    assert len(seg_files) <= _MAX_SEGMENTS_ON_DISK, (
        f"Expected <= {_MAX_SEGMENTS_ON_DISK} segments on disk after rotation, "
        f"got {len(seg_files)}"
    )
    """When psutil is not importable and os.getloadavg raises, the _system_load
    sentinel value must be returned."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp, reflexive=False)
        ctrl._system_load = 37.3

        with patch.dict("sys.modules", {"psutil": None}):
            with patch("os.getloadavg", side_effect=OSError("unavailable")):
                result = ctrl.platform_interface_get_cpu_load()

    assert result == 37.3
