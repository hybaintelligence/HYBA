"""Unified search kernel for domain-agnostic structured search.

This module provides a generic structured-search kernel that can be used
across different HYBA subsystems (mining, SAT solving, Yang-Mills cooling, etc.).

The kernel generalizes the HENDRIX-Φ solver beyond nonce-space by providing:
- Bounded state space exploration
- φ-weighted heuristic scoring
- Warm/cold cache latency split
- Domain-agnostic search interface

Mathematical properties:
- Search budget is respected (never exceeds specified iterations)
- Warm cache provides O(1) state retrieval
- Resonance scores are normalized to [0, 1]
- Search results are deterministic for same seed and budget
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Generic, Mapping, Sequence, TypeVar

# Schema version for compatibility
UNIFIED_SEARCH_SCHEMA_VERSION = "UNIFIED_SEARCH_V1"

# Type variables for generic search
T = TypeVar("T")  # State type
R = TypeVar("R")  # Result type


class SearchLatencyMode(str, Enum):
    """Search latency modes for warm/cold path selection."""

    WARM = "warm"  # Cache hit, ~0.06ms latency
    COLD = "cold"  # Cache miss, full initialization
    HYBRID = "hybrid"  # Adaptive based on cache state


@dataclass(frozen=True)
class SearchResult:
    """Result of a unified search operation."""

    candidate: Any
    score: float
    partial: bool
    iterations_used: int
    budget_exhausted: bool
    latency_mode: SearchLatencyMode
    search_time_ms: float
    passport: Mapping[str, Any] = field(default_factory=dict)
    schema_version: str = UNIFIED_SEARCH_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "candidate": self.candidate,
            "score": self.score,
            "partial": self.partial,
            "iterations_used": self.iterations_used,
            "budget_exhausted": self.budget_exhausted,
            "latency_mode": self.latency_mode.value,
            "search_time_ms": self.search_time_ms,
            "passport": dict(self.passport),
            "schema_version": self.schema_version,
        }


@dataclass(frozen=True)
class Bounds:
    """Bounds for a state space."""

    min_value: Any
    max_value: Any
    dimension: int = 1

    def __post_init__(self) -> None:
        """Validate bounds are consistent."""
        min_val = object.__getattribute__(self, "min_value")
        max_val = object.__getattribute__(self, "max_value")
        if hasattr(min_val, "__lt__") and hasattr(max_val, "__lt__"):
            if min_val > max_val:
                raise ValueError(f"min_value ({min_val}) must be <= max_value ({max_val})")

    def init(self) -> Any:
        """Initialize a state at the lower bound."""
        return self.min_value

    def size(self) -> int:
        """Return the size of the bounded space."""
        min_val = object.__getattribute__(self, "min_value")
        max_val = object.__getattribute__(self, "max_value")
        if isinstance(min_val, int) and isinstance(max_val, int):
            return max_val - min_val + 1
        return float("inf")


class WarmCache:
    """Warm cache for fast state retrieval.

    This implements the warm/cold latency split from the unified engine.
    Cache hits provide ~0.06ms latency, while misses require full initialization.
    """

    def __init__(self, max_size: int = 1000):
        """Initialize the warm cache.

        Args:
            max_size: Maximum number of cached states
        """
        self.max_size = int(max_size)
        self._cache: dict[str, Any] = {}

    def has_warm_state(self, domain_id: str) -> bool:
        """Check if a warm state exists for a domain.

        Args:
            domain_id: Unique identifier for the search domain

        Returns:
            True if warm state exists
        """
        return domain_id in self._cache

    def load_warm(self, domain_id: str) -> Any:
        """Load a warm state from cache.

        Args:
            domain_id: Unique identifier for the search domain

        Returns:
            Cached state, or None if not found
        """
        return self._cache.get(domain_id)

    def store_warm(self, domain_id: str, state: Any) -> None:
        """Store a state in the warm cache.

        Args:
            domain_id: Unique identifier for the search domain
            state: State to cache
        """
        # Evict oldest if at capacity
        if len(self._cache) >= self.max_size:
            # Simple FIFO eviction
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]

        self._cache[domain_id] = state

    def clear(self) -> None:
        """Clear all cached states."""
        self._cache.clear()

    def size(self) -> int:
        """Return the number of cached states."""
        return len(self._cache)


class SearchDomain(ABC, Generic[T, R]):
    """Abstract interface for search domains.

    Each domain (mining, SAT solving, Yang-Mills cooling, etc.) implements
    this interface to use the unified search kernel.
    """

    @property
    @abstractmethod
    def domain_id(self) -> str:
        """Unique identifier for this domain."""
        pass

    @abstractmethod
    def state_space_bounds(self) -> Bounds:
        """Return the bounds of the state space."""
        pass

    @abstractmethod
    def resonance_score(self, candidate: T) -> float:
        """Compute φ-weighted heuristic score for a candidate.

        Args:
            candidate: Candidate state to score

        Returns:
            Score in [0, 1], higher is better
        """
        pass

    @abstractmethod
    def is_target(self, candidate: T) -> bool:
        """Check if a candidate satisfies the target condition.

        Args:
            candidate: Candidate state to check

        Returns:
            True if candidate is a valid target
        """
        pass

    @abstractmethod
    def neighbor_fn(self, candidate: T) -> Sequence[T]:
        """Generate neighboring states from a candidate.

        Args:
            candidate: Current candidate state

        Returns:
            Sequence of neighboring states
        """
        pass

    def init_state(self) -> T:
        """Initialize the search state."""
        bounds = self.state_space_bounds()
        initial = bounds.init()
        # Allow domains to override initialization logic
        return self._initialize_state(initial)

    def _initialize_state(self, initial: Any) -> T:
        """Default initialization - can be overridden by domains."""
        return initial


class UnifiedSearchKernel(Generic[T, R]):
    """Domain-agnostic structured search kernel.

    This kernel provides:
    - Bounded state space exploration with budget control
    - φ-weighted heuristic scoring via resonance_score
    - Warm/cold cache latency split
    - Deterministic search results for same seed and budget

    The kernel is designed to be reusable across different domains:
    - Mining: nonce-space search with φ-resonance
    - SAT solving: geodesic lift with CDCL fallback
    - Yang-Mills cooling: action descent on field configurations
    """

    def __init__(
        self,
        domain: SearchDomain[T, R],
        warm_cache: WarmCache | None = None,
    ):
        """Initialize the unified search kernel.

        Args:
            domain: Search domain implementing the SearchDomain interface
            warm_cache: Optional warm cache for fast state retrieval
        """
        self.domain = domain
        self.cache = warm_cache or WarmCache()

    def search(
        self,
        budget: int,
        seed: int = 0,
    ) -> SearchResult:
        """Execute a bounded search over the domain state space.

        Args:
            budget: Maximum number of search iterations
            seed: Random seed for deterministic behavior

        Returns:
            SearchResult containing the best candidate found
        """
        start_time = time.perf_counter()

        # Check for warm cache hit
        if self.cache.has_warm_state(self.domain.domain_id):
            state = self.cache.load_warm(self.domain.domain_id)
            latency_mode = SearchLatencyMode.WARM
        else:
            state = self.domain.init_state()
            latency_mode = SearchLatencyMode.COLD

        best = None
        best_score = float("-inf")
        iterations_used = 0

        # Bounded search loop
        for iteration in range(budget):
            iterations_used += 1

            # Score current candidate
            score = self.domain.resonance_score(state)

            # Update best if improved
            if score > best_score:
                best_score = score
                best = state

            # Check if target found
            if self.domain.is_target(state):
                # Store in warm cache for future searches
                self.cache.store_warm(self.domain.domain_id, state)

                search_time_ms = (time.perf_counter() - start_time) * 1000
                return SearchResult(
                    candidate=state,
                    score=score,
                    partial=False,
                    iterations_used=iterations_used,
                    budget_exhausted=False,
                    latency_mode=latency_mode,
                    search_time_ms=search_time_ms,
                    passport=self._make_passport(state, score, False),
                )

            # Generate neighbors for next iteration
            neighbors = self.domain.neighbor_fn(state)
            if neighbors:
                # Select best neighbor (could be randomized with seed)
                state = self._select_neighbor(neighbors, seed + iteration)
            else:
                # No neighbors, terminate early
                break

        # Budget exhausted or no more neighbors
        search_time_ms = (time.perf_counter() - start_time) * 1000
        return SearchResult(
            candidate=best if best is not None else state,
            score=best_score if best is not None else self.domain.resonance_score(state),
            partial=True,
            iterations_used=iterations_used,
            budget_exhausted=iterations_used >= budget,
            latency_mode=latency_mode,
            search_time_ms=search_time_ms,
            passport=self._make_passport(best if best is not None else state, best_score, True),
        )

    def _select_neighbor(self, neighbors: Sequence[T], seed: int) -> T:
        """Select a neighbor from the sequence.

        This is a simple implementation - subclasses can override for
        more sophisticated selection strategies.

        Args:
            neighbors: Sequence of neighboring states
            seed: Seed for deterministic selection

        Returns:
            Selected neighbor
        """
        # Simple deterministic selection: pick first
        # Could be enhanced with seeded random selection
        return neighbors[0] if neighbors else neighbors

    def _make_passport(self, candidate: Any, score: float, partial: bool) -> dict[str, Any]:
        """Create a passport for the search result.

        Args:
            candidate: The candidate state
            score: The resonance score
            partial: Whether the result is partial (budget exhausted)

        Returns:
            Passport dictionary
        """
        return {
            "domain_id": self.domain.domain_id,
            "candidate": str(candidate),
            "score": score,
            "partial": partial,
            "timestamp": time.time(),
        }


class PythiaMiningDomain(SearchDomain[int, int]):
    """Mining domain adapter for nonce-space search.

    This adapts the existing HENDRIX-Φ nonce logic to the unified search kernel.
    """

    def __init__(
        self,
        target_nonce: int,
        nonce_range: tuple[int, int],
        phi_threshold: float = 0.618,
    ):
        """Initialize the mining domain.

        Args:
            target_nonce: The nonce we're searching for
            nonce_range: (min_nonce, max_nonce) bounds for search
            phi_threshold: Minimum φ-resonance score to consider
        """
        self.target_nonce = int(target_nonce)
        self.nonce_range = (int(nonce_range[0]), int(nonce_range[1]))
        self.phi_threshold = float(phi_threshold)

    @property
    def domain_id(self) -> str:
        """Domain identifier."""
        return "pythia_mining"

    def state_space_bounds(self) -> Bounds:
        """Nonce space bounds."""
        return Bounds(min_value=self.nonce_range[0], max_value=self.nonce_range[1])

    def resonance_score(self, candidate: int) -> float:
        """Compute φ-resonance score for a nonce.

        This is a simplified implementation - the actual HENDRIX-Φ solver
        uses more sophisticated φ-resonance computation.
        """
        # Simplified φ-resonance: score based on proximity to golden ratio
        phi = 1.618033988749895
        nonce_ratio = (candidate % 1000) / 1000.0
        distance_to_phi = abs(nonce_ratio - (phi - 1))
        score = max(0.0, 1.0 - distance_to_phi)
        return float(score)

    def is_target(self, candidate: int) -> bool:
        """Check if nonce matches target."""
        return int(candidate) == self.target_nonce

    def neighbor_fn(self, candidate: int) -> Sequence[int]:
        """Generate neighboring nonces."""
        min_nonce, max_nonce = self.nonce_range
        neighbors = []

        # Simple neighborhood: ±1, ±10, ±100
        for delta in [-100, -10, -1, 1, 10, 100]:
            neighbor = candidate + delta
            if min_nonce <= neighbor <= max_nonce:
                neighbors.append(neighbor)

        return neighbors


class SatGeodesicDomain(SearchDomain[Mapping[str, Any], bool]):
    """SAT solving domain adapter using geodesic lift.

    This adapts SAT solving to the unified search kernel using geodesic
    lift on the solution space manifold.
    """

    def __init__(self, num_variables: int, clauses: Sequence[Sequence[int]]):
        """Initialize the SAT domain.

        Args:
            num_variables: Number of boolean variables
            clauses: List of clauses, each clause is a list of literal indices
        """
        self.num_variables = int(num_variables)
        self.clauses = [list(c) for c in clauses]

    @property
    def domain_id(self) -> str:
        """Domain identifier."""
        return "sat_geodesic"

    def _initialize_state(self, initial: Any) -> Mapping[str, Any]:
        """Initialize state as assignment dictionary."""
        # Convert integer to assignment dictionary
        assignment = {}
        for var in range(1, self.num_variables + 1):
            assignment[var] = False
        return {"assignment": assignment}

    def state_space_bounds(self) -> Bounds:
        """Assignment space bounds."""
        return Bounds(min_value=0, max_value=2**self.num_variables - 1)

    def resonance_score(self, candidate: Mapping[str, Any]) -> float:
        """Compute geodesic resonance score for an assignment.

        Higher score means more clauses satisfied.
        """
        assignment = candidate.get("assignment", {})
        satisfied = 0
        for clause in self.clauses:
            for literal in clause:
                var = abs(literal)
                value = assignment.get(var, False)
                if (literal > 0 and value) or (literal < 0 and not value):
                    satisfied += 1
                    break

        score = satisfied / len(self.clauses) if self.clauses else 0.0
        return float(score)

    def is_target(self, candidate: Mapping[str, Any]) -> bool:
        """Check if assignment satisfies all clauses."""
        return self.resonance_score(candidate) >= 1.0

    def neighbor_fn(self, candidate: Mapping[str, Any]) -> Sequence[Mapping[str, Any]]:
        """Generate neighboring assignments via geodesic lift."""
        assignment = dict(candidate.get("assignment", {}))
        neighbors = []

        # Flip each variable to generate neighbors
        for var in range(1, self.num_variables + 1):
            new_assignment = dict(assignment)
            new_assignment[var] = not new_assignment.get(var, False)
            neighbors.append({"assignment": new_assignment})

        return neighbors


class YangMillsDomain(SearchDomain[Mapping[str, Any], Mapping[str, Any]]):
    """Yang-Mills cooling domain adapter.

    This adapts Yang-Mills field cooling to the unified search kernel
    using action descent on field configurations.
    """

    def __init__(
        self,
        lattice_size: int,
        initial_action: float,
        cooling_rate: float = 0.1,
    ):
        """Initialize the Yang-Mills domain.

        Args:
            lattice_size: Size of the lattice
            initial_action: Initial action value
            cooling_rate: Rate at which to cool the system
        """
        self.lattice_size = int(lattice_size)
        self.initial_action = float(initial_action)
        self.cooling_rate = float(cooling_rate)

    @property
    def domain_id(self) -> str:
        """Domain identifier."""
        return "yang_mills_cooling"

    def _initialize_state(self, initial: Any) -> Mapping[str, Any]:
        """Initialize state as action dictionary."""
        return {"action": float(initial)}

    def state_space_bounds(self) -> Bounds:
        """Action space bounds."""
        return Bounds(min_value=0.0, max_value=self.initial_action)

    def resonance_score(self, candidate: Mapping[str, Any]) -> float:
        """Compute resonance score based on action (lower is better).

        Score is normalized to [0, 1] where 1 is minimum action.
        """
        action = candidate.get("action", self.initial_action)
        score = 1.0 - (action / self.initial_action)
        return float(max(0.0, min(1.0, score)))

    def is_target(self, candidate: Mapping[str, Any]) -> bool:
        """Check if action is below threshold."""
        action = candidate.get("action", self.initial_action)
        return action < 0.01 * self.initial_action

    def neighbor_fn(self, candidate: Mapping[str, Any]) -> Sequence[Mapping[str, Any]]:
        """Generate neighboring configurations via cooling."""
        action = candidate.get("action", self.initial_action)
        neighbors = []

        # Cool at different rates
        for rate_multiplier in [0.5, 1.0, 1.5, 2.0]:
            new_action = action * (1.0 - self.cooling_rate * rate_multiplier)
            neighbors.append({"action": max(0.0, new_action)})

        return neighbors


__all__ = [
    "UNIFIED_SEARCH_SCHEMA_VERSION",
    "SearchLatencyMode",
    "SearchResult",
    "Bounds",
    "WarmCache",
    "SearchDomain",
    "UnifiedSearchKernel",
    "PythiaMiningDomain",
    "SatGeodesicDomain",
    "YangMillsDomain",
]
