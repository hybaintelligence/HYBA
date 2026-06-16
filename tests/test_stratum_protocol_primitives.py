import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from pythia_mining.stratum_client import PoolManager, StratumClient
from pythia_mining.stratum_protocol import (
    DifficultyMessage,
    NotifyMessage,
    StratumProtocolError,
    build_authorize,
    build_submit,
    build_subscribe,
    parse_authorize_result,
    parse_notify_params,
    parse_set_difficulty,
    parse_subscribe_result,
)


class StratumProtocolPrimitiveTests(unittest.TestCase):
    def test_build_messages(self):
        self.assertEqual("mining.subscribe", json.loads(build_subscribe(1))["method"])
        self.assertEqual("mining.authorize", json.loads(build_authorize(2, "w", "x"))["method"])
        self.assertEqual(
            "mining.submit",
            json.loads(build_submit(3, "w", "j", "0001", "65aa00ff", "00000002"))["method"],
        )

    def test_parse_results(self):
        sub = parse_subscribe_result({"id": 1, "result": [[], "0a0b", 4], "error": None})
        self.assertEqual("0a0b", sub.extranonce1)
        self.assertEqual(4, sub.extranonce2_size)
        self.assertTrue(parse_authorize_result({"id": 2, "result": True, "error": None}))

    def test_parse_notify_and_difficulty(self):
        notify = parse_notify_params(
            ["j", "00" * 32, "01", "02", [], "20", "1d00ffff", "65aa00ff", True]
        )
        self.assertEqual("j", notify.job_id)
        self.assertTrue(notify.clean_jobs)
        self.assertEqual(2.0, parse_set_difficulty([2.0]).difficulty)

    def test_rejects_bad_inputs(self):
        with self.assertRaises(StratumProtocolError):
            build_submit(1, "w", "j", "zz", "65aa00ff", "00000002")
        with self.assertRaises(StratumProtocolError):
            parse_set_difficulty([0])
        with self.assertRaises(StratumProtocolError):
            parse_notify_params(["short"])

    def test_client_status_tracks_pool_work_item(self):
        class FakeSession:
            def __init__(self):
                self.events = [
                    ("mining.set_difficulty", DifficultyMessage(2.0)),
                    (
                        "mining.notify",
                        NotifyMessage(
                            "job-42",
                            "00" * 32,
                            "01",
                            "02",
                            [],
                            "20",
                            "1d00ffff",
                            "65aa00ff",
                            True,
                        ),
                    ),
                ]

            async def read_event(self, timeout=None, include_responses=False):
                import asyncio

                if not self.events:
                    raise asyncio.TimeoutError()
                return self.events.pop(0)

            async def close(self):
                return None

        async def run_case():
            client = StratumClient("stratum+tcp://example.com:3333", "worker", "x", "Test Pool")
            client.live_session = FakeSession()
            client.is_connected = True
            client.is_authenticated = True
            first = await client.poll_live_event(timeout=0.01)
            item = await client.poll_live_event(timeout=0.01)
            return first, item, client.get_status()

        import asyncio

        first, item, status = asyncio.run(run_case())
        self.assertIsNone(first)
        self.assertEqual("job-42", item.job_id)
        self.assertEqual("job-42", status["active_job_id"])
        self.assertEqual(1, status["performance"]["jobs_received"])
        self.assertEqual("job-42", status["current_job"]["job_id"])

    def test_pool_manager_reports_active_pool_status(self):
        async def run_case():
            manager = PoolManager(
                {
                    "alpha": {
                        "name": "Alpha",
                        "url": "stratum+tcp://example.com:3333",
                        "username": "worker",
                        "password": "x",
                    }
                }
            )
            pool = await manager.get_best_pool()
            return pool, manager.current_pool_key, manager.get_all_pools_status()

        import asyncio

        pool, key, statuses = asyncio.run(run_case())
        self.assertEqual("Alpha", pool.pool_name)
        self.assertEqual("alpha", key)
        self.assertEqual(1, len(statuses))
        self.assertTrue(statuses[0]["is_active"])
        self.assertEqual("AUTHENTICATED", statuses[0]["connection_state"])


if __name__ == "__main__":
    unittest.main()
