import asyncio
import unittest

from pythia_mining.pool_profiles import build_profile
from pythia_mining.stratum_v2 import (
    LiveStratumV2Session,
    SV2_SETUP_CONNECTION_SUCCESS,
    build_setup_connection_frame,
    decode_frame,
    decode_uint24,
    encode_frame,
    encode_uint24,
    parse_setup_connection_success,
)


class FakeV2Transport:
    def __init__(self):
        self.sent = []
        self.connected = False
        self.response = encode_frame(0, SV2_SETUP_CONNECTION_SUCCESS, (2).to_bytes(2, "little") + (0).to_bytes(4, "little"))

    async def connect(self):
        self.connected = True

    async def send_frame(self, frame):
        self.sent.append(frame)

    async def read_frame(self):
        return decode_frame(self.response)

    async def close(self):
        self.connected = False


class StratumV2PrimitiveTests(unittest.TestCase):
    def test_uint24_and_frame_round_trip(self):
        self.assertEqual(0x00A1B2, decode_uint24(encode_uint24(0x00A1B2)))
        frame = decode_frame(encode_frame(0, 1, b"abc"))
        self.assertEqual(0, frame.extension_type)
        self.assertEqual(1, frame.msg_type)
        self.assertEqual(b"abc", frame.payload)

    def test_setup_connection_payload_is_binary_framed(self):
        frame = decode_frame(build_setup_connection_frame(endpoint_host="pool.example", endpoint_port=3336))
        self.assertEqual(0, frame.msg_type)
        self.assertGreater(len(frame.payload), 20)

    def test_setup_connection_success_parser(self):
        payload = (2).to_bytes(2, "little") + (7).to_bytes(4, "little")
        self.assertEqual({"used_version": 2, "flags": 7}, parse_setup_connection_success(payload))

    def test_live_v2_session_setup_success(self):
        async def run_case():
            transport = FakeV2Transport()
            session = LiveStratumV2Session(
                build_profile(
                    "v2",
                    name="V2 Pool",
                    url="stratum2+tcp://pool.example:3336",
                    username="test.worker",
                    password="test",
                    stratum_version=2,
                ),
                transport=transport,
            )
            await session.connect()
            handshake = await session.setup_connection()
            await session.close()
            return transport, handshake

        transport, handshake = asyncio.run(run_case())
        self.assertTrue(transport.sent)
        self.assertEqual(2, handshake.used_version)
        self.assertTrue(handshake.authorized)


if __name__ == "__main__":
    unittest.main()
