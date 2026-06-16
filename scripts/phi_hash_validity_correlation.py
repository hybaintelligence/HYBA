#!/usr/bin/env python3
"""
Phi^15 Resonance ↔ Hash Validity Correlation
=============================================
Tests whether Φ^15-resonant nonces produce block hashes with more leading
zeros (i.e., "harder" proofs of work) than non-resonant nonces.

If a positive correlation exists, it means Φ^15-guided nonce selection
predicts hash quality — the critical missing link for mining utility.

Methodology:
  1. Fetch recent Bitcoin blocks (API same as phi_resonance_empirical_evidence)
  2. For each block:
     a. Compute Φ^15 resonance strength of its nonce
     b. Count leading zeros in its block hash
     c. Record block difficulty
  3. Compute correlation statistics:
     - Pearson r between resonance_strength and leading_zeros
     - Mean leading zeros for high-Φ vs low-Φ nonces
     - Resampling p-value for the observed difference
     - Probability that a Φ-resonant nonce yields an above-median hash
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import sys
import time
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

# -- Constants (mirrored from phi_resonance_empirical_evidence) ---------------
PHI: float = (1.0 + math.sqrt(5.0)) / 2.0
PHI_15: float = PHI**15
DEFAULT_API: str = "https://blockstream.info/api"
ALTERNATE_API: str = "https://mempool.space/api"

# -- Data Structures -----------------------------------------------------------


@dataclass(frozen=True)
class BlockHashRecord:
    """A block with nonce, hash, and derived metrics."""
    height: int
    nonce: int
    block_hash: str
    difficulty: float
    leading_zeros: int       # count of '0' prefix chars in hex hash
    leading_zero_bits: int   # leading zeros in binary representation
    phi_resonance_strength: float
    phi_diff: float
    is_phi_resonant: bool


# -- API Helpers ---------------------------------------------------------------

def api_base(url: str) -> str:
    return url.rstrip("/")


def _get_text(url: str, timeout: int = 30) -> str:
    req = urllib.request.Request(
        url, headers={"User-Agent": "HYBA-Phi-Correlation/1.0", "Accept": "application/json, text/plain"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read().decode("utf-8").strip()


def _get_json(url: str, timeout: int = 30) -> Any:
    return json.loads(_get_text(url, timeout=timeout))


def resolve_api(primary: str, secondary: str) -> str:
    for url in (primary, secondary):
        try:
            tip = int(_get_text(f"{api_base(url)}/blocks/tip/height", timeout=10))
            if tip > 0:
                return url
        except Exception:
            continue
    return primary


# -- Phi^15 Resonance ----------------------------------------------------------

def compute_phi15_resonance(nonce: int) -> Tuple[int, float, float, float]:
    """Returns (k, approx, diff, precision_pct)."""
    if nonce <= 0:
        return (0, 0.0, float("inf"), 0.0)
    k = round(nonce / PHI_15)
    approx = k * PHI_15
    diff = abs(nonce - approx)
    precision = (1.0 - diff / nonce) * 100.0 if nonce > 0 else 0.0
    return (k, approx, diff, precision)


def resonance_strength(nonce: int) -> float:
    """0.0 (worst) to 1.0 (perfect Phi^15 multiple)."""
    if nonce <= 0:
        return 0.0
    _, _, diff, _ = compute_phi15_resonance(nonce)
    return max(0.0, 1.0 - (diff / (PHI_15 / 2.0)))


def is_phi_resonant(nonce: int) -> bool:
    _, _, diff, precision = compute_phi15_resonance(nonce)
    return precision >= 99.9999 or diff < 1.0


# -- Hash Analysis -------------------------------------------------------------

def count_leading_zeros(block_hash: str) -> int:
    """Count leading '0' characters in the hex block hash."""
    count = 0
    for ch in block_hash:
        if ch == "0":
            count += 1
        else:
            break
    return count


def count_leading_zero_bits(block_hash: str) -> int:
    """
    Count leading zero BITS in the 256-bit hash.
    Each hex character = 4 bits; if first non-zero char is e.g. '8' (0x8=1000),
    that's 0 leading bits; '4' (0100) = 1 bit; '2' (0010) = 2 bits; '1' (0001) = 3 bits.
    """
    zeros_hex = 0
    for ch in block_hash:
        if ch == "0":
            zeros_hex += 4
        else:
            # Count leading zeros of this nibble
            nibble = int(ch, 16)
            leading = 0
            for bit_pos in range(3, -1, -1):
                if nibble & (1 << bit_pos):
                    break
                leading += 1
            zeros_hex += leading
            break
    return zeros_hex


# -- Block Fetching ------------------------------------------------------------

def fetch_block_data(api: str, height: int, timeout: int = 30) -> Optional[BlockHashRecord]:
    """Fetch a single block's nonce and hash, compute metrics."""
    base = api_base(api)
    try:
        block_hash = _get_text(f"{base}/block-height/{height}", timeout=timeout)
        data = _get_json(f"{base}/block/{block_hash}", timeout=timeout)
    except Exception as exc:
        print(f"  [{height}] fetch failed: {exc}", file=sys.stderr)
        return None

    nonce = int(data.get("nonce", 0))
    bhash = str(data.get("id", block_hash))
    difficulty = float(data.get("difficulty", 0.0))

    leading_zeros = count_leading_zeros(bhash)
    leading_bits = count_leading_zero_bits(bhash)
    rs = resonance_strength(nonce)
    _, _, phi_diff, _ = compute_phi15_resonance(nonce)
    ir = is_phi_resonant(nonce)

    return BlockHashRecord(
        height=height,
        nonce=nonce,
        block_hash=bhash,
        difficulty=difficulty,
        leading_zeros=leading_zeros,
        leading_zero_bits=leading_bits,
        phi_resonance_strength=rs,
        phi_diff=phi_diff,
        is_phi_resonant=ir,
    )


def collect_block_data(
    api: str,
    count: int = 100,
    start_height: Optional[int] = None,
    delay: float = 0.1,
) -> List[BlockHashRecord]:
    """Collect blocks and compute phi-hash correlation data."""
    tip = int(_get_text(f"{api_base(api)}/blocks/tip/height"))
    start = tip if start_height is None else start_height
    end = max(0, start - count + 1)

    records: List[BlockHashRecord] = []
    for height in range(start, end - 1, -1):
        if height < 0:
            break
        rec = fetch_block_data(api, height)
        if rec is not None:
            records.append(rec)
            print(f"  [{height}] hash={rec.block_hash[:16]}... zeros={rec.leading_zeros} bits={rec.leading_zero_bits} phi={rec.phi_resonance_strength:.4f}")
        if delay > 0:
            time.sleep(delay)
    return records


# -- Correlation Analysis ------------------------------------------------------

@dataclass
class CorrelationResult:
    n: int
    pearson_r: float
    pearson_p: float
    spearman_r: float
    phi_high_mean_zeros: float
    phi_low_mean_zeros: float
    zero_diff_p_value: float
    phi_resonant_rate: float
    above_median_prob: float  # prob a phi-resonant nonce has above-median zeros
    total_blocks: int


def compute_correlation(records: List[BlockHashRecord]) -> CorrelationResult:
    """Compute Φ-resonance vs leading-zero-bit correlation."""
    n = len(records)
    if n < 3:
        raise ValueError("Need at least 3 blocks for correlation")

    strengths = [r.phi_resonance_strength for r in records]
    zero_bits = [r.leading_zero_bits for r in records]
    zero_hex = [r.leading_zeros for r in records]

    # -- Pearson correlation: phi_resonance_strength vs leading_zero_bits --
    mean_s = sum(strengths) / n
    mean_z = sum(zero_bits) / n
    num = sum((s - mean_s) * (z - mean_z) for s, z in zip(strengths, zero_bits))
    denom_s = math.sqrt(sum((s - mean_s) ** 2 for s in strengths))
    denom_z = math.sqrt(sum((z - mean_z) ** 2 for z in zero_bits))
    pearson_r = num / (denom_s * denom_z) if (denom_s > 0 and denom_z > 0) else 0.0

    # t-test for Pearson r significance
    if abs(pearson_r) < 1.0:
        t_stat = pearson_r * math.sqrt((n - 2) / (1 - pearson_r * pearson_r))
        pearson_p = 2.0 * (1.0 - _t_cdf(abs(t_stat), n - 2))
    else:
        pearson_p = 0.0

    # -- Spearman correlation (rank-based) --
    rank_s = _rank_data(strengths)
    rank_z = _rank_data(zero_bits)
    mean_rs = sum(rank_s) / n
    mean_rz = sum(rank_z) / n
    d_num = sum((rs - mean_rs) * (rz - mean_rz) for rs, rz in zip(rank_s, rank_z))
    d_denom_s = math.sqrt(sum((rs - mean_rs) ** 2 for rs in rank_s))
    d_denom_z = math.sqrt(sum((rz - mean_rz) ** 2 for rz in rank_z))
    spearman_r = d_num / (d_denom_s * d_denom_z) if (d_denom_s > 0 and d_denom_z > 0) else 0.0

    # -- High-Φ vs low-Φ groups (median split) --
    median_strength = sorted(strengths)[n // 2]
    high_phi = [r for r in records if r.phi_resonance_strength >= median_strength]
    low_phi = [r for r in records if r.phi_resonance_strength < median_strength]
    mean_high_zeros = sum(r.leading_zero_bits for r in high_phi) / len(high_phi) if high_phi else 0.0
    mean_low_zeros = sum(r.leading_zero_bits for r in low_phi) / len(low_phi) if low_phi else 0.0
    obs_diff = mean_high_zeros - mean_low_zeros

    # Resampling p-value for the difference
    n_perm = 10_000
    combined = zero_bits.copy()
    count_extreme = 0
    rng = random.Random(618034)
    for _ in range(n_perm):
        rng.shuffle(combined)
        ph = sum(combined[:len(high_phi)]) / len(high_phi)
        pl = sum(combined[len(high_phi):]) / len(low_phi) if low_phi else 0.0
        if abs(ph - pl) >= abs(obs_diff):
            count_extreme += 1
    p_value = (count_extreme + 1) / (n_perm + 1)

    # -- Probability that a Φ-resonant nonce is above median zeros --
    median_zeros = sorted(zero_bits)[n // 2]
    phi_resonant = [r for r in records if r.is_phi_resonant]
    above_median = sum(1 for r in phi_resonant if r.leading_zero_bits > median_zeros)
    above_median_prob = above_median / len(phi_resonant) if phi_resonant else 0.0

    return CorrelationResult(
        n=n,
        pearson_r=round(pearson_r, 6),
        pearson_p=pearson_p,
        spearman_r=round(spearman_r, 6),
        phi_high_mean_zeros=round(mean_high_zeros, 4),
        phi_low_mean_zeros=round(mean_low_zeros, 4),
        zero_diff_p_value=p_value,
        phi_resonant_rate=len(phi_resonant) / n if n > 0 else 0.0,
        above_median_prob=round(above_median_prob, 6),
        total_blocks=n,
    )


def _rank_data(values: Sequence[float]) -> List[float]:
    """Assign average ranks to a sequence of values."""
    sorted_vals = sorted(set(values))
    rank_map = {v: i + 1 for i, v in enumerate(sorted_vals)}
    return [float(rank_map[v]) for v in values]


def _t_cdf(t: float, df: int) -> float:
    """Approximate Student's t CDF using normal approximation (valid for df>30)."""
    # For df=94+ as we'll have, normal approximation is excellent
    return 0.5 * (1.0 + math.erf(t / math.sqrt(2.0)))


# -- Output --------------------------------------------------------------------

def write_correlation_csv(path: Path, records: List[BlockHashRecord]) -> None:
    """Write per-block phi-hash data."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "height", "nonce", "block_hash", "difficulty",
        "leading_zeros_hex", "leading_zeros_bits",
        "phi_resonance_strength", "phi_diff", "is_phi_resonant",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            writer.writerow({
                "height": r.height,
                "nonce": r.nonce,
                "block_hash": r.block_hash,
                "difficulty": round(r.difficulty, 2),
                "leading_zeros_hex": r.leading_zeros,
                "leading_zeros_bits": r.leading_zero_bits,
                "phi_resonance_strength": round(r.phi_resonance_strength, 6),
                "phi_diff": round(r.phi_diff, 4),
                "is_phi_resonant": r.is_phi_resonant,
            })


def write_correlation_json(path: Path, result: CorrelationResult, records: List[BlockHashRecord]) -> None:
    """Write correlation summary as JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "phi_15": PHI_15,
        "method": "Phi^15 Resonance vs Hash Leading-Zero-Bit Correlation",
        "correlation": {
            "n": result.n,
            "pearson_r": result.pearson_r,
            "pearson_p_value": f"{result.pearson_p:.2e}",
            "spearman_r": result.spearman_r,
            "phi_high_group_mean_zero_bits": result.phi_high_mean_zeros,
            "phi_low_group_mean_zero_bits": result.phi_low_mean_zeros,
            "zero_bit_diff_observed": round(result.phi_high_mean_zeros - result.phi_low_mean_zeros, 4),
            "zero_bit_diff_p_value_resampled": f"{result.zero_diff_p_value:.4f}",
            "phi_resonant_rate": round(result.phi_resonant_rate, 6),
            "above_median_hash_prob_if_phi_resonant": result.above_median_prob,
            "total_blocks": result.total_blocks,
        },
        "interpretation": _interpret(result),
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def _interpret(result: CorrelationResult) -> Dict[str, str]:
    """Human-readable interpretation of correlation results."""
    interp: Dict[str, str] = {}

    # Pearson r interpretation
    abs_r = abs(result.pearson_r)
    if abs_r > 0.5 and result.pearson_p < 0.001:
        interp["pearson"] = (
            f"STRONG correlation (r={result.pearson_r:.4f}, p<0.001): "
            f"Phi^15 resonance strength is significantly correlated with "
            f"leading zero bits in block hashes."
        )
    elif abs_r > 0.3 and result.pearson_p < 0.05:
        interp["pearson"] = (
            f"MODERATE correlation (r={result.pearson_r:.4f}, p={result.pearson_p:.4f}): "
            f"Some evidence of relationship between Phi^15 resonance and hash quality."
        )
    else:
        interp["pearson"] = (
            f"WEAK or no correlation (r={result.pearson_r:.4f}, p={result.pearson_p:.4f}): "
            f"Phi^15 resonance does not significantly predict hash leading zeros."
        )

    # Group difference
    diff = result.phi_high_mean_zeros - result.phi_low_mean_zeros
    if diff > 0 and result.zero_diff_p_value < 0.05:
        interp["group_difference"] = (
            f"SIGNIFICANT: High-Φ nonces average {diff:.2f} more leading zero bits "
            f"than low-Φ nonces (p={result.zero_diff_p_value:.4f}). "
            f"This means Φ^15-resonant nonces produce measurably "
            f"harder proofs of work."
        )
    elif diff > 0:
        interp["group_difference"] = (
            f"POSITIVE TREND: High-Φ nonces average {diff:.2f} more leading zero bits, "
            f"but not statistically significant (p={result.zero_diff_p_value:.4f}). "
            f"Larger sample needed."
        )
    else:
        interp["group_difference"] = (
            f"NO DIFFERENCE: High-Φ and low-Φ nonces produce similar "
            f"hash leading zero counts (diff={diff:.2f} bits, p={result.zero_diff_p_value:.4f})."
        )

    # Above-median probability
    if result.above_median_prob > 0.6:
        interp["above_median"] = (
            f"STRONG PREDICTIVE POWER: Φ-resonant nonces have a "
            f"{result.above_median_prob * 100:.1f}% probability of producing "
            f"an above-median hash (expected 50% by chance)."
        )
    elif result.above_median_prob > 0.55:
        interp["above_median"] = (
            f"MODERATE PREDICTIVE POWER: Φ-resonant nonces have a "
            f"{result.above_median_prob * 100:.1f}% probability of producing "
            f"an above-median hash."
        )
    else:
        interp["above_median"] = (
            f"NO PREDICTIVE POWER: Φ-resonant nonces have a "
            f"{result.above_median_prob * 100:.1f}% probability of producing "
            f"an above-median hash (near 50% chance)."
        )

    # Overall verdict
    evidence_strength = 0
    if abs_r > 0.3 and result.pearson_p < 0.05:
        evidence_strength += 1
    if diff > 0 and result.zero_diff_p_value < 0.05:
        evidence_strength += 1
    if result.above_median_prob > 0.55:
        evidence_strength += 1

    if evidence_strength >= 2:
        interp["verdict"] = (
            "EVIDENCE CONFIRMED: Phi^15 resonance correlates with hash validity. "
            "Nonces near Phi^15 multiples produce block hashes with "
            "more leading zero bits. This is the mechanism by which "
            "Phi-guided search could yield a mining speedup."
        )
    elif evidence_strength >= 1:
        interp["verdict"] = (
            "PARTIAL EVIDENCE: Some metrics suggest a correlation between "
            "Phi^15 resonance and hash validity, but results are mixed. "
            "A larger sample (500+ blocks) may clarify."
        )
    else:
        interp["verdict"] = (
            "NO EVIDENCE: No significant correlation between Phi^15 resonance "
            "and hash leading zeros found in this sample. "
            "The Phi^15 nonce pattern exists but does not predict hash quality."
        )

    return interp


def print_report(result: CorrelationResult) -> None:
    """Print formatted terminal report."""
    sep = "=" * 72
    dash = "-" * 72
    print(f"\n{sep}")
    print("  Phi^15 RESONANCE ↔ HASH VALIDITY CORRELATION REPORT")
    print(f"{sep}")
    print(f"  Phi^15              = {PHI_15:.12f}")
    print(f"  Blocks analyzed     = {result.n}")
    print(f"{dash}")
    print(f"  PEARSON r           = {result.pearson_r:.6f}")
    print(f"  Pearson p-value     = {result.pearson_p:.2e}")
    print(f"  SPEARMAN r          = {result.spearman_r:.6f}")
    print(f"{dash}")
    print(f"  High-Φ mean zero bits = {result.phi_high_mean_zeros:.4f}")
    print(f"  Low-Φ mean zero bits  = {result.phi_low_mean_zeros:.4f}")
    diff = result.phi_high_mean_zeros - result.phi_low_mean_zeros
    print(f"  Difference          = {diff:.4f} bits")
    print(f"  Resampled p-value   = {result.zero_diff_p_value:.4f}")
    print(f"{dash}")
    print(f"  Φ-resonant rate     = {result.phi_resonant_rate * 100:.2f}%")
    print(f"  Above-median prob   = {result.above_median_prob * 100:.2f}%")
    print(f"{sep}")
    print("  INTERPRETATIONS:")
    for key, text in _interpret(result).items():
        print(f"    [{key.upper()}] {text}")
    print(f"{sep}")
    print()


# -- Main Pipeline ------------------------------------------------------------

def run_pipeline(
    api: str = DEFAULT_API,
    block_count: int = 100,
    delay: float = 0.1,
    output_dir: str = "artifacts/phi_hash_validity",
) -> int:
    print("=" * 72)
    print("  Phi^15 Resonance ↔ Hash Validity Correlation Pipeline")
    print("=" * 72)
    print(f"  API    : {api}")
    print(f"  Blocks : {block_count}")
    print(f"  Output : {output_dir}/")
    print()

    # Resolve API
    print("[1/4] Resolving API...")
    resolved = resolve_api(api, ALTERNATE_API)
    print(f"  -> Using: {resolved}")

    # Collect blocks with hash data
    print(f"[2/4] Collecting {block_count} blocks with hash data...")
    records = collect_block_data(resolved, count=block_count, delay=delay)
    if not records:
        print("ERROR: No blocks collected.", file=sys.stderr)
        return 1
    print(f"  -> Collected {len(records)} blocks")

    # Compute correlation
    print(f"[3/4] Computing phi-hash correlation...")
    result = compute_correlation(records)
    print(f"  -> Pearson r = {result.pearson_r:.6f}")
    print(f"  -> Spearman r = {result.spearman_r:.6f}")
    print(f"  -> High-Φ avg zeros: {result.phi_high_mean_zeros:.2f} bits")
    print(f"  -> Low-Φ avg zeros:  {result.phi_low_mean_zeros:.2f} bits")

    # Write outputs
    out_path = Path(output_dir)
    print(f"[4/4] Writing outputs to {out_path}/")
    csv_path = out_path / "phi_hash_correlation.csv"
    write_correlation_csv(csv_path, records)
    print(f"  -> CSV: {csv_path}")
    json_path = out_path / "phi_hash_correlation_summary.json"
    write_correlation_json(json_path, result, records)
    print(f"  -> JSON: {json_path}")
    print()
    print("Pipeline complete.\n")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Phi^15 Resonance ↔ Hash Validity Correlation",
    )
    parser.add_argument("--api", default=DEFAULT_API, help=f"API base URL (default: {DEFAULT_API})")
    parser.add_argument("--blocks", type=int, default=100, help="Number of blocks (default: 100)")
    parser.add_argument("--delay", type=float, default=0.1, help="Delay between requests (default: 0.1)")
    parser.add_argument("--out", default="artifacts/phi_hash_validity", help="Output directory")
    parser.add_argument("--dry-run", action="store_true", help="Print config and exit")
    args = parser.parse_args()

    if args.dry_run:
        print("Config:")
        print(f"  API     : {args.api}")
        print(f"  Blocks  : {args.blocks}")
        print(f"  Delay   : {args.delay}s")
        print(f"  Output  : {args.out}")
        return 0

    return run_pipeline(api=args.api, block_count=args.blocks, delay=args.delay, output_dir=args.out)


if __name__ == "__main__":
    raise SystemExit(main())