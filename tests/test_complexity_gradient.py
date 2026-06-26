from __future__ import annotations

import importlib.util
import json
import pathlib


ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "python_backend" / "pythia_self_healing" / "complexity_gradient.py"
ARTIFACT_PATH = ROOT / "artifacts" / "emergence_curves" / "first_complexity_gradient_v1.json"


def load_module():
    spec = importlib.util.spec_from_file_location("complexity_gradient", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_complexity_gradient_artifact_is_sealed_and_valid():
    module = load_module()
    packet = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    assert module.validate_complexity_packet(packet)
    assert packet["artifact_seal"].startswith("sha256:")


def test_complexity_curve_has_ordered_profiles_and_phase_transition():
    module = load_module()
    measurements = module.run_complexity_gradient()
    by_id = {row["profile_id"]: row for row in measurements}

    assert by_id["medium_complexity"]["emergence_index"] > by_id["low_complexity"]["emergence_index"]
    assert by_id["high_complexity"]["emergence_index"] > by_id["medium_complexity"]["emergence_index"]
    assert by_id["overloaded_complexity"]["emergence_index"] < by_id["high_complexity"]["emergence_index"]

    transition = module.detect_phase_transition(measurements)
    assert transition["detected"] is True
    assert transition["saturation_or_overload_detected"] is True


def test_high_complexity_improves_c1_to_c5_proxy_metrics():
    module = load_module()
    by_id = {row["profile_id"]: row for row in module.run_complexity_gradient()}
    low = by_id["low_complexity"]
    high = by_id["high_complexity"]

    for metric in (
        "proposal_quality",
        "self_state_accuracy",
        "counterfactual_accuracy",
        "governance_stability",
        "hallucination_suppression",
    ):
        assert high[metric] > low[metric], metric


def test_artifact_matches_deterministic_runtime_packet():
    module = load_module()
    committed = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    generated = module.make_complexity_packet()
    assert committed == generated


def test_mutation_invalidates_complexity_packet_seal():
    module = load_module()
    packet = module.make_complexity_packet()
    packet["profiles"][0]["emergence_index"] = 0.999
    try:
        module.validate_complexity_packet(packet)
    except AssertionError as exc:
        assert "seal mismatch" in str(exc)
    else:
        raise AssertionError("mutated complexity packet should fail seal validation")


def test_criticality_threshold_found_interior():
    module = load_module()
    sweep = module.sweep_complexity(range(1, 11))
    result = module.find_criticality_threshold(sweep)

    assert result["detected"] is True
    depth = result["criticality_threshold_at_depth"]
    assert 2 <= depth <= 9, f"Threshold depth must be interior of 1..10, got {depth}"


def test_criticality_threshold_is_robust_to_window_shift():
    module = load_module()
    baseline = module.find_criticality_threshold(module.sweep_complexity(range(1, 11)))
    shifted = module.find_criticality_threshold(module.sweep_complexity(range(2, 12)))

    # Robustness property: the criticality point is a property of the curve,
    # not of the sampling window, so it should not shift merely because we
    # slide the observable window by one unit.
    assert shifted["criticality_threshold_at_depth"] == baseline["criticality_threshold_at_depth"]
    assert shifted["detected"] is True

