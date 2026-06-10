import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from pythia_mining.live_stratum_session import LiveStratumSession
from pythia_mining.pool_profiles import build_profile


class FakeTransport:
    def __init__(self):
        self.sent = []
        self.responses = [
            json.dumps({"id": 1, "result": [[], "0a0b", 4], "error": None}),
            json.dumps({"id": 2, "result": True, "error": None}),
        ]
        self.closed = False

    async def connect(self):
        return None

    async def send_line(self, line):
        self.sent.append(line)

    async def read_line(self, timeout=None):
        return self.responses.pop(0)

    async def close(self):
        self.closed = True


class LiveStratumSessionTests(unittest.TestCase):
    def _profile(self):
        return build_profile(
            "alpha",
            name="Alpha",
            url="stratum+tcp://example.com:3333",
            username="worker",
            password="x",
        )

    def test_subscribe_and_authorize_uses_transport(self):
        async def run_case():
            transport = FakeTransport()
            session = LiveStratumSession(self._profile(), transport=transport)
            await session.connect()
            handshake = await session.subscribe_and_authorize()
            await session.close()
            return handshake, transport

        import asyncio
        handshake, transport = asyncio.run(run_case())
        self.assertEqual("alpha", handshake.pool_id)
        self.assertEqual("0a0b", handshake.extranonce1)
        self.assertEqual(4, handshake.extranonce2_size)
        self.assertTrue(handshake.authorized)
        self.assertTrue(transport.closed)
        self.assertIn("mining.subscribe", transport.sent[0])
        self.assertIn("mining.authorize", transport.sent[1])

    def test_read_event_parses_notify_and_difficulty(self):
        async def run_case():
            transport = FakeTransport()
            transport.responses.extend([
                json.dumps({"id": None, "method": "mining.set_difficulty", "params": [2.0]}),
                json.dumps({
                    "id": None,
                    "method": "mining.notify",
                    "params": [
                        "job-1",
                        "00" * 32,
                        "0100000001",
                        "ffffffff",
                        ["11" * 32],
                        "20000000",
                        "1d00ffff",
                        "6578ab4e",
                        True,
                    ],
                }),
            ])
            session = LiveStratumSession(self._profile(), transport=transport)
            difficulty_event = await session.read_event()
            notify_event = await session.read_event()
            return difficulty_event, notify_event

        import asyncio
        difficulty_event, notify_event = asyncio.run(run_case())
        self.assertEqual("mining.set_difficulty", difficulty_event[0])
        self.assertEqual(2.0, difficulty_event[1].difficulty)
        self.assertEqual("mining.notify", notify_event[0])
        self.assertEqual("job-1", notify_event[1].job_id)

    def test_submit_share_waits_for_matching_response(self):
        async def run_case():
            transport = FakeTransport()
            session = LiveStratumSession(self._profile(), transport=transport)
            await session.connect()
            await session.subscribe_and_authorize()
            transport.responses.extend([
                json.dumps({"id": None, "method": "mining.set_difficulty", "params": [4]}),
                json.dumps({"id": 3, "result": True, "error": None}),
            ])
            result = await session.submit_share(
                job_id="job-1",
                extranonce2="00000000",
                ntime="6578ab4e",
                nonce="00000000",
            )
            return result, transport

        import asyncio
        result, transport = asyncio.run(run_case())
        self.assertTrue(result.accepted)
        self.assertIsNone(result.error)
        self.assertIn("mining.submit", transport.sent[-1])


if __name__ == "__main__":
    unittest.main()
