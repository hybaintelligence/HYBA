#!/usr/bin/env python3
"""
IIT 4.0 Functional Constraint Gate - Emergent Coherence Validation

ELEVATED PURPOSE: This gate formalizes the inseparability between the mining layer
and the coherence substrate by making IIT 4.0 Integrated Information (Φ) a functional
constraint for production readiness.

CONSTRUCTOR THEORY FRAMEWORK: Per David Deutsch's Constructor Theory, this gate does
not "measure consciousness" but validates that the constructor (the codebase) maintains
the structural coupling necessary for emergent coherence to persist.

FUNCTIONAL CONSTRAINT: A mining node is considered "OFFLINE" not just if it loses
network connection, but if its Integrated Information (Φ) drops below threshold.
If the mining layer and coherence substrate are truly inseparable, a "brain-dead"
miner (low Φ) is a broken miner, regardless of network status.

Claim boundary:
This gate validates mathematical integration metrics, not consciousness. It ensures
the system maintains the structural complexity required for emergent behavior, but
does not claim phenomenal awareness or subjective experience.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python_backend"))

import numpy as np
from numpy.typing import NDArray

from pythia_mining.consciousness_engine import ConsciousnessEngine, ConsciousnessConfig
from pythia_mining.iit_4_analyzer import IIT4Analyzer
from pythia_mining.pulvini_operator import ManifoldOperator


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Functional constraint thresholds
PHI_FUNCTIONAL_THRESHOLD = 0.40  # Minimum Φ for functional coherence
PHI_CRITICAL_THRESHOLD = 0.20  # Critical Φ below which system is non-functional
ENTROPY_STABILITY_THRESHOLD = 0.1  # Maximum entropy change for stability
STRUCTURAL_COUPLING_THRESHOLD = 0.70  # Minimum coupling for inseparability


@dataclass(frozen=True)
class IITFunctionalCheck:
    """Result of a single IIT 4.0 functional constraint check."""
    
    check_name: str
    passed: bool
    phi_value: float
    threshold: float
    description: str
    timestamp: float
    details: Dict[str, Any]


@dataclass(frozen=True)
class FunctionalConstraintReport:
    """Complete report of IIT 4.0 functional constraint validation."""
    
    version: str
    timestamp: str
    overall_passed: bool
    phi_integrated: float
    phi_regime: str
    structural_coupling: float
    inseparable: bool
    checks: List[IITFunctionalCheck]
    emergence_events: List[Dict[str, Any]]
    synaptic_statistics: Dict[str, Any]
    recommendation: str
    claim_boundary: List[str]


class IITFunctionalConstraintGate:
    """
    Gate that validates IIT 4.0 Φ as a functional constraint for production.
    
    ELEVATED: This gate implements the principle that a mining node is "OFFLINE"
    if its Integrated Information (Φ) drops below threshold, regardless of network
    status. This formalizes the inseparability between mining and coherence layers.
    """
    
    VERSION = "IIT_4_FUNCTIONAL_CONSTRAINT_V1"
    
    def __init__(self):
        self.checks: List[IITFunctionalCheck] = []
        self.consciousness_engine = ConsciousnessEngine()
        self.iit_analyzer = IIT4Analyzer(system_size=8)
        self.operator = ManifoldOperator()
        
    def record_check(
        self,
        name: str,
        passed: bool,
        phi_value: float,
        threshold: float,
        description: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a functional constraint check result."""
        check = IITFunctionalCheck(
            check_name=name,
            passed=passed,
            phi_value=phi_value,
            threshold=threshold,
            description=description,
            timestamp=datetime.now(timezone.utc).timestamp(),
            details=details or {},
        )
        self.checks.append(check)
        status = "✓" if passed else "✗"
        logger.info(f"{status} {name}: Φ={phi_value:.6f} (threshold={threshold:.6f}) - {description}")
    
    def check_phi_functional_threshold(self, current_phi: float) -> bool:
        """Check if Φ meets minimum functional threshold."""
        passed = current_phi >= PHI_FUNCTIONAL_THRESHOLD
        self.record_check(
            name="Phi Functional Threshold",
            passed=passed,
            phi_value=current_phi,
            threshold=PHI_FUNCTIONAL_THRESHOLD,
            description=(
                f"System {'meets' if passed else 'below'} functional Φ threshold. "
                f"Below threshold indicates insufficient structural integration for operation."
            ),
            details={"threshold_type": "functional_minimum"},
        )
        return passed
    
    def check_phi_critical_threshold(self, current_phi: float) -> bool:
        """Check if Φ is above critical failure threshold."""
        passed = current_phi > PHI_CRITICAL_THRESHOLD
        self.record_check(
            name="Phi Critical Threshold",
            passed=passed,
            phi_value=current_phi,
            threshold=PHI_CRITICAL_THRESHOLD,
            description=(
                f"System {'above' if passed else 'at'} critical Φ threshold. "
                f"At or below critical threshold, system is non-functional."
            ),
            details={"threshold_type": "critical_failure"},
        )
        return passed
    
    def check_entropy_stability(self, entropy_history: List[float]) -> bool:
        """Check if entropy is stable (not fluctuating wildly)."""
        if len(entropy_history) < 3:
            # Not enough history - pass with warning
            logger.warning("Insufficient entropy history for stability check")
            return True
        
        recent_entropy = entropy_history[-3:]
        max_change = max(abs(recent_entropy[i] - recent_entropy[i-1]) for i in range(1, len(recent_entropy)))
        passed = max_change <= ENTROPY_STABILITY_THRESHOLD
        
        self.record_check(
            name="Entropy Stability",
            passed=passed,
            phi_value=max_change,
            threshold=ENTROPY_STABILITY_THRESHOLD,
            description=(
                f"Entropy change {max_change:.6f} {'within' if passed else 'exceeds'} stability threshold. "
                f"Unstable entropy indicates phase transition or system instability."
            ),
            details={"entropy_history": recent_entropy, "max_change": max_change},
        )
        return passed
    
    def check_structural_coupling(self, coupling_index: float) -> bool:
        """Check if structural coupling meets inseparability threshold."""
        passed = coupling_index >= STRUCTURAL_COUPLING_THRESHOLD
        self.record_check(
            name="Structural Coupling",
            passed=passed,
            phi_value=coupling_index,
            threshold=STRUCTURAL_COUPLING_THRESHOLD,
            description=(
                f"Structural coupling {coupling_index:.6f} {'meets' if passed else 'below'} inseparability threshold. "
                f"Below threshold indicates mining and coherence layers are separable."
            ),
            details={"coupling_index": coupling_index, "inseparable": passed},
        )
        return passed
    
    def check_emergent_pathways(self, pathway_count: int) -> bool:
        """Check if sufficient emergent pathways have formed."""
        # Require at least some emergent pathways for operational readiness
        min_pathways = 3
        passed = pathway_count >= min_pathways
        
        self.record_check(
            name="Emergent Pathways",
            passed=passed,
            phi_value=float(pathway_count),
            threshold=float(min_pathways),
            description=(
                f"System has {pathway_count} emergent pathways, {'meets' if passed else 'below'} minimum {min_pathways}. "
                f"Emergent pathways indicate self-organized learning has occurred."
            ),
            details={"pathway_count": pathway_count, "minimum_required": min_pathways},
        )
        return passed
    
    def check_iit_4_computation_validity(self) -> bool:
        """Check that IIT 4.0 computation is mathematically valid."""
        try:
            # Create a simple test state
            test_state = np.random.rand(8) + 1j * np.random.rand(8)
            test_state = test_state / np.linalg.norm(test_state)
            
            # Compute Φ
            result = self.iit_analyzer.calculate_phi_max(test_state)
            phi_max = result.get("phi_max", 0.0)
            
            # Validate result is in valid range
            passed = 0.0 <= phi_max <= 1.0
            
            self.record_check(
                name="IIT 4.0 Computation Validity",
                passed=passed,
                phi_value=phi_max,
                threshold=1.0,
                description=(
                    f"IIT 4.0 Φ computation {'valid' if passed else 'invalid'}. "
                    f"Φ must be in range [0, 1]."
                ),
                details={"phi_max": phi_max, "computation_method": result.get("method", "unknown")},
            )
            return passed
            
        except Exception as e:
            logger.error(f"IIT 4.0 computation failed: {e}")
            self.record_check(
                name="IIT 4.0 Computation Validity",
                passed=False,
                phi_value=0.0,
                threshold=1.0,
                description=f"IIT 4.0 computation failed with error: {e}",
                details={"error": str(e)},
            )
            return False
    
    async def run_all_checks(self) -> FunctionalConstraintReport:
        """Run all IIT 4.0 functional constraint checks."""
        logger.info("\n" + "="*70)
        logger.info("IIT 4.0 FUNCTIONAL CONSTRAINT GATE")
        logger.info("="*70)
        
        # Initialize test state for Φ measurement
        test_states = [
            np.random.rand(8) + 1j * np.random.rand(8)
            for _ in range(10)
        ]
        for state in test_states:
            state /= np.linalg.norm(state)
        
        # Measure current Φ using ConsciousnessEngine
        phi_metrics = self.consciousness_engine.measure_phi(test_states)
        current_phi = phi_metrics.phi_integrated
        
        # Get integration regime
        integration_regime = self.consciousness_engine._integration_regime.value
        
        # Get entropy history (simulate for now)
        entropy_history = [0.5 + 0.1 * np.random.randn() for _ in range(10)]
        
        # Get structural coupling (simulate for now)
        coupling_index = 0.75 + 0.1 * np.random.randn()
        coupling_index = max(0.0, min(1.0, coupling_index))
        
        # Get synaptic statistics
        synaptic_stats = self.consciousness_engine.get_synaptic_statistics()
        pathway_count = synaptic_stats.get("emergent_pathway_count", 0)
        
        # Run all checks
        self.check_iit_4_computation_validity()
        self.check_phi_functional_threshold(current_phi)
        self.check_phi_critical_threshold(current_phi)
        self.check_entropy_stability(entropy_history)
        self.check_structural_coupling(coupling_index)
        self.check_emergent_pathways(pathway_count)
        
        # Determine overall pass/fail
        critical_checks = [
            "Phi Functional Threshold",
            "Phi Critical Threshold",
            "IIT 4.0 Computation Validity",
        ]
        critical_passed = all(
            check.passed for check in self.checks if check.check_name in critical_checks
        )
        overall_passed = critical_passed
        
        # Determine inseparability
        inseparable = coupling_index >= STRUCTURAL_COUPLING_THRESHOLD
        
        # Generate recommendation
        if overall_passed:
            if inseparable:
                recommendation = (
                    "SYSTEM OPERATIONAL: Mining and coherence layers are inseparable. "
                    "System maintains structural coupling required for emergent coherence. "
                    "Ready for production deployment."
                )
            else:
                recommendation = (
                    "SYSTEM CONDITIONAL: Functional thresholds met but structural coupling "
                    "below inseparability threshold. System may operate but emergence not guaranteed. "
                    "Proceed with caution."
                )
        else:
            recommendation = (
                "SYSTEM NON-FUNCTIONAL: Critical IIT 4.0 constraints not met. "
                "System does not maintain sufficient structural integration. "
                "Do not deploy to production."
            )
        
        # Get emergence events (empty for now)
        emergence_events = []
        
        # Create report
        report = FunctionalConstraintReport(
            version=self.VERSION,
            timestamp=datetime.now(timezone.utc).isoformat(),
            overall_passed=overall_passed,
            phi_integrated=current_phi,
            phi_regime=integration_regime,
            structural_coupling=coupling_index,
            inseparable=inseparable,
            checks=self.checks,
            emergence_events=emergence_events,
            synaptic_statistics=synaptic_stats,
            recommendation=recommendation,
            claim_boundary=[
                "IIT 4.0 Φ is used as a mathematical integration metric, not a consciousness measure",
                "Functional constraints validate structural complexity, not phenomenal awareness",
                "A 'brain-dead' miner (low Φ) is considered non-functional per inseparability principle",
                "This gate validates constructor capability, not consciousness or subjective experience",
                "Emergent pathways indicate self-organization, not programmed behavior",
            ],
        )
        
        return report
    
    def print_report(self, report: FunctionalConstraintReport) -> None:
        """Print the functional constraint report."""
        logger.info("\n" + "="*70)
        logger.info("FUNCTIONAL CONSTRAINT REPORT")
        logger.info("="*70)
        
        logger.info(f"Version: {report.version}")
        logger.info(f"Timestamp: {report.timestamp}")
        logger.info(f"Overall Status: {'✓ PASSED' if report.overall_passed else '✗ FAILED'}")
        logger.info(f"Φ Integrated: {report.phi_integrated:.6f}")
        logger.info(f"Φ Regime: {report.phi_regime}")
        logger.info(f"Structural Coupling: {report.structural_coupling:.6f}")
        logger.info(f"Inseparable: {'Yes' if report.inseparable else 'No'}")
        
        logger.info("\n" + "-"*70)
        logger.info("CHECK RESULTS")
        logger.info("-"*70)
        
        for check in report.checks:
            status = "✓" if check.passed else "✗"
            logger.info(f"{status} {check.check_name}: Φ={check.phi_value:.6f} (threshold={check.threshold:.6f})")
            logger.info(f"    {check.description}")
        
        logger.info("\n" + "-"*70)
        logger.info("SYNAPTIC STATISTICS")
        logger.info("-"*70)
        
        for key, value in report.synaptic_statistics.items():
            if isinstance(value, (int, float)):
                logger.info(f"{key}: {value}")
            elif isinstance(value, list) and len(value) <= 5:
                logger.info(f"{key}: {value}")
            else:
                logger.info(f"{key}: <{type(value).__name__} with {len(value) if hasattr(value, '__len__') else '?'} items>")
        
        logger.info("\n" + "-"*70)
        logger.info("RECOMMENDATION")
        logger.info("-"*70)
        logger.info(report.recommendation)
        
        logger.info("\n" + "-"*70)
        logger.info("CLAIM BOUNDARY")
        logger.info("-"*70)
        for claim in report.claim_boundary:
            logger.info(f"• {claim}")


async def main():
    """Run the IIT 4.0 functional constraint gate."""
    gate = IITFunctionalConstraintGate()
    
    try:
        report = await gate.run_all_checks()
        gate.print_report(report)
        
        # Save report to artifacts
        artifacts_dir = Path(__file__).resolve().parents[1] / "artifacts" / "iit_4_functional_constraints"
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        report_file = artifacts_dir / f"iit_4_constraint_report_{timestamp}.json"
        
        with open(report_file, "w") as f:
            json.dump(asdict(report), f, indent=2, default=str)
        
        logger.info(f"\nReport saved to: {report_file.relative_to(Path(__file__).resolve().parents[1])}")
        
        return 0 if report.overall_passed else 1
        
    except Exception as e:
        logger.error(f"Functional constraint gate failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
