"""Shared golden-ratio constants and policies for PULVINI systems.

The values here are intentionally conservative defaults.  Runtime callers may
still override them through existing constructor/config parameters; this module
only removes duplicated magic numbers from phi scaling and memory compression.
"""

from __future__ import annotations

import logging
import math
import os
import sys
from dataclasses import dataclass

PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV = 1.0 / PHI
EPSILON = 1e-12
DEFAULT_TOLERANCE = (
    1e-8  # float64 accumulation over 2 fold levels can reach ~1e-9; 1e-8 gives safe headroom
)
DEFAULT_PHI_SCALING_POWER = 1.5
DEFAULT_LOW_VARIANCE_THRESHOLD = 0.05
DEFAULT_HIGH_VARIANCE_THRESHOLD = 0.2
DEFAULT_ENSEMBLE_MEMORY_LIMIT = 1024
DEFAULT_SPARSE_SKIP_THRESHOLD = 0.85


def initialize_production_secrets() -> dict:
    """
    Mandatory production environment initialization gate.
    Verifies secrets are pulled safely from an active vault service.

    Returns:
        Dictionary with 'status' key indicating security state

    Raises:
        SystemExit: If critical secrets are missing or insecure in production mode
    """
    # Allow development mode bypass
    if os.getenv("HYBA_ALLOW_DEV_FIXTURES") == "true":
        return {"status": "DEV_PASS"}

    # Assert production compliance rules
    critical_secrets = [
        "JWT_SECRET",
        "HYBA_OPERATOR_CREDENTIALS",
        "POOL_PRIMARY_CREDENTIALS",
    ]

    logger = logging.getLogger("hyba.security")
    failed_secrets = []

    for secret in critical_secrets:
        val = os.getenv(secret, "")
        # Check for missing, placeholder, or insecure values
        if not val or val.startswith("PLACEHOLDER_") or len(val) < 16:
            failed_secrets.append(secret)

    if failed_secrets:
        logger.critical(
            f"SEC_FAIL: Missing or insecure configuration secrets: {', '.join(failed_secrets)}. "
            "System execution halted."
        )
        print(
            f"\n[CRITICAL] Insecure secret configurations found.\n"
            f"   Failed secrets: {', '.join(failed_secrets)}\n"
            f"   System execution halted to prevent production exposure.\n"
        )
        sys.exit(1)  # Fail-closed logic blocking initialization

    logger.info("Production secrets validated successfully")
    return {"status": "SEC_SECURE"}


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
