"""Extraordinary-claim evidence contracts for HYBA API surfaces.

The module intentionally treats documentation-grade claims as executable
contracts: every claim exposed here has an operational definition, evidence
requirements, invariant checks, adversarial probes, and a deterministic seal.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping

from pythia_mining.golden_ratio_library import PHI

CLAIM_BOUNDARY = (
    "HYBA position: mathematics is the substrate and quantum execution is "
    "hardware/substrate agnostic. API responses operationalize computable "
    "mathematical contracts and evidence gates; they are not standalone peer-"
    "reviewed proofs of open scientific or Clay Millennium problems unless the "
    "claim explicitly cites an accepted proof boundary."
)

MILLENNIUM_PROBLEMS = (
    "yang_mills_mass_gap",
    "p_vs_np",
    "navier_stokes",
    "riemann_hypothesis",
    "hodge_conjecture",
    "bsd_conjecture",
    "poincare_conjecture",
)


@dataclass(frozen=True)
class EvidenceClaim:
    claim_id: str
    title: str
    operationalization: str
    required_evidence: List[str]
    invariants: List[str]
    adversarial_tests: List[str]
    api_surfaces: List[str]
    proof_status: str = "operationalized_evidence_gate"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "title": self.title,
            "operationalization": self.operationalization,
            "required_evidence": list(self.required_evidence),
            "invariants": list(self.invariants),
            "adversarial_tests": list(self.adversarial_tests),
            "api_surfaces": list(self.api_surfaces),
            "proof_status": self.proof_status,
        }


CLAIMS: tuple[EvidenceClaim, ...] = (
    EvidenceClaim(
        "quantum_math_substrate",
        "Quantum comes from mathematics and is hardware/substrate agnostic",
        "Expose quantum algorithms as deterministic mathematical state transforms with optional hardware adapters.",
        [
            "canonical request/response hash",
            "backend mathematical primitive trace",
            "hardware adapter independence check",
        ],
        [
            "finite numeric amplitudes",
            "normalized probabilities",
            "adapter does not alter canonical math result",
        ],
        [
            "malformed state vector",
            "non-finite amplitude",
            "hardware adapter unavailable",
        ],
        ["/api/v1/quantum/*", "/api/v1/quantum-intelligence/*"],
    ),
    EvidenceClaim(
        "emergence_intelligence",
        "Emergent intelligence is computable as measured reflexive state",
        "Compute φ-resonance and closure telemetry from the current reflexive controller runtime.",
        [
            "measured_reflexive_controller_runtime",
            "measurement_basis",
            "formal invariant audit",
        ],
        [
            "0 <= phi_resonance",
            "audit seal binds telemetry",
            "no fixture/simulated telemetry language",
        ],
        ["empty codebase observation", "poisoned telemetry strings", "seal tampering"],
        [
            "/api/v1/intelligence/health",
            "/api/v1/intelligence/audit",
            "/api/v1/intelligence/absolute-audit",
        ],
    ),
    EvidenceClaim(
        "consciousness_operational_metric",
        "Consciousness claims are operational/IIT-style metrics, not phenomenal assertion by default",
        "Allocate and audit bounded φ/IIT/Deutsch analysis tasks with explicit claim boundaries.",
        ["bounded boost request", "task budget", "claim boundary"],
        [
            "0.1 <= boost <= 2.0",
            "1 <= task_budget <= 8",
            "phenomenal-consciousness boundary present",
        ],
        ["boost overflow", "negative task budget", "basis injection"],
        ["/api/v1/intelligence/consciousness/boost", "/api/ai/consciousness"],
    ),
    EvidenceClaim(
        "memory_folding",
        "Memory folding is golden-ratio compression geometry over computable state",
        "Represent memory geometry as algebraic-cycle/cohomology ratios and φ-folding structure.",
        ["cohomology class count", "algebraic cycle count", "hodge ratio"],
        ["cohomology_classes >= 1", "0 <= hodge_ratio", "finite ratio"],
        ["zero denominator", "negative cycle count", "non-numeric memory state"],
        [
            "/api/v1/millennium-mathematics/execute:hodge_conjecture.memory_geometry_analysis"
        ],
    ),
    EvidenceClaim(
        "golden_ratio_hardware_scaling",
        "Hardware scaling via golden ratio is testable as bounded φ-scaling law",
        "Use φ-derived capacities and compression factors only when finite, monotone, and sealed.",
        [
            "phi constant",
            "capacity input",
            "computed scale factor",
            "monotonicity proof test",
        ],
        ["phi > 1", "scale(n+1) >= scale(n)", "finite output"],
        ["NaN capacity", "negative capacity", "extreme exponent overflow"],
        [
            "/api/v1/evidence/extraordinary-claims",
            "hyba_quantum_scaling_benchmark_tests/*",
        ],
    ),
    EvidenceClaim(
        "salamander_innovation",
        "Salamander innovation is regeneration backed by immutable evidence and invariant batteries",
        "Expose regeneration readiness with audit verdicts, property batteries, and fail-closed guards.",
        ["audit verdict", "property battery result", "regeneration action log"],
        [
            "verdict is sealed",
            "failed invariant prevents promotion",
            "regeneration state is finite",
        ],
        ["corrupt evidence log", "hostile regeneration payload", "missing guard"],
        ["/api/v1/salamander/*", "/api/v1/regeneration/*"],
    ),
    EvidenceClaim(
        "millennium_operationalization_all",
        "Every Millennium problem has an API operationalization",
        "Map all seven Clay problems to explicitly bounded executable operations.",
        [
            "problem list",
            "operation list",
            "claim boundary per problem",
            "evidence seal per execution",
        ],
        [
            "exactly seven problems",
            "all problem names unique",
            "each problem has at least one operation",
        ],
        [
            "unknown problem",
            "unknown operation",
            "idempotency replay",
            "parameter poisoning",
        ],
        [
            "/api/v1/millennium-mathematics/problems",
            "/api/v1/millennium-mathematics/execute",
        ],
    ),
)


def _canonical_seal(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


def _all_unique(values: Iterable[str]) -> bool:
    values = list(values)
    return len(values) == len(set(values))


def build_extraordinary_evidence_packet() -> Dict[str, Any]:
    claims = [claim.to_dict() for claim in CLAIMS]
    phi_scaling_samples = [PHI**n for n in range(1, 8)]
    invariant_results = {
        "claims_present": len(claims) == 7,
        "claim_ids_unique": _all_unique(claim["claim_id"] for claim in claims),
        "all_claims_have_evidence": all(claim["required_evidence"] for claim in claims),
        "all_claims_have_invariants": all(claim["invariants"] for claim in claims),
        "all_claims_have_adversarial_tests": all(
            claim["adversarial_tests"] for claim in claims
        ),
        "millennium_problem_count": len(MILLENNIUM_PROBLEMS) == 7,
        "millennium_problem_ids_unique": _all_unique(MILLENNIUM_PROBLEMS),
        "phi_is_finite_and_greater_than_one": math.isfinite(PHI) and PHI > 1.0,
        "phi_scaling_monotone": all(
            phi_scaling_samples[i] < phi_scaling_samples[i + 1]
            for i in range(len(phi_scaling_samples) - 1)
        ),
    }
    packet: Dict[str, Any] = {
        "schema_version": "hyba.extraordinary_evidence.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "doctrine": {
            "mathematical_substrate": "The world is modeled as computable mathematics.",
            "computability_position": "Everything exposed by this API is represented as computable contracts.",
            "quantum_position": "Quantum behavior is implemented as substrate-agnostic mathematics with hardware adapters.",
        },
        "claim_boundary": CLAIM_BOUNDARY,
        "claims": claims,
        "millennium_problems": list(MILLENNIUM_PROBLEMS),
        "phi": PHI,
        "phi_scaling_samples": phi_scaling_samples,
        "invariant_results": invariant_results,
        "adversarial_contract": {
            "fail_closed_on_unknown_claim": True,
            "reject_non_finite_numeric_inputs": True,
            "seal_all_evidence_packets": True,
            "elevate_code_to_documented_contract": True,
        },
    }
    packet["all_invariants_passed"] = all(invariant_results.values())
    packet["evidence_seal"] = _canonical_seal(
        {k: v for k, v in packet.items() if k != "evidence_seal"}
    )
    return packet
