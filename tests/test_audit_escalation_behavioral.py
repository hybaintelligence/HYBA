"""Behavioral tests for autonomous_audit_persistence and autonomous_escalation.

Both modules were previously only ast.parse-validated (Layer 2 structural).
These tests actually exercise the code paths: append → query → chain integrity,
and escalation thresholds → callback → audit log entry.
"""

from __future__ import annotations

import tempfile
import time
from unittest.mock import MagicMock

import pytest

from pythia_mining.autonomous_audit_persistence import AuditJournal, AutonomousAuditLogger
from pythia_mining.autonomous_escalation import (
    AutonomousEscalationEngine,
    DEGRADATION_RECOVERY,
    ESCALATION_THRESHOLDS,
)


# ---------------------------------------------------------------------------
# AuditJournal — append / query / chain integrity
# ---------------------------------------------------------------------------


def test_audit_journal_append_and_query():
    """Appended entry must be queryable by event_type."""
    with tempfile.TemporaryDirectory() as tmp:
        journal = AuditJournal(journal_dir=tmp)
        journal.append("startup_self_healing", "supervised", action="boot", outcome="ok")

        results = journal.query(event_type="startup_self_healing")
        assert len(results) == 1
        assert results[0].event_type == "startup_self_healing"
        assert results[0].autonomy_level == "supervised"


def test_audit_journal_chain_integrity_clean():
    """A freshly-written journal must report chain_intact=True."""
    with tempfile.TemporaryDirectory() as tmp:
        journal = AuditJournal(journal_dir=tmp)
        journal.append("decision", "advisory", action="a", outcome="ok")
        journal.append("decision", "advisory", action="b", outcome="ok")
        journal.append("escalation", "supervised", action="c", outcome="escalated")

        report = journal.verify_chain_integrity()
        assert report["chain_intact"] is True, f"Chain issues: {report['issues']}"
        assert report["total_entries"] == 3


def test_audit_journal_count_filtered():
    with tempfile.TemporaryDirectory() as tmp:
        journal = AuditJournal(journal_dir=tmp)
        journal.append("decision", "advisory")
        journal.append("escalation", "supervised")
        journal.append("decision", "supervised")

        assert journal.count(event_type="decision") == 2
        assert journal.count(event_type="escalation") == 1
        assert journal.count() == 3


def test_autonomous_audit_logger_startup_self_healing_writes_entry():
    """log_startup_self_healing must write a 'startup_self_healing' entry with state_diff."""
    with tempfile.TemporaryDirectory() as tmp:
        journal = AuditJournal(journal_dir=tmp)
        logger = AutonomousAuditLogger(journal=journal)
        logger.log_startup_self_healing(
            "supervised",
            phi_density_before=0.50,
            phi_density_after=0.72,
            duration_ms=42.0,
            proposals_generated=3,
            proposals_applied=2,
            stale_lock_recoveries=1,
        )

        entries = journal.query(event_type="startup_self_healing")
        assert len(entries) == 1
        diff = entries[0].state_diff
        assert diff["phi_density_before"] == 0.50
        assert diff["phi_density_after"] == 0.72
        assert diff["proposals_generated"] == 3
        assert diff["stale_lock_recoveries"] == 1


# ---------------------------------------------------------------------------
# AutonomousEscalationEngine — threshold-crossing escalation
# ---------------------------------------------------------------------------


def _make_escalation_engine():
    """Build an escalation engine with spy callbacks."""
    logger_mock = MagicMock(spec=AutonomousAuditLogger)
    escalated_to: list[str] = []
    degraded_to: list[str] = []

    def _escalate(level: str) -> None:
        escalated_to.append(level)

    def _degrade(reason: str) -> str:
        degraded_to.append(reason)
        return "advisory"

    engine = AutonomousEscalationEngine(
        audit_logger=logger_mock,
        escalation_callback=_escalate,
        degradation_callback=_degrade,
    )
    return engine, escalated_to, degraded_to, logger_mock


def test_escalation_advisory_to_supervised_fires_when_thresholds_met():
    """Engine must escalate ADVISORY→SUPERVISED when phi and acceptance cross thresholds."""
    engine, escalated_to, _, audit_mock = _make_escalation_engine()
    # Force last escalation time to be old enough
    engine._last_escalation_at = 0.0

    thresholds = ESCALATION_THRESHOLDS["advisory_to_supervised"]
    result = engine.evaluate_and_escalate(
        "advisory",
        phi_density=thresholds["min_phi_density"] + 0.01,
        proposal_acceptance_rate=thresholds["min_proposal_acceptance"] + 0.01,
        consecutive_failures=0,
    )

    assert result["action"] == "escalation"
    assert result["to_level"] == "supervised"
    assert "supervised" in escalated_to
    audit_mock.log_autonomy_escalation.assert_called_once()


def test_escalation_does_not_fire_below_phi_threshold():
    """Engine must NOT escalate when phi_density is below the threshold."""
    engine, escalated_to, _, _ = _make_escalation_engine()
    engine._last_escalation_at = 0.0

    thresholds = ESCALATION_THRESHOLDS["advisory_to_supervised"]
    result = engine.evaluate_and_escalate(
        "advisory",
        phi_density=thresholds["min_phi_density"] - 0.01,
        proposal_acceptance_rate=thresholds["min_proposal_acceptance"] + 0.10,
        consecutive_failures=0,
    )

    assert result["action"] == "none"
    assert escalated_to == []


def test_escalation_respects_cooldown():
    """Engine must not escalate again within _MIN_ESCALATION_INTERVAL_SECONDS."""
    engine, escalated_to, _, _ = _make_escalation_engine()
    engine._last_escalation_at = time.time()  # just happened

    thresholds = ESCALATION_THRESHOLDS["advisory_to_supervised"]
    result = engine.evaluate_and_escalate(
        "advisory",
        phi_density=thresholds["min_phi_density"] + 0.05,
        proposal_acceptance_rate=thresholds["min_proposal_acceptance"] + 0.05,
        consecutive_failures=0,
    )

    assert result["action"] == "none"
    assert escalated_to == []


def test_degradation_fires_on_consecutive_failures():
    """Engine must call degrade callback when consecutive_failures > 0 and cooldown elapsed."""
    engine, _, degraded_to, audit_mock = _make_escalation_engine()
    engine._last_degradation_at = 0.0  # cooldown not active

    result = engine.evaluate_and_escalate(
        "supervised",
        phi_density=0.30,
        proposal_acceptance_rate=0.20,
        consecutive_failures=2,
    )

    assert result["action"] == "degradation"
    assert len(degraded_to) == 1
    audit_mock.log_autonomy_degradation.assert_called_once()


def test_recovery_escalates_after_enough_successes():
    """After degradation+recovery cycles, engine escalates back when phi and successes are met."""
    engine, escalated_to, _, _ = _make_escalation_engine()
    engine._last_escalation_at = 0.0
    min_successes = int(DEGRADATION_RECOVERY["min_consecutive_successes"])
    min_phi = DEGRADATION_RECOVERY["min_phi_density"]

    # Simulate consecutive successes by calling evaluate with 0 failures repeatedly
    for _ in range(min_successes):
        engine.evaluate_and_escalate(
            "advisory",
            phi_density=min_phi - 0.01,  # below threshold — no escalation yet
            proposal_acceptance_rate=0.30,
            consecutive_failures=0,
        )

    # Now phi crosses the recovery threshold
    result = engine.evaluate_and_escalate(
        "advisory",
        phi_density=min_phi + 0.01,
        proposal_acceptance_rate=0.50,
        consecutive_failures=0,
    )

    # Either a recovery or escalation action must have fired
    assert result["action"] in ("recovery", "escalation"), (
        f"Expected recovery or escalation after {min_successes} successes, got {result['action']}"
    )
    assert len(escalated_to) >= 1
