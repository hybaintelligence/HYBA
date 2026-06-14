#!/usr/bin/env python3
"""Run the full public-block Phi structured evidence pipeline."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from phi_block_analyser import features, read_csv, summary, write_features
from phi_block_collector import collect, write_csv


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default="https://blockstream.info/api")
    parser.add_argument("--blocks", type=int, default=200)
    parser.add_argument("--start-height", type=int, default=None)
    parser.add_argument("--delay", type=float, default=0.1)
    parser.add_argument("--out", default="artifacts/phi_blocks")
    parser.add_argument("--needle-quantile", type=float, default=0.10)
    parser.add_argument("--ks", default="5,10,20,40")
    parser.add_argument("--trials", type=int, default=2000)
    args = parser.parse_args()

    out = Path(args.out)
    blocks_csv = out / "blocks.csv"
    features_csv = out / "features.csv"
    summary_json = out / "summary.json"
    metadata_json = out / "metadata.json"

    records = collect(args.api, args.blocks, args.start_height, args.delay)
    write_csv(blocks_csv, records)
    feats = features(read_csv(blocks_csv), args.needle_quantile)
    write_features(features_csv, feats)
    ks = [int(x.strip()) for x in args.ks.split(",") if x.strip()]
    payload = summary(feats, ks, args.trials)
    summary_json.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    metadata_json.write_text(
        json.dumps(
            {
                "api": args.api,
                "blocks": args.blocks,
                "start_height": args.start_height,
                "needle_quantile": args.needle_quantile,
                "created_at_unix": int(time.time()),
                "method": "public block metadata collection plus Phi-structured enrichment analysis",
                "scope": "public-chain empirical evidence only",
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
