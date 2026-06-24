from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / 'python_backend'
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from pythia_mining.iit_4_analyzer import IIT4Analyzer


def test_phi_bounded_for_random_connectivity_samples():
    rng = np.random.default_rng(42)
    analyzer = IIT4Analyzer(system_size=6)

    for _ in range(250):
        state = rng.random(6)
        conn = rng.random((6, 6))
        np.fill_diagonal(conn, 0.0)

        phi = analyzer.calculate_phi_max(state, conn)['phi_max']
        assert 0.0 <= phi <= 1.0


def test_phi_invariant_under_node_permutation():
    analyzer = IIT4Analyzer(system_size=4)

    state = np.array([1, 1, 0, 0], dtype=float)
    conn = np.array([
        [0, 1, 0, 0],
        [1, 0, 1, 0],
        [0, 1, 0, 1],
        [0, 0, 1, 0],
    ], dtype=float)

    base = analyzer.calculate_phi_max(state, conn)['phi_max']

    perm = [2, 0, 3, 1]
    state_p = state[perm]
    conn_p = conn[np.ix_(perm, perm)]

    permuted = analyzer.calculate_phi_max(state_p, conn_p)['phi_max']
    assert abs(base - permuted) < 1e-9


def test_cross_partition_connectivity_monotonicity():
    analyzer = IIT4Analyzer(system_size=4)
    state = np.ones(4)

    weak = np.zeros((4, 4))
    weak[0, 2] = weak[2, 0] = 0.1

    strong = np.zeros((4, 4))
    strong[0, 2] = strong[2, 0] = 1.0

    weak_phi = analyzer.calculate_phi_max(state, weak)['phi_max']
    strong_phi = analyzer.calculate_phi_max(state, strong)['phi_max']

    assert strong_phi >= weak_phi
