"""Live Stratum V2 common-handshake adapter.

This adapter performs only the transport-level ``SetupConnection`` handshake.
It intentionally does not synthesize mining jobs, extranonces, or share results;
subsequent channel-open/job messages must arrive from a real Stratum V2 pool.

Supports optional Noise protocol handshake for pools like Braiins that require
authenticated encrypted connections.
"""
from __future__ import annotations

import logging
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

try:
    from pythia_mining.noise_wrapper import NoiseWrapper, NoiseHandshakeResult, extract_pool_authority_key
    NOISE_AVAILABLE = True
except ImportError:
    NOISE_AVAILABLE = False
    NoiseWrapper = None
    NoiseHandshakeResult = None
    extract_pool_authority_key = None


logger = logging.getLogger("live_stratum_v2_session")


class LiveStratumV2SessionError(ConnectionError):
    """Raised when a live Stratum V2 setup handshake fails."""


@dataclass(frozen=True)
class StratumV2Handshake:
    pool_id: str
    used_version: int
    flags: int
    setup: Dict[str, Any]
    noise_handshake: Optional[NoiseHandshakeResult] = None

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        if self.noise_handshake:
            result["noise_handshake"] = {
                "encrypted": self.noise_handshake.encrypted,
                "remote_static_public": self.noise_handshake.remote_static_public.hex() if self.noise_handshake.remote_static_public else None,
            }
        return result


class LiveStratumV2Session:
    def __init__(
        self,
        profile: PoolProfile,
        *,
        transport: Optional[Any] = None,
        setup: Optional[SetupConnection] = None,
        enable_noise: bool = False,
        noise_static_key: Optional[bytes] = None,
        noise_remote_static_public: Optional[bytes] = None,
    ) -> None:
        self.profile = validate_profile(profile)
        if int(self.profile.stratum_version) != 2:
            raise LiveStratumV2SessionError("LiveStratumV2Session requires a Stratum V2 profile")
        self.transport = transport or StratumLineTransport(profile.url)
        self.setup = setup or setup_connection_from_url(profile.url)
        self.handshake: Optional[SetupConnectionSuccess] = None
        self.enable_noise = enable_noise
        self.noise_wrapper: Optional[NoiseWrapper] = None
        self.noise_handshake_result: Optional[NoiseHandshakeResult] = None
        
        if self.enable_noise and NOISE_AVAILABLE:
            self.noise_wrapper = NoiseWrapper()
            
            # Extract pool authority key from URL if not provided
            remote_key = noise_remote_static_public
            if remote_key is None and extract_pool_authority_key:
                remote_key = extract_pool_authority_key(profile.url)
                if remote_key:
                    logger.info(f"Extracted pool authority key from URL")
            
            self.noise_wrapper.initialize(
                local_static_key=noise_static_key,
                remote_static_public=remote_key
            )
        elif self.enable_noise and not NOISE_AVAILABLE:
            raise LiveStratumV2SessionError(
                "Noise protocol requested but noiseprotocol library not available. "
                "Install with: pip install noiseprotocol"
            )

    async def connect(self) -> None:
        await self.transport.connect()
        
        # Perform Noise protocol handshake if enabled
        if self.enable_noise and self.noise_wrapper:
            await self._perform_noise_handshake()

    async def _perform_noise_handshake(self) -> None:
        """Perform Noise protocol handshake before Stratum V2 setup."""
        if not self.noise_wrapper:
            return
            
        try:
            # Get the underlying reader/writer from transport
            if hasattr(self.transport, 'reader') and hasattr(self.transport, 'writer'):
                reader = self.transport.reader
                writer = self.transport.writer
            else:
                raise LiveStratumV2SessionError(
                    "Transport does not expose reader/writer for Noise handshake"
                )
            
            self.noise_handshake_result = await self.noise_wrapper.perform_handshake(
                reader, writer, is_initiator=True
            )
            
            if not self.noise_handshake_result.encrypted:
                raise LiveStratumV2SessionError("Noise handshake did not establish encryption")
                
        except Exception as e:
            raise LiveStratumV2SessionError(f"Noise protocol handshake failed: {e}")

    async def _send_frame(self, frame: StratumV2Frame) -> None:
        frame_bytes = encode_frame(frame)
        
        # Encrypt if noise protocol is enabled
        if self.enable_noise and self.noise_wrapper and self.noise_handshake_result:
            frame_bytes = await self.noise_wrapper.encrypt(frame_bytes)
        
        if hasattr(self.transport, "send_frame"):
            await self.transport.send_frame(frame)
            return
        await self.transport.send_bytes(frame_bytes)

    async def _read_frame(self, *, timeout: Optional[float] = None) -> StratumV2Frame:
        if hasattr(self.transport, "read_frame"):
            frame = await self.transport.read_frame(timeout=timeout)
        else:
            header = await self.transport.read_exactly(SV2_HEADER_SIZE, timeout=timeout)
            payload_length = decode_u24_le(header[3:6])
            payload = await self.transport.read_exactly(payload_length, timeout=timeout) if payload_length else b""
            frame = decode_frame(header + payload)
        
        # Decrypt if noise protocol is enabled
        if self.enable_noise and self.noise_wrapper and self.noise_handshake_result:
            frame_bytes = encode_frame(frame)
            decrypted_bytes = await self.noise_wrapper.decrypt(frame_bytes)
            frame = decode_frame(decrypted_bytes)
        
        return frame

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
            noise_handshake=self.noise_handshake_result,
        )


    async def submit_share(self, **_: Any) -> Any:
        raise LiveStratumV2SessionError(
            "Stratum V2 share submission requires an opened mining channel and pool job; no simulated submit path is available"
        )

    async def close(self) -> None:
        await self.transport.close()


__all__ = ["LiveStratumV2Session", "LiveStratumV2SessionError", "StratumV2Handshake"]
