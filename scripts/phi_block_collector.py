#!/usr/bin/env python3
"""Collect public Bitcoin block metadata from a Blockstream-compatible API."""

from __future__ import annotations

import argparse
import csv
import json
import time
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, List, Optional

DEFAULT_API = "https://blockstream.info/api"


@dataclass(frozen=True)
class BlockRecord:
    height: int
    block_hash: str
    timestamp: int
    tx_count: int
    size: int
    weight: int
    nonce: int
    bits: int
    difficulty: float
    merkle_root: str
    previous_block_hash: str


def _get_text(url: str, timeout: int = 20) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "HYBA-Phi-Collector/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read().decode("utf-8").strip()


def _get_json(url: str, timeout: int = 20) -> Any:
    return json.loads(_get_text(url, timeout=timeout))


def api_base(value: str) -> str:
    return value.rstrip("/")


def tip_height(api: str) -> int:
    return int(_get_text(f"{api_base(api)}/blocks/tip/height"))


def block_at_height(api: str, height: int) -> BlockRecord:
    base = api_base(api)
    block_hash = _get_text(f"{base}/block-height/{height}")
    data = _get_json(f"{base}/block/{block_hash}")
    return BlockRecord(
        height=int(data.get("height", height)),
        block_hash=str(data.get("id", block_hash)),
        timestamp=int(data.get("timestamp", 0)),
        tx_count=int(data.get("tx_count", 0)),
        size=int(data.get("size", 0)),
        weight=int(data.get("weight", 0)),
        nonce=int(data.get("nonce", 0)),
        bits=int(data.get("bits", 0)),
        difficulty=float(data.get("difficulty", 0.0)),
        merkle_root=str(data.get("merkle_root", "")),
        previous_block_hash=str(data.get("previousblockhash", "")),
    )


def collect(
    api: str, count: int = 200, start_height: Optional[int] = None, delay: float = 0.1
) -> List[BlockRecord]:
    if count < 1:
        raise ValueError("count must be at least 1")
    start = tip_height(api) if start_height is None else int(start_height)
    rows: List[BlockRecord] = []
    for height in range(start, start - count, -1):
        if height < 0:
            break
        rows.append(block_at_height(api, height))
        if delay > 0:
            time.sleep(delay)
    return rows


def write_csv(path: Path, rows: List[BlockRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(rows[0]).keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default=DEFAULT_API)
    parser.add_argument("--blocks", type=int, default=200)
    parser.add_argument("--start-height", type=int, default=None)
    parser.add_argument("--delay", type=float, default=0.1)
    parser.add_argument("--out", default="artifacts/phi_blocks/blocks.csv")
    args = parser.parse_args()
    rows = collect(args.api, args.blocks, args.start_height, args.delay)
    write_csv(Path(args.out), rows)
    print(
        json.dumps(
            {
                "rows": len(rows),
                "out": args.out,
                "first_height": rows[0].height,
                "last_height": rows[-1].height,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
