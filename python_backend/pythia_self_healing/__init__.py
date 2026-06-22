"""Sovereign-gated Salamander self-healing subsystem.

This package turns codebase damage signals into sealed, auditable regeneration
proposals. It deliberately stages proposals only; it does not silently mutate
source files. The design complements ``pythia_mining.regeneration_manager``:
that module owns lane-level mathematical regeneration, while this package owns
codebase-level damage detection, proposal generation, prioritisation, memory,
algorithm discovery, cross-lane intelligence, predictive healing, rewiring,
benchmark evolution, Pulvini handshakes, and regulator-grade evidence.
"""

from .autonomic_organism_governor import (
    BenchmarkEvolutionEngine,
    CrossLaneRegenerationIntelligence,
    HierarchicalRewiringOrchestrator,
    PredictiveRegenerationEngine,
    RegulatorEvidenceEngine,
    SalamanderOrganismGovernor,
    TemporalRegenerationMemory,
)
from .autonomous_damage_detector import AutonomousDamageDetector, DamageReport
from .salamander_regenerator import RegenerationCandidate, SalamanderRegenerator
from .self_healing_reactor import SelfHealingReactor, create_healing_proposal

__all__ = [
    "AutonomousDamageDetector",
    "BenchmarkEvolutionEngine",
    "CrossLaneRegenerationIntelligence",
    "DamageReport",
    "HierarchicalRewiringOrchestrator",
    "PredictiveRegenerationEngine",
    "RegenerationCandidate",
    "RegulatorEvidenceEngine",
    "SalamanderOrganismGovernor",
    "SalamanderRegenerator",
    "SelfHealingReactor",
    "TemporalRegenerationMemory",
    "create_healing_proposal",
]
