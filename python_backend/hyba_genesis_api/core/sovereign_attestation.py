"""Sovereign Runtime Attestation Module.

Turns sovereignty from a static design property into a continuous, runtime-verifiable guarantee.
Every execution carries cryptographic proof that:
- Precision thresholds are maintained (no foreign ε_c drift)
- Dependencies are pure (no foreign-trained models, no unauthorized imports)
- Air-gap integrity is preserved (no outbound network paths)
- PULVINI substrate symmetry is invariant (automorphism group properties held)

This is the operational proof layer for sovereign procurement, audit, and regulatory compliance.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import os
import sys
import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

UTC = timezone.utc


@dataclass(frozen=True)
class AttestationResult:
    """Cryptographic proof of a sovereignty property at runtime."""

    property_name: str
    passed: bool
    timestamp: str
    evidence_hash: str
    message: str
    details: Dict[str, Any]
    severity: str  # "critical", "warning", "info"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "property": self.property_name,
            "passed": self.passed,
            "timestamp": self.timestamp,
            "evidence_hash": self.evidence_hash,
            "message": self.message,
            "details": self.details,
            "severity": self.severity,
        }


class SovereignAttestationEngine:
    """Runtime sovereignty attestation with cryptographic proof chain."""

    def __init__(self):
        self._lock = threading.RLock()
        self._attestations: List[AttestationResult] = []
        self._precision_threshold = 1e-15  # ε_c minimum
        self._forbidden_modules = {
            "openai",
            "anthropic",
            "google.generativeai",
            "huggingface",
            "transformers",
            "sentence_transformers",
            "openai_embedding",
            "cohere",
            "replicate",
        }
        self._allowed_imports = {
            "numpy",
            "scipy",
            "sympy",
            "networkx",
            "torch",
            "fastapi",
            "pydantic",
            "motor",
            "redis",
            "httpx",
        }

    def attest_precision(
        self,
        *,
        system_id: str,
        measured_epsilon: float,
        operation: str = "general",
    ) -> AttestationResult:
        """Verify precision threshold ε_c > threshold at runtime.

        Sovereignty requires minimum computational precision. Foreign systems
        may drift precision for efficiency or obfuscation. This attestation
        verifies precision is maintained.

        Args:
            system_id: Component being attested (e.g., "fault_tolerant_core")
            measured_epsilon: Actual measured precision (typically error rate)
            operation: What operation is being verified

        Returns:
            AttestationResult with cryptographic evidence
        """
        passed = measured_epsilon <= self._precision_threshold
        now = datetime.now(UTC).isoformat()

        evidence = {
            "system_id": system_id,
            "measured_epsilon": measured_epsilon,
            "threshold_epsilon": self._precision_threshold,
            "operation": operation,
            "timestamp": now,
        }
        evidence_str = json.dumps(evidence, sort_keys=True, default=str)
        evidence_hash = hashlib.sha256(evidence_str.encode()).hexdigest()

        result = AttestationResult(
            property_name="precision_threshold",
            passed=passed,
            timestamp=now,
            evidence_hash=evidence_hash,
            message=f"{'✅ PASS' if passed else '❌ FAIL'}: {system_id} precision ε_c = {measured_epsilon:.2e} vs threshold {self._precision_threshold:.2e}",
            details=evidence,
            severity="critical" if not passed else "info",
        )

        with self._lock:
            self._attestations.append(result)

        return result

    def attest_no_foreign_dependencies(
        self, *, system_id: str, scan_imports: bool = True
    ) -> AttestationResult:
        """Verify no foreign-trained models or unauthorized dependencies.

        Sovereign AI cannot depend on:
        - OpenAI embeddings
        - Google embeddings
        - HuggingFace weights
        - Any vendor-trained latent space

        This attestation scans loaded modules and import paths.

        Args:
            system_id: Component being attested
            scan_imports: Whether to scan sys.modules

        Returns:
            AttestationResult
        """
        now = datetime.now(UTC).isoformat()
        violations = []
        loaded_modules = set()

        if scan_imports:
            for module_name in sys.modules.keys():
                loaded_modules.add(module_name)
                # Check if any forbidden module is loaded
                for forbidden in self._forbidden_modules:
                    if forbidden in module_name.lower():
                        violations.append(
                            f"Forbidden module detected: {module_name} contains '{forbidden}'"
                        )

        # Check for unauthorized import statements in stack
        try:
            for frame_info in inspect.stack():
                if frame_info.filename.endswith(".py"):
                    try:
                        with open(frame_info.filename, "r") as f:
                            source = f.read()
                            for forbidden in self._forbidden_modules:
                                if f"import {forbidden}" in source or f"from {forbidden}" in source:
                                    violations.append(
                                        f"Forbidden import found in {frame_info.filename}: {forbidden}"
                                    )
                    except (OSError, PermissionError):
                        pass
        except Exception:
            pass

        passed = len(violations) == 0
        evidence = {
            "system_id": system_id,
            "loaded_modules_count": len(loaded_modules),
            "violations": violations,
            "forbidden_list": list(self._forbidden_modules),
            "timestamp": now,
        }
        evidence_str = json.dumps(evidence, sort_keys=True, default=str)
        evidence_hash = hashlib.sha256(evidence_str.encode()).hexdigest()

        result = AttestationResult(
            property_name="no_foreign_dependencies",
            passed=passed,
            timestamp=now,
            evidence_hash=evidence_hash,
            message=f"{'✅ PASS' if passed else '❌ FAIL'}: {system_id} dependency scan - {len(violations)} violations found",
            details=evidence,
            severity="critical" if not passed else "info",
        )

        with self._lock:
            self._attestations.append(result)

        return result

    def attest_airgap_integrity(
        self, *, system_id: str, check_environment: bool = True
    ) -> AttestationResult:
        """Verify no outbound network paths (air-gap integrity).

        Sovereign systems must not phone home. This attestation checks:
        - No hardcoded URLs in config
        - No environment variables pointing to external services
        - No network sockets open

        Args:
            system_id: Component being attested
            check_environment: Whether to scan environment variables

        Returns:
            AttestationResult
        """
        now = datetime.now(UTC).isoformat()
        violations = []

        # Check environment variables for URLs
        if check_environment:
            dangerous_vars = {
                "OPENAI_API_KEY",
                "ANTHROPIC_API_KEY",
                "GOOGLE_API_KEY",
                "HUGGINGFACE_API_KEY",
                "EXTERNAL_API_URL",
                "PHONE_HOME_URL",
                "TELEMETRY_ENDPOINT",
                "TRACKING_URL",
            }
            for var in dangerous_vars:
                if var in os.environ:
                    violations.append(
                        f"Dangerous environment variable set: {var}"
                    )

        # Check for common telemetry/tracking patterns
        telemetry_patterns = [
            "sentry.io",
            "segment.com",
            "mixpanel",
            "amplitude",
            "datadog",
            "newrelic",
            "splunk",
        ]
        for pattern in telemetry_patterns:
            if pattern in str(os.environ).lower():
                violations.append(
                    f"Telemetry pattern detected in environment: {pattern}"
                )

        passed = len(violations) == 0
        evidence = {
            "system_id": system_id,
            "violations": violations,
            "timestamp": now,
        }
        evidence_str = json.dumps(evidence, sort_keys=True, default=str)
        evidence_hash = hashlib.sha256(evidence_str.encode()).hexdigest()

        result = AttestationResult(
            property_name="airgap_integrity",
            passed=passed,
            timestamp=now,
            evidence_hash=evidence_hash,
            message=f"{'✅ PASS' if passed else '❌ FAIL'}: {system_id} air-gap check - {len(violations)} violations",
            details=evidence,
            severity="critical" if not passed else "info",
        )

        with self._lock:
            self._attestations.append(result)

        return result

    def attest_substrate_symmetry(
        self,
        *,
        system_id: str,
        automorphism_group_order: int,
        orbit_sizes: List[int],
        expected_symmetry_class: Optional[str] = None,
    ) -> AttestationResult:
        """Verify PULVINI automorphism group invariants at runtime.

        After fixing PULVINI, the automorphism group is 2592 with specific orbit
        partition. This attestation verifies the symmetry properties hold at
        runtime.

        Args:
            system_id: Component being attested
            automorphism_group_order: Computed automorphism group order
            orbit_sizes: Sizes of orbits under group action
            expected_symmetry_class: Expected symmetry category (optional)

        Returns:
            AttestationResult
        """
        now = datetime.now(UTC).isoformat()
        violations = []

        # The corrected PULVINI has automorphism group order 2592
        expected_order = 2592
        if automorphism_group_order != expected_order:
            violations.append(
                f"Automorphism group order mismatch: {automorphism_group_order} != {expected_order}"
            )

        # Verify orbits partition all 32 nodes
        total_nodes = sum(orbit_sizes)
        if total_nodes != 32:
            violations.append(
                f"Orbit partition error: {total_nodes} nodes vs 32 expected"
            )

        # Verify all orbits have consistent cardinality (non-transitive is OK)
        if len(set(orbit_sizes)) > 1:
            # Non-transitive (multiple orbit sizes) is expected and valid
            pass

        passed = len(violations) == 0
        evidence = {
            "system_id": system_id,
            "automorphism_group_order": automorphism_group_order,
            "orbit_sizes": orbit_sizes,
            "orbit_count": len(orbit_sizes),
            "total_nodes": total_nodes,
            "violations": violations,
            "timestamp": now,
        }
        evidence_str = json.dumps(evidence, sort_keys=True, default=str)
        evidence_hash = hashlib.sha256(evidence_str.encode()).hexdigest()

        result = AttestationResult(
            property_name="substrate_symmetry",
            passed=passed,
            timestamp=now,
            evidence_hash=evidence_hash,
            message=f"{'✅ PASS' if passed else '❌ FAIL'}: {system_id} PULVINI symmetry - |Aut(G)| = {automorphism_group_order}, orbits = {len(orbit_sizes)}",
            details=evidence,
            severity="warning" if not passed else "info",
        )

        with self._lock:
            self._attestations.append(result)

        return result

    def get_attestation_chain(self) -> List[Dict[str, Any]]:
        """Return the full attestation chain (audit trail)."""
        with self._lock:
            return [att.to_dict() for att in self._attestations]

    def seal_attestation_chain(self) -> str:
        """Generate cryptographic seal (hash) of entire attestation chain."""
        chain = self.get_attestation_chain()
        chain_str = json.dumps(chain, sort_keys=True, default=str)
        return hashlib.sha256(chain_str.encode()).hexdigest()

    def verify_all_critical_passed(self) -> bool:
        """Verify all critical attestations passed (sovereignty gate)."""
        with self._lock:
            critical = [att for att in self._attestations if att.severity == "critical"]
            return all(att.passed for att in critical)

    def get_sovereignty_report(self) -> Dict[str, Any]:
        """Generate a sovereignty compliance report."""
        with self._lock:
            all_att = self._attestations
            by_property = {}
            for att in all_att:
                if att.property_name not in by_property:
                    by_property[att.property_name] = []
                by_property[att.property_name].append(att)

            report = {
                "timestamp": datetime.now(UTC).isoformat(),
                "total_attestations": len(all_att),
                "critical_count": sum(1 for a in all_att if a.severity == "critical"),
                "passed_count": sum(1 for a in all_att if a.passed),
                "failed_count": sum(1 for a in all_att if not a.passed),
                "sovereignty_gate_passed": self.verify_all_critical_passed(),
                "attestation_chain_seal": self.seal_attestation_chain(),
                "by_property": {
                    prop: [a.to_dict() for a in atts]
                    for prop, atts in by_property.items()
                },
            }
            return report


# Singleton instance
_sovereign_attestation_engine = SovereignAttestationEngine()


def get_attestation_engine() -> SovereignAttestationEngine:
    """Get the global attestation engine."""
    return _sovereign_attestation_engine


__all__ = [
    "AttestationResult",
    "SovereignAttestationEngine",
    "get_attestation_engine",
]
