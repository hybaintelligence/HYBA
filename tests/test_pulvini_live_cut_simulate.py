from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipIf(importlib.util.find_spec("numpy") is None, "NumPy is required for the PULVINI live-cut drill")
class PulviniLiveCutSimulationTests(unittest.TestCase):
    def test_three_node_drill_reports_high_purity_and_valid_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / "pythia_state.live_cut.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/pulvini_simulate_live_cut.py",
                    "--nodes",
                    "0,1,2",
                    "--state",
                    str(state_path),
                    "--json",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            payload = json.loads(result.stdout)
            state = json.loads(state_path.read_text(encoding="utf-8"))

        self.assertTrue(payload["readiness"]["passed"])
        self.assertGreaterEqual(payload["manifold_purity"], 0.9)
        self.assertAlmostEqual(1.0, payload["rho_trace"], places=12)
        self.assertTrue(payload["healing_ranges_overlap_free"])
        self.assertTrue(payload["pool_identity_stable"])
        self.assertEqual([0, 1, 2], payload["severed_nodes"])
        self.assertEqual([0, 1, 2], state["latest_autonomic_event"]["failed_nodes"])


if __name__ == "__main__":
    unittest.main()
