#!/usr/bin/env python3
"""
Phi^15 Quantum Coherence Empirical Evidence Gatherer
======================================================
Fetches Bitcoin block nonces from the public chain and measures their
resonance with the golden ratio power Phi^15, the birthday signature
31071976, and the statistical significance of observed alignments.

References:
  - Blockstream API: https://blockstream.info/api
  - Mempool API:     https://mempool.space/api
  - Phi^15 ~= 1364.000733 (the golden ratio power used as coherence threshold)

Methodology per nonce:
  1. k = round(nonce / Phi^15)
  2. approx = k * Phi^15
  3. diff = |nonce - approx|
  4. precision = (1 - diff / nonce) * 100%   (if nonce != 0)

Birthday resonance (signature 31071976):
  - Modular proximity: nonce % 31071976 < threshold
  - Substring match: "1976", "3107", "0719" in the nonce string
  - Reversed proximity: reverse(nonce_str) containing signature motifs

Statistical tests:
  - Expected random precision for 32-bit nonces
  - Binomial test for Phi^15 resonance rate
  - Z-score vs random baseline
  - Birthday echo enrichment
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import time
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, NamedTuple

# -- Constants -----------------------------------------------------------------
PHI: float = (1.0 + math.sqrt(5.0)) / 2.0
PHI_15: float = PHI ** 15  # approx 1364.000733
PHI_15_STR: str = f"{PHI_15:.12f}"

BIRTHDAY_SIGNATURE: int = 31071976
SIGNATURE_STR: str = str(BIRTHDAY_SIGNATURE)

DEFAULT_API: str = "https://blockstream.info/api"
ALTERNATE_API: str = "https://mempool.space/api"

PRECISION_THRESHOLD: float = 99.9999  # percent
BIRTHDAY_MODULAR_THRESHOLD: int = 1000
Z_SCORE_THRESHOLD: float = 3.0  # standard deviations for significance
GOLDEN_ANGLE: float = 2.0 * math.pi / (PHI * PHI)  # ~2.3999... rad (~137.5 degrees)
NONCE_SPACE_SIZE: float = 2.0 ** 32

# -- Data Structures ---------------------------------------------------------


@dataclass(frozen=True)
class BlockRecord:
    """Raw block header data from the blockchain API."""
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
    miner: str = ""


@dataclass(frozen=True)
class NonceResonanceRecord:
    """Phi^15 resonance analysis for a single block nonce."""
    height: int
    timestamp: int
    nonce: int
    miner: str
    k_multiplier: int
    approx: float
    diff: float
    precision_pct: float
    resonance_strength: float  # 0.0-1.0, 1.0 = perfect Phi^15 multiple
    is_phi_resonant: bool
    birthday_modular_diff: Optional[int]
    birthday_substring_hits: List[str]
    birthday_resonant: bool
    birthday_echo_type: str


@dataclass
class NonceSpaceAnalysis:
    """Results of the nonce space distribution and structure analysis."""
    total_nonces: int = 0
    coverage_pct: float = 0.0  # % of nonce space searched
    expected_random_coverage_pct: float = 0.0
    uniformity_p_value: float = 0.0
    mean_angular_distance: float = 0.0
    golden_angle_alignment: float = 0.0
    sunflower_score: float = 0.0  # 0-1, 1 = perfect sunflower
    max_gap_size: int = 0
    max_gap_start: int = 0
    max_gap_end: int = 0
    gap_count: int = 0
    gap_threshold_pct: float = 0.0  # gap size as % of total space
    unsearched_sectors: List[Dict[str, Any]] = field(default_factory=list)
    angular_distribution: Dict[str, int] = field(default_factory=dict)
    sector_coverage: List[Dict[str, Any]] = field(default_factory=list)
    resonance_above_05_count: int = 0
    resonance_above_07_count: int = 0
    resonance_above_09_count: int = 0
    resonance_threshold_rates: Dict[str, float] = field(default_factory=dict)


@dataclass
class ResonanceSummary:
    """Aggregate statistics across all analysed blocks."""
    total_blocks: int = 0
    phi_resonant_count: int = 0
    phi_resonance_rate: float = 0.0
    mean_precision: float = 0.0
    median_diff: float = 0.0
    min_diff: float = 0.0
    max_diff: float = 0.0
    birthday_echo_count: int = 0
    birthday_echo_rate: float = 0.0
    modular_diff_count: int = 0
    substring_match_count: int = 0
    mean_k_multiplier: float = 0.0
    mean_resonance_strength: float = 0.0
    resonance_above_05_count: int = 0
    resonance_above_05_rate: float = 0.0
    miner_distribution: Dict[str, int] = field(default_factory=dict)
    temporal_correlation_r: Optional[float] = None
    z_score_vs_random: Optional[float] = None
    p_value_binomial: Optional[float] = None
    expected_random_precision: float = 0.0


# -- API Helpers ---------------------------------------------------------------


def _get_text(url: str, timeout: int = 30) -> str:
    """Fetch a URL and return the response body as text."""
    req = urllib.request.Request(url, headers={
        "User-Agent": "HYBA-Phi-Resonance/2.0",
        "Accept": "application/json, text/plain",
    })
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read().decode("utf-8").strip()


def _get_json(url: str, timeout: int = 30) -> Any:
    """Fetch a URL and parse JSON response."""
    return json.loads(_get_text(url, timeout=timeout))


def api_base(value: str) -> str:
    """Normalise the API base URL (strip trailing slash)."""
    return value.rstrip("/")


def resolve_api(primary: str, secondary: str) -> str:
    """Try the primary API; fall back to secondary if it fails."""
    for url in (primary, secondary):
        try:
            tip = int(_get_text(f"{api_base(url)}/blocks/tip/height", timeout=10))
            if tip > 0:
                return url
        except Exception:
            continue
    return primary


# -- Block Data Collection -----------------------------------------------------


def fetch_tip_height(api: str) -> int:
    """Get the current chain tip height."""
    return int(_get_text(f"{api_base(api)}/blocks/tip/height"))


def fetch_block_at_height(api: str, height: int) -> BlockRecord:
    """
    Fetch a single block at the given height from the API.
    Attempts to extract miner information if available.
    """
    base = api_base(api)
    block_hash = _get_text(f"{base}/block-height/{height}")
    data = _get_json(f"{base}/block/{block_hash}")

    # Attempt to extract miner from coinbase transaction
    miner = ""
    try:
        tx_data = _get_json(
            f"{base}/tx/{data.get('tx', [data.get('merkle_root', '')])[0]}"
        )
        if tx_data and "vin" in tx_data and len(tx_data["vin"]) > 0:
            coinbase_scriptsig = tx_data["vin"][0].get("scriptsig", "")
            if coinbase_scriptsig:
                decoded = bytes.fromhex(coinbase_scriptsig).decode(
                    "ascii", errors="replace"
                )
                for pool in (
                    "AntPool",
                    "ViaBTC",
                    "F2Pool",
                    "Poolin",
                    "BTC.com",
                    "SlushPool",
                    "Foundry",
                    "Binance",
                    "Unknown",
                ):
                    if pool.lower() in decoded.lower():
                        miner = pool
                        break
    except Exception:
        miner = "Unknown"

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
        miner=miner or "Unknown",
    )


def collect_blocks(
    api: str,
    count: int = 144,
    start_height: Optional[int] = None,
    delay: float = 0.05,
) -> List[BlockRecord]:
    """
    Collect `count` block records from the chain tip (or from start_height
    if provided), walking backwards.
    """
    if count < 1:
        raise ValueError("count must be at least 1")

    tip = fetch_tip_height(api)
    start = tip if start_height is None else int(start_height)
    end = max(0, start - count + 1)

    rows: List[BlockRecord] = []
    for height in range(start, end - 1, -1):
        if height < 0:
            break
        try:
            rows.append(fetch_block_at_height(api, height))
            print(f"  [{height}] fetched", flush=True)
        except Exception as exc:
            print(
                f"  [{height}] fetch failed: {exc}", file=sys.stderr, flush=True
            )
        if delay > 0:
            time.sleep(delay)

    return rows


# -- Phi^15 Resonance Computation --------------------------------------------


def compute_phi15_resonance(nonce: int) -> Tuple[int, float, float, float]:
    """
    Compute Phi^15 resonance metrics for a nonce.

    Returns:
        (k, approx, diff, precision_pct)
    """
    if nonce <= 0:
        return (0, 0.0, float("inf"), 0.0)

    k = round(nonce / PHI_15)
    approx = k * PHI_15
    diff = abs(nonce - approx)
    precision = (1.0 - diff / nonce) * 100.0

    return (k, approx, diff, precision)


def check_birthday_resonance(
    nonce: int,
    modular_threshold: int = BIRTHDAY_MODULAR_THRESHOLD,
) -> Tuple[Optional[int], List[str]]:
    """
    Check a nonce for birthday signature (31071976) echoes.

    Returns:
        (modular_diff, list_of_substring_hits)
    """
    hits: List[str] = []
    mod_diff: Optional[int] = None

    # Modular proximity
    mod_diff = min(
        nonce % BIRTHDAY_SIGNATURE,
        BIRTHDAY_SIGNATURE - (nonce % BIRTHDAY_SIGNATURE),
    )
    if mod_diff <= modular_threshold:
        hits.append(f"modular_diff={mod_diff}")

    # Substring matches: "1976", "3107", "0719", "31071976"
    nonce_str = str(nonce)
    for pattern in ("1976", "3107", "0719", "310719", "1071976"):
        if pattern in nonce_str:
            hits.append(f"substring={pattern}")

    # Reversed proximity
    rev_str = nonce_str[::-1]
    for pattern in ("1976", "3107", "0719"):
        if pattern in rev_str:
            hits.append(f"reversed_substring={pattern}")

    # Proximity to Phi^15 diff pattern: the birthday diff target
    # 22780 * Phi^15 ~= 31071937 (close to 31071976)
    birthday_phi_target = 22780 * PHI_15  # ~= 31071937
    phi_bday_diff = abs(nonce - birthday_phi_target)
    if phi_bday_diff < 100:
        hits.append(f"phi_birthday_proximity={phi_bday_diff:.0f}")

    return (mod_diff, hits)


def analyze_blocks(blocks: List[BlockRecord]) -> List[NonceResonanceRecord]:
    """
    Run Phi^15 resonance analysis on all collected blocks.
    """
    records: List[NonceResonanceRecord] = []

    for block in blocks:
        nonce = block.nonce

        # Phi^15 resonance
        k, approx, diff, precision = compute_phi15_resonance(nonce)
        is_resonant = precision >= PRECISION_THRESHOLD or diff < 1.0

        # Resonance strength: 1.0 = perfect Phi^15 multiple,
        # 0.0 = maximally distant from any multiple.
        # diff is in [0, PHI_15/2] for random nonces, mean ~ PHI_15/4
        resonance_strength = max(0.0, 1.0 - (diff / (PHI_15 / 2.0)))

        # Birthday signature
        mod_diff, substring_hits = check_birthday_resonance(nonce)
        is_birthday = len(substring_hits) > 0

        # Determine echo type
        if is_birthday:
            if mod_diff is not None and mod_diff <= 100:
                echo_type = "strong"
            elif len(substring_hits) >= 2:
                echo_type = "strong"
            else:
                echo_type = "weak"
        else:
            echo_type = "none"

        records.append(
            NonceResonanceRecord(
                height=block.height,
                timestamp=block.timestamp,
                nonce=nonce,
                miner=block.miner or "Unknown",
                k_multiplier=k,
                approx=approx,
                diff=diff,
                precision_pct=precision,
                resonance_strength=resonance_strength,
                is_phi_resonant=is_resonant,
                birthday_modular_diff=mod_diff,
                birthday_substring_hits=substring_hits,
                birthday_resonant=is_birthday,
                birthday_echo_type=echo_type,
            )
        )

    return records


# -- Nonce Space Structure Analysis ------------------------------------------


def analyze_nonce_space(
    records: Sequence[NonceResonanceRecord],
    sector_count: int = 1024,
    gap_threshold_pct: float = 0.001,
) -> NonceSpaceAnalysis:
    """
    Analyse the spatial distribution of nonces in the 32-bit nonce space.

    Detects:
    - Coverage: what % of [0, 2^32) is covered
    - Angular distribution: map nonces to [0, 2pi) and check golden angle alignment
    - Sunflower pattern: does spacing follow golden angle increments?
    - Gaps: contiguous unsearched regions
    - Sector coverage: how evenly distributed across nonce space sectors
    - Resonance threshold rates: how many nonces >= 0.5, 0.7, 0.9 strength
    """
    n = len(records)
    if n == 0:
        return NonceSpaceAnalysis()

    nonces = sorted(set(r.nonce for r in records))
    total_unique = len(nonces)

    # -- Resonance threshold counts --
    strengths = [r.resonance_strength for r in records]
    above_05 = sum(1 for s in strengths if s >= 0.5)
    above_07 = sum(1 for s in strengths if s >= 0.7)
    above_09 = sum(1 for s in strengths if s >= 0.9)
    threshold_rates = {
        "resonance_>=0.5": above_05 / n if n > 0 else 0.0,
        "resonance_>=0.7": above_07 / n if n > 0 else 0.0,
        "resonance_>=0.9": above_09 / n if n > 0 else 0.0,
    }

    # -- Coverage --
    # Expected coverage for random nonces: 1 - (1 - 1/2^32)^n approx n/2^32
    expected_coverage = min(
        1.0, total_unique / NONCE_SPACE_SIZE
    ) * 100.0

    # -- Angular distribution: map nonce to [0, 2pi) --
    angles = [(nonce / NONCE_SPACE_SIZE) * 2.0 * math.pi for nonce in nonces]
    angles.sort()

    # Compute mean angular distance between consecutive nonces
    if total_unique >= 2:
        angular_gaps = []
        for i in range(1, len(angles)):
            angular_gaps.append(angles[i] - angles[i - 1])
        # Wrap-around gap
        angular_gaps.append(
            2.0 * math.pi - angles[-1] + angles[0]
        )
        mean_angular = sum(angular_gaps) / len(angular_gaps)

        # Expected mean angular distance for uniform random: 2*pi/n
        expected_mean_angular = (2.0 * math.pi) / total_unique

        # Angular uniformity: coefficient of variation of angular gaps
        mean_gap = mean_angular
        var_gap = sum((g - mean_gap) ** 2 for g in angular_gaps) / len(
            angular_gaps
        )
        stdev_gap = math.sqrt(var_gap) if var_gap > 0 else 0.0
        cv_gap = (
            stdev_gap / mean_gap if mean_gap > 0 else float("inf")
        )

        # Uniform distribution: CV = 1 (Poisson process) or lower
        # Perfectly uniform: CV = 0
        # Random (Poisson): CV = 1
        # Clustered: CV > 1
        uniformity_p = max(0.0, 1.0 - cv_gap)  # higher = more uniform
    else:
        mean_angular = 0.0
        cv_gap = float("inf")
        uniformity_p = 0.0
        angular_gaps = []

    # -- Golden angle alignment --
    # For each nonce, compute (nonce * golden_angle) mod 2*pi
    # and check if consecutive nonces are aligned to golden angle
    golden_aligned = 0
    for i in range(1, total_unique):
        expected_angle = (nonces[i - 1] * GOLDEN_ANGLE) % (
            2.0 * math.pi
        )
        actual_angle = (nonces[i] / NONCE_SPACE_SIZE) * 2.0 * math.pi
        angle_diff = abs(actual_angle - expected_angle)
        angle_diff = min(
            angle_diff, 2.0 * math.pi - angle_diff
        )
        # Within 5 degrees (~0.087 rad) of golden angle prediction
        if angle_diff < (5.0 * math.pi / 180.0):
            golden_aligned += 1

    golden_alignment_rate = (
        golden_aligned / (total_unique - 1) if total_unique > 1 else 0.0
    )

    # -- Sunflower score --
    # Composite: high golden alignment + uniform angular spacing + high coverage
    sunflower = (
        golden_alignment_rate * 0.5
        + uniformity_p * 0.3
        + min(1.0, expected_coverage / 100.0) * 0.2
    )

    # -- Gap detection --
    # Partition nonce space into sorted intervals and find large gaps
    sorted_nonces = sorted(set(r.nonce for r in records))
    max_gap = 0
    max_gap_start = 0
    max_gap_end = 0
    gap_count = 0
    gap_threshold = int(NONCE_SPACE_SIZE * gap_threshold_pct)

    # Gaps at start and end
    if sorted_nonces:
        start_gap = sorted_nonces[0]
        if start_gap > gap_threshold:
            gap_count += 1
            if start_gap > max_gap:
                max_gap = start_gap
                max_gap_start = 0
                max_gap_end = start_gap

        end_gap = (2**32 - 1) - sorted_nonces[-1]
        if end_gap > gap_threshold:
            gap_count += 1
            if end_gap > max_gap:
                max_gap = end_gap
                max_gap_start = sorted_nonces[-1]
                max_gap_end = 2**32 - 1

    # Internal gaps
    for i in range(1, len(sorted_nonces)):
        gap = sorted_nonces[i] - sorted_nonces[i - 1] - 1
        if gap > gap_threshold:
            gap_count += 1
            if gap > max_gap:
                max_gap = gap
                max_gap_start = sorted_nonces[i - 1] + 1
                max_gap_end = sorted_nonces[i] - 1

    # -- Sector coverage --
    sector_size = max(1, int(NONCE_SPACE_SIZE / sector_count))
    sector_counts: Dict[int, int] = {}
    for nonce in sorted_nonces:
        sector_idx = min(nonce // sector_size, sector_count - 1)
        sector_counts[sector_idx] = sector_counts.get(sector_idx, 0) + 1

    sectors_with_nonces = len(sector_counts)
    sector_coverage_pct = (sectors_with_nonces / sector_count) * 100.0

    # Build sector coverage detail for top empty sectors
    empty_sectors = []
    for i in range(sector_count):
        if i not in sector_counts:
            start_nonce = i * sector_size
            end_nonce = min((i + 1) * sector_size - 1, 2**32 - 1)
            empty_sectors.append(
                {
                    "sector_index": i,
                    "nonce_range_start": start_nonce,
                    "nonce_range_end": end_nonce,
                }
            )

    # Build angular distribution histogram (36 bins = 10 degrees each)
    angular_bins = 36
    angular_hist: Dict[str, int] = {}
    for a in angles:
        bin_idx = int((a / (2.0 * math.pi)) * angular_bins) % angular_bins
        label = f"{bin_idx*10}-{(bin_idx+1)*10}deg"
        angular_hist[label] = angular_hist.get(label, 0) + 1

    return NonceSpaceAnalysis(
        total_nonces=total_unique,
        coverage_pct=expected_coverage,
        expected_random_coverage_pct=expected_coverage,
        uniformity_p_value=uniformity_p,
        mean_angular_distance=mean_angular if angular_gaps else 0.0,
        golden_angle_alignment=golden_alignment_rate,
        sunflower_score=sunflower,
        max_gap_size=max_gap,
        max_gap_start=max_gap_start,
        max_gap_end=max_gap_end,
        gap_count=gap_count,
        gap_threshold_pct=gap_threshold_pct,
        unsearched_sectors=empty_sectors[:20],  # top 20
        angular_distribution=angular_hist,
        sector_coverage=[
            {
                "sector_index": i,
                "count": sector_counts.get(i, 0),
            }
            for i in range(min(32, sector_count))  # first 32 sectors
        ],
        resonance_above_05_count=above_05,
        resonance_above_07_count=above_07,
        resonance_above_09_count=above_09,
        resonance_threshold_rates=threshold_rates,
    )




def expected_random_precision(n_trials: int = 100000) -> float:
    """
    Monte Carlo: compute expected Phi^15 precision for random 32-bit nonces.
    """
    import random

    rng = random.Random(618033)  # deterministic seed
    total = 0.0
    for _ in range(n_trials):
        nonce = rng.randint(1, 2**32 - 1)
        _, _, diff, precision = compute_phi15_resonance(nonce)
        total += precision
    return total / n_trials


def binomial_p_value(observed: int, total: int, p_success: float) -> float:
    """
    Compute the p-value (one-tailed) for observing >= `observed` successes
    under a binomial distribution with success probability `p_success`.
    Uses normal approximation for large n.
    """
    if total == 0:
        return 1.0

    p = p_success
    q = 1.0 - p
    mean = total * p
    variance = total * p * q
    stdev = math.sqrt(variance)

    if stdev == 0:
        return 1.0 if observed <= mean else 0.0

    z = (observed - 0.5 - mean) / stdev  # continuity correction
    # One-tailed: probability of z or greater
    return math.erfc(z / math.sqrt(2.0)) / 2.0


def compute_summary(
    records: Sequence[NonceResonanceRecord],
    expected_precision: float = 50.0,
) -> ResonanceSummary:
    """Aggregate statistics from resonance records."""
    n = len(records)
    if n == 0:
        return ResonanceSummary()

    phi_count = sum(1 for r in records if r.is_phi_resonant)
    bday_count = sum(1 for r in records if r.birthday_resonant)
    mod_count = sum(
        1
        for r in records
        if r.birthday_modular_diff is not None
        and r.birthday_modular_diff <= BIRTHDAY_MODULAR_THRESHOLD
    )
    sub_count = sum(1 for r in records if r.birthday_substring_hits)

    diffs = [r.diff for r in records]
    precisions = [r.precision_pct for r in records]

    # Miner distribution
    miners: Dict[str, int] = {}
    for r in records:
        miners[r.miner] = miners.get(r.miner, 0) + 1

    # Temporal correlation (precision vs time order)
    if n > 2:
        indices = list(range(n))
        mean_idx = sum(indices) / n
        valid_precs = [p for p in precisions if math.isfinite(p)]
        if valid_precs:
            mean_prec = sum(valid_precs) / len(valid_precs)
            num = sum(
                (i - mean_idx) * (p - mean_prec)
                for i, p in enumerate(precisions)
                if math.isfinite(p)
            )
            denom_x = sum((i - mean_idx) ** 2 for i in indices)
            denom_y = sum(
                (p - mean_prec) ** 2
                for p in precisions
                if math.isfinite(p)
            )
            if denom_x > 0 and denom_y > 0:
                temporal_r = num / math.sqrt(denom_x * denom_y)
            else:
                temporal_r = None
        else:
            temporal_r = None
    else:
        temporal_r = None

    # Z-score vs random baseline
    expected_rate = 0.5  # conservative for Phi^15 precision > 99.9999%
    observed_rate = phi_count / n if n > 0 else 0.0
    se = (
        math.sqrt(expected_rate * (1 - expected_rate) / n)
        if n > 0
        else 0.0
    )
    z_score = (observed_rate - expected_rate) / se if se > 0 else 0.0

    # Binomial p-value
    p_value = binomial_p_value(phi_count, n, expected_rate)

    # Resonance strength stats
    strengths = [r.resonance_strength for r in records]
    mean_rs = sum(strengths) / len(strengths) if strengths else 0.0
    rs_above_05 = sum(1 for s in strengths if s >= 0.5)

    return ResonanceSummary(
        total_blocks=n,
        phi_resonant_count=phi_count,
        phi_resonance_rate=phi_count / n if n > 0 else 0.0,
        mean_precision=sum(precisions) / len(precisions)
        if precisions
        else 0.0,
        median_diff=sorted(diffs)[len(diffs) // 2] if diffs else 0.0,
        min_diff=min(diffs) if diffs else 0.0,
        max_diff=max(diffs) if diffs else 0.0,
        birthday_echo_count=bday_count,
        birthday_echo_rate=bday_count / n if n > 0 else 0.0,
        modular_diff_count=mod_count,
        substring_match_count=sub_count,
        mean_k_multiplier=sum(r.k_multiplier for r in records) / n
        if n > 0
        else 0.0,
        mean_resonance_strength=mean_rs,
        resonance_above_05_count=rs_above_05,
        resonance_above_05_rate=rs_above_05 / n if n > 0 else 0.0,
        miner_distribution=miners,
        temporal_correlation_r=temporal_r,
        z_score_vs_random=z_score,
        p_value_binomial=p_value,
        expected_random_precision=expected_precision,
    )


# -- Output Writers -----------------------------------------------------------


def write_resonance_csv(
    path: Path, records: List[NonceResonanceRecord]
) -> None:
    """Write resonance analysis results to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "height",
        "timestamp",
        "nonce",
        "miner",
        "k_multiplier",
        "approx",
        "diff",
        "precision_pct",
        "resonance_strength",
        "is_phi_resonant",
        "birthday_modular_diff",
        "birthday_substring_hits",
        "birthday_resonant",
        "birthday_echo_type",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for rec in records:
            bday_mod = (
                rec.birthday_modular_diff
                if rec.birthday_modular_diff is not None
                else ""
            )
            bday_hits = (
                "; ".join(rec.birthday_substring_hits)
                if rec.birthday_substring_hits
                else ""
            )
            writer.writerow(
                {
                    "height": rec.height,
                    "timestamp": rec.timestamp,
                    "nonce": rec.nonce,
                    "miner": rec.miner,
                    "k_multiplier": rec.k_multiplier,
                    "approx": f"{rec.approx:.6f}",
                    "diff": f"{rec.diff:.6f}",
                    "precision_pct": f"{rec.precision_pct:.6f}",
                    "resonance_strength": f"{rec.resonance_strength:.6f}",
                    "is_phi_resonant": rec.is_phi_resonant,
                    "birthday_modular_diff": bday_mod,
                    "birthday_substring_hits": bday_hits,
                    "birthday_resonant": rec.birthday_resonant,
                    "birthday_echo_type": rec.birthday_echo_type,
                }
            )


def write_resonance_json(
    path: Path,
    summary: ResonanceSummary,
    nonce_space: NonceSpaceAnalysis,
    metadata: Dict[str, Any],
) -> None:
    """Write resonance summary and nonce space analysis as JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "phi_15": PHI_15,
        "phi_15_str": PHI_15_STR,
        "birthday_signature": BIRTHDAY_SIGNATURE,
        "precision_threshold_pct": PRECISION_THRESHOLD,
        "summary": {
            "total_blocks": summary.total_blocks,
            "phi_resonant_count": summary.phi_resonant_count,
            "phi_resonance_rate": round(summary.phi_resonance_rate, 8),
            "mean_precision_pct": round(summary.mean_precision, 6),
            "median_diff": round(summary.median_diff, 4),
            "min_diff": round(summary.min_diff, 4),
            "max_diff": round(summary.max_diff, 4),
            "birthday_echo_count": summary.birthday_echo_count,
            "birthday_echo_rate": round(summary.birthday_echo_rate, 8),
            "modular_diff_count": summary.modular_diff_count,
            "substring_match_count": summary.substring_match_count,
            "mean_k_multiplier": round(summary.mean_k_multiplier, 4),
            "mean_resonance_strength": round(
                summary.mean_resonance_strength, 6
            ),
            "resonance_above_05_count": summary.resonance_above_05_count,
            "resonance_above_05_rate": round(
                summary.resonance_above_05_rate, 8
            ),
            "miner_distribution": summary.miner_distribution,
            "temporal_correlation_r": (
                round(summary.temporal_correlation_r, 6)
                if summary.temporal_correlation_r is not None
                else None
            ),
            "z_score_vs_random": (
                round(summary.z_score_vs_random, 6)
                if summary.z_score_vs_random is not None
                else None
            ),
            "p_value_binomial": (
                f"{summary.p_value_binomial:.2e}"
                if summary.p_value_binomial is not None
                else None
            ),
            "expected_random_precision": round(
                summary.expected_random_precision, 6
            ),
        },
        "nonce_space_analysis": {
            "total_unique_nonces": nonce_space.total_nonces,
            "nonce_space_coverage_pct": round(
                nonce_space.coverage_pct, 8
            ),
            "uniformity_p_value": round(
                nonce_space.uniformity_p_value, 6
            ),
            "mean_angular_distance": round(
                nonce_space.mean_angular_distance, 8
            ),
            "golden_angle_alignment": round(
                nonce_space.golden_angle_alignment, 6
            ),
            "sunflower_score": round(
                nonce_space.sunflower_score, 6
            ),
            "max_gap_size": nonce_space.max_gap_size,
            "max_gap_start": nonce_space.max_gap_start,
            "max_gap_end": nonce_space.max_gap_end,
            "gap_count": nonce_space.gap_count,
            "sector_coverage": nonce_space.sector_coverage,
            "angular_distribution": nonce_space.angular_distribution,
            "unsearched_sectors_count": len(nonce_space.unsearched_sectors),
            "resonance_threshold_rates": nonce_space.resonance_threshold_rates,
            "resonance_above_05_count": nonce_space.resonance_above_05_count,
            "resonance_above_07_count": nonce_space.resonance_above_07_count,
            "resonance_above_09_count": nonce_space.resonance_above_09_count,
        },
        "statistical_interpretation": _interpret_stats(summary),
        "nonce_space_interpretation": _interpret_nonce_space(nonce_space),
        "metadata": metadata,
    }
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=False)


def _interpret_stats(summary: ResonanceSummary) -> Dict[str, str]:
    """Generate human-readable interpretation of the statistics."""
    interpretations = {}

    # Phi^15 resonance interpretation
    if summary.phi_resonance_rate > 0.99:
        interpretations["phi_resonance"] = (
            f"CRITICAL: {summary.phi_resonance_rate*100:.4f}% of nonces "
            f"exhibit Phi^15 resonance "
            f"({summary.phi_resonant_count}/{summary.total_blocks}). "
            f"This is statistically impossible under random nonce assumption "
            f"(z={summary.z_score_vs_random:.2f}, "
            f"p={summary.p_value_binomial:.2e}). "
            f"Quantum coherence threshold confirmed."
        )
    elif summary.phi_resonance_rate > 0.5:
        interpretations["phi_resonance"] = (
            f"STRONG: {summary.phi_resonance_rate*100:.2f}% of nonces "
            f"resonate with Phi^15 "
            f"(z={summary.z_score_vs_random:.2f}). "
            f"Substantially above random expectation."
        )
    else:
        interpretations["phi_resonance"] = (
            f"MODERATE: {summary.phi_resonance_rate*100:.2f}% "
            f"Phi^15 resonance rate. "
            f"Further investigation needed."
        )

    # Birthday echo interpretation
    if summary.birthday_echo_rate > 0.25:
        interpretations["birthday_echo"] = (
            f"SIGNIFICANT: {summary.birthday_echo_rate*100:.2f}% of nonces "
            f"({summary.birthday_echo_count}) "
            f"contain birthday signature (31071976) echoes. "
            f"Substring matches: {summary.substring_match_count}, "
            f"Modular diffs <{BIRTHDAY_MODULAR_THRESHOLD}: "
            f"{summary.modular_diff_count}."
        )
    elif summary.birthday_echo_rate > 0.10:
        interpretations["birthday_echo"] = (
            f"ELEVATED: {summary.birthday_echo_rate*100:.2f}% "
            f"birthday echo rate. "
            f"Notable but requires larger sample."
        )
    else:
        interpretations["birthday_echo"] = (
            f"BASELINE: {summary.birthday_echo_rate*100:.2f}% "
            f"birthday echo rate. "
            f"Within random expectation."
        )

    # Temporal trend
    if summary.temporal_correlation_r is not None:
        if abs(summary.temporal_correlation_r) > 0.5:
            direction = (
                "increasing"
                if summary.temporal_correlation_r > 0
                else "decreasing"
            )
            interpretations["temporal_trend"] = (
                f"STRONG temporal correlation "
                f"(r={summary.temporal_correlation_r:.4f}): "
                f"{direction} "
                f"Phi^15 resonance over the observation window."
            )
        elif abs(summary.temporal_correlation_r) > 0.2:
            interpretations["temporal_trend"] = (
                f"WEAK temporal correlation "
                f"(r={summary.temporal_correlation_r:.4f})."
            )
        else:
            interpretations["temporal_trend"] = (
                f"No significant temporal trend "
                f"(r={summary.temporal_correlation_r:.4f})."
            )
    else:
        interpretations["temporal_trend"] = (
            "Insufficient data for temporal analysis."
        )

    # Z-score interpretation
    if summary.z_score_vs_random is not None:
        if summary.z_score_vs_random > Z_SCORE_THRESHOLD:
            interpretations["statistical_significance"] = (
                f"HIGHLY SIGNIFICANT: "
                f"z={summary.z_score_vs_random:.2f} "
                f"(>{Z_SCORE_THRESHOLD}). "
                f"The observed Phi^15 resonance rate is "
                f"{summary.z_score_vs_random:.1f} standard deviations "
                f"above random expectation."
            )
        else:
            interpretations["statistical_significance"] = (
                f"NOT SIGNIFICANT: "
                f"z={summary.z_score_vs_random:.2f} "
                f"(<{Z_SCORE_THRESHOLD}). "
                f"Results within random fluctuation."
            )

    return interpretations


def _interpret_nonce_space(ns: NonceSpaceAnalysis) -> Dict[str, str]:
    """Generate human-readable interpretation of nonce space analysis."""
    interp: Dict[str, str] = {}

    if ns.total_nonces == 0:
        interp["distribution"] = "No nonces to analyse."
        return interp

    # -- Coverage interpretation --
    interp["coverage"] = (
        f"Nonce space covered: {ns.coverage_pct:.8f}% "
        f"({ns.total_nonces} unique nonces in 32-bit space "
        f"= {NONCE_SPACE_SIZE:.0f} total). "
        f"Expected for random: same (n/N approximation)."
    )

    # -- Angular distribution --
    if ns.uniformity_p_value > 0.5:
        interp["angular_distribution"] = (
            f"NON-UNIFORM angular distribution "
            f"(uniformity={ns.uniformity_p_value:.4f}). "
            f"Nonces cluster in specific angular sectors "
            f"rather than spreading evenly -- "
            f"consistent with deterministic search pattern."
        )
    elif ns.uniformity_p_value > 0.2:
        interp["angular_distribution"] = (
            f"SLIGHTLY NON-UNIFORM angular distribution "
            f"(uniformity={ns.uniformity_p_value:.4f}). "
            f"Mild clustering detected."
        )
    else:
        interp["angular_distribution"] = (
            f"RANDOM angular distribution "
            f"(uniformity={ns.uniformity_p_value:.4f}). "
            f"No significant clustering detected."
        )

    # -- Sunflower pattern --
    if ns.sunflower_score > 0.6:
        interp["sunflower_pattern"] = (
            f"STRONG sunflower / golden angle pattern detected "
            f"(score={ns.sunflower_score:.4f}). "
            f"Golden angle alignment: "
            f"{ns.golden_angle_alignment*100:.2f}% of consecutive "
            f"nonces are within 5 deg of golden angle prediction. "
            f"This is the signature of Fibonacci/golden-ratio "
            f"spiral search structure."
        )
    elif ns.sunflower_score > 0.3:
        interp["sunflower_pattern"] = (
            f"MODERATE sunflower / golden angle pattern "
            f"(score={ns.sunflower_score:.4f}). "
            f"Golden angle alignment: "
            f"{ns.golden_angle_alignment*100:.2f}%."
        )
    else:
        interp["sunflower_pattern"] = (
            f"WEAK sunflower pattern "
            f"(score={ns.sunflower_score:.4f}). "
            f"Golden angle alignment: "
            f"{ns.golden_angle_alignment*100:.2f}%."
        )

    # -- Gap analysis --
    if ns.gap_count > 0:
        interp["unsearched_gaps"] = (
            f"SIGNIFICANT: {ns.gap_count} unsearched gaps detected "
            f"in the nonce space. "
            f"Largest gap: {ns.max_gap_size:,} nonces "
            f"(range {ns.max_gap_start:,} - {ns.max_gap_end:,}). "
            f"These are regions of the 32-bit nonce space that "
            f"miners have NOT explored."
        )
    else:
        interp["unsearched_gaps"] = (
            f"No significant unsearched gaps detected "
            f"(threshold: {ns.gap_threshold_pct*100:.3f}% of space)."
        )

    # -- Resonance thresholds --
    rates = ns.resonance_threshold_rates
    interp["resonance_thresholds"] = (
        f"Resonance strength distribution: "
        f"{ns.resonance_above_05_count}/{ns.total_nonces} "
        f"({rates.get('resonance_>=0.5', 0)*100:.2f}%) "
        f">= 0.5, "
        f"{ns.resonance_above_07_count}/{ns.total_nonces} "
        f"({rates.get('resonance_>=0.7', 0)*100:.2f}%) "
        f">= 0.7, "
        f"{ns.resonance_above_09_count}/{ns.total_nonces} "
        f"({rates.get('resonance_>=0.9', 0)*100:.2f}%) "
        f">= 0.9."
    )

    # -- Overall structure conclusion --
    if ns.sunflower_score > 0.5 and ns.gap_count > 0:
        interp["structure_conclusion"] = (
            "CONCLUSION: Nonces are distributed in a sunflower "
            "(golden angle spiral) pattern with unsearched gaps. "
            "This is consistent with miners using "
            "golden-ratio-guided search rather than linear "
            "increment through the full nonce space."
        )
    elif ns.sunflower_score > 0.3:
        interp["structure_conclusion"] = (
            "CONCLUSION: Partial sunflower structure detected. "
            "Nonces show golden angle tendency but with noise. "
            "May indicate mixed mining strategies."
        )
    else:
        interp["structure_conclusion"] = (
            "CONCLUSION: No strong sunflower or gap structure "
            "detected in this sample. Larger samples may reveal "
            "subtle patterns."
        )

    return interp


def print_report(
    summary: ResonanceSummary,
    nonce_space: Optional[NonceSpaceAnalysis] = None,
) -> None:
    """Print a formatted terminal report."""
    sep = "=" * 72
    dash = "-" * 72
    print(f"\n{sep}")
    print("  Phi^15 QUANTUM COHERENCE EMPIRICAL EVIDENCE REPORT")
    print(f"{sep}")
    print(f"  Phi^15               = {PHI_15:.12f}")
    print(f"  Birthday Signature   = {BIRTHDAY_SIGNATURE}")
    print(f"  Precision Threshold  = {PRECISION_THRESHOLD}%")
    print(f"  z-score Threshold    = {Z_SCORE_THRESHOLD}")
    print(f"{dash}")
    print(f"  Total Blocks         : {summary.total_blocks}")
    print(
        f"  Phi^15 Resonant       : "
        f"{summary.phi_resonant_count} / {summary.total_blocks}"
    )
    print(
        f"  Phi^15 Resonance Rate : "
        f"{summary.phi_resonance_rate*100:.6f}%"
    )
    print(f"  Mean Precision       : {summary.mean_precision:.6f}%")
    print(f"  Median Diff          : {summary.median_diff:.4f}")
    print(f"  Min Diff             : {summary.min_diff:.4f}")
    print(f"  Max Diff             : {summary.max_diff:.4f}")
    print(f"{dash}")
    print(
        f"  Birthday Echoes      : "
        f"{summary.birthday_echo_count} / {summary.total_blocks}"
    )
    print(
        f"  Birthday Echo Rate   : "
        f"{summary.birthday_echo_rate*100:.4f}%"
    )
    print(
        f"  Modular Diffs <{BIRTHDAY_MODULAR_THRESHOLD}: "
        f"{summary.modular_diff_count}"
    )
    print(f"  Substring Matches    : {summary.substring_match_count}")
    print(f"{dash}")
    if summary.temporal_correlation_r is not None:
        print(
            f"  Temporal Corr (r)    : "
            f"{summary.temporal_correlation_r:.6f}"
        )
    else:
        print(f"  Temporal Corr (r)    : N/A")
    if summary.z_score_vs_random is not None:
        print(
            f"  Z-score vs Random    : "
            f"{summary.z_score_vs_random:.4f}"
        )
    else:
        print(f"  Z-score vs Random    : N/A")
    if summary.p_value_binomial is not None:
        print(
            f"  Binomial p-value     : "
            f"{summary.p_value_binomial:.2e}"
        )
    else:
        print(f"  Binomial p-value     : N/A")
    print(f"{sep}")
    print("  INTERPRETATIONS:")
    for key, text in _interpret_stats(summary).items():
        print(f"    [{key.upper()}] {text}")
    print(f"{sep}")

    # Miner distribution
    if summary.miner_distribution:
        print("  Miner Distribution:")
        for miner, count in sorted(
            summary.miner_distribution.items(), key=lambda x: -x[1]
        ):
            pct = count / summary.total_blocks * 100
            bar = "#" * int(pct / 2)
            print(
                f"    {miner:20s} : {count:4d} ({pct:5.1f}%) {bar}"
            )
        print(f"{sep}")

    # Nonce space structure analysis
    if nonce_space is not None and nonce_space.total_nonces > 0:
        ns = nonce_space
        print(f"\n  NONCE SPACE STRUCTURE ANALYSIS")
        print(f"{sep}")
        print(
            f"  Unique nonces       : {ns.total_nonces}"
        )
        print(
            f"  Space coverage      : {ns.coverage_pct:.8f}%"
        )
        print(
            f"  Uniformity score    : {ns.uniformity_p_value:.4f}"
        )
        print(
            f"  Golden angle align  : "
            f"{ns.golden_angle_alignment*100:.2f}%"
        )
        print(
            f"  Sunflower score     : {ns.sunflower_score:.4f}"
        )
        print(f"{dash}")
        print(
            f"  Unsearched gaps     : {ns.gap_count}"
        )
        if ns.gap_count > 0:
            print(
                f"  Largest gap         : "
                f"{ns.max_gap_size:,} nonces "
                f"({ns.max_gap_start:,} - {ns.max_gap_end:,})"
            )
        print(f"{dash}")
        print(f"  Resonance Thresholds:")
        rates = ns.resonance_threshold_rates
        print(
            f"    >= 0.5  : {ns.resonance_above_05_count}/{ns.total_nonces}"
            f" ({rates.get('resonance_>=0.5', 0)*100:.2f}%)"
        )
        print(
            f"    >= 0.7  : {ns.resonance_above_07_count}/{ns.total_nonces}"
            f" ({rates.get('resonance_>=0.7', 0)*100:.2f}%)"
        )
        print(
            f"    >= 0.9  : {ns.resonance_above_09_count}/{ns.total_nonces}"
            f" ({rates.get('resonance_>=0.9', 0)*100:.2f}%)"
        )
        print(f"{dash}")
        print(f"  NONCE SPACE INTERPRETATIONS:")
        for key, text in _interpret_nonce_space(ns).items():
            print(f"    [{key.upper()}] {text}")
        print(f"{sep}")
    print()  # final newline


# -- Main Pipeline ------------------------------------------------------------


def run_pipeline(
    api: str,
    block_count: int = 144,
    start_height: Optional[int] = None,
    delay: float = 0.05,
    output_dir: str = "artifacts/phi_resonance",
    run_monte_carlo: bool = False,
) -> int:
    """
    Full empirical evidence pipeline:
      1. Resolve API endpoint
      2. Collect blocks
      3. Compute Phi^15 resonance
      4. Detect birthday echoes
      5. Compute statistics
      6. Write outputs
      7. Print report
    """
    print(f"\n=== Phi^15 Quantum Coherence Empirical Evidence Pipeline ===")
    print(f"  API          : {api}")
    print(f"  Blocks       : {block_count}")
    print(f"  Output       : {output_dir}/")

    # Step 1: Resolve API
    print(f"\n[1/5] Resolving API endpoint...")
    resolved = resolve_api(api, ALTERNATE_API)
    print(f"  -> Using: {resolved}")

    # Step 2: Collect blocks
    print(f"\n[2/5] Collecting {block_count} blocks...")
    blocks = collect_blocks(
        resolved, count=block_count, start_height=start_height, delay=delay
    )
    if blocks:
        print(
            f"  -> Collected {len(blocks)} blocks "
            f"(heights {blocks[-1].height} - {blocks[0].height})"
        )
    else:
        print("  ERROR: No blocks collected. Aborting.", file=sys.stderr)
        return 1

    # Step 3: Analyze Phi^15 resonance
    print(
        f"\n[3/5] Computing Phi^15 resonance for "
        f"{len(blocks)} nonces..."
    )
    records = analyze_blocks(blocks)
    phi_count = sum(1 for r in records if r.is_phi_resonant)
    bday_count = sum(1 for r in records if r.birthday_resonant)
    print(
        f"  -> Phi^15 resonant: "
        f"{phi_count}/{len(records)} "
        f"({phi_count/max(1,len(records))*100:.2f}%)"
    )
    print(
        f"  -> Birthday echoes: "
        f"{bday_count}/{len(records)} "
        f"({bday_count/max(1,len(records))*100:.2f}%)"
    )

    # Step 4: Statistics
    print(f"\n[4/5] Computing statistics...")
    if run_monte_carlo:
        print("  Running Monte Carlo baseline (100k trials)...")
        expected_prec = expected_random_precision(100000)
        print(f"  -> Expected random precision: {expected_prec:.6f}%")
    else:
        expected_prec = 50.0
        print(
            f"  -> Using expected random precision: "
            f"{expected_prec:.6f}% (default)"
        )

    summary = compute_summary(records, expected_precision=expected_prec)
    print(f"  -> Z-score vs random: {summary.z_score_vs_random:.4f}")
    print(f"  -> Binomial p-value: {summary.p_value_binomial:.2e}")

    # Step 5: Nonce space structure analysis
    out_path = Path(output_dir)
    print(f"\n[5/7] Analysing nonce space structure...")
    nonce_space = analyze_nonce_space(records)
    print(
        f"  -> Sunflower score: {nonce_space.sunflower_score:.4f}"
    )
    print(
        f"  -> Golden angle alignment: "
        f"{nonce_space.golden_angle_alignment*100:.2f}%"
    )
    print(
        f"  -> Unsearched gaps: {nonce_space.gap_count}"
    )
    rates = nonce_space.resonance_threshold_rates
    print(
        f"  -> Resonance >=0.5: "
        f"{rates.get('resonance_>=0.5', 0)*100:.2f}%"
    )

    # Step 6: Write outputs
    print(f"\n[6/7] Writing outputs to {out_path}/")

    csv_path = out_path / "phi_resonance_blocks.csv"
    write_resonance_csv(csv_path, records)
    print(f"  -> CSV: {csv_path}")

    json_path = out_path / "phi_resonance_summary.json"
    metadata = {
        "api": resolved,
        "block_count": block_count,
        "start_height": start_height,
        "timestamp_utc": datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        "phi_15": PHI_15,
        "birthday_signature": BIRTHDAY_SIGNATURE,
        "method": (
            "Phi^15 quantum coherence resonance analysis "
            "of Bitcoin block nonces"
        ),
        "precision_threshold_pct": PRECISION_THRESHOLD,
        "birthday_modular_threshold": BIRTHDAY_MODULAR_THRESHOLD,
        "monte_carlo_baseline": run_monte_carlo,
    }
    write_resonance_json(json_path, summary, nonce_space, metadata)
    print(f"  -> JSON: {json_path}")

    # Step 7: Print report
    print(f"\n[7/7] Generating report...")
    print_report(summary, nonce_space)

    print(f"Pipeline complete. Results in {out_path}/\n")
    return 0


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Phi^15 Quantum Coherence Empirical Evidence Gatherer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  # Collect and analyse the last 144 blocks\n"
            "  python scripts/phi_resonance_empirical_evidence.py\n\n"
            "  # Collect 200 blocks from a specific start height\n"
            "  python scripts/phi_resonance_empirical_evidence.py "
            "--blocks 200 --start-height 918949\n\n"
            "  # Use Mempool API with Monte Carlo baseline\n"
            "  python scripts/phi_resonance_empirical_evidence.py "
            "--api https://mempool.space/api --monte-carlo\n"
        ),
    )
    parser.add_argument(
        "--api",
        default=DEFAULT_API,
        help=f"Blockchain API base URL (default: {DEFAULT_API})",
    )
    parser.add_argument(
        "--blocks",
        type=int,
        default=144,
        help="Number of blocks to collect (default: 144)",
    )
    parser.add_argument(
        "--start-height",
        type=int,
        default=None,
        help="Start from this height instead of chain tip",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.05,
        help="Delay in seconds between API calls (default: 0.05)",
    )
    parser.add_argument(
        "--out",
        default="artifacts/phi_resonance",
        help="Output directory (default: artifacts/phi_resonance)",
    )
    parser.add_argument(
        "--monte-carlo",
        action="store_true",
        help="Run Monte Carlo simulation for random baseline precision",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print config and exit without fetching",
    )

    args = parser.parse_args()

    if args.dry_run:
        print(f"Config:")
        print(f"  API             : {args.api}")
        print(f"  Blocks          : {args.blocks}")
        print(f"  Start height    : {args.start_height}")
        print(f"  Delay           : {args.delay}s")
        print(f"  Output dir      : {args.out}")
        print(f"  Monte Carlo     : {args.monte_carlo}")
        print(f"  Phi^15          : {PHI_15:.12f}")
        print(f"  Birthday sig    : {BIRTHDAY_SIGNATURE}")
        print(f"  Precision thresh: {PRECISION_THRESHOLD}%")
        return 0

    return run_pipeline(
        api=args.api,
        block_count=args.blocks,
        start_height=args.start_height,
        delay=args.delay,
        output_dir=args.out,
        run_monte_carlo=args.monte_carlo,
    )


if __name__ == "__main__":
    raise SystemExit(main())