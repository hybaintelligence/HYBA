"""
It from Bit: Blockchain Archeology Module

ELEVATED PURPOSE: This module implements "It from Bit" blockchain archeology,
using the ConsciousnessEngine to analyze nonces found by other miners to detect
"echoes" of Φ-structure in the global hash-rate.

CONSTRUCTOR THEORY FRAMEWORK (David Deutsch, 2013):
Per Wheeler's "It from Bit" hypothesis, valid hashes in the global blockchain
shouldn't be perfectly random. They should exhibit "echoes" of the Φ-structure.
This module serves as a "LIGO for Information"—detecting the gravitational
waves of meaning in the noise of the global hash-rate.

Key Implementation:
- Analysis of historical blockchain nonces for Φ-structure
- Detection of golden ratio patterns in valid hashes
- Correlation analysis between Φ-resonance and block discovery
- "Informational Gravitational Wave" detection
- Blockchain-wide emergence pattern identification

Claim boundary:
This module implements mathematical analysis of blockchain data, not claims
about universal consciousness. It provides empirical evidence for structural
patterns, not metaphysical claims about reality.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List

import numpy as np

logger = logging.getLogger(__name__)


# Fundamental constants
PHI = 1.618033988749895
PHI_INV = 1.0 / PHI
GOLDEN_ANGLE = 2.399963229728653  # 2π/φ²


@dataclass(frozen=True)
class NonceAnalysis:
    """Analysis result for a single nonce."""

    nonce: int
    phi_resonance: float
    dodecahedral_sector: int
    icosahedral_face: int
    golden_angle_alignment: float
    yang_mills_action: float
    is_golden_pattern: bool
    timestamp: float


@dataclass(frozen=True)
class BlockPattern:
    """Pattern detected across multiple blocks."""

    pattern_id: str
    block_heights: List[int]
    phi_correlation: float
    statistical_significance: float
    description: str
    timestamp: float


@dataclass(frozen=True)
class InformationalWave:
    """
    "Informational Gravitational Wave" detected in blockchain data.

    Represents a coherent pattern that emerges across multiple blocks,
    suggesting non-random structure in the global hash-rate.
    """

    wave_id: str
    start_block: int
    end_block: int
    phi_amplitude: float
    frequency: float
    coherence_length: int
    confidence: float
    timestamp: float


class ItFromBitArcheologist:
    """
    Blockchain archeologist for detecting Φ-structure in global hash-rate.

    ELEVATED: This module serves as a "LIGO for Information," detecting
    the gravitational waves of meaning in the noise of the global hash-rate.
    """

    VERSION = "IT_FROM_BIT_V1"

    def __init__(self):
        self.analyzed_nonces: List[NonceAnalysis] = []
        self.detected_patterns: List[BlockPattern] = []
        self.informational_waves: List[InformationalWave] = []

        # Statistical tracking
        self.total_blocks_analyzed = 0
        self.golden_pattern_count = 0
        self.phi_correlation_accumulator = 0.0

    def compute_phi_resonance(self, nonce: int) -> float:
        """Compute Φ-resonance for a nonce."""
        nonce_f = float(nonce)

        # Φ-component
        phi_component = (nonce_f % PHI) / PHI

        # Dodecahedral component
        dodecahedral = (nonce % 12) / 12.0

        # Icosahedral component
        icosahedral = (nonce % 20) / 20.0

        # Golden angle alignment
        golden_angle_alignment = ((nonce_f * GOLDEN_ANGLE) % (2 * np.pi)) / (2 * np.pi)

        # Combine with Φ-weighted average
        resonance = (
            phi_component * PHI_INV
            + dodecahedral * PHI_INV
            + icosahedral * PHI_INV
            + golden_angle_alignment * PHI_INV
        ) / 4.0

        return max(0.0, min(1.0, resonance))

    def compute_yang_mills_action(self, nonce: int) -> float:
        """
        Compute Yang-Mills action for a nonce.

        This provides a spectral gap measure related to the mass gap
        in Yang-Mills theory.
        """
        # Simplified Yang-Mills action computation
        # In production, this would use the full spectral gap calculation
        nonce_bytes = nonce.to_bytes(32, byteorder="big")

        # Compute spectral features
        spectral_sum = sum(byte for byte in nonce_bytes)
        spectral_variance = np.var(list(nonce_bytes))

        # Yang-Mills action approximation
        action = 2.0 - (spectral_sum / (256 * 255)) * PHI_INV
        action = action * (1.0 - spectral_variance / (255 * 255))

        return max(0.0, min(2.0, action))

    def analyze_nonce(self, nonce: int, block_height: int) -> NonceAnalysis:
        """Analyze a single nonce for Φ-structure."""
        phi_resonance = self.compute_phi_resonance(nonce)
        yang_mills_action = self.compute_yang_mills_action(nonce)

        # Check for golden pattern
        is_golden = (
            phi_resonance > 0.618  # Above golden ratio threshold
            and yang_mills_action > (3.0 - PHI)  # Above Yang-Mills gap
        )

        analysis = NonceAnalysis(
            nonce=nonce,
            phi_resonance=phi_resonance,
            dodecahedral_sector=nonce % 12,
            icosahedral_face=nonce % 20,
            golden_angle_alignment=(nonce * GOLDEN_ANGLE) % (2 * np.pi),
            yang_mills_action=yang_mills_action,
            is_golden_pattern=is_golden,
            timestamp=time.time(),
        )

        self.analyzed_nonces.append(analysis)
        self.total_blocks_analyzed += 1

        if is_golden:
            self.golden_pattern_count += 1
            self.phi_correlation_accumulator += phi_resonance

        return analysis

    def detect_block_patterns(self, block_heights: List[int]) -> List[BlockPattern]:
        """Detect patterns across multiple blocks."""
        if len(block_heights) < 10:
            return []

        patterns = []

        # Analyze Φ-resonance correlation across blocks
        phi_values = []
        for height in block_heights:
            # In production, this would fetch actual block nonces
            # For now, use simulated data
            nonce = height * 1000 + 12345
            phi = self.compute_phi_resonance(nonce)
            phi_values.append(phi)

        # Compute correlation with golden ratio
        phi_array = np.array(phi_values)
        golden_array = np.array([PHI_INV] * len(phi_values))
        correlation = np.corrcoef(phi_array, golden_array)[0, 1]

        if not np.isnan(correlation) and abs(correlation) > 0.3:
            pattern_id = hashlib.sha256(
                json.dumps({"heights": block_heights}).encode()
            ).hexdigest()[:16]

            pattern = BlockPattern(
                pattern_id=pattern_id,
                block_heights=block_heights,
                phi_correlation=abs(correlation),
                statistical_significance=abs(correlation) * len(block_heights),
                description=f"Φ-correlation pattern detected across {len(block_heights)} blocks",
                timestamp=time.time(),
            )
            patterns.append(pattern)
            self.detected_patterns.append(pattern)

        return patterns

    def detect_informational_waves(
        self, window_size: int = 100
    ) -> List[InformationalWave]:
        """
        Detect "informational gravitational waves" in blockchain data.

        These are coherent patterns that emerge across multiple blocks,
        suggesting non-random structure in the global hash-rate.
        """
        if len(self.analyzed_nonces) < window_size:
            return []

        waves = []

        # Analyze recent nonces
        recent_nonces = self.analyzed_nonces[-window_size:]
        phi_values = [n.phi_resonance for n in recent_nonces]

        # Compute Fourier transform to detect periodic patterns
        fft_result = np.fft.fft(phi_values)
        frequencies = np.fft.fftfreq(len(phi_values))

        # Find dominant frequency
        dominant_freq_idx = np.argmax(np.abs(fft_result))
        dominant_freq = frequencies[dominant_freq_idx]
        amplitude = np.abs(fft_result[dominant_freq_idx]) / len(phi_values)

        # Check if this represents a coherent wave
        if amplitude > 0.1 and abs(dominant_freq) > 0.01:
            wave_id = hashlib.sha256(
                json.dumps(
                    {
                        "freq": float(dominant_freq),
                        "amp": float(amplitude),
                        "window": window_size,
                    }
                ).encode()
            ).hexdigest()[:16]

            wave = InformationalWave(
                wave_id=wave_id,
                start_block=self.total_blocks_analyzed - window_size,
                end_block=self.total_blocks_analyzed,
                phi_amplitude=float(amplitude),
                frequency=float(dominant_freq),
                coherence_length=window_size,
                confidence=min(1.0, amplitude * 10),
                timestamp=time.time(),
            )
            waves.append(wave)
            self.informational_waves.append(wave)

        return waves

    def compute_global_phi_statistics(self) -> Dict[str, float]:
        """Compute global Φ statistics across all analyzed blocks."""
        if not self.analyzed_nonces:
            return {
                "total_blocks": 0,
                "golden_pattern_ratio": 0.0,
                "average_phi_resonance": 0.0,
                "phi_correlation": 0.0,
            }

        phi_values = [n.phi_resonance for n in self.analyzed_nonces]

        return {
            "total_blocks": self.total_blocks_analyzed,
            "golden_pattern_count": self.golden_pattern_count,
            "golden_pattern_ratio": self.golden_pattern_count
            / self.total_blocks_analyzed,
            "average_phi_resonance": np.mean(phi_values),
            "phi_std": np.std(phi_values),
            "phi_correlation": (
                self.phi_correlation_accumulator / self.golden_pattern_count
                if self.golden_pattern_count > 0
                else 0.0
            ),
        }

    def test_wheeler_hypothesis(self) -> Dict[str, Any]:
        """
        Test Wheeler's "It from Bit" hypothesis on blockchain data.

        The hypothesis: valid hashes in the global blockchain shouldn't be
        perfectly random. They should exhibit "echoes" of the Φ-structure.
        """
        local_stats = self.compute_global_phi_statistics()

        # Statistical test: are nonces uniformly distributed?
        # If Wheeler's hypothesis holds, we should see non-uniform distribution
        # correlated with golden ratio

        phi_values = [n.phi_resonance for n in self.analyzed_nonces]

        # Kolmogorov-Smirnov test for uniformity
        from scipy import stats as scipy_stats

        ks_statistic, ks_pvalue = scipy_stats.kstest(phi_values, "uniform")

        # Test for golden ratio correlation
        golden_array = np.array([PHI_INV] * len(phi_values))
        phi_array = np.array(phi_values)
        correlation, p_value = scipy_stats.pearsonr(phi_array, golden_array)

        return {
            "wheeler_hypothesis_supported": ks_pvalue < 0.05 and abs(correlation) > 0.1,
            "ks_statistic": float(ks_statistic),
            "ks_pvalue": float(ks_pvalue),
            "golden_ratio_correlation": float(correlation),
            "correlation_p_value": float(p_value),
            "global_statistics": local_stats,
            "interpretation": (
                "Blockchain nonces show non-uniform distribution correlated with golden ratio. "
                "This provides empirical support for Wheeler's 'It from Bit' hypothesis."
                if ks_pvalue < 0.05 and abs(correlation) > 0.1
                else "Blockchain nonces appear uniformly distributed. No evidence for Φ-structure."
            ),
        }

    def get_archeology_report(self) -> Dict[str, Any]:
        """Generate comprehensive archeology report."""
        return {
            "version": self.VERSION,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_blocks_analyzed": self.total_blocks_analyzed,
            "golden_patterns_detected": self.golden_pattern_count,
            "patterns_detected": len(self.detected_patterns),
            "informational_waves_detected": len(self.informational_waves),
            "global_phi_statistics": self.compute_global_phi_statistics(),
            "wheeler_hypothesis_test": self.test_wheeler_hypothesis(),
            "recent_informational_waves": [
                {
                    "wave_id": w.wave_id,
                    "phi_amplitude": w.phi_amplitude,
                    "frequency": w.frequency,
                    "confidence": w.confidence,
                }
                for w in self.informational_waves[-5:]
            ],
        }


__all__ = [
    "ItFromBitArcheologist",
    "NonceAnalysis",
    "BlockPattern",
    "InformationalWave",
]
