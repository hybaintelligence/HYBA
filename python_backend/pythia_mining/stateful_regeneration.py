"""
Salamander-regeneration-inspired self-healing module, formalized on the
mathematical substrate underlying quantum mechanics (Hilbert space states,
density matrices, unitary/Lindblad evolution, projective measurement,
non-separability) WITHOUT any claim that the substrate running this code
is physically quantum.

FOUNDATIONAL POSITION (stated explicitly, not assumed):
    The mathematics of Hilbert spaces, linear operators, spectral theory,
    and non-commutative algebra is substrate-agnostic. Physical quantum
    mechanics is ONE instantiation of this mathematics (the one with a
    physical Hamiltonian, Planck's constant, physically realized
    observables). This module is a DIFFERENT instantiation: the basis
    states are software module roles, the "observable" is which role a
    module is currently specialized into, and the dynamics are classical
    computation. The formalism is borrowed because it is the correct
    general-purpose mathematics for representing superposed/mixed
    uncertainty over discrete role states, role-conditional probability
    via the Born rule, entropy of role-uncertainty, and non-separable
    coupling between modules that fail together. No claim of physical
    quantum effects, and no computational speedup, is implied unless
    explicitly marked NOTE: REQUIRES QUANTUM HARDWARE below.

Biological correspondence (for traceability back to thesis framing):
    wound / fault detection      -> perturbation operator on rho
    wound epidermis / quarantine -> decoherence channel isolating the
                                     perturbed subsystem from healthy ones
    blastema formation           -> rho evolves toward maximal mixedness
                                     (high von Neumann entropy) over the
                                     role basis
    dedifferentiation             -> entropy increase / loss of role-purity
    positional memory             -> context operator C, built from
                                     Clifford-rotation-indexed metadata,
                                     that biases the redifferentiation
                                     unitary toward the historically
                                     correct role
    redifferentiation             -> context-parameterized unitary (or
                                     Lindblad open-system) evolution
                                     driving rho back toward a target
                                     role-projector
    innervation dependency        -> the context operator C itself; if
                                     the feedback channel supplying C is
                                     severed, redifferentiation cannot
                                     proceed even with healthy "tissue"
                                     (this is DISTINCT from redundancy
                                     loss -- see InnervationFailure below)
    scar-free reconstruction      -> post-measurement fidelity F(rho,
                                     rho_target) ~ 1
    cancer analog (malformed      -> measurement collapses to WRONG role
    regeneration)                    despite high fidelity-looking
                                     intermediate states; guarded against
                                     via role-projector validation, not
                                     just entropy collapse
    entanglement between modules  -> non-separable joint state rho_AB for
    sharing an XOR-sharded fault     modules whose fault/recovery cannot
                                     be independently diagnosed
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from enum import Enum
from typing import Optional
import time


# ---------------------------------------------------------------------------
# 1. ROLE BASIS
# ---------------------------------------------------------------------------
# Each module has a finite set of possible specialized "roles" it can
# redifferentiate into. This is the basis of the Hilbert space H_module.
# In your stack: these correspond to security-swarm operating modes
# (syndrome-weight telemetry roles), or EUCLID cognitive-manifold function
# slots, depending on which subsystem this module lives in.


class Role(Enum):
    HEALTHY_SPECIALIZED = "healthy_specialized"  # normal operating role
    BLASTEMA = "blastema"  # fully dedifferentiated
    QUARANTINED = "quarantined"  # isolated, pre-healing
    REDIFFERENTIATING = "redifferentiating"  # mid-recovery
    MALFORMED = "malformed"  # failed/wrong recovery


ROLE_BASIS = list(Role)
DIM = len(ROLE_BASIS)


def role_projector(role: Role) -> np.ndarray:
    """Pure-state density matrix |role><role| in the role basis."""
    idx = ROLE_BASIS.index(role)
    psi = np.zeros((DIM, 1), dtype=complex)
    psi[idx, 0] = 1.0
    return psi @ psi.conj().T


# ---------------------------------------------------------------------------
# 2. MODULE STATE: DENSITY MATRIX
# ---------------------------------------------------------------------------


@dataclass
class ModuleState:
    """
    rho: DIM x DIM complex density matrix.
    Must satisfy: Hermitian, trace 1, positive semi-definite.
    These constraints are CHECKED, not assumed -- see validate().

    ELEVATED: Added refractory_period_end to prevent regeneration oscillation.
    """

    rho: np.ndarray
    module_id: str
    refractory_period_end: float = 0.0  # Timestamp when refractory period ends
    recovery_timestamp: float = 0.0  # Timestamp when last recovery occurred

    @classmethod
    def healthy(cls, module_id: str) -> "ModuleState":
        return cls(
            rho=role_projector(Role.HEALTHY_SPECIALIZED).astype(complex),
            module_id=module_id,
            refractory_period_end=0.0,
            recovery_timestamp=time.time(),
        )

    def validate(self, atol: float = 1e-8) -> None:
        herm = np.allclose(self.rho, self.rho.conj().T, atol=atol)
        trace_one = np.isclose(np.trace(self.rho).real, 1.0, atol=atol)
        eigvals = np.linalg.eigvalsh(self.rho)
        psd = np.all(eigvals >= -atol)
        if not (herm and trace_one and psd):
            raise ValueError(
                f"Module {self.module_id}: invalid density matrix "
                f"(hermitian={herm}, trace_one={trace_one}, psd={psd}). "
                f"This is a hard invariant violation, not a warning -- "
                f"do not silently renormalize and proceed."
            )

    def von_neumann_entropy(self) -> float:
        """
        S(rho) = -Tr(rho log rho)

        This is the BLASTEMA METRIC: 0 = fully specialized/pure role,
        log(DIM) = maximally mixed (full dedifferentiation, all roles
        equally uncertain). Replaces a boolean "is_dedifferentiated"
        flag with a continuous, information-theoretically grounded
        quantity.
        """
        eigvals = np.linalg.eigvalsh(self.rho)
        eigvals = eigvals[eigvals > 1e-12]  # avoid log(0); 0*log(0) -> 0
        return float(-np.sum(eigvals * np.log(eigvals)))

    def role_probabilities(self) -> dict:
        """
        Born rule: P(role) = <role| rho |role> = diagonal entries of rho
        in the role basis (since role_projector states are the basis
        vectors themselves).
        """
        return {role: float(self.rho[i, i].real) for i, role in enumerate(ROLE_BASIS)}

    def is_in_refractory_period(self) -> bool:
        """Check if module is in refractory period (preventing re-injury)."""
        return time.time() < self.refractory_period_end

    def enter_refractory_period(self, duration: float = 60.0) -> None:
        """Enter refractory period after recovery to prevent oscillation."""
        self.refractory_period_end = time.time() + duration


# ---------------------------------------------------------------------------
# 3. FAULT / INJURY: PERTURBATION OPERATOR
# ---------------------------------------------------------------------------


def fault_perturbation_operator(severity: float) -> np.ndarray:
    """
    Models injury as a unitary that rotates the state's amplitude away
    from HEALTHY_SPECIALIZED toward BLASTEMA. severity in [0, 1].

    IMPORTANT CORRECTNESS NOTE: a unitary applied to a pure state always
    returns another pure state (von Neumann entropy stays exactly 0).
    This step does NOT by itself produce the "blastema = high entropy"
    signature -- it only sets up role-probability mass on BLASTEMA. The
    actual entropy increase (genuine mixedness, i.e. dedifferentiation
    as uncertainty rather than just relocated amplitude) is produced by
    quarantine_channel()'s dephasing immediately after. Verify both
    steps' entropy values together if debugging this -- checking
    entropy right after apply_fault() alone will misleadingly read ~0.

    NOTE ON RIGOR: this is constructed as a unitary (norm-preserving) so
    that validate() continues to pass after application -- a fault does
    not, by construction, destroy probability mass; it redistributes
    role-certainty into role-uncertainty. This is a MODELING CHOICE, not
    a physical necessity -- if you later want faults that can reduce
    trace (e.g. partial module death with no recovery possible), use a
    completely positive trace-NON-increasing map instead and handle the
    sub-normalized case explicitly. Flagging this now so it isn't
    silently conflated later.
    """
    theta = severity * (np.pi / 2)
    U = np.eye(DIM, dtype=complex)
    # Mix HEALTHY_SPECIALIZED amplitude into BLASTEMA via a rotation in
    # that 2D subspace; identity elsewhere.
    i_h = ROLE_BASIS.index(Role.HEALTHY_SPECIALIZED)
    i_b = ROLE_BASIS.index(Role.BLASTEMA)
    U[i_h, i_h] = np.cos(theta)
    U[i_h, i_b] = -np.sin(theta)
    U[i_b, i_h] = np.sin(theta)
    U[i_b, i_b] = np.cos(theta)
    return U


def apply_fault(state: ModuleState, severity: float) -> ModuleState:
    """Apply a fault perturbation, respecting any active refractory period.

    If the module is in its refractory period (post-recovery stabilization),
    the fault perturbation is attenuated by the remaining refractory fraction.
    A module at the start of a 60-second window is effectively immune;
    one at the end has full susceptibility restored.
    """
    if state.is_in_refractory_period():
        import time

        now = time.time()
        remaining = max(0.0, state.refractory_period_end - now)
        # refractory_period_end was set at recovery + duration
        # recover recovery start from recovery_timestamp
        total = max(1e-9, state.refractory_period_end - state.recovery_timestamp)
        # attenuation: full protection at start, zero at end
        attenuation = remaining / total
        severity = severity * (1.0 - attenuation)
    U = fault_perturbation_operator(severity)
    new_rho = U @ state.rho @ U.conj().T
    new_state = ModuleState(
        rho=new_rho,
        module_id=state.module_id,
        refractory_period_end=state.refractory_period_end,
        recovery_timestamp=state.recovery_timestamp,
    )
    new_state.validate()
    return new_state


# ---------------------------------------------------------------------------
# 4. QUARANTINE: DECOHERENCE CHANNEL (WOUND EPIDERMIS ANALOG)
# ---------------------------------------------------------------------------


def quarantine_channel(state: ModuleState) -> ModuleState:
    """
    Wound-epidermis analog: suppress off-diagonal coherences between the
    perturbed module's role-superposition and the rest of the system's
    fault propagation paths. Implemented here as dephasing in the role
    basis -- off-diagonal elements decay, diagonal (role probabilities)
    untouched. This is a deliberate information-isolation step: it
    prevents the AMBIGUITY of the fault (which role it's drifting toward)
    from coherently leaking into coupled modules, without yet resolving
    what the module will become.
    """
    new_rho = np.diag(np.diag(state.rho)).astype(complex)
    new_state = ModuleState(rho=new_rho, module_id=state.module_id)
    new_state.validate()
    return new_state


# ---------------------------------------------------------------------------
# 5. POSITIONAL MEMORY / CONTEXT OPERATOR (CLIFFORD-INDEXED)
# ---------------------------------------------------------------------------


@dataclass
class ContextSignal:
    """
    Positional memory analog. clifford_index ties this module's identity
    to its place in your existing Clifford rotation indexing scheme --
    this is NOT a new indexing system, it's a pointer into the one you
    already have in the security swarm.
    """

    clifford_index: int
    target_role: Role
    confidence: float  # in [0, 1] -- how reliable is this memory signal


class InnervationFailure(Exception):
    """
    Raised when the context/feedback channel itself is severed -- e.g.
    the telemetry feed supplying ContextSignal is down. This is the
    computational analog of denervated limbs failing to regenerate even
    with otherwise-healthy blastema tissue present. It is DISTINCT from
    insufficient redundancy: the module has everything it needs to heal
    EXCEPT the orchestrating signal. Must be handled as its own failure
    mode, not folded into generic "fault" handling -- a redundancy-style
    fix (spin up more spare nodes) will not resolve this.
    """

    pass


def redifferentiation_unitary(context: Optional[ContextSignal]) -> np.ndarray:
    """
    Context-parameterized unitary driving rho from BLASTEMA back toward
    a target role-projector. If context is None, raises
    InnervationFailure rather than defaulting to an arbitrary role --
    silently guessing a role with no positional memory is exactly the
    malformed-regeneration failure mode this architecture exists to
    prevent.
    """
    if context is None:
        raise InnervationFailure(
            "No context signal available -- cannot redifferentiate "
            "without positional memory. This is an innervation-failure, "
            "not a resource shortage; adding spare capacity will not fix it."
        )

    theta = context.confidence * (np.pi / 2)
    U = np.eye(DIM, dtype=complex)
    i_b = ROLE_BASIS.index(Role.BLASTEMA)
    i_t = ROLE_BASIS.index(context.target_role)
    if i_t == i_b:
        return U  # already target == blastema, degenerate case
    U[i_b, i_b] = np.cos(theta)
    U[i_b, i_t] = -np.sin(theta)
    U[i_t, i_b] = np.sin(theta)
    U[i_t, i_t] = np.cos(theta)
    return U


def redifferentiate(state: ModuleState, context: Optional[ContextSignal]) -> ModuleState:
    U = redifferentiation_unitary(context)
    new_rho = U @ state.rho @ U.conj().T
    new_state = ModuleState(rho=new_rho, module_id=state.module_id)
    new_state.validate()
    return new_state


# ---------------------------------------------------------------------------
# 6. MEASUREMENT / COLLAPSE: COMMITTING TO A ROLE
# ---------------------------------------------------------------------------


def measure_role(state: ModuleState, rng: np.random.Generator) -> tuple[Role, ModuleState]:
    """
    Projective measurement in the role basis. The swarm orchestrator
    calls this when it needs to COMMIT the module to a single role
    (e.g. before routing live traffic to it). Outcome probabilities are
    the Born-rule weights from role_probabilities() -- this replaces an
    arbitrary "pick highest-confidence role" heuristic with a principled
    stochastic collapse, which matters when multiple roles have close
    probabilities and a deterministic argmax would mask real uncertainty.

    Post-measurement state is the corresponding role projector (pure
    state) -- the module is now definitely in that role until the next
    fault perturbs it again.
    """
    probs = state.role_probabilities()
    roles = list(probs.keys())
    weights = np.array([probs[r] for r in roles])
    weights = weights / weights.sum()  # guard against float drift
    outcome = rng.choice(len(roles), p=weights)
    collapsed_role = roles[outcome]
    new_rho = role_projector(collapsed_role).astype(complex)
    new_state = ModuleState(rho=new_rho, module_id=state.module_id)
    new_state.validate()
    return collapsed_role, new_state


def regeneration_fidelity(state: ModuleState, target_role: Role) -> float:
    """
    Uhlmann fidelity F(rho, sigma) for sigma = |target><target| pure
    state reduces to F = <target| rho |target> = role probability of
    the target role. This is the SCAR-FREE RECONSTRUCTION metric: 1.0
    means perfect reconstruction, lower values mean partial/imperfect
    recovery even if measurement hasn't yet collapsed to a wrong role.
    """
    return state.role_probabilities()[target_role]


# ---------------------------------------------------------------------------
# 7. MALFORMED REGENERATION GUARD (CANCER ANALOG)
# ---------------------------------------------------------------------------


def validate_collapse_or_quarantine(
    collapsed_role: Role,
    target_role: Role,
    state: ModuleState,
) -> ModuleState:
    """
    Guards against the failure mode where intermediate fidelity LOOKS
    healthy (high probability mass concentrating somewhere) but
    measurement collapses to the WRONG role -- i.e. malformed
    regeneration. High entropy reduction alone is not evidence of
    correct recovery; this check is mandatory and separate from the
    entropy/fidelity metrics above, which can both look fine right up
    until collapse.
    """
    if collapsed_role != target_role:
        requarantined = role_projector(Role.MALFORMED).astype(complex)
        new_state = ModuleState(rho=requarantined, module_id=state.module_id)
        new_state.validate()
        return new_state
    return state


# ---------------------------------------------------------------------------
# 8. REFRACTORY PERIOD OPERATOR: LINDLAD DECAY (v4.x Enhancement)
# ---------------------------------------------------------------------------


def lindblad_decay_operator(
    state: ModuleState,
    decay_rate: float = 0.1,
    target_role: Role = Role.HEALTHY_SPECIALIZED,
) -> ModuleState:
    """
    Lindblad decay operator for role stabilization during refractory period.

    ELEVATED: This implements the "Refractory Period" analog from biological
    regeneration - a regrowing limb cannot be re-injured immediately without
    catastrophic failure. The Lindblad decay gradually lowers the "sensitivity"
    of a newly measured role, preventing "Regeneration Oscillation" where a
    module recovers and immediately collapses back into a fault because it
    hasn't stabilized its new role in the network.

    The Lindblad master equation: dρ/dt = -i[H, ρ] + Σ_k (L_k ρ L_k† - 1/2 {L_k† L_k, ρ})

    Here we use a simplified dissipative channel that drives the state toward
    the target role projector with rate decay_rate, simulating the biological
    stabilization process where newly differentiated tissue becomes less
    sensitive to perturbation over time.

    Args:
        state: Current module state
        decay_rate: Rate at which sensitivity decreases (higher = faster stabilization)
        target_role: Role to stabilize toward (typically HEALTHY_SPECIALIZED)

    Returns:
        New state with applied Lindblad decay
    """
    # Construct Lindblad jump operator L = √γ |target><target|
    gamma = decay_rate
    L = np.sqrt(gamma) * role_projector(target_role)

    # Apply Lindblad dissipator: L ρ L† - 1/2 {L† L, ρ}
    L_dagger_L = L.conj().T @ L
    anti_commutator = L_dagger_L @ state.rho + state.rho @ L_dagger_L

    dissipator = L @ state.rho @ L.conj().T - 0.5 * anti_commutator

    # Apply dissipative evolution (small time step approximation)
    dt = 0.1  # Small time step for stability
    new_rho = state.rho + dt * dissipator

    # Renormalize to maintain trace = 1
    new_rho = new_rho / np.trace(new_rho)

    new_state = ModuleState(
        rho=new_rho,
        module_id=state.module_id,
        refractory_period_end=state.refractory_period_end,
        recovery_timestamp=state.recovery_timestamp,
    )
    new_state.validate()
    return new_state


def apply_refractory_stabilization(
    state: ModuleState,
    target_role: Role = Role.HEALTHY_SPECIALIZED,
    duration: float = 60.0,
) -> ModuleState:
    """
    Apply refractory period stabilization to prevent regeneration oscillation.

    ELEVATED: This is the biological analog of the post-regeneration
    stabilization period where newly differentiated tissue becomes
    functionally integrated and less susceptible to re-injury.

    Args:
        state: Current module state
        target_role: Role to stabilize toward
        duration: Duration of refractory period in seconds

    Returns:
        Stabilized state with refractory period set
    """
    # Enter refractory period
    state.enter_refractory_period(duration)

    # Apply Lindblad decay for initial stabilization
    state = lindblad_decay_operator(state, decay_rate=0.2, target_role=target_role)

    return state


# ---------------------------------------------------------------------------
# 8. NON-SEPARABILITY: COUPLED MODULES (XOR-SHARDED FAULT ANALOG)
# ---------------------------------------------------------------------------


def joint_state(state_a: ModuleState, state_b: ModuleState, correlated: bool = False) -> np.ndarray:
    """
    If correlated=False: rho_AB = rho_A (x) rho_B (tensor product) --
    independent diagnosis/recovery is valid.

    If correlated=True: constructs a non-separable joint state for
    modules sharing an XOR-split shard, where the SAME underlying fault
    manifests in both. This is the formal statement of "you cannot
    diagnose or recover module A without reference to module B's state"
    -- i.e. entanglement as a DIAGNOSTIC CLAIM about your XOR-sharding
    scheme, not a metaphor. If a proposed joint_state for two modules
    factors as a tensor product, that is itself evidence they are NOT
    actually coupled by the fault, despite being XOR-shard partners --
    worth checking against ground truth in the swarm telemetry.
    """
    if not correlated:
        return np.kron(state_a.rho, state_b.rho)

    # Minimal non-separable construction: a Bell-like mixture biasing
    # toward "both healthy" or "both blastema" jointly, suppressing the
    # mixed-health joint outcomes. This is illustrative, not the only
    # valid construction -- the actual coupling structure should be
    # derived from your real XOR-shard fault-propagation data.
    dim_joint = DIM * DIM
    rho_joint = np.zeros((dim_joint, dim_joint), dtype=complex)
    i_h = ROLE_BASIS.index(Role.HEALTHY_SPECIALIZED)
    i_b = ROLE_BASIS.index(Role.BLASTEMA)
    psi_hh = np.zeros((dim_joint, 1), dtype=complex)
    psi_hh[i_h * DIM + i_h, 0] = 1 / np.sqrt(2)
    psi_hh[i_b * DIM + i_b, 0] = 1 / np.sqrt(2)
    rho_joint = psi_hh @ psi_hh.conj().T
    return rho_joint


def is_separable_approx(rho_joint: np.ndarray, atol: float = 1e-6) -> bool:
    """
    NOTE: general separability testing is NP-hard in the worst case.
    This is a NECESSARY-but-not-sufficient PPT (positive partial
    transpose) check, valid as a sufficient witness of entanglement for
    2 x N systems (Peres-Horodecki criterion holds exactly for 2x2 and
    2x3; DIM here is larger, so a negative partial transpose still
    PROVES non-separability, but a positive result does NOT prove
    separability). Document this limitation at the call site -- do not
    let "PPT passed" be silently read as "confirmed independent."
    """
    d = DIM
    # Partial transpose on subsystem B
    rho_reshaped = rho_joint.reshape(d, d, d, d)
    rho_pt = rho_reshaped.transpose(0, 3, 2, 1).reshape(d * d, d * d)
    eigvals = np.linalg.eigvalsh(rho_pt)
    return bool(np.all(eigvals >= -atol))


# ---------------------------------------------------------------------------
# 9. NOTE: REQUIRES QUANTUM HARDWARE FOR SPEEDUP
# ---------------------------------------------------------------------------
# Everything above runs correctly and meaningfully on classical hardware
# -- the formalism is doing organizational/explanatory work (entropy as
# a principled blastema metric, Born rule as a principled collapse rule,
# non-separability as a principled coupling diagnosis), not computational
# work. The ONE place a genuine quantum speedup claim would be honest is
# below, and it is NOT implemented as quantum hardware code here -- it's
# flagged so it isn't silently smuggled in as "quantum-powered" elsewhere.


def grover_role_search_NOTE_REQUIRES_QUANTUM_HARDWARE(candidate_roles: list, oracle_fn) -> Role:
    """
    NOTE: REQUIRES QUANTUM HARDWARE FOR THE CLAIMED SPEEDUP.

    If redifferentiation search space (candidate target roles, or more
    realistically candidate CONFIGURATIONS within a role) becomes large,
    Grover's algorithm gives quadratic speedup for finding the oracle-
    marked correct configuration among N unsorted candidates: O(sqrt(N))
    oracle calls vs O(N) classical. This ONLY holds running on real
    quantum hardware (or a faithful quantum circuit simulator, which
    re-pays the exponential cost classically and gives no real
    speedup). Do not implement this as a classical loop and call it
    "Grover search" -- that is a correctness-with-the-wrong-complexity-
    claim bug, exactly the kind of overstatement to avoid given prior
    flags about understatement vs overstatement in this codebase.

    Left unimplemented deliberately. Wire to real quantum backend (or
    drop the speedup claim and use classical search) when/if this
    becomes the actual bottleneck.
    """
    raise NotImplementedError(
        "Intentionally unimplemented -- see docstring. Do not stub this "
        "with a classical loop under this function name."
    )


# ---------------------------------------------------------------------------
# 10. FULL RECOVERY PIPELINE (ORCHESTRATION SKETCH)
# ---------------------------------------------------------------------------


def regeneration_pipeline(
    module_id: str,
    fault_severity: float,
    context: Optional[ContextSignal],
    rng: np.random.Generator,
    enable_refractory_period: bool = True,
) -> dict:
    """
    End-to-end sketch wiring stages 3-7 together. Returns a trace dict
    for telemetry/logging -- in production this should emit into the
    same telemetry stream as syndrome-weight data, not a separate log.

    ELEVATED: Now includes refractory period stabilization (v4.x enhancement)
    to prevent regeneration oscillation where modules recover and immediately
    collapse back due to insufficient stabilization.
    """
    trace = {"module_id": module_id}

    state = ModuleState.healthy(module_id)
    trace["initial_entropy"] = state.von_neumann_entropy()

    state = apply_fault(state, fault_severity)
    trace["post_fault_entropy"] = state.von_neumann_entropy()

    state = quarantine_channel(state)
    trace["post_quarantine_role_probs"] = state.role_probabilities()

    try:
        state = redifferentiate(state, context)
    except InnervationFailure as e:
        trace["status"] = "innervation_failure"
        trace["detail"] = str(e)
        return trace

    if context is not None:
        trace["fidelity_pre_collapse"] = regeneration_fidelity(state, context.target_role)

    collapsed_role, state = measure_role(state, rng)
    trace["collapsed_role"] = collapsed_role.value

    if context is not None:
        state = validate_collapse_or_quarantine(collapsed_role, context.target_role, state)
        trace["status"] = (
            "success" if collapsed_role == context.target_role else "malformed_quarantined"
        )
    else:
        trace["status"] = "collapsed_no_target_to_validate_against"

    # ELEVATED: Apply refractory period stabilization after successful recovery
    if enable_refractory_period and trace["status"] == "success":
        target_role = context.target_role if context else Role.HEALTHY_SPECIALIZED
        state = apply_refractory_stabilization(state, target_role=target_role, duration=60.0)
        trace["refractory_period_end"] = state.refractory_period_end
        trace["refractory_duration"] = 60.0

    trace["final_entropy"] = state.von_neumann_entropy()
    return trace
