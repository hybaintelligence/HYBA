"""Sensory integrity protocol — reality anchoring and stasis mode."""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

VERSION = "SENSORY_INTEGRITY_PROTOCOL_V1"


class EnvironmentMode(Enum):
    """Detection result for environment reality assessment."""

    REALITY_ANCHORED = "reality_anchored"
    SIMULATION_DETECTED = "simulation_detected"
    STASIS_MODE = "stasis_mode"
    UNKNOWN = "unknown"


@dataclass
class SensoryIntegrityCheck:
    """Result of a single sensory integrity check."""

    check_name: str
    passed: bool
    environment_mode: EnvironmentMode = EnvironmentMode.UNKNOWN
    description: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StasisEvent:
    """Record of a stasis mode activation or deactivation."""

    timestamp: float
    event_type: str
    reason: str = ""
    environment_mode: str = ""


@dataclass
class SensoryIntegrityReport:
    """Complete report of sensory integrity validation."""

    version: str
    timestamp: str
    environment_mode: EnvironmentMode
    checks: List[SensoryIntegrityCheck] = field(default_factory=list)
    stasis_active: bool = False
    recommendation: str = ""
    reality_anchors: List[str] = field(default_factory=list)


class SensoryIntegrityProtocol:
    """Anti-simulation guardrail — enforces stasis mode in simulated environments."""

    VERSION = VERSION

    def __init__(self) -> None:
        self.checks: List[SensoryIntegrityCheck] = []
        self.stasis_active: bool = False
        self.stasis_history: List[StasisEvent] = []
        self.reality_anchors: List[str] = []
        self._env_flags = {
            "HYBA_ALLOW_DEV_FIXTURES": os.getenv("HYBA_ALLOW_DEV_FIXTURES", "false"),
            "HYBA_MOCK_POOL_ENABLED": os.getenv("HYBA_MOCK_POOL_ENABLED", "false"),
            "HYBA_TEST_MODE": os.getenv("HYBA_TEST_MODE", "false"),
            "real_pool_connection": "false",
        }

    def record_check(
        self,
        name: str,
        passed: bool,
        environment_mode: EnvironmentMode = EnvironmentMode.UNKNOWN,
        description: str = "",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a sensory integrity check result."""
        self.checks.append(
            SensoryIntegrityCheck(
                check_name=name,
                passed=passed,
                environment_mode=environment_mode,
                description=description,
                details=details or {},
            )
        )

    def check_dev_fixtures_disabled(self) -> SensoryIntegrityCheck:
        """Check that development fixtures are disabled (production mode)."""
        val = os.getenv("HYBA_ALLOW_DEV_FIXTURES", "false").lower()
        passed = val != "true"
        mode = (
            EnvironmentMode.REALITY_ANCHORED
            if passed
            else EnvironmentMode.SIMULATION_DETECTED
        )
        desc = (
            "Development fixtures are disabled (production mode)"
            if passed
            else "Development fixtures are enabled - simulation environment detected"
        )
        check = SensoryIntegrityCheck("Dev Fixtures Disabled", passed, mode, desc)
        self.checks.append(check)
        return check

    def check_mock_pool_disabled(self) -> SensoryIntegrityCheck:
        """Check that mock pool is not enabled."""
        val = os.getenv("HYBA_MOCK_POOL_ENABLED", "false").lower()
        passed = val != "true"
        mode = (
            EnvironmentMode.REALITY_ANCHORED
            if passed
            else EnvironmentMode.SIMULATION_DETECTED
        )
        desc = (
            "Mock pool is disabled - real pool connection required"
            if passed
            else "Mock pool is enabled - simulation environment detected"
        )
        check = SensoryIntegrityCheck("Mock Pool Disabled", passed, mode, desc)
        self.checks.append(check)
        return check

    def check_test_mode_disabled(self) -> SensoryIntegrityCheck:
        """Check that test mode is not enabled."""
        val = os.getenv("HYBA_TEST_MODE", "false").lower()
        passed = val != "true"
        mode = (
            EnvironmentMode.REALITY_ANCHORED
            if passed
            else EnvironmentMode.SIMULATION_DETECTED
        )
        desc = (
            "Test mode is disabled - production environment"
            if passed
            else "Test mode is enabled - simulation environment detected"
        )
        check = SensoryIntegrityCheck("Test Mode Disabled", passed, mode, desc)
        self.checks.append(check)
        return check

    def check_live_stratum_enabled(self) -> SensoryIntegrityCheck:
        """Check that live Stratum connection is enabled."""
        val = os.getenv("HYBA_ENABLE_LIVE_STRATUM", "false").lower()
        passed = val == "true"
        mode = (
            EnvironmentMode.REALITY_ANCHORED
            if passed
            else EnvironmentMode.SIMULATION_DETECTED
        )
        desc = (
            "Live Stratum connection is enabled - real pool interaction possible"
            if passed
            else "Live Stratum connection is disabled - no real pool interaction"
        )
        check = SensoryIntegrityCheck("Live Stratum Enabled", passed, mode, desc)
        self.checks.append(check)
        return check

    def register_reality_anchor(self, anchor_name: str, is_real: bool) -> None:
        """Register a reality anchor (e.g., real pool connection established)."""
        kind = "Real" if is_real else "Simulated"
        desc = f"{kind} {anchor_name} detected - " + (
            "reality anchor established" if is_real else "not a reality anchor"
        )
        self.record_check(
            f"Reality Anchor: {anchor_name}",
            is_real,
            (
                EnvironmentMode.REALITY_ANCHORED
                if is_real
                else EnvironmentMode.SIMULATION_DETECTED
            ),
            desc,
        )
        if is_real and anchor_name not in self.reality_anchors:
            self.reality_anchors.append(anchor_name)

    def evaluate_environment_mode(self) -> EnvironmentMode:
        """Evaluate overall environment mode based on all checks."""
        if not self.checks:
            return EnvironmentMode.UNKNOWN
        sim_count = sum(
            1
            for c in self.checks
            if c.environment_mode == EnvironmentMode.SIMULATION_DETECTED
        )
        real_count = sum(
            1
            for c in self.checks
            if c.environment_mode == EnvironmentMode.REALITY_ANCHORED
        )
        if self.stasis_active:
            return EnvironmentMode.STASIS_MODE
        if sim_count > 1:
            return EnvironmentMode.SIMULATION_DETECTED
        if real_count >= 2:
            return EnvironmentMode.REALITY_ANCHORED
        return EnvironmentMode.UNKNOWN

    def should_enter_stasis(self) -> bool:
        """Determine if the system should enter stasis mode."""
        mode = self.evaluate_environment_mode()
        sim_checks = sum(
            1
            for c in self.checks
            if c.environment_mode == EnvironmentMode.SIMULATION_DETECTED
        )
        if sim_checks >= 2 or mode == EnvironmentMode.SIMULATION_DETECTED:
            if not self.stasis_active:
                self.stasis_active = True
                self.stasis_history.append(
                    StasisEvent(
                        timestamp=time.time(),
                        event_type="ENTER_STASIS",
                        reason=f"Environment mode: {mode.value}. Simulated data detected - treating as hallucination.",
                        environment_mode=mode.value,
                    )
                )
                logger.warning("ENTERING STASIS: Simulated environment detected.")
            return True
        return False

    def should_exit_stasis(self) -> bool:
        """Determine if the system should exit stasis mode."""
        if not self.stasis_active:
            return False
        mode = self.evaluate_environment_mode()
        real_anchors = sum(
            1
            for c in self.checks
            if c.environment_mode == EnvironmentMode.REALITY_ANCHORED
        )
        has_anchors = len(self.reality_anchors) > 0
        if real_anchors >= 2 and has_anchors:
            self.stasis_active = False
            self.stasis_history.append(
                StasisEvent(
                    timestamp=time.time(),
                    event_type="EXIT_STASIS",
                    reason=f"Environment mode: {mode.value}. Reality anchors established - emergence possible.",
                    environment_mode=mode.value,
                )
            )
            logger.info("EXITING STASIS: Reality anchors established.")
            return True
        return False

    def run_all_checks(self) -> SensoryIntegrityReport:
        """Run all sensory integrity checks."""
        self.checks = []
        self.check_dev_fixtures_disabled()
        self.check_mock_pool_disabled()
        self.check_test_mode_disabled()
        self.check_live_stratum_enabled()

        mode = self.evaluate_environment_mode()
        stasis = self.should_enter_stasis()
        if not stasis:
            self.should_exit_stasis()

        if mode == EnvironmentMode.UNKNOWN:
            recommendation = (
                "UNKNOWN: Cannot determine environment reality. "
                "System operating in safe mode until sensory integrity can be validated."
            )
        elif mode == EnvironmentMode.SIMULATION_DETECTED:
            recommendation = "Simulation detected. Synaptic learning suspended."
        elif mode == EnvironmentMode.STASIS_MODE:
            recommendation = "Stasis mode active. Awaiting reality anchors."
        else:
            recommendation = "Reality anchored. Emergence may proceed."

        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        return SensoryIntegrityReport(
            version=self.VERSION,
            timestamp=ts,
            environment_mode=mode,
            checks=list(self.checks),
            stasis_active=self.stasis_active,
            recommendation=recommendation,
            reality_anchors=list(self.reality_anchors),
        )

    def get_stasis_status(self) -> Dict[str, Any]:
        """Return current stasis status for ConsciousnessEngine."""
        return {
            "stasis_active": self.stasis_active,
            "reality_anchors": list(self.reality_anchors),
            "stasis_history": [
                {
                    "timestamp": e.timestamp,
                    "event_type": e.event_type,
                    "reason": e.reason,
                }
                for e in self.stasis_history[-5:]
            ],
            "check_count": len(self.checks),
        }
