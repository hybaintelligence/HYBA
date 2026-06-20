#!/usr/bin/env python3
"""ViaBTC Stratum handshake smoke with live and deterministic mock modes.

Live mode performs real DNS/TCP I/O and records redacted evidence. Mock mode is
for CI: it exercises the same transcript/parser path without external network
or fabricated share acceptance. This script never submits shares.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import socket
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable, List, Tuple

DEFAULT_HOST = "btc.viabtc.io"
DEFAULT_PORT = 3333
DEFAULT_WORKER = "PYTHIA.001"
DEFAULT_PASSWORD = "123"


@dataclass(frozen=True)
class HandshakeEvidence:
    mode: str
    endpoint: str
    worker_redacted: str
    connected: bool
    subscribed: bool
    authorized: bool
    share_submitted: bool
    accepted_share_claimed: bool
    duration_ms: float
    transcript_sha256: str
    transcript_redacted: List[str]

    def to_dict(self) -> dict:
        return asdict(self)


class _SocketLineTransport:
    def __init__(self, host: str, port: int, timeout: float):
        self._socket = socket.create_connection((host, port), timeout=timeout)
        self._socket.settimeout(timeout)
        self._file = self._socket.makefile("rb")

    def send_json(self, payload: dict) -> None:
        self._socket.sendall((json.dumps(payload, separators=(",", ":")) + "\n").encode())

    def read_line(self) -> str:
        raw = self._file.readline()
        if not raw:
            raise ConnectionError("stratum endpoint closed connection")
        return raw.decode("utf-8", errors="replace").strip()

    def close(self) -> None:
        self._file.close()
        self._socket.close()


class _MockLineTransport:
    def __init__(self, responses: Iterable[dict]):
        self.sent: List[dict] = []
        self._responses = list(responses)

    def send_json(self, payload: dict) -> None:
        self.sent.append(payload)

    def read_line(self) -> str:
        if not self._responses:
            raise ConnectionError("mock stratum transcript exhausted")
        return json.dumps(self._responses.pop(0), separators=(",", ":"))

    def close(self) -> None:
        return None


def _redact(line: str, worker: str, password: str) -> str:
    return line.replace(worker, "<worker>").replace(password, "<password>")


def run_handshake(
    *,
    mode: str,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    worker: str = DEFAULT_WORKER,
    password: str = DEFAULT_PASSWORD,
    timeout: float = 10.0,
    transport_factory: Callable[[], object] | None = None,
) -> HandshakeEvidence:
    """Run subscribe/authorize only and return redacted evidence."""

    start = time.time()
    transport = transport_factory() if transport_factory else _SocketLineTransport(host, port, timeout)
    transcript: List[str] = []
    subscribed = False
    authorized = False
    try:
        subscribe = {"id": 1, "method": "mining.subscribe", "params": ["HYBA-PYTHIA-smoke/1.0"]}
        authorize = {"id": 2, "method": "mining.authorize", "params": [worker, password]}
        transport.send_json(subscribe)  # type: ignore[attr-defined]
        for _ in range(8):
            line = transport.read_line()  # type: ignore[attr-defined]
            transcript.append(line)
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if payload.get("id") == 1:
                subscribed = bool(payload.get("result")) and not payload.get("error")
                break
        transport.send_json(authorize)  # type: ignore[attr-defined]
        for _ in range(8):
            line = transport.read_line()  # type: ignore[attr-defined]
            transcript.append(line)
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if payload.get("id") == 2:
                authorized = bool(payload.get("result")) and not payload.get("error")
                break
    finally:
        transport.close()  # type: ignore[attr-defined]

    redacted = [_redact(line, worker, password) for line in transcript]
    digest = hashlib.sha256("\n".join(redacted).encode("utf-8")).hexdigest()
    return HandshakeEvidence(
        mode=mode,
        endpoint=f"{host}:{port}",
        worker_redacted="<worker>",
        connected=True,
        subscribed=subscribed,
        authorized=authorized,
        share_submitted=False,
        accepted_share_claimed=False,
        duration_ms=round((time.time() - start) * 1000.0, 2),
        transcript_sha256=digest,
        transcript_redacted=redacted,
    )


def run_mock_handshake() -> HandshakeEvidence:
    responses = [
        {"id": 1, "result": [[ ["mining.set_difficulty", "1"], ["mining.notify", "1"] ], "abcdef01", 4], "error": None},
        {"id": 2, "result": True, "error": None},
    ]
    return run_handshake(mode="mock", transport_factory=lambda: _MockLineTransport(responses))


def write_evidence(evidence: HandshakeEvidence, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"viabtc_{evidence.mode}_handshake_{int(time.time())}.json"
    path.write_text(json.dumps(evidence.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("mock", "live"), default="mock")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--worker", default=DEFAULT_WORKER)
    parser.add_argument("--password", default=DEFAULT_PASSWORD)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--output-dir", default="artifacts/live_evidence")
    args = parser.parse_args()

    if args.mode == "mock":
        evidence = run_mock_handshake()
    else:
        evidence = run_handshake(
            mode="live",
            host=args.host,
            port=args.port,
            worker=args.worker,
            password=args.password,
            timeout=args.timeout,
        )
    path = write_evidence(evidence, Path(args.output_dir))
    print(json.dumps({"evidence_path": str(path), **evidence.to_dict()}, indent=2, sort_keys=True))
    return 0 if evidence.subscribed and evidence.authorized else 2


if __name__ == "__main__":
    raise SystemExit(main())
