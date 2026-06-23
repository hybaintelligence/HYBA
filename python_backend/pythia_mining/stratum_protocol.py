"""Stratum v1 protocol primitives for production pool integration.

The functions in this module are intentionally pure and deterministic. They
build JSON-RPC messages and parse pool notifications without opening sockets,
which makes them safe to test and reuse from live transports.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Sequence, Tuple

_HEX_RE = re.compile(r"^[0-9a-fA-F]*$")


class StratumProtocolError(ValueError):
    """Raised when a Stratum message is malformed or unsupported."""


@dataclass(frozen=True)
class SubscribeResult:
    extranonce1: str
    extranonce2_size: int
    raw_result: Any

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NotifyMessage:
    job_id: str
    prevhash: str
    coinbase1: str
    coinbase2: str
    merkle_branch: List[str]
    version: str
    nbits: str
    ntime: str
    clean_jobs: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DifficultyMessage:
    difficulty: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SetExtranonceMessage:
    extranonce1: str
    extranonce2_size: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SetVersionMaskMessage:
    version_mask: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _require_hex(value: str, field: str, *, even: bool = True) -> str:
    if not isinstance(value, str) or not value:
        raise StratumProtocolError(f"{field} must be a non-empty hex string")
    if even and len(value) % 2 != 0:
        raise StratumProtocolError(f"{field} must have even hex length")
    try:
        int(value, 16)
    except ValueError as exc:
        raise StratumProtocolError(f"{field} is not valid hex") from exc
    return value.lower()


def dumps_message(message_id: int, method: str, params: Sequence[Any]) -> str:
    if message_id <= 0:
        raise StratumProtocolError("message_id must be positive")
    if not method:
        raise StratumProtocolError("method is required")
    return (
        json.dumps(
            {"id": int(message_id), "method": method, "params": list(params)},
            separators=(",", ":"),
        )
        + "\n"
    )


def build_subscribe(message_id: int, user_agent: str = "hyba-pulvini/1.0") -> str:
    return dumps_message(message_id, "mining.subscribe", [user_agent])


def build_authorize(message_id: int, username: str, password: str) -> str:
    if not username:
        raise StratumProtocolError("username is required")
    if password is None:
        raise StratumProtocolError("password is required")
    return dumps_message(message_id, "mining.authorize", [username, password])


def build_submit(
    message_id: int,
    username: str,
    job_id: str,
    extranonce2: str,
    ntime: str,
    nonce: str,
) -> str:
    _require_hex(extranonce2, "extranonce2")
    _require_hex(ntime, "ntime")
    _require_hex(nonce, "nonce")
    if not username or not job_id:
        raise StratumProtocolError("username and job_id are required")
    return dumps_message(
        message_id,
        "mining.submit",
        [username, job_id, extranonce2.lower(), ntime.lower(), nonce.lower()],
    )


def parse_json_line(line: str) -> Dict[str, Any]:
    try:
        payload = json.loads(line)
    except json.JSONDecodeError as exc:
        raise StratumProtocolError("invalid JSON-RPC message") from exc
    if not isinstance(payload, dict):
        raise StratumProtocolError("Stratum message must be a JSON object")
    return payload


def parse_subscribe_result(message: Dict[str, Any]) -> SubscribeResult:
    if message.get("error"):
        raise StratumProtocolError(f"subscribe failed: {message['error']}")
    result = message.get("result")
    if not isinstance(result, list) or len(result) < 3:
        raise StratumProtocolError(
            "subscribe result must contain subscription data, extranonce1, extranonce2_size"
        )
    extranonce1_raw = str(result[1]) if result[1] else ""
    # Allow empty extranonce1 for live mining - use fallback
    if extranonce1_raw and not _HEX_RE.match(extranonce1_raw):
        raise StratumProtocolError(
            f"extranonce1 must be a hex string, got: {extranonce1_raw}"
        )
    extranonce1 = (
        extranonce1_raw if extranonce1_raw else "00000001"
    )  # Fallback for live mining
    size = int(result[2])
    if size <= 0 or size > 32:
        raise StratumProtocolError("extranonce2_size is out of safe range")
    return SubscribeResult(
        extranonce1=extranonce1, extranonce2_size=size, raw_result=result
    )


def parse_authorize_result(message: Dict[str, Any]) -> bool:
    if message.get("error"):
        raise StratumProtocolError(f"authorize failed: {message['error']}")
    return bool(message.get("result"))


def parse_notify_params(params: Sequence[Any]) -> NotifyMessage:
    if len(params) < 9:
        raise StratumProtocolError("mining.notify requires at least 9 params")
    job_id = str(params[0])
    prevhash = _require_hex(str(params[1]), "prevhash")
    coinbase1 = _require_hex(str(params[2]), "coinbase1")
    coinbase2 = _require_hex(str(params[3]), "coinbase2")
    branch_raw = params[4]
    if not isinstance(branch_raw, list):
        raise StratumProtocolError("merkle branch must be a list")
    merkle_branch = [_require_hex(str(item), "merkle_branch") for item in branch_raw]
    version = _require_hex(str(params[5]), "version")
    nbits = _require_hex(str(params[6]), "nbits")
    ntime = _require_hex(str(params[7]), "ntime")
    clean_jobs = bool(params[8])
    if not job_id:
        raise StratumProtocolError("job_id is required")
    return NotifyMessage(
        job_id,
        prevhash,
        coinbase1,
        coinbase2,
        merkle_branch,
        version,
        nbits,
        ntime,
        clean_jobs,
    )


def parse_set_difficulty(params: Sequence[Any]) -> DifficultyMessage:
    if not params:
        raise StratumProtocolError("mining.set_difficulty requires difficulty")
    difficulty = float(params[0])
    if difficulty <= 0:
        raise StratumProtocolError("difficulty must be positive")
    return DifficultyMessage(difficulty=difficulty)


def parse_set_extranonce(params: Sequence[Any]) -> SetExtranonceMessage:
    if len(params) < 2:
        raise StratumProtocolError(
            "mining.set_extranonce requires extranonce1 and extranonce2_size"
        )
    extranonce1 = _require_hex(str(params[0]), "extranonce1")
    extranonce2_size = int(params[1])
    if extranonce2_size <= 0 or extranonce2_size > 32:
        raise StratumProtocolError("extranonce2_size is out of safe range")
    return SetExtranonceMessage(
        extranonce1=extranonce1, extranonce2_size=extranonce2_size
    )


def parse_set_version_mask(params: Sequence[Any]) -> SetVersionMaskMessage:
    if not params:
        raise StratumProtocolError("mining.set_version_mask requires version_mask")
    version_mask = _require_hex(str(params[0]), "version_mask")
    return SetVersionMaskMessage(version_mask=version_mask)


def parse_server_message(line: str) -> Tuple[str, Any]:
    message = parse_json_line(line)
    method = message.get("method")
    if method == "mining.notify":
        return method, parse_notify_params(message.get("params", []))
    if method == "mining.set_difficulty":
        return method, parse_set_difficulty(message.get("params", []))
    if method == "mining.set_extranonce":
        return method, parse_set_extranonce(message.get("params", []))
    if method == "mining.set_version_mask":
        return method, parse_set_version_mask(message.get("params", []))
    if "id" in message:
        return "response", message
    # Log unsupported messages but don't raise - allows future protocol extensions
    if method:
        return "unknown", {"method": method, "params": message.get("params", [])}
    raise StratumProtocolError("unsupported Stratum server message")


__all__ = [
    "StratumProtocolError",
    "SubscribeResult",
    "NotifyMessage",
    "DifficultyMessage",
    "SetExtranonceMessage",
    "SetVersionMaskMessage",
    "build_subscribe",
    "build_authorize",
    "build_submit",
    "parse_json_line",
    "parse_subscribe_result",
    "parse_authorize_result",
    "parse_notify_params",
    "parse_set_difficulty",
    "parse_set_extranonce",
    "parse_set_version_mask",
    "parse_server_message",
]
