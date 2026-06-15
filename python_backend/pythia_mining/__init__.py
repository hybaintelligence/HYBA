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

_ORCHESTRATOR_EXPORTS = {
    "PhiCoreOrchestrator",
    "PhiOrchestratorFactory",
    "PhiTelemetry",
    "PhiExecutionCycle",
}

_TUNER_EXPORTS = {
    "PhiTuner",
    "PhiBackpropTuner",
    "PhiSystemController",
    "PhiALUHardwareTuner",
}

_NETWORK_EXPORTS = {
    "PhiNetworkRouter",
    "GOLDEN_ANGLE",
}

_ORACLE_EXPORTS = {
    "PhiOracle",
    "PhiSystemControllerEnhanced",
}

_VM_EXPORTS = {
    "PhiVM",
    "search_optimization_kernel",
    "PHIMUL",
    "FOLD",
    "GADDR",
    "PMOD",
    "JPH",
    "SYNC_PHI",
    "MGATE",
    "TUNE",
}

_JIT_EXPORTS = {
    "PhiJIT",
    "resonant",
    "mining_kernel_template",
}

_MALLOC_EXPORTS = {
    "PhiBlock",
    "PhiMalloc",
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
        if name in {
            "CoherenceClassification",
            "ManifoldConfig",
            "ManifoldOperator",
            "ManifoldState",
            "OperatorEvolution",
        }:
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
    if name in _ORCHESTRATOR_EXPORTS:
        module = import_module(".phi_core_orchestrator", __name__)
        return getattr(module, name)
    if name in _TUNER_EXPORTS:
        module = import_module(".phi_tuner", __name__)
        return getattr(module, name)
    if name in _NETWORK_EXPORTS:
        module = import_module(".phi_network_router", __name__)
        return getattr(module, name)
    if name in _ORACLE_EXPORTS:
        module = import_module(".phi_oracle", __name__)
        return getattr(module, name)
    if name in _VM_EXPORTS:
        module = import_module(".phi_vm", __name__)
        return getattr(module, name)
    if name in _JIT_EXPORTS:
        module = import_module(".phi_jit", __name__)
        return getattr(module, name)
    if name in _MALLOC_EXPORTS:
        module = import_module(".phi_malloc", __name__)
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = sorted(
    _AUTONOMICS_EXPORTS
    | _OPERATOR_EXPORTS
    | _ORCHESTRATOR_EXPORTS
    | _TUNER_EXPORTS
    | _NETWORK_EXPORTS
    | _ORACLE_EXPORTS
    | _VM_EXPORTS
    | _JIT_EXPORTS
    | _MALLOC_EXPORTS
)
