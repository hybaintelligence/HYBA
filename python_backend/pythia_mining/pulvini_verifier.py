"""Unified PULVINI substate verifier.

``SubstateVerifier`` consolidates the structural, coverage, Grover-scope, Choi,
Bures, and operator-topology certificates into a single deterministic passport
that can be attached to runtime telemetry or block/share audit records.
"""

from __future__ import annotations

import hashlib
import json
import struct
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, ClassVar, Optional, Sequence

import numpy as np
from numpy.typing import NDArray

from .pulvini_bures import bures_certificate
from .pulvini_certificates import adjacency_map_digest, automorphism_runtime_certificate
from .pulvini_coverage_certificate import coverage_certificate
from .pulvini_grover_certificate import grover_scope_certificate
from .pulvini_operator import ManifoldOperator
from .pulvini_structural_certificate import structural_certificate
from .pulvini_topology import MAX_UINT32_NONCE, NUM_NODES


class IntegrityStatus(str, Enum):
    """Substate passport verification status."""

    VERIFIED = "verified"
    MARGINAL = "marginal"
    FAILED = "failed"


PULVINI_BINARY_MAGIC = b"PULV"
PULVINI_BINARY_HEADER_SIZE = 128
_PASSPORT_HEADER = struct.Struct(">4sQ32sII32s44s")
_FIXED_POINT_SCALE = 1_000_000_000
_ZERO_DIGEST = "0" * 64
_ZERO_SIGNATURE = b"\x00" * 44


@dataclass(frozen=True)
class SubstateBinaryHeader:
    """Fixed-width binary header for Stratum/share audit transport.

    Layout, in network byte order, is exactly 128 bytes:
    ``MAGIC[4] | TS_NS[8] | RHO_HASH[32] | PURITY[4] | FIDELITY[4] |
    TOP_HASH[32] | SIGNATURE[44]``.  The signature field is caller-supplied;
    when omitted the header is deliberately unsigned and padded with zeros.
    """

    STRUCT: ClassVar[struct.Struct] = _PASSPORT_HEADER

    timestamp_ns: int
    rho_hash: bytes
    purity_fixed: int
    fidelity_fixed: int
    topology_hash: bytes
    signature: bytes = _ZERO_SIGNATURE
    magic: bytes = PULVINI_BINARY_MAGIC

    def __post_init__(self) -> None:
        if self.magic != PULVINI_BINARY_MAGIC:
            raise ValueError("invalid PULVINI binary magic")
        if len(self.rho_hash) != 32:
            raise ValueError("rho_hash must be 32 bytes")
        if len(self.topology_hash) != 32:
            raise ValueError("topology_hash must be 32 bytes")
        if len(self.signature) != 44:
            raise ValueError("signature must be 44 bytes")
        if not 0 <= int(self.purity_fixed) <= _FIXED_POINT_SCALE:
            raise ValueError("purity_fixed must be in [0, 1e9]")
        if not 0 <= int(self.fidelity_fixed) <= _FIXED_POINT_SCALE:
            raise ValueError("fidelity_fixed must be in [0, 1e9]")

    def to_bytes(self) -> bytes:
        """Pack the header as exactly 128 bytes."""
        return self.STRUCT.pack(
            self.magic,
            int(self.timestamp_ns),
            self.rho_hash,
            int(self.purity_fixed),
            int(self.fidelity_fixed),
            self.topology_hash,
            self.signature,
        )

    @classmethod
    def from_bytes(cls, payload: bytes) -> "SubstateBinaryHeader":
        """Parse and validate a 128-byte binary passport header."""
        if len(payload) != PULVINI_BINARY_HEADER_SIZE:
            raise ValueError("PULVINI binary header must be exactly 128 bytes")
        (
            magic,
            timestamp_ns,
            rho_hash,
            purity,
            fidelity,
            topology_hash,
            signature,
        ) = cls.STRUCT.unpack(payload)
        return cls(
            timestamp_ns=timestamp_ns,
            rho_hash=rho_hash,
            purity_fixed=purity,
            fidelity_fixed=fidelity,
            topology_hash=topology_hash,
            signature=signature,
            magic=magic,
        )


@dataclass(frozen=True)
class SubstatePassport:
    """Single integrity object for one PULVINI runtime substate."""

    structural_hash: str
    passport_hash: str
    topology_verified: bool
    coverage_verified: bool
    grover_scope_verified: bool
    choi_verified: Optional[bool] = None
    bures_closed: Optional[bool] = None
    manifold_dimension: int = NUM_NODES
    coverage_ratio: float = 1.0
    information_content: float = 0.0
    grover_certificate_hash: str = ""
    rho_hash: str = _ZERO_DIGEST
    purity_fixed: int = 0
    fidelity_fixed: int = 0
    quantum_speedup_claimed: bool = False
    timestamp_ns: int = field(default_factory=time.time_ns)
    version: str = "SUBSTATE_PASSPORT_V1"
    status: str = IntegrityStatus.VERIFIED.value

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_blob(self) -> bytes:
        """Serialize the passport as canonical JSON bytes."""
        return json.dumps(
            self.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

    def to_binary_header(self, signature: Optional[bytes] = None) -> bytes:
        """Serialize the passport into the 128-byte Substate Handshake header."""
        return SubstateBinaryHeader(
            timestamp_ns=self.timestamp_ns,
            rho_hash=bytes.fromhex(self.rho_hash),
            purity_fixed=self.purity_fixed,
            fidelity_fixed=self.fidelity_fixed,
            topology_hash=bytes.fromhex(self.structural_hash),
            signature=_normalize_signature(signature),
        ).to_bytes()

    def verify_binary_header(self, payload: bytes, signature: Optional[bytes] = None) -> bool:
        """Validate a binary header against this passport's stable fields."""
        header = SubstateBinaryHeader.from_bytes(payload)
        return (
            header.timestamp_ns == self.timestamp_ns
            and header.rho_hash.hex() == self.rho_hash
            and header.purity_fixed == self.purity_fixed
            and header.fidelity_fixed == self.fidelity_fixed
            and header.topology_hash.hex() == self.structural_hash
            and header.signature == _normalize_signature(signature)
        )

    def verify_hash(self) -> bool:
        """Verify the embedded passport digest."""
        payload = self.to_dict()
        digest = payload.pop("passport_hash")
        material = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(material).hexdigest() == digest

    def verify(self, expected: "SubstatePassport") -> bool:
        """Compare two passports by stable digest and verified status."""
        return (
            self.passport_hash == expected.passport_hash
            and self.status == IntegrityStatus.VERIFIED.value
            and expected.status == IntegrityStatus.VERIFIED.value
            and self.verify_hash()
            and expected.verify_hash()
        )


class SubstateVerifier:
    """Unified proof-of-integrity engine for PULVINI substates."""

    VERSION = "SUBSTATE_VERIFIER_V1"

    def __init__(self, operator: Optional[ManifoldOperator] = None) -> None:
        self.operator = operator or ManifoldOperator()
        self._certificate_cache: dict[str, SubstatePassport] = {}

    def generate_passport(
        self,
        *,
        target: int = 0,
        nonce_ranges: Optional[Sequence[tuple[int, int]]] = None,
        rho: Optional[NDArray[np.complex128]] = None,
        reference_rho: Optional[NDArray[np.complex128]] = None,
        entropy_rate: float = 0.0,
        hamiltonian: Optional[NDArray[np.complex128]] = None,
        timestamp_ns: Optional[int] = None,
        use_cache: bool = True,
    ) -> SubstatePassport:
        """Generate a deterministic Substate Passport.

        The passport is honest about the Grover layer: it records the existing
        certificate's explicit ``quantum_speedup_claimed=False`` invariant.
        """
        nonce_ranges = list(nonce_ranges or [(0, MAX_UINT32_NONCE)])
        cache_key = self._cache_key(
            target,
            nonce_ranges,
            rho,
            reference_rho,
            entropy_rate,
            hamiltonian,
            timestamp_ns,
        )
        if use_cache and cache_key in self._certificate_cache:
            return self._certificate_cache[cache_key]

        adjacency = self.operator.adjacency_map
        auto_cert = automorphism_runtime_certificate(adjacency)
        structural = structural_certificate(adjacency)
        coverage = coverage_certificate()
        grover = grover_scope_certificate(target=target, nonce_ranges=nonce_ranges)

        choi_ok: Optional[bool] = None
        if hamiltonian is not None:
            choi_ok = self.operator.certify_channel(hamiltonian).positive_semidefinite

        bures_closed: Optional[bool] = None
        information_content = 0.0
        rho_hash = _ZERO_DIGEST
        purity_fixed = 0
        fidelity_fixed = 0
        if rho is not None:
            density = self.operator.ensure_density_state(rho)
            eigvals = np.linalg.eigvalsh(density).real
            eigvals = eigvals[eigvals > 0]
            information_content = float(-np.sum(eigvals * np.log2(eigvals)))
            bures_closed = bures_certificate(density, entropy_rate).closed
            rho_hash = hashlib.sha256(density.tobytes()).hexdigest()
            purity = float(np.clip(np.real(np.trace(density @ density)), 0.0, 1.0))
            purity_fixed = _to_fixed_point(purity)
            reference = (
                density
                if reference_rho is None
                else self.operator.ensure_density_state(reference_rho)
            )
            fidelity_fixed = _to_fixed_point(
                self.operator.compute_fidelity(density, reference)
            )

        topology_verified = bool(
            auto_cert.get("gate_closed")
            and structural.complete_graph
            and structural.adjacency_preserved
            and structural.automorphism_group_order == 120
        )
        coverage_verified = bool(
            coverage.complete_coverage
            and coverage.overlap_free
            and coverage.automorphism_preserves_coverage
        )
        grover_verified = bool(grover.deterministic_behavior and not grover.quantum_speedup_claimed)
        status = self._status(topology_verified, coverage_verified, grover_verified, choi_ok)

        payload = {
            "structural_hash": adjacency_map_digest(adjacency),
            "topology_verified": topology_verified,
            "coverage_verified": coverage_verified,
            "grover_scope_verified": grover_verified,
            "choi_verified": choi_ok,
            "bures_closed": bures_closed,
            "manifold_dimension": NUM_NODES,
            "coverage_ratio": 1.0 if coverage_verified else 0.0,
            "information_content": information_content,
            "grover_certificate_hash": self._hash_dict(grover.to_dict()),
            "rho_hash": rho_hash,
            "purity_fixed": purity_fixed,
            "fidelity_fixed": fidelity_fixed,
            "quantum_speedup_claimed": bool(grover.quantum_speedup_claimed),
            "timestamp_ns": time.time_ns() if timestamp_ns is None else int(timestamp_ns),
            "version": SubstatePassport.__dataclass_fields__["version"].default,
            "status": status.value,
        }
        passport_hash = self._hash_dict(payload)
        passport = SubstatePassport(passport_hash=passport_hash, **payload)
        if use_cache:
            self._certificate_cache[cache_key] = passport
        return passport

    def verify_passport(self, passport: SubstatePassport) -> bool:
        """Validate digest and all mandatory integrity gates."""
        return bool(
            passport.verify_hash()
            and passport.status == IntegrityStatus.VERIFIED.value
            and passport.topology_verified
            and passport.coverage_verified
            and passport.grover_scope_verified
            and not passport.quantum_speedup_claimed
        )

    def command_center_payload(self, passport: SubstatePassport) -> dict[str, Any]:
        """Return a compact JSON-ready payload for the UI."""
        return {
            "version": self.VERSION,
            "status": passport.status,
            "passport_hash": passport.passport_hash,
            "topology_verified": passport.topology_verified,
            "coverage_verified": passport.coverage_verified,
            "grover_scope_verified": passport.grover_scope_verified,
            "quantum_speedup_claimed": passport.quantum_speedup_claimed,
            "information_content": passport.information_content,
            "binary_header_size": PULVINI_BINARY_HEADER_SIZE,
            "purity": passport.purity_fixed / _FIXED_POINT_SCALE,
            "fidelity": passport.fidelity_fixed / _FIXED_POINT_SCALE,
        }

    def _status(
        self,
        topology_verified: bool,
        coverage_verified: bool,
        grover_verified: bool,
        choi_ok: Optional[bool],
    ) -> IntegrityStatus:
        required = topology_verified and coverage_verified and grover_verified
        if not required or choi_ok is False:
            return IntegrityStatus.FAILED
        if choi_ok is None:
            return IntegrityStatus.VERIFIED
        return IntegrityStatus.VERIFIED if choi_ok else IntegrityStatus.MARGINAL

    def _cache_key(
        self,
        target: int,
        nonce_ranges: Sequence[tuple[int, int]],
        rho: Optional[NDArray[np.complex128]],
        reference_rho: Optional[NDArray[np.complex128]],
        entropy_rate: float,
        hamiltonian: Optional[NDArray[np.complex128]],
        timestamp_ns: Optional[int],
    ) -> str:
        payload: dict[str, Any] = {
            "target": int(target),
            "nonce_ranges": [(int(start), int(end)) for start, end in nonce_ranges],
            "entropy_rate": float(entropy_rate),
            "adjacency": adjacency_map_digest(self.operator.adjacency_map),
            "timestamp_ns": timestamp_ns,
        }
        if rho is not None:
            payload["rho_sha256"] = hashlib.sha256(
                np.asarray(rho, dtype=np.complex128).tobytes()
            ).hexdigest()
        if reference_rho is not None:
            payload["reference_rho_sha256"] = hashlib.sha256(
                np.asarray(reference_rho, dtype=np.complex128).tobytes()
            ).hexdigest()
        if hamiltonian is not None:
            payload["hamiltonian_sha256"] = hashlib.sha256(
                np.asarray(hamiltonian, dtype=np.complex128).tobytes()
            ).hexdigest()
        return self._hash_dict(payload)

    @staticmethod
    def _hash_dict(payload: dict[str, Any]) -> str:
        material = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
        return hashlib.sha256(material).hexdigest()


def _to_fixed_point(value: float) -> int:
    return int(round(float(np.clip(value, 0.0, 1.0)) * _FIXED_POINT_SCALE))


def _normalize_signature(signature: Optional[bytes]) -> bytes:
    if signature is None:
        return _ZERO_SIGNATURE
    if len(signature) != 44:
        raise ValueError("signature must be exactly 44 bytes")
    return bytes(signature)


__all__ = [
    "IntegrityStatus",
    "PULVINI_BINARY_HEADER_SIZE",
    "PULVINI_BINARY_MAGIC",
    "SubstateBinaryHeader",
    "SubstatePassport",
    "SubstateVerifier",
]
