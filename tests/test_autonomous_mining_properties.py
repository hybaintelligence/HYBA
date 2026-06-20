"""Property-style invariants for PYTHIA autonomous mining."""

from __future__ import annotations

from pathlib import Path
import sys
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[1]
PYTHON_BACKEND = ROOT / "python_backend"
if str(PYTHON_BACKEND) not in sys.path:
    sys.path.insert(0, str(PYTHON_BACKEND))

from pythia_mining.autonomous_mining_controller import (  # noqa: E402
    AutonomousConfig,
    AutonomousMiningController,
    ReflexiveTargetBanditStats,
)


def _controller() -> AutonomousMiningController:
    engine = MagicMock()
    engine.optimizer = MagicMock()
    engine.phi_ensemble = MagicMock(config={})
    engine.solver = MagicMock()
    engine.consciousness = None
    return AutonomousMiningController(engine, AutonomousConfig(persistence_enabled=False))


def test_property_pool_history_never_exceeds_cap_for_many_lengths() -> None:
    for n in (0, 1, 999, 1000, 1001, 4096):
        ctrl = _controller()
        for i in range(n):
            ctrl.record_pool_response(accepted=bool(i % 2), target="phi_scaling")
        assert len(ctrl._pool_response_history) <= 1000


def test_property_beta_posterior_mean_is_always_probability() -> None:
    for successes in (0, 1, 2, 100, 10_000):
        for failures in (0, 1, 3, 250, 10_000):
            stats = ReflexiveTargetBanditStats(successes=successes, failures=failures)
            assert 0.0 <= stats.posterior_mean <= 1.0


def test_property_target_selection_is_deterministic_for_same_evidence() -> None:
    targets = ["phi_scaling", "search_depth", "compression_target", "coherence_threshold"]
    left = _controller()
    right = _controller()
    sequence = [True, False, True, True, False, False, True]
    for accepted in sequence:
        left.record_pool_response(accepted=accepted, target="search_depth")
        right.record_pool_response(accepted=accepted, target="search_depth")
    assert left._select_reflexive_targets(targets, "phi_scaling", 0.0) == right._select_reflexive_targets(
        targets, "phi_scaling", 0.0
    )


def test_property_phi_density_is_finite_probability() -> None:
    ctrl = _controller()
    for violated_count in range(0, 25):
        ctrl.decision_log = []
        for _ in range(violated_count):
            ctrl.record_autonomy_failure("property-test")
        density = ctrl.get_phi_density()
        assert 0.0 <= density <= 1.0


def test_property_restored_state_preserves_supported_schema_version(tmp_path: Path) -> None:
    ctrl = AutonomousMiningController(
        MagicMock(), AutonomousConfig(persistence_enabled=True, persistence_dir=str(tmp_path))
    )
    ctrl.record_pool_response(accepted=True, target="compression_target")
    ctrl._save_reflexive_state()
    restored = AutonomousMiningController(
        MagicMock(), AutonomousConfig(persistence_enabled=True, persistence_dir=str(tmp_path))
    )
    assert restored.config.state_schema_version == ctrl.config.state_schema_version
    assert len(restored._pool_response_history) == 1
