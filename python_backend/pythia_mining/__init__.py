"""PYTHIA mining package exports.

The package initializer remains lightweight: PULVINI autonomics uses NumPy, so
symbols are resolved lazily to avoid importing heavy numerical dependencies when
callers only need non-autonomic package metadata.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_OPERATOR_EXPORTS = {
    "ConsciousnessConfig",
    "ConsciousnessEngine",
    "CoherenceClassification",
    "ConsciousnessState",
    "IntegrationRegime",
    "IntegrityStatus",
    "ManifoldConfig",
    "ManifoldOperator",
    "ManifoldState",
    "OperatorEvolution",
    "PhiMetrics",
    "PULVINI_BINARY_HEADER_SIZE",
    "PULVINI_BINARY_MAGIC",
    "SubstateBinaryHeader",
    "SubstatePassport",
    "SubstateVerifier",
}

_AUTONOMICS_EXPORTS = {
    "AutonomicOrchestrator",
    "BuresOptimizer",
    "DodecahedronIcosahedronCompound",
    "GeometricRebalancer",
    "ManifoldHomeostasis",
    "NodeTelemetry",
    "NodeType",
    "PulviniAutonomicsEngine",
    "RebalanceEvent",
    "ReducedDensityMatrix",
    "ThermalNodeState",
    "ThermalGovernor",
    "ThermalGovernanceEvent",
}


def __getattr__(name: str) -> Any:
    if name in _OPERATOR_EXPORTS:
        if name in {"CoherenceClassification", "ManifoldConfig", "ManifoldOperator", "ManifoldState", "OperatorEvolution"}:
            module = import_module(".pulvini_operator", __name__)
        elif name in {
            "IntegrityStatus",
            "PULVINI_BINARY_HEADER_SIZE",
            "PULVINI_BINARY_MAGIC",
            "SubstateBinaryHeader",
            "SubstatePassport",
            "SubstateVerifier",
        }:
            module = import_module(".pulvini_verifier", __name__)
        else:
            module = import_module(".consciousness_engine", __name__)
        return getattr(module, name)
    if name in _AUTONOMICS_EXPORTS:
        pulvini_autonomics = import_module(".pulvini_autonomics", __name__)
        return getattr(pulvini_autonomics, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = sorted(_AUTONOMICS_EXPORTS | _OPERATOR_EXPORTS)
