"""Golden Ratio Hardware Scaling — Mathematical Resource Allocation.

Scales hardware resources (GPUs, batch sizes, memory, search depth) using
the Fibonacci sequence derived from the golden ratio φ ≈ 1.618.

This avoids arbitrary step sizes and maintains natural growth curves aligned
with HYBA's mathematical substrate.

REFLEXIVE KNOWLEDGE LOOP:
The scaler exposes propose_scaling_plan() which the autonomous controller
can call during reflexive cycles to optimize hardware utilization based on
current φ-coherence and φ-density.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


PHI: float = (1.0 + math.sqrt(5.0)) / 2.0


@dataclass
class ScalingProposal:
    """A single hardware scaling recommendation."""

    dimension: str  # "gpus", "batch_size", "memory_mb", "search_depth"
    current_value: int
    proposed_value: int
    fibonacci_index: int
    rationale: str


@dataclass
class ScalingPlan:
    """Complete scaling plan with evidence seal."""

    proposals: List[ScalingProposal]
    coherence_factor: float
    phi_density: float
    timestamp: float
    evidence_seal: Optional[Dict[str, Any]] = None


class GoldenRatioScaler:
    """Scale hardware dimensions using golden-ratio / Fibonacci sequences.

    The scaler is deterministic, auditable, and maps directly to the PHI
    constant used throughout HYBA's mathematical stack.
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
        """Return the next GPU count in the Fibonacci sequence > current_gpus."""
        if current_gpus < 1:
            return 1
        n = 2
        while self._fib(n) <= current_gpus:
            n += 1
            if n > 50:
                break
        return self._fib(min(n, 50))

    def prev_gpu_count(self, current_gpus: int) -> int:
        """Return the previous GPU count in the Fibonacci sequence."""
        if current_gpus <= 2:
            return 1
        # Find largest fib <= current by scanning upward then stepping back
        n = 2
        while self._fib(n) <= current_gpus:
            n += 1
            if n > 50:
                break
        # Back up one step
        n = max(2, n - 2)
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
        if direction == "up":
            target = int(current_mb * PHI)
        else:
            target = int(current_mb / PHI)
        return max(1, target)

    # ------------------------------------------------------------------
    # Proposal generation
    # ------------------------------------------------------------------

    def propose_scaling_plan(
        self,
        dimensions: List[str],
        current: Dict[str, int],
        target_coherence: float,
        phi_density: float,
    ) -> ScalingPlan:
        """Generate a φ-scaled resource plan for multiple dimensions.

        Args:
            dimensions: List of dimension names (e.g., ["gpus", "batch_size", "search_depth"])
            current: Current values for each dimension
            target_coherence: Target φ-coherence (0-1)
            phi_density: Current φ-density from mining state

        Returns:
            ScalingPlan with proposals and evidence seal
        """
        import time

        proposals: List[ScalingProposal] = []
        coherence_factor = max(0.0, min(1.0, target_coherence))

        for dim in dimensions:
            cur = current.get(dim, 1)
            if cur < 1:
                cur = 1

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

            # Cap at reasonable maximum
            proposed = min(proposed, 144)

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

        plan = ScalingPlan(
            proposals=proposals,
            coherence_factor=coherence_factor,
            phi_density=phi_density,
            timestamp=time.time(),
        )

        # Attach evidence seal if pythia_shared is available
        try:
            from pythia_shared.pulvini_core import compute_evidence_seal

            seal_body = {
                "type": "scaling_plan",
                "coherence_factor": round(coherence_factor, 6),
                "phi_density": round(phi_density, 6),
                "timestamp": plan.timestamp,
                "proposal_count": len(proposals),
                "proposed_changes": [
                    {
                        "dimension": p.dimension,
                        "from": p.current_value,
                        "to": p.proposed_value,
                        "fib_index": p.fibonacci_index,
                    }
                    for p in proposals
                ],
            }
            plan.evidence_seal = compute_evidence_seal(seal_body)
        except Exception:
            # Evidence seal is optional; continue without it if dependency missing
            pass

        return plan

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base": self.base,
            "phi": PHI,
            "fib_series_10": self.fib_series(10, start=1),
        }