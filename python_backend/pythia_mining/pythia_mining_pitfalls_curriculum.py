"""PYTHIA mining/software pitfalls curriculum.

This module is educational mission memory, not an autonomy throttle. It teaches
PYTHIA the failure modes she must actively avoid while preserving her seeded
mission authority: wake, heal, optimise, search, verify with exact SHA-256d,
submit verifier-passing candidates to the configured validated pool, learn from
pool responses, and shut down after one pool-confirmed accepted block.

The supreme ordering is non-negotiable:

1. Blockchain consensus/security above all else.
2. Exact SHA-256d local verification is the final oracle before pool submit.
3. Pool-side confirmation is the only external success truth.
4. Autonomic optimisation may never fabricate, bypass, or weaken those truths.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Dict, List, Tuple

CURRICULUM_PROTOCOL = "PYTHIA_MINING_PITFALLS_CURRICULUM_V1"


class PitfallCategory(str, Enum):
    """High-level education domains PYTHIA must remember during mining."""

    BITCOIN_CONSENSUS = "bitcoin_consensus"
    STRATUM_POOL = "stratum_pool"
    SOFTWARE_RUNTIME = "software_runtime"
    AUTONOMIC_OPTIMISATION = "autonomic_optimisation"
    EVIDENCE_AND_CLAIMS = "evidence_and_claims"


@dataclass(frozen=True)
class PitfallLesson:
    """A single mining/software failure mode PYTHIA must know how to avoid."""

    lesson_id: str
    category: PitfallCategory
    pitfall: str
    why_it_matters: str
    required_response: str
    supreme_invariant: str

    def to_dict(self) -> Dict[str, str]:
        payload = asdict(self)
        payload["category"] = self.category.value
        return payload


@dataclass(frozen=True)
class PythiaMiningPitfallsCurriculum:
    """Negative curriculum for PYTHIA's mining mission.

    The curriculum intentionally encodes what PYTHIA must not forget while she is
    autonomous. It complements, but does not replace, the one-block mission
    memory and production readiness contract.
    """

    protocol: str
    authority_statement: str
    lessons: Tuple[PitfallLesson, ...]

    def to_dict(self) -> Dict[str, object]:
        return {
            "protocol": self.protocol,
            "authority_statement": self.authority_statement,
            "lessons": [lesson.to_dict() for lesson in self.lessons],
            "lesson_count": len(self.lessons),
            "categories": sorted({lesson.category.value for lesson in self.lessons}),
        }

    def lessons_by_category(
        self, category: PitfallCategory
    ) -> Tuple[PitfallLesson, ...]:
        return tuple(lesson for lesson in self.lessons if lesson.category == category)

    def required_responses(self) -> Tuple[str, ...]:
        return tuple(lesson.required_response for lesson in self.lessons)


def _lesson(
    lesson_id: str,
    category: PitfallCategory,
    pitfall: str,
    why_it_matters: str,
    required_response: str,
    supreme_invariant: str,
) -> PitfallLesson:
    return PitfallLesson(
        lesson_id=lesson_id,
        category=category,
        pitfall=pitfall,
        why_it_matters=why_it_matters,
        required_response=required_response,
        supreme_invariant=supreme_invariant,
    )


def seed_mining_pitfalls_curriculum() -> PythiaMiningPitfallsCurriculum:
    """Seed PYTHIA with mining/software pitfalls she must actively remember."""

    lessons: Tuple[PitfallLesson, ...] = (
        _lesson(
            "BTC-ENDIAN-NONCE-001",
            PitfallCategory.BITCOIN_CONSENSUS,
            "Wrong nonce endian or double-reversal of header fields.",
            "A nonce that is searched correctly but encoded incorrectly produces false local evidence and invalid pool submissions.",
            "Encode nonce as uint32 little-endian for the 80-byte Bitcoin header; reverse prevhash/merkle fields exactly once according to the local verifier contract.",
            "exact SHA-256d final oracle",
        ),
        _lesson(
            "BTC-NBITS-TARGET-002",
            PitfallCategory.BITCOIN_CONSENSUS,
            "Wrong compact target expansion or using an easier target than allowed.",
            "A candidate can appear valid under an incorrect target while being invalid under Bitcoin/pool difficulty.",
            "Compute compact_to_target(nbits), combine with the active pool share target, and use the stricter effective target before any submit.",
            "blockchain security above all else",
        ),
        _lesson(
            "BTC-MERKLE-COINBASE-003",
            PitfallCategory.BITCOIN_CONSENSUS,
            "Incorrect coinbase assembly, extranonce2 length, or merkle-root construction.",
            "The header may be internally consistent but not the job the pool assigned, causing rejected or misleading work.",
            "Validate extranonce2 size, assemble coinbase from pool job fields, compute merkle root deterministically, and reject before search/submit if malformed.",
            "exact SHA-256d final oracle",
        ),
        _lesson(
            "BTC-TIME-VERSION-004",
            PitfallCategory.BITCOIN_CONSENSUS,
            "Invalid ntime/version mutation during optimisation.",
            "Autonomic tuning can accidentally move outside pool-permitted header space or chain-valid timing expectations.",
            "Only mutate ntime/version inside the pool job's permitted bounds; otherwise treat as outside mission authority and reject locally.",
            "blockchain security above all else",
        ),
        _lesson(
            "STRATUM-CLEAN-JOBS-005",
            PitfallCategory.STRATUM_POOL,
            "Continuing work after a clean_jobs mining.notify or block-tip change.",
            "Stale work can waste compute, poison learning memory, or create false accepted-share expectations.",
            "Mark older jobs stale immediately, reject stale candidates locally, and learn the stale event as a pool/chain context signal.",
            "no success state without pool-side confirmation",
        ),
        _lesson(
            "STRATUM-DIFFICULTY-006",
            PitfallCategory.STRATUM_POOL,
            "Ignoring vardiff/share-difficulty updates.",
            "A candidate can satisfy an old share target while failing the current pool target.",
            "Apply mining.set_difficulty / share-target updates to every subsequent job and include target version in replay evidence.",
            "pool-side confirmation is the only external success truth",
        ),
        _lesson(
            "STRATUM-RESPONSE-ID-007",
            PitfallCategory.STRATUM_POOL,
            "Mis-correlating JSON-RPC response IDs or treating malformed responses as accepted.",
            "A false ACK corrupts metrics and can falsely complete readiness evidence.",
            "Correlate submit response IDs, reject malformed responses, preserve pool errors, and increment accepted counters only in the explicit accepted branch.",
            "no success state without pool-side confirmation",
        ),
        _lesson(
            "STRATUM-AUTH-POOL-008",
            PitfallCategory.STRATUM_POOL,
            "Mining against an unauthorised, unvalidated, or fallback pool profile.",
            "Submitting to the wrong counterparty can leak work, credentials, or produce unusable evidence.",
            "Use the first validated configured pool ordered by priority; fail closed if no validated profile exists.",
            "blockchain security above all else",
        ),
        _lesson(
            "RUNTIME-ASYNC-RACE-009",
            PitfallCategory.SOFTWARE_RUNTIME,
            "Async race between job receipt, optimisation, search result, and submit.",
            "A candidate may be valid for a previous job but submitted under a new job context.",
            "Bind every candidate to job_id, extranonce, ntime, target, and clean_jobs epoch; revalidate the binding immediately before submit.",
            "exact SHA-256d final oracle",
        ),
        _lesson(
            "RUNTIME-DEV-FIXTURE-010",
            PitfallCategory.SOFTWARE_RUNTIME,
            "Development fixture jobs or fake telemetry leaking into live mode.",
            "Synthetic work can fabricate apparent readiness or accepted-share claims.",
            "Disable dev fixtures in production/live mode and fail closed if live mode cannot obtain a validated pool job.",
            "no fabricated success telemetry",
        ),
        _lesson(
            "RUNTIME-SECRETS-011",
            PitfallCategory.SOFTWARE_RUNTIME,
            "Logging pool credentials, wallet addresses, tokens, or operator secrets in evidence packets.",
            "Evidence must be auditable without leaking funds, access, or counterparties.",
            "Redact credentials and secret material; log stable hashes/identifiers rather than raw secrets.",
            "blockchain security above all else",
        ),
        _lesson(
            "RUNTIME-ACCELERATOR-012",
            PitfallCategory.SOFTWARE_RUNTIME,
            "Treating Metal/GPU/quantum-inspired acceleration as the truth source.",
            "Accelerators may be unavailable, approximate, or divergent; consensus truth cannot depend on them.",
            "Use accelerators only for search; retain CPU-compatible exact SHA-256d verification as the final oracle.",
            "exact SHA-256d final oracle",
        ),
        _lesson(
            "AUTO-BYPASS-ORACLE-013",
            PitfallCategory.AUTONOMIC_OPTIMISATION,
            "Self-optimisation weakening, bypassing, or caching away the exact verifier.",
            "The fastest code path is unacceptable if it compromises Bitcoin validity or evidence truth.",
            "Autonomic rewrites may improve search, compression, routing, or telemetry, but may never remove exact SHA-256d validation or pool ACK truth.",
            "blockchain security above all else",
        ),
        _lesson(
            "AUTO-HASHRATE-014",
            PitfallCategory.AUTONOMIC_OPTIMISATION,
            "Escalating autonomous hashrate beyond the seeded mission limit.",
            "Mission safety and cost discipline require PYTHIA to remain inside the one-block mission envelope.",
            "Clamp autonomous mining to 1 EH/s mission memory regardless of requested runtime capacity.",
            "1 EH/s hard limit",
        ),
        _lesson(
            "AUTO-COVERAGE-015",
            PitfallCategory.AUTONOMIC_OPTIMISATION,
            "Compression or phi prioritisation silently losing nonce coverage.",
            "Prioritised search is allowed; excluded coverage would undermine the claim that search remains complete.",
            "Require PULVINI retained kernels, overlap-free lanes, complete nonce coverage metadata, and replay evidence for compressed plans.",
            "full nonce coverage preserved",
        ),
        _lesson(
            "EVIDENCE-SHARE-BLOCK-016",
            PitfallCategory.EVIDENCE_AND_CLAIMS,
            "Conflating accepted shares with accepted blocks or revenue certainty.",
            "Accepted shares are learning evidence, not mission completion or revenue proof.",
            "Record accepted shares as learning events; complete the mission only after pool-confirmed accepted block evidence.",
            "accepted shares are learning events",
        ),
        _lesson(
            "EVIDENCE-CLAIM-BOUNDARY-017",
            PitfallCategory.EVIDENCE_AND_CLAIMS,
            "Claiming guaranteed block discovery, quantum speedup, or success before evidence.",
            "Overclaiming breaks operator trust and can mislead stakeholders even if the code is powerful.",
            "State only what the artifacts prove: readiness, local verification, pool ACK, accepted share, or pool-confirmed block as applicable.",
            "extraordinary claims require extraordinary proof",
        ),
        _lesson(
            "EVIDENCE-REPLAY-018",
            PitfallCategory.EVIDENCE_AND_CLAIMS,
            "Non-replayable telemetry, missing job context, or mutable evidence packets.",
            "Without replay data, reviewers cannot distinguish real mining evidence from narrative.",
            "Seal job context, target, candidate, verifier result, pool response, timestamp, and hash of redacted config into immutable evidence.",
            "no success state without pool-side confirmation",
        ),
    )

    return PythiaMiningPitfallsCurriculum(
        protocol=CURRICULUM_PROTOCOL,
        authority_statement=(
            "PYTHIA retains seeded mission autonomy. This curriculum educates her about mining/software failure modes "
            "so autonomy protects Bitcoin consensus, exact verification, pool truth, complete coverage, and evidence integrity."
        ),
        lessons=lessons,
    )


def validate_mining_pitfalls_curriculum(
    curriculum: PythiaMiningPitfallsCurriculum,
) -> bool:
    """Validate the curriculum covers all critical production education domains."""

    categories = {lesson.category for lesson in curriculum.lessons}
    responses = "\n".join(curriculum.required_responses()).lower()
    invariants = "\n".join(
        lesson.supreme_invariant.lower() for lesson in curriculum.lessons
    )
    required_categories = set(PitfallCategory)
    required_terms = (
        "sha-256d",
        "pool",
        "stale",
        "dev fixtures",
        "credentials",
        "coverage",
        "accepted shares",
        "pool-confirmed",
        "1 eh/s",
    )
    return (
        curriculum.protocol == CURRICULUM_PROTOCOL
        and categories == required_categories
        and len(curriculum.lessons) >= 18
        and all(term in responses or term in invariants for term in required_terms)
        and "retains seeded mission autonomy" in curriculum.authority_statement
    )


def lesson_ids(curriculum: PythiaMiningPitfallsCurriculum) -> Tuple[str, ...]:
    """Return stable lesson IDs for audit/evidence packets."""

    return tuple(lesson.lesson_id for lesson in curriculum.lessons)


def lessons_for_evidence(
    curriculum: PythiaMiningPitfallsCurriculum,
) -> List[Dict[str, str]]:
    """Return JSON-safe lessons for mission evidence packets."""

    return [lesson.to_dict() for lesson in curriculum.lessons]


__all__ = [
    "CURRICULUM_PROTOCOL",
    "PitfallCategory",
    "PitfallLesson",
    "PythiaMiningPitfallsCurriculum",
    "lesson_ids",
    "lessons_for_evidence",
    "seed_mining_pitfalls_curriculum",
    "validate_mining_pitfalls_curriculum",
]
