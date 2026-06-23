from __future__ import annotations

import json
import subprocess
import sys

from pythia_mining.after_quantum_trifecta import (
    CLAIM_BOUNDARY,
    benchmark_ai_reasoning_integrity,
    benchmark_ai_weight_geometry,
    benchmark_biotech_interaction,
    benchmark_cyber_topological_defense,
    benchmark_finance_tail_risk,
    benchmark_fluid_resonance,
    benchmark_logistics_manifold,
    run_global_formalism_efficiency_index,
)


def _assert_report(report) -> None:
    assert report.duration_ms >= 0.0
    assert 0.0 <= report.primary_score <= 1.0
    assert report.compression_ratio >= 1.0
    assert 0.0 <= report.phi_alignment <= 1.0
    assert 0.0 <= report.mass_gap_alignment <= 1.0
    assert report.claim_boundary == CLAIM_BOUNDARY


def test_after_quantum_trifecta_reports_are_bounded() -> None:
    reports = [
        benchmark_logistics_manifold(nodes=50),
        benchmark_ai_weight_geometry(dimension=256),
        benchmark_biotech_interaction(points=128),
        benchmark_finance_tail_risk(assets=128),
        benchmark_fluid_resonance(grid_side=64),
        benchmark_ai_reasoning_integrity(steps=8, hidden_dim=256),
        benchmark_cyber_topological_defense(nodes=256),
    ]

    for report in reports:
        _assert_report(report)


def test_global_formalism_efficiency_index_covers_all_domains() -> None:
    reports = run_global_formalism_efficiency_index()
    domains = {report.domain for report in reports}

    assert len(reports) == 7
    assert "logistics_geodesic_tsp" in domains
    assert "ai_weight_geometry" in domains
    assert "biotech_docking_manifold" in domains
    assert "finance_tail_risk" in domains
    assert "fluid_dynamics_resonance" in domains
    assert "ai_reasoning_integrity" in domains
    assert "cyber_topological_defense" in domains


def test_global_formalism_efficiency_index_script_outputs_json() -> None:
    completed = subprocess.run(
        [sys.executable, "benchmarks/global_formalism_efficiency_index.py"],
        check=True,
        text=True,
        capture_output=True,
    )
    payload = json.loads(completed.stdout)

    assert payload["index"] == "Global Formalism Efficiency Index"
    assert len(payload["reports"]) == 7
    assert all(
        "Formalism-derived classical" in row["claim_boundary"]
        for row in payload["reports"]
    )
