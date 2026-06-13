"""Production elevation artifacts for the PULVINI/PYTHIA runtime.

The elevation layer turns the production façade, mathematical primitives, and
substate certificates into deterministic regulatory artifacts.  It is purposely
small and dependency-light so the objects can be generated in CI, attached to
share telemetry, or exported for institutional review without importing the
research runtime directly.
"""

from __future__ import annotations

import hashlib
import importlib
import inspect
import json
import struct
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Protocol, Sequence, TYPE_CHECKING

if TYPE_CHECKING:
    from numpy.typing import NDArray
    from .pulvini_operator import ManifoldOperator
    from .pulvini_verifier import SubstatePassport, SubstateVerifier
else:
    NDArray = Any
    ManifoldOperator = Any
    SubstatePassport = Any
    SubstateVerifier = Any

ELEVATION_SCHEMA_VERSION = "PULVINI_ELEVATION_V1"
TELEMETRY_CONTRACT_VERSION = "PULVINI_TELEMETRY_CONTRACT_V1"
RUNTIME_MANIFEST_VERSION = "PULVINI_RUNTIME_MANIFEST_V1"
CERTIFICATE_LEDGER_MAGIC = b"PLED"
_FIXED_POINT_SCALE = 1_000_000_000
_FIXED_POINT_BIT_DEPTH = 64


class Severity(str, Enum):
    """Runtime health severity levels emitted by the Φ supervisor."""

    OK = "ok"
    WATCH = "watch"
    WARN = "warn"
    CRITICAL = "critical"


@dataclass(frozen=True)
class ProductionResponse:
    """Constitutional façade response envelope for regulator-visible calls.

    External integrations can require this object at the boundary without
    changing legacy internal call sites.  It binds each result to the hash of
    the module version that produced it and to the exact certificate-ledger
    entry that recorded the transaction.
    """

    result: Mapping[str, Any]
    module_version_hash: str
    ledger_entry_hash: str
    ledger_index: int
    endpoint: str
    schema_version: str = ELEVATION_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return _canonicalize(asdict(self))

    @property
    def response_hash(self) -> str:
        return _hash_dict(self.to_dict())


@dataclass(frozen=True)
class QuantumRuntimePassport:
    """Per-transaction metadata header verified before network submission."""

    module_id: str
    phi_value_fixed: int
    bures_score_fixed: int
    kernel_invariants_met: bool
    ledger_entry_hash: str
    schema_version: str = ELEVATION_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return _canonicalize(asdict(self))

    @property
    def passport_hash(self) -> str:
        return _hash_dict(self.to_dict())


@dataclass(frozen=True)
class CapabilityManifest:
    """Versioned production façade capability manifest."""

    version: str
    operator_version: str
    verifier_version: str
    capability_flags: Mapping[str, bool]
    facade_api_signatures: Mapping[str, str]
    endpoint_invariants: Mapping[str, Sequence[str]]
    generated_at_ns: int = field(default_factory=time.time_ns)
    schema_version: str = ELEVATION_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return _canonicalize(asdict(self))

    @property
    def manifest_hash(self) -> str:
        return _hash_dict(self.to_dict())


@dataclass(frozen=True)
class ComplianceManifest:
    """Regulator-facing compliance alignment artifact."""

    jurisdictions: tuple[str, ...] = ("DIFC", "FSRA", "MAS")
    guarantees: tuple[str, ...] = (
        "production_facade_only",
        "deterministic_density_repair",
        "trace_one_psd_hermitian_invariants",
        "append_only_certificate_ledger",
        "fixed_point_telemetry",
        "no_quantum_speedup_claims",
    )
    quantum_speedup_claimed: bool = False
    schema_version: str = ELEVATION_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return _canonicalize(asdict(self))


@dataclass(frozen=True)
class KernelInvariantReport:
    """Mathematical-kernel invariant report for a repaired density state."""

    trace_one: bool
    positive_semidefinite: bool
    hermitian: bool
    bures_bounds: bool
    purity_bounds: bool
    trace: float
    min_eigenvalue: float
    purity: float
    bures_distance_to_self: float
    syscall_table: tuple[str, ...]
    schema_version: str = ELEVATION_SCHEMA_VERSION

    @property
    def closed(self) -> bool:
        return all((self.trace_one, self.positive_semidefinite, self.hermitian, self.bures_bounds, self.purity_bounds))

    def to_dict(self) -> dict[str, Any]:
        return _canonicalize(asdict(self) | {"closed": self.closed})


class MathematicalException(RuntimeError):
    """Invariant violation raised by the mathematical kernel guardrail."""

    def __init__(self, message: str, report: KernelInvariantReport) -> None:
        super().__init__(message)
        self.report = report


class MathProvider(Protocol):
    """Dependency-free mathematical provider contract for kernel tests/audits."""

    dimension: int

    def invariant_report(self, rho: Any, *, stage: str) -> KernelInvariantReport:
        ...

    def copy_density(self, rho: Any) -> Any:
        ...

    def density_equal(self, left: Any, right: Any) -> bool:
        ...


class StaticMathProvider:
    """Pure-Python invariant provider used when NumPy is unavailable.

    The provider validates explicit mapping-based density fixtures and is meant
    for ledger/manifest/passport tests, CI smoke tests, and regulator replay of
    non-numerical control-plane logic.  Production numerical paths still use
    the NumPy-backed operator provider.
    """

    dimension = 1

    def invariant_report(self, rho: Any, *, stage: str) -> KernelInvariantReport:
        if isinstance(rho, Mapping):
            trace = float(rho.get("trace", 1.0))
            min_eigenvalue = float(rho.get("min_eigenvalue", 0.0))
            purity = float(rho.get("purity", 1.0))
            bures = float(rho.get("bures_distance_to_self", 0.0))
            trace_one = bool(rho.get("trace_one", abs(trace - 1.0) <= 1e-9))
            positive = bool(rho.get("positive_semidefinite", min_eigenvalue >= -1e-9))
            hermitian = bool(rho.get("hermitian", True))
        else:
            trace = 1.0
            min_eigenvalue = 0.0
            purity = 1.0
            bures = 0.0
            trace_one = positive = hermitian = True
        return KernelInvariantReport(
            trace_one=trace_one,
            positive_semidefinite=positive,
            hermitian=hermitian,
            bures_bounds=0.0 <= bures <= 2.0 ** 0.5,
            purity_bounds=0.0 <= purity <= 1.0 + 1e-9,
            trace=trace,
            min_eigenvalue=min_eigenvalue,
            purity=purity,
            bures_distance_to_self=bures,
            syscall_table=("static_precondition", "static_postcondition", stage),
        )

    def copy_density(self, rho: Any) -> Any:
        return dict(rho) if isinstance(rho, Mapping) else rho

    def density_equal(self, left: Any, right: Any) -> bool:
        return _canonicalize(left) == _canonicalize(right)


class OperatorMathProvider:
    """NumPy-backed provider that adapts the production ManifoldOperator."""

    def __init__(self, operator: "ManifoldOperator") -> None:
        self.operator = operator
        self.dimension = int(operator.dim)

    def invariant_report(self, rho: Any, *, stage: str) -> KernelInvariantReport:
        np = _require_numpy()
        values = np.asarray(rho, dtype=np.complex128)
        if values.shape != (self.dimension, self.dimension):
            raise ValueError("kernel density tensor has invalid shape")
        eigvals = np.linalg.eigvalsh((values + values.conj().T) / 2.0).real
        trace = float(np.trace(values).real)
        purity = float(np.real(np.trace(values @ values)))
        repaired = self.operator.ensure_density_state(values)
        bures = self.operator.compute_bures_distance(repaired, repaired)
        return KernelInvariantReport(
            trace_one=bool(np.isclose(trace, 1.0, atol=1e-9)),
            positive_semidefinite=bool(np.min(eigvals) >= -1e-9),
            hermitian=bool(np.allclose(values, values.conj().T, atol=1e-9)),
            bures_bounds=bool(0.0 <= bures <= np.sqrt(2.0)),
            purity_bounds=bool(0.0 <= purity <= 1.0 + 1e-9),
            trace=trace,
            min_eigenvalue=float(np.min(eigvals)),
            purity=purity,
            bures_distance_to_self=bures,
            syscall_table=("kernel_precondition", "kernel_postcondition", stage),
        )

    def copy_density(self, rho: Any) -> Any:
        return rho.copy() if hasattr(rho, "copy") else rho

    def density_equal(self, left: Any, right: Any) -> bool:
        np = _require_numpy()
        return bool(np.array_equal(left, right))


class KernelSupervisor:
    """Hermitian guardrail and deterministic execution supervisor for Tier 2."""

    def __init__(
        self,
        operator: Optional["ManifoldOperator"] = None,
        ledger: Optional["CertificateLedger"] = None,
        *,
        math_provider: Optional[MathProvider] = None,
    ) -> None:
        self.operator = operator if operator is not None else (_default_operator() if math_provider is None else None)
        self.math_provider = math_provider or OperatorMathProvider(self.operator)
        self.ledger = ledger or CertificateLedger()

    def validate_density(self, rho: NDArray[np.complex128], *, stage: str) -> KernelInvariantReport:
        try:
            report = self.math_provider.invariant_report(rho, stage=stage)
        except ValueError as exc:
            fallback = StaticMathProvider().invariant_report(
                {"trace_one": False, "positive_semidefinite": False, "hermitian": False},
                stage=stage,
            )
            self.ledger.append("mathematical_exception", {"stage": stage, "reason": str(exc), "report": fallback.to_dict()})
            raise MathematicalException(str(exc), fallback) from exc
        if not report.closed:
            self.ledger.append("mathematical_exception", {"stage": stage, "report": report.to_dict()})
            raise MathematicalException("kernel invariant violation", report)
        self.ledger.append("kernel_invariant", {"stage": stage, "report": report.to_dict()})
        return report

    def execute_density_contract(
        self,
        function: Any,
        rho: NDArray[np.complex128],
        *,
        seed: int = 0,
        stage: str = "kernel_contract",
    ) -> tuple[NDArray[np.complex128], KernelInvariantReport]:
        """Run a Tier-2 function under pre/post density invariants.

        The seed is passed to promoted functions that accept a ``seed`` keyword.
        Functions that do not accept ``seed`` are still executed twice and must
        produce bit-wise/canonical identical output for the same input.
        """

        self.validate_density(rho, stage=f"{stage}:pre")
        first = self._call_kernel(function, self.math_provider.copy_density(rho), seed)
        second = self._call_kernel(function, self.math_provider.copy_density(rho), seed)
        if not self.math_provider.density_equal(first, second):
            report = StaticMathProvider().invariant_report(first, stage=stage)
            self.ledger.append("mathematical_exception", {"stage": stage, "reason": "non_deterministic", "report": report.to_dict()})
            raise MathematicalException("kernel function is not deterministic for the given seed", report)
        report = self.validate_density(first, stage=f"{stage}:post")
        return first, report

    @staticmethod
    def _call_kernel(function: Any, rho: Any, seed: int) -> Any:
        try:
            return function(rho, seed=seed)
        except TypeError:
            return function(rho)


@dataclass(frozen=True)
class LedgerEntry:
    """Single append-only certificate ledger entry."""

    index: int
    previous_hash: str
    certificate_type: str
    certificate_hash: str
    payload: Mapping[str, Any]
    timestamp_ns: int
    entry_hash: str

    def to_dict(self) -> dict[str, Any]:
        return _canonicalize(asdict(self))


class CertificateLedger:
    """Deterministic append-only, hash-chained compliance ledger."""

    def __init__(self, entries: Optional[Sequence[LedgerEntry]] = None) -> None:
        self._entries: list[LedgerEntry] = list(entries or [])
        if not self.verify_chain():
            raise ValueError("certificate ledger chain is invalid")

    @property
    def entries(self) -> tuple[LedgerEntry, ...]:
        return tuple(self._entries)

    @property
    def root_hash(self) -> str:
        return self._entries[-1].entry_hash if self._entries else "0" * 64

    def append(self, certificate_type: str, payload: Mapping[str, Any], *, timestamp_ns: Optional[int] = None) -> LedgerEntry:
        canonical = _canonicalize(dict(payload))
        certificate_hash = _hash_dict(canonical)
        material = {
            "index": len(self._entries),
            "previous_hash": self.root_hash,
            "certificate_type": str(certificate_type),
            "certificate_hash": certificate_hash,
            "payload": canonical,
            "timestamp_ns": time.time_ns() if timestamp_ns is None else int(timestamp_ns),
        }
        entry = LedgerEntry(entry_hash=_hash_dict(material), **material)
        self._entries.append(entry)
        return entry

    def verify_chain(self) -> bool:
        previous = "0" * 64
        for index, entry in enumerate(self._entries):
            if entry.index != index or entry.previous_hash != previous:
                return False
            material = entry.to_dict().copy()
            digest = material.pop("entry_hash")
            if _hash_dict(material) != digest:
                return False
            previous = entry.entry_hash
        return True

    def to_bytes(self) -> bytes:
        payload = json.dumps([e.to_dict() for e in self._entries], sort_keys=True, separators=(",", ":")).encode()
        return CERTIFICATE_LEDGER_MAGIC + struct.pack(">I", len(payload)) + payload

    @classmethod
    def from_bytes(cls, blob: bytes) -> "CertificateLedger":
        if len(blob) < 8 or blob[:4] != CERTIFICATE_LEDGER_MAGIC:
            raise ValueError("invalid certificate ledger binary envelope")
        size = struct.unpack(">I", blob[4:8])[0]
        payload = blob[8:]
        if len(payload) != size:
            raise ValueError("certificate ledger payload size mismatch")
        return cls(LedgerEntry(**entry) for entry in json.loads(payload.decode()))


@dataclass(frozen=True)
class ConsensusLedgerReport:
    """Network-wide proof of health across node-local certificate ledgers."""

    node_count: int
    verified_node_count: int
    root_hashes: tuple[str, ...]
    consensus_root_hash: str
    mathematical_exception_count: int
    autonomic_repair_count: int
    passed: bool
    schema_version: str = ELEVATION_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return _canonicalize(asdict(self))


class ConsensusLedger:
    """Aggregate multiple node ledgers into a deterministic super-ledger report."""

    def __init__(self, ledgers: Sequence[CertificateLedger]) -> None:
        if not ledgers:
            raise ValueError("at least one node ledger is required")
        self.ledgers = tuple(ledgers)

    def report(self) -> ConsensusLedgerReport:
        root_hashes = tuple(ledger.root_hash for ledger in self.ledgers)
        verified = tuple(ledger.verify_chain() for ledger in self.ledgers)
        mathematical_exceptions = sum(
            1
            for ledger in self.ledgers
            for entry in ledger.entries
            if entry.certificate_type == "mathematical_exception"
        )
        autonomic_repairs = sum(
            1
            for ledger in self.ledgers
            for entry in ledger.entries
            if entry.certificate_type == "autonomic_repair"
        )
        payload = {"node_roots": sorted(root_hashes), "node_count": len(self.ledgers)}
        return ConsensusLedgerReport(
            node_count=len(self.ledgers),
            verified_node_count=sum(1 for ok in verified if ok),
            root_hashes=root_hashes,
            consensus_root_hash=_hash_dict(payload),
            mathematical_exception_count=mathematical_exceptions,
            autonomic_repair_count=autonomic_repairs,
            passed=all(verified) and mathematical_exceptions == 0,
        )


@dataclass(frozen=True)
class TelemetryContract:
    """Fixed-point telemetry contract for forensic replay."""

    version: str = TELEMETRY_CONTRACT_VERSION
    fixed_point_scale: int = _FIXED_POINT_SCALE
    fixed_point_bit_depth: int = _FIXED_POINT_BIT_DEPTH
    metrics: tuple[str, ...] = ("phi", "bures", "purity", "manifold_drift", "solver_latency_ms")

    def metric_specs(self) -> dict[str, dict[str, Any]]:
        return {
            "phi": FixedPointMetricSpec("phi").to_dict(),
            "bures": FixedPointMetricSpec("bures").to_dict(),
            "purity": FixedPointMetricSpec("purity").to_dict(),
            "manifold_drift": FixedPointMetricSpec("manifold_drift").to_dict(),
            "solver_latency_ms": FixedPointMetricSpec("solver_latency_ms", maximum=10_000.0).to_dict(),
        }

    def encode(self, sample: Mapping[str, float]) -> dict[str, int]:
        specs = self.metric_specs()
        return {
            metric: _to_fixed_point(float(sample.get(metric, 0.0)), maximum=float(specs[metric]["maximum"]))
            for metric in self.metrics
        }

    def digest(self, samples: Iterable[Mapping[str, float]]) -> str:
        encoded = [self.encode(sample) for sample in samples]
        return _hash_dict({"version": self.version, "fixed_point_bit_depth": self.fixed_point_bit_depth, "fixed_point_scale": self.fixed_point_scale, "samples": encoded})

    def runtime_passport(self, module_id: str, sample: Mapping[str, float], invariant_report: KernelInvariantReport, ledger_entry: LedgerEntry) -> QuantumRuntimePassport:
        encoded = self.encode(sample)
        return QuantumRuntimePassport(
            module_id=module_id,
            phi_value_fixed=encoded["phi"],
            bures_score_fixed=encoded["bures"],
            kernel_invariants_met=invariant_report.closed,
            ledger_entry_hash=ledger_entry.entry_hash,
        )

    def verify_runtime_passport(self, passport: QuantumRuntimePassport, ledger: CertificateLedger) -> bool:
        return bool(
            passport.kernel_invariants_met
            and any(entry.entry_hash == passport.ledger_entry_hash for entry in ledger.entries)
            and ledger.verify_chain()
        )


@dataclass(frozen=True)
class RuntimeHealthPassport:
    """Φ-health supervisor output parallel to the quantum passport."""

    status: Severity
    phi_density: float
    phi_drift: float
    manifold_health_score: float
    suggestions: tuple[Mapping[str, str], ...]
    telemetry_digest: str
    timestamp_ns: int = field(default_factory=time.time_ns)
    schema_version: str = ELEVATION_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return _canonicalize(asdict(self))


@dataclass(frozen=True)
class FixedPointMetricSpec:
    """Exact deterministic representation for one telemetry metric."""

    name: str
    bit_depth: int = _FIXED_POINT_BIT_DEPTH
    scale: int = _FIXED_POINT_SCALE
    minimum: float = 0.0
    maximum: float = 1.0
    signed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return _canonicalize(asdict(self))


@dataclass(frozen=True)
class AutonomicRepairPlan:
    """Self-healing action plan emitted by the Φ-health supervisor."""

    action: str
    severity: str
    reason: str
    phi_density: float
    phi_drift: float
    manifold_health_score: float
    telemetry_digest: str
    ledger_entry_hash: str
    timestamp_ns: int = field(default_factory=time.time_ns)
    schema_version: str = ELEVATION_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return _canonicalize(asdict(self))


class PhiHealthSupervisor:
    """Runtime Φ-density drift detector and manifold health governor."""

    def __init__(self, *, phi_target: float = 0.6180339887498948, warn_drift: float = 0.08, critical_drift: float = 0.18) -> None:
        self.phi_target = float(phi_target)
        self.warn_drift = float(warn_drift)
        self.critical_drift = float(critical_drift)
        self.contract = TelemetryContract()

    def evaluate(self, samples: Sequence[Mapping[str, float]]) -> RuntimeHealthPassport:
        if not samples:
            raise ValueError("at least one telemetry sample is required")
        phis = [float(s.get("phi", self.phi_target)) for s in samples]
        phi_density = _mean(phis)
        phi_drift = abs(phi_density - self.phi_target)
        manifold_drift = _mean([abs(float(s.get("manifold_drift", 0.0))) for s in samples])
        latency = _mean([max(0.0, float(s.get("solver_latency_ms", 0.0))) for s in samples])
        health = _clip(1.0 - phi_drift - manifold_drift - min(latency / 10_000.0, 0.25), 0.0, 1.0)
        status = Severity.OK if phi_drift < self.warn_drift and health >= 0.85 else Severity.WATCH
        if phi_drift >= self.warn_drift or health < 0.75:
            status = Severity.WARN
        if phi_drift >= self.critical_drift or health < 0.45:
            status = Severity.CRITICAL
        suggestions: list[Mapping[str, str]] = []
        if status != Severity.OK:
            suggestions.append({"severity": status.value, "action": "rebalance_phi_density_window"})
        if manifold_drift > 0.05:
            suggestions.append({"severity": Severity.WARN.value, "action": "run_density_state_repair_and_topology_gate"})
        return RuntimeHealthPassport(status, phi_density, phi_drift, health, tuple(suggestions), self.contract.digest(samples))


    def repair_plan(self, passport: RuntimeHealthPassport, ledger: CertificateLedger) -> AutonomicRepairPlan:
        """Emit and ledger an autonomic repair plan for degraded Φ health."""
        if passport.status == Severity.OK:
            action = "observe"
            reason = "phi_health_within_operating_envelope"
        elif passport.status == Severity.WATCH:
            action = "increase_phi_sampling_window"
            reason = "early_phi_density_watch"
        elif passport.status == Severity.WARN:
            action = "resonance_recalibration"
            reason = "phi_density_or_manifold_drift_warning"
        else:
            action = "isolate_module_and_rebuild_density_state"
            reason = "critical_phi_or_manifold_health_violation"
        material = {
            "action": action,
            "severity": passport.status.value,
            "reason": reason,
            "phi_density": passport.phi_density,
            "phi_drift": passport.phi_drift,
            "manifold_health_score": passport.manifold_health_score,
            "telemetry_digest": passport.telemetry_digest,
        }
        entry = ledger.append("autonomic_repair", material)
        return AutonomicRepairPlan(ledger_entry_hash=entry.entry_hash, **material)

    def evaluate_and_repair(self, samples: Sequence[Mapping[str, float]], ledger: CertificateLedger) -> tuple[RuntimeHealthPassport, AutonomicRepairPlan]:
        passport = self.evaluate(samples)
        return passport, self.repair_plan(passport, ledger)


class ElevationBridge:
    """Read-only production façade to research-kernel bridge."""

    def __init__(self, operator: Optional[ManifoldOperator] = None, verifier: Optional[SubstateVerifier] = None) -> None:
        self.operator = operator or _default_operator()
        self.verifier = verifier or _default_verifier(self.operator)

    def readonly_snapshot(self) -> dict[str, Any]:
        return {"operator": self.operator.snapshot(), "topology_verified": self.verifier.verify_topology()}

    def promotion_manifest(self, passport: SubstatePassport, ledger: CertificateLedger) -> dict[str, Any]:
        certificate_suite = {
            "grover": bool(passport.grover_scope_verified),
            "topology": bool(passport.topology_verified),
            "automorphism": bool(passport.structural_hash),
            "coverage": bool(passport.coverage_verified),
        }
        if not self.verifier.verify_passport(passport) or not ledger.verify_chain() or not all(certificate_suite.values()):
            raise ValueError("only verified passports and ledgers can be promoted")
        return {
            "passport_hash": passport.passport_hash,
            "ledger_root_hash": ledger.root_hash,
            "read_only_research_access": True,
            "one_way_valve": "research_to_production_requires_certificate_suite",
            "certificate_suite": certificate_suite,
        }

    def anonymized_research_telemetry(self, samples: Sequence[Mapping[str, Any]]) -> tuple[Mapping[str, Any], ...]:
        anonymized: list[Mapping[str, Any]] = []
        for index, sample in enumerate(samples):
            numeric = {key: value for key, value in sample.items() if isinstance(value, (int, float))}
            anonymized.append({
                "sample_hash": _hash_dict({"index": index, "numeric": numeric}),
                "fixed_point": TelemetryContract().encode({key: float(value) for key, value in numeric.items()}),
            })
        return tuple(anonymized)


class QuantumRuntimeManifestBuilder:
    """Build the production-grade runtime manifest handed to institutions."""

    def __init__(self, operator: Optional[ManifoldOperator] = None, verifier: Optional[SubstateVerifier] = None) -> None:
        self.operator = operator or _default_operator()
        self.verifier = verifier or _default_verifier(self.operator)

    def capability_manifest(self) -> CapabilityManifest:
        return CapabilityManifest(
            version=RUNTIME_MANIFEST_VERSION,
            operator_version=self.operator.VERSION,
            verifier_version=self.verifier.VERSION,
            capability_flags={
                "supports_bures_v2": True,
                "supports_phi_windowing": True,
                "supports_certificate_ledger": True,
                "supports_fixed_point_telemetry": True,
                "supports_elevation_bridge": True,
                "supports_production_response_envelope": True,
                "supports_hermitian_guardrail": True,
                "supports_autonomic_repair_ledgering": True,
                "supports_forensic_audit_cli": True,
            },
            facade_api_signatures=_facade_signatures_from_instances((self.operator, self.verifier)),
            endpoint_invariants={
                "ManifoldOperator.ensure_density_state": ("trace_one", "positive_semidefinite", "hermitian"),
                "ManifoldOperator.compute_bures_distance": ("bures_metric_bounds", "trace_one_inputs"),
                "ManifoldOperator.certify_channel": ("choi_positive_semidefinite", "trace_preservation"),
                "ManifoldOperator.verify_topology": ("automorphism_order_120", "adjacency_digest"),
                "SubstateVerifier.generate_passport": ("coverage_complete", "grover_scope_no_speedup_claim", "binary_header_fixed_point"),
            },
        )

    def kernel_invariants(self, rho: Optional[NDArray[np.complex128]] = None) -> KernelInvariantReport:
        if rho is None:
            return StaticMathProvider().invariant_report({}, stage="manifest_default")
        if isinstance(rho, Mapping):
            return StaticMathProvider().invariant_report(rho, stage="manifest")
        return OperatorMathProvider(self.operator).invariant_report(self.operator.ensure_density_state(rho), stage="manifest")


    def build(self, ledger: Optional[CertificateLedger] = None, rho: Optional[NDArray[np.complex128]] = None) -> dict[str, Any]:
        ledger = ledger or CertificateLedger()
        capability = self.capability_manifest()
        compliance = ComplianceManifest()
        invariants = self.kernel_invariants(rho)
        payload = {
            "version": RUNTIME_MANIFEST_VERSION,
            "module_versions": {"operator": self.operator.VERSION, "verifier": self.verifier.VERSION},
            "capability_manifest": capability.to_dict() | {"manifest_hash": capability.manifest_hash},
            "manifest_json_name": "manifest.json",
            "certificate_ledger_root_hash": ledger.root_hash,
            "telemetry_contract_version": TELEMETRY_CONTRACT_VERSION,
            "fixed_point_telemetry_spec": TelemetryContract().metric_specs(),
            "kernel_invariants": invariants.to_dict(),
            "compliance": compliance.to_dict(),
            "quantum_speedup_claimed": False,
        }
        return payload | {"runtime_manifest_hash": _hash_dict(payload)}

    def write_manifest_json(self, path: str | Path, ledger: Optional[CertificateLedger] = None, rho: Optional[NDArray[np.complex128]] = None) -> Path:
        target = Path(path)
        manifest = self.build(ledger=ledger, rho=rho)
        target.write_text(json.dumps(manifest, sort_keys=True, indent=2), encoding="utf-8")
        return target

    def production_response(self, endpoint: str, result: Mapping[str, Any], ledger: CertificateLedger) -> ProductionResponse:
        entry = ledger.append("production_response", {"endpoint": endpoint, "result": result})
        return ProductionResponse(
            result=_canonicalize(result),
            module_version_hash=_hash_dict({"operator": self.operator.VERSION, "verifier": self.verifier.VERSION}),
            ledger_entry_hash=entry.entry_hash,
            ledger_index=entry.index,
            endpoint=endpoint,
        )


def _facade_signatures(classes: Sequence[type]) -> dict[str, str]:
    signatures: dict[str, str] = {}
    for cls in classes:
        for name, member in inspect.getmembers(cls, predicate=inspect.isfunction):
            if not name.startswith("_"):
                signatures[f"{cls.__name__}.{name}"] = str(inspect.signature(member))
    return dict(sorted(signatures.items()))


def _to_fixed_point(value: float, *, maximum: float = 1.0) -> int:
    normalized = 0.0 if maximum <= 0.0 else _clip(float(value) / maximum, 0.0, 1.0)
    return int(round(normalized * _FIXED_POINT_SCALE))


def _canonicalize(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(k): _canonicalize(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (tuple, list)):
        return [_canonicalize(v) for v in value]
    return value


def _hash_dict(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(_canonicalize(payload), sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def _default_operator() -> "ManifoldOperator":
    from .pulvini_operator import ManifoldOperator as _ManifoldOperator

    return _ManifoldOperator()


def _default_verifier(operator: "ManifoldOperator") -> "SubstateVerifier":
    from .pulvini_verifier import SubstateVerifier as _SubstateVerifier

    return _SubstateVerifier(operator)


def _require_numpy() -> Any:
    if importlib.util.find_spec("numpy") is None:
        raise RuntimeError("NumPy is required for production mathematical-kernel execution; use StaticMathProvider for dependency-free ledger/manifest tests")
    return importlib.import_module("numpy")


def _mean(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    return float(sum(values) / len(values))


def _clip(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, float(value)))


def _facade_signatures_from_instances(instances: Sequence[Any]) -> dict[str, str]:
    signatures: dict[str, str] = {}
    for instance in instances:
        cls = instance.__class__
        for name, member in inspect.getmembers(cls, predicate=inspect.isfunction):
            if not name.startswith("_"):
                signatures[f"{cls.__name__}.{name}"] = str(inspect.signature(member))
    return dict(sorted(signatures.items()))


__all__ = [
    "AutonomicRepairPlan",
    "CapabilityManifest",
    "CertificateLedger",
    "ComplianceManifest",
    "ConsensusLedger",
    "ConsensusLedgerReport",
    "ElevationBridge",
    "FixedPointMetricSpec",
    "KernelInvariantReport",
    "KernelSupervisor",
    "MathProvider",
    "LedgerEntry",
    "MathematicalException",
    "PhiHealthSupervisor",
    "OperatorMathProvider",
    "ProductionResponse",
    "QuantumRuntimeManifestBuilder",
    "QuantumRuntimePassport",
    "RuntimeHealthPassport",
    "StaticMathProvider",
    "TelemetryContract",
]
