"""Behavioral tests for QuantumHealingSwarm.

These tests measure what the quantum-mathematical healing actually produces.
They are the Layer 1 evidence for the claim that density matrix superposition
and OR collapse produce measurable purity gain under controlled degradation.

No assertions are asserted-to-be-true before running.  The tests:
1. Run the math.
2. Measure the outcomes.
3. Assert the mathematical invariants that MUST hold (Hermiticity, unit trace,
   purity bounds) — these are not empirical claims, they are definitional.
4. Assert empirical outcomes that the math SHOULD produce — if these fail,
   the implementation has a bug OR the math doesn't do what we think it does.
   Both outcomes are scientifically interesting.

The line being pushed:
  - Can density matrix OR collapse reliably select a higher-purity repair state
    from a superposition of candidates?
  - Does purity increase after collapse on a degraded input?
  - Is entropy reduced?
  - Do more degraded inputs produce more healing gain?
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from pythia_mining.quantum_healing_swarm import (
    HealingResult,
    QuantumHealingSwarm,
    PHI,
    PURITY_COLLAPSE_THRESHOLD,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def swarm() -> QuantumHealingSwarm:
    return QuantumHealingSwarm(num_candidates=8, num_lanes=32)


# ---------------------------------------------------------------------------
# 1. Mathematical invariants — MUST hold regardless of input
# ---------------------------------------------------------------------------


def test_density_matrix_is_hermitian_after_degradation(swarm):
    """Degraded density matrix must be Hermitian: ρ = ρ†."""
    rho = swarm._form_degraded_density_matrix(0.3, 5, 1.0)
    assert np.allclose(rho, rho.conj().T, atol=1e-12), "ρ must be Hermitian"


def test_density_matrix_unit_trace_after_degradation(swarm):
    """tr(ρ) = 1 must hold for all degraded states."""
    for phi_d in (0.1, 0.5, 0.9):
        rho = swarm._form_degraded_density_matrix(phi_d, 0, 1.0)
        assert abs(np.trace(rho).real - 1.0) < 1e-10, f"tr(ρ) ≠ 1 at phi_density={phi_d}"


def test_density_matrix_positive_semidefinite_after_degradation(swarm):
    """All eigenvalues of ρ must be ≥ 0 (positive semi-definite)."""
    rho = swarm._form_degraded_density_matrix(0.2, 10, 1.0)
    eigvals = np.linalg.eigvalsh(rho).real
    assert np.all(eigvals >= -1e-10), f"ρ has negative eigenvalues: {eigvals.min()}"


def test_superposed_state_unit_trace(swarm):
    """Superposed repair density matrix must have tr(ρ) = 1."""
    rho_deg = swarm._form_degraded_density_matrix(0.4, 3, 1.0)
    rho_super, _ = swarm._superpose_repair_candidates(rho_deg, 0.4)
    assert abs(np.trace(rho_super).real - 1.0) < 1e-10


def test_collapsed_state_is_pure(swarm):
    """After OR collapse, purity must equal 1.0 (collapsed to eigenstate)."""
    rho_deg = swarm._form_degraded_density_matrix(0.1, 10, 1.0)
    rho_super, _ = swarm._superpose_repair_candidates(rho_deg, 0.1)
    rho_collapsed, fired = swarm._or_collapse(rho_super)
    if fired:
        purity = swarm._purity(rho_collapsed)
        assert abs(purity - 1.0) < 1e-10, f"Collapsed state purity = {purity}, expected 1.0"


def test_purity_bounds(swarm):
    """Purity must be in [1/n, 1] for any n×n density matrix."""
    n = swarm.num_candidates
    for phi_d in (0.05, 0.5, 0.95):
        rho = swarm._form_degraded_density_matrix(phi_d, 0, 1.0)
        p = swarm._purity(rho)
        assert 1.0 / n - 1e-10 <= p <= 1.0 + 1e-10, f"purity={p} out of [1/n, 1] at phi_density={phi_d}"


def test_von_neumann_entropy_non_negative(swarm):
    """Von Neumann entropy must be ≥ 0."""
    rho = swarm._form_degraded_density_matrix(0.3, 5, 1.0)
    s = swarm._von_neumann_entropy(rho)
    assert s >= -1e-10, f"Entropy = {s} is negative"


def test_phi_basis_vector_is_unit_norm(swarm):
    """φ-basis vectors must have unit L2 norm."""
    for n in (4, 8, 16):
        v = swarm._phi_basis_vector(n)
        assert abs(np.linalg.norm(v) - 1.0) < 1e-12, f"φ-basis vector not normalised at n={n}"


# ---------------------------------------------------------------------------
# 2. Empirical outcomes — what the math SHOULD produce
# ---------------------------------------------------------------------------


def test_or_collapse_fires_on_degraded_input(swarm):
    """OR collapse must fire when phi_density is very low (highly mixed state)."""
    rho_deg = swarm._form_degraded_density_matrix(0.05, 20, 1.0)
    rho_super, _ = swarm._superpose_repair_candidates(rho_deg, 0.05)
    _, fired = swarm._or_collapse(rho_super)
    assert fired, "OR collapse must fire for highly degraded (low purity) input"


def test_or_collapse_does_not_fire_on_healthy_input(swarm):
    """OR collapse must NOT fire when phi_density is high (already coherent)."""
    rho_deg = swarm._form_degraded_density_matrix(0.98, 0, 0.0)
    rho_super, _ = swarm._superpose_repair_candidates(rho_deg, 0.98)
    _, fired = swarm._or_collapse(rho_super)
    assert not fired, "OR collapse must not fire for healthy (high purity) input"


def test_heal_increases_purity_on_degraded_input(swarm):
    """Healing a degraded system must produce purity_gain > 0."""
    result = swarm.heal(phi_density=0.10, consecutive_failures=8)
    assert result.purity_gain > 0, (
        f"Expected purity gain > 0, got {result.purity_gain:.6f}. "
        f"pre={result.pre_heal_purity:.4f} post={result.post_heal_purity:.4f}"
    )


def test_heal_reduces_entropy_on_degraded_input(swarm):
    """Healing must reduce Von Neumann entropy on a degraded input."""
    result = swarm.heal(phi_density=0.10, consecutive_failures=8)
    assert result.entropy_reduction > 0, (
        f"Expected entropy reduction > 0, got {result.entropy_reduction:.6f}. "
        f"pre={result.pre_heal_entropy:.4f} post={result.post_heal_entropy:.4f}"
    )


def test_heal_increases_phi_density_projection(swarm):
    """Post-heal φ-density projection must be ≥ pre-heal value."""
    result = swarm.heal(phi_density=0.3, consecutive_failures=3)
    assert result.post_heal_phi_density >= result.pre_heal_phi_density, (
        f"φ-density regressed: pre={result.pre_heal_phi_density:.4f} "
        f"post={result.post_heal_phi_density:.4f}"
    )


def test_more_degraded_input_produces_more_purity_gain(swarm):
    """Heavily degraded system should gain more purity than a mildly degraded one."""
    heavy = swarm.heal(phi_density=0.05, consecutive_failures=15)
    mild = swarm.heal(phi_density=0.7, consecutive_failures=1)
    assert heavy.purity_gain >= mild.purity_gain, (
        f"Expected heavy degradation to produce more purity gain than mild. "
        f"heavy={heavy.purity_gain:.4f} mild={mild.purity_gain:.4f}"
    )


def test_lanes_healed_proportional_to_degradation(swarm):
    """More degraded systems must heal more lanes."""
    heavy = swarm.heal(phi_density=0.1, consecutive_failures=10)
    mild = swarm.heal(phi_density=0.9, consecutive_failures=0)
    assert heavy.lanes_healed >= mild.lanes_healed, (
        f"Expected heavy degradation to heal more lanes: "
        f"heavy={heavy.lanes_healed} mild={mild.lanes_healed}"
    )


def test_full_heal_result_has_required_fields(swarm):
    """HealingResult must contain all documented fields."""
    result = swarm.heal(phi_density=0.5, consecutive_failures=2)
    d = result.to_dict()
    required = {
        "pre_heal_purity", "pre_heal_entropy", "pre_heal_phi_density",
        "post_heal_purity", "post_heal_entropy", "post_heal_phi_density",
        "or_collapse_fired", "dominant_eigenvalue", "candidates_superposed",
        "lanes_healed", "purity_gain", "entropy_reduction", "duration_ms",
    }
    missing = required - d.keys()
    assert not missing, f"HealingResult.to_dict() missing fields: {missing}"


def test_heal_duration_is_sub_100ms(swarm):
    """Full quantum healing cycle must complete in < 100 ms on any modern CPU."""
    result = swarm.heal(phi_density=0.3, consecutive_failures=5)
    assert result.duration_ms < 100.0, (
        f"Quantum healing took {result.duration_ms:.1f}ms — exceeds 100ms guard"
    )


# ---------------------------------------------------------------------------
# 3. Repeatability — quantum math is deterministic on classical hardware
# ---------------------------------------------------------------------------


def test_healing_is_deterministic(swarm):
    """Same inputs must produce identical outputs (classical determinism)."""
    r1 = swarm.heal(phi_density=0.3, consecutive_failures=4)
    swarm2 = QuantumHealingSwarm(num_candidates=8, num_lanes=32)
    r2 = swarm2.heal(phi_density=0.3, consecutive_failures=4)
    assert abs(r1.post_heal_purity - r2.post_heal_purity) < 1e-12, (
        "Healing is not deterministic: different purity on identical inputs"
    )
    assert abs(r1.purity_gain - r2.purity_gain) < 1e-12


# ---------------------------------------------------------------------------
# 4. Controller integration — _handle_performance_degradation uses the swarm
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_controller_quantum_healing_writes_audit_entry():
    """_handle_performance_degradation must write a quantum_healing_complete
    AuditLogEntry so the event is in the tamper-evident chain."""
    import os
    import tempfile
    from pythia_mining.autonomous_mining_controller import (
        AutonomousConfig,
        AutonomyLevel,
        AutonomousMiningController,
    )
    from pythia_mining.autonomous_audit_persistence import AuditJournal, AutonomousAuditLogger
    from pythia_mining.autonomous_escalation import AutonomousEscalationEngine

    class _FakeEngine:
        phi_density = 0.2
        current_job = None
        stratum_client = None
        phi_ensemble = None
        optimizer = None
        solver = None
        consciousness = None
        def get_hashrate(self): return 0.0
        def get_phi_density(self): return self.phi_density
        def get_state(self): return {"status": "idle"}
        class _PhiScaling:
            phi_scaling = 1.5
            search_depth = 60
            coherence_threshold = 0.45
            compression_target = 1.86
        phi_scaling_engine = _PhiScaling()

    with tempfile.TemporaryDirectory() as tmp:
        config = AutonomousConfig(
            persistence_enabled=True,
            persistence_dir=tmp,
            reflexive_loop_enabled=False,
        )
        ctrl = AutonomousMiningController(_FakeEngine(), config=config)
        audit_dir = os.path.join(tmp, "audit")
        ctrl._persistent_audit_logger = AutonomousAuditLogger(
            journal=AuditJournal(journal_dir=audit_dir)
        )
        ctrl._escalation_engine = AutonomousEscalationEngine(
            audit_logger=ctrl._persistent_audit_logger,
            escalation_callback=lambda level: ctrl.set_autonomy_level(AutonomyLevel(level)),
            degradation_callback=lambda reason: ctrl.degrade_autonomy_level(reason).value,
        )
        # Simulate a degraded state
        ctrl._actual_hashrate = 0.3
        ctrl._target_hashrate = 1.0
        ctrl._consecutive_failures = 5

        await ctrl._handle_performance_degradation()

    healing_entries = [
        e for e in ctrl.audit_log if e.event_type == "quantum_healing_complete"
    ]
    assert len(healing_entries) == 1, (
        f"Expected 1 quantum_healing_complete audit entry, got {len(healing_entries)}"
    )
    # Verify key fields are present in the state_diff
    diff = healing_entries[0].state_diff
    assert "post_heal_purity" in diff
    assert "purity_gain" in diff
    assert "or_collapse_fired" in diff


@pytest.mark.asyncio
async def test_controller_quantum_healing_resets_failure_state():
    """After quantum healing, consecutive_failures must be 0 and error_rate 0.0."""
    import os
    import tempfile
    from pythia_mining.autonomous_mining_controller import (
        AutonomousConfig, AutonomousMiningController,
    )
    from pythia_mining.autonomous_audit_persistence import AuditJournal, AutonomousAuditLogger
    from pythia_mining.autonomous_escalation import AutonomousEscalationEngine
    from pythia_mining.autonomous_mining_controller import AutonomyLevel

    class _FakeEngine:
        phi_density = 0.15
        current_job = None; stratum_client = None; phi_ensemble = None
        optimizer = None; solver = None; consciousness = None
        def get_hashrate(self): return 0.0
        def get_phi_density(self): return self.phi_density
        def get_state(self): return {}
        class _PhiScaling:
            phi_scaling = 1.5; search_depth = 60
            coherence_threshold = 0.45; compression_target = 1.86
        phi_scaling_engine = _PhiScaling()

    with tempfile.TemporaryDirectory() as tmp:
        config = AutonomousConfig(persistence_enabled=True, persistence_dir=tmp, reflexive_loop_enabled=False)
        ctrl = AutonomousMiningController(_FakeEngine(), config=config)
        audit_dir = os.path.join(tmp, "audit")
        ctrl._persistent_audit_logger = AutonomousAuditLogger(journal=AuditJournal(journal_dir=audit_dir))
        ctrl._escalation_engine = AutonomousEscalationEngine(
            audit_logger=ctrl._persistent_audit_logger,
            escalation_callback=lambda level: ctrl.set_autonomy_level(AutonomyLevel(level)),
            degradation_callback=lambda reason: ctrl.degrade_autonomy_level(reason).value,
        )
        ctrl._actual_hashrate = 0.2
        ctrl._target_hashrate = 1.0
        ctrl._consecutive_failures = 7
        ctrl._error_rate = 0.25

        await ctrl._handle_performance_degradation()

    assert ctrl._consecutive_failures == 0
    assert ctrl._error_rate == 0.0
