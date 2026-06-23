from __future__ import annotations

import json
import subprocess
import sys

import pytest

try:
    import numpy as np
except ModuleNotFoundError:  # pragma: no cover
    np = None

pytestmark_numpy = pytest.mark.skipif(np is None, reason="numpy is not installed")


@pytestmark_numpy
def test_dodecahedral_density_trace_and_mass_gap_anchor() -> None:
    from pythia_mining.dodecahedral_solver import DodecahedralQuantumSolver

    solver = DodecahedralQuantumSolver()
    metrics = solver.get_metrics()

    assert metrics["density_trace"] == 1.0
    assert metrics["unitary_closure"] is True
    assert metrics["truncation_rule"] == "irrational_gauge_svd_boundary"
    assert metrics["mass_gap_alignment"] == pytest.approx(3.0 - (1.0 + 5.0**0.5) / 2.0)
    assert metrics["mass_gap_alignment_error"] == pytest.approx(0.0)


@pytestmark_numpy
def test_irrational_truncation_boundary_selects_golden_mean_gap() -> None:
    from pythia_mining.dodecahedral_solver import (
        DodecahedralQuantumSolver,
        MASS_GAP_TARGET,
    )

    spectrum = np.array([MASS_GAP_TARGET ** (-idx) for idx in range(1, 7)])
    result = DodecahedralQuantumSolver.irrational_truncation_boundary(spectrum)

    assert result["selected_ratio"] == pytest.approx(MASS_GAP_TARGET)
    assert result["alignment_error"] == pytest.approx(0.0)
    assert result["boundary_index"] >= 1


def test_geometric_phase_formalism_reports_nonzero_holonomy() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/geometric_phase_formalism.py"],
        check=True,
        text=True,
        capture_output=True,
    )
    report = json.loads(completed.stdout)

    assert report["formalism"] == "Topological Information Grammar"
    assert report["observable"] == "manifold_holonomy_geometric_phase"
    assert report["non_zero_holonomy"] is True
    assert "no physical quantum hardware claim" in report["claim_boundary"]
