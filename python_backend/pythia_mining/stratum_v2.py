"""Stratum V2 binary framing and common handshake primitives.

This module is intentionally limited to protocol-safe primitives: validating the
binary frame header, encoding payloads, decoding complete frames, and building
or parsing the common ``SetupConnection`` handshake.  It does not fabricate jobs
or emulate pool behavior; callers must provide bytes received from a real
Stratum V2 transport.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Tuple
from urllib.parse import urlparse


class StratumV2ProtocolError(ValueError):
    """Raised when a Stratum V2 frame or common message is malformed."""


SV2_HEADER_SIZE = 6
SV2_MAX_MESSAGE_SIZE = (1 << 24) - 1
SV2_EXTENSION_CHANNEL_MSG = 0x8000
SV2_EXTENSION_TYPE_CORE = 0x0000

SV2_MSG_SETUP_CONNECTION = 0x00
SV2_MSG_SETUP_CONNECTION_SUCCESS = 0x01
SV2_MSG_SETUP_CONNECTION_ERROR = 0x02

SV2_PROTOCOL_MINING = 0
SV2_VERSION = 2


@dataclass(frozen=True)
class StratumV2Frame:
    extension_type: int
    message_type: int
    payload: bytes

    @property
    def message_length(self) -> int:
        return len(self.payload)

    def to_dict(self, include_payload: bool = False) -> Dict[str, Any]:
        payload = asdict(self)
        payload["message_length"] = self.message_length
        payload["payload"] = self.payload.hex() if include_payload else "<binary>"
        return payload


@dataclass(frozen=True)
class SetupConnection:
    protocol: int = SV2_PROTOCOL_MINING
    min_version: int = SV2_VERSION
    max_version: int = SV2_VERSION
    flags: int = 0
    endpoint_host: str = ""
    endpoint_port: int = 3336
    vendor: str = "HYBA"
    hardware_version: str = "PULVINI-32"
    firmware: str = "hyba-pulvini/1.0"
    device_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SetupConnectionSuccess:
    used_version: int
    flags: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SetupConnectionError:
    flags: int
    error_code: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _require_uint(value: int, *, bits: int, field: str) -> int:
    value = int(value)
    if value < 0 or value >= (1 << bits):
        raise StratumV2ProtocolError(f"{field} must fit in uint{bits}")
    return value


def _encode_uint(value: int, *, bits: int, field: str) -> bytes:
    value = _require_uint(value, bits=bits, field=field)
    return value.to_bytes(bits // 8, "little")


def _decode_uint(payload: bytes, *, bits: int, field: str) -> int:
    size = bits // 8
    if len(payload) != size:
        raise StratumV2ProtocolError(f"{field} must be exactly {size} bytes")
    return int.from_bytes(payload, "little")


def encode_u24_le(value: int) -> bytes:
    value = _require_uint(value, bits=24, field="message_length")
    return value.to_bytes(3, "little")


def decode_u24_le(payload: bytes) -> int:
    if len(payload) != 3:
        raise StratumV2ProtocolError("uint24 payload must be exactly 3 bytes")
    return int.from_bytes(payload, "little")


def encode_str0_255(value: str, *, field: str = "str0_255") -> bytes:
    if not isinstance(value, str):
        raise StratumV2ProtocolError(f"{field} must be a string")
    encoded = value.encode("ascii")
    if len(encoded) > 255:
        raise StratumV2ProtocolError(f"{field} exceeds STR0_255 length")
    return len(encoded).to_bytes(1, "little") + encoded


def decode_str0_255(
    payload: bytes, offset: int = 0, *, field: str = "str0_255"
) -> Tuple[str, int]:
    if offset < 0 or offset >= len(payload) + 1:
        raise StratumV2ProtocolError(f"{field} offset is out of range")
    if offset == len(payload):
        raise StratumV2ProtocolError(f"{field} length prefix is missing")
    length = payload[offset]
    start = offset + 1
    end = start + length
    if end > len(payload):
        raise StratumV2ProtocolError(f"{field} payload is truncated")
    try:
        return payload[start:end].decode("ascii"), end
    except UnicodeDecodeError as exc:
        raise StratumV2ProtocolError(f"{field} must be ASCII") from exc


def encode_frame(frame: StratumV2Frame) -> bytes:
    extension_type = _require_uint(
        frame.extension_type, bits=16, field="extension_type"
    )
    message_type = _require_uint(frame.message_type, bits=8, field="message_type")
    if len(frame.payload) > SV2_MAX_MESSAGE_SIZE:
        raise StratumV2ProtocolError("payload exceeds Stratum V2 uint24 length")
    return (
        extension_type.to_bytes(2, "little")
        + message_type.to_bytes(1, "little")
        + encode_u24_le(len(frame.payload))
        + bytes(frame.payload)
    )


def decode_frame(data: bytes) -> StratumV2Frame:
    if len(data) < SV2_HEADER_SIZE:
        raise StratumV2ProtocolError("Stratum V2 frame header is incomplete")
    extension_type = int.from_bytes(data[0:2], "little")
    message_type = data[2]
    message_length = decode_u24_le(data[3:6])
    payload = data[SV2_HEADER_SIZE:]
    if len(payload) != message_length:
        raise StratumV2ProtocolError("Stratum V2 frame length does not match payload")
    return StratumV2Frame(
        extension_type=extension_type, message_type=message_type, payload=payload
    )


def split_complete_frame(buffer: bytes) -> tuple[StratumV2Frame | None, bytes]:
    if len(buffer) < SV2_HEADER_SIZE:
        return None, buffer
    message_length = decode_u24_le(buffer[3:6])
    frame_size = SV2_HEADER_SIZE + message_length
    if len(buffer) < frame_size:
        return None, buffer
    return decode_frame(buffer[:frame_size]), buffer[frame_size:]


def setup_connection_from_url(
    url: str,
    *,
    vendor: str = "HYBA",
    hardware_version: str = "PULVINI-32",
    firmware: str = "hyba-pulvini/1.0",
    device_id: str = "",
    flags: int = 0,
) -> SetupConnection:
    parsed = urlparse(url)
    if not parsed.hostname:
        raise StratumV2ProtocolError("SetupConnection endpoint_host is required")
    return SetupConnection(
        flags=_require_uint(flags, bits=32, field="flags"),
        endpoint_host=parsed.hostname,
        endpoint_port=int(parsed.port or 3336),
        vendor=vendor,
        hardware_version=hardware_version,
        firmware=firmware,
        device_id=device_id,
    )


def encode_setup_connection_payload(message: SetupConnection) -> bytes:
    if int(message.min_version) > int(message.max_version):
        raise StratumV2ProtocolError("min_version cannot exceed max_version")
    payload = bytearray()
    payload += _encode_uint(message.protocol, bits=8, field="protocol")
    payload += _encode_uint(message.min_version, bits=16, field="min_version")
    payload += _encode_uint(message.max_version, bits=16, field="max_version")
    payload += _encode_uint(message.flags, bits=32, field="flags")
    payload += encode_str0_255(message.endpoint_host, field="endpoint_host")
    payload += _encode_uint(message.endpoint_port, bits=16, field="endpoint_port")
    payload += encode_str0_255(message.vendor, field="vendor")
    payload += encode_str0_255(message.hardware_version, field="hardware_version")
    payload += encode_str0_255(message.firmware, field="firmware")
    payload += encode_str0_255(message.device_id, field="device_id")
    return bytes(payload)


def decode_setup_connection_payload(payload: bytes) -> SetupConnection:
    if len(payload) < 9:
        raise StratumV2ProtocolError("SetupConnection payload is too short")
    protocol = payload[0]
    min_version = _decode_uint(payload[1:3], bits=16, field="min_version")
    max_version = _decode_uint(payload[3:5], bits=16, field="max_version")
    flags = _decode_uint(payload[5:9], bits=32, field="flags")
    endpoint_host, offset = decode_str0_255(payload, 9, field="endpoint_host")
    if offset + 2 > len(payload):
        raise StratumV2ProtocolError("endpoint_port is missing")
    endpoint_port = _decode_uint(
        payload[offset : offset + 2], bits=16, field="endpoint_port"
    )
    offset += 2
    vendor, offset = decode_str0_255(payload, offset, field="vendor")
    hardware_version, offset = decode_str0_255(
        payload, offset, field="hardware_version"
    )
    firmware, offset = decode_str0_255(payload, offset, field="firmware")
    device_id, offset = decode_str0_255(payload, offset, field="device_id")
    if offset != len(payload):
        raise StratumV2ProtocolError("SetupConnection payload contains trailing bytes")
    return SetupConnection(
        protocol,
        min_version,
        max_version,
        flags,
        endpoint_host,
        endpoint_port,
        vendor,
        hardware_version,
        firmware,
        device_id,
    )


def build_setup_connection_frame(message: SetupConnection) -> StratumV2Frame:
    return StratumV2Frame(
        extension_type=SV2_EXTENSION_TYPE_CORE,
        message_type=SV2_MSG_SETUP_CONNECTION,
        payload=encode_setup_connection_payload(message),
    )


def parse_setup_connection_success(
    frame: StratumV2Frame, *, requested: SetupConnection | None = None
) -> SetupConnectionSuccess:
    if (
        frame.extension_type != SV2_EXTENSION_TYPE_CORE
        or frame.message_type != SV2_MSG_SETUP_CONNECTION_SUCCESS
    ):
        raise StratumV2ProtocolError("expected SetupConnection.Success core frame")
    if len(frame.payload) != 6:
        raise StratumV2ProtocolError("SetupConnection.Success payload must be 6 bytes")
    used_version = _decode_uint(frame.payload[0:2], bits=16, field="used_version")
    flags = _decode_uint(frame.payload[2:6], bits=32, field="flags")
    if requested is not None and not (
        int(requested.min_version) <= used_version <= int(requested.max_version)
    ):
        raise StratumV2ProtocolError(
            "SetupConnection.Success used_version is outside requested range"
        )
    return SetupConnectionSuccess(used_version=used_version, flags=flags)


def parse_setup_connection_error(frame: StratumV2Frame) -> SetupConnectionError:
    if (
        frame.extension_type != SV2_EXTENSION_TYPE_CORE
        or frame.message_type != SV2_MSG_SETUP_CONNECTION_ERROR
    ):
        raise StratumV2ProtocolError("expected SetupConnection.Error core frame")
    if len(frame.payload) < 5:
        raise StratumV2ProtocolError("SetupConnection.Error payload is too short")
    flags = _decode_uint(frame.payload[0:4], bits=32, field="flags")
    error_code, offset = decode_str0_255(frame.payload, 4, field="error_code")
    if offset != len(frame.payload):
        raise StratumV2ProtocolError(
            "SetupConnection.Error payload contains trailing bytes"
        )
    return SetupConnectionError(flags=flags, error_code=error_code)


def parse_setup_connection_response(
    frame: StratumV2Frame, *, requested: SetupConnection | None = None
) -> SetupConnectionSuccess:
    if frame.message_type == SV2_MSG_SETUP_CONNECTION_SUCCESS:
        return parse_setup_connection_success(frame, requested=requested)
    if frame.message_type == SV2_MSG_SETUP_CONNECTION_ERROR:
        error = parse_setup_connection_error(frame)
        raise StratumV2ProtocolError(
            f"SetupConnection.Error: {error.error_code} (flags={error.flags})"
        )
    raise StratumV2ProtocolError(
        "expected SetupConnection.Success or SetupConnection.Error"
    )


__all__ = [
    "SV2_EXTENSION_CHANNEL_MSG",
    "SV2_EXTENSION_TYPE_CORE",
    "SV2_HEADER_SIZE",
    "SV2_MAX_MESSAGE_SIZE",
    "SV2_MSG_SETUP_CONNECTION",
    "SV2_MSG_SETUP_CONNECTION_ERROR",
    "SV2_MSG_SETUP_CONNECTION_SUCCESS",
    "SV2_PROTOCOL_MINING",
    "SV2_VERSION",
    "SetupConnection",
    "SetupConnectionError",
    "SetupConnectionSuccess",
    "StratumV2Frame",
    "StratumV2ProtocolError",
    "build_setup_connection_frame",
    "decode_frame",
    "decode_setup_connection_payload",
    "decode_str0_255",
    "decode_u24_le",
    "encode_frame",
    "encode_setup_connection_payload",
    "encode_str0_255",
    "encode_u24_le",
    "parse_setup_connection_error",
    "parse_setup_connection_response",
    "parse_setup_connection_success",
    "setup_connection_from_url",
    "split_complete_frame",
]
