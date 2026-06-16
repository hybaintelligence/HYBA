"""
PYTHIA matched mining benchmark harness.

This module elevates the mining code toward the documented HYBA claim: PYTHIA is
not a blind brute-force loop. It is deterministic structured traversal over the
same exact cryptographic oracle as the baseline.

The benchmark is intentionally offline and replay-safe:
    - no pool connection;
    - no share submission;
    - no live wallet or payout logic;
    - same 80-byte header prefix, same target, same nonce budget;
    - baseline and PYTHIA both use exact Bitcoin-style double SHA-256.

What it measures:
    - candidate budget to first target hit, if a target hit exists;
    - best hash reached under the same budget;
    - rank advantage of PYTHIA's dodecahedral/icosahedral/PULVINI ordering;
    - deterministic report hash for board/auditor replay.

This is not a throttling layer. It is the evidence bridge between the HYBA
technical doctrine and a measurable claim.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from pythia_mining.nonce_resonance_guidance import (
    BlockContext,
    EmpiricalStructureEvidence,
    PythiaNonceResonanceGuidance,
    ResonanceSignal,
    build_nonce_resonance_guidance,
)

UINT32_MAX = 2**32 - 1
MAX_HASH = 2**256 - 1
DEFAULT_HEADER_PREFIX_BYTES = 76


class TraversalStrategy(str, Enum):
    """Matched candidate ordering strategies."""

    BASELINE_SEQUENTIAL = "baseline_sequential"
    PYTHIA_STRUCTURED = "pythia_structured"


@dataclass(frozen=True)
class ReplayBlockTemplate:
    """Offline replay template for exact SHA-256d nonce verification.

    ``header_prefix_hex`` must represent the first 76 bytes of an 80-byte block
    header. The benchmark appends the nonce as little-endian uint32 and performs
    exact double SHA-256 on the resulting 80-byte header.
    """

    header_prefix_hex: str
    target: int
    block_height: int
    difficulty: float
    template_id: str = "offline_replay_template"

    def header_prefix(self) -> bytes:
        prefix = bytes.fromhex(self.header_prefix_hex)
        if len(prefix) != DEFAULT_HEADER_PREFIX_BYTES:
            raise ValueError("header_prefix_hex must encode exactly 76 bytes")
        if self.target < 1 or self.target > MAX_HASH:
            raise ValueError("target must be in 1..2**256-1")
        return prefix

    def header_for_nonce(self, nonce: int) -> bytes:
        if not isinstance(nonce, int) or nonce < 0 or nonce > UINT32_MAX:
            raise ValueError("nonce must be an unsigned 32-bit integer")
        return self.header_prefix() + int(nonce).to_bytes(4, byteorder="little", signed=False)


@dataclass(frozen=True)
class CandidateHash:
    """Exact SHA-256d verification result for one nonce."""

    nonce: int
    hash_hex: str
    hash_int: int
    accepted: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TraversalResult:
    """Result for one strategy under the same replay template and budget."""

    strategy: TraversalStrategy
    candidate_budget: int
    tested_nonces: List[int]
    accepted_count: int
    first_accepted_nonce: Optional[int]
    first_accepted_index: Optional[int]
    best_nonce: int
    best_hash_hex: str
    best_hash_int: int

    @property
    def first_hit_budget(self) -> Optional[int]:
        if self.first_accepted_index is None:
            return None
        return int(self.first_accepted_index) + 1

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["strategy"] = self.strategy.value
        payload["first_hit_budget"] = self.first_hit_budget
        return payload


@dataclass(frozen=True)
class MatchedMiningBenchmarkReport:
    """Sealed matched benchmark comparing baseline and PYTHIA traversal."""

    protocol: str
    template_id: str
    target_hex: str
    block_height: int
    difficulty: float
    candidate_budget: int
    guidance_protocol: str
    top_structure_signals: List[str]
    baseline: TraversalResult
    pythia: TraversalResult
    candidate_budget_advantage: Optional[float]
    best_hash_improvement_ratio: float
    interpretation: str
    claim_boundary: List[str]
    report_hash: str = ""

    def to_payload(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["baseline"] = self.baseline.to_dict()
        payload["pythia"] = self.pythia.to_dict()
        return payload

    def with_hash(self) -> "MatchedMiningBenchmarkReport":
        payload = self.to_payload()
        payload.pop("report_hash", None)
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return MatchedMiningBenchmarkReport(
            protocol=self.protocol,
            template_id=self.template_id,
            target_hex=self.target_hex,
            block_height=self.block_height,
            difficulty=self.difficulty,
            candidate_budget=self.candidate_budget,
            guidance_protocol=self.guidance_protocol,
            top_structure_signals=self.top_structure_signals,
            baseline=self.baseline,
            pythia=self.pythia,
            candidate_budget_advantage=self.candidate_budget_advantage,
            best_hash_improvement_ratio=self.best_hash_improvement_ratio,
            interpretation=self.interpretation,
            claim_boundary=self.claim_boundary,
            report_hash=hashlib.sha256(encoded).hexdigest(),
        )


def exact_sha256d_header(header: bytes) -> Tuple[str, int]:
    """Return Bitcoin display hash hex and little-endian integer for a header."""

    if len(header) != 80:
        raise ValueError("header must be exactly 80 bytes")
    digest = hashlib.sha256(hashlib.sha256(header).digest()).digest()
    return digest[::-1].hex(), int.from_bytes(digest, byteorder="little", signed=False)


def verify_candidate(template: ReplayBlockTemplate, nonce: int) -> CandidateHash:
    """Verify one nonce with exact double SHA-256 under the replay target."""

    hash_hex, hash_int = exact_sha256d_header(template.header_for_nonce(nonce))
    return CandidateHash(
        nonce=int(nonce),
        hash_hex=hash_hex,
        hash_int=int(hash_int),
        accepted=hash_int <= int(template.target),
    )


def baseline_nonce_order(candidate_budget: int, start_nonce: int = 0) -> List[int]:
    """Baseline candidate order: deterministic sequential traversal."""

    _validate_budget(candidate_budget)
    return [int((start_nonce + offset) & UINT32_MAX) for offset in range(candidate_budget)]


def pythia_structured_nonce_order(
    guidance: PythiaNonceResonanceGuidance,
    candidate_budget: int,
    *,
    start_nonce: int = 0,
) -> List[int]:
    """PYTHIA ordering from dodecahedral/icosahedral resonance priorities.

    The order is deterministic, duplicate-free inside the budget, and eventually
    filled by the same sequential coverage fallback as the baseline. That means a
    matched replay measures ordering advantage without losing coverage.
    """

    _validate_budget(candidate_budget)
    seen: set[int] = set()
    ordered: List[int] = []
    seed = f"{guidance.seal}:{guidance.block_context.block_height}:{guidance.block_context.target_hex}"

    for rank, priority in enumerate(guidance.priorities):
        center = _anchor_nonce(seed, priority.signal.value, rank, start_nonce)
        radius = max(3, int(1 + priority.weight * 31))
        stride = _phi_stride(rank)
        for offset in _symmetric_offsets(radius):
            nonce = int((center + offset * stride) & UINT32_MAX)
            if nonce not in seen:
                seen.add(nonce)
                ordered.append(nonce)
                if len(ordered) >= candidate_budget:
                    return ordered

    for nonce in baseline_nonce_order(candidate_budget * 2, start_nonce=start_nonce):
        if nonce not in seen:
            seen.add(nonce)
            ordered.append(nonce)
            if len(ordered) >= candidate_budget:
                return ordered

    return ordered[:candidate_budget]


def run_traversal(
    *,
    template: ReplayBlockTemplate,
    nonces: Sequence[int],
    strategy: TraversalStrategy,
) -> TraversalResult:
    """Run one traversal strategy under exact SHA-256d verification."""

    if not nonces:
        raise ValueError("nonces must not be empty")

    accepted: List[Tuple[int, CandidateHash]] = []
    best: Optional[CandidateHash] = None
    for index, nonce in enumerate(nonces):
        candidate = verify_candidate(template, int(nonce))
        if best is None or candidate.hash_int < best.hash_int:
            best = candidate
        if candidate.accepted:
            accepted.append((index, candidate))

    assert best is not None
    first_index, first = accepted[0] if accepted else (None, None)
    return TraversalResult(
        strategy=strategy,
        candidate_budget=len(nonces),
        tested_nonces=[int(n) for n in nonces],
        accepted_count=len(accepted),
        first_accepted_nonce=first.nonce if first else None,
        first_accepted_index=int(first_index) if first_index is not None else None,
        best_nonce=best.nonce,
        best_hash_hex=best.hash_hex,
        best_hash_int=best.hash_int,
    )


def run_matched_mining_benchmark(
    *,
    template: ReplayBlockTemplate,
    guidance: PythiaNonceResonanceGuidance,
    candidate_budget: int,
    start_nonce: int = 0,
) -> MatchedMiningBenchmarkReport:
    """Compare baseline and PYTHIA under the same template, target and budget."""

    _validate_budget(candidate_budget)
    baseline_order = baseline_nonce_order(candidate_budget, start_nonce=start_nonce)
    pythia_order = pythia_structured_nonce_order(
        guidance,
        candidate_budget,
        start_nonce=start_nonce,
    )
    baseline = run_traversal(
        template=template,
        nonces=baseline_order,
        strategy=TraversalStrategy.BASELINE_SEQUENTIAL,
    )
    pythia = run_traversal(
        template=template,
        nonces=pythia_order,
        strategy=TraversalStrategy.PYTHIA_STRUCTURED,
    )

    candidate_advantage = _candidate_budget_advantage(baseline, pythia)
    best_hash_ratio = baseline.best_hash_int / max(pythia.best_hash_int, 1)
    interpretation = _interpret_report(candidate_advantage, best_hash_ratio, baseline, pythia)

    report = MatchedMiningBenchmarkReport(
        protocol="PYTHIA_MATCHED_MINING_BENCHMARK_V1",
        template_id=template.template_id,
        target_hex=f"{int(template.target):064x}",
        block_height=int(template.block_height),
        difficulty=float(template.difficulty),
        candidate_budget=int(candidate_budget),
        guidance_protocol=guidance.protocol,
        top_structure_signals=[priority.signal.value for priority in guidance.priorities[:5]],
        baseline=baseline,
        pythia=pythia,
        candidate_budget_advantage=candidate_advantage,
        best_hash_improvement_ratio=round(float(best_hash_ratio), 12),
        interpretation=interpretation,
        claim_boundary=[
            "Matched replay only: no live pool connection or share submission.",
            "Baseline and PYTHIA use the same header prefix, target and nonce budget.",
            "Every candidate is verified with exact double SHA-256.",
            "PYTHIA advantage is measured as ordering/budget advantage, not asserted by doctrine.",
            "A pool-side accepted share or block remains a separate production evidence gate.",
        ],
    )
    return report.with_hash()


def build_guidance_from_structure(
    *,
    block_height: int,
    difficulty: float,
    target_hex: str,
    sample_size: int = 4096,
    phi15_rate: float = 0.18,
    golden_angle_alignment: float = 0.52,
    birthday_echo_rate: float = 0.27,
    sector_coverage: float = 0.86,
    large_gap_score: float = 0.42,
    dodecahedral_domain_score: float = 0.91,
    icosahedral_face_score: float = 0.88,
    mass_gap_valley_score: float = 0.76,
    entanglement_spectrum_score: float = 0.81,
    uniformity_score: float = 0.64,
) -> PythiaNonceResonanceGuidance:
    """Convenience builder for an empirical structure packet used in replay."""

    return build_nonce_resonance_guidance(
        EmpiricalStructureEvidence(
            sample_size=sample_size,
            phi15_rate=phi15_rate,
            golden_angle_alignment=golden_angle_alignment,
            birthday_echo_rate=birthday_echo_rate,
            sector_coverage=sector_coverage,
            large_gap_score=large_gap_score,
            dodecahedral_domain_score=dodecahedral_domain_score,
            icosahedral_face_score=icosahedral_face_score,
            mass_gap_valley_score=mass_gap_valley_score,
            entanglement_spectrum_score=entanglement_spectrum_score,
            uniformity_score=uniformity_score,
        ),
        BlockContext(
            block_height=block_height,
            difficulty=difficulty,
            target_hex=target_hex,
        ),
    )


def synthetic_header_prefix(seed: str) -> str:
    """Create a deterministic 76-byte replay header prefix from a seed string."""

    material = b""
    counter = 0
    while len(material) < DEFAULT_HEADER_PREFIX_BYTES:
        material += hashlib.sha256(f"{seed}:{counter}".encode("utf-8")).digest()
        counter += 1
    return material[:DEFAULT_HEADER_PREFIX_BYTES].hex()


def target_from_best_nonce(
    *,
    template_prefix_hex: str,
    nonces: Iterable[int],
    block_height: int = 0,
    difficulty: float = 1.0,
    template_id: str = "target_from_best_nonce",
) -> Tuple[int, int, str]:
    """Return target equal to the best hash among the supplied nonces.

    This is useful for controlled replay: exactly the best candidate in the
    supplied set is guaranteed to satisfy the target unless there are ties.
    """

    probe = ReplayBlockTemplate(
        header_prefix_hex=template_prefix_hex,
        target=MAX_HASH,
        block_height=block_height,
        difficulty=difficulty,
        template_id=template_id,
    )
    best: Optional[CandidateHash] = None
    for nonce in nonces:
        candidate = verify_candidate(probe, int(nonce))
        if best is None or candidate.hash_int < best.hash_int:
            best = candidate
    if best is None:
        raise ValueError("nonces must not be empty")
    return best.hash_int, best.nonce, best.hash_hex


def _candidate_budget_advantage(
    baseline: TraversalResult,
    pythia: TraversalResult,
) -> Optional[float]:
    if baseline.first_hit_budget is None or pythia.first_hit_budget is None:
        return None
    return round(float(baseline.first_hit_budget) / max(float(pythia.first_hit_budget), 1.0), 12)


def _interpret_report(
    candidate_advantage: Optional[float],
    best_hash_ratio: float,
    baseline: TraversalResult,
    pythia: TraversalResult,
) -> str:
    if candidate_advantage is not None and candidate_advantage > 1.0:
        return "PYTHIA reached the target in fewer candidates under matched replay."
    if pythia.best_hash_int < baseline.best_hash_int:
        return "PYTHIA produced a stronger best hash under matched replay; no target hit advantage was required."
    if pythia.best_hash_int == baseline.best_hash_int:
        return "PYTHIA and baseline reached the same best hash under matched replay."
    return "Baseline produced the stronger best hash under this replay; retain as criticism input."


def _anchor_nonce(seed: str, signal: str, rank: int, start_nonce: int) -> int:
    digest = hashlib.sha256(f"{seed}:{signal}:{rank}".encode("utf-8")).digest()
    return (start_nonce + int.from_bytes(digest[:4], byteorder="little", signed=False)) & UINT32_MAX


def _phi_stride(rank: int) -> int:
    # Odd strides avoid trivial even-only loops and keep ordering deterministic.
    stride = int((rank + 1) * 2654435761) & UINT32_MAX
    return stride | 1


def _symmetric_offsets(radius: int) -> List[int]:
    offsets = [0]
    for value in range(1, int(radius) + 1):
        offsets.extend([value, -value])
    return offsets


def _validate_budget(candidate_budget: int) -> None:
    if not isinstance(candidate_budget, int) or candidate_budget < 1:
        raise ValueError("candidate_budget must be a positive integer")


__all__ = [
    "CandidateHash",
    "MatchedMiningBenchmarkReport",
    "ReplayBlockTemplate",
    "TraversalResult",
    "TraversalStrategy",
    "baseline_nonce_order",
    "build_guidance_from_structure",
    "exact_sha256d_header",
    "pythia_structured_nonce_order",
    "run_matched_mining_benchmark",
    "run_traversal",
    "synthetic_header_prefix",
    "target_from_best_nonce",
    "verify_candidate",
]
