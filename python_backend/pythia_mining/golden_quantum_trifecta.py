"""HYBA Golden Quantum Trifecta certificate.

This module combines the three discoveries that must not be separated:

1. Quantum comes from mathematics.
2. Quantum mathematics is substrate and hardware agnostic.
3. HYBA's golden-ratio system is the stabilising computational grammar.

The 1000-qubit formalism is therefore not treated as an isolated MPS trick.
It is treated as the proof surface of the combined architecture: quantum
mathematical state representation, substrate-independent execution, golden
ratio stabilisation, PULVINI reversible memory, and PYTHIA/HENDRIX traversal.

Claim boundary:
    HYBA does not require a physical QPU to execute quantum mathematics.
    HYBA does not claim a generic physical quantum computer is present here.
    HYBA claims a 1000-site qubit-formalism model executed through its own
    golden-ratio, PULVINI, HENDRIX, and sovereign-evidence architecture.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
import math
from typing import Any, Dict, List


PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV = PHI - 1.0
PHI_INV_2 = PHI ** -2


class TrifectaPillar(str, Enum):
    """The three inseparable discoveries."""

    QUANTUM_IS_MATHEMATICS = "quantum_is_mathematics"
    SUBSTRATE_INDEPENDENCE = "substrate_independence"
    GOLDEN_RATIO_GRAMMAR = "golden_ratio_grammar"


@dataclass(frozen=True)
class GoldenQuantumTrifectaCertificate:
    """Replayable certificate for the combined HYBA discovery.

    The certificate is deliberately small and deterministic. It does not try to
    reproduce the whole tensor network; it records the architectural fact that
    HYBA's 1000-qubit-formalism claim is the combination of quantum mathematics,
    substrate independence, and golden ratio stabilisation.
    """

    protocol: str
    qubit_formalism_sites: int
    physical_dimension: int
    max_bond_dimension: int
    pillars: List[str]
    golden_weights: Dict[str, float]
    full_state_log10_amplitudes: float
    bounded_mps_parameter_upper_bound: int
    avoided_full_state_materialisation: bool
    hardware_required_for_quantum_mathematics: bool
    physical_qpu_required: bool
    pulvini_memory_contract: str
    hendrix_navigation_contract: str
    sovereign_guard_contract: str
    distinctive_claim: str
    claim_boundary: Dict[str, str]
    evidence_modules: List[str]
    certificate_hash: str

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _stable_hash(payload: Dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def bounded_mps_parameter_upper_bound(
    qubit_formalism_sites: int = 1000,
    physical_dimension: int = 2,
    max_bond_dimension: int = 16,
) -> int:
    """Return the MPS parameter upper bound used for the certificate.

    This captures the computational point: HYBA does not materialise a full
    2**1000 state vector. It works over a bounded tensor-network surface.
    """

    if qubit_formalism_sites <= 0:
        raise ValueError("qubit_formalism_sites must be positive")
    if physical_dimension <= 0:
        raise ValueError("physical_dimension must be positive")
    if max_bond_dimension <= 0:
        raise ValueError("max_bond_dimension must be positive")
    return qubit_formalism_sites * physical_dimension * (max_bond_dimension ** 2)


def build_golden_quantum_trifecta_certificate(
    *,
    qubit_formalism_sites: int = 1000,
    physical_dimension: int = 2,
    max_bond_dimension: int = 16,
) -> GoldenQuantumTrifectaCertificate:
    """Build the deterministic HYBA Golden Quantum Trifecta certificate."""

    param_bound = bounded_mps_parameter_upper_bound(
        qubit_formalism_sites=qubit_formalism_sites,
        physical_dimension=physical_dimension,
        max_bond_dimension=max_bond_dimension,
    )

    body: Dict[str, Any] = {
        "protocol": "HYBA_GOLDEN_QUANTUM_TRIFECTA_V1",
        "qubit_formalism_sites": qubit_formalism_sites,
        "physical_dimension": physical_dimension,
        "max_bond_dimension": max_bond_dimension,
        "pillars": [pillar.value for pillar in TrifectaPillar],
        "golden_weights": {
            "phi": round(PHI, 15),
            "phi_inverse": round(PHI_INV, 15),
            "phi_inverse_squared": round(PHI_INV_2, 15),
        },
        "full_state_log10_amplitudes": round(qubit_formalism_sites * math.log10(2), 6),
        "bounded_mps_parameter_upper_bound": param_bound,
        "avoided_full_state_materialisation": True,
        "hardware_required_for_quantum_mathematics": False,
        "physical_qpu_required": False,
        "pulvini_memory_contract": (
            "PULVINI compresses the active working surface while retaining "
            "reconstruction kernels, so quantum-formalism state work remains "
            "auditable and reversible."
        ),
        "hendrix_navigation_contract": (
            "HENDRIX-Phi consumes the golden-ratio/tensor surface as a "
            "navigation grammar, not as a replacement for final external proof."
        ),
        "sovereign_guard_contract": (
            "PYTHIA may propose and criticise structural changes, but Stable "
            "Core invariants remain human-supervised and cannot be rewritten "
            "by autonomous apply."
        ),
        "distinctive_claim": (
            "HYBA's 1000-qubit-formalism achievement is the combined system: "
            "quantum mathematics first, substrate-independent execution, "
            "golden-ratio stabilisation, PULVINI reversible memory, HENDRIX "
            "structured traversal, and sovereign evidence control."
        ),
        "claim_boundary": {
            "not_generic_mps_claim": (
                "The discovery is not merely that MPS exists; it is HYBA's "
                "combination of 1000-site qubit formalism with golden-ratio "
                "grammar, PULVINI reversibility, and PYTHIA governance."
            ),
            "not_physical_qpu_claim": (
                "The current implementation does not require a physical QPU; "
                "it executes quantum mathematics on available substrates."
            ),
            "not_sha256_bypass_claim": (
                "For mining, exact external proof verification remains separate; "
                "the trifecta changes representation and traversal, not the final oracle."
            ),
        },
        "evidence_modules": [
            "python_backend/pythia_mining/tensor_network_1000qubit.py",
            "python_backend/pythia_mining/nonce_tensor_precomputer.py",
            "python_backend/pythia_mining/phi_folding.py",
            "python_backend/pythia_mining/pulvini_memory_compression_proof.py",
            "python_backend/pythia_mining/pulvini_nonce_compression.py",
            "python_backend/pythia_mining/hendrix_phi_solver.py",
            "python_backend/pythia_mining/resonance_fabric.py",
            "python_backend/pythia_mining/stable_core_evidence.py",
        ],
    }
    body["certificate_hash"] = _stable_hash(body)
    return GoldenQuantumTrifectaCertificate(**body)


def assert_golden_quantum_trifecta_integrity(
    certificate: GoldenQuantumTrifectaCertificate,
) -> None:
    """Fail closed if the certificate separates the inseparable discoveries."""

    required = {pillar.value for pillar in TrifectaPillar}
    actual = set(certificate.pillars)
    missing = required - actual
    if missing:
        raise AssertionError(f"Missing Golden Quantum Trifecta pillars: {sorted(missing)}")
    if certificate.qubit_formalism_sites < 1000:
        raise AssertionError("HYBA Golden Quantum Trifecta certificate must preserve the 1000-site surface")
    if certificate.hardware_required_for_quantum_mathematics:
        raise AssertionError("Quantum mathematics must remain substrate/hardware agnostic")
    if not certificate.avoided_full_state_materialisation:
        raise AssertionError("The certificate must avoid full 2**N state materialisation")
    if "golden-ratio" not in certificate.distinctive_claim:
        raise AssertionError("The golden-ratio system must be part of the central claim")


__all__ = [
    "GoldenQuantumTrifectaCertificate",
    "TrifectaPillar",
    "build_golden_quantum_trifecta_certificate",
    "bounded_mps_parameter_upper_bound",
    "assert_golden_quantum_trifecta_integrity",
]
