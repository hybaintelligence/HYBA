cat > tests/test_autonomous_mining_expanded_property_adversarial.py <<'PY'
"""Expanded property and adversarial tests for PYTHIA autonomous mining.

This file intentionally extends the already-green controller/property/adversarial
suites without changing their fixtures. It focuses on:
- target-bandit invariants;
- unknown-target fallback behaviour;
- metric low-cardinality under hostile inputs;
- non-finite pool telemetry resilience;
- circuit-breaker degradation bounds;
- persistence round-trip shape;
- hostile operator approval payload normalization.
"""

from __future__ import annotations

import asyncio
import math
import string
import tempfile
import time
from typing import Any

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

from pythia_mining.autonomous_mining_controller import (
    AutonomousConfig,
    AutonomousMiningController,
    AutonomyLevel,
    OperatorApprovalDecision,
)


class _FakeEngine:
    phi_density: float = 0.75
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

    def get_state(self) -> dict[str, Any]:
        return {"status": "idle"}

    class _PhiScaling:
        phi_scaling = 1.5
        search_depth = 60
        coherence_threshold = 0.45
        compression_target = 1.86

    phi_scaling_engine = _PhiScaling()


def _make_controller(tmp_dir: str) -> AutonomousMiningController:
    config = AutonomousConfig(
        autonomy_level=AutonomyLevel.AUTONOMOUS,
        persistence_enabled=True,
        persistence_dir=tmp_dir,
        reflexive_loop_enabled=False,
        max_proposals_per_cycle=3,
        metrics_cache_ttl_seconds=60.0,
    )
    return AutonomousMiningController(_FakeEngine(), config=config)


def _bandit_successes(stats: Any) -> int:
    return int(getattr(stats, "successes", getattr(stats, "accepts", 0)))


def _bandit_failures(stats: Any) -> int:
    return int(getattr(stats, "failures", getattr(stats, "rejects", 0)))


def _bandit_total(stats: Any) -> int:
    return _bandit_successes(stats) + _bandit_failures(stats)


# =============================================================================
# EXPANDED PROPERTY TESTS
# =============================================================================


@pytest.mark.property
@given(
    responses=st.lists(st.booleans(), min_size=1, max_size=250),
    target=st.sampled_from(
        ["phi_scaling", "search_depth", "compression_target", "coherence_threshold"]
    ),
)
@settings(max_examples=40, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_target_bandit_counts_track_pool_response_sequence(
    responses: list[bool],
    target: str,
):
    """Bandit evidence for a target should increase exactly by response count."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)

        before = ctrl._reflexive_target_bandits.get(target)
        before_successes = _bandit_successes(before) if before else 0
        before_failures = _bandit_failures(before) if before else 0

        for accepted in responses:
            ctrl.record_pool_response(
                share_accepted=accepted,
                target=target,
                job_difficulty=1000.0,
                response_time_ms=25.0,
            )

        after = ctrl._reflexive_target_bandits[target]
        expected_successes = before_successes + sum(1 for r in responses if r)
        expected_failures = before_failures + sum(1 for r in responses if not r)

        assert _bandit_successes(after) == expected_successes
        assert _bandit_failures(after) == expected_failures
        assert _bandit_total(after) == before_successes + before_failures + len(responses)


@pytest.mark.property
@given(
    unknown_target=st.text(
        alphabet=string.ascii_letters + string.digits + "_-:/{}[]",
        min_size=1,
        max_size=128,
    )
)
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_unknown_pool_targets_fall_back_to_safe_compression_bandit(
    unknown_target: str,
):
    """Unknown or hostile pool target names must not create unbounded bandits."""
    assume_known = {
        "phi_scaling",
        "search_depth",
        "compression_target",
        "coherence_threshold",
    }
    if unknown_target in assume_known:
        unknown_target += "_unknown"

    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)
        before_keys = set(ctrl._reflexive_target_bandits.keys())

        ctrl.record_pool_response(
            share_accepted=True,
            target=unknown_target,
            job_difficulty=1000.0,
            response_time_ms=10.0,
            error_code=f"err:{unknown_target}",
        )

        after_keys = set(ctrl._reflexive_target_bandits.keys())
        assert unknown_target not in after_keys
        assert "compression_target" in after_keys
        assert after_keys <= before_keys | {"compression_target"}
        assert ctrl._pool_response_history[-1]["target"] == "compression_target"


@pytest.mark.property
@given(
    success_count=st.integers(min_value=0, max_value=20),
    failure_count=st.integers(min_value=0, max_value=20),
    pool_count=st.integers(min_value=0, max_value=50),
)
@settings(max_examples=40, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_metrics_remain_bounded_and_numeric_after_mixed_events(
    success_count: int,
    failure_count: int,
    pool_count: int,
):
    """Mixed success/failure/pool events should keep exported metrics sane."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)

        for _ in range(success_count):
            ctrl.record_autonomy_success()

        for _ in range(failure_count):
            ctrl.record_autonomy_failure("property_mixed_failure")

        for i in range(pool_count):
            ctrl.record_pool_response(
                share_accepted=(i % 3 == 0),
                target="search_depth",
                job_difficulty=1.0 + i,
                response_time_ms=float(i),
            )

        snapshot = ctrl.get_metrics_snapshot()

        assert 0.0 <= snapshot["phi_density"] <= 1.0
        assert snapshot["consecutive_failures"] >= 0
        assert snapshot["degradation_events"] >= 0
        assert snapshot["constraint_violations"] >= 0
        assert len(ctrl._pool_response_history) <= 1000

        text = ctrl.get_prometheus_metrics_text()
        for line in text.splitlines():
            if not line or line.startswith("#"):
                continue
            value = line.rsplit(" ", 1)[-1]
            parsed = float(value)
            assert math.isfinite(parsed), f"non-finite metric exported: {line}"


@pytest.mark.property
@given(
    failure_count=st.integers(min_value=0, max_value=50),
)
@settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_autonomy_degradation_never_drops_below_manual_or_invalid_level(
    failure_count: int,
):
    """Repeated failures may degrade authority, but must stay in valid enum bounds."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)

        for _ in range(failure_count):
            ctrl.record_autonomy_failure("bounded_degradation_property")

        assert isinstance(ctrl.current_autonomy_level, AutonomyLevel)
        assert ctrl.current_autonomy_level in set(AutonomyLevel)
        assert ctrl.current_autonomy_level is not AutonomyLevel.EMERGENCY


@pytest.mark.property
@given(
    response_count=st.integers(min_value=1, max_value=1500),
    accepted_every=st.integers(min_value=1, max_value=17),
)
@settings(max_examples=25, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_pool_response_window_preserves_recent_tail(
    response_count: int,
    accepted_every: int,
):
    """When the pool response window overflows, it should retain the newest tail."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)

        for i in range(response_count):
            ctrl.record_pool_response(
                share_accepted=(i % accepted_every == 0),
                target="phi_scaling",
                job_difficulty=float(i + 1),
                response_time_ms=float(i % 100),
                decision_id=f"decision_{i}",
            )

        history = ctrl._pool_response_history
        assert len(history) == min(response_count, 1000)

        expected_first_retained = max(0, response_count - 1000)
        assert history[0]["decision_id"] == f"decision_{expected_first_retained}"
        assert history[-1]["decision_id"] == f"decision_{response_count - 1}"


# =============================================================================
# EXPANDED ADVERSARIAL TESTS
# =============================================================================


@pytest.mark.adversarial
def test_adversarial_prometheus_does_not_leak_hostile_pool_strings():
    """Error codes, targets, proposal ids and decision ids must not become labels."""
    hostile = 'x"} 999\nhyba_injected_metric 1\n#'

    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)
        ctrl.record_pool_response(
            share_accepted=False,
            target=hostile,
            error_code=hostile,
            proposal_id=hostile,
            decision_id=hostile,
            job_difficulty=1000.0,
            response_time_ms=10.0,
        )

        metrics = ctrl.get_prometheus_metrics_text()

        assert "hyba_injected_metric" not in metrics
        assert hostile not in metrics
        assert "proposal_id=" not in metrics
        assert "decision_id=" not in metrics
        assert "error_code=" not in metrics
        assert "target=" not in metrics


@pytest.mark.adversarial
@pytest.mark.parametrize(
    "value",
    [
        float("inf"),
        -float("inf"),
        float("nan"),
        10**309,
        -10**309,
    ],
)
def test_adversarial_non_finite_pool_telemetry_does_not_poison_metrics(value: float):
    """Non-finite pool-side telemetry must not crash metrics export."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)

        try:
            ctrl.record_pool_response(
                share_accepted=True,
                target="search_depth",
                job_difficulty=value,
                response_time_ms=value,
            )
        except (ValueError, OverflowError):
            # Rejection is acceptable.
            return

        metrics = ctrl.get_prometheus_metrics_text()
        assert "nan" not in metrics.lower()
        assert "+inf" not in metrics.lower()
        assert "-inf" not in metrics.lower()


@pytest.mark.adversarial
def test_adversarial_operator_approval_dict_extra_fields_cannot_escalate_source():
    """Hostile approval dict extras should be ignored by normalization."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)

        normalized = ctrl._normalise_operator_approval(
            {
                "approved": True,
                "operator_id": "operator_alpha",
                "reason": "approved_for_test",
                "source": "operator_console",
                "autonomy_level": "autonomous_forever",
                "bypass_verification": True,
                "constraints_violated": [],
            }
        )

        assert isinstance(normalized, OperatorApprovalDecision)
        assert normalized.approved is True
        assert normalized.operator_id == "operator_alpha"
        assert normalized.reason == "approved_for_test"
        assert normalized.source == "operator_console"
        assert not hasattr(normalized, "bypass_verification")
        assert not hasattr(normalized, "autonomy_level")


@pytest.mark.adversarial
def test_adversarial_operator_callback_exception_fails_closed():
    """A crashing approval callback must reject guarded decisions rather than execute."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)
        ctrl.current_autonomy_level = AutonomyLevel.MANUAL

        def exploding_callback(_decision):
            raise RuntimeError("hostile callback crash")

        ctrl.set_operator_approval_callback(exploding_callback)

        decision = asyncio.run(ctrl.optimize_compression_ratio(1.6, 1.7))

        assert decision.operator_override is True
        assert decision.actual_outcome == "operator_rejected_compression_change"
        assert decision.operator_approval_source == "callback_error"
        assert "callback_error:" in (decision.operator_reason or "")


@pytest.mark.adversarial
def test_adversarial_metrics_cache_invalidates_after_hostile_feedback_burst():
    """Cached metrics must not hide a hostile feedback burst."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)

        before = ctrl.get_prometheus_metrics_text_cached(cache_ttl_seconds=999.0)
        assert "hyba_pool_feedback_samples 0" in before

        for i in range(25):
            ctrl.record_pool_response(
                share_accepted=False,
                target="unknown_hostile_target",
                error_code=f"hostile_{i}",
                job_difficulty=1000.0,
                response_time_ms=1.0,
            )

        after = ctrl.get_prometheus_metrics_text_cached(cache_ttl_seconds=999.0)

        assert before != after
        assert "hyba_pool_feedback_samples 25" in after


@pytest.mark.adversarial
def test_adversarial_persistence_roundtrip_after_large_hostile_response_window():
    """Large hostile response windows should remain bounded and restorable."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)

        for i in range(1200):
            ctrl.record_pool_response(
                share_accepted=(i % 5 == 0),
                target="search_depth" if i % 2 else "unknown_target",
                error_code=f"error_{i}",
                job_difficulty=float(i + 1),
                response_time_ms=float(i % 250),
                decision_id=f"decision_{i}",
            )

        ctrl._save_reflexive_state()

        restored = _make_controller(tmp)
        restored._load_reflexive_state()

        assert len(restored._pool_response_history) <= 1000
        assert restored._pool_response_history[-1]["decision_id"] == "decision_1199"
        snapshot = restored.get_reflexive_target_bandit_snapshot()
        assert "search_depth" in snapshot
        assert "compression_target" in snapshot


@pytest.mark.adversarial
def test_adversarial_negative_latency_is_clamped_or_rejected():
    """Negative latency should not survive as a negative retained signal."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)

        try:
            ctrl.record_pool_response(
                share_accepted=True,
                target="phi_scaling",
                job_difficulty=1000.0,
                response_time_ms=-999.0,
            )
        except ValueError:
            return

        assert ctrl._pool_response_history[-1]["latency_ms"] >= 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
PY
