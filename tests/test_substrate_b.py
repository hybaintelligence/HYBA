"""Tests for the cross-substrate parity (Substrate B) module."""

from __future__ import annotations

import importlib.util
import pathlib


ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "python_backend" / "pythia_self_healing" / "substrate_b.py"


def load_module():
    spec = importlib.util.spec_from_file_location("substrate_b", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_hyperbolic_state_has_correct_dimensions():
    module = load_module()
    state = module.hyperbolic_test_state()
    assert len(state.amplitudes) == module.HYPERBOLIC_DIMENSIONS
    norm = sum(v * v for v in state.amplitudes)
    assert abs(norm - 1.0) < 1e-12


def test_substrate_b_surfaces_self_consistent():
    module = load_module()
    results = module.run_substrate_b_all_surfaces()
    assert set(results) == {"hyperbolic_python", "hyperbolic_cpu", "hyperbolic_shadow"}

    from python_backend.pythia_self_healing.quantum_substrate_invariance import (
        assert_invariant_equivalence,
    )

    assert assert_invariant_equivalence(results)


def test_dual_substrate_invariance_test_runs():
    module = load_module()
    result = module.run_dual_substrate_invariance_test()
    assert result["schema"] == "HYBA_DUAL_SUBSTRATE_INVARIANCE_V1"
    assert result["substrate_a_self_consistent"] is True
    assert result["substrate_b_self_consistent"] is True
    assert "cross_substrate_deltas" in result
    assert result["falsifier_result"] == "not_falsified" or "falsified" in result["falsifier_result"]