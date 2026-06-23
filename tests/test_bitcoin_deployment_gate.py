from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "scripts" / "local_production_gate.py"
PACKAGE_JSON = ROOT / "package.json"


def _load_gate() -> ModuleType:
    spec = importlib.util.spec_from_file_location("local_production_gate", GATE)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _names(steps: list[tuple[str, list[str]]]) -> list[str]:
    return [name for name, _ in steps]


def test_bitcoin_rc_gate_excludes_research_only_blockers() -> None:
    gate = _load_gate()
    names = _names(gate._steps_for_mode("bitcoin"))

    assert "adaptive_science_bundle" not in names
    assert "elevation_packet_bundle" not in names
    assert "frontier_experiment_bundle" not in names
    assert "post_quantum_benchmark_contracts" not in names

    assert "nodus_solutus_computability_doctrine" in names
    assert "reviewer_evidence_map_and_conflict_guard" in names
    assert "runtime_mock_guard" in names
    assert "unified_mining_engine_control_loop" in names
    assert "unified_mining_api_surface" in names
    assert "stratum_share_acceptance_e2e" in names
    assert "pool_profile_readiness" in names
    assert "mining_production_doctor" in names
    assert "funding_gate_without_live_share_claim" in names
    assert "production_build" in names
    assert "deployment_property_tests" in names


def test_rc_mode_is_bitcoin_release_candidate_gate() -> None:
    gate = _load_gate()
    assert gate._steps_for_mode("rc") == gate._steps_for_mode("bitcoin")


def test_research_gate_keeps_frontier_and_adaptive_science_evidence() -> None:
    gate = _load_gate()
    names = _names(gate._steps_for_mode("research"))

    assert "adaptive_science_bundle" in names
    assert "elevation_packet_bundle" in names
    assert "frontier_experiment_bundle" in names
    assert "elevation_suite_local_mathematical_invariants" in names


def test_package_scripts_expose_bitcoin_and_research_gates() -> None:
    scripts = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))["scripts"]

    assert (
        scripts["prod:local:gate"]
        == "python scripts/local_production_gate.py --mode rc"
    )
    assert (
        scripts["prod:bitcoin:gate"]
        == "python scripts/local_production_gate.py --mode bitcoin"
    )
    assert (
        scripts["prod:research:gate"]
        == "python scripts/local_production_gate.py --mode research --continue-on-failure"
    )
    assert "review:manifest:gate" in scripts
