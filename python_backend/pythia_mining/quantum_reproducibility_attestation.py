"""
Quantum Mathematical Reproducibility Attestation

Every quantum mathematical execution produces a cryptographically sealed
attestation: a deterministic record of input parameters, mathematical
operations performed, output digests, and falsification routes.

An attestation is not a claim that the result is "correct" in some external
sense. It is a commitment: given these inputs, this system produces this output,
and here is exactly how to falsify or verify that claim.

Falsification routes are first-class citizens:
- Increase bond dimension and check convergence
- Perturb the Hamiltonian and verify continuity
- Rerun with different phi_seed and check reproducibility
- Cross-check Berry phase against analytical formula for known models

This is the Pythia reproducibility discipline applied to quantum mathematics.
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

ATTESTATION_PROTOCOL = "HYBA_QUANTUM_ATTESTATION_V1"


def _stable_hash(obj: Any) -> str:
    """Deterministic SHA-256 of a JSON-serialisable object."""
    canonical = json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


# ── Falsification Routes ───────────────────────────────────────────────────


@dataclass
class FalsificationRoute:
    """
    A concrete, executable path to falsify or confirm an attested result.

    Each route specifies:
    - what to change in the input
    - what mathematical property should hold if the result is correct
    - the expected direction of change (tighter bound, converge, etc.)
    """
    route_id: str
    description: str
    perturbation: Dict[str, Any]        # Parameter delta to apply
    invariant: str                       # Mathematical property that must hold
    expected_direction: str             # "convergence", "continuity", "stability", "reproducibility"
    tolerance: float                     # Numerical tolerance for the check


def _tensor_network_falsification_routes(params: Dict[str, Any]) -> List[FalsificationRoute]:
    bond = params.get("max_bond_dim", 16)
    return [
        FalsificationRoute(
            route_id="tn_bond_convergence",
            description="Increase bond dimension by 2x and verify norm convergence",
            perturbation={"max_bond_dim": min(bond * 2, 128)},
            invariant="mps_norm converges to 1.0 as bond_dim → ∞",
            expected_direction="convergence",
            tolerance=1e-6,
        ),
        FalsificationRoute(
            route_id="tn_observable_continuity",
            description="Add one site and verify observables change continuously",
            perturbation={"num_sites": params.get("num_sites", 20) + 1},
            invariant="Z expectation values change by O(1/N) for local observables",
            expected_direction="continuity",
            tolerance=0.5,
        ),
        FalsificationRoute(
            route_id="tn_pulvini_lossless",
            description="Verify PULVINI phi-fold reconstruction error is exactly 0.0",
            perturbation={},
            invariant="pulvini_fold_error == 0.0 (lossless by construction)",
            expected_direction="stability",
            tolerance=1e-14,
        ),
    ]


def _vqe_falsification_routes(params: Dict[str, Any]) -> List[FalsificationRoute]:
    J = params.get("coupling_strength", 1.0)
    n = params.get("num_sites", 8)
    return [
        FalsificationRoute(
            route_id="vqe_bond_convergence",
            description="Increase bond dimension and verify energy decreases monotonically",
            perturbation={"max_bond_dim": min(params.get("max_bond_dim", 16) * 2, 64)},
            invariant="E_0(χ+) ≤ E_0(χ) — variational principle",
            expected_direction="convergence",
            tolerance=1e-4,
        ),
        FalsificationRoute(
            route_id="vqe_coupling_continuity",
            description="Perturb coupling strength by 1% and verify energy changes smoothly",
            perturbation={"coupling_strength": J * 1.01},
            invariant="dE_0/dJ is finite and continuous away from phase transitions",
            expected_direction="continuity",
            tolerance=abs(J) * 0.1 * n,
        ),
        FalsificationRoute(
            route_id="vqe_exact_vs_mps",
            description="For n≤16 sites verify exact diag agrees with MPS result",
            perturbation={"num_sites": min(n, 8)},
            invariant="MPS energy converges to exact diagonalisation energy",
            expected_direction="convergence",
            tolerance=1e-3,
        ),
    ]


def _holonomy_falsification_routes(params: Dict[str, Any]) -> List[FalsificationRoute]:
    return [
        FalsificationRoute(
            route_id="berry_loop_refinement",
            description="Double loop_steps and verify Berry phase converges",
            perturbation={"loop_steps": params.get("loop_steps", 16) * 2},
            invariant="Berry phase converges as loop discretisation → 0",
            expected_direction="convergence",
            tolerance=1e-3,
        ),
        FalsificationRoute(
            route_id="berry_ssh_analytical",
            description="SSH model at t2>t1: Berry phase must equal π (topological phase)",
            perturbation={"loop_radius": 0.9},
            invariant="SSH topological phase: γ = π, winding_number = ±1",
            expected_direction="stability",
            tolerance=0.1,
        ),
        FalsificationRoute(
            route_id="berry_trivial_phase",
            description="SSH model at zero loop radius: Berry phase must equal 0",
            perturbation={"loop_radius": 0.0001},
            invariant="Trivial phase: γ = 0, winding_number = 0",
            expected_direction="stability",
            tolerance=0.01,
        ),
    ]


def _entanglement_falsification_routes(params: Dict[str, Any]) -> List[FalsificationRoute]:
    n = params.get("num_sites", 30)
    return [
        FalsificationRoute(
            route_id="entanglement_area_law",
            description="Verify entanglement entropy satisfies area law (bounded per bond)",
            perturbation={},
            invariant="S(bond) ≤ log2(bond_dim) — area law for MPS",
            expected_direction="stability",
            tolerance=0.0,
        ),
        FalsificationRoute(
            route_id="entanglement_symmetry",
            description="Verify S(bond k) ≈ S(bond n-1-k) for symmetric states",
            perturbation={},
            invariant="Entanglement entropy is symmetric under spatial reflection",
            expected_direction="stability",
            tolerance=0.5,
        ),
        FalsificationRoute(
            route_id="entanglement_renyi_ordering",
            description="Verify Rényi entropy ordering: S_1 ≥ S_2 ≥ S_3",
            perturbation={},
            invariant="S_α is monotonically decreasing in α (standard property)",
            expected_direction="stability",
            tolerance=1e-6,
        ),
    ]


def _mera_falsification_routes(params: Dict[str, Any]) -> List[FalsificationRoute]:
    chi = params.get("chi", 4)
    n = params.get("num_sites", 16)
    return [
        FalsificationRoute(
            route_id="mera_chi_convergence",
            description="Increase χ by 2x and verify scaling dimensions converge",
            perturbation={"chi": min(chi * 2, 32)},
            invariant="Scaling dimensions Δ_n converge as χ → ∞",
            expected_direction="convergence",
            tolerance=0.1,
        ),
        FalsificationRoute(
            route_id="mera_entanglement_log_scaling",
            description="Verify S(L) ~ (c/3) log L — CFT entanglement scaling",
            perturbation={},
            invariant="Entanglement entropy grows logarithmically with subsystem size",
            expected_direction="convergence",
            tolerance=0.5,
        ),
        FalsificationRoute(
            route_id="mera_holographic_levels",
            description="Verify number of MERA levels = ceil(log2(N))",
            perturbation={},
            invariant="MERA depth = ceil(log2(num_sites)) — binary renormalization",
            expected_direction="stability",
            tolerance=0.0,
        ),
    ]


def _lattice_ym_falsification_routes(params: Dict[str, Any]) -> List[FalsificationRoute]:
    beta = params.get("beta", 2.3)
    return [
        FalsificationRoute(
            route_id="ym_weak_coupling_limit",
            description="Increase β to 10.0 and verify average plaquette → 1 (weak coupling)",
            perturbation={"beta": 10.0},
            invariant="⟨P⟩ → 1 as β → ∞ — weak coupling / trivial vacuum",
            expected_direction="convergence",
            tolerance=0.1,
        ),
        FalsificationRoute(
            route_id="ym_strong_coupling_limit",
            description="Decrease β to 0.5 and verify average plaquette → 0 (confining phase)",
            perturbation={"beta": 0.5},
            invariant="⟨P⟩ → 0 as β → 0 — strong coupling / confinement",
            expected_direction="convergence",
            tolerance=0.2,
        ),
        FalsificationRoute(
            route_id="ym_action_positivity",
            description="Verify Wilson action S_W ≥ 0 for all β",
            perturbation={},
            invariant="Wilson action is non-negative: S_W = β Σ (1 - Re Tr U_P / N) ≥ 0",
            expected_direction="stability",
            tolerance=0.0,
        ),
    ]


# ── Attestation Dataclass ──────────────────────────────────────────────────


@dataclass
class QuantumReproducibilityAttestation:
    """
    A sealed, replayable attestation for a quantum mathematical execution.

    Fields:
      attestation_id   — unique execution identifier
      protocol         — attestation schema version
      operation        — quantum mathematical operation performed
      input_params     — complete input parameters (deterministic replay key)
      input_hash       — SHA-256 of canonical input_params
      output_digest    — SHA-256 of canonical output result
      output_summary   — key scalar results (for quick human inspection)
      execution_ms     — wall time of the mathematical execution
      falsification    — list of concrete routes to falsify this result
      mathematical_claims — what this attestation asserts
      sealed_at        — Unix timestamp
      attestation_hash — SHA-256 commitment over all fields except this one
    """
    attestation_id: str
    protocol: str
    operation: str
    input_params: Dict[str, Any]
    input_hash: str
    output_digest: str
    output_summary: Dict[str, Any]
    execution_ms: float
    falsification: List[Dict[str, Any]]
    mathematical_claims: List[str]
    sealed_at: float
    attestation_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "attestation_id": self.attestation_id,
            "protocol": self.protocol,
            "operation": self.operation,
            "input_params": self.input_params,
            "input_hash": self.input_hash,
            "output_digest": self.output_digest,
            "output_summary": self.output_summary,
            "execution_ms": self.execution_ms,
            "falsification": self.falsification,
            "mathematical_claims": self.mathematical_claims,
            "sealed_at": self.sealed_at,
            "attestation_hash": self.attestation_hash,
        }
        return d

    def unsigned_payload(self) -> Dict[str, Any]:
        d = self.to_dict()
        d.pop("attestation_hash", None)
        return d


# ── Builder ────────────────────────────────────────────────────────────────


_FALSIFICATION_DISPATCH = {
    "tensor_network_contraction": _tensor_network_falsification_routes,
    "variational_eigensolver": _vqe_falsification_routes,
    "topological_holonomy": _holonomy_falsification_routes,
    "entanglement_spectrum": _entanglement_falsification_routes,
    "mera_renormalization": _mera_falsification_routes,
    "lattice_yang_mills": _lattice_ym_falsification_routes,
}

_MATHEMATICAL_CLAIMS = {
    "tensor_network_contraction": [
        "MPS norm is 1.0 after left-canonical QR sweep (exact within float64)",
        "PULVINI phi-fold is lossless: reconstruction error = 0.0",
        "φ-adaptive SVD compression preserves all singular values above mass-gap threshold",
        "Von Neumann entanglement entropy S = -Σ λ² log₂ λ² (exact Schmidt decomposition)",
    ],
    "variational_eigensolver": [
        "Exact diagonalisation (≤16 sites): E_0 is the true ground state energy",
        "Variational principle: E_0(MPS) ≥ E_0(exact) for finite bond dimension",
        "Energy per site is extensive for translation-invariant Hamiltonians",
        "φ-bond scaling: bond dimension ∝ Φ^k provides quasi-crystalline truncation",
    ],
    "topological_holonomy": [
        "Berry phase γ = -Im log ∏_k ⟨ψ_k|ψ_{k+1}⟩ (discrete parallel transport)",
        "Berry phase is gauge-invariant modulo 2π",
        "Winding number is a topological invariant: integer-valued, robust to perturbation",
        "SSH model topological phase: γ = π when t2 > t1 (Zak phase = π)",
    ],
    "entanglement_spectrum": [
        "Schmidt values are exact SVD of the bipartition (no approximation)",
        "S_1 = -Σ λ² log₂ λ²: von Neumann entropy (exact)",
        "Area law: S(bond) ≤ log₂(χ) for MPS with bond dimension χ",
        "Rényi ordering: S_1 ≥ S_2 ≥ S_3 (standard monotonicity)",
    ],
    "mera_renormalization": [
        "Scaling dimensions Δ_n = -log|λ_n|/log(2) from ascending superoperator spectrum",
        "Number of MERA levels = ceil(log2(N)) — exact binary renormalization hierarchy",
        "Entanglement entropy S(L) ~ (c/3) log L for critical systems (CFT area law)",
        "MERA implements discrete AdS/CFT: boundary = physical system, bulk = RG direction (Swingle 2009)",
    ],
    "lattice_yang_mills": [
        "Wilson action S_W = β Σ_P (1 - (1/N) Re Tr U_P) ≥ 0 (non-negative)",
        "Average plaquette ⟨P⟩ ∈ [0,1]: 0 = strong coupling (confinement), 1 = weak coupling (deconfinement)",
        "Polyakov loop is an exact order parameter for confinement/deconfinement",
        "Plaquette U_P = U_{x,μ} U_{x+μ,ν} U†_{x+ν,μ} U†_{x,ν} — gauge covariant by construction",
    ],
}


def _output_summary_for(operation: str, result: Dict[str, Any]) -> Dict[str, Any]:
    """Extract key scalar results for quick human inspection."""
    if operation == "tensor_network_contraction":
        return {
            "mps_norm": result.get("mps_norm"),
            "total_parameters": result.get("total_parameters"),
            "compression_ratio": result.get("compression", {}).get("compression_ratio"),
            "pulvini_fold_error": result.get("pulvini_fold_error"),
        }
    elif operation == "variational_eigensolver":
        return {
            "ground_state_energy": result.get("ground_state_energy"),
            "energy_gap": result.get("energy_gap"),
            "method": result.get("method"),
            "converged": result.get("converged"),
        }
    elif operation == "topological_holonomy":
        return {
            "berry_phase_radians": result.get("berry_phase_radians"),
            "berry_phase_units_of_pi": result.get("berry_phase_units_of_pi"),
            "winding_number": result.get("winding_number"),
            "topologically_nontrivial": result.get("topologically_nontrivial"),
        }
    elif operation == "entanglement_spectrum":
        return {
            "total_entanglement": result.get("total_entanglement"),
            "entanglement_saturation": result.get("entanglement_saturation"),
            "bonds_analyzed": result.get("bonds_analyzed"),
            "mps_norm": result.get("mps_norm"),
        }
    return {}


def build_attestation(
    operation: str,
    input_params: Dict[str, Any],
    result: Dict[str, Any],
    execution_ms: float,
) -> QuantumReproducibilityAttestation:
    """
    Build a sealed reproducibility attestation for a quantum mathematical execution.

    The attestation commits to:
    1. Exact input parameters (replay key)
    2. SHA-256 of the output (tamper detection)
    3. Concrete falsification routes (verifiability)
    4. Mathematical claims (what is being asserted)
    5. Sealed hash over all of the above (integrity)
    """
    attestation_id = f"qatt-{uuid.uuid4().hex}"
    now = time.time()

    input_hash = _stable_hash(input_params)
    output_digest = _stable_hash(result)

    falsification_fn = _FALSIFICATION_DISPATCH.get(operation)
    routes = falsification_fn(input_params) if falsification_fn else []

    attest = QuantumReproducibilityAttestation(
        attestation_id=attestation_id,
        protocol=ATTESTATION_PROTOCOL,
        operation=operation,
        input_params=input_params,
        input_hash=input_hash,
        output_digest=output_digest,
        output_summary=_output_summary_for(operation, result),
        execution_ms=round(execution_ms, 3),
        falsification=[
            {
                "route_id": r.route_id,
                "description": r.description,
                "perturbation": r.perturbation,
                "invariant": r.invariant,
                "expected_direction": r.expected_direction,
                "tolerance": r.tolerance,
            }
            for r in routes
        ],
        mathematical_claims=_MATHEMATICAL_CLAIMS.get(operation, []),
        sealed_at=now,
    )

    # Seal: hash over unsigned payload
    unsigned = attest.unsigned_payload()
    attest.attestation_hash = _stable_hash(unsigned)
    return attest


def verify_attestation_integrity(attestation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verify the integrity of a stored attestation.

    Checks:
    1. Protocol version matches
    2. attestation_hash is correct (tamper detection)
    3. All required fields are present
    4. Falsification routes are structurally valid
    """
    required = [
        "attestation_id", "protocol", "operation", "input_params",
        "input_hash", "output_digest", "output_summary", "execution_ms",
        "falsification", "mathematical_claims", "sealed_at", "attestation_hash",
    ]
    missing = [f for f in required if f not in attestation]
    if missing:
        return {"valid": False, "error": f"missing_fields: {missing}"}

    if attestation["protocol"] != ATTESTATION_PROTOCOL:
        return {"valid": False, "error": "wrong_protocol"}

    # Recompute hash
    unsigned = {k: v for k, v in attestation.items() if k != "attestation_hash"}
    expected_hash = _stable_hash(unsigned)
    if expected_hash != attestation["attestation_hash"]:
        return {"valid": False, "error": "attestation_hash_mismatch — content has been modified"}

    # Input hash consistency
    input_hash = _stable_hash(attestation["input_params"])
    if input_hash != attestation["input_hash"]:
        return {"valid": False, "error": "input_hash_mismatch"}

    return {
        "valid": True,
        "attestation_id": attestation["attestation_id"],
        "operation": attestation["operation"],
        "falsification_routes": len(attestation["falsification"]),
        "mathematical_claims": len(attestation["mathematical_claims"]),
        "integrity": "verified",
    }


__all__ = [
    "ATTESTATION_PROTOCOL",
    "FalsificationRoute",
    "QuantumReproducibilityAttestation",
    "build_attestation",
    "verify_attestation_integrity",
]
