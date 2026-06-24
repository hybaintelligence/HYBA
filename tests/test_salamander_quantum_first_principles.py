"""
Falsification tests for HYBA/Salamander quantum-first-principles and
emergent-intelligence theses.

These tests deliberately avoid proving a narrative by assertion. They encode
what can be checked in CI while respecting the project thesis being tested:

1. The quantum substrate can be expressed from first-principles mathematics
   rather than from an external quantum-SDK dependency.
2. CPU/GPU/Metal/CUDA-style execution backends are legitimate computational
   substrates. They are not synonymous with quantum, and they must be tested as
   execution/evidence surfaces rather than forbidden as claim sources.
3. Structural memory seeding is not dismissed as "only metadata". It is tested
   as a possible evidence surface for emergence when complexity, topology, and
   differentiated coupling are actually measured.
4. A bootstrap artifact that exposes self-optimisation infrastructure must not
   be misread as evidence that optimisation proposals were actually applied.
5. Intelligence/emergence claims must be topology- and complexity-dependent:
   the system may discover/measure emergent structure, but a bare declaration
   must not manufacture emergence.
6. Once emergence is detected, the system may enhance it by seeding knowledge
   substrates and bounded, reversible optimisation loops.

If these tests fail, the claim boundary has moved faster than the evidence
surface and the system needs repair before the claim is made externally.
"""

from __future__ import annotations

import ast
import importlib
import importlib.util
import json
import math
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_BACKEND = REPO_ROOT / "python_backend"
if str(PYTHON_BACKEND) not in sys.path:
    sys.path.insert(0, str(PYTHON_BACKEND))


PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV = 1.0 / PHI


PURE_MATH_SUBSTRATE_MODULES = [
    REPO_ROOT / "python_backend" / "pythia_mining" / "golden_ratio_library.py",
    REPO_ROOT / "python_backend" / "pythia_mining" / "hendrix_phi_solver.py",
    REPO_ROOT / "python_backend" / "pythia_mining" / "quantum_regeneration.py",
]

# These are external quantum SDK/framework dependencies. They are different
# from CPU, GPU, Metal, CUDA, MLX, NumPy, or other legitimate execution
# substrates.
FORBIDDEN_REQUIRED_QUANTUM_SDK_IMPORT_ROOTS = {
    "qiskit",
    "cirq",
    "braket",
}


def _import_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def _load_memory_seed_module():
    """Load scripts/seed_system_memory.py without requiring scripts to be a package."""
    script_path = REPO_ROOT / "scripts" / "seed_system_memory.py"
    spec = importlib.util.spec_from_file_location("seed_system_memory", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_phi_algebra_is_a_first_principles_invariant() -> None:
    """The base constant must satisfy the defining algebra, not a fixture value."""
    assert PHI > 1.0
    assert math.isclose(PHI * PHI, PHI + 1.0, rel_tol=0.0, abs_tol=1e-15)
    assert math.isclose(PHI_INV, PHI - 1.0, rel_tol=0.0, abs_tol=1e-15)
    assert math.isclose(PHI * PHI_INV, 1.0, rel_tol=0.0, abs_tol=1e-15)


@pytest.mark.parametrize("module_path", PURE_MATH_SUBSTRATE_MODULES)
def test_quantum_substrate_core_has_no_required_quantum_sdk_imports(module_path: Path) -> None:
    """Core substrate modules must not require external quantum SDK frameworks."""
    assert module_path.exists(), f"Missing expected substrate module: {module_path}"
    imported_roots = _import_roots(module_path)
    forbidden = imported_roots & FORBIDDEN_REQUIRED_QUANTUM_SDK_IMPORT_ROOTS
    assert forbidden == set(), (
        f"{module_path.relative_to(REPO_ROOT)} imports quantum SDK roots {sorted(forbidden)}. "
        "That would make the first-principles substrate depend on an external quantum framework."
    )


def test_computational_hardware_paths_are_first_class_execution_surfaces() -> None:
    """CPU/GPU/Metal/MLX are computation surfaces and must be tested, not forbidden."""
    hardware_gate = REPO_ROOT / "tests" / "test_apple_silicon_metal_gate.py"
    assert hardware_gate.exists(), "Expected Apple Silicon/MLX/Metal evidence tests to exist"

    source = hardware_gate.read_text(encoding="utf-8")
    assert "test_probe_verifies_fake_mlx_gpu_cpu_paths" in source
    assert "cpu_fallback_verified" in source
    assert "metal_path_verified" in source
    assert "absolute_delta" in source


def test_hardware_probe_degrades_cleanly_when_requested_backend_is_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing hardware should degrade honestly, not fabricate acceleration evidence."""
    apple_silicon_metal = importlib.import_module("pythia_mining.apple_silicon_metal")

    monkeypatch.setattr(apple_silicon_metal.platform, "system", lambda: "Linux")
    monkeypatch.setattr(apple_silicon_metal.platform, "machine", lambda: "x86_64")

    packet = apple_silicon_metal.probe_mlx_metal(matrix_size=8, require_mlx=False)

    assert packet["status"] == "unavailable"
    assert packet["apple_silicon_detected"] is False
    assert packet["mlx_available"] is False
    assert packet["metal_path_verified"] is False
    assert "hardware speedup claim" in packet["claim_boundary"]["not_supported"]


def test_memory_seed_is_evidence_surface_for_complexity_emergence_not_a_dead_boundary() -> None:
    """
    Memory seeding is allowed to move the boundary when it records measured
    complexity/topology rather than a bare label.

    This test intentionally does not freeze the older defensive wording that
    structural metrics can never support intelligence claims. The thesis under
    test is stronger: intelligence is not engineered by declaration, but can
    emerge from measured complexity and then become enhanceable.
    """
    seed_path = REPO_ROOT / "artifacts" / "memory_seed" / "memory_seed_v1.json"
    seed_script_path = REPO_ROOT / "scripts" / "seed_system_memory.py"

    seed = json.loads(seed_path.read_text(encoding="utf-8"))
    seed_script = seed_script_path.read_text(encoding="utf-8")

    metadata = seed["metadata"]
    structural = seed["structural_intelligence"]

    assert metadata["seed_source"] == "codebase_structural_analysis"
    assert metadata["total_nodes"] >= 1
    assert metadata["total_edges"] >= metadata["total_nodes"]
    assert metadata["emergent_intelligence_index"] > 0.0

    assert structural["knowledge_graph"]
    assert structural["emergent_patterns"]
    assert structural["hubs"]
    assert "STRUCTURAL METRICS" in seed_script
    assert "emergent_intelligence_index" in seed_script


def test_bootstrap_artifact_separates_self_optimisation_surface_from_applied_optimisation() -> None:
    """Self-optimising infrastructure must not be overstated as applied optimisation."""
    artifact_path = (
        REPO_ROOT
        / "artifacts"
        / "autonomous_mining"
        / "pythia_autonomous_bootstrap_latest.json"
    )
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))

    assert artifact["schema"] == "HYBA_PYTHIA_AUTONOMOUS_BOOTSTRAP_V2"
    assert "self_optimising" in artifact
    assert artifact["self_optimising"]["virtual_mining_simulation"] == (
        "deterministic_sha256d_hash_landscape"
    )

    reflexive = artifact["after"]["status"]["reflexive_learning"]
    assert reflexive["enabled"] is True
    assert reflexive["compression_drive_enabled"] is True

    generated = reflexive["proposals_generated"]
    applied = reflexive["proposals_applied"]
    acceptance_rate = artifact["after"]["metrics"]["proposal_acceptance_rate"]

    assert generated >= 0
    assert applied >= 0
    assert applied <= generated
    if generated == 0:
        assert applied == 0
        assert acceptance_rate == 0.0


def test_quantum_regeneration_runs_from_mathematical_state_and_context() -> None:
    """Regeneration should be driven by formal state/context, not by quantum-SDK calls."""
    quantum_regeneration = importlib.import_module("pythia_mining.quantum_regeneration")

    trace_without_context = quantum_regeneration.regeneration_pipeline(
        module_id="substrate_probe",
        fault_severity=0.5,
        context=None,
    )
    assert trace_without_context["status"] == "innervation_failure"

    context = quantum_regeneration.ContextSignal(
        clifford_index=0,
        target_role=quantum_regeneration.Role.HEALTHY_SPECIALIZED,
        confidence=0.95,
    )
    trace_with_context = quantum_regeneration.regeneration_pipeline(
        module_id="substrate_probe",
        fault_severity=0.5,
        context=context,
    )

    assert trace_with_context["module_id"] == "substrate_probe"
    assert trace_with_context["status"] != "innervation_failure"
    assert "qiskit" not in json.dumps(trace_with_context).lower()
    assert "cirq" not in json.dumps(trace_with_context).lower()
    assert "braket" not in json.dumps(trace_with_context).lower()


def test_emergence_cannot_be_engineered_by_declaration_without_structure() -> None:
    """
    A narrative label or pre-seeded pattern must not manufacture emergence.

    The seed extractor's emergent index must remain zero when there is no
    knowledge graph. This guards the thesis: emergence is measured from
    complexity/topology; it is not engineered by setting a flag or writing a
    slogan into the artifact.
    """
    seed_system_memory = _load_memory_seed_module()
    extractor = seed_system_memory.CodebaseIntelligenceExtractor(REPO_ROOT)

    extractor.emergent_patterns.append(
        {
            "name": "Declared Intelligence",
            "type": "declaration_only",
            "nodes": [],
            "description": "A claim without measured topology.",
            "emergence_index": 1.0,
        }
    )

    assert extractor._calculate_emergent_index() == 0.0


def test_emergence_index_increases_from_complexity_topology_not_constant_fixture() -> None:
    """
    The emergent index should be a function of measured structure.

    This is a falsification harness for the complexity thesis: adding patterns,
    edges, and differentiated module complexity should produce a higher index
    than a same-sized graph with no patterns, no edges, and uniform complexity.
    """
    seed_system_memory = _load_memory_seed_module()

    sparse = seed_system_memory.CodebaseIntelligenceExtractor(REPO_ROOT)
    sparse.knowledge_graph = {
        "a.py": {},
        "b.py": {},
        "c.py": {},
        "d.py": {},
    }
    sparse.import_graph = {
        "a.py": set(),
        "b.py": set(),
        "c.py": set(),
        "d.py": set(),
    }
    sparse.complexity_map = {
        "a.py": 10,
        "b.py": 10,
        "c.py": 10,
        "d.py": 10,
    }

    complex_system = seed_system_memory.CodebaseIntelligenceExtractor(REPO_ROOT)
    complex_system.knowledge_graph = dict(sparse.knowledge_graph)
    complex_system.import_graph = {
        "a.py": {"b.py", "c.py"},
        "b.py": {"c.py"},
        "c.py": {"d.py"},
        "d.py": set(),
    }
    complex_system.complexity_map = {
        "a.py": 5,
        "b.py": 17,
        "c.py": 41,
        "d.py": 83,
    }
    complex_system.emergent_patterns = [
        {
            "name": "Measured Coupling",
            "type": "structural",
            "nodes": ["a.py", "b.py", "c.py"],
            "description": "A pattern derived from topology.",
            "emergence_index": 0.85,
        }
    ]

    assert sparse._calculate_emergent_index() == 0.0
    assert complex_system._calculate_emergent_index() > sparse._calculate_emergent_index()


def test_detected_emergence_can_seed_enhancement_but_absence_cannot() -> None:
    """
    Once emergence is detected, it can be enhanced into explanations and
    counterfactuals. With no detected patterns, the enhancement layer must stay
    empty rather than invent intelligence.
    """
    seed_system_memory = _load_memory_seed_module()

    no_emergence = {
        "emergent_patterns": [],
    }
    seeded_from_absence = seed_system_memory.seed_deutsch_knowledge_substrate(no_emergence)
    assert seeded_from_absence["explanations"] == []
    assert seeded_from_absence["counterfactuals"] == []
    assert seeded_from_absence["strategy_performance"] == {}

    measured_emergence = {
        "emergent_patterns": [
            {
                "name": "Pattern Alpha",
                "type": "structural_coupling",
                "nodes": ["a.py", "b.py"],
                "description": "A measured structural coupling.",
                "emergence_index": 0.82,
            },
            {
                "name": "Pattern Beta",
                "type": "counterfactual_growth",
                "nodes": ["b.py", "c.py"],
                "description": "A second measured pattern.",
                "emergence_index": 0.88,
            },
        ],
    }

    seeded_from_emergence = seed_system_memory.seed_deutsch_knowledge_substrate(
        measured_emergence
    )
    assert len(seeded_from_emergence["explanations"]) == 2
    assert len(seeded_from_emergence["counterfactuals"]) == 1
    assert set(seeded_from_emergence["strategy_performance"]) == {
        "Pattern Alpha",
        "Pattern Beta",
    }
    assert all(
        explanation["source"] == "codebase_structural_analysis"
        for explanation in seeded_from_emergence["explanations"]
    )


def test_once_emergence_has_a_measurable_signal_it_can_be_enhanced_reversibly() -> None:
    """
    Enhancement is allowed after a measurable signal exists, but it must be
    bounded, audited, and reversible.

    This uses the existing autonomous optimizer as the enhancement surface:
    it moves a parameter toward a better objective, records the adjustment, and
    can roll back from history.
    """
    autonomous_controller = importlib.import_module("pythia_mining.autonomous_controller")

    audit = autonomous_controller.AuditLog()
    optimizer = autonomous_controller.AutonomousOptimizer(audit)
    optimizer.register_target(
        autonomous_controller.OptimizationTarget(
            name="emergence_gain",
            current_value=0.2,
            bounds=(0.0, 1.0),
            step_size=0.1,
            objective_fn=lambda value: -(value - 0.7) ** 2,
        )
    )

    before = optimizer.targets["emergence_gain"].current_value
    after = optimizer.optimize_tick("emergence_gain")

    assert after > before
    assert optimizer.targets["emergence_gain"].bounds[0] <= after <= optimizer.targets[
        "emergence_gain"
    ].bounds[1]

    optimizing_entries = audit.recent(subsystem="optimizing")
    assert optimizing_entries[-1].action == "parameter_adjustment"
    assert optimizing_entries[-1].reversible is True

    restored = optimizer.rollback("emergence_gain")
    assert restored == before
    assert audit.recent(subsystem="optimizing")[-1].action == "rollback"
