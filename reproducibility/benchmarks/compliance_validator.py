#!/usr/bin/env python3
"""Multi-framework compliance validation."""
from __future__ import annotations
from typing import Any, Dict, Iterable

class ComplianceValidator:
    FRAMEWORKS={"SOC2":["availability","security","confidentiality","integrity"],"ISO27001":["information_security","risk_management","audit"],"GDPR":["data_protection","consent","right_to_be_forgotten"],"HIPAA":["privacy","security","breach_notification"],"FedRAMP":["cloud_security","compliance","continuous_monitoring"]}
    def validate_framework(self, framework: str, components: Dict[str, Any] | Iterable[str]) -> Dict[str, Any]:
        if framework not in self.FRAMEWORKS: raise ValueError(f"unknown framework: {framework}")
        available=set(components.keys() if isinstance(components, dict) else components); required=set(self.FRAMEWORKS[framework]); missing=sorted(required-available)
        return {"framework":framework,"required":sorted(required),"implemented":sorted(required & available),"missing":missing,"score":(len(required)-len(missing))/len(required),"compliant":not missing}
    def generate_compliance_report(self, frameworks: Iterable[str], components: Dict[str, Any] | Iterable[str]) -> Dict[str, Any]:
        results={fw:self.validate_framework(fw, components) for fw in frameworks}
        return {"frameworks":results,"overall_score":sum(r["score"] for r in results.values())/len(results) if results else 0,"compliant":all(r["compliant"] for r in results.values())}
