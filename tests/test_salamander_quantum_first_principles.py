"""
Falsification tests for HYBA/Salamander quantum-first-principles claims.

These tests deliberately avoid proving a narrative. They encode the narrow
claims that can be checked in CI:

1. The quantum substrate can be expressed as mathematics rather than as a
   hardware/vendor dependency.
2. Hardware acceleration remains optional evidence, not the source of the
   quantum claim.
3. Memory seeding is treated as a structural prior, not as smuggled proof of
   consciousness/quantum behaviour.
4. A bootstrap artifact that exposes self-optimisation infrastructure must not
   be misread as evidence that optimisation proposals were actually applied.

If these tests fail, the claim boundary has drifted and the system needs repair
before the claim is made externally.
"""

from __future__ import annotations

import ast
import importlib
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

FORBIDDEN_VENDOR_IMPORT_ROOTS = {
    "mlx",
    "metal",
    "qiskit",
    "cirq",
    "braket",
    "cuda",
    "cupy",
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


def test_phi_algebra_is_a_first_principles_invariant() -> None:
    """The base constant must satisfy the defining algebra, not a fixture value."""
    assert PHI > 1.0
    assert math.isclose(PHI * PHI, PHI + 1.0, rel_tol=0.0, abs_tol=1e-15)
    assert math.isclose(PHI_INV, PHI - 1.0, rel_tol=0.0, abs_tol=1e-15)
    assert math.isclose(PHI * PHI_INV, 1.0, rel_tol=0.0, abs_tol=1e-15)


@pytest.mark.parametrize("module_path", PURE_MATH_SUBSTRATE_MODULES)
def test_quantum_substrate_core_has_no_required_hardware_vendor_imports(module_path: Path) -> None:
    """Core substrate modules must not depend on vendor quantum/GPU stacks."""
    assert module_path.exists(), f"Missing expected substrate module: {module_path}"
    imported_roots = _import_roots(module_path)
    forbidden = imported_roots & FORBIDDEN_VENDOR_IMPORT_ROOTS
    assert forbidden == set(), (
        f"{module_path.relative_to(REPO_ROOT)} imports vendor/hardware roots {sorted(forbidden)}. "
        "That would violate the substrate-agnostic claim boundary."
    )


def test_hardware_probe_is_optional_evidence_not_the_quantum_source(monkeypatch: pytest.MonkeyPatch) -> None:
    """Forcing a non-Apple host must degrade cleanly instead of fabricating hardware proof."""
    apple_silicon_metal = importlib.import_module("pythia_mining.apple_silicon_metal")

    monkeypatch.setattr(apple_silicon_metal.platform, "system", lambda: "Linux")
    monkeypatch.setattr(apple_silicon_metal.platform, "machine", lambda: "x86_64")

    packet = apple_silicon_metal.probe_mlx_metal(matrix_size=8, require_mlx=False)

    assert packet["status"] == "unavailable"
    assert packet["apple_silicon_detected"] is False
    assert packet["mlx_available"] is False
    assert packet["metal_path_verified"] is False
    assert "hardware speedup claim" in packet["claim_boundary"]["not_supported"]


def test_memory_seed_is_structural_prior_not_claim_smuggling() -> None:
    """The seed can prime memory, but its own boundary must remain structural."""
    seed_path = REPO_ROOT / "artifacts" / "memory_seed" / "memory_seed_v1.json"
    seed_script_path = REPO_ROOT / "scripts" / "seed_system_memory.py"

    seed = json.loads(seed_path.read_text(encoding="utf-8"))
    seed_script = seed_script_path.read_text(encoding="utf-8")

    assert seed["metadata"]["seed_source"] == "codebase_structural_analysis"
    assert seed["metadata"]["total_nodes"] >= 1
    assert seed["metadata"]["total_edges"] >= seed["metadata"]["total_nodes"]
    assert "STRUCTURAL METRICS" in seed_script
    assert "NOT measurements of consciousness" in seed_script
    assert "No claims about consciousness, quantum properties, or intelligence" in seed_script


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


def test_quantum_regeneration_is_contextual_math_not_hardware_execution() -> None:
    """The regeneration pipeline should run from state/context maths without hardware."""
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
    assert "hardware" not in json.dumps(trace_with_context).lower()
