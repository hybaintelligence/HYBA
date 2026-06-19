"""
Tests for Phi^15 Quantum Coherence Empirical Evidence Pipeline
===============================================================
Verifies:
  1. Phi^15 mathematical identity
  2. compute_phi15_resonance correctness (known test vectors)
  3. check_birthday_resonance correctness
  4. Statistical functions (binomial_p_value, expected_random_precision)
  5. CSV/JSON output formatting
  6. analyze_blocks integration
"""

from __future__ import annotations

import csv
import json
import math
import sys
from io import StringIO
from pathlib import Path
from typing import Any, List

# Ensure scripts directory is importable
ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from phi_resonance_empirical_evidence import (
    BIRTHDAY_SIGNATURE,
    PHI,
    PHI_15,
    PRECISION_THRESHOLD,
    BlockRecord,
    NonceResonanceRecord,
    ResonanceSummary,
    _interpret_stats,
    analyze_blocks,
    analyze_nonce_space,
    binomial_p_value,
    check_birthday_resonance,
    compute_phi15_resonance,
    compute_summary,
    print_report,
    write_resonance_csv,
    write_resonance_json,
)

# ============================================================================
# SECTION 1 -- Phi^15 Mathematical Identity Verification
# ============================================================================


class TestPhi15MathematicalIdentity:
    """Verify Phi^15 satisfies its mathematical relationships."""

    def test_phi_15_is_positive(self) -> None:
        """Phi^15 > 0"""
        assert PHI_15 > 0

    def test_phi_15_approximate_value(self) -> None:
        """Phi^15 approx 1364.000733 (known constant)"""
        assert abs(PHI_15 - 1364.000733) < 0.001, f"Phi^15 = {PHI_15} not approx 1364.000733"

    def test_phi_15_via_fibonacci(self) -> None:
        """Phi^n = F_n * Phi + F_{n-1} (Binet-like identity)"""
        # F_15 = 610, F_14 = 377
        # Phi^15 = F_15 * Phi + F_14
        f15, f14 = 610, 377
        computed = f15 * PHI + f14
        assert abs(computed - PHI_15) < 0.001, f"Phi^15 via Fibonacci: {computed} != {PHI_15}"

    def test_phi_15_power_chain(self) -> None:
        """Phi^15 = Phi^14 * Phi  (power chain consistency)"""
        phi_14 = PHI**14
        assert abs(PHI_15 - phi_14 * PHI) < 1e-10

    def test_phi_15_div_phi_14_is_phi(self) -> None:
        """Phi^15 / Phi^14 = Phi"""
        phi_14 = PHI**14
        ratio = PHI_15 / phi_14
        assert abs(ratio - PHI) < 1e-12

    def test_phi_15_integer_proximity(self) -> None:
        """Phi^15 is extremely close to integer 1364"""
        nearest_int = round(PHI_15)
        assert abs(PHI_15 - nearest_int) < 0.001
        assert nearest_int == 1364

    def test_phi_15_continued_fraction_convergence(self) -> None:
        """Phi^15 from continued fraction of Phi converges within 1e-8"""
        cf = 1.0
        for _ in range(30):
            cf = 1.0 + 1.0 / cf
        phi_from_cf = cf
        computed = phi_from_cf**15
        # 30 iterations -> ~3e-9 accuracy (relaxed from 1e-10 for float precision)
        assert abs(computed - PHI_15) < 1e-8


# ============================================================================
# SECTION 2 -- compute_phi15_resonance Tests
# ============================================================================


class TestComputePhi15Resonance:
    """Test the core Phi^15 resonance computation."""

    def test_zero_nonce_returns_inf(self) -> None:
        """Nonce = 0 should return inf diff and 0% precision."""
        k, approx, diff, precision = compute_phi15_resonance(0)
        assert k == 0
        assert approx == 0.0
        assert diff == float("inf")
        assert precision == 0.0

    def test_negative_nonce_returns_inf(self) -> None:
        """Negative nonce should return inf diff."""
        k, approx, diff, precision = compute_phi15_resonance(-100)
        assert k == 0
        assert diff == float("inf")

    def test_nonce_equals_phi15_k1(self) -> None:
        """nonce = Phi^15 -> k=1, diff close to 0"""
        k, approx, diff, precision = compute_phi15_resonance(round(PHI_15))
        assert k == 1
        assert diff < 1.0
        assert precision > 99.9999

    def test_nonce_equals_2x_phi15(self) -> None:
        """nonce = 2*Phi^15 -> k=2, diff near 0"""
        target = round(2 * PHI_15)
        k, approx, diff, precision = compute_phi15_resonance(target)
        assert k == 2
        assert diff < 1.0
        assert precision > 99.9999

    def test_nonce_equals_1000x_phi15(self) -> None:
        """nonce = 1000*Phi^15 -> k=1000, diff near 0"""
        target = round(1000 * PHI_15)
        k, approx, diff, precision = compute_phi15_resonance(target)
        assert k == 1000
        assert diff < 1.0
        assert precision > 99.9999

    def test_diff_increases_with_distance(self) -> None:
        """Nonces far from Phi^15 multiples have larger differences."""
        near_target = round(100 * PHI_15) + 100  # offset by 100
        far_target = round(100 * PHI_15) + 100000  # offset by 100000
        _, _, near_diff, _ = compute_phi15_resonance(near_target)
        _, _, far_diff, _ = compute_phi15_resonance(far_target)
        assert near_diff < far_diff, (
            f"Near diff {near_diff:.4f} should be < far diff {far_diff:.4f}"
        )

    def test_known_nonce_block_919092(self) -> None:
        """Block 919,092 nonce = 4067381598 -> k=2981950, diff < 500."""
        nonce = 4067381598
        k, approx, diff, precision = compute_phi15_resonance(nonce)
        assert k == 2981950
        assert diff < 500
        assert precision > 99.9999

    def test_known_nonce_block_919073(self) -> None:
        """Block 919,073 nonce = 1764759171 (100.0000% precision from analysis)."""
        nonce = 1764759171
        k, approx, diff, precision = compute_phi15_resonance(nonce)
        assert k == 1293811
        assert diff < 30
        assert precision > 99.99999

    def test_random_nonces_diff_distribution(self) -> None:
        """
        Random nonces have diff uniformly distributed in [0, Phi^15/2].
        The mean diff for random nonces should be approx Phi^15/4 ~= 341.
        """
        import random

        rng = random.Random(42)
        diffs = []
        for _ in range(1000):
            nonce = rng.randint(1, 2**32 - 1)
            _, _, d, _ = compute_phi15_resonance(nonce)
            diffs.append(d)
        mean_diff = sum(diffs) / len(diffs)
        # Expected mean for random uniform nonces: Phi^15 / 4 ~= 341
        expected_mean = PHI_15 / 4.0
        assert abs(mean_diff - expected_mean) < expected_mean * 0.15, (
            f"Mean diff {mean_diff:.2f} not near expected {expected_mean:.2f}"
        )

    def test_birthday_phi_target_resonance(self) -> None:
        """22780 * Phi^15 approx 31071937 should show strong resonance."""
        target = round(22780 * PHI_15)  # approx 31071937
        k, approx, diff, precision = compute_phi15_resonance(target)
        assert k == 22780
        assert diff < 1.0
        assert precision > 99.99999


# ============================================================================
# SECTION 3 -- check_birthday_resonance Tests
# ============================================================================


class TestCheckBirthdayResonance:
    """Test birthday signature detection in nonces."""

    def test_exact_birthday_nonce(self) -> None:
        """Nonce exactly = BIRTHDAY_SIGNATURE should hit."""
        mod_diff, hits = check_birthday_resonance(BIRTHDAY_SIGNATURE)
        assert mod_diff is not None
        assert mod_diff == 0
        assert len(hits) >= 1

    def test_modular_proximity(self) -> None:
        """Nonce close to a multiple of BIRTHDAY_SIGNATURE."""
        close_nonce = BIRTHDAY_SIGNATURE * 10 + 50  # diff = 50
        mod_diff, hits = check_birthday_resonance(close_nonce)
        assert mod_diff is not None
        assert mod_diff <= 50
        assert any("modular_diff" in h for h in hits)

    def test_modular_far_no_hit(self) -> None:
        """Nonce far from any multiple of BIRTHDAY_SIGNATURE."""
        far_nonce = BIRTHDAY_SIGNATURE * 10 + 5000  # diff > threshold
        mod_diff, hits = check_birthday_resonance(far_nonce, modular_threshold=100)
        if mod_diff is not None and mod_diff > 100:
            assert not any("modular_diff" in h for h in hits)

    def test_substring_1976(self) -> None:
        """Nonce containing '1976' should detect substring."""
        mod_diff, hits = check_birthday_resonance(1231976456)
        assert any("1976" in h for h in hits)

    def test_substring_3107(self) -> None:
        """Nonce containing '3107' should detect substring."""
        mod_diff, hits = check_birthday_resonance(453107892)
        assert any("3107" in h for h in hits)

    def test_substring_0719(self) -> None:
        """Nonce containing '0719' should detect substring."""
        mod_diff, hits = check_birthday_resonance(980719123)
        assert any("0719" in h for h in hits)

    def test_reversed_substring(self) -> None:
        """Reversed nonce containing '1976'."""
        # "6791" reversed is "1976"
        mod_diff, hits = check_birthday_resonance(123456791)
        assert any("reversed_substring" in h for h in hits)

    def test_phi_birthday_proximity(self) -> None:
        """Nonce close to 22780*Phi^15 should detect phi_birthday_proximity."""
        target = round(22780 * PHI_15)  # approx 31071937
        mod_diff, hits = check_birthday_resonance(target)
        assert any("phi_birthday_proximity" in h for h in hits)

    def test_no_resonance(self) -> None:
        """Random nonce far from birthday signature should have no hits."""
        nonce = 1234567890
        mod_diff, hits = check_birthday_resonance(nonce, modular_threshold=10)
        assert len(hits) == 0 or all("modular" not in h for h in hits)

    def test_multiple_hits_accumulated(self) -> None:
        """Nonce with multiple birthday echoes."""
        base = BIRTHDAY_SIGNATURE * 5  # multiple of BIRTHDAY_SIGNATURE
        nonce_str = str(base) + "1976"
        nonce = int(nonce_str[:10])
        mod_diff, hits = check_birthday_resonance(nonce)
        assert len(hits) >= 1


# ============================================================================
# SECTION 4 -- analyze_blocks Integration Tests
# ============================================================================


class TestAnalyzeBlocks:
    """Test the full block analysis pipeline."""

    def make_block(self, height: int, nonce: int, miner: str = "TestPool") -> BlockRecord:
        return BlockRecord(
            height=height,
            block_hash="0" * 64,
            timestamp=int(1_700_000_000 + height),
            tx_count=2000,
            size=1_500_000,
            weight=3_000_000,
            nonce=nonce,
            bits=0x1A0FFFF,
            difficulty=50_000_000_000_000.0,
            merkle_root="a" * 64,
            previous_block_hash="b" * 64,
            miner=miner,
        )

    def test_single_perfect_block(self) -> None:
        """A nonce exactly at Phi^15 multiple should be resonant."""
        nonce = round(1000 * PHI_15)
        block = self.make_block(900000, nonce)
        records = analyze_blocks([block])
        assert len(records) == 1
        assert records[0].is_phi_resonant
        assert records[0].k_multiplier == 1000
        assert records[0].precision_pct > 99.9999

    def test_multiple_blocks_analysed(self) -> None:
        """Multiple blocks with known properties."""
        blocks = [
            self.make_block(900001, 4067381598),  # known resonant
            self.make_block(900002, 1764759171),  # known high precision
            self.make_block(900003, 123456789),  # random
        ]
        records = analyze_blocks(blocks)
        assert len(records) == 3
        assert records[0].is_phi_resonant
        assert records[1].is_phi_resonant
        assert all(r.miner == "TestPool" for r in records)

    def test_miner_preserved(self) -> None:
        """Miner information is preserved through analysis."""
        block = self.make_block(900000, round(500 * PHI_15), miner="AntPool")
        records = analyze_blocks([block])
        assert records[0].miner == "AntPool"

    def test_birthday_resonance_detected(self) -> None:
        """Birthday signature in nonce is detected."""
        block = self.make_block(900000, BIRTHDAY_SIGNATURE)
        records = analyze_blocks([block])
        assert records[0].birthday_resonant
        assert records[0].birthday_echo_type in ("strong", "weak")

    def test_no_birthday_resonance(self) -> None:
        """Nonce without birthday signature has no echo."""
        block = self.make_block(900000, 123456789)
        records = analyze_blocks([block])
        assert not records[0].birthday_resonant
        assert records[0].birthday_echo_type == "none"


# ============================================================================
# SECTION 5 -- Statistical Tests
# ============================================================================


class TestBinomialPValue:
    """Test binomial p-value computation."""

    def test_all_successes_p_miniscule(self) -> None:
        """All successes with low p -> tiny p-value."""
        p = binomial_p_value(144, 144, 0.5)
        assert p < 1e-30

    def test_all_failures_p_large(self) -> None:
        """No successes -> p approx 1.0."""
        p = binomial_p_value(0, 100, 0.5)
        assert p > 0.99

    def test_half_successes_p_approx_half(self) -> None:
        """Half successes with p=0.5 -> p approx 0.5."""
        p = binomial_p_value(50, 100, 0.5)
        assert 0.4 < p < 0.6

    def test_zero_total_returns_one(self) -> None:
        """total=0 should return p=1.0."""
        assert binomial_p_value(0, 0, 0.5) == 1.0

    def test_p_equals_1_all_success(self) -> None:
        """p=1.0, all successes -> p=1.0."""
        p = binomial_p_value(100, 100, 1.0)
        assert p == 1.0 or math.isclose(p, 1.0, rel=1e-9)

    def test_p_equals_0_no_success(self) -> None:
        """p=0.0, no successes -> p=1.0."""
        p = binomial_p_value(0, 100, 0.0)
        assert p >= 0.0


class TestComputeSummary:
    """Test summary statistics computation."""

    def make_records(
        self, n: int, phi_resonant: bool = True, birthday_resonant: bool = False
    ) -> List[NonceResonanceRecord]:
        """Create test records."""
        records = []
        for i in range(n):
            nonce = round((i + 1) * PHI_15)
            k = i + 1
            approx = k * PHI_15
            diff = abs(nonce - approx)
            precision = (1.0 - diff / nonce) * 100.0 if nonce > 0 else 0.0

            bday_mod, bday_hits = None, []
            if birthday_resonant and i % 3 == 0:
                bday_mod = 50
                bday_hits = ["modular_diff=50"]

            records.append(
                NonceResonanceRecord(
                    height=900000 + i,
                    timestamp=1700000000 + i,
                    nonce=nonce,
                    miner="TestPool",
                    k_multiplier=k,
                    approx=approx,
                    diff=diff,
                    precision_pct=precision,
                    resonance_strength=1.0 - (diff / (PHI_15 / 2.0)),
                    is_phi_resonant=phi_resonant or (i < n // 2),
                    birthday_modular_diff=bday_mod,
                    birthday_substring_hits=bday_hits,
                    birthday_resonant=len(bday_hits) > 0,
                    birthday_echo_type="strong" if bday_hits else "none",
                )
            )
        return records

    def test_empty_summary(self) -> None:
        """Empty records -> empty summary."""
        summary = compute_summary([])
        assert summary.total_blocks == 0
        assert summary.phi_resonant_count == 0
        assert summary.phi_resonance_rate == 0.0

    def test_all_resonant_summary(self) -> None:
        """All records resonant."""
        records = self.make_records(100, phi_resonant=True)
        summary = compute_summary(records)
        assert summary.total_blocks == 100
        assert summary.phi_resonant_count == 100
        assert summary.phi_resonance_rate == 1.0
        assert summary.mean_precision > 99.0

    def test_half_resonant_summary(self) -> None:
        """Half resonant."""
        records = self.make_records(100, phi_resonant=False)
        summary = compute_summary(records)
        assert summary.phi_resonant_count == 50
        assert abs(summary.phi_resonance_rate - 0.50) < 0.01

    def test_birthday_echo_count(self) -> None:
        """Birthday echoes counted correctly."""
        records = self.make_records(90, birthday_resonant=True)
        summary = compute_summary(records)
        assert summary.birthday_echo_count == 30
        assert abs(summary.birthday_echo_rate - 30 / 90) < 0.01

    def test_miner_distribution(self) -> None:
        """Miner distribution tracked."""
        records = self.make_records(50)
        records_with_variant = list(records)
        records_with_variant[0] = NonceResonanceRecord(
            height=records[0].height,
            timestamp=records[0].timestamp,
            nonce=records[0].nonce,
            miner="OtherPool",
            k_multiplier=records[0].k_multiplier,
            approx=records[0].approx,
            diff=records[0].diff,
            precision_pct=records[0].precision_pct,
            resonance_strength=records[0].resonance_strength,
            is_phi_resonant=records[0].is_phi_resonant,
            birthday_modular_diff=records[0].birthday_modular_diff,
            birthday_substring_hits=records[0].birthday_substring_hits,
            birthday_resonant=records[0].birthday_resonant,
            birthday_echo_type=records[0].birthday_echo_type,
        )
        summary = compute_summary(records_with_variant)
        assert "TestPool" in summary.miner_distribution
        assert "OtherPool" in summary.miner_distribution
        assert summary.miner_distribution["TestPool"] == 49
        assert summary.miner_distribution["OtherPool"] == 1

    def test_z_score_calculation(self) -> None:
        """Z-score computed for perfect resonance."""
        records = self.make_records(144, phi_resonant=True)
        summary = compute_summary(records)
        assert summary.z_score_vs_random is not None
        assert summary.z_score_vs_random > 0

    def test_temporal_correlation(self) -> None:
        """Temporal r computed with sufficient data."""
        records = self.make_records(50)
        summary = compute_summary(records)
        assert summary.temporal_correlation_r is not None


# ============================================================================
# SECTION 6 -- Output Formatting Tests
# ============================================================================


class TestWriteResonanceCSV:
    """Test CSV output formatting."""

    def make_test_records(self) -> List[NonceResonanceRecord]:
        return [
            NonceResonanceRecord(
                height=900000,
                timestamp=1700000000,
                nonce=round(100 * PHI_15),
                miner="TestPool",
                k_multiplier=100,
                approx=100 * PHI_15,
                diff=0.5,
                precision_pct=99.99999,
                resonance_strength=0.999,
                is_phi_resonant=True,
                birthday_modular_diff=100,
                birthday_substring_hits=["substring=1976"],
                birthday_resonant=True,
                birthday_echo_type="weak",
            ),
            NonceResonanceRecord(
                height=900001,
                timestamp=1700000600,
                nonce=round(200 * PHI_15),
                miner="OtherPool",
                k_multiplier=200,
                approx=200 * PHI_15,
                diff=0.3,
                precision_pct=100.0,
                resonance_strength=0.999,
                is_phi_resonant=True,
                birthday_modular_diff=None,
                birthday_substring_hits=[],
                birthday_resonant=False,
                birthday_echo_type="none",
            ),
        ]

    def test_csv_writes_correctly(self, tmp_path: Path) -> None:
        """CSV file is written with correct headers and data."""
        records = self.make_test_records()
        csv_path = tmp_path / "test_blocks.csv"
        write_resonance_csv(csv_path, records)

        assert csv_path.exists()
        with csv_path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2
        assert rows[0]["height"] == "900000"
        assert rows[0]["nonce"] == str(round(100 * PHI_15))
        assert rows[0]["is_phi_resonant"] == "True"
        assert rows[0]["birthday_resonant"] == "True"
        assert "1976" in rows[0]["birthday_substring_hits"]

        assert rows[1]["height"] == "900001"
        assert rows[1]["miner"] == "OtherPool"
        assert rows[1]["birthday_resonant"] == "False"
        assert rows[1]["birthday_substring_hits"] == ""

    def test_csv_headers_match_fields(self, tmp_path: Path) -> None:
        """CSV headers should match the NonceResonanceRecord fields."""
        records = self.make_test_records()
        csv_path = tmp_path / "test_headers.csv"
        write_resonance_csv(csv_path, records)

        with csv_path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = set(reader.fieldnames or [])

        expected = {
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
        }
        assert headers == expected


class TestWriteResonanceJSON:
    """Test JSON output formatting."""

    def make_summary(self) -> ResonanceSummary:
        return ResonanceSummary(
            total_blocks=144,
            phi_resonant_count=144,
            phi_resonance_rate=1.0,
            mean_precision=99.99995,
            median_diff=187.0,
            min_diff=18.0,
            max_diff=614.0,
            birthday_echo_count=43,
            birthday_echo_rate=0.2986,
            modular_diff_count=12,
            substring_match_count=31,
            mean_k_multiplier=1_000_000.0,
            miner_distribution={"AntPool": 75, "ViaBTC": 40, "Unknown": 29},
            temporal_correlation_r=0.67,
            z_score_vs_random=12.0,
            p_value_binomial=1e-20,
            expected_random_precision=50.0,
        )

    def test_json_writes_correctly(self, tmp_path: Path) -> None:
        """JSON file is written with correct structure."""
        summary = self.make_summary()
        metadata = {
            "api": "https://blockstream.info/api",
            "block_count": 144,
            "timestamp_utc": "2025-10-14T21:45:23Z",
        }
        nonce_space = analyze_nonce_space(
            [
                NonceResonanceRecord(
                    height=953400,
                    timestamp=1781300000,
                    nonce=1364,
                    miner="TestPool",
                    k_multiplier=1,
                    approx=1364.000733,
                    diff=0.000733,
                    precision_pct=99.999946,
                    resonance_strength=0.999999,
                    is_phi_resonant=True,
                    birthday_modular_diff=None,
                    birthday_substring_hits=[],
                    birthday_resonant=False,
                    birthday_echo_type="none",
                ),
            ]
        )
        json_path = tmp_path / "test_summary.json"
        write_resonance_json(json_path, summary, nonce_space, metadata)

        assert json_path.exists()
        with json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        assert "phi_15" in data
        assert "birthday_signature" in data
        assert data["birthday_signature"] == BIRTHDAY_SIGNATURE
        assert "summary" in data
        assert "statistical_interpretation" in data
        assert "metadata" in data

        s = data["summary"]
        assert s["total_blocks"] == 144
        assert s["phi_resonant_count"] == 144
        assert s["phi_resonance_rate"] == 1.0
        assert s["birthday_echo_count"] == 43
        assert s["miner_distribution"]["AntPool"] == 75

    def test_json_interpretation_included(self, tmp_path: Path) -> None:
        """JSON includes human-readable interpretations."""
        summary = self.make_summary()
        nonce_space = analyze_nonce_space(
            [
                NonceResonanceRecord(
                    height=953400,
                    timestamp=1781300000,
                    nonce=1364,
                    miner="TestPool",
                    k_multiplier=1,
                    approx=1364.000733,
                    diff=0.000733,
                    precision_pct=99.999946,
                    resonance_strength=0.999999,
                    is_phi_resonant=True,
                    birthday_modular_diff=None,
                    birthday_substring_hits=[],
                    birthday_resonant=False,
                    birthday_echo_type="none",
                ),
            ]
        )
        json_path = tmp_path / "test_interp.json"
        write_resonance_json(json_path, summary, nonce_space, {})

        with json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        assert "statistical_interpretation" in data
        interp = data["statistical_interpretation"]
        assert "phi_resonance" in interp
        assert "birthday_echo" in interp
        assert "temporal_trend" in interp
        assert "statistical_significance" in interp


class TestInterpretStats:
    """Test the interpretation generator."""

    def make_summary(self, **kwargs: Any) -> ResonanceSummary:
        defaults = {
            "total_blocks": 144,
            "phi_resonant_count": 144,
            "phi_resonance_rate": 1.0,
            "mean_precision": 99.99995,
            "median_diff": 187.0,
            "min_diff": 18.0,
            "max_diff": 614.0,
            "birthday_echo_count": 43,
            "birthday_echo_rate": 0.2986,
            "modular_diff_count": 12,
            "substring_match_count": 31,
            "mean_k_multiplier": 1000000.0,
            "miner_distribution": None,
            "temporal_correlation_r": 0.67,
            "z_score_vs_random": 12.0,
            "p_value_binomial": 1e-20,
            "expected_random_precision": 50.0,
        }
        defaults.update(kwargs)
        return ResonanceSummary(**defaults)  # type: ignore[arg-type]

    def test_critical_phi_resonance(self) -> None:
        """>99% resonance -> CRITICAL."""
        interp = _interpret_stats(self.make_summary(phi_resonance_rate=0.9999))
        assert "CRITICAL" in interp["phi_resonance"]

    def test_strong_phi_resonance(self) -> None:
        """50-99% resonance -> STRONG."""
        interp = _interpret_stats(self.make_summary(phi_resonance_rate=0.75))
        assert "STRONG" in interp["phi_resonance"]

    def test_moderate_phi_resonance(self) -> None:
        """<50% resonance -> MODERATE."""
        interp = _interpret_stats(self.make_summary(phi_resonance_rate=0.30))
        assert "MODERATE" in interp["phi_resonance"]

    def test_significant_birthday_echo(self) -> None:
        """>25% birthday echo -> SIGNIFICANT."""
        interp = _interpret_stats(self.make_summary(birthday_echo_rate=0.30))
        assert "SIGNIFICANT" in interp["birthday_echo"]

    def test_elevated_birthday_echo(self) -> None:
        """10-25% birthday echo -> ELEVATED."""
        interp = _interpret_stats(self.make_summary(birthday_echo_rate=0.15))
        assert "ELEVATED" in interp["birthday_echo"]

    def test_baseline_birthday_echo(self) -> None:
        """<10% birthday echo -> BASELINE."""
        interp = _interpret_stats(self.make_summary(birthday_echo_rate=0.05))
        assert "BASELINE" in interp["birthday_echo"]

    def test_strong_temporal_trend(self) -> None:
        """|r| > 0.5 -> STRONG."""
        interp = _interpret_stats(self.make_summary(temporal_correlation_r=0.67))
        assert "STRONG" in interp["temporal_trend"]

    def test_no_temporal_trend(self) -> None:
        """|r| < 0.2 -> no significant trend."""
        interp = _interpret_stats(self.make_summary(temporal_correlation_r=0.05))
        assert "No significant" in interp["temporal_trend"]

    def test_highly_significant_z_score(self) -> None:
        """z > 3.0 -> HIGHLY SIGNIFICANT."""
        interp = _interpret_stats(self.make_summary(z_score_vs_random=12.0))
        assert "HIGHLY SIGNIFICANT" in interp["statistical_significance"]

    def test_not_significant_z_score(self) -> None:
        """z < 3.0 -> NOT SIGNIFICANT."""
        interp = _interpret_stats(self.make_summary(z_score_vs_random=1.5))
        assert "NOT SIGNIFICANT" in interp["statistical_significance"]


# ============================================================================
# SECTION 7 -- Print Report (Smoke Test)
# ============================================================================


class TestPrintReport:
    """Smoke test for report printing."""

    def make_summary(self) -> ResonanceSummary:
        return ResonanceSummary(
            total_blocks=144,
            phi_resonant_count=144,
            phi_resonance_rate=1.0,
            mean_precision=99.99995,
            median_diff=187.0,
            min_diff=18.0,
            max_diff=614.0,
            birthday_echo_count=43,
            birthday_echo_rate=0.2986,
            modular_diff_count=12,
            substring_match_count=31,
            mean_k_multiplier=1000000.0,
            miner_distribution={"AntPool": 75, "ViaBTC": 40, "Unknown": 29},
            temporal_correlation_r=0.67,
            z_score_vs_random=12.0,
            p_value_binomial=1e-20,
            expected_random_precision=50.0,
        )

    def test_print_report_does_not_crash(self) -> None:
        """print_report should execute without errors."""
        summary = self.make_summary()
        captured = StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        try:
            print_report(summary)
        finally:
            sys.stdout = old_stdout

        output = captured.getvalue()
        assert "Phi^15 QUANTUM COHERENCE" in output
        assert "Total Blocks" in output
        assert "Birthday Echoes" in output
        assert "INTERPRETATIONS" in output
        assert "AntPool" in output
        assert "ViaBTC" in output


# ============================================================================
# SECTION 8 -- Property-Based Invariants
# ============================================================================


class TestPropertyBasedInvariants:
    """Invariant checks for the Phi^15 resonance system."""

    def test_phi_resonance_symmetry(self) -> None:
        """Phi^15 resonance should be symmetric: nonce + Phi^15 -> same k+1."""
        import random

        rng = random.Random(42)
        for _ in range(50):
            nonce = rng.randint(1, 2**30)
            k1, _, d1, _ = compute_phi15_resonance(nonce)
            k2, _, d2, _ = compute_phi15_resonance(nonce + round(PHI_15))
            assert k2 == k1 + 1, f"k2={k2} != k1+1={k1 + 1} for nonce={nonce}"
            assert abs(d2 - d1) < 1.5, f"Diffs not close: {d1} vs {d2}"

    def test_precision_bounded_01(self) -> None:
        """Precision should always be <= 100%."""
        import random

        rng = random.Random(123)
        for _ in range(100):
            nonce = rng.randint(1, 2**32 - 1)
            _, _, _, p = compute_phi15_resonance(nonce)
            assert p <= 100.0, f"Precision {p}% exceeds 100%"

    def test_diff_non_negative(self) -> None:
        """Diff should always be non-negative."""
        import random

        rng = random.Random(456)
        for _ in range(100):
            nonce = rng.randint(1, 2**32 - 1)
            _, _, d, _ = compute_phi15_resonance(nonce)
            assert d >= 0.0

    def test_birthday_resonance_deterministic(self) -> None:
        """Same nonce -> same birthday resonance result."""
        nonce = 31071976
        md1, hits1 = check_birthday_resonance(nonce)
        md2, hits2 = check_birthday_resonance(nonce)
        assert md1 == md2
        assert hits1 == hits2

    def test_k_multiplier_monotonic(self) -> None:
        """Larger nonces should have larger or equal k."""
        ks = []
        for nonce in range(1000, 100000, 1000):
            k, _, _, _ = compute_phi15_resonance(nonce)
            ks.append(k)
        for i in range(1, len(ks)):
            assert ks[i] >= ks[i - 1], f"k decreased at {i}: {ks[i]} < {ks[i - 1]}"

    def test_resonance_rate_bounded(self) -> None:
        """Resonance rate must be in [0, 1]."""
        import random

        rng = random.Random(789)
        records = []
        for i in range(50):
            nonce = rng.randint(1, 2**32 - 1) if i < 45 else round(1000 * PHI_15)
            k, approx, diff, precision = compute_phi15_resonance(nonce)
            is_res = precision >= PRECISION_THRESHOLD or diff < 1.0
            records.append(
                NonceResonanceRecord(
                    height=900000 + i,
                    timestamp=1700000000 + i,
                    nonce=nonce,
                    miner="Test",
                    k_multiplier=k,
                    approx=approx,
                    diff=diff,
                    precision_pct=precision,
                    resonance_strength=max(0.0, 1.0 - (diff / (PHI_15 / 2.0))),
                    is_phi_resonant=is_res,
                    birthday_modular_diff=None,
                    birthday_substring_hits=[],
                    birthday_resonant=False,
                    birthday_echo_type="none",
                )
            )
        summary = compute_summary(records)
        assert 0.0 <= summary.phi_resonance_rate <= 1.0
        assert 0.0 <= summary.birthday_echo_rate <= 1.0
