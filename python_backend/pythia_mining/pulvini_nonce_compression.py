"""Pre-search PULVINI nonce-space compression.

The pool gives one 32-bit nonce space. PULVINI first partitions that space
into the 32 verified D/I lanes, then applies the same golden-ratio folding
contract used by the memory layer to the lane surface before search planning.

The folded surface is the active working set. Retained lane segments are the
coverage kernel, so every uint32 nonce remains covered exactly once.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import asdict, dataclass
from typing import Any, List, Sequence, Tuple

import numpy as np

from .pulvini_phi_memory import PulviniPhiMemoryCompressionEngine

NONCE_BITS = 32
NONCE_SPACE_SIZE = 1 << NONCE_BITS
MAX_UINT32_NONCE = NONCE_SPACE_SIZE - 1


@dataclass(frozen=True)
class NonceSegment:
    lane_id: int
    start: int
    end: int

    @property
    def size(self) -> int:
        return int(self.end - self.start + 1)

    def contains(self, nonce: int) -> bool:
        return self.start <= int(nonce) <= self.end

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CompressedNonceCoordinate:
    coordinate_id: int
    folded_lane_value: float
    active_segments: Tuple[NonceSegment, ...]

    @property
    def coverage_size(self) -> int:
        return int(sum(segment.size for segment in self.active_segments))

    def contains(self, nonce: int) -> bool:
        return any(segment.contains(nonce) for segment in self.active_segments)

    def to_dict(self) -> dict[str, Any]:
        return {
            "coordinate_id": self.coordinate_id,
            "folded_lane_value": self.folded_lane_value,
            "coverage_size": self.coverage_size,
            "active_segments": [segment.to_dict() for segment in self.active_segments],
        }


@dataclass(frozen=True)
class CompressedNonceSpacePlan:
    nonce_space_size: int
    original_lanes: int
    working_set_dimension: int
    retained_kernel_lanes: int
    working_set_compression_ratio: float
    complete_coverage: bool
    overlap_free: bool
    coordinates: Tuple[CompressedNonceCoordinate, ...]
    coverage_segments: Tuple[NonceSegment, ...]

    @property
    def solver_ranges(self) -> List[Tuple[int, int]]:
        return [(segment.start, segment.end) for segment in self.coverage_segments]

    @property
    def coverage_size(self) -> int:
        return int(sum(segment.size for segment in self.coverage_segments))

    def coordinate_for_nonce(self, nonce: int) -> CompressedNonceCoordinate | None:
        for coordinate in self.coordinates:
            if coordinate.contains(nonce):
                return coordinate
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "nonce_space_size": self.nonce_space_size,
            "original_lanes": self.original_lanes,
            "working_set_dimension": self.working_set_dimension,
            "retained_kernel_lanes": self.retained_kernel_lanes,
            "working_set_compression_ratio": self.working_set_compression_ratio,
            "complete_coverage": self.complete_coverage,
            "overlap_free": self.overlap_free,
            "coverage_size": self.coverage_size,
            "coordinates": [coordinate.to_dict() for coordinate in self.coordinates],
            "coverage_segments": [segment.to_dict() for segment in self.coverage_segments],
        }


class PulviniNonceSpaceCompressor:
    """Compress the lane surface before search while retaining exact coverage."""

    def __init__(self, *, lanes: int = 32, nonce_space_size: int = NONCE_SPACE_SIZE) -> None:
        if lanes <= 0:
            raise ValueError("lanes must be positive")
        if nonce_space_size <= 0 or nonce_space_size % lanes != 0:
            raise ValueError("nonce_space_size must be positive and divisible by lanes")
        self.lanes = int(lanes)
        self.nonce_space_size = int(nonce_space_size)
        self.lane_size = self.nonce_space_size // self.lanes
        self.engine = PulviniPhiMemoryCompressionEngine(fold_depth=1)
        self.current_plan: CompressedNonceSpacePlan | None = None

    def _segments(self) -> Tuple[NonceSegment, ...]:
        return tuple(
            NonceSegment(
                lane_id=lane_id,
                start=lane_id * self.lane_size,
                end=((lane_id + 1) * self.lane_size) - 1,
            )
            for lane_id in range(self.lanes)
        )

    @staticmethod
    def _overlap_free(segments: Sequence[NonceSegment]) -> bool:
        ordered = sorted(segments, key=lambda segment: segment.start)
        return all(
            ordered[index - 1].end < ordered[index].start for index in range(1, len(ordered))
        )

    def phi_resonant(self, nonce: int, threshold: float = 0.5) -> bool:
        material = f"phi-search:{int(nonce) % self.nonce_space_size}".encode("utf-8")
        digest = hashlib.blake2b(material, digest_size=8).digest()
        sample = int.from_bytes(digest, "big") / float(2**64)
        phi = (1.0 + math.sqrt(5.0)) / 2.0
        score = 1.0 - abs(0.5 - ((sample * phi) % 1.0)) * 2.0
        return bool(score >= float(threshold))

    def build_compression_plan(self) -> CompressedNonceSpacePlan:
        return self.build_plan()

    def build_plan(self) -> CompressedNonceSpacePlan:
        segments = self._segments()
        lane_surface = np.arange(self.lanes, dtype=np.float64)
        fold = self.engine.compress(lane_surface)
        folded_values = np.asarray(fold.working_set, dtype=np.float64).reshape(-1)
        working_dim = int(folded_values.size)
        kernel_lanes = max(0, self.lanes - working_dim)

        coordinates: List[CompressedNonceCoordinate] = []
        for coordinate_id, folded_value in enumerate(folded_values):
            active = [segments[coordinate_id]]
            paired_lane = working_dim + coordinate_id
            if paired_lane < self.lanes:
                active.append(segments[paired_lane])
            coordinates.append(
                CompressedNonceCoordinate(
                    coordinate_id=coordinate_id,
                    folded_lane_value=float(folded_value),
                    active_segments=tuple(active),
                )
            )

        complete_size = sum(segment.size for segment in segments)
        overlap_free = self._overlap_free(segments)
        plan = CompressedNonceSpacePlan(
            nonce_space_size=self.nonce_space_size,
            original_lanes=self.lanes,
            working_set_dimension=working_dim,
            retained_kernel_lanes=kernel_lanes,
            working_set_compression_ratio=float(self.lanes / max(1, working_dim)),
            complete_coverage=bool(complete_size == self.nonce_space_size and overlap_free),
            overlap_free=overlap_free,
            coordinates=tuple(coordinates),
            coverage_segments=segments,
        )
        self.current_plan = plan
        return plan


def build_pulvini_nonce_plan(
    *, lanes: int = 32, nonce_space_size: int = NONCE_SPACE_SIZE
) -> CompressedNonceSpacePlan:
    """Build a PULVINI nonce compression plan.

    Convenience function that creates a compressor and builds the plan.
    """
    compressor = PulviniNonceSpaceCompressor(lanes=lanes, nonce_space_size=nonce_space_size)
    return compressor.build_plan()


__all__ = [
    "CompressedNonceCoordinate",
    "CompressedNonceSpacePlan",
    "NonceSegment",
    "PulviniNonceSpaceCompressor",
    "build_pulvini_nonce_plan",
]
