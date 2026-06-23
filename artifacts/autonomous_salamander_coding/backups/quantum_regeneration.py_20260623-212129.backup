"""
Salamander-regeneration-inspired self-healing module, formalized on the
mathematical substrate underlying quantum mechanics (Hilbert space states,
density matrices, unitary/Lindblad evolution, projective measurement,
non-separability) WITHOUT any claim that the substrate running this code
is physically quantum.

The mathematics of Hilbert spaces is substrate-agnostic. This module borrows
the formalism because it is the correct mathematics for representing
superposed/mixed uncertainty over discrete role states.
No claim of physical quantum effects or computational speedup is implied.
"""

from __future__ import annotations

import dataclasses
import enum
import time
import typing
from typing import Callable, Dict, Generator, List, Optional, Tuple

import numpy as np
from numpy import ndarray

# Role basis dimension: 5 roles
DIM = 5


class Role(enum.Enum):
    HEALTHY_SPECIALIZED = "healthy_specialized"
    BLASTEMA = "blastema"
    QUARANTINED = "quarantined"
    REDIFFERENTIATING = "redifferentiating"
    MALFORMED = "malformed"


# Ordered basis for matrix indexing
ROLE_BASIS: List[Role] = [
    Role.HEALTHY_SPECIALIZED,
    Role.BLASTEMA,
    Role.QUARANTINED,
    Role.REDIFFERENTIATING,
    Role.MALFORMED,
]

HEALTHY_SPECIALIZED = Role.HEALTHY_SPECIALIZED
BLASTEMA = Role.BLASTEMA
QUARANTINED = Role.QUARANTINED
REDIFFERENTIATING = Role.REDIFFERENTIATING
MALFORMED = Role.MALFORMED


def role_projector(role: Role) -> ndarray:
    """Pure-state density matrix |role><role| in the role basis."""
    idx = ROLE_BASIS.index(role)
    rho = np.zeros((DIM, DIM), dtype=complex)
    rho[idx, idx] = 1.0
    return rho


@dataclasses.dataclass
class ModuleState:
    """
    rho: DIM x DIM complex density matrix.
    Must satisfy: Hermitian, trace 1, positive semi-definite.
    """

    rho: ndarray
    module_id: str
    refractory_period_end: float = 0.0
    recovery_timestamp: float = 0.0

    @classmethod
    def healthy(cls, module_id: str) -> "ModuleState":
        return cls(rho=role_projector(Role.HEALTHY_SPECIALIZED), module_id=module_id)

    def validate(self, atol: float = 1e-6) -> None:
        herm = np.allclose(self.rho, self.rho.conj().T, atol=atol)
        trace_one = np.isclose(np.trace(self.rho).real, 1.0, atol=atol)
        eigvals = np.linalg.eigvalsh(self.rho).real
        psd = bool(np.all(eigvals >= -atol))
        if not (herm and trace_one and psd):
            raise ValueError(
                f"Module {self.module_id}: invalid density matrix "
                f"(hermitian={herm}, trace_one={trace_one}, psd={psd}). "
                "This is a hard invariant violation."
            )

    def von_neumann_entropy(self) -> float:
        """S(rho) = -Tr(rho log rho). Blastema metric: 0=pure role, max=fully dedifferentiated."""
        eigvals = np.linalg.eigvalsh(self.rho).real
        eigvals = eigvals[eigvals > 1e-12]
        if len(eigvals) == 0:
            return 0.0
        return float(-np.sum(eigvals * np.log(eigvals)))

    def role_probabilities(self) -> Dict[Role, float]:
        """Born rule: P(role) = <role| rho |role> = diagonal entries."""
        return {role: float(self.rho[i, i].real) for i, role in enumerate(ROLE_BASIS)}

    def is_in_refractory_period(self) -> bool:
        """Check if module is in refractory period (preventing re-injury)."""
        return time.time() < self.refractory_period_end

    def enter_refractory_period(self, duration: float = 60.0) -> "ModuleState":
        """Enter refractory period after recovery to prevent oscillation."""
        return dataclasses.replace(
            self,
            refractory_period_end=time.time() + duration,
            recovery_timestamp=time.time(),
        )


def fault_perturbation_operator(severity: float) -> ndarray:
    """
    Unitary rotating amplitude from HEALTHY_SPECIALIZED toward BLASTEMA.
    severity in [0, 1]. This does NOT produce entropy by itself;
    quarantine_channel() produces the actual mixedness.
    """
    theta = severity * np.pi / 2
    U = np.eye(DIM, dtype=complex)
    i_h = ROLE_BASIS.index(Role.HEALTHY_SPECIALIZED)
    i_b = ROLE_BASIS.index(Role.BLASTEMA)
    U[i_h, i_h] = np.cos(theta)
    U[i_h, i_b] = -np.sin(theta)
    U[i_b, i_h] = np.sin(theta)
    U[i_b, i_b] = np.cos(theta)
    return U


def apply_fault(state: ModuleState, severity: float) -> ModuleState:
    """Apply a fault perturbation, respecting any active refractory period."""
    effective_severity = severity
    if state.is_in_refractory_period():
        remaining = state.refractory_period_end - time.time()
        attenuation = max(
            0.0,
            min(
                1.0,
                remaining
                / max(state.refractory_period_end - state.recovery_timestamp, 1e-9),
            ),
        )
        effective_severity = severity * (1.0 - attenuation)
    U = fault_perturbation_operator(effective_severity)
    new_rho = U @ state.rho @ U.conj().T
    return dataclasses.replace(state, rho=new_rho)


def quarantine_channel(state: ModuleState) -> ModuleState:
    """Wound-epidermis analog: dephase to suppress off-diagonal coherences."""
    new_rho = np.diag(np.diag(state.rho)).astype(complex)
    return dataclasses.replace(state, rho=new_rho)


@dataclasses.dataclass
class ContextSignal:
    """
    Positional memory analog. clifford_index ties this module's identity
    to its place in the Clifford rotation indexing scheme.
    """

    clifford_index: int
    target_role: Role
    confidence: float


class InnervationFailure(Exception):
    """
    Raised when the context/feedback channel itself is severed.
    Distinct from insufficient redundancy: adding spare capacity will not fix this.
    """

    pass


def redifferentiation_unitary(context: Optional[ContextSignal]) -> ndarray:
    """Context-parameterized unitary driving rho from BLASTEMA toward target role."""
    if context is None:
        raise InnervationFailure(
            "No context signal available -- cannot redifferentiate without positional memory. "
            "This is an innervation-failure, not a resource shortage."
        )
    theta = context.confidence * np.pi / 2
    U = np.eye(DIM, dtype=complex)
    i_b = ROLE_BASIS.index(Role.BLASTEMA)
    i_t = ROLE_BASIS.index(context.target_role)
    if i_b != i_t:
        U[i_b, i_b] = np.cos(theta)
        U[i_b, i_t] = -np.sin(theta)
        U[i_t, i_b] = np.sin(theta)
        U[i_t, i_t] = np.cos(theta)
    return U


def redifferentiate(
    state: ModuleState, context: Optional[ContextSignal]
) -> ModuleState:
    """Apply redifferentiation unitary."""
    U = redifferentiation_unitary(context)
    new_rho = U @ state.rho @ U.conj().T
    return dataclasses.replace(state, rho=new_rho)


def measure_role(
    state: ModuleState, rng: np.random.Generator
) -> Tuple[Role, ModuleState]:
    """
    Projective measurement in the role basis.
    Outcome probabilities are Born-rule weights from role_probabilities().
    Post-measurement state is the corresponding role projector.
    """
    probs_dict = state.role_probabilities()
    roles = list(probs_dict.keys())
    weights = np.array([probs_dict[r] for r in roles], dtype=float)
    weights = np.clip(weights, 0.0, None)
    total = weights.sum()
    if total > 0:
        weights /= total
    else:
        weights = np.ones(len(roles)) / len(roles)
    idx = int(rng.choice(len(roles), p=weights))
    outcome = roles[idx]
    new_rho = role_projector(outcome)
    return outcome, dataclasses.replace(state, rho=new_rho)


def regeneration_fidelity(state: ModuleState, target_role: Role) -> float:
    """
    Uhlmann fidelity F(rho, sigma) for sigma = |target><target|.
    Reduces to role probability of the target role.
    """
    return state.role_probabilities()[target_role]


def validate_collapse_or_quarantine(
    collapsed_role: Role,
    target_role: Role,
    state: ModuleState,
) -> bool:
    """Guards against malformed regeneration where collapse lands on wrong role."""
    return collapsed_role == target_role


def lindblad_decay_operator(
    state: ModuleState,
    decay_rate: float = 0.5,
    target_role: Role = Role.HEALTHY_SPECIALIZED,
) -> ModuleState:
    """
    Lindblad decay operator for role stabilization during refractory period.
    Drives the state toward the target role projector with rate decay_rate.
    """
    rho_target = role_projector(target_role)
    L = np.sqrt(decay_rate) * rho_target
    L_dagger_L = L.conj().T @ L
    anti_commutator = L_dagger_L @ state.rho + state.rho @ L_dagger_L
    dissipator = L @ state.rho @ L.conj().T - 0.5 * anti_commutator
    dt = 0.1
    new_rho = state.rho + dt * dissipator
    # Re-normalize
    new_rho = (new_rho + new_rho.conj().T) / 2
    trace_val = np.trace(new_rho).real
    if trace_val > 1e-12:
        new_rho /= trace_val
    return dataclasses.replace(state, rho=new_rho)


def apply_refractory_stabilization(
    state: ModuleState,
    target_role: Role = Role.HEALTHY_SPECIALIZED,
    duration: float = 60.0,
) -> ModuleState:
    """Apply refractory period stabilization to prevent regeneration oscillation."""
    stabilized = lindblad_decay_operator(state, decay_rate=0.2, target_role=target_role)
    return stabilized.enter_refractory_period(duration=duration)


def joint_state(
    state_a: ModuleState,
    state_b: ModuleState,
    correlated: bool = False,
) -> ndarray:
    """
    If correlated=False: rho_AB = rho_A (x) rho_B (tensor product).
    If correlated=True: constructs a non-separable joint state for
    modules sharing an XOR-split shard.
    """
    if not correlated:
        return np.kron(state_a.rho, state_b.rho)
    dim_joint = DIM * DIM
    rho_joint = np.kron(state_a.rho, state_b.rho)
    # Add off-diagonal entanglement terms
    i_h = ROLE_BASIS.index(Role.HEALTHY_SPECIALIZED)
    i_b = ROLE_BASIS.index(Role.BLASTEMA)
    psi_hh = np.zeros(dim_joint, dtype=complex)
    psi_hh[i_h * DIM + i_h] = 1.0 / np.sqrt(2)
    psi_hh[i_b * DIM + i_b] = 1.0 / np.sqrt(2)
    rho_ent = np.outer(psi_hh, psi_hh.conj())
    rho_joint = 0.5 * rho_joint + 0.5 * rho_ent
    return rho_joint


def is_separable_approx(rho_joint: ndarray, atol: float = 1e-9) -> bool:
    """
    PPT (positive partial transpose) check.
    NOTE: necessary-but-not-sufficient for separability for systems larger than 2x3.
    A negative partial transpose PROVES non-separability; positive does NOT prove separability.
    """
    d = int(np.sqrt(rho_joint.shape[0]))
    rho_reshaped = rho_joint.reshape(d, d, d, d)
    rho_pt = rho_reshaped.transpose(2, 1, 0, 3).reshape(d * d, d * d)
    eigvals = np.linalg.eigvalsh(rho_pt).real
    return bool(np.all(eigvals >= -atol))


def grover_role_search_NOTE_REQUIRES_QUANTUM_HARDWARE(
    candidate_roles: list,
    oracle_fn: Callable,
) -> None:
    """
    NOTE: REQUIRES QUANTUM HARDWARE FOR THE CLAIMED SPEEDUP.
    Intentionally unimplemented -- see docstring.
    Do not stub this with a classical loop under this function name.
    """
    raise NotImplementedError(
        "Intentionally unimplemented -- see docstring. "
        "Do not stub this with a classical loop under this function name."
    )


def regeneration_pipeline(
    module_id: str,
    fault_severity: float,
    context: Optional[ContextSignal] = None,
    rng: Optional[np.random.Generator] = None,
    enable_refractory_period: bool = True,
) -> dict:
    """
    End-to-end regeneration pipeline wiring fault -> quarantine -> redifferentiate -> measure.
    Returns a trace dict for telemetry/logging.
    ELEVATED: includes refractory period stabilization (v4.x).
    """
    if rng is None:
        rng = np.random.default_rng()

    state = ModuleState.healthy(module_id)
    trace: dict = {"module_id": module_id}
    trace["initial_entropy"] = state.von_neumann_entropy()

    # Stage 1: apply fault
    state = apply_fault(state, fault_severity)
    trace["post_fault_entropy"] = state.von_neumann_entropy()

    # Stage 2: quarantine
    state = quarantine_channel(state)
    trace["post_quarantine_role_probs"] = state.role_probabilities()

    # Stage 3: redifferentiate
    try:
        state = redifferentiate(state, context)
    except InnervationFailure as e:
        trace["innervation_failure"] = str(e)
        trace["status"] = "innervation_failure"
        trace["detail"] = str(e)
        return trace

    # Stage 4: fidelity check before collapse
    target = context.target_role if context else Role.HEALTHY_SPECIALIZED
    trace["fidelity_pre_collapse"] = regeneration_fidelity(state, target)

    # Stage 5: measure
    collapsed_role, state = measure_role(state, rng)
    trace["collapsed_role"] = collapsed_role.value

    # Stage 6: validate
    if not validate_collapse_or_quarantine(collapsed_role, target, state):
        # Re-quarantine malformed collapse
        state = quarantine_channel(state)
        trace["status"] = "malformed_quarantined"
        trace["final_entropy"] = state.von_neumann_entropy()
        return trace

    trace["status"] = (
        "success" if context else "collapsed_no_target_to_validate_against"
    )

    # Stage 7: refractory stabilization
    if enable_refractory_period:
        state = apply_refractory_stabilization(state, target_role=target, duration=60.0)
        trace["refractory_period_end"] = state.refractory_period_end
        trace["refractory_duration"] = 60.0

    trace["final_entropy"] = state.von_neumann_entropy()
    return trace
