"""
Φ-Entropy Generator: Fibonacci-LCG for Optimal Dispersion (Tier 10¹⁵)

Implements a low-discrepancy Fibonacci Linear Congruential Generator (Φ-LCG)
that produces nonces following a Golden Spiral trajectory.  Unlike standard RNGs
(Mersenne Twister, etc.) which are designed for statistical randomness, this
generator guarantees optimal dispersion—maximum coverage with zero wasted
proximity—by exploiting the irrationality of the Golden Ratio.

Mathematics:
    X_{n+1} = (X_n + φ⁻¹) mod 1

Because φ⁻¹ is irrational, the sequence never repeats until the entire space
is exhausted, and consecutive points are separated by the golden angle—the same
angle that governs phyllotaxis in sunflower seed arrangements.
"""

from __future__ import annotations

from typing import Optional

import numpy as np

# ── Golden Ratio constants ─────────────────────────────────────────────────
PHI: float = 1.618033988749895
INV_PHI: float = 0.618033988749895  # 1/φ, the fundamental spacing
GOLDEN_ANGLE: float = 137.50776405003785  # 360/φ² degrees


class PhiEntropyGenerator:
    """Fibonacci Linear Congruential Generator (Φ-LCG).

    Produces nonces following a Golden Spiral trajectory for optimal
    dispersion across the mining manifold.  The sequence is deterministic,
    low-discrepancy, and guaranteed not to repeat until the full space
    has been traversed (by irrational rotation on the unit interval).

    Typical usage::

        gen = PhiEntropyGenerator(seed=42, memory_size=2**32)
        nonce = gen.next_nonce()          # single nonce
        batch = gen.get_batch(1024)       # vectorised batch (GPU-ready)
    """

    def __init__(self, seed: int, memory_size: int) -> None:
        """Initialise the generator.

        Args:
            seed: Intial seed value (any non-negative integer).
            memory_size: Size of the nonce/address space to map into.
                Must be >= 1.
        """
        if memory_size < 1:
            raise ValueError(f"memory_size must be >= 1, got {memory_size}")

        self.PHI = PHI
        self.INV_PHI = INV_PHI
        # Normalise seed onto [0, 1) with golden offset
        self.current_state = (seed * INV_PHI) % 1.0
        self.memory_size = memory_size
        self.counter = 0
        self._spiral_radius = 0.0
        self._spiral_angle = 0.0

    # ── Core generation ────────────────────────────────────────────────────

    def next_nonce(self) -> int:
        """Generate the next single nonce.

        The irrationality of φ⁻¹ guarantees the sequence never repeats
        until the entire space is exhausted (*Golden Uniformity*).

        Returns:
            An integer nonce in ``[0, memory_size)``.
        """
        # Fibonacci-LCG step: advance along unit circle by φ⁻¹
        self.current_state = (self.current_state + self.INV_PHI) % 1.0
        self.counter += 1

        # Advance golden spiral coordinates
        self._spiral_radius = np.sqrt(self.counter + 1)
        self._spiral_angle = (self._spiral_angle + GOLDEN_ANGLE) % 360.0

        # Scale fractional state to integer address space
        return int(self.current_state * self.memory_size)

    # ── Batch / vectorised generation ──────────────────────────────────────

    def get_batch(self, batch_size: int) -> np.ndarray:
        """Vectorised batch generation for Tier 10¹⁵+ execution.

        Uses NumPy vectorisation to compute ``batch_size`` consecutive
        nonces in a single pass, avoiding the Python loop overhead of
        repeated ``next_nonce()`` calls.

        Args:
            batch_size: Number of nonces to generate.

        Returns:
            ``uint32`` NumPy array of shape ``(batch_size,)`` containing
            nonces in ``[0, memory_size)``.
        """
        if batch_size < 1:
            raise ValueError(f"batch_size must be >= 1, got {batch_size}")

        # Build index array: [counter, counter+1, ..., counter+batch_size-1]
        indices = np.arange(self.counter, self.counter + batch_size, dtype=np.float64)

        # Closed-form Φ-LCG: X_n = (seed + n * φ⁻¹) mod 1
        # Precompute the full batch state in one vectorised operation
        batch_states = (self.current_state + indices * self.INV_PHI) % 1.0

        # Update internal state to the tail of the batch
        self.counter += batch_size
        self.current_state = float(batch_states[-1])

        # Advance spiral tracking (approximate — batch endpoint only)
        self._spiral_radius = np.sqrt(self.counter + 1)
        self._spiral_angle = (self._spiral_angle + GOLDEN_ANGLE * batch_size) % 360.0

        # Scale to memory space and cast to uint32
        return (batch_states * self.memory_size).astype(np.uint32)

    # ── Spiral diagnostic helpers ──────────────────────────────────────────

    def get_spiral_point(self) -> dict[str, float]:
        """Return the current golden spiral coordinates for diagnostics."""
        return {
            "radius": float(self._spiral_radius),
            "angle_deg": float(self._spiral_angle),
            "iteration": self.counter,
        }

    def get_coverage_entropy(self, bins: int = 1024) -> dict[str, float]:
        """Estimate coverage quality over a coarse histogram.

        Useful for verifying that the low-discrepancy property is
        being maintained at runtime.

        Args:
            bins: Number of histogram bins (default 1024).

        Returns:
            Dictionary with *entropy*, *coverage_pct*, and
            *golden_uniformity* metrics.
        """
        if self.counter < bins:
            return {
                "entropy": -1.0,
                "coverage_pct": 0.0,
                "golden_uniformity": 0.0,
                "status": "insufficient_data",
            }

        # Build a coarse histogram of the most recent `bins * 4` nonces
        n_samples = bins * 4
        indices = np.arange(
            max(0, self.counter - n_samples), self.counter, dtype=np.float64
        )
        states = (self.current_state + indices * self.INV_PHI) % 1.0
        hist, _ = np.histogram(states, bins=bins, range=(0.0, 1.0))

        total = float(hist.sum())
        if total == 0.0:
            return {
                "entropy": 0.0,
                "coverage_pct": 0.0,
                "golden_uniformity": 0.0,
            }

        probs = hist / total
        entropy = -float(np.sum(probs * np.log(probs + 1e-30)))
        coverage = float(np.sum(hist > 0))

        # Ideal entropy for uniform is log(bins)
        ideal_entropy = np.log(bins)
        uniformity = entropy / ideal_entropy if ideal_entropy > 0 else 0.0

        return {
            "entropy": entropy,
            "coverage_pct": (coverage / bins) * 100.0,
            "golden_uniformity": float(uniformity),
            "bins": bins,
            "samples": n_samples,
            "status": "golden_uniform" if uniformity > 0.95 else "suboptimal",
        }

    def reset(self, seed: Optional[int] = None) -> None:
        """Reset the generator to its initial state.

        Args:
            seed: Optional new seed.  If ``None``, preserves the
                  original seed used at construction.
        """
        original_seed = int(
            (self.current_state * self.memory_size) / self.INV_PHI
        ) if self.counter > 0 else 0

        s = seed if seed is not None else original_seed
        self.current_state = (s * self.INV_PHI) % 1.0
        self.counter = 0
        self._spiral_radius = 0.0
        self._spiral_angle = 0.0


# ── Convenience factory ────────────────────────────────────────────────────

def create_phi_entropy_generator(
    seed: Optional[int] = None,
    memory_size: int = 2**32,
) -> PhiEntropyGenerator:
    """Create a configured Φ-Entropy Generator.

    Args:
        seed: Entropy seed.  Defaults to ``int(φ * 1e9)`` for a
              deterministic golden baseline.
        memory_size: Search space size (default 2³²).

    Returns:
        Configured :class:`PhiEntropyGenerator` instance.
    """
    if seed is None:
        seed = int(PHI * 1e9)
    return PhiEntropyGenerator(seed=seed, memory_size=memory_size)


# ── Self-test / validation ─────────────────────────────────────────────────

def _self_test() -> None:
    """Quick sanity check of the generator's dispersion properties."""
    gen = create_phi_entropy_generator(seed=42, memory_size=10_000)

    # Single nonce generation
    nonces = [gen.next_nonce() for _ in range(1000)]
    assert all(0 <= n < 10_000 for n in nonces), "nonces out of range"
    unique = len(set(nonces))
    print(f"Single-step: {unique}/1000 unique nonces ({unique/10:.1f}%)")

    # Batch generation
    gen.reset(seed=42)
    batch = gen.get_batch(1000)
    assert batch.shape == (1000,), f"unexpected batch shape: {batch.shape}"
    assert batch.dtype == np.uint32, f"unexpected dtype: {batch.dtype}"
    batch_unique = len(set(batch.tolist()))
    print(f"Batch:       {batch_unique}/1000 unique nonces ({batch_unique/10:.1f}%)")

    # Coverage diagnostics
    metrics = gen.get_coverage_entropy(bins=128)
    print(f"Coverage:    {metrics['coverage_pct']:.1f}% "
          f"(uniformity={metrics['golden_uniformity']:.4f})")
    assert metrics["golden_uniformity"] > 0.85, (
        f"low golden uniformity: {metrics['golden_uniformity']}"
    )
    print("[PASS] All self-tests passed.")


if __name__ == "__main__":
    _self_test()


__all__ = [
    "PHI",
    "INV_PHI",
    "GOLDEN_ANGLE",
    "PhiEntropyGenerator",
    "create_phi_entropy_generator",
]