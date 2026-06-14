"""Live Stratum v1 session adapter.

This adapter composes the pure protocol primitives and the async line transport.
It owns live subscribe/authorize, pool event reads, and share submission responses.
"""

from __future__ import annotations

import itertools
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

from pythia_mining.pool_profiles import PoolProfile, validate_profile
from pythia_mining.stratum_protocol import (
    build_authorize,
    build_submit,
    build_subscribe,
    parse_authorize_result,
    parse_server_message,
    parse_subscribe_result,
)
from pythia_mining.stratum_transport import StratumLineTransport


class LiveStratumSessionError(ConnectionError):
    """Raised when a live Stratum session cannot subscribe, authorize, or submit."""


@dataclass(frozen=True)
class SessionHandshake:
    pool_id: str
    extranonce1: str
    extranonce2_size: int
    authorized: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SubmitResult:
    accepted: bool
    error: Optional[Any]
    response: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class LiveStratumSession:
    def __init__(self, profile: PoolProfile, *, transport: Optional[StratumLineTransport] = None):
        self.profile = validate_profile(profile)
        self.transport = transport or StratumLineTransport(profile.url)
        self._ids = itertools.count(1)
        self.extranonce1: Optional[str] = None
        self.extranonce2_size: Optional[int] = None
        self.authorized = False

    def next_id(self) -> int:
        return next(self._ids)

    async def connect(self) -> None:
        await self.transport.connect()

    async def _read_response_for_id(
        self, request_id: int, *, timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """Read until the matching JSON-RPC response arrives.

        Real Stratum pools may interleave notifications such as
        ``mining.set_difficulty`` or ``mining.notify`` during handshake and share
        submission. Treating the next line as the response makes live deployment
        brittle, so this helper ignores notifications and unrelated responses
        until the requested id is observed.
        """
        while True:
            line = await self.transport.read_line(timeout=timeout)
            event, payload = parse_server_message(line)
            if event == "response" and payload.get("id") == request_id:
                return payload

    async def subscribe_and_authorize(self) -> SessionHandshake:
        subscribe_id = self.next_id()
        await self.transport.send_line(build_subscribe(subscribe_id))
        subscribe_payload = await self._read_response_for_id(subscribe_id)
        subscribe = parse_subscribe_result(subscribe_payload)
        self.extranonce1 = subscribe.extranonce1
        self.extranonce2_size = subscribe.extranonce2_size

        authorize_id = self.next_id()
        await self.transport.send_line(
            build_authorize(authorize_id, self.profile.username, self.profile.password)
        )
        authorize_payload = await self._read_response_for_id(authorize_id)
        self.authorized = parse_authorize_result(authorize_payload)
        if not self.authorized:
            raise LiveStratumSessionError("pool rejected authorization")
        return SessionHandshake(
            self.profile.pool_id,
            self.extranonce1,
            self.extranonce2_size,
            self.authorized,
        )

    async def read_event(self, *, timeout: Optional[float] = None, include_responses: bool = False):
        while True:
            line = await self.transport.read_line(timeout=timeout)
            event, payload = parse_server_message(line)
            if include_responses or event != "response":
                return event, payload

    async def submit_share(
        self, *, job_id: str, extranonce2: str, ntime: str, nonce: str
    ) -> SubmitResult:
        if not self.authorized:
            raise LiveStratumSessionError("cannot submit before authorization")
        submit_id = self.next_id()
        await self.transport.send_line(
            build_submit(submit_id, self.profile.username, job_id, extranonce2, ntime, nonce)
        )
        payload = await self._read_response_for_id(submit_id)
        accepted = bool(payload.get("result")) and not payload.get("error")
        return SubmitResult(accepted=accepted, error=payload.get("error"), response=payload)

    async def close(self) -> None:
        await self.transport.close()


__all__ = [
    "LiveStratumSessionError",
    "SessionHandshake",
    "SubmitResult",
    "LiveStratumSession",
]
