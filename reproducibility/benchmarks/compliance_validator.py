#!/usr/bin/env python3
"""Multi-framework compliance validation."""

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List


class ComplianceValidator:
    """Multi-framework compliance verification."""

    FRAMEWORKS = {
        "SOC2": ["availability", "security", "confidentiality", "integrity"],
        "ISO27001": ["information_security", "risk_management", "audit"],
        "GDPR": ["data_protection", "consent", "right_to_be_forgotten"],
        "HIPAA": ["privacy", "security", "breach_notification"],
        "FedRAMP": ["cloud_security", "compliance", "continuous_monitoring"],
    }

    def validate_framework(self, framework: str, components: Iterable[str]) -> Dict[str, Any]:
        """Validate supplied components against a compliance framework."""
        if framework not in self.FRAMEWORKS:
            raise ValueError(f"Unsupported framework: {framework}")
        provided = set(components)
        required = set(self.FRAMEWORKS[framework])
        missing = sorted(required - provided)
        coverage = (len(required) - len(missing)) / len(required) if required else 1.0
        return {
            "framework": framework,
            "status": "compliant" if not missing else "gap",
            "coverage": coverage,
            "required": sorted(required),
            "missing": missing,
            "validated_at": datetime.now(timezone.utc).isoformat(),
        }

    def generate_compliance_report(self, frameworks: Dict[str, Iterable[str]]) -> Dict[str, Any]:
        """Generate executive compliance summary."""
        results = {name: self.validate_framework(name, comps) for name, comps in frameworks.items()}
        avg = sum(r["coverage"] for r in results.values()) / len(results) if results else 0.0
        return {
            "overall_status": (
                "compliant"
                if all(r["status"] == "compliant" for r in results.values())
                else "action_required"
            ),
            "average_coverage": avg,
            "frameworks": results,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
