#!/usr/bin/env python3
"""Analyse public block metadata for Phi-structured enrichment evidence."""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import statistics
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Sequence

PHI = (1.0 + math.sqrt(5.0)) / 2.0
INV_PHI = 1.0 / PHI


@dataclass(frozen=True)
class FeatureRecord:
    height: int
    block_hash: str
    hash_ratio: float
    pow_strength: float
    leading_zero_bits: int
    nonce_ratio: float
    fullness: float
    tx_log: float
    time_delta_norm: float
    merkle_phi_residue: float
    phi_score: float
    is_needle: bool


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def hex_ratio(hex_value: str) -> float:
    if not hex_value:
        return 1.0
    return int(hex_value, 16) / float(1 << (4 * len(hex_value)))


def leading_zero_bits(hex_value: str) -> int:
    if not hex_value:
        return 0
    value = int(hex_value, 16)
    width = 4 * len(hex_value)
    return width if value == 0 else width - value.bit_length()


def phi_residue(value: float) -> float:
    frac = value - math.floor(value)
    return min(abs(frac - INV_PHI), abs(frac - (1.0 - INV_PHI)), frac, 1.0 - frac)


def golden_distance(x: float, levels: int = 13) -> float:
    x = max(0.0, min(1.0, float(x)))
    anchors = [((i * INV_PHI) % 1.0) for i in range(1, levels + 1)] + [0.0, 1.0]
    return min(abs(x - anchor) for anchor in anchors)


def features(rows: Sequence[Dict[str, str]], needle_quantile: float = 0.10) -> List[FeatureRecord]:
    ordered = sorted(rows, key=lambda r: int(r["height"]))
    deltas: Dict[int, int] = {}
    prev_ts = None
    for row in ordered:
        h = int(row["height"])
        ts = int(row["timestamp"])
        deltas[h] = 600 if prev_ts is None else max(1, ts - prev_ts)
        prev_ts = ts
    max_tx = max(1, max(int(r["tx_count"]) for r in rows))
    ratios = [hex_ratio(r["block_hash"]) for r in rows]
    cutoff = sorted(ratios)[max(0, min(len(ratios) - 1, int(len(ratios) * needle_quantile)))]
    out: List[FeatureRecord] = []
    for row in rows:
        height = int(row["height"])
        block_hash = row["block_hash"]
        hratio = hex_ratio(block_hash)
        nonce_ratio = (int(row["nonce"]) % (2**32)) / float(2**32)
        fullness = min(1.0, int(row["weight"]) / 4_000_000.0) if int(row["weight"]) else 0.0
        tx_log = math.log1p(int(row["tx_count"])) / math.log1p(max_tx)
        time_delta_norm = min(3.0, deltas.get(height, 600) / 600.0) / 3.0
        merkle_ratio = (
            hex_ratio(row.get("merkle_root", "")[:16]) if row.get("merkle_root", "") else 1.0
        )
        component_distances = [
            golden_distance(nonce_ratio),
            golden_distance(fullness),
            golden_distance(tx_log),
            golden_distance(time_delta_norm),
            golden_distance(merkle_ratio),
        ]
        phi_score = sum(
            (INV_PHI**i) * value for i, value in enumerate(component_distances, start=1)
        )
        out.append(
            FeatureRecord(
                height=height,
                block_hash=block_hash,
                hash_ratio=hratio,
                pow_strength=-math.log10(max(hratio, 1e-80)),
                leading_zero_bits=leading_zero_bits(block_hash),
                nonce_ratio=nonce_ratio,
                fullness=fullness,
                tx_log=tx_log,
                time_delta_norm=time_delta_norm,
                merkle_phi_residue=phi_residue(merkle_ratio * PHI),
                phi_score=float(phi_score),
                is_needle=bool(hratio <= cutoff),
            )
        )
    return out


def write_features(path: Path, rows: List[FeatureRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(rows[0]).keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def enrichment(rows: Sequence[FeatureRecord], k: int) -> Dict[str, float]:
    ranked = sorted(rows, key=lambda r: (r.phi_score, -r.pow_strength))[:k]
    needles = sum(1 for r in rows if r.is_needle)
    hits = sum(1 for r in ranked if r.is_needle)
    return {
        "hits": float(hits),
        "precision": hits / max(1, k),
        "recall": hits / max(1, needles),
    }


def baseline(
    rows: Sequence[FeatureRecord], k: int, trials: int = 2000, seed: int = 618033
) -> Dict[str, float]:
    rng = random.Random(seed)
    values = []
    for _ in range(trials):
        sample = rng.sample(list(rows), min(k, len(rows)))
        values.append(sum(1 for r in sample if r.is_needle) / max(1, k))
    return {
        "precision_mean": statistics.mean(values),
        "precision_stdev": statistics.pstdev(values) if len(values) > 1 else 0.0,
    }


def summary(rows: Sequence[FeatureRecord], ks: Sequence[int], trials: int) -> Dict[str, object]:
    payload: Dict[str, object] = {
        "sample_size": len(rows),
        "needle_count": sum(1 for r in rows if r.is_needle),
        "phi": PHI,
        "ks": {},
    }
    for raw_k in ks:
        k = min(int(raw_k), len(rows))
        if k <= 0:
            continue
        phi_result = enrichment(rows, k)
        random_result = baseline(rows, k, trials=trials)
        sd = random_result["precision_stdev"]
        z_score = (
            0.0 if sd == 0 else (phi_result["precision"] - random_result["precision_mean"]) / sd
        )
        payload["ks"][str(k)] = {
            "phi_rank": phi_result,
            "random_baseline": random_result,
            "z_score": z_score,
        }
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--blocks-csv", default="artifacts/phi_blocks/blocks.csv")
    parser.add_argument("--features-csv", default="artifacts/phi_blocks/features.csv")
    parser.add_argument("--summary-json", default="artifacts/phi_blocks/summary.json")
    parser.add_argument("--needle-quantile", type=float, default=0.10)
    parser.add_argument("--ks", default="5,10,20,40")
    parser.add_argument("--trials", type=int, default=2000)
    args = parser.parse_args()
    feats = features(read_csv(Path(args.blocks_csv)), args.needle_quantile)
    write_features(Path(args.features_csv), feats)
    ks = [int(x.strip()) for x in args.ks.split(",") if x.strip()]
    payload = summary(feats, ks, args.trials)
    Path(args.summary_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.summary_json).write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
