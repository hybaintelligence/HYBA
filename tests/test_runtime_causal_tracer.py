"""Tests for the runtime causal tracer module."""

from __future__ import annotations

import importlib.util
import pathlib


ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "python_backend" / "pythia_self_healing" / "runtime_causal_tracer.py"


def load_module():
    spec = importlib.util.spec_from_file_location("runtime_causal_tracer", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_trace_perturbation_propagation_returns_expected_structure():
    module = load_module()
    result = module.trace_perturbation_propagation(epsilon=0.01)
    assert result["schema"] == "HYBA_RUNTIME_CAUSAL_TRACE_V1"
    assert "pure_python" in result["surface_invariant_deltas"]
    assert "complexity_gradient_deltas" in result
    assert "causally_transparent" in result


def test_trace_complexity_shift_returns_expected_structure():
    module = load_module()
    result = module.trace_complexity_shift(depth_shift=1)
    assert result["schema"] == "HYBA_COMPLEXITY_TRACE_V1"
    assert result["baseline_threshold"] is not None
    assert result["shifted_threshold"] is not None


def test_perturbed_operator_equals_original_at_zero_epsilon():
    module = load_module()
    from python_backend.pythia_self_healing.quantum_substrate_invariance import (
        phi_resonance_operator,
    )

    for index in range(5):
        for value in (0.5, 1.0, -0.25, 0.0):
            original = phi_resonance_operator(value, index)
            perturbed = module.perturbed_phi_resonance(value, index, epsilon=0.0)
            assert abs(original - perturbed) < 1e-15, f"Failed at value={value} index={index}"