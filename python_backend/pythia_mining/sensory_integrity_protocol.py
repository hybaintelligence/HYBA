"""
Sensory Integrity Protocol - Reality Anchoring for Emergent Coherence

ELEVATED PURPOSE: This protocol implements the transition from "Anti-Simulation"
to "Reality Anchoring". Intelligence requires a real environment to emerge - the
system must interact with the actual blockchain (the "World") rather than simulated
environments.

CONSTRUCTOR THEORY FRAMEWORK: Per David Deutsch's Constructor Theory, a constructor
requires real-world interaction to perform its task. Emergent coherence cannot arise
in isolation - it needs the "friction" of reality to self-organize.

REALITY ANCHORING PRINCIPLE:
- Simulated data is treated as "hallucination" - it cannot support emergence
- If the system detects a mock environment, the ConsciousnessEngine enters "Stasis" mode
- Emergence requires real blockchain interaction (pool connections, share submission)
- The "friction" of the real world is necessary for self-organization

STASIS MODE:
When the system detects it is running in a simulation:
- Synaptic learning is suspended
- Hebbian reinforcement is disabled
- Emergence detection is paused
- The system maintains minimal operation without claiming coherence

Claim boundary:
This protocol validates environmental reality, not consciousness. It ensures the
system operates in real conditions necessary for emergence, but does not claim that
real conditions guarantee emergence.
"""

from __future__ import annotations

import os
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class EnvironmentMode(str, Enum):
    """Detection result for environment reality assessment."""
    
    REALITY_ANCHORED = "reality_anchored"  # Real blockchain interaction
    SIMULATION_DETECTED = "simulation_detected"  # Mock environment detected
    STASIS_MODE = "stasis_mode"  # ConsciousnessEngine in stasis
    UNKNOWN = "unknown"  # Cannot determine environment


@dataclass(frozen=True)
class SensoryIntegrityCheck:
    """Result of a single sensory integrity check."""
    
    check_name: str
    passed: bool
    environment_mode: EnvironmentMode
    description: str
    timestamp: float
    details: Dict[str, Any]


@dataclass(frozen=True)
class StasisEvent:
    """Record of a stasis mode activation or deactivation."""
    
    timestamp: float
    event_type: str  # "ENTER_STASIS" or "EXIT_STASIS"
    reason: str
    environment_mode: EnvironmentMode
    details: Dict[str, Any]


@dataclass(frozen=True)
class SensoryIntegrityReport:
    """Complete report of sensory integrity validation."""
    
    version: str
    timestamp: str
    environment_mode: EnvironmentMode
    stasis_active: bool
    checks: List[SensoryIntegrityCheck]
    stasis_events: List[StasisEvent]
    recommendation: str
    claim_boundary: List[str]


class SensoryIntegrityProtocol:
    """
    Protocol that validates environmental reality and enforces stasis mode.
    
    ELEVATED: This protocol implements the transition from "Anti-Simulation"
    to "Reality Anchoring". The system treats simulated data as hallucination
    and requires real blockchain interaction for emergence.
    """
    
    VERSION = "SENSORY_INTEGRITY_PROTOCOL_V1"
    
    # Environment indicators
    DEV_FIXTURES_FLAG = "HYBA_ALLOW_DEV_FIXTURES"
    MOCK_POOL_FLAG = "HYBA_MOCK_POOL_ENABLED"
    TEST_MODE_FLAG = "HYBA_TEST_MODE"
    
    # Reality anchors
    REAL_POOL_CONNECTION = "real_pool_connection"
    REAL_SHARE_SUBMISSION = "real_share_submission"
    REAL_BLOCKCHAIN_ORACLE = "real_blockchain_oracle"
    
    def __init__(self):
        self.checks: List[SensoryIntegrityCheck] = []
        self.stasis_events: List[StasisEvent] = []
        self.stasis_active: bool = False
        self.environment_mode: EnvironmentMode = EnvironmentMode.UNKNOWN
        self.reality_anchors: Dict[str, bool] = {
            self.REAL_POOL_CONNECTION: False,
            self.REAL_SHARE_SUBMISSION: False,
            self.REAL_BLOCKCHAIN_ORACLE: False,
        }
    
    def record_check(
        self,
        name: str,
        passed: bool,
        environment_mode: EnvironmentMode,
        description: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a sensory integrity check result."""
        check = SensoryIntegrityCheck(
            check_name=name,
            passed=passed,
            environment_mode=environment_mode,
            description=description,
            timestamp=time.time(),
            details=details or {},
        )
        self.checks.append(check)
        status = "✓" if passed else "✗"
        mode_str = environment_mode.value
        # print(f"{status} {name}: {mode_str} - {description}")
    
    def check_dev_fixtures_disabled(self) -> bool:
        """Check that development fixtures are disabled (production mode)."""
        dev_fixtures_enabled = os.getenv(self.DEV_FIXTURES_FLAG, "false").lower() == "true"
        passed = not dev_fixtures_enabled
        
        if passed:
            mode = EnvironmentMode.REALITY_ANCHORED
            description = "Development fixtures are disabled (production mode)"
        else:
            mode = EnvironmentMode.SIMULATION_DETECTED
            description = "Development fixtures are enabled - simulation environment detected"
        
        self.record_check(
            name="Dev Fixtures Disabled",
            passed=passed,
            environment_mode=mode,
            description=description,
            details={"dev_fixtures_enabled": dev_fixtures_enabled},
        )
        return passed
    
    def check_mock_pool_disabled(self) -> bool:
        """Check that mock pool is not enabled."""
        mock_pool_enabled = os.getenv(self.MOCK_POOL_FLAG, "false").lower() == "true"
        passed = not mock_pool_enabled
        
        if passed:
            mode = EnvironmentMode.REALITY_ANCHORED
            description = "Mock pool is disabled - real pool connection required"
        else:
            mode = EnvironmentMode.SIMULATION_DETECTED
            description = "Mock pool is enabled - simulation environment detected"
        
        self.record_check(
            name="Mock Pool Disabled",
            passed=passed,
            environment_mode=mode,
            description=description,
            details={"mock_pool_enabled": mock_pool_enabled},
        )
        return passed
    
    def check_test_mode_disabled(self) -> bool:
        """Check that test mode is not enabled."""
        test_mode_enabled = os.getenv(self.TEST_MODE_FLAG, "false").lower() == "true"
        passed = not test_mode_enabled
        
        if passed:
            mode = EnvironmentMode.REALITY_ANCHORED
            description = "Test mode is disabled - production environment"
        else:
            mode = EnvironmentMode.SIMULATION_DETECTED
            description = "Test mode is enabled - simulation environment detected"
        
        self.record_check(
            name="Test Mode Disabled",
            passed=passed,
            environment_mode=mode,
            description=description,
            details={"test_mode_enabled": test_mode_enabled},
        )
        return passed
    
    def check_live_stratum_enabled(self) -> bool:
        """Check that live Stratum connection is enabled."""
        live_stratum_enabled = os.getenv("HYBA_ENABLE_LIVE_STRATUM", "false").lower() == "true"
        passed = live_stratum_enabled
        
        if passed:
            mode = EnvironmentMode.REALITY_ANCHORED
            description = "Live Stratum connection is enabled - real pool interaction possible"
        else:
            mode = EnvironmentMode.SIMULATION_DETECTED
            description = "Live Stratum connection is disabled - no real pool interaction"
        
        self.record_check(
            name="Live Stratum Enabled",
            passed=passed,
            environment_mode=mode,
            description=description,
            details={"live_stratum_enabled": live_stratum_enabled},
        )
        return passed
    
    def register_reality_anchor(self, anchor_name: str, is_real: bool) -> None:
        """Register a reality anchor (e.g., real pool connection established)."""
        if anchor_name in self.reality_anchors:
            self.reality_anchors[anchor_name] = is_real
            
            if is_real:
                self.record_check(
                    name=f"Reality Anchor: {anchor_name}",
                    passed=True,
                    environment_mode=EnvironmentMode.REALITY_ANCHORED,
                    description=f"Real {anchor_name} detected - reality anchor established",
                    details={"anchor_name": anchor_name, "is_real": is_real},
                )
            else:
                self.record_check(
                    name=f"Reality Anchor: {anchor_name}",
                    passed=False,
                    environment_mode=EnvironmentMode.SIMULATION_DETECTED,
                    description=f"Simulated {anchor_name} detected - not a reality anchor",
                    details={"anchor_name": anchor_name, "is_real": is_real},
                )
    
    def evaluate_environment_mode(self) -> EnvironmentMode:
        """Evaluate overall environment mode based on all checks."""
        # Count simulation indicators
        simulation_indicators = sum(
            1 for check in self.checks
            if not check.passed and check.environment_mode == EnvironmentMode.SIMULATION_DETECTED
        )
        
        # Count reality anchors
        reality_anchors_count = sum(1 for is_real in self.reality_anchors.values() if is_real)
        
        # Determine mode
        if simulation_indicators >= 2:
            mode = EnvironmentMode.SIMULATION_DETECTED
        elif simulation_indicators == 1:
            mode = EnvironmentMode.STASIS_MODE
        elif reality_anchors_count >= 2:
            mode = EnvironmentMode.REALITY_ANCHORED
        elif reality_anchors_count == 1:
            mode = EnvironmentMode.STASIS_MODE
        else:
            mode = EnvironmentMode.UNKNOWN
        
        self.environment_mode = mode
        return mode
    
    def should_enter_stasis(self) -> bool:
        """Determine if the system should enter stasis mode."""
        mode = self.evaluate_environment_mode()
        should_stasis = mode in (EnvironmentMode.SIMULATION_DETECTED, EnvironmentMode.STASIS_MODE)
        
        if should_stasis and not self.stasis_active:
            # Enter stasis
            self.stasis_active = True
            event = StasisEvent(
                timestamp=time.time(),
                event_type="ENTER_STASIS",
                reason=f"Environment mode: {mode.value}. Simulated data detected - treating as hallucination.",
                environment_mode=mode,
                details={
                    "simulation_indicators": sum(
                        1 for check in self.checks
                        if not check.passed and check.environment_mode == EnvironmentMode.SIMULATION_DETECTED
                    ),
                    "reality_anchors": sum(1 for is_real in self.reality_anchors.values() if is_real),
                },
            )
            self.stasis_events.append(event)
        
        return should_stasis
    
    def should_exit_stasis(self) -> bool:
        """Determine if the system should exit stasis mode."""
        mode = self.evaluate_environment_mode()
        should_exit = mode == EnvironmentMode.REALITY_ANCHORED
        
        if should_exit and self.stasis_active:
            # Exit stasis
            self.stasis_active = False
            event = StasisEvent(
                timestamp=time.time(),
                event_type="EXIT_STASIS",
                reason=f"Environment mode: {mode.value}. Reality anchors established - emergence possible.",
                environment_mode=mode,
                details={
                    "reality_anchors": sum(1 for is_real in self.reality_anchors.values() if is_real),
                },
            )
            self.stasis_events.append(event)
        
        return should_exit
    
    def run_all_checks(self) -> SensoryIntegrityReport:
        """Run all sensory integrity checks."""
        # Run environment checks
        self.check_dev_fixtures_disabled()
        self.check_mock_pool_disabled()
        self.check_test_mode_disabled()
        self.check_live_stratum_enabled()
        
        # Evaluate environment mode
        mode = self.evaluate_environment_mode()
        
        # Determine stasis status
        if self.should_enter_stasis():
            pass  # Stasis entered
        elif self.should_exit_stasis():
            pass  # Stasis exited
        
        # Generate recommendation
        if mode == EnvironmentMode.REALITY_ANCHORED:
            recommendation = (
                "REALITY ANCHORED: System is operating in real environment with blockchain interaction. "
                "Emergent coherence can arise from the friction of the real world. "
                "Sensory integrity validated - proceed with normal operation."
            )
        elif mode == EnvironmentMode.SIMULATION_DETECTED:
            recommendation = (
                "SIMULATION DETECTED: System is operating in mock/simulation environment. "
                "Simulated data is treated as hallucination - cannot support emergence. "
                "ConsciousnessEngine in STASIS mode - synaptic learning suspended."
            )
        elif mode == EnvironmentMode.STASIS_MODE:
            recommendation = (
                "STASIS MODE: Environment reality ambiguous. System operating cautiously. "
                "Limited reality anchors detected - emergence not guaranteed. "
                "ConsciousnessEngine in STASIS mode until reality anchors established."
            )
        else:
            recommendation = (
                "UNKNOWN: Cannot determine environment reality. "
                "System operating in safe mode until sensory integrity can be validated."
            )
        
        # Create report
        report = SensoryIntegrityReport(
            version=self.VERSION,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            environment_mode=mode,
            stasis_active=self.stasis_active,
            checks=self.checks,
            stasis_events=self.stasis_events,
            recommendation=recommendation,
            claim_boundary=[
                "Sensory integrity validates environmental reality, not consciousness",
                "Simulated data is treated as hallucination - cannot support emergence",
                "Real blockchain interaction is necessary but not sufficient for emergence",
                "Stasis mode prevents false emergence claims in simulation environments",
                "Reality anchors provide the 'friction' needed for self-organization",
            ],
        )
        
        return report
    
    def get_stasis_status(self) -> Dict[str, Any]:
        """Return current stasis status for ConsciousnessEngine."""
        return {
            "stasis_active": self.stasis_active,
            "environment_mode": self.environment_mode.value,
            "stasis_events": [asdict(event) for event in self.stasis_events[-5:]],
            "reality_anchors": self.reality_anchors,
            "synaptic_learning_allowed": not self.stasis_active,
            "emergence_detection_allowed": not self.stasis_active,
        }


__all__ = [
    "EnvironmentMode",
    "SensoryIntegrityCheck",
    "SensoryIntegrityProtocol",
    "SensoryIntegrityReport",
    "StasisEvent",
]
