"""Live Stratum v1 session adapter.

This adapter composes the pure protocol primitives and the async line transport.
It is intentionally separate from the existing PoolManager so production rollout
can opt in without destabilising current tests or dashboards.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional

from pythia_mining.pool_profiles import PoolProfile, validate_profile
from pythia_mining.stratum_protocol import (
    StratumProtocolError,
    build_authorize,
    build_subscribe,
    parse_authorize_result,
    parse_server_message,
    parse_subscribe_result,
)
from pythia_mining.stratum_transport import StratumLineTransport, StratumTransportError


class LiveStratumSessionError(ConnectionError):
    """Raised when a live Stratum session cannot subscribe or authorize."""


@dataclass(frozen=True)
class SessionHandshake:
    pool_id: str
    extranonce1: str
    extranonce2_size: int
    authorized: bool
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

    async def subscribe_and_authorize(self) -> SessionHandshake:
        subscribe_id = self.next_id()
        await self.transport.send_line(build_subscribe(subscribe_id))
        subscribe_line = await self.transport.read_line()
        event, payload = parse_server_message(subscribe_line)
        if event != "response" or payload.get("id") != subscribe_id:
            raise LiveStratumSessionError("unexpected subscribe response")
        subscribe = parse_subscribe_result(payload)
        self.extranonce1 = subscribe.extranonce1
        self.extranonce2_size = subscribe.extranonce2_size

        authorize_id = self.next_id()
        await self.transport.send_line(build_authorize(authorize_id, self.profile.username, self.profile.password))
        authorize_line = await self.transport.read_line()
        event, payload = parse_server_message(authorize_line)
        if event != "response" or payload.get("id") != authorize_id:
            raise LiveStratumSessionError("unexpected authorize response")
        self.authorized = parse_authorize_result(payload)
        if not self.authorized:
            raise LiveStratumSessionError("pool rejected authorization")
        return SessionHandshake(self.profile.pool_id, self.extranonce1, self.extranonce2_size, self.authorized)

    async def read_event(self):
        line = await self.transport.read_line()
        return parse_server_message(line)

    async def close(self) -> None:
        await self.transport.close()


__all__ = ["LiveStratumSessionError", "SessionHandshake", "LiveStratumSession"]
