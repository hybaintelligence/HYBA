from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from pythia_mining.pulvini_certificates import (
    adjacency_map_digest,
    automorphism_runtime_certificate,
)
from pythia_mining.pulvini_group import (
    AutomophismBudgetExceeded,
    compute_graph_automorphisms,
)
from pythia_mining.pulvini_topology import ADJACENCY_MAP


class PulviniCertificateTests(unittest.TestCase):
    def test_automorphism_certificate_is_exact_and_digest_keyed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(
                "os.environ", {"PULVINI_CERTIFICATE_CACHE_DIR": tmpdir}, clear=False
            ):
                first = automorphism_runtime_certificate(ADJACENCY_MAP)
                second = automorphism_runtime_certificate(ADJACENCY_MAP)
        self.assertEqual(120, first["group_order"])
        self.assertTrue(first["adjacency_preserved"])
        self.assertTrue(first["gate_closed"])
        self.assertEqual(
            adjacency_map_digest(ADJACENCY_MAP), first["adjacency_map_sha256"]
        )
        self.assertEqual("miss", first["cache_status"])
        self.assertEqual("hit", second["cache_status"])
        self.assertEqual(first["group_order"], second["group_order"])

    def test_adjacency_digest_is_canonical_over_key_order(self):
        reordered = {
            node: {
                "i": list(reversed(payload.get("i", []))),
                "d": list(reversed(payload.get("d", []))),
            }
            for node, payload in reversed(ADJACENCY_MAP.items())
        }
        self.assertEqual(
            adjacency_map_digest(ADJACENCY_MAP), adjacency_map_digest(reordered)
        )

    def test_nominal_topology_completes_within_default_budget(self):
        """32-node icosahedral topology must finish within the 500_000 node-visit budget."""
        result = compute_graph_automorphisms(ADJACENCY_MAP)
        self.assertEqual(120, len(result))

    def test_budget_exceeded_on_high_symmetry_graph(self):
        """A complete graph K6 has 720 automorphisms; a tiny budget must raise."""
        n = 6
        # Build complete graph K_n (all nodes connected to all others)
        k6 = {i: {"d": [j for j in range(n) if j != i], "i": []} for i in range(n)}
        with self.assertRaises(AutomophismBudgetExceeded):
            compute_graph_automorphisms(k6, node_budget=10)

    def test_path_graph_terminates_with_trivial_automorphism_group(self):
        """A path graph P_n with labelled endpoints has only the flip automorphism."""
        n = 8
        path = {}
        for i in range(n):
            neighbours = []
            if i > 0:
                neighbours.append(i - 1)
            if i < n - 1:
                neighbours.append(i + 1)
            path[i] = {"d": neighbours, "i": []}
        result = compute_graph_automorphisms(path)
        # Path graph has exactly 2 automorphisms: identity and end-to-end flip
        self.assertEqual(2, len(result))


if __name__ == "__main__":
    unittest.main()
