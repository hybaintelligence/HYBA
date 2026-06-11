from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from pythia_mining.pulvini_overlay import (  # noqa: E402
    NUM_NODES,
    SLICE_SIZE,
    PulviniOverlayConcentrator,
    graph_diameter,
    nonce_range_inclusive,
    verify_symmetry,
)
from pythia_mining.stratum_client import MiningJob, ShareResult  # noqa: E402


class PulviniOverlayTopologyTests(unittest.TestCase):
    def test_topology_is_symmetric_diameter_four_and_nonce_space_is_exact(self) -> None:
        self.assertTrue(verify_symmetry())
        self.assertLessEqual(graph_diameter(), 4)
        ranges = [nonce_range_inclusive(node_id) for node_id in range(NUM_NODES)]

        self.assertEqual((0, SLICE_SIZE - 1), ranges[0])
        self.assertEqual((2**32 - SLICE_SIZE, 2**32 - 1), ranges[-1])
        for index in range(1, len(ranges)):
            self.assertEqual(ranges[index - 1][1] + 1, ranges[index][0])
        self.assertEqual(2**32, sum(end - start + 1 for start, end in ranges))

    def test_pool_sees_one_worker_while_overlay_assigns_thirty_two_nodes(self) -> None:
        overlay = PulviniOverlayConcentrator(worker_name="PULVINI.singularity")
        job = MiningJob(
            job_id="job-1",
            prevhash="00" * 32,
            coinbase_parts=("01", "ff"),
            merkle_branch=[],
            version="20000000",
            nbits="1d00ffff",
            ntime="5e9a5c00",
            target=123456789,
            extranonce1="abcd",
            extranonce2_size=4,
        )

        assignments = overlay.register_pool_job(job, pool_name="Pool")
        snapshot = overlay.snapshot()

        self.assertEqual(1, snapshot["pool_visible_workers"])
        self.assertEqual(32, snapshot["internal_nodes"])
        self.assertEqual("job-1", snapshot["active_job_id"])
        self.assertEqual(NUM_NODES, len(assignments))
        self.assertEqual(NUM_NODES, len({assignment.extranonce2 for assignment in assignments.values()}))
        self.assertEqual(NUM_NODES, len(overlay.nonce_ranges()))
        phases = [event["phase"] for event in snapshot["lifecycle"]]
        self.assertIn("job_received", phases)
        self.assertIn("work_configured", phases)

    def test_every_node_can_observe_neighbor_state_and_route_share_upward(self) -> None:
        overlay = PulviniOverlayConcentrator()
        job = MiningJob(
            job_id="job-2",
            prevhash="00" * 32,
            coinbase_parts=("01", "ff"),
            merkle_branch=[],
            version="20000000",
            nbits="1d00ffff",
            ntime="5e9a5c00",
            target=987654321,
            extranonce1="abcd",
            extranonce2_size=4,
        )
        overlay.register_pool_job(job, pool_name="Pool")
        overlay.record_node_progress(0, nonce_range_inclusive(0)[0] + 10, hashes=100)
        overlay.record_link_latency(0, 20, 0.0001)
        overlay.record_share_candidate(0, nonce_range_inclusive(0)[0] + 11)
        outcome = overlay.record_share_outcome(
            0,
            nonce_range_inclusive(0)[0] + 11,
            ShareResult(True, job_id="job-2", nonce=nonce_range_inclusive(0)[0] + 11, block_hash="00" * 32),
        )
        knowledge = overlay.node_knows(0)

        self.assertEqual("job-2", knowledge["active_job_id"])
        self.assertEqual(6, len(knowledge["neighbors"]))
        self.assertEqual(20, knowledge["best_neighbor"])
        self.assertEqual([0, 20], outcome["route"])
        self.assertTrue(outcome["accepted"])
        phases = [event["phase"] for event in overlay.snapshot()["lifecycle"]]
        self.assertIn("candidate_evaluated", phases)
        self.assertIn("share_submitted", phases)
        self.assertIn("share_outcome_recorded", phases)

    def test_nonce_assignment_selects_correct_node_for_solver_result(self) -> None:
        overlay = PulviniOverlayConcentrator()
        job = SimpleNamespace(job_id="job-3", target=1, extranonce2_size=4)
        overlay.register_pool_job(job, pool_name="Pool")
        node_7_start, node_7_end = nonce_range_inclusive(7)
        assignment = overlay.assignment_for_nonce(node_7_start + 123)

        self.assertIsNotNone(assignment)
        assert assignment is not None
        self.assertEqual(7, assignment.node_id)
        self.assertLessEqual(assignment.nonce_start, node_7_start + 123)
        self.assertGreaterEqual(assignment.nonce_end, node_7_start + 123)


if __name__ == "__main__":
    unittest.main()
