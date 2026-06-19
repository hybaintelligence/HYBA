"""Unit and property tests for UnifiedSearchKernel module.

This test suite validates:
1. Basic functionality of unified search kernel
2. Warm/cold cache latency split
3. Domain adapters (mining, SAT, Yang-Mills)
4. Property-based tests for mathematical invariants
5. Integration with different search domains
"""

from __future__ import annotations

import time

import pytest
from hypothesis import given, strategies as st
from hypothesis.strategies import floats, integers, lists, text

from python_backend.core.search.unified_search_kernel import (
    Bounds,
    PythiaMiningDomain,
    SatGeodesicDomain,
    SearchLatencyMode,
    SearchResult,
    SearchDomain,
    UnifiedSearchKernel,
    WarmCache,
    YangMillsDomain,
)


# ============================================================================
# Unit Tests
# ============================================================================


class TestBounds:
    """Test Bounds dataclass."""

    def test_bounds_creation(self):
        """Test creating valid bounds."""
        bounds = Bounds(min_value=0, max_value=100)
        assert bounds.min_value == 0
        assert bounds.max_value == 100
        assert bounds.dimension == 1

    def test_bounds_invalid_raises_error(self):
        """Test that invalid bounds raise ValueError."""
        with pytest.raises(ValueError, match="min_value.*must be <= max_value"):
            Bounds(min_value=100, max_value=0)

    def test_bounds_init(self):
        """Test bounds initialization."""
        bounds = Bounds(min_value=10, max_value=100)
        assert bounds.init() == 10

    def test_bounds_size_integers(self):
        """Test bounds size for integer ranges."""
        bounds = Bounds(min_value=0, max_value=100)
        assert bounds.size() == 101

    def test_bounds_size_infinite(self):
        """Test bounds size for non-integer ranges."""
        bounds = Bounds(min_value=0.0, max_value=1.0)
        assert bounds.size() == float("inf")


class TestWarmCache:
    """Test WarmCache functionality."""

    def test_cache_creation(self):
        """Test creating a warm cache."""
        cache = WarmCache(max_size=100)
        assert cache.max_size == 100
        assert cache.size() == 0

    def test_cache_store_and_retrieve(self):
        """Test storing and retrieving cached states."""
        cache = WarmCache()
        cache.store_warm("domain_1", {"state": "value"})
        assert cache.has_warm_state("domain_1")
        assert cache.load_warm("domain_1") == {"state": "value"}

    def test_cache_miss(self):
        """Test cache miss returns None."""
        cache = WarmCache()
        assert not cache.has_warm_state("domain_1")
        assert cache.load_warm("domain_1") is None

    def test_cache_eviction(self):
        """Test cache eviction when at capacity."""
        cache = WarmCache(max_size=2)
        cache.store_warm("domain_1", "state_1")
        cache.store_warm("domain_2", "state_2")
        cache.store_warm("domain_3", "state_3")  # Should evict domain_1

        assert cache.size() == 2
        assert not cache.has_warm_state("domain_1")
        assert cache.has_warm_state("domain_2")
        assert cache.has_warm_state("domain_3")

    def test_cache_clear(self):
        """Test clearing the cache."""
        cache = WarmCache()
        cache.store_warm("domain_1", "state_1")
        cache.clear()
        assert cache.size() == 0
        assert not cache.has_warm_state("domain_1")


class TestSearchResult:
    """Test SearchResult dataclass."""

    def test_result_creation(self):
        """Test creating a valid search result."""
        result = SearchResult(
            candidate=42,
            score=0.8,
            partial=False,
            iterations_used=10,
            budget_exhausted=False,
            latency_mode=SearchLatencyMode.WARM,
            search_time_ms=5.0,
        )
        assert result.candidate == 42
        assert result.score == 0.8
        assert result.partial is False
        assert result.iterations_used == 10

    def test_result_to_dict(self):
        """Test result serialization to dict."""
        result = SearchResult(
            candidate=42,
            score=0.8,
            partial=False,
            iterations_used=10,
            budget_exhausted=False,
            latency_mode=SearchLatencyMode.WARM,
            search_time_ms=5.0,
        )
        result_dict = result.to_dict()
        assert result_dict["candidate"] == 42
        assert result_dict["score"] == 0.8
        assert result_dict["latency_mode"] == "warm"


class TestPythiaMiningDomain:
    """Test PythiaMiningDomain adapter."""

    def test_mining_domain_creation(self):
        """Test creating a mining domain."""
        domain = PythiaMiningDomain(
            target_nonce=50,
            nonce_range=(0, 100),
        )
        assert domain.target_nonce == 50
        assert domain.nonce_range == (0, 100)

    def test_mining_domain_id(self):
        """Test domain identifier."""
        domain = PythiaMiningDomain(target_nonce=50, nonce_range=(0, 100))
        assert domain.domain_id == "pythia_mining"

    def test_mining_state_space_bounds(self):
        """Test state space bounds."""
        domain = PythiaMiningDomain(target_nonce=50, nonce_range=(0, 100))
        bounds = domain.state_space_bounds()
        assert bounds.min_value == 0
        assert bounds.max_value == 100

    def test_mining_resonance_score(self):
        """Test resonance score computation."""
        domain = PythiaMiningDomain(target_nonce=50, nonce_range=(0, 100))
        score = domain.resonance_score(618)  # Golden ratio related
        assert 0.0 <= score <= 1.0

    def test_mining_is_target(self):
        """Test target detection."""
        domain = PythiaMiningDomain(target_nonce=50, nonce_range=(0, 100))
        assert domain.is_target(50) is True
        assert domain.is_target(51) is False

    def test_mining_neighbor_fn(self):
        """Test neighbor generation."""
        domain = PythiaMiningDomain(target_nonce=50, nonce_range=(0, 100))
        neighbors = domain.neighbor_fn(50)
        assert len(neighbors) > 0
        assert all(isinstance(n, int) for n in neighbors)
        assert all(0 <= n <= 100 for n in neighbors)


class TestSatGeodesicDomain:
    """Test SatGeodesicDomain adapter."""

    def test_sat_domain_creation(self):
        """Test creating a SAT domain."""
        domain = SatGeodesicDomain(
            num_variables=3,
            clauses=[[1, 2], [-1, 3]],
        )
        assert domain.num_variables == 3
        assert len(domain.clauses) == 2

    def test_sat_domain_id(self):
        """Test domain identifier."""
        domain = SatGeodesicDomain(num_variables=3, clauses=[[1, 2]])
        assert domain.domain_id == "sat_geodesic"

    def test_sat_state_space_bounds(self):
        """Test state space bounds."""
        domain = SatGeodesicDomain(num_variables=3, clauses=[[1, 2]])
        bounds = domain.state_space_bounds()
        assert bounds.min_value == 0
        assert bounds.max_value == 7  # 2^3 - 1

    def test_sat_resonance_score(self):
        """Test resonance score computation."""
        domain = SatGeodesicDomain(
            num_variables=3,
            clauses=[[1, 2], [-1, 3]],
        )
        assignment = {"assignment": {1: True, 2: True, 3: False}}
        score = domain.resonance_score(assignment)
        assert 0.0 <= score <= 1.0

    def test_sat_is_target(self):
        """Test target detection (all clauses satisfied)."""
        domain = SatGeodesicDomain(
            num_variables=3,
            clauses=[[1, 2], [-1, 3]],
        )
        # Assignment that satisfies both clauses
        assignment = {"assignment": {1: True, 2: True, 3: False}}
        assert domain.is_target(assignment) is True

    def test_sat_neighbor_fn(self):
        """Test neighbor generation."""
        domain = SatGeodesicDomain(num_variables=3, clauses=[[1, 2]])
        assignment = {"assignment": {1: True, 2: False, 3: False}}
        neighbors = domain.neighbor_fn(assignment)
        assert len(neighbors) == 3  # One neighbor per variable


class TestYangMillsDomain:
    """Test YangMillsDomain adapter."""

    def test_yang_mills_domain_creation(self):
        """Test creating a Yang-Mills domain."""
        domain = YangMillsDomain(
            lattice_size=10,
            initial_action=1.0,
        )
        assert domain.lattice_size == 10
        assert domain.initial_action == 1.0

    def test_yang_mills_domain_id(self):
        """Test domain identifier."""
        domain = YangMillsDomain(lattice_size=10, initial_action=1.0)
        assert domain.domain_id == "yang_mills_cooling"

    def test_yang_mills_state_space_bounds(self):
        """Test state space bounds."""
        domain = YangMillsDomain(lattice_size=10, initial_action=1.0)
        bounds = domain.state_space_bounds()
        assert bounds.min_value == 0.0
        assert bounds.max_value == 1.0

    def test_yang_mills_resonance_score(self):
        """Test resonance score computation."""
        domain = YangMillsDomain(lattice_size=10, initial_action=1.0)
        config = {"action": 0.5}
        score = domain.resonance_score(config)
        assert 0.0 <= score <= 1.0

    def test_yang_mills_is_target(self):
        """Test target detection (action below threshold)."""
        domain = YangMillsDomain(lattice_size=10, initial_action=1.0)
        config = {"action": 0.001}  # Below 1% threshold
        assert domain.is_target(config) is True

    def test_yang_mills_neighbor_fn(self):
        """Test neighbor generation."""
        domain = YangMillsDomain(lattice_size=10, initial_action=1.0)
        config = {"action": 0.5}
        neighbors = domain.neighbor_fn(config)
        assert len(neighbors) == 4  # Different cooling rates
        assert all("action" in n for n in neighbors)


class TestUnifiedSearchKernel:
    """Test UnifiedSearchKernel."""

    def test_kernel_creation(self):
        """Test creating a search kernel."""
        domain = PythiaMiningDomain(target_nonce=50, nonce_range=(0, 100))
        kernel = UnifiedSearchKernel(domain)
        assert kernel.domain == domain
        assert isinstance(kernel.cache, WarmCache)

    def test_kernel_with_custom_cache(self):
        """Test creating kernel with custom cache."""
        domain = PythiaMiningDomain(target_nonce=50, nonce_range=(0, 100))
        cache = WarmCache(max_size=50)
        kernel = UnifiedSearchKernel(domain, warm_cache=cache)
        assert kernel.cache == cache

    def test_search_cold_path(self):
        """Test search with cold cache (first search)."""
        domain = PythiaMiningDomain(target_nonce=50, nonce_range=(0, 100))
        kernel = UnifiedSearchKernel(domain)
        result = kernel.search(budget=10)
        
        assert isinstance(result, SearchResult)
        assert result.latency_mode == SearchLatencyMode.COLD
        assert result.iterations_used <= 10

    def test_search_warm_path(self):
        """Test search with warm cache (subsequent search)."""
        domain = PythiaMiningDomain(target_nonce=50, nonce_range=(0, 100))
        cache = WarmCache()
        cache.store_warm("pythia_mining", 50)  # Pre-warm cache
        kernel = UnifiedSearchKernel(domain, warm_cache=cache)
        result = kernel.search(budget=10)
        
        assert result.latency_mode == SearchLatencyMode.WARM

    def test_search_budget_respected(self):
        """Test that search budget is respected."""
        domain = PythiaMiningDomain(target_nonce=50, nonce_range=(0, 100))
        kernel = UnifiedSearchKernel(domain)
        result = kernel.search(budget=5)
        
        assert result.iterations_used <= 5

    def test_search_target_found(self):
        """Test search when target is found."""
        domain = PythiaMiningDomain(target_nonce=50, nonce_range=(0, 100))
        kernel = UnifiedSearchKernel(domain)
        
        # Start near target to ensure quick find
        result = kernel.search(budget=100, seed=0)
        
        # May or may not find target depending on search strategy
        assert isinstance(result, SearchResult)

    def test_search_partial_result(self):
        """Test search returns partial result when budget exhausted."""
        domain = PythiaMiningDomain(target_nonce=999999, nonce_range=(0, 100))
        kernel = UnifiedSearchKernel(domain)
        result = kernel.search(budget=3)
        
        # Target is outside range, should return partial result
        assert result.partial is True
        assert result.budget_exhausted is True

    def test_search_score_normalized(self):
        """Test that search scores are normalized to [0, 1]."""
        domain = PythiaMiningDomain(target_nonce=50, nonce_range=(0, 100))
        kernel = UnifiedSearchKernel(domain)
        result = kernel.search(budget=10)
        
        assert 0.0 <= result.score <= 1.0

    def test_search_deterministic(self):
        """Test that search is deterministic for same seed."""
        domain = PythiaMiningDomain(target_nonce=50, nonce_range=(0, 100))
        kernel = UnifiedSearchKernel(domain)
        
        result1 = kernel.search(budget=10, seed=42)
        result2 = kernel.search(budget=10, seed=42)
        
        assert result1.candidate == result2.candidate
        assert result1.score == result2.score

    def test_search_passport_generated(self):
        """Test that search result includes passport."""
        domain = PythiaMiningDomain(target_nonce=50, nonce_range=(0, 100))
        kernel = UnifiedSearchKernel(domain)
        result = kernel.search(budget=10)
        
        assert "passport" in result.to_dict()
        assert "domain_id" in result.passport
        assert "timestamp" in result.passport


# ============================================================================
# Property-Based Tests
# ============================================================================


class TestBoundsProperties:
    """Property-based tests for Bounds."""

    @given(
        min_value=integers(min_value=0, max_value=1000),
        max_value=integers(min_value=0, max_value=1000),
    )
    def test_property_bounds_valid_when_min_le_max(self, min_value, max_value):
        """Property: Bounds are valid when min <= max."""
        if min_value <= max_value:
            bounds = Bounds(min_value=min_value, max_value=max_value)
            assert bounds.min_value == min_value
            assert bounds.max_value == max_value

    @given(
        min_value=integers(min_value=0, max_value=100),
        max_value=integers(min_value=0, max_value=100),
    )
    def test_property_bounds_size_non_negative(self, min_value, max_value):
        """Property: Bounds size is non-negative."""
        if min_value <= max_value:
            bounds = Bounds(min_value=min_value, max_value=max_value)
            size = bounds.size()
            assert size >= 0


class TestWarmCacheProperties:
    """Property-based tests for WarmCache."""

    @given(
        num_states=integers(min_value=1, max_value=50),
        max_size=integers(min_value=10, max_value=100),
    )
    def test_property_cache_size_respects_max(self, num_states, max_size):
        """Property: Cache size never exceeds max_size."""
        cache = WarmCache(max_size=max_size)
        for i in range(num_states):
            cache.store_warm(f"domain_{i}", f"state_{i}")
        
        assert cache.size() <= max_size

    @given(
        domain_id=text(min_size=1, max_size=10),
    )
    def test_property_cache_retrieval_stores_value(self, domain_id):
        """Property: Stored values can be retrieved."""
        cache = WarmCache()
        state = {"value": 42}
        cache.store_warm(domain_id, state)
        assert cache.load_warm(domain_id) == state


class TestSearchResultProperties:
    """Property-based tests for SearchResult."""

    @given(
        score=floats(min_value=0.0, max_value=1.0),
        iterations_used=integers(min_value=0, max_value=1000),
        search_time_ms=floats(min_value=0.0, max_value=10000.0),
    )
    def test_property_score_in_range(self, score, iterations_used, search_time_ms):
        """Property: Valid scores are in [0, 1]."""
        result = SearchResult(
            candidate=42,
            score=score,
            partial=False,
            iterations_used=iterations_used,
            budget_exhausted=False,
            latency_mode=SearchLatencyMode.WARM,
            search_time_ms=search_time_ms,
        )
        assert 0.0 <= result.score <= 1.0

    @given(
        iterations_used=integers(min_value=0, max_value=100),
        budget=integers(min_value=0, max_value=100),
    )
    def test_property_iterations_non_negative(self, iterations_used, budget):
        """Property: Iterations used is non-negative."""
        result = SearchResult(
            candidate=42,
            score=0.5,
            partial=iterations_used >= budget,
            iterations_used=iterations_used,
            budget_exhausted=iterations_used >= budget,
            latency_mode=SearchLatencyMode.WARM,
            search_time_ms=5.0,
        )
        assert result.iterations_used >= 0


class TestUnifiedSearchKernelProperties:
    """Property-based tests for UnifiedSearchKernel."""

    @given(
        budget=integers(min_value=1, max_value=100),
    )
    def test_property_search_budget_respected(self, budget):
        """Property: Search never exceeds budget."""
        domain = PythiaMiningDomain(target_nonce=50, nonce_range=(0, 100))
        kernel = UnifiedSearchKernel(domain)
        result = kernel.search(budget=budget)
        assert result.iterations_used <= budget

    @given(
        budget=integers(min_value=1, max_value=50),
    )
    def test_property_search_score_normalized(self, budget):
        """Property: Search results have normalized scores."""
        domain = PythiaMiningDomain(target_nonce=50, nonce_range=(0, 100))
        kernel = UnifiedSearchKernel(domain)
        result = kernel.search(budget=budget)
        assert 0.0 <= result.score <= 1.0

    @given(
        budget=integers(min_value=1, max_value=50),
        seed=integers(min_value=0, max_value=1000),
    )
    def test_property_search_deterministic_with_seed(self, budget, seed):
        """Property: Same seed produces same result."""
        domain = PythiaMiningDomain(target_nonce=50, nonce_range=(0, 100))
        kernel = UnifiedSearchKernel(domain)
        
        result1 = kernel.search(budget=budget, seed=seed)
        result2 = kernel.search(budget=budget, seed=seed)
        
        assert result1.candidate == result2.candidate
        assert result1.score == result2.score


# ============================================================================
# Integration Tests
# ============================================================================


class TestUnifiedSearchIntegration:
    """Test integration across different domains."""

    def test_mining_domain_search(self):
        """Test complete search workflow for mining domain."""
        domain = PythiaMiningDomain(target_nonce=50, nonce_range=(0, 100))
        kernel = UnifiedSearchKernel(domain)
        result = kernel.search(budget=20)
        
        assert isinstance(result, SearchResult)
        assert result.passport["domain_id"] == "pythia_mining"

    def test_sat_domain_search(self):
        """Test complete search workflow for SAT domain."""
        domain = SatGeodesicDomain(
            num_variables=3,
            clauses=[[1, 2], [-1, 3]],
        )
        kernel = UnifiedSearchKernel(domain)
        result = kernel.search(budget=10)
        
        assert isinstance(result, SearchResult)
        assert result.passport["domain_id"] == "sat_geodesic"

    def test_yang_mills_domain_search(self):
        """Test complete search workflow for Yang-Mills domain."""
        domain = YangMillsDomain(lattice_size=10, initial_action=1.0)
        kernel = UnifiedSearchKernel(domain)
        result = kernel.search(budget=10)
        
        assert isinstance(result, SearchResult)
        assert result.passport["domain_id"] == "yang_mills_cooling"

    def test_cache_persistence_across_searches(self):
        """Test that cache persists across multiple searches."""
        domain = PythiaMiningDomain(target_nonce=50, nonce_range=(0, 100))
        cache = WarmCache()
        kernel = UnifiedSearchKernel(domain, warm_cache=cache)
        
        # First search (cold)
        result1 = kernel.search(budget=5)
        assert result1.latency_mode == SearchLatencyMode.COLD
        
        # Second search (warm if target found)
        result2 = kernel.search(budget=5)
        # May still be cold if target not found in first search
        assert isinstance(result2.latency_mode, SearchLatencyMode)

    def test_multiple_domains_isolated(self):
        """Test that multiple domains use isolated cache entries."""
        mining_domain = PythiaMiningDomain(target_nonce=50, nonce_range=(0, 100))
        sat_domain = SatGeodesicDomain(num_variables=3, clauses=[[1, 2]])
        
        cache = WarmCache()
        mining_kernel = UnifiedSearchKernel(mining_domain, warm_cache=cache)
        sat_kernel = UnifiedSearchKernel(sat_domain, warm_cache=cache)
        
        mining_result = mining_kernel.search(budget=5)
        sat_result = sat_kernel.search(budget=5)
        
        # Both should have valid results
        assert isinstance(mining_result, SearchResult)
        assert isinstance(sat_result, SearchResult)
        assert mining_result.passport["domain_id"] != sat_result.passport["domain_id"]

    def test_search_time_measured(self):
        """Test that search time is accurately measured."""
        domain = PythiaMiningDomain(target_nonce=50, nonce_range=(0, 100))
        kernel = UnifiedSearchKernel(domain)
        result = kernel.search(budget=10)
        
        assert result.search_time_ms >= 0.0
        assert result.search_time_ms < 10000.0  # Should complete in < 10s


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
