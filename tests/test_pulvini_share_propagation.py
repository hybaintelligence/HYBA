from __future__ import annotations

import asyncio
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from pythia_mining.pulvini_propagation import (  # noqa: E402
    PROXY_GATEWAY,
    CancelFlood,
    SharePropagationController,
    ShareSignal,
    ShareRouter,
)
from pythia_mining.stratum_client import ShareResult  # noqa: E402


class PulviniSharePropagationTests(unittest.TestCase):
    def test_share_signal_routes_unicast_to_h31_gateway(self) -> None:
        signal = ShareSignal.create(job_id="job-1", finder_id=2, nonce=101, extranonce2="00000002")
        route = ShareRouter().route_to_proxy(signal)

        self.assertEqual(2, route[0])
        self.assertEqual(PROXY_GATEWAY, route[-1])
        self.assertEqual(route, signal.hop_trace)
        self.assertEqual(len(route), len(set(route)))
        self.assertLessEqual(len(route) - 1, 4)

    def test_cancel_flood_reaches_all_nodes_within_three_hops(self) -> None:
        from pythia_mining.pulvini_propagation import CancelSignal

        signal = CancelSignal(job_id="job-1", reason="share_accepted", source_share_id="share-1")
        visited, max_hop = CancelFlood().flood(signal)

        self.assertEqual(32, len(visited))
        self.assertEqual(32, len(set(visited)))
        self.assertEqual(PROXY_GATEWAY, visited[0])
        self.assertLessEqual(max_hop, 3)
        self.assertEqual(visited, signal.visited)
        self.assertEqual(max_hop, signal.max_hop)

    def test_found_share_submits_once_then_cancels_job_for_all_nodes(self) -> None:
        async def run_case():
            controller = SharePropagationController()
            submitted = []
            job = SimpleNamespace(job_id="job-2")

            async def submitter(submit_job, nonce, extranonce2):
                submitted.append((submit_job.job_id, nonce, extranonce2))
                return ShareResult(True, job_id=submit_job.job_id, nonce=nonce, block_hash="00" * 32)

            result = await controller.handle_share_found(
                job=job,
                finder_id=17,
                nonce=123,
                extranonce2="00000011",
                submitter=submitter,
            )
            return controller, result, submitted

        controller, result, submitted = asyncio.run(run_case())

        self.assertEqual(1, len(submitted))
        self.assertEqual(("job-2", 123, "00000011"), submitted[0])
        self.assertEqual(17, result.route[0])
        self.assertEqual(PROXY_GATEWAY, result.route[-1])
        self.assertTrue(result.share_result.accepted)
        self.assertEqual("share_accepted", result.cancel_signal.reason)
        self.assertEqual(32, len(result.cancelled_nodes))
        self.assertTrue(controller.is_job_cancelled("job-2"))
        self.assertEqual(1, controller.snapshot()["seen_shares"])
        self.assertEqual(1, len(controller.snapshot()["history"]))

    def test_rejected_share_still_records_cancelled_job_to_stop_stale_work(self) -> None:
        async def run_case():
            controller = SharePropagationController()
            job = SimpleNamespace(job_id="job-3")

            async def submitter(submit_job, nonce, extranonce2):
                return ShareResult(False, error_code=2, error_message="low difficulty", job_id=submit_job.job_id, nonce=nonce)

            return await controller.handle_share_found(
                job=job,
                finder_id=0,
                nonce=77,
                extranonce2="00000000",
                submitter=submitter,
            )

        result = asyncio.run(run_case())

        self.assertFalse(result.share_result.accepted)
        self.assertEqual("share_rejected", result.cancel_signal.reason)
        self.assertEqual(32, len(result.cancelled_nodes))
        self.assertEqual(PROXY_GATEWAY, result.route[-1])


if __name__ == "__main__":
    unittest.main()
