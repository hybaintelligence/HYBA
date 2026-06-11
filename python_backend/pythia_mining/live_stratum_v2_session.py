"""Live Stratum V2 common-handshake adapter.

This adapter performs only the transport-level ``SetupConnection`` handshake.
It intentionally does not synthesize mining jobs, extranonces, or share results;
subsequent channel-open/job messages must arrive from a real Stratum V2 pool.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

from pythia_mining.pool_profiles import PoolProfile, validate_profile
from pythia_mining.stratum_transport import StratumLineTransport
from pythia_mining.stratum_v2 import (
    SV2_HEADER_SIZE,
    SetupConnection,
    SetupConnectionSuccess,
    StratumV2Frame,
    StratumV2ProtocolError,
    build_setup_connection_frame,
    decode_frame,
    decode_u24_le,
    encode_frame,
    parse_setup_connection_response,
    setup_connection_from_url,
)


class LiveStratumV2SessionError(ConnectionError):
    """Raised when a live Stratum V2 setup handshake fails."""


@dataclass(frozen=True)
class StratumV2Handshake:
    pool_id: str
    used_version: int
    flags: int
    setup: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class LiveStratumV2Session:
    def __init__(
        self,
        profile: PoolProfile,
        *,
        transport: Optional[Any] = None,
        setup: Optional[SetupConnection] = None,
    ) -> None:
        self.profile = validate_profile(profile)
        if int(self.profile.stratum_version) != 2:
            raise LiveStratumV2SessionError("LiveStratumV2Session requires a Stratum V2 profile")
        self.transport = transport or StratumLineTransport(profile.url)
        self.setup = setup or setup_connection_from_url(profile.url)
        self.handshake: Optional[SetupConnectionSuccess] = None

    async def connect(self) -> None:
        await self.transport.connect()

    async def _send_frame(self, frame: StratumV2Frame) -> None:
        if hasattr(self.transport, "send_frame"):
            await self.transport.send_frame(frame)
            return
        await self.transport.send_bytes(encode_frame(frame))

    async def _read_frame(self, *, timeout: Optional[float] = None) -> StratumV2Frame:
        if hasattr(self.transport, "read_frame"):
            return await self.transport.read_frame(timeout=timeout)
        header = await self.transport.read_exactly(SV2_HEADER_SIZE, timeout=timeout)
        payload_length = decode_u24_le(header[3:6])
        payload = await self.transport.read_exactly(payload_length, timeout=timeout) if payload_length else b""
        return decode_frame(header + payload)

    async def setup_connection(self, *, timeout: Optional[float] = None) -> StratumV2Handshake:
        try:
            await self._send_frame(build_setup_connection_frame(self.setup))
            response = await self._read_frame(timeout=timeout)
            self.handshake = parse_setup_connection_response(response, requested=self.setup)
        except StratumV2ProtocolError as exc:
            raise LiveStratumV2SessionError(str(exc)) from exc
        return StratumV2Handshake(
            pool_id=self.profile.pool_id,
            used_version=self.handshake.used_version,
            flags=self.handshake.flags,
            setup=self.setup.to_dict(),
        )


    async def submit_share(self, **_: Any) -> Any:
        raise LiveStratumV2SessionError(
            "Stratum V2 share submission requires an opened mining channel and pool job; no simulated submit path is available"
        )

    async def close(self) -> None:
        await self.transport.close()


__all__ = ["LiveStratumV2Session", "LiveStratumV2SessionError", "StratumV2Handshake"]
