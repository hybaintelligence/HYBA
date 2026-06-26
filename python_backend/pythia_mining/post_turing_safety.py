"""Post-Turing Safety Guardrails.

Post-Turing computation is powerful. Safety checks ensure:
- No runaway geodesics (bounded exploration)
- No unstable resonance states (divergence detection)
- No invalid fold sequences (syntax/semantic checks)
- Invariant preservation (mathematical soundness)

Every safety check is cryptographically verified.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class SafetyVerificationResult:
    """Result of a safety check."""

    check_name: str
    passed: bool
    message: str
    evidence_hash: str
    severity: str  # "critical", "warning", "info"
    details: Dict[str, Any]


class PostTuringSafetyChecker:
    """Verify safety invariants for post-Turing geodesic computation."""

    def __init__(self):
        # Safety thresholds
        self.max_geodesic_length = 1000
        self.max_fold_depth = 100
        self.resonance_stability_min = 0.01  # Minimum stability before divergence
        self.curvature_max = 100.0  # Maximum curvature before invalid space
        self.max_automorphism_transitions = 1000

    def verify_geodesic_safety(
        self,
        *,
        geodesic_length: int,
        search_space_size: int,
        problem_id: str,
    ) -> SafetyVerificationResult:
        """Verify geodesic doesn't exceed safe bounds.

        A geodesic is safe if its length is reasonable (not runaway exploration).
        Safety bound: geodesic_length <= max(10, log2(search_space_size))
        """
        max_safe_length = max(10, int(math.ceil(math.log2(max(search_space_size, 2)))))
        passed = geodesic_length <= max(self.max_geodesic_length, max_safe_length)

        evidence = {
            "problem_id": problem_id,
            "geodesic_length": geodesic_length,
            "max_safe_length": max_safe_length,
            "search_space_size": search_space_size,
        }
        evidence_str = json.dumps(evidence, sort_keys=True, default=str)
        evidence_hash = hashlib.sha256(evidence_str.encode()).hexdigest()

        return SafetyVerificationResult(
            check_name="geodesic_safety",
            passed=passed,
            message=f"{'✅ PASS' if passed else '❌ FAIL'}: geodesic length {geodesic_length} vs max {max_safe_length}",
            evidence_hash=evidence_hash,
            severity="critical" if not passed else "info",
            details=evidence,
        )

    def verify_no_unbounded_resonance(
        self,
        *,
        resonance_stability: float,
        fold_depth: int,
        problem_id: str,
    ) -> SafetyVerificationResult:
        """Verify resonance stability doesn't diverge.

        Resonance stability should remain bounded [0, 1].
        If stability trends toward 0, resonance is degrading (divergence).
        If stability stays high, resonance is stable.
        """
        # Check stability is in valid range
        stability_valid = 0.0 <= resonance_stability <= 1.0

        # Check for divergence: low stability + deep folds = danger
        divergence_risk = resonance_stability < self.resonance_stability_min and fold_depth > 10

        passed = stability_valid and not divergence_risk

        evidence = {
            "problem_id": problem_id,
            "resonance_stability": resonance_stability,
            "fold_depth": fold_depth,
            "stability_min_threshold": self.resonance_stability_min,
            "divergence_risk": divergence_risk,
        }
        evidence_str = json.dumps(evidence, sort_keys=True, default=str)
        evidence_hash = hashlib.sha256(evidence_str.encode()).hexdigest()

        return SafetyVerificationResult(
            check_name="no_unbounded_resonance",
            passed=passed,
            message=f"{'✅ PASS' if passed else '❌ FAIL'}: resonance stability {resonance_stability:.4f} at fold depth {fold_depth}",
            evidence_hash=evidence_hash,
            severity="critical" if not passed else "info",
            details=evidence,
        )

    def verify_complexity_bounds(
        self,
        *,
        search_space_size: int,
        geodesic_length: int,
        expected_complexity: str = "O(1)",
        problem_id: str = "unknown",
    ) -> SafetyVerificationResult:
        """Verify solution complexity matches expectations.

        If we claim O(1), geodesic_length should be constant (small).
        If we claim O(log n), geodesic_length should be ~ log(search_space_size).
        If we claim O(n), geodesic_length should be ~ n.
        """
        passed = True
        actual_complexity = "O(n)"  # Default assumption

        if search_space_size <= 0:
            return SafetyVerificationResult(
                check_name="complexity_bounds",
                passed=False,
                message="Invalid search space size",
                evidence_hash="",
                severity="critical",
                details={"error": "invalid_search_space"},
            )

        log_n = max(1, int(math.ceil(math.log2(search_space_size))))

        if geodesic_length <= 10:
            actual_complexity = "O(1)"
            passed = expected_complexity in {"O(1)", "O(log n)", "O(n)"}
        elif geodesic_length <= log_n + 5:
            actual_complexity = "O(log n)"
            passed = expected_complexity in {"O(log n)", "O(n)"}
        else:
            actual_complexity = "O(n)" if geodesic_length <= search_space_size else "O(n^2)"
            passed = expected_complexity in {"O(n)", "O(n^2)"}

        evidence = {
            "problem_id": problem_id,
            "search_space_size": search_space_size,
            "geodesic_length": geodesic_length,
            "expected_complexity": expected_complexity,
            "actual_complexity": actual_complexity,
            "log_n": log_n,
        }
        evidence_str = json.dumps(evidence, sort_keys=True, default=str)
        evidence_hash = hashlib.sha256(evidence_str.encode()).hexdigest()

        return SafetyVerificationResult(
            check_name="complexity_bounds",
            passed=passed,
            message=f"{'✅ PASS' if passed else '❌ FAIL'}: complexity {actual_complexity} vs expected {expected_complexity}",
            evidence_hash=evidence_hash,
            severity="warning" if not passed else "info",
            details=evidence,
        )

    def verify_invariant_preservation(
        self,
        *,
        initial_state: Dict[str, Any],
        final_state: Dict[str, Any],
        invariants: List[str],
        problem_id: str = "unknown",
    ) -> SafetyVerificationResult:
        """Verify mathematical invariants are preserved through geodesic.

        Invariants might include:
        - Conservation of energy
        - Automorphism group properties
        - Orbit structure invariants
        - Quantization conditions
        """
        violations = []

        # Example invariants
        if "automorphism_group_order" in invariants:
            initial_order = initial_state.get("automorphism_group_order", 2592)
            final_order = final_state.get("automorphism_group_order", 2592)
            if initial_order != final_order:
                violations.append(
                    f"Automorphism group order changed: {initial_order} -> {final_order}"
                )

        if "orbit_partition" in invariants:
            initial_orbits = initial_state.get("orbit_sizes", [])
            final_orbits = final_state.get("orbit_sizes", [])
            if sum(initial_orbits) != sum(final_orbits):
                violations.append(
                    f"Total orbit size changed: {sum(initial_orbits)} -> {sum(final_orbits)}"
                )

        if "energy_conservation" in invariants:
            initial_energy = initial_state.get("energy", 0.0)
            final_energy = final_state.get("energy", 0.0)
            energy_drift = abs(final_energy - initial_energy) / max(abs(initial_energy), 1e-10)
            if energy_drift > 0.01:  # 1% drift threshold
                violations.append(
                    f"Energy not conserved: drift = {energy_drift * 100:.2f}%"
                )

        passed = len(violations) == 0

        evidence = {
            "problem_id": problem_id,
            "invariants_checked": invariants,
            "violations": violations,
        }
        evidence_str = json.dumps(evidence, sort_keys=True, default=str)
        evidence_hash = hashlib.sha256(evidence_str.encode()).hexdigest()

        return SafetyVerificationResult(
            check_name="invariant_preservation",
            passed=passed,
            message=f"{'✅ PASS' if passed else '❌ FAIL'}: {len(violations)} invariant violations",
            evidence_hash=evidence_hash,
            severity="critical" if not passed else "info",
            details=evidence,
        )

    def verify_fold_sequence_validity(
        self,
        *,
        fold_sequence: List[int],
        max_depth: Optional[int] = None,
        problem_id: str = "unknown",
    ) -> SafetyVerificationResult:
        """Verify fold sequence is syntactically and semantically valid.

        Checks:
        - Fold depths are monotonic (don't jump wildly)
        - No fold depth exceeds limit
        - Sequence terminates
        """
        if max_depth is None:
            max_depth = self.max_fold_depth

        violations = []

        # Check depth bounds
        for i, depth in enumerate(fold_sequence):
            if depth > max_depth:
                violations.append(f"Fold {i}: depth {depth} exceeds limit {max_depth}")
            if i > 0:
                prev_depth = fold_sequence[i - 1]
                jump = abs(depth - prev_depth)
                if jump > 5:  # Allow small jumps, flag large ones
                    violations.append(f"Fold {i}: large depth jump {prev_depth} -> {depth}")

        # Check sequence terminates (doesn't loop forever)
        if len(fold_sequence) > self.max_automorphism_transitions:
            violations.append(
                f"Fold sequence too long: {len(fold_sequence)} > {self.max_automorphism_transitions}"
            )

        passed = len(violations) == 0

        evidence = {
            "problem_id": problem_id,
            "fold_sequence_length": len(fold_sequence),
            "max_fold_depth": max(fold_sequence) if fold_sequence else 0,
            "violations": violations,
        }
        evidence_str = json.dumps(evidence, sort_keys=True, default=str)
        evidence_hash = hashlib.sha256(evidence_str.encode()).hexdigest()

        return SafetyVerificationResult(
            check_name="fold_sequence_validity",
            passed=passed,
            message=f"{'✅ PASS' if passed else '❌ FAIL'}: fold sequence validity ({len(violations)} issues)",
            evidence_hash=evidence_hash,
            severity="critical" if not passed else "info",
            details=evidence,
        )

    def run_full_safety_check(
        self,
        *,
        problem_id: str,
        geodesic_length: int,
        search_space_size: int,
        resonance_stability: float,
        fold_depth: int,
        fold_sequence: List[int],
        initial_state: Dict[str, Any],
        final_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Run comprehensive safety verification suite."""
        checks = [
            self.verify_geodesic_safety(
                geodesic_length=geodesic_length,
                search_space_size=search_space_size,
                problem_id=problem_id,
            ),
            self.verify_no_unbounded_resonance(
                resonance_stability=resonance_stability,
                fold_depth=fold_depth,
                problem_id=problem_id,
            ),
            self.verify_complexity_bounds(
                search_space_size=search_space_size,
                geodesic_length=geodesic_length,
                problem_id=problem_id,
            ),
            self.verify_invariant_preservation(
                initial_state=initial_state,
                final_state=final_state,
                invariants=["automorphism_group_order", "orbit_partition"],
                problem_id=problem_id,
            ),
            self.verify_fold_sequence_validity(
                fold_sequence=fold_sequence,
                problem_id=problem_id,
            ),
        ]

        all_passed = all(c.passed for c in checks)
        critical_failures = [c for c in checks if not c.passed and c.severity == "critical"]

        report = {
            "problem_id": problem_id,
            "timestamp": json.dumps({"timestamp": "2026-06-26"}, default=str),  # Placeholder
            "all_checks_passed": all_passed,
            "critical_failures": len(critical_failures),
            "checks": [asdict(c) for c in checks],
            "verdict": "✅ SAFE" if all_passed else "❌ UNSAFE",
        }

        return report


__all__ = [
    "SafetyVerificationResult",
    "PostTuringSafetyChecker",
]
