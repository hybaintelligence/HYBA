"""Shared golden-ratio constants and policies for PULVINI systems.

The values here are intentionally conservative defaults.  Runtime callers may
still override them through existing constructor/config parameters; this module
only removes duplicated magic numbers from phi scaling and memory compression.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV = 1.0 / PHI
EPSILON = 1e-12
DEFAULT_TOLERANCE = 1e-9
DEFAULT_PHI_SCALING_POWER = 1.5
DEFAULT_LOW_VARIANCE_THRESHOLD = 0.05
DEFAULT_HIGH_VARIANCE_THRESHOLD = 0.2
DEFAULT_ENSEMBLE_MEMORY_LIMIT = 1024
DEFAULT_SPARSE_SKIP_THRESHOLD = 0.85


@dataclass(frozen=True)
class PhiScalingPolicy:
    """Configurable policy for phi-weighted model aggregation."""

    phi_scaling_power: float = DEFAULT_PHI_SCALING_POWER
    low_variance_threshold: float = DEFAULT_LOW_VARIANCE_THRESHOLD
    high_variance_threshold: float = DEFAULT_HIGH_VARIANCE_THRESHOLD
    memory_limit: int = DEFAULT_ENSEMBLE_MEMORY_LIMIT

    def __post_init__(self) -> None:
        if self.low_variance_threshold < 0:
            raise ValueError("low_variance_threshold must be non-negative")
        if self.high_variance_threshold <= self.low_variance_threshold:
            raise ValueError("high_variance_threshold must be greater than low_variance_threshold")
        if self.memory_limit < 0:
            raise ValueError("memory_limit must be non-negative")


@dataclass(frozen=True)
class PhiCompressionPolicy:
    """Configurable policy for reversible phi memory folding."""

    tolerance: float = DEFAULT_TOLERANCE
    fold_depth: int = 2
    sparse_skip_threshold: float = DEFAULT_SPARSE_SKIP_THRESHOLD

    def __post_init__(self) -> None:
        if self.tolerance <= 0:
            raise ValueError("tolerance must be positive")
        if self.fold_depth < 1:
            raise ValueError("fold_depth must be >= 1")
        if not 0.0 <= self.sparse_skip_threshold <= 1.0:
            raise ValueError("sparse_skip_threshold must be between 0.0 and 1.0")
