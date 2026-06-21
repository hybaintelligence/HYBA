"""PYTHIA mining package exports.

The package initializer remains lightweight: PULVINI autonomics uses NumPy, so
symbols are resolved lazily to avoid importing heavy numerical dependencies when
callers only need non-autonomic package metadata.

The Stratum submission firewall is intentionally installed at package-import
scope. It is a small runtime safety seam, not a search/autonomy throttle: PYTHIA
continues to own search, healing, optimisation, and learning, while the immutable
verifier firewall owns the final pre-submit boundary.
"""

from __future__ import annotations

import os
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

_PYTHIA_AUTONOMOUS_MINING_EXPORTS = {
    "HashVerifier",
    "MiningChainState",
    "PythiaAutonomousMiningAgent",
    "PythiaMiningObservation",
    "PythiaMiningPlan",
    "PythiaPersistentMiningMemory",
    "PythiaSearchSeed",
    "ShareSubmitter",
}

_AUTONOMOUS_SEARCH_EXPORTS = {
    "AutonomousSearchSystem",
    "create_autonomous_search_system",
    "SearchMode",
    "SearchPhase",
    "UnifiedSearchResult",
    "SearchBenchmarkResult",
    "GroverAmplifier",
    "StructurePrior",
    "MemoryCompressor",
    "PhiScaler",
    "ManifoldRouter",
    "HealingCoordinator",
}

_REPLAY_REPORTING_EXPORTS = {
    "VerificationReport",
    "build_verification_report",
    "unified_text_diff",
    "write_report_html",
    "write_report_json",
}

_MANIFEST_REGISTRY_EXPORTS = {
    "RegistryRecord",
    "ReverificationResult",
    "list_claims",
    "load_and_reverify",
    "load_manifest",
    "save_verified_manifest",
}

_AUTO_ATTESTER_EXPORTS = {
    "AutoAttestedMiningManifest",
    "DEFAULT_MINING_BOUNDARIES",
    "emit_attested_mining_success_manifest",
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


def _live_or_production_mode() -> bool:
    return (
        os.getenv("HYBA_ENV", "").strip().lower() == "production"
        or os.getenv("NODE_ENV", "").strip().lower() == "production"
        or os.getenv("HYBA_ENABLE_LIVE_STRATUM", "").strip().lower() in {"1", "true", "yes", "on"}
    )


def _install_runtime_firewalls() -> None:
    """Install small runtime invariants that must sit outside optimisation."""

    try:
        from .stratum_submission_firewall import install_stratum_submit_firewall

        install_stratum_submit_firewall()
    except Exception:
        # General metadata tooling should not crash on optional import shape, but
        # live/prod mining must fail closed rather than continue without the
        # pre-submit verification firewall.
        if _live_or_production_mode():
            raise

    # Post-install integrity assertion: the firewall must be the active submit
    # path. If the install succeeded but the wrapper was subsequently replaced
    # (monkey-patch, mock leak, dynamic reassignment), refuse to continue in
    # production/live mode.
    try:
        from .stratum_submission_firewall import verify_stratum_firewall_integrity

        if _live_or_production_mode() and not verify_stratum_firewall_integrity():
            raise RuntimeError(
                "post_install_firewall_integrity_check_failed: "
                "submit_validated_share is not wrapped"
            )
    except Exception:
        if _live_or_production_mode():
            raise


_install_runtime_firewalls()


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
    if name in _REPLAY_REPORTING_EXPORTS:
        module = import_module(".replay_reporting", __name__)
        return getattr(module, name)
    if name in _MANIFEST_REGISTRY_EXPORTS:
        module = import_module(".manifest_registry", __name__)
        return getattr(module, name)
    if name in _AUTO_ATTESTER_EXPORTS:
        module = import_module(".mining_auto_attester", __name__)
        return getattr(module, name)
    if name in _AUTONOMICS_EXPORTS:
        pulvini_autonomics = import_module(".pulvini_autonomics", __name__)
        return getattr(pulvini_autonomics, name)
    if name in _PYTHIA_AUTONOMOUS_MINING_EXPORTS:
        module = import_module(".pythia_autonomous_mining_agent", __name__)
        return getattr(module, name)
    if name in _AUTONOMOUS_SEARCH_EXPORTS:
        module = import_module(".autonomous_searching_system", __name__)
        return getattr(module, name)
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
    elif name in _VM_EXPORTS:
        module = import_module(".phi_vm", __name__)
    elif name in _JIT_EXPORTS:
        module = import_module(".phi_jit", __name__)
    elif name in _MALLOC_EXPORTS:
        module = import_module(".phi_malloc", __name__)
    else:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    return getattr(module, name)


__all__ = sorted(
    _REPLAY_REPORTING_EXPORTS
    | _MANIFEST_REGISTRY_EXPORTS
    | _AUTO_ATTESTER_EXPORTS
    | _AUTONOMICS_EXPORTS
    | _OPERATOR_EXPORTS
    | _ORCHESTRATOR_EXPORTS
    | _TUNER_EXPORTS
    | _NETWORK_EXPORTS
    | _ORACLE_EXPORTS
    | _VM_EXPORTS
    | _JIT_EXPORTS
    | _MALLOC_EXPORTS
    | _PYTHIA_AUTONOMOUS_MINING_EXPORTS
    | _AUTONOMOUS_SEARCH_EXPORTS
)
