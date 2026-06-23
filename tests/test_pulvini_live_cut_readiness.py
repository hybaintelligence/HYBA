from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.pulvini_live_cut_readiness import evaluate_live_cut_state  # noqa: E402


def base_state() -> dict:
    return {
        "pool_visible_workers": 1,
        "current_job_id": "job-live-cut",
        "pulvini_autonomics": {
            "status": "ok",
            "rho": {"trace": 1.0, "purity": 0.98},
            "sacrificed_nodes": [31],
            "rebalances": [{"failed_nodes": [31]}],
        },
        "pulvini_overlay": {
            "pool_visible_workers": 1,
            "active_job_id": "job-live-cut",
            "healing_ranges_overlap_free": True,
            "healing_routes": [
                {"failed_node": 31, "recipient_node": 26, "nonce_range": [1, 2]}
            ],
        },
    }


class PulviniLiveCutReadinessTests(unittest.TestCase):
    def test_preflight_report_passes_when_invariants_hold(self) -> None:
        report = evaluate_live_cut_state(base_state(), mode="preflight")
        self.assertTrue(report.passed)
        self.assertEqual("ready", report.status)
        self.assertEqual(0.98, report.manifold_purity)

    def test_postcut_requires_healing_evidence(self) -> None:
        state = base_state()
        state["pulvini_autonomics"]["sacrificed_nodes"] = []
        state["pulvini_autonomics"]["rebalances"] = []
        state["pulvini_overlay"]["healing_routes"] = []
        report = evaluate_live_cut_state(state, mode="postcut")
        self.assertFalse(report.passed)
        self.assertIn(
            "postcut_healing_observed",
            [check.code for check in report.checks if not check.passed],
        )

    def test_trace_drift_blocks_live_cut(self) -> None:
        state = base_state()
        state["pulvini_autonomics"]["rho"]["trace"] = 0.99
        report = evaluate_live_cut_state(state, mode="preflight", tolerance=1e-9)
        self.assertFalse(report.passed)
        self.assertIn(
            "rho_trace_unit",
            [check.code for check in report.checks if not check.passed],
        )

    def test_expected_severed_nodes_must_be_observed(self) -> None:
        report = evaluate_live_cut_state(
            base_state(), mode="postcut", expected_severed_nodes=[0, 1, 2]
        )
        self.assertFalse(report.passed)
        self.assertIn(
            "expected_severed_nodes_observed",
            [check.code for check in report.checks if not check.passed],
        )

    def test_low_purity_blocks_live_cut(self) -> None:
        state = base_state()
        state["pulvini_autonomics"]["rho"]["purity"] = 0.2
        report = evaluate_live_cut_state(state, mode="preflight", min_purity=0.9)
        self.assertFalse(report.passed)
        self.assertIn(
            "rho_purity_minimum",
            [check.code for check in report.checks if not check.passed],
        )

    def test_cli_emits_json_and_exit_zero_for_valid_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "pythia_state.json"
            path.write_text(json.dumps(base_state()), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/pulvini_live_cut_readiness.py",
                    "--state",
                    str(path),
                    "--json",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["passed"])
        self.assertEqual("ready", payload["status"])
        self.assertEqual(0.98, payload["manifold_purity"])


if __name__ == "__main__":
    unittest.main()
