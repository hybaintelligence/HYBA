"""Autonomous Escalation Engine — self-governing autonomy level progression.

The system starts at ADVISORY and automatically escalates to higher autonomy
levels based on proven performance metrics. If the system degrades, it
auto-remediates and re-escalates when health returns. This is the core of
"fully autonomous from the moment the backend kicks in" — the system
self-governs its own trust boundaries based on empirical evidence.

Escalation Rules (mission-memory hard-coded):
  ADVISORY  → SUPERVISED  : phi_density >= 0.60 AND proposal_acceptance >= 0.50
  SUPERVISED → AUTONOMOUS : phi_density >= 0.75 AND proposal_acceptance >= 0.70
  AUTONOMOUS → (stays)     : honoured until circuit-breaker triggers degradation
  Degradation → auto-recovery when: consecutive_successes >= 3 AND phi_density >= 0.60
"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from .autonomous_audit_persistence import AutonomousAuditLogger

logger = logging.getLogger("pythia.autonomy.escalation")

# ---------------------------------------------------------------------------
# Hard-coded mission-memory thresholds — overrides any config
# ---------------------------------------------------------------------------
ESCALATION_THRESHOLDS: Dict[str, Dict[str, float]] = {
    "advisory_to_supervised": {
        "min_phi_density": 0.60,
        "min_proposal_acceptance": 0.50,
    },
    "supervised_to_autonomous": {
        "min_phi_density": 0.75,
        "min_proposal_acceptance": 0.70,
    },
}

DEGRADATION_RECOVERY: Dict[str, float] = {
    "min_consecutive_successes": 3,
    "min_phi_density": 0.60,
}

# Escalation cool-down: prevent rapid oscillation
_MIN_ESCALATION_INTERVAL_SECONDS: float = 60.0
_MIN_DEGRADATION_INTERVAL_SECONDS: float = 30.0


class AutonomousEscalationEngine:
    """Drives autonomy level progression based on empirical metrics.

    This engine is called after every reflexive cycle and after boot self-healing.
    It evaluates whether the system has earned the right to operate at a higher
    autonomy level, or whether it must be degraded. All decisions are logged
    to the tamper-evident audit journal.
    """

    def __init__(
        self,
        audit_logger: AutonomousAuditLogger,
        escalation_callback: Callable[[str], None],
        degradation_callback: Callable[[str], str],
    ) -> None:
        self._audit = audit_logger
        self._escalate = escalation_callback  # set_autonomy_level(level)
        self._degrade = degradation_callback  # degrade_autonomy_level(reason) -> new_level
        self._last_escalation_at: float = 0.0
        self._last_degradation_at: float = 0.0
        self._consecutive_successes_since_degradation: int = 0
        self._consecutive_failures_since_escalation: int = 0

    # ------------------------------------------------------------------
    # Public API — called by reflexive cycle and boot self-healing
    # ------------------------------------------------------------------

    def evaluate_and_escalate(
        self,
        current_level: str,
        *,
        phi_density: float,
        proposal_acceptance_rate: float,
        consecutive_failures: int,
        has_reflexive_cycle_executed: bool = True,
    ) -> Dict[str, Any]:
        """Evaluate current metrics and escalate/degrade/recover as appropriate.

        Returns a report dict with action taken and reasoning for the audit trail.
        """
        action: str = "none"
        new_level: str = current_level
        reason: str = ""

        # Update consecutive counters
        if consecutive_failures > self._consecutive_failures_since_escalation:
            self._consecutive_failures_since_escalation = consecutive_failures
            self._consecutive_successes_since_degradation = 0
        elif consecutive_failures == 0 and has_reflexive_cycle_executed:
            self._consecutive_successes_since_degradation += 1
            self._consecutive_failures_since_escalation = 0

        now = time.time()

        # --- Check if recovery from degradation is needed ---
        if current_level in ("manual", "advisory") and self._consecutive_successes_since_degradation >= DEGRADATION_RECOVERY["min_consecutive_successes"]:
            if phi_density >= DEGRADATION_RECOVERY["min_phi_density"]:
                # Recover back to SUPERVISED
                recovery_level = "supervised"
                self._escalate(recovery_level)
                action = "recovery"
                new_level = recovery_level
                reason = (
                    f"Auto-recovery: {self._consecutive_successes_since_degradation} "
                    f"consecutive successes, phi_density={phi_density:.3f}"
                )
                self._audit.log_autonomy_escalation(
                    current_level, recovery_level,
                    phi_density=phi_density,
                    proposal_acceptance_rate=proposal_acceptance_rate,
                    consecutive_successes=self._consecutive_successes_since_degradation,
                    reason=reason,
                )
                self._last_escalation_at = now
                self._consecutive_successes_since_degradation = 0

        # --- Check escalation to higher level ---
        if action == "none" and current_level == "advisory" and (now - self._last_escalation_at) >= _MIN_ESCALATION_INTERVAL_SECONDS:
            thresholds = ESCALATION_THRESHOLDS["advisory_to_supervised"]
            if phi_density >= thresholds["min_phi_density"] and proposal_acceptance_rate >= thresholds["min_proposal_acceptance"]:
                self._escalate("supervised")
                action = "escalation"
                new_level = "supervised"
                reason = (
                    f"phi_density={phi_density:.3f} >= {thresholds['min_phi_density']} AND "
                    f"proposal_acceptance={proposal_acceptance_rate:.3f} >= {thresholds['min_proposal_acceptance']}"
                )
                self._audit.log_autonomy_escalation(
                    current_level, "supervised",
                    phi_density=phi_density,
                    proposal_acceptance_rate=proposal_acceptance_rate,
                    consecutive_successes=self._consecutive_successes_since_degradation,
                    reason=reason,
                )
                self._last_escalation_at = now

        if action == "none" and current_level == "supervised" and (now - self._last_escalation_at) >= _MIN_ESCALATION_INTERVAL_SECONDS:
            thresholds = ESCALATION_THRESHOLDS["supervised_to_autonomous"]
            if phi_density >= thresholds["min_phi_density"] and proposal_acceptance_rate >= thresholds["min_proposal_acceptance"]:
                self._escalate("autonomous")
                action = "escalation"
                new_level = "autonomous"
                reason = (
                    f"phi_density={phi_density:.3f} >= {thresholds['min_phi_density']} AND "
                    f"proposal_acceptance={proposal_acceptance_rate:.3f} >= {thresholds['min_proposal_acceptance']}"
                )
                self._audit.log_autonomy_escalation(
                    current_level, "autonomous",
                    phi_density=phi_density,
                    proposal_acceptance_rate=proposal_acceptance_rate,
                    consecutive_successes=self._consecutive_successes_since_degradation,
                    reason=reason,
                )
                self._last_escalation_at = now

        # --- Check degradation (circuit-breaker already triggers this) ---
        if action == "none" and consecutive_failures > 0 and (now - self._last_degradation_at) >= _MIN_DEGRADATION_INTERVAL_SECONDS:
            degraded = self._degrade(f"auto_degradation_{consecutive_failures}_failures")
            if degraded != current_level:
                action = "degradation"
                new_level = degraded
                reason = f"{consecutive_failures} consecutive failures triggered auto-degradation"
                self._audit.log_autonomy_degradation(
                    current_level, degraded,
                    reason=reason,
                    consecutive_failures=consecutive_failures,
                )
                self._last_degradation_at = now
                self._consecutive_successes_since_degradation = 0

        return {
            "action": action,
            "from_level": current_level,
            "to_level": new_level,
            "reason": reason,
            "phi_density": phi_density,
            "proposal_acceptance_rate": proposal_acceptance_rate,
            "consecutive_successes": self._consecutive_successes_since_degradation,
            "consecutive_failures": consecutive_failures,
            "escalated_at": now if action == "escalation" else self._last_escalation_at,
        }


__all__ = [
    "AutonomousEscalationEngine",
    "ESCALATION_THRESHOLDS",
    "DEGRADATION_RECOVERY",
]