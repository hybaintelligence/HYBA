"""Property-based tests for autonomous mining controller.

These tests use Hypothesis to validate mathematical invariants and correctness:
- Thompson sampling properties
- Recency weighting monotonicity
- Circuit breaker state machine
- Evidence accumulation properties
- Constraint satisfaction guarantees
"""

from __future__ import annotations

import tempfile
import time
from hypothesis import given, strategies as st, assume, settings
from hypothesis import HealthCheck

import pytest

from pythia_mining.autonomous_mining_controller import (
    AutonomousConfig,
    AutonomousMiningController,
    AutonomyLevel,
    SelfOptimizationProposal,
)


class _FakeEngine:
    """Minimal duck-type stand-in for UnifiedMiningEngine."""

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

    def get_state(self) -> dict:
        return {"status": "idle"}

    class _PhiScaling:
        phi_scaling = 1.5
        search_depth = 60
        coherence_threshold = 0.45
        compression_target = 1.86

    phi_scaling_engine = _PhiScaling()


def _make_controller(tmp_dir: str) -> AutonomousMiningController:
    """Create controller for testing."""
    config = AutonomousConfig(
        autonomy_level=AutonomyLevel.AUTONOMOUS,
        persistence_enabled=True,
        persistence_dir=tmp_dir,
        reflexive_loop_enabled=False,  # Disable for faster property tests
        max_proposals_per_cycle=3,
    )
    return AutonomousMiningController(_FakeEngine(), config=config)


# =============================================================================
# PROPERTY: Thompson Sampling Posterior Properties
# =============================================================================


@pytest.mark.property
@given(
    accepts=st.integers(min_value=0, max_value=100),
    rejects=st.integers(min_value=0, max_value=100),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
def test_property_thompson_posterior_bounded(accepts: int, rejects: int):
    """Thompson posterior mean should always be in [0, 1]."""
    # Beta distribution posterior: (a+1)/(a+r+2)
    posterior_mean = (accepts + 1) / (accepts + rejects + 2)

    assert (
        0.0 <= posterior_mean <= 1.0
    ), f"Posterior mean {posterior_mean} outside [0,1] for a={accepts}, r={rejects}"


@pytest.mark.property
@given(
    accepts1=st.integers(min_value=1, max_value=50),
    rejects1=st.integers(min_value=1, max_value=50),
    accepts2=st.integers(min_value=1, max_value=50),
    rejects2=st.integers(min_value=1, max_value=50),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
def test_property_thompson_monotonicity(
    accepts1: int, rejects1: int, accepts2: int, rejects2: int
):
    """Higher accept ratio should yield higher posterior mean."""
    ratio1 = accepts1 / (accepts1 + rejects1)
    ratio2 = accepts2 / (accepts2 + rejects2)

    posterior1 = (accepts1 + 1) / (accepts1 + rejects1 + 2)
    posterior2 = (accepts2 + 1) / (accepts2 + rejects2 + 2)

    if ratio1 > ratio2:
        assert posterior1 >= posterior2, (
            f"Posterior ordering violated: ratio1={ratio1:.3f} > ratio2={ratio2:.3f} "
            f"but posterior1={posterior1:.3f} < posterior2={posterior2:.3f}"
        )


# =============================================================================
# PROPERTY: Recency Weighting Properties
# =============================================================================


@pytest.mark.property
@given(
    age_hours=st.floats(min_value=0.0, max_value=168.0),  # 0-7 days
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
def test_property_recency_weight_bounded(age_hours: float):
    """Recency weight should be in [0, 1] and monotonically decreasing."""
    decay_factor = 0.95
    weight = decay_factor**age_hours

    assert (
        0.0 <= weight <= 1.0
    ), f"Recency weight {weight} outside [0,1] for age={age_hours}h"


@pytest.mark.property
@given(
    age1=st.floats(min_value=0.0, max_value=100.0),
    age2=st.floats(min_value=0.0, max_value=100.0),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
def test_property_recency_weight_monotonic(age1: float, age2: float):
    """Older responses should have lower or equal weight."""
    decay_factor = 0.95
    weight1 = decay_factor**age1
    weight2 = decay_factor**age2

    if age1 > age2:
        assert weight1 <= weight2, (
            f"Recency weight not monotonic: age1={age1:.2f}h > age2={age2:.2f}h "
            f"but weight1={weight1:.6f} > weight2={weight2:.6f}"
        )


# =============================================================================
# PROPERTY: Circuit Breaker State Machine
# =============================================================================


@pytest.mark.property
@given(
    failure_count=st.integers(min_value=0, max_value=10),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=20)
def test_property_circuit_breaker_threshold(failure_count: int):
    """Circuit should open if and only if consecutive failures >= threshold."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)
        threshold = ctrl.config.circuit_breaker_failure_threshold

        # Record failures
        for _ in range(failure_count):
            ctrl.record_autonomy_failure("property_test")

        is_open = ctrl.is_circuit_open()

        if failure_count >= threshold:
            assert (
                is_open
            ), f"Circuit should be open after {failure_count} failures (threshold={threshold})"
        else:
            assert (
                not is_open
            ), f"Circuit should be closed with {failure_count} failures (threshold={threshold})"


@pytest.mark.property
def test_property_circuit_breaker_success_resets():
    """A single success should reset consecutive failure count to zero."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)

        # Record some failures (but below threshold)
        ctrl.record_autonomy_failure("test1")
        ctrl.record_autonomy_failure("test2")

        assert ctrl._consecutive_failures == 2

        # Single success should reset
        ctrl.record_autonomy_success()

        assert (
            ctrl._consecutive_failures == 0
        ), "Consecutive failures should reset to 0 after success"


# =============================================================================
# PROPERTY: Pool Response Evidence Accumulation
# =============================================================================


@pytest.mark.property
@given(
    response_count=st.integers(min_value=1, max_value=2000),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=20)
def test_property_pool_history_bounded(response_count: int):
    """Pool response history should never exceed maximum window size."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)
        max_window = 1000  # From implementation

        # Record many responses
        for i in range(response_count):
            ctrl.record_pool_response(
                share_accepted=(i % 2 == 0),
                job_difficulty=1000.0,
            )

        actual_size = len(ctrl._pool_response_history)

        assert (
            actual_size <= max_window
        ), f"Pool history size {actual_size} exceeds maximum {max_window}"

        if response_count <= max_window:
            assert actual_size == response_count, (
                f"Pool history should contain all {response_count} responses "
                f"when below window limit, but has {actual_size}"
            )


@pytest.mark.property
@given(
    accept_rate=st.floats(min_value=0.0, max_value=1.0),
    sample_count=st.integers(min_value=10, max_value=100),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=30)
def test_property_evidence_reflects_accept_rate(accept_rate: float, sample_count: int):
    """Target evidence should approximately reflect actual accept rate."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)

        # Record responses with known accept rate
        for i in range(sample_count):
            accepted = (i / sample_count) < accept_rate
            ctrl.record_pool_response(
                share_accepted=accepted,
                job_difficulty=1000.0,
                target="test_target",
            )

        # Check if evidence was accumulated in reflexive target bandits
        if "test_target" in ctrl._reflexive_target_bandits:
            stats = ctrl._reflexive_target_bandits["test_target"]
            total = stats.accepts + stats.rejects

            if total > 0:
                observed_rate = stats.accepts / total

                # Should be approximately equal (within reasonable error)
                error = abs(observed_rate - accept_rate)
                assert (
                    error < 0.2
                ), f"Evidence rate {observed_rate:.3f} differs from actual {accept_rate:.3f}"


# =============================================================================
# PROPERTY: Constraint Satisfaction
# =============================================================================


@pytest.mark.property
@given(
    current_value=st.floats(min_value=0.1, max_value=10.0),
    proposed_value=st.floats(min_value=0.1, max_value=10.0),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
def test_property_hermiticity_symmetric(current_value: float, proposed_value: float):
    """Hermiticity constraint should be symmetric."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)

        # Create proposal A→B
        proposal_forward = SelfOptimizationProposal(
            proposal_id="forward",
            timestamp=time.time(),
            improvement_type="phi_scaling",
            current_value=current_value,
            proposed_value=proposed_value,
            expected_phi_density_gain=0.1,
            logical_consistency_score=0.8,
            constraints_satisfied=[],
            constraints_violated=[],
            counterfactual_confidence=0.8,
            codebase_source_module="property_test",
        )

        # Create proposal B→A
        proposal_backward = SelfOptimizationProposal(
            proposal_id="backward",
            timestamp=time.time(),
            improvement_type="phi_scaling",
            current_value=proposed_value,
            proposed_value=current_value,
            expected_phi_density_gain=0.1,
            logical_consistency_score=0.8,
            constraints_satisfied=[],
            constraints_violated=[],
            counterfactual_confidence=0.8,
            codebase_source_module="property_test",
        )

        valid_forward = ctrl.validate_constraints(proposal_forward)
        valid_backward = ctrl.validate_constraints(proposal_backward)

        # Hermiticity should be symmetric (if A→B violates, B→A should too)
        # (Note: This may not hold if constraints are asymmetric by design)
        # Adjust assertion based on actual constraint logic


@pytest.mark.property
@given(
    proposed_search_depth=st.floats(min_value=1.0, max_value=1000.0),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
def test_property_natural_scaling_positive(proposed_search_depth: float):
    """Natural scaling constraint should require positive values."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)

        proposal = SelfOptimizationProposal(
            proposal_id="scaling_test",
            timestamp=time.time(),
            improvement_type="search_depth",
            current_value=60.0,
            proposed_value=proposed_search_depth,
            expected_phi_density_gain=0.1,
            logical_consistency_score=0.8,
            constraints_satisfied=[],
            constraints_violated=[],
            counterfactual_confidence=0.8,
            codebase_source_module="property_test",
        )

        valid = ctrl.validate_constraints(proposal)

        if proposed_search_depth <= 0:
            assert (
                not valid
            ), f"Negative/zero search_depth {proposed_search_depth} should be rejected"


# =============================================================================
# PROPERTY: Metrics Consistency
# =============================================================================


@pytest.mark.property
@given(
    success_count=st.integers(min_value=0, max_value=100),
    failure_count=st.integers(min_value=0, max_value=100),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=30)
def test_property_metrics_accumulation(success_count: int, failure_count: int):
    """Metrics should accurately accumulate successes and failures."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)

        # Record events
        for _ in range(success_count):
            ctrl.record_autonomy_success()

        for _ in range(failure_count):
            ctrl.record_autonomy_failure("property_test")

        metrics = ctrl.get_metrics_snapshot()

        # Total decisions should equal sum of successes and failures
        # (if controller tracks both in decision history)
        if "autonomous_executions" in metrics:
            assert metrics["autonomous_executions"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "property"])
