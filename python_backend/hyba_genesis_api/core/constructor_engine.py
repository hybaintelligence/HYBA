"""Constructor-theory integrity checks for reflexive learning proposals."""

from __future__ import annotations

import math
from typing import Any, Dict

PHI = (1.0 + math.sqrt(5.0)) / 2.0


class ExplainerIntegrity:
    """Validate that proposed bridges are deterministic and hard to vary."""

    def validate_explanation(
        self, proposal: Dict[str, Any], codebase_hash: str
    ) -> bool:
        """Return True only for bounded, hash-stable, φ-coupled proposals."""

        if not codebase_hash or "adjustment" not in proposal:
            return False
        adjustment = abs(float(proposal["adjustment"]))
        if not math.isfinite(adjustment) or adjustment < 0.0:
            return False
        hash_tether = int(codebase_hash[:8], 16) / 0xFFFFFFFF
        phi_phase = (adjustment * PHI + hash_tether) % (1.0 / PHI)
        return phi_phase < 0.1 or adjustment <= 0.01
