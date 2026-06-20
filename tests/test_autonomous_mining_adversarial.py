"""Adversarial coverage for PYTHIA autonomous mining control paths."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
import sys
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[1]
PYTHON_BACKEND = ROOT / "python_backend"
if str(PYTHON_BACKEND) not in sys.path:
    sys.path.insert(0, str(PYTHON_BACKEND))

from pythia_mining.autonomous_mining_controller import (  # noqa: E402
    AutonomousConfig,
    AutonomousDecision,
    AutonomousMiningController,
    AutonomyLevel,
)


def _controller(**kwargs) -> AutonomousMiningController:
    engine = MagicMock()
    engine.optimizer = MagicMock()
    engine.phi_ensemble = MagicMock(config={})
    engine.solver = MagicMock()
    engine.consciousness = None
    config = AutonomousConfig(persistence_enabled=False, **kwargs)
    return AutonomousMiningController(engine, config)


def test_contradictory_pool_responses_do_not_escape_bounded_evidence() -> None:
    ctrl = _controller()
    for accepted in (True, False, True, False):
        ctrl.record_pool_response(
            accepted=accepted,
            target="coherence_threshold",
            proposal_id="same-proposal",
            decision_id="same-decision",
            error_code=None if accepted else "duplicate-share",
        )
    samples = [r for r in ctrl._pool_response_history if r["decision_id"] == "same-decision"]
    assert [s["accepted"] for s in samples] == [True, False, True, False]
    posterior = ctrl.get_reflexive_target_bandit_snapshot()["coherence_threshold"]["posterior_mean"]
    assert 0.0 <= posterior <= 1.0


def test_malformed_operator_callback_fails_closed() -> None:
    ctrl = _controller(operator_approval_timeout_seconds=0.01)
    ctrl.set_operator_approval_callback(MagicMock(side_effect=ValueError("not-json")))
    decision = AutonomousDecision(
        decision_id="bad-approval",
        timestamp=time.time(),
        autonomy_level=AutonomyLevel.SUPERVISED,
        decision_type="wallet_address_change",
        mathematical_justification={},
        constraints_satisfied=[],
        constraints_violated=[],
        action_taken="change_wallet",
        expected_outcome="operator gate",
    )
    assert ctrl._request_operator_approval(decision) is False
    assert decision.operator_reason == "callback_error:not-json"


def test_corrupt_reflexive_state_is_rejected_without_crashing_boot(tmp_path: Path) -> None:
    state = tmp_path / "reflexive_state.json"
    state.write_text("{bad json", encoding="utf-8")
    ctrl = AutonomousMiningController(
        MagicMock(),
        AutonomousConfig(persistence_enabled=True, persistence_dir=str(tmp_path)),
    )
    assert ctrl._self_optimization_epochs == 0
    assert any(event.event_type == "load_state_error" for event in ctrl.audit_log)


def test_checksum_mismatch_on_rollback_is_rejected(tmp_path: Path) -> None:
    ctrl = AutonomousMiningController(
        MagicMock(),
        AutonomousConfig(persistence_enabled=True, persistence_dir=str(tmp_path)),
    )
    state = tmp_path / "candidate.json"
    state.write_text(json.dumps({"schema_version": ctrl.config.state_schema_version}), encoding="utf-8")
    state.with_suffix(".json.sha256").write_text(hashlib.sha256(b"different").hexdigest())
    try:
        ctrl.rollback_to_state(state, operator_reason="adversarial checksum test")
    except ValueError as exc:
        assert "checksum mismatch" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("rollback accepted a corrupt checksum")


def test_circuit_reset_while_pending_approval_leaves_request_auditable() -> None:
    ctrl = _controller()
    decision = AutonomousDecision(
        decision_id="pending-reset",
        timestamp=time.time(),
        autonomy_level=AutonomyLevel.SUPERVISED,
        decision_type="wallet_address_change",
        mathematical_justification={},
        constraints_satisfied=[],
        constraints_violated=[],
        action_taken="change_wallet",
        expected_outcome="operator gate",
    )
    assert ctrl._request_operator_approval(decision) is False
    ctrl.reset_circuit_breaker("operator reviewed pending approval")
    assert ctrl.operator_approval_requests[-1].status == "rejected"
    assert ctrl.operator_approval_requests[-1].reason == "approval_callback_missing"
