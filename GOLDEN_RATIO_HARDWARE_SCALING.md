# Golden Ratio Hardware Scaling — Design and Implementation

**Date:** June 26, 2026  
**Status:** Design Complete, Ready for Implementation

---

## Executive Summary

The golden ratio φ ≈ 1.618 can be used to scale hardware resources in a mathematically principled way, avoiding arbitrary step sizes while maintaining natural resource allocation curves. This is particularly valuable for:

1. **GPU allocation** — Scale GPU counts across nodes via φ-power series
2. **Batch size tuning** — φ-scaled search depths and batch sizes
3. **Memory allocation** — φ-proportional working set sizes
4. **Power/performance curves** — φ-based thermal and power envelopes

---

## Mathematical Foundation

The golden ratio φ = (1+√5)/2 ≈ 1.6180339887 has unique mathematical properties:

### Key Identities

- φ² = φ + 1 ≈ 2.618
- 1/φ = φ - 1 ≈ 0.618
- φⁿ = Fₙφ + Fₙ₋₁ (Fibonacci relationship)

### Golden Branching

For discrete hardware scaling, use the **Fibonacci sequence** derived from φ:

```
F(0)=0, F(1)=1, F(n)=F(n-1)+F(n-2)
0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144...
```

This gives natural scaling steps that avoid powers of 2 (which overshoot) or linear steps (which are too fine-grained).

---

## Implementation: GoldenRatioScaler

```python
# python_backend/pythia_mining/golden_ratio_scaler.py

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional


PHI: float = (1.0 + math.sqrt(5.0)) / 2.0


@dataclass
class ScalingProposal:
    """A single hardware scaling recommendation."""

    dimension: str  # "gpus", "batch_size", "memory_mb", "search_depth"
    current_value: int
    proposed_value: int
    fibonacci_index: int
    rationale: str


class GoldenRatioScaler:
    """Scale hardware dimensions using golden-ratio / Fibonacci sequences.

    This class provides mathematically principled scaling that:
    - Avoids binary overshoot
    - Maintains natural growth curves
    - Is deterministic and auditable
    - Maps directly to PHI constant used throughout HYBA
    """

    def __init__(self, base: int = 1) -> None:
        if base < 1:
            base = 1
        self.base = base
        self._fib_cache: List[int] = [0, 1]

    # ------------------------------------------------------------------
    # Fibonacci sequence (scaled by base)
    # ------------------------------------------------------------------

    def _fib(self, n: int) -> int:
        """Return the n-th Fibonacci number scaled by base."""
        if n < 0:
            raise ValueError(f"Negative Fibonacci index: {n}")
        cache = self._fib_cache
        while len(cache) <= n:
            cache.append(cache[-1] + cache[-2])
        return self.base * cache[n]

    def fib_series(self, count: int, start: int = 0) -> List[int]:
        """Return *count* Fibonacci values starting at *start*."""
        return [self._fib(start + i) for i in range(count)]

    # ------------------------------------------------------------------
    # Scaling helpers
    # ------------------------------------------------------------------

    def next_gpu_count(self, current_gpus: int) -> int:
        """Return the next GPU count in the Fibonacci sequence >= current_gpus."""
        if current_gpus < 1:
            return self._fib(2)  # 1
        # Find smallest fib >= current
        n = 2
        while self._fib(n) < current_gpus:
            n += 1
            if n > 50:
                break
        # Return next step up
        n += 1
        return self._fib(min(n, 50))

    def prev_gpu_count(self, current_gpus: int) -> int:
        """Return the previous GPU count in the Fibonacci sequence."""
        if current_gpus <= 1:
            return 1
        n = 2
        while self._fib(n) > current_gpus:
            n -= 1
            if n < 2:
                return 1
        return self._fib(n)

    def scale_batch_size(self, current: int, direction: str = "up") -> int:
        """Scale batch size by Fibonacci series."""
        if current < 1:
            current = 1
        if direction == "up":
            n = 2
            while self._fib(n) <= current:
                n += 1
                if n > 50:
                    return current
            return self._fib(n)
        else:
            n = 2
            while self._fib(n) >= current:
                n -= 1
                if n < 2:
                    return 1
            return self._fib(n)

    def scale_memory(self, current_mb: int, direction: str = "up") -> int:
        """Scale memory allocation in MB using φ-scaled Fibonacci."""
        if current_mb < 1:
            current_mb = 1
        # Use fib index = log_φ(current/base) to find close match
        if direction == "up":
            target = int(current_mb * PHI)
        else:
            target = int(current_mb / PHI)
        return max(1, target)

    def propose_scaling_plan(
        self,
        dimensions: List[str],
        current: Dict[str, int],
        target_coherence: float,
        phi_density: float,
    ) -> List[ScalingProposal]:
        """Generate a φ-scaled resource plan for multiple dimensions.

        Args:
            dimensions: List of dimension names (e.g., ["gpus", "batch_size", "search_depth"])
            current: Current values for each dimension
            target_coherence: Target φ-coherence (0-1)
            phi_density: Current φ-density from mining state

        Returns:
            List of ScalingProposal objects
        """
        proposals: List[ScalingProposal] = []
        coherence_factor = max(0.0, min(1.0, target_coherence))

        for dim in dimensions:
            cur = current.get(dim, 1)
            if cur < 1:
                cur = 1

            # High coherence → scale up; low coherence → hold or scale down
            if coherence_factor >= 0.7:
                direction = "up"
                rationale = (
                    f"High coherence ({coherence_factor:.2f}) "
                    f"and phi_density ({phi_density:.2f}) → scale up via φ-series"
                )
            elif coherence_factor >= 0.4:
                direction = "maintain"
                rationale = (
                    f"Medium coherence ({coherence_factor:.2f}) → maintain current scale"
                )
            else:
                direction = "down"
                rationale = (
                    f"Low coherence ({coherence_factor:.2f}) → defensive scale down"
                )

            if dim == "gpus":
                if direction == "up":
                    proposed = self.next_gpu_count(cur)
                elif direction == "down":
                    proposed = self.prev_gpu_count(cur)
                else:
                    proposed = cur
            elif dim == "batch_size":
                if direction == "up":
                    proposed = self.scale_batch_size(cur, "up")
                elif direction == "down":
                    proposed = self.scale_batch_size(cur, "down")
                else:
                    proposed = cur
            elif dim == "memory_mb":
                proposed = self.scale_memory(cur, direction)
            elif dim == "search_depth":
                # Search depth follows Fibonacci directly
                if direction == "up":
                    n = 2
                    while self._fib(n) <= cur:
                        n += 1
                    proposed = self._fib(n)
                elif direction == "down":
                    n = 2
                    while self._fib(n) >= cur:
                        n -= 1
                    proposed = max(1, self._fib(max(n, 1)))
                else:
                    proposed = cur
            else:
                proposed = cur

            # Cap proposed value at reasonable maximum (e.g., 144 GPUs)
            proposed = min(proposed, 144)

            # Find Fibonacci index for audit trail
            fib_idx = 2
            while self._fib(fib_idx) < proposed:
                fib_idx += 1
                if fib_idx > 50:
                    break

            proposals.append(
                ScalingProposal(
                    dimension=dim,
                    current_value=cur,
                    proposed_value=proposed,
                    fibonacci_index=fib_idx,
                    rationale=rationale,
                )
            )

        return proposals

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base": self.base,
            "phi": PHI,
            "fib_series_10": self.fib_series(10, start=1),
        }