"""Comprehensive tests for Pythia integration adapters.

This test suite validates:
1. SubstatePassportAdapter for migration compatibility
2. MiningSearchAdapter for unified search integration
3. MiningCausalAdapter for causal attribution integration
4. MiningPassportFactory for passport creation
5. Integration with existing Pythia mining code
6. Property-based tests for mathematical invariants
7. Auditable JSON output generation
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Mapping

import pytest
from hypothesis import given, strategies as st
from hypothesis.strategies import dictionaries, floats, integers, text

from python_backend.core.audit.universal_passport import (
    ClaimType,
    EpistemicBound,
    Subsystem,
    UniversalPassport,
)
from python_backend.core.attribution.causal_router import (
    CausalAttributionEngine,
    CausalHotspot,
    CounterfactualResult,
    CausalExplanation,
    FabricGraph,
    MiningGraph,
)
from python_backend.core.integration.pythia_adapters import (
    MiningCausalAdapter,
    MiningPassportFactory,
    MiningSearchAdapter,
    SubstatePassportAdapter,
)


# ============================================================================
# Mock SubstatePassport for testing
# ============================================================================


@dataclass
class MockSubstatePassport:
    """Mock SubstatePassport for testing migration adapter."""

    structural_hash: str = "abc123"
    passport_hash: str = "def456"
    topology_verified: bool = True
    coverage_verified: bool = True
    quantum_speedup_claimed: bool = False
    manifold_dimension: int = 20
    information_content: float = 0.5
    timestamp_ns: int = 1234567890000000000


# ============================================================================
# Unit Tests for SubstatePassportAdapter
# ============================================================================


class TestSubstatePassportAdapter:
    """Test SubstatePassportAdapter for migration compatibility."""

    def test_from_substate_passport(self):
        """Test converting SubstatePassport to UniversalPassport."""
        mock_substate = MockSubstatePassport()
        adapter = SubstatePassportAdapter()
        
        universal_passport = adapter.from_substate_passport(mock_substate)
        
        assert isinstance(universal_passport, UniversalPassport)
        assert universal_passport.subsystem == Subsystem.PYTHIA.value
        assert universal_passport.claim_type == ClaimType.MINING_RESULT.value
        assert universal_passport.payload["structural_hash"] == "abc123"
        assert universal_passport.payload["topology_verified"] is True

    def test_to_substate_passport(self):
        """Test converting UniversalPassport back to SubstatePassport format."""
        mock_substate = MockSubstatePassport()
        adapter = SubstatePassportAdapter()
        
        universal_passport = adapter.from_substate_passport(mock_substate)
        substate_dict = adapter.to_substate_passport(universal_passport)
        
        assert substate_dict["structural_hash"] == "abc123"
        assert substate_dict["topology_verified"] is True
        assert substate_dict["version"] == "SUBSTATE_PASSPORT_V2"

    def test_roundtrip_conversion(self):
        """Test roundtrip conversion preserves data."""
        mock_substate = MockSubstatePassport()
        adapter = SubstatePassportAdapter()
        
        universal_passport = adapter.from_substate_passport(mock_substate)
        substate_dict = adapter.to_substate_passport(universal_passport)
        
        # Verify key fields preserved
        assert substate_dict["structural_hash"] == mock_substate.structural_hash
        assert substate_dict["topology_verified"] == mock_substate.topology_verified
        assert substate_dict["coverage_verified"] == mock_substate.coverage_verified

    def test_epistemic_bounds_mapping(self):
        """Test that epistemic bounds are correctly mapped."""
        mock_substate = MockSubstatePassport(quantum_speedup_claimed=False)
        adapter = SubstatePassportAdapter()
        
        universal_passport = adapter.from_substate_passport(mock_substate)
        
        # Should include NO_QUANTUM_SPEEDUP bound when quantum_speedup_claimed is False
        assert EpistemicBound.NO_QUANTUM_SPEEDUP.value in universal_passport.epistemic_bounds


# ============================================================================
# Unit Tests for MiningSearchAdapter
# ============================================================================


class TestMiningSearchAdapter:
    """Test MiningSearchAdapter for unified search integration."""

    def test_adapter_creation(self):
        """Test creating a mining search adapter."""
        adapter = MiningSearchAdapter(
            target_nonce=50,
            nonce_range=(0, 100),
            phi_threshold=0.618,
        )
        
        assert adapter.domain.target_nonce == 50
        assert adapter.domain.nonce_range == (0, 100)

    def test_search_nonce(self):
        """Test searching for nonce using unified kernel."""
        adapter = MiningSearchAdapter(
            target_nonce=50,
            nonce_range=(0, 100),
        )
        
        result = adapter.search_nonce(budget=10, seed=42)
        
        assert "nonce" in result
        assert "phi_score" in result
        assert "iterations_used" in result
        assert "passport" in result
        assert result["iterations_used"] <= 10

    def test_search_nonce_deterministic(self):
        """Test that search is deterministic with same seed."""
        adapter = MiningSearchAdapter(
            target_nonce=50,
            nonce_range=(0, 100),
        )
        
        result1 = adapter.search_nonce(budget=10, seed=42)
        result2 = adapter.search_nonce(budget=10, seed=42)
        
        assert result1["nonce"] == result2["nonce"]
        assert result1["phi_score"] == result2["phi_score"]

    def test_get_warm_cache_stats(self):
        """Test getting warm cache statistics."""
        adapter = MiningSearchAdapter(
            target_nonce=50,
            nonce_range=(0, 100),
            warm_cache_size=100,
        )
        
        stats = adapter.get_warm_cache_stats()
        
        assert "size" in stats
        assert "max_size" in stats
        assert "has_warm_state" in stats
        assert stats["max_size"] == 100


# ============================================================================
# Unit Tests for MiningCausalAdapter
# ============================================================================


class TestMiningCausalAdapter:
    """Test MiningCausalAdapter for causal attribution integration."""

    def test_adapter_creation(self):
        """Test creating a mining causal adapter."""
        mining_nodes = {
            "solver": {"type": "hendrix_phi"},
            "memory": {"type": "hebbian_kernel"},
        }
        mining_edges = {
            "solver": ["memory"],
            "memory": ["solver"],
        }
        
        adapter = MiningCausalAdapter(
            mining_nodes=mining_nodes,
            mining_edges=mining_edges,
            coverage_threshold=0.8,
        )
        
        assert adapter.engine.coverage_threshold == 0.8

    def test_explain_nonce_discovery(self):
        """Test generating causal explanation for nonce discovery."""
        mining_nodes = {
            "solver": {"type": "hendrix_phi"},
            "memory": {"type": "hebbian_kernel"},
        }
        mining_edges = {
            "solver": ["memory"],
            "memory": ["solver"],
        }
        
        adapter = MiningCausalAdapter(
            mining_nodes=mining_nodes,
            mining_edges=mining_edges,
        )
        
        explanation = adapter.explain_nonce_discovery(
            nonce=42,
            phi_score=0.8,
        )
        
        assert "hotspots" in explanation
        assert "counterfactual" in explanation
        assert "explanation_quality" in explanation
        assert "timestamp" in explanation

    def test_rank_mining_hotspots(self):
        """Test ranking mining components by causal impact."""
        mining_nodes = {
            "solver": {"type": "hendrix_phi"},
            "memory": {"type": "hebbian_kernel"},
        }
        mining_edges = {
            "solver": ["memory"],
            "memory": ["solver"],
        }
        
        adapter = MiningCausalAdapter(
            mining_nodes=mining_nodes,
            mining_edges=mining_edges,
        )
        
        hotspots = adapter.rank_mining_hotspots({"type": "nonce_found"})
        
        assert isinstance(hotspots, list)
        assert all("node_id" in h for h in hotspots)


# ============================================================================
# Unit Tests for MiningPassportFactory
# ============================================================================


class TestMiningPassportFactory:
    """Test MiningPassportFactory for passport creation."""

    def test_create_nonce_passport(self):
        """Test creating a passport for nonce discovery."""
        passport = MiningPassportFactory.create_nonce_passport(
            nonce=42,
            job_id="job_123",
            pool_name="test_pool",
            phi_score=0.8,
            bures_score=0.9,
        )
        
        assert isinstance(passport, UniversalPassport)
        assert passport.subsystem == Subsystem.PYTHIA.value
        assert passport.payload["nonce"] == 42
        assert passport.payload["job_id"] == "job_123"

    def test_create_share_passport(self):
        """Test creating a passport for share submission."""
        passport = MiningPassportFactory.create_share_passport(
            share_hash="abc123",
            job_id="job_123",
            difficulty=1.0,
            submitter="miner_1",
        )
        
        assert isinstance(passport, UniversalPassport)
        assert passport.claim_type == ClaimType.SHARE_SUBMISSION.value
        assert passport.payload["share_hash"] == "abc123"

    def test_create_mining_result_passport(self):
        """Test creating a passport for general mining results."""
        passport = MiningPassportFactory.create_mining_result_passport(
            result_type="nonce_found",
            result_data={"nonce": 42},
            success=True,
        )
        
        assert isinstance(passport, UniversalPassport)
        assert passport.claim_type == ClaimType.MINING_RESULT.value
        assert passport.payload["result_type"] == "nonce_found"
        assert passport.payload["success"] is True

    def test_nonce_passport_with_additional_metadata(self):
        """Test creating nonce passport with additional metadata."""
        passport = MiningPassportFactory.create_nonce_passport(
            nonce=42,
            job_id="job_123",
            pool_name="test_pool",
            phi_score=0.8,
            bures_score=0.9,
            additional_metadata={"custom_field": "value"},
        )
        
        assert passport.payload["custom_field"] == "value"


# ============================================================================
# Integration Tests
# ============================================================================


class TestPythiaAdapterIntegration:
    """Test integration of all adapters with existing Pythia code."""

    def test_full_mining_workflow(self):
        """Test complete mining workflow using adapters."""
        # Step 1: Create nonce passport
        nonce_passport = MiningPassportFactory.create_nonce_passport(
            nonce=42,
            job_id="job_123",
            pool_name="test_pool",
            phi_score=0.8,
            bures_score=0.9,
        )
        
        # Step 2: Search for nonce
        search_adapter = MiningSearchAdapter(
            target_nonce=42,
            nonce_range=(0, 100),
        )
        search_result = search_adapter.search_nonce(budget=10)
        
        # Step 3: Generate causal explanation
        causal_adapter = MiningCausalAdapter(
            mining_nodes={
                "solver": {"type": "hendrix_phi"},
                "memory": {"type": "hebbian_kernel"},
            },
            mining_edges={
                "solver": ["memory"],
                "memory": ["solver"],
            },
        )
        explanation = causal_adapter.explain_nonce_discovery(
            nonce=42,
            phi_score=0.8,
        )
        
        # Verify all steps completed
        assert isinstance(nonce_passport, UniversalPassport)
        assert "nonce" in search_result
        assert "hotspots" in explanation

    def test_adapter_json_serialization(self):
        """Test that adapter outputs are JSON-serializable and auditable."""
        passport = MiningPassportFactory.create_nonce_passport(
            nonce=42,
            job_id="job_123",
            pool_name="test_pool",
            phi_score=0.8,
            bures_score=0.9,
        )
        
        # Should be JSON-serializable
        passport_dict = passport.to_dict()
        json_str = json.dumps(passport_dict)
        
        # Should be deserializable
        deserialized = json.loads(json_str)
        assert deserialized["nonce"] == 42

    def test_search_result_auditable(self):
        """Test that search results are auditable."""
        adapter = MiningSearchAdapter(
            target_nonce=50,
            nonce_range=(0, 100),
        )
        
        result = adapter.search_nonce(budget=10)
        
        # Should be JSON-serializable
        json_str = json.dumps(result)
        deserialized = json.loads(json_str)
        
        assert "nonce" in deserialized
        assert "passport" in deserialized
        assert "timestamp" in deserialized["passport"]


# ============================================================================
# Property-Based Tests
# ============================================================================


class TestAdapterProperties:
    """Property-based tests for adapter invariants."""

    @given(
        nonce=integers(min_value=0, max_value=1000000),
        job_id=text(min_size=1, max_size=20),
        pool_name=text(min_size=1, max_size=20),
        phi_score=floats(min_value=0.0, max_value=1.0),
        bures_score=floats(min_value=0.0, max_value=1.0),
    )
    def test_property_nonce_passport_valid(self, nonce, job_id, pool_name, phi_score, bures_score):
        """Property: Nonce passports are always valid."""
        passport = MiningPassportFactory.create_nonce_passport(
            nonce=nonce,
            job_id=job_id,
            pool_name=pool_name,
            phi_score=phi_score,
            bures_score=bures_score,
        )
        
        assert isinstance(passport, UniversalPassport)
        assert passport.payload["nonce"] == nonce
        assert 0.0 <= passport.payload["phi_score"] <= 1.0

    @given(
        share_hash=text(min_size=1, max_size=64),
        job_id=text(min_size=1, max_size=20),
        difficulty=floats(min_value=0.1, max_value=100.0),
    )
    def test_property_share_passport_serializable(self, share_hash, job_id, difficulty):
        """Property: Share passports are always JSON-serializable."""
        passport = MiningPassportFactory.create_share_passport(
            share_hash=share_hash,
            job_id=job_id,
            difficulty=difficulty,
            submitter="miner_1",
        )
        
        passport_dict = passport.to_dict()
        json_str = json.dumps(passport_dict)
        
        # Should not raise
        deserialized = json.loads(json_str)
        assert deserialized["share_hash"] == share_hash


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
