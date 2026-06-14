"""Run a controlled HYBA_FULLSTACK mining-session evidence capture.

This command-room helper is intentionally evidence-first:

* it does not embed operator or pool credentials;
* it captures true pre-configuration, post-configuration, post-connect,
  periodic session, final, and post-disconnect snapshots;
* it records share counters separately from connection evidence;
* it keeps revenue/accepted-share claims dependent on pool-side evidence.

Required environment variables:
    HYBA_OPERATOR_USERNAME
    HYBA_OPERATOR_PASSWORD
    HYBA_POOL_ID
    HYBA_POOL_URL
    HYBA_POOL_USERNAME
    HYBA_POOL_PASSWORD

Optional environment variables:
    HYBA_BACKEND_BASE=http://127.0.0.1:3001
    HYBA_BRIDGE_BASE=http://127.0.0.1:3000
    HYBA_EVIDENCE_DIR=HYBA_FULLSTACK_COMMAND_ROOM_20260612
    HYBA_SESSION_MINUTES=5
    HYBA_SESSION_CAPACITY_EHS=0.1
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

BASE = os.getenv("HYBA_BACKEND_BASE", "http://127.0.0.1:3001")
BRIDGE = os.getenv("HYBA_BRIDGE_BASE", "http://127.0.0.1:3000")
EVIDENCE_DIR = Path(os.getenv("HYBA_EVIDENCE_DIR", "HYBA_FULLSTACK_COMMAND_ROOM_20260612"))
SESSION_MINUTES = int(os.getenv("HYBA_SESSION_MINUTES", "5"))
SESSION_CAPACITY_EHS = float(os.getenv("HYBA_SESSION_CAPACITY_EHS", "0.1"))


REQUIRED_ENV = [
    "HYBA_OPERATOR_USERNAME",
    "HYBA_OPERATOR_PASSWORD",
    "HYBA_POOL_ID",
    "HYBA_POOL_URL",
    "HYBA_POOL_USERNAME",
    "HYBA_POOL_PASSWORD",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def log(message: str) -> None:
    print(f"[{utc_now()}] {message}", flush=True)


def require_env() -> dict[str, str]:
    missing = [name for name in REQUIRED_ENV if not os.getenv(name)]
    if missing:
        raise SystemExit("Missing required environment variables: " + ", ".join(missing))
    return {name: os.environ[name] for name in REQUIRED_ENV}


def write_json(name: str, payload: Any) -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    path = EVIDENCE_DIR / name
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    log(f"Wrote {path}")


def get_json(url: str, *, headers: dict[str, str] | None = None) -> Any:
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    return response.json()


def post_json(
    url: str,
    payload: dict[str, Any] | None = None,
    *,
    headers: dict[str, str] | None = None,
) -> requests.Response:
    response = requests.post(url, json=payload or {}, headers=headers, timeout=30)
    response.raise_for_status()
    return response


def redact_status(payload: Any) -> Any:
    """Return payload with obvious secret-bearing fields redacted."""
    if isinstance(payload, dict):
        redacted: dict[str, Any] = {}
        for key, value in payload.items():
            lowered = key.lower()
            if lowered in {"password", "token", "secret", "api_key", "authorization"}:
                redacted[key] = "<redacted>"
            elif lowered in {"url", "pool_url"} and isinstance(value, str):
                redacted[key] = value.split("?")[0]
            else:
                redacted[key] = redact_status(value)
        return redacted
    if isinstance(payload, list):
        return [redact_status(item) for item in payload]
    return payload


def main() -> int:
    env = require_env()
    log("Starting controlled mining-session evidence capture")
    log(f"Backend={BASE} Bridge={BRIDGE} EvidenceDir={EVIDENCE_DIR}")

    # 1. Health snapshots before authentication or pool mutation.
    write_json("bridge_health_pre_session.json", get_json(f"{BRIDGE}/bridge/health"))
    write_json("backend_readiness_pre_session.json", get_json(f"{BASE}/api/health/readiness"))

    # 2. Login with externally supplied operator credentials.
    log("Authenticating operator")
    login = post_json(
        f"{BASE}/api/auth/login",
        {
            "username": env["HYBA_OPERATOR_USERNAME"],
            "password": env["HYBA_OPERATOR_PASSWORD"],
        },
    ).json()
    token = login["token"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    write_json(
        "operator_login_summary.json",
        {
            "authenticated": True,
            "username": env["HYBA_OPERATOR_USERNAME"],
            "token_prefix": token[:12] + "...",
            "timestamp": utc_now(),
        },
    )

    # 3. True pre-configuration/pre-connect status.
    log("Capturing true pre-configuration mining status")
    write_json(
        "mining_status_00_pre_config.json",
        redact_status(get_json(f"{BASE}/api/mining/status", headers=headers)),
    )

    # 4. Configure selected pool without embedding credentials in source.
    pool_id = env["HYBA_POOL_ID"]
    log(f"Configuring pool profile {pool_id}")
    config_response = post_json(
        f"{BASE}/api/mining/pool-config",
        {
            "pool_id": pool_id,
            "url": env["HYBA_POOL_URL"],
            "username": env["HYBA_POOL_USERNAME"],
            "password": env["HYBA_POOL_PASSWORD"],
            "enabled": True,
        },
        headers=headers,
    )
    write_json("pool_config_response.json", redact_status(config_response.json()))
    write_json(
        "mining_status_01_post_config_pre_connect.json",
        redact_status(get_json(f"{BASE}/api/mining/status", headers=headers)),
    )

    # 5. Explicit operator connect.
    log("Connecting to configured pool via MIDAS/operator path")
    connect_response = post_json(
        f"{BASE}/api/mining/connect",
        {"pool_id": pool_id, "capacity_ehs": SESSION_CAPACITY_EHS, "switch": True},
        headers=headers,
    )
    write_json("pool_connect_response.json", redact_status(connect_response.json()))
    write_json(
        "mining_status_02_post_connect.json",
        redact_status(get_json(f"{BASE}/api/mining/status", headers=headers)),
    )

    # 6. Timed session with per-minute snapshots.
    log("=" * 56)
    log(f"MINING SESSION STARTED — {SESSION_MINUTES} MINUTES")
    log("=" * 56)
    minute_summaries: list[dict[str, Any]] = []
    for minute in range(1, SESSION_MINUTES + 1):
        time.sleep(60)
        status = redact_status(get_json(f"{BASE}/api/mining/status", headers=headers))
        bridge = get_json(f"{BRIDGE}/bridge/health")
        summary = {
            "minute": minute,
            "timestamp": utc_now(),
            "active": status.get("active"),
            "hashrate_ehs": status.get("hashrate_ehs"),
            "shares": status.get("shares", {}),
            "acceptance_rate": status.get("acceptance_rate"),
            "bridge_status": bridge.get("status"),
        }
        minute_summaries.append(summary)
        write_json(f"mining_status_minute_{minute:02d}.json", status)
        log(
            "Minute %s/%s: submitted=%s accepted=%s rejected=%s hashrate=%s EH/s active=%s bridge=%s"
            % (
                minute,
                SESSION_MINUTES,
                summary["shares"].get("submitted", 0),
                summary["shares"].get("accepted", 0),
                summary["shares"].get("rejected", 0),
                summary.get("hashrate_ehs"),
                summary.get("active"),
                summary.get("bridge_status"),
            )
        )
    write_json("mining_session_minute_summary.json", minute_summaries)

    # 7. Final status and pools status before disconnect.
    log("Capturing final status before disconnect")
    write_json(
        "mining_status_03_final_before_disconnect.json",
        redact_status(get_json(f"{BASE}/api/mining/status", headers=headers)),
    )
    write_json(
        "pools_status.json",
        redact_status(get_json(f"{BASE}/api/mining/pools", headers=headers)),
    )

    # 8. Disconnect and prove post-disconnect state.
    log("Disconnecting mining session")
    try:
        disconnect_response = post_json(f"{BASE}/api/mining/disconnect", headers=headers)
        write_json("pool_disconnect_response.json", redact_status(disconnect_response.json()))
    except requests.HTTPError as exc:
        write_json(
            "pool_disconnect_response.json",
            {"error": str(exc), "timestamp": utc_now()},
        )
        raise

    write_json(
        "mining_status_04_post_disconnect.json",
        redact_status(get_json(f"{BASE}/api/mining/status", headers=headers)),
    )
    log("DONE — command-room evidence capture complete")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        log("Interrupted by operator")
        raise SystemExit(130)
