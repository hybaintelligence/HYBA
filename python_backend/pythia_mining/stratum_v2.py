"""Minimal Stratum V2 binary framing and setup handshake primitives.

The implementation covers the production-critical framing contract used by a
proxy/head node: uint24 little-endian message lengths, binary frame encode /
decode, SetupConnection construction, and SetupConnection.Success parsing.
"""

from __future__ import annotations

import asyncio
import socket
from dataclasses import asdict, dataclass
from typing import Any, Optional
from urllib.parse import urlparse

from pythia_mining.pool_profiles import PoolProfile, validate_profile

SV2_HEADER_SIZE = 6
SV2_MAX_FRAME_PAYLOAD = (1 << 24) - 1
SV2_SETUP_CONNECTION = 0x00
SV2_SETUP_CONNECTION_SUCCESS = 0x01
SV2_SETUP_CONNECTION_ERROR = 0x02
SV2_MIN_VERSION = 2
SV2_MAX_VERSION = 2
SV2_MINING_PROTOCOL = 0


class StratumV2ProtocolError(ValueError):
    """Raised when a Stratum V2 frame or payload is malformed."""


class LiveStratumV2SessionError(ConnectionError):
    """Raised when the live Stratum V2 setup handshake fails."""


@dataclass(frozen=True)
class StratumV2Frame:
    extension_type: int
    msg_type: int
    payload: bytes

    def to_bytes(self) -> bytes:
        return encode_frame(self.extension_type, self.msg_type, self.payload)


@dataclass(frozen=True)
class StratumV2Handshake:
    pool_id: str
    used_version: int
    flags: int
    endpoint_host: str
    endpoint_port: int
    authorized: bool = True

    @property
    def extranonce1(self) -> str:
        # Stratum V2 channel-specific extranonce material arrives after setup.
        return ""

    @property
    def extranonce2_size(self) -> int:
        return 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def encode_uint24(value: int) -> bytes:
    value = int(value)
    if value < 0 or value > SV2_MAX_FRAME_PAYLOAD:
        raise StratumV2ProtocolError("uint24 value out of range")
    return value.to_bytes(3, "little")


def decode_uint24(payload: bytes) -> int:
    if len(payload) != 3:
        raise StratumV2ProtocolError("uint24 requires exactly three bytes")
    return int.from_bytes(payload, "little")


def encode_frame(extension_type: int, msg_type: int, payload: bytes) -> bytes:
    payload = bytes(payload)
    if not 0 <= int(extension_type) <= 0xFFFF:
        raise StratumV2ProtocolError("extension_type must fit uint16")
    if not 0 <= int(msg_type) <= 0xFF:
        raise StratumV2ProtocolError("msg_type must fit uint8")
    if len(payload) > SV2_MAX_FRAME_PAYLOAD:
        raise StratumV2ProtocolError("payload exceeds uint24 frame length")
    return int(extension_type).to_bytes(2, "little") + bytes([int(msg_type)]) + encode_uint24(len(payload)) + payload


def decode_frame(data: bytes) -> StratumV2Frame:
    data = bytes(data)
    if len(data) < SV2_HEADER_SIZE:
        raise StratumV2ProtocolError("frame shorter than Stratum V2 header")
    extension_type = int.from_bytes(data[0:2], "little")
    msg_type = data[2]
    length = decode_uint24(data[3:6])
    payload = data[6:]
    if len(payload) != length:
        raise StratumV2ProtocolError("frame length does not match payload")
    return StratumV2Frame(extension_type, msg_type, payload)


def _encode_sv2_string(value: str) -> bytes:
    encoded = value.encode("utf-8")
    if len(encoded) > 0xFFFF:
        raise StratumV2ProtocolError("string too long for setup payload")
    return len(encoded).to_bytes(2, "little") + encoded


def _decode_sv2_string(payload: bytes, offset: int = 0) -> tuple[str, int]:
    if offset + 2 > len(payload):
        raise StratumV2ProtocolError("missing string length")
    size = int.from_bytes(payload[offset:offset + 2], "little")
    offset += 2
    if offset + size > len(payload):
        raise StratumV2ProtocolError("string length exceeds payload")
    return payload[offset:offset + size].decode("utf-8"), offset + size


def build_setup_connection_payload(
    *,
    endpoint_host: str,
    endpoint_port: int,
    vendor: str = "HYBA",
    hardware_version: str = "PULVINI-32",
    firmware: str = "hyba-pythia",
    device_id: str = "pulvini-head-node",
    flags: int = 0,
) -> bytes:
    if not endpoint_host:
        raise StratumV2ProtocolError("endpoint_host is required")
    if not 0 < int(endpoint_port) <= 65535:
        raise StratumV2ProtocolError("endpoint_port must fit uint16")
    return b"".join(
        [
            bytes([SV2_MINING_PROTOCOL]),
            SV2_MIN_VERSION.to_bytes(2, "little"),
            SV2_MAX_VERSION.to_bytes(2, "little"),
            int(flags).to_bytes(4, "little"),
            _encode_sv2_string(endpoint_host),
            int(endpoint_port).to_bytes(2, "little"),
            _encode_sv2_string(vendor),
            _encode_sv2_string(hardware_version),
            _encode_sv2_string(firmware),
            _encode_sv2_string(device_id),
        ]
    )


def build_setup_connection_frame(**kwargs: Any) -> bytes:
    return encode_frame(0, SV2_SETUP_CONNECTION, build_setup_connection_payload(**kwargs))


def parse_setup_connection_success(payload: bytes) -> dict[str, int]:
    if len(payload) < 6:
        raise StratumV2ProtocolError("SetupConnection.Success payload must contain used_version and flags")
    return {"used_version": int.from_bytes(payload[0:2], "little"), "flags": int.from_bytes(payload[2:6], "little")}


def parse_setup_connection_error(payload: bytes) -> dict[str, Any]:
    code, offset = _decode_sv2_string(payload, 0)
    return {"error_code": code, "extra": payload[offset:].hex()}


class StratumV2SocketTransport:
    def __init__(self, url: str, *, timeout: float = 10.0):
        self.url = url
        self.timeout = float(timeout)
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None

    async def connect(self) -> None:
        parsed = urlparse(self.url)
        host = parsed.hostname
        if not host:
            raise LiveStratumV2SessionError("Stratum V2 URL must include a hostname")
        port = parsed.port or 3336
        ssl_context = True if parsed.scheme in {"stratum2+ssl", "stratum2+tls"} else None
        try:
            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(host, port, ssl=ssl_context, family=socket.AF_UNSPEC),
                timeout=self.timeout,
            )
        except Exception as exc:  # noqa: BLE001 - preserve connection cause in session error
            raise LiveStratumV2SessionError(f"failed to connect Stratum V2 transport: {exc}") from exc

    async def send_frame(self, frame: bytes) -> None:
        if self.writer is None:
            raise LiveStratumV2SessionError("Stratum V2 transport is not connected")
        self.writer.write(bytes(frame))
        await self.writer.drain()

    async def read_frame(self) -> StratumV2Frame:
        if self.reader is None:
            raise LiveStratumV2SessionError("Stratum V2 transport is not connected")
        header = await asyncio.wait_for(self.reader.readexactly(SV2_HEADER_SIZE), timeout=self.timeout)
        length = decode_uint24(header[3:6])
        payload = await asyncio.wait_for(self.reader.readexactly(length), timeout=self.timeout)
        return decode_frame(header + payload)

    async def close(self) -> None:
        if self.writer is not None:
            self.writer.close()
            await self.writer.wait_closed()
        self.reader = None
        self.writer = None


class LiveStratumV2Session:
    def __init__(self, profile: PoolProfile, *, transport: Optional[Any] = None):
        self.profile = validate_profile(profile)
        self.transport = transport or StratumV2SocketTransport(profile.url)
        parsed = urlparse(profile.url)
        self.endpoint_host = parsed.hostname or "localhost"
        self.endpoint_port = parsed.port or 3336
        self.handshake: Optional[StratumV2Handshake] = None

    async def connect(self) -> None:
        await self.transport.connect()

    async def setup_connection(self) -> StratumV2Handshake:
        await self.transport.send_frame(
            build_setup_connection_frame(
                endpoint_host=self.endpoint_host,
                endpoint_port=self.endpoint_port,
                device_id=self.profile.username or "pulvini-head-node",
            )
        )
        frame = await self.transport.read_frame()
        if frame.msg_type == SV2_SETUP_CONNECTION_ERROR:
            error = parse_setup_connection_error(frame.payload)
            raise LiveStratumV2SessionError(f"SetupConnection.Error: {error['error_code']}")
        if frame.msg_type != SV2_SETUP_CONNECTION_SUCCESS:
            raise LiveStratumV2SessionError(f"unexpected Stratum V2 setup response type: {frame.msg_type}")
        success = parse_setup_connection_success(frame.payload)
        self.handshake = StratumV2Handshake(
            pool_id=self.profile.pool_id,
            used_version=success["used_version"],
            flags=success["flags"],
            endpoint_host=self.endpoint_host,
            endpoint_port=self.endpoint_port,
            authorized=True,
        )
        return self.handshake

    async def close(self) -> None:
        await self.transport.close()


__all__ = [
    "LiveStratumV2Session",
    "LiveStratumV2SessionError",
    "SV2_HEADER_SIZE",
    "SV2_SETUP_CONNECTION",
    "SV2_SETUP_CONNECTION_ERROR",
    "SV2_SETUP_CONNECTION_SUCCESS",
    "StratumV2Frame",
    "StratumV2Handshake",
    "StratumV2ProtocolError",
    "build_setup_connection_frame",
    "build_setup_connection_payload",
    "decode_frame",
    "decode_uint24",
    "encode_frame",
    "encode_uint24",
    "parse_setup_connection_error",
    "parse_setup_connection_success",
]
