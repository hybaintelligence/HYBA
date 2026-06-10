"""Async Stratum line transport.

This module provides a minimal TCP/TLS line transport for Stratum v1 JSON-RPC.
It does not perform mining logic; it only opens sockets, sends newline-delimited
messages, receives newline-delimited messages, and closes cleanly.
"""
from __future__ import annotations

import asyncio
import ssl
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse


class StratumTransportError(ConnectionError):
    """Raised when transport connection or I/O fails."""


@dataclass(frozen=True)
class TransportEndpoint:
    scheme: str
    host: str
    port: int
    use_tls: bool


def parse_endpoint(url: str, *, default_port: int = 3333) -> TransportEndpoint:
    parsed = urlparse(url)
    if not parsed.hostname:
        raise StratumTransportError("pool URL must include hostname")
    scheme = parsed.scheme
    use_tls = scheme in {"stratum+ssl", "stratum+tls", "stratum2+ssl"}
    if scheme not in {"stratum+tcp", "stratum+ssl", "stratum+tls", "stratum2+tcp", "stratum2+ssl"}:
        raise StratumTransportError(f"unsupported Stratum scheme: {scheme}")
    return TransportEndpoint(scheme=scheme, host=parsed.hostname, port=int(parsed.port or default_port), use_tls=use_tls)


class StratumLineTransport:
    def __init__(self, url: str, *, connect_timeout: float = 10.0, read_timeout: float = 30.0):
        self.url = url
        self.endpoint = parse_endpoint(url)
        self.connect_timeout = float(connect_timeout)
        self.read_timeout = float(read_timeout)
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None

    @property
    def connected(self) -> bool:
        return self.writer is not None and not self.writer.is_closing()

    async def connect(self) -> None:
        ssl_context = None
        if self.endpoint.use_tls:
            ssl_context = ssl.create_default_context()
            # Enforce certificate verification to prevent MITM attacks
            ssl_context.verify_mode = ssl.CERT_REQUIRED
            ssl_context.check_hostname = True
            # Use only secure TLS protocols
            ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
            ssl_context.maximum_version = ssl.TLSVersion.TLSv1_3
        try:
            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(self.endpoint.host, self.endpoint.port, ssl=ssl_context),
                timeout=self.connect_timeout,
            )
        except ssl.SSLCertVerificationError as exc:
            raise StratumTransportError(
                f"TLS certificate verification failed for {self.endpoint.host}:{self.endpoint.port}: {exc}"
            ) from exc
        except Exception as exc:  # pragma: no cover - network dependent
            raise StratumTransportError(f"failed to connect to {self.endpoint.host}:{self.endpoint.port}: {exc}") from exc

    async def send_line(self, line: str) -> None:
        if self.writer is None or self.writer.is_closing():
            raise StratumTransportError("transport is not connected")
        payload = line if line.endswith("\n") else line + "\n"
        self.writer.write(payload.encode("utf-8"))
        try:
            await self.writer.drain()
        except Exception as exc:  # pragma: no cover - network dependent
            raise StratumTransportError(f"failed to send Stratum line: {exc}") from exc

    async def read_line(self, *, timeout: Optional[float] = None) -> str:
        if self.reader is None:
            raise StratumTransportError("transport is not connected")
        try:
            raw = await asyncio.wait_for(self.reader.readline(), timeout=self.read_timeout if timeout is None else timeout)
        except asyncio.TimeoutError as exc:
            raise StratumTransportError("timed out waiting for Stratum line") from exc
        except Exception as exc:  # pragma: no cover - network dependent
            raise StratumTransportError(f"failed to read Stratum line: {exc}") from exc
        if raw == b"":
            raise StratumTransportError("pool closed Stratum connection")
        return raw.decode("utf-8").strip()

    async def close(self) -> None:
        if self.writer is not None:
            self.writer.close()
            try:
                await self.writer.wait_closed()
            except Exception:  # pragma: no cover - close best effort
                pass
        self.reader = None
        self.writer = None


__all__ = ["StratumTransportError", "TransportEndpoint", "parse_endpoint", "StratumLineTransport"]
