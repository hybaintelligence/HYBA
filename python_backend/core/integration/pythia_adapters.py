"""Integration adapters for existing Pythia mining code.

This module provides minimal, additive adapters that connect the new
core modules (UniversalPassport, CausalAttributionEngine, UnifiedSearchKernel,
MemoryRoutedController) to the existing Pythia mining infrastructure.

The adapters follow the principle of wrapping or extending existing tested
code without rewriting core logic. They provide drop-in compatibility and
migration paths for the existing SubstatePassport system.
"""

from __future__ import annotations

from typing import Any, Mapping, Optional

from python_backend.core.audit.universal_passport import (
    ClaimType,
    EpistemicBound,
    Subsystem,
    UniversalPassport,
    make_passport,
    make_mining_passport,
)
from python_backend.core.attribution.causal_router import (
    CausalAttributionEngine,
    FabricGraph,
    MiningGraph,
)
from python_backend.core.search.unified_search_kernel import (
    PythiaMiningDomain,
    UnifiedSearchKernel,
    WarmCache,
)


class SubstatePassportAdapter:
    """Adapter for migrating SubstatePassport to UniversalPassport.

    This adapter provides a compatibility layer that allows existing
    SubstatePassport usage to gradually migrate to UniversalPassport.
    """

    @staticmethod
    def from_substate_passport(substate_passport: Any) -> UniversalPassport:
        """Convert a SubstatePassport to UniversalPassport.

        Args:
            substate_passport: Existing SubstatePassport instance

        Returns:
            UniversalPassport with equivalent information
        """
        # Extract relevant fields from SubstatePassport
        payload = {
            "structural_hash": getattr(substate_passport, "structural_hash", ""),
            "topology_verified": getattr(substate_passport, "topology_verified", False),
            "coverage_verified": getattr(substate_passport, "coverage_verified", False),
            "quantum_speedup_claimed": getattr(substate_passport, "quantum_speedup_claimed", False),
            "manifold_dimension": getattr(substate_passport, "manifold_dimension", 0),
            "information_content": getattr(substate_passport, "information_content", 0.0),
        }

        # Map epistemic bounds from existing flags
        epistemic_bounds = []
        if getattr(substate_passport, "quantum_speedup_claimed", False) is False:
            epistemic_bounds.append(EpistemicBound.NO_QUANTUM_SPEEDUP.value)

        return make_passport(
            subsystem=Subsystem.PYTHIA.value,
            claim_type=ClaimType.MINING_RESULT.value,
            payload=payload,
            epistemic_bounds=epistemic_bounds,
            timestamp=getattr(substate_passport, "timestamp_ns", 0) / 1e9,
        )

    @staticmethod
    def to_substate_passport(passport: UniversalPassport) -> dict[str, Any]:
        """Convert UniversalPassport back to SubstatePassport format.

        Args:
            passport: UniversalPassport instance

        Returns:
            Dictionary in SubstatePassport format
        """
        return {
            "structural_hash": passport.payload.get("structural_hash", ""),
            "passport_hash": passport.embedded_hash,
            "topology_verified": passport.payload.get("topology_verified", False),
            "coverage_verified": passport.payload.get("coverage_verified", False),
            "quantum_speedup_claimed": passport.payload.get("quantum_speedup_claimed", False),
            "manifold_dimension": passport.payload.get("manifold_dimension", 0),
            "information_content": passport.payload.get("information_content", 0.0),
            "timestamp_ns": int(passport.timestamp * 1e9),
            "version": "SUBSTATE_PASSPORT_V2",  # Migrated version
        }


class MiningSearchAdapter:
    """Adapter for integrating UnifiedSearchKernel with Pythia mining.

    This adapter wraps the existing HENDRIX-Φ solver logic in the
    UnifiedSearchKernel interface, providing domain-agnostic search
    capabilities while maintaining compatibility with existing code.
    """

    def __init__(
        self,
        target_nonce: int,
        nonce_range: tuple[int, int],
        phi_threshold: float = 0.618,
        warm_cache_size: int = 1000,
    ):
        """Initialize the mining search adapter.

        Args:
            target_nonce: The nonce to search for
            nonce_range: (min_nonce, max_nonce) bounds
            phi_threshold: Minimum φ-resonance score
            warm_cache_size: Size of warm cache for fast state retrieval
        """
        self.domain = PythiaMiningDomain(
            target_nonce=target_nonce,
            nonce_range=nonce_range,
            phi_threshold=phi_threshold,
        )
        self.cache = WarmCache(max_size=warm_cache_size)
        self.kernel = UnifiedSearchKernel(self.domain, warm_cache=self.cache)

    def search_nonce(
        self,
        budget: int,
        seed: int = 0,
    ) -> dict[str, Any]:
        """Search for nonce using unified kernel.

        Args:
            budget: Maximum search iterations
            seed: Random seed for determinism

        Returns:
            Search result in dictionary format compatible with existing code
        """
        result = self.kernel.search(budget=budget, seed=seed)

        return {
            "nonce": result.candidate,
            "phi_score": result.score,
            "partial": result.partial,
            "iterations_used": result.iterations_used,
            "budget_exhausted": result.budget_exhausted,
            "latency_mode": result.latency_mode.value,
            "search_time_ms": result.search_time_ms,
            "passport": result.passport,
        }

    def get_warm_cache_stats(self) -> dict[str, Any]:
        """Get warm cache statistics."""
        return {
            "size": self.cache.size(),
            "max_size": self.cache.max_size,
            "has_warm_state": self.cache.has_warm_state(self.domain.domain_id),
        }


class MiningCausalAdapter:
    """Adapter for integrating CausalAttributionEngine with Pythia mining.

    This adapter provides causal hotspot ranking and counterfactual
    coverage analysis for mining operations, enabling explainable
    mining decisions.
    """

    def __init__(
        self,
        mining_nodes: Mapping[str, Mapping[str, Any]],
        mining_edges: Mapping[str, list[str]],
        coverage_threshold: float = 1.0,
    ):
        """Initialize the mining causal adapter.

        Args:
            mining_nodes: Mining component nodes (solver, memory, etc.)
            mining_edges: Causal relationships between nodes
            coverage_threshold: Minimum coverage for high-confidence explanations
        """
        self.graph = MiningGraph(mining_nodes, mining_edges)
        self.engine = CausalAttributionEngine(
            self.graph,
            coverage_threshold=coverage_threshold,
        )

    def explain_nonce_discovery(
        self,
        nonce: int,
        phi_score: float,
        additional_context: Optional[Mapping[str, Any]] = None,
    ) -> dict[str, Any]:
        """Generate causal explanation for nonce discovery.

        Args:
            nonce: The discovered nonce
            phi_score: The φ-resonance score
            additional_context: Optional additional context

        Returns:
            Causal explanation in dictionary format
        """
        event = {
            "type": "nonce_found",
            "nonce": nonce,
            "phi_score": phi_score,
        }
        if additional_context:
            event.update(additional_context)

        claim = {
            "type": "valid_nonce",
            "nonce": nonce,
        }

        explanation = self.engine.explain(event, claim)

        return {
            "hotspots": [h.to_dict() for h in explanation.hotspots],
            "counterfactual": explanation.counterfactual.to_dict(),
            "explanation_quality": explanation.explanation_quality,
            "timestamp": explanation.timestamp,
        }

    def rank_mining_hotspots(
        self,
        event: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        """Rank mining components by causal impact.

        Args:
            event: Mining event to analyze

        Returns:
            List of hotspots sorted by impact score
        """
        hotspots = self.engine.rank_hotspots(event)
        return [h.to_dict() for h in hotspots]


class MiningPassportFactory:
    """Factory for creating mining-specific UniversalPassports.

    This factory provides convenience methods for creating passports
    for common mining operations, ensuring consistency with the
    UniversalPassport system.
    """

    @staticmethod
    def create_nonce_passport(
        nonce: int,
        job_id: str,
        pool_name: str,
        phi_score: float,
        bures_score: float,
        additional_metadata: Optional[Mapping[str, Any]] = None,
    ) -> UniversalPassport:
        """Create a passport for nonce discovery.

        Args:
            nonce: The discovered nonce
            job_id: Mining job identifier
            pool_name: Mining pool name
            phi_score: φ-resonance score
            bures_score: Bures distance score
            additional_metadata: Optional additional metadata

        Returns:
            UniversalPassport for nonce discovery
        """
        payload = {
            "nonce": nonce,
            "job_id": job_id,
            "pool_name": pool_name,
            "phi_score": phi_score,
            "bures_score": bures_score,
        }
        if additional_metadata:
            payload.update(additional_metadata)

        return make_mining_passport(
            nonce=nonce,
            job_id=job_id,
            pool_name=pool_name,
            phi_score=phi_score,
            bures_score=bures_score,
        )

    @staticmethod
    def create_share_passport(
        share_hash: str,
        job_id: str,
        difficulty: float,
        submitter: str,
    ) -> UniversalPassport:
        """Create a passport for share submission.

        Args:
            share_hash: Hash of the share
            job_id: Mining job identifier
            difficulty: Share difficulty
            submitter: Submitter identifier

        Returns:
            UniversalPassport for share submission
        """
        return make_passport(
            subsystem=Subsystem.PYTHIA.value,
            claim_type=ClaimType.SHARE_SUBMISSION.value,
            payload={
                "share_hash": share_hash,
                "job_id": job_id,
                "difficulty": difficulty,
                "submitter": submitter,
            },
            epistemic_bounds=[
                EpistemicBound.NO_QUANTUM_SPEEDUP.value,
                EpistemicBound.NO_GUARANTEE_CORRECTNESS.value,
            ],
        )

    @staticmethod
    def create_mining_result_passport(
        result_type: str,
        result_data: Mapping[str, Any],
        success: bool,
    ) -> UniversalPassport:
        """Create a passport for general mining results.

        Args:
            result_type: Type of mining result
            result_data: Result-specific data
            success: Whether the operation succeeded

        Returns:
            UniversalPassport for mining result
        """
        return make_passport(
            subsystem=Subsystem.PYTHIA.value,
            claim_type=ClaimType.MINING_RESULT.value,
            payload={
                "result_type": result_type,
                "result_data": dict(result_data),
                "success": success,
            },
            epistemic_bounds=[
                EpistemicBound.NO_QUANTUM_SPEEDUP.value,
                EpistemicBound.NO_GUARANTEE_CORRECTNESS.value,
            ],
        )


__all__ = [
    "SubstatePassportAdapter",
    "MiningSearchAdapter",
    "MiningCausalAdapter",
    "MiningPassportFactory",
]
