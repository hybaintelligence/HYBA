from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[1]
PYTHON_BACKEND = ROOT / "python_backend"
if str(PYTHON_BACKEND) not in sys.path:
    sys.path.insert(0, str(PYTHON_BACKEND))

from pythia_mining.autonomous_mining_controller import (  # noqa: E402
    AutonomousConfig,
    AutonomousMiningController,
    SafetyConstraint,
    SelfOptimizationProposal,
)
from pythia_mining.runtime_reflexive_introspection import (  # noqa: E402
    bind_runtime_reflexive_adapters,
    inspect_python_modules,
    simulate_virtual_mining_with_hash_landscape,
)


def _controller() -> AutonomousMiningController:
    engine = MagicMock()
    engine.optimizer = MagicMock()
    engine.phi_ensemble = MagicMock()
    engine.solver = MagicMock()
    engine.consciousness = None
    config = AutonomousConfig(
        persistence_enabled=False,
        reflexive_loop_enabled=True,
        virtual_session_horizon=0.05,
    )
    return AutonomousMiningController(engine, config=config)


def _proposal(**overrides) -> SelfOptimizationProposal:
    payload = dict(
        proposal_id="proposal-runtime-test",
        timestamp=1.0,
        improvement_type="phi_scaling",
        current_value=1.5,
        proposed_value=1.425,
        expected_phi_density_gain=0.02,
        logical_consistency_score=0.82,
        constraints_satisfied=[
            SafetyConstraint.HERMITICITY,
            SafetyConstraint.POSITIVE_SEMIDEFINITE,
            SafetyConstraint.INFORMATION_INTEGRITY,
        ],
        constraints_violated=[],
        counterfactual_confidence=0.76,
        codebase_source_module="autonomous_mining_controller",
    )
    payload.update(overrides)
    return SelfOptimizationProposal(**payload)


def test_runtime_introspection_scans_real_pythia_package_surface() -> None:
    modules = inspect_python_modules(PYTHON_BACKEND / "pythia_mining")
    names = {module.name for module in modules}

    assert len(modules) > 12
    assert "autonomous_mining_controller" in names
    assert "phi_unified_mining_engine" in names
    assert any(module.invariant_hits for module in modules)


def test_binding_refreshes_controller_surroundings_beyond_fixed_table() -> None:
    controller = _controller()
    previous_count = len(controller.surroundings.module_names)

    report = bind_runtime_reflexive_adapters(controller, PYTHON_BACKEND / "pythia_mining")

    assert report["source"] == "runtime_ast_import_graph"
    assert report["previous_module_count"] == previous_count
    assert report["module_count"] > previous_count
    assert report["edge_count"] > 0
    assert report["virtual_mining_simulation"] == "deterministic_sha256d_hash_landscape"
    assert "autonomous_mining_controller" in controller.surroundings.module_names


def test_hash_landscape_virtual_mining_is_deterministic() -> None:
    controller = _controller()
    proposal = _proposal()

    first = simulate_virtual_mining_with_hash_landscape(controller, proposal)
    second = simulate_virtual_mining_with_hash_landscape(controller, proposal)

    assert first == second
    assert 0.0 <= first <= 1.0


def test_hash_landscape_penalises_constraint_violations() -> None:
    controller = _controller()
    clean = _proposal()
    violated = _proposal(
        constraints_violated=[SafetyConstraint.INFORMATION_INTEGRITY],
        logical_consistency_score=0.20,
        counterfactual_confidence=0.20,
    )

    clean_score = simulate_virtual_mining_with_hash_landscape(controller, clean)
    violated_score = simulate_virtual_mining_with_hash_landscape(controller, violated)

    assert violated_score < clean_score


def test_bound_adapter_replaces_instance_virtual_mining() -> None:
    controller = _controller()
    bind_runtime_reflexive_adapters(controller, PYTHON_BACKEND / "pythia_mining")

    score = controller._simulate_virtual_mining(_proposal())

    assert 0.0 <= score <= 1.0
