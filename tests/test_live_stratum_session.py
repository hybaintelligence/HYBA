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
    def test_subscribe_and_authorize_uses_transport(self):
        async def run_case():
            profile = build_profile(
                "alpha",
                name="Alpha",
                url="stratum+tcp://example.com:3333",
                username="worker",
                password="x",
            )
            transport = FakeTransport()
            session = LiveStratumSession(profile, transport=transport)
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


if __name__ == "__main__":
    unittest.main()
