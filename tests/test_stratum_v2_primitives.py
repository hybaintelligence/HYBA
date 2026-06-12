from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from pythia_mining.live_stratum_v2_session import LiveStratumV2Session
from pythia_mining.pool_profiles import build_profile, validate_pool_url
from pythia_mining.stratum_transport import parse_endpoint
from pythia_mining.stratum_v2 import (
    SV2_EXTENSION_TYPE_CORE,
    SV2_MSG_SETUP_CONNECTION,
    SV2_MSG_SETUP_CONNECTION_SUCCESS,
    SV2_VERSION,
    SetupConnection,
    StratumV2Frame,
    StratumV2ProtocolError,
    build_setup_connection_frame,
    decode_frame,
    decode_setup_connection_payload,
    decode_u24_le,
    encode_frame,
    encode_str0_255,
    encode_u24_le,
    parse_setup_connection_response,
    setup_connection_from_url,
    split_complete_frame,
)


class FakeV2Transport:
    def __init__(self):
        self.sent = []
        self.closed = False

    async def connect(self):
        return None

    async def send_frame(self, frame):
        self.sent.append(frame)

    async def read_frame(self, timeout=None):
        payload = SV2_VERSION.to_bytes(2, "little") + (0).to_bytes(4, "little")
        return StratumV2Frame(SV2_EXTENSION_TYPE_CORE, SV2_MSG_SETUP_CONNECTION_SUCCESS, payload)

    async def close(self):
        self.closed = True


class StratumV2PrimitiveTests(unittest.TestCase):
    def test_frame_round_trip_uses_uint24_length(self):
        frame = StratumV2Frame(extension_type=0x8000, message_type=0x12, payload=b"abc")
        encoded = encode_frame(frame)
        self.assertEqual(b"\x03\x00\x00", encoded[3:6])
        self.assertEqual(frame, decode_frame(encoded))
        self.assertEqual(3, decode_u24_le(encode_u24_le(3)))

    def test_split_complete_frame_preserves_trailing_bytes(self):
        encoded = encode_frame(StratumV2Frame(extension_type=1, message_type=2, payload=b"payload"))
        frame, rest = split_complete_frame(encoded + b"next")
        self.assertIsNotNone(frame)
        assert frame is not None
        self.assertEqual(b"payload", frame.payload)
        self.assertEqual(b"next", rest)

    def test_setup_connection_payload_round_trips_spec_fields(self):
        setup = SetupConnection(endpoint_host="sv2.example.com", endpoint_port=3336, vendor="HYBA", hardware_version="PULVINI-32", firmware="test-fw", device_id="")
        frame = build_setup_connection_frame(setup)
        self.assertEqual(SV2_EXTENSION_TYPE_CORE, frame.extension_type)
        self.assertEqual(SV2_MSG_SETUP_CONNECTION, frame.message_type)
        self.assertEqual(setup, decode_setup_connection_payload(frame.payload))
        self.assertEqual(b"\x04HYBA", encode_str0_255("HYBA"))

    def test_setup_connection_success_is_validated_against_requested_version(self):
        requested = setup_connection_from_url("stratum2+tls://sv2.example.com:3336")
        success_frame = StratumV2Frame(
            SV2_EXTENSION_TYPE_CORE,
            SV2_MSG_SETUP_CONNECTION_SUCCESS,
            SV2_VERSION.to_bytes(2, "little") + (0).to_bytes(4, "little"),
        )
        success = parse_setup_connection_response(success_frame, requested=requested)
        self.assertEqual(SV2_VERSION, success.used_version)
        bad_version = StratumV2Frame(SV2_EXTENSION_TYPE_CORE, SV2_MSG_SETUP_CONNECTION_SUCCESS, (3).to_bytes(2, "little") + (0).to_bytes(4, "little"))
        with self.assertRaises(StratumV2ProtocolError):
            parse_setup_connection_response(bad_version, requested=requested)

    def test_rejects_malformed_frames(self):
        with self.assertRaises(StratumV2ProtocolError):
            decode_frame(b"\x00")
        with self.assertRaises(StratumV2ProtocolError):
            decode_frame(b"\x00\x00\x01\x02\x00\x00x")
        with self.assertRaises(StratumV2ProtocolError):
            encode_frame(StratumV2Frame(extension_type=1 << 16, message_type=1, payload=b""))

    def test_pool_profile_accepts_stratum_v2_tls_endpoint(self):
        url = validate_pool_url("stratum2+tls://sv2.example.com:3336", tls_required=True)
        endpoint = parse_endpoint(url)
        profile = build_profile("sv2", name="SV2", url=url, username="worker", password="secret", stratum_version=2, tls_required=True)
        self.assertTrue(endpoint.use_tls)
        self.assertEqual(2, profile.stratum_version)

    def test_live_session_sends_setup_connection_and_accepts_success(self):
        async def run_case():
            profile = build_profile("sv2", name="SV2", url="stratum2+tcp://sv2.example.com:3336", username="worker", password="secret", stratum_version=2)
            transport = FakeV2Transport()
            session = LiveStratumV2Session(profile, transport=transport)
            await session.connect()
            handshake = await session.setup_connection()
            await session.close()
            return handshake, transport

        import asyncio
        handshake, transport = asyncio.run(run_case())
        self.assertEqual(SV2_VERSION, handshake.used_version)
        self.assertEqual(1, len(transport.sent))
        self.assertEqual(SV2_MSG_SETUP_CONNECTION, transport.sent[0].message_type)
        self.assertTrue(transport.closed)

    def test_live_session_handles_setup_connection_timeout(self):
        async def run_case():
            profile = build_profile("sv2", name="SV2", url="stratum2+tcp://sv2.example.com:3336", username="worker", password="secret", stratum_version=2)
            
            class TimeoutTransport:
                def __init__(self):
                    self.closed = False
                async def connect(self):
                    return None
                async def send_frame(self, frame):
                    pass
                async def read_frame(self, timeout=None):
                    import asyncio
                    await asyncio.sleep(10)
                    return None
                async def close(self):
                    self.closed = True
            
            transport = TimeoutTransport()
            session = LiveStratumV2Session(profile, transport=transport)
            await session.connect()
            try:
                await session.setup_connection()
                self.fail("Should have raised timeout error")
            except Exception as e:
                self.assertIn("timeout", str(e).lower())
            finally:
                await session.close()

        import asyncio
        asyncio.run(run_case())

    def test_live_session_handles_version_mismatch(self):
        async def run_case():
            profile = build_profile("sv2", name="SV2", url="stratum2+tcp://sv2.example.com:3336", username="worker", password="secret", stratum_version=2)
            
            class VersionMismatchTransport:
                def __init__(self):
                    self.closed = False
                async def connect(self):
                    return None
                async def send_frame(self, frame):
                    pass
                async def read_frame(self, timeout=None):
                    bad_version = (3).to_bytes(2, "little") + (0).to_bytes(4, "little")
                    return StratumV2Frame(SV2_EXTENSION_TYPE_CORE, SV2_MSG_SETUP_CONNECTION_SUCCESS, bad_version)
                async def close(self):
                    self.closed = True
            
            transport = VersionMismatchTransport()
            session = LiveStratumV2Session(profile, transport=transport)
            await session.connect()
            try:
                await session.setup_connection()
                self.fail("Should have raised version mismatch error")
            except StratumV2ProtocolError as e:
                self.assertIn("version", str(e).lower())
            finally:
                await session.close()

        import asyncio
        asyncio.run(run_case())

    def test_pool_profile_rejects_invalid_stratum_v2_urls(self):
        invalid_urls = [
            "http://example.com:3336",
            "stratum+tcp://example.com:3336",
            "stratum2+tcp://",
            "stratum2+tcp://example.com",
            "stratum2+tcp://example.com:99999",
        ]
        for url in invalid_urls:
            with self.assertRaises((ValueError, StratumV2ProtocolError)):
                validate_pool_url(url, tls_required=False)

    def test_pool_profile_accepts_all_valid_stratum_v2_schemes(self):
        valid_schemes = [
            "stratum2+tcp://sv2.example.com:3336",
            "stratum2+ssl://sv2.example.com:3336",
            "stratum2+tls://sv2.example.com:3336",
        ]
        for url in valid_schemes:
            try:
                validated = validate_pool_url(url, tls_required=False)
                self.assertTrue(validiated.startswith("stratum2+"))
            except Exception as e:
                self.fail(f"Valid URL {url} should not raise error: {e}")


if __name__ == "__main__":
    unittest.main()
