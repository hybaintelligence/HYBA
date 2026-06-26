"""Agentic-Mining Integration — Unified HYBA Intelligence Layer.

This module wires the agentic intelligence layer into the PYTHIA mining engine,
providing:

1. Token-optimized mining contexts via shared PULVINI core
2. Evidence sealing for all autonomous mining decisions
3. Golden-ratio hardware scaling integration
4. Mining-specific agent execution via agentic marketplace
5. Cross-system metrics aggregation

The integration is fail-closed: if any agentic component is unavailable,
mining falls back to native behavior without breaking the mining loop.

REFLEXIVE KNOWLEDGE LOOP:
This module is called from phi_unified_mining_engine.search() and
autonomous_mining_controller.seek_improvement() to augment mining
decisions with agentic capabilities.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AgenticMiningIntegration:
    """Bridge between agentic intelligence and mining subsystems."""

    def __init__(
        self,
        pulvini_core: Any = None,
        token_optimizer: Any = None,
        gpu_coordinator: Any = None,
        golden_scaler: Any = None,
        mining_evidence_seal: Any = None,
    ) -> None:
        # Lazy imports to avoid circular dependencies
        if pulvini_core is None:
            try:
                from pythia_shared.pulvini_core import PulviniCore

                pulvini_core = PulviniCore()
            except Exception as exc:
                logger.warning("Failed to import shared PULVINI core: %s", exc)
                pulvini_core = None

        if token_optimizer is None:
            try:
                from hyba_genesis_api.api.agentic_intelligence_service.service import (
                    TokenOptimizationEngine,
                )

                token_optimizer = TokenOptimizationEngine(
                    pulvini_engine=pulvini_core
                )
            except Exception as exc:
                logger.warning("Failed to import agentic token optimizer: %s", exc)
                token_optimizer = None

        if gpu_coordinator is None:
            try:
                from hyba_genesis_api.api.agentic_intelligence_service.service import (
                    GPUScalingCoordinator,
                )

                gpu_coordinator = GPUScalingCoordinator(max_gpus=4)
            except Exception as exc:
                logger.warning("Failed to import agentic GPU coordinator: %s", exc)
                gpu_coordinator = None

        if golden_scaler is None:
            try:
                from pythia_mining.golden_ratio_scaler import GoldenRatioScaler

                golden_scaler = GoldenRatioScaler(base=1)
            except Exception as exc:
                logger.warning("Failed to import golden ratio scaler: %s", exc)
                golden_scaler = None

        if mining_evidence_seal is None:
            try:
                from pythia_mining.mining_evidence_seal import (
                    create_mining_evidence_seal,
                )

                mining_evidence_seal = create_mining_evidence_seal
            except Exception as exc:
                logger.warning("Failed to import mining evidence seal: %s", exc)
                mining_evidence_seal = None

        self.pulvini_core = pulvini_core
        self.token_optimizer = token_optimizer
        self.gpu_coordinator = gpu_coordinator
        self.golden_scaler = golden_scaler
        self.mining_evidence_seal = mining_evidence_seal

    # ------------------------------------------------------------------
    # Token optimization for mining contexts
    # ------------------------------------------------------------------

    def optimize_mining_context(
        self,
        context: str,
        *,
        enable_pulvini: bool = True,
    ) -> Dict[str, Any]:
        """Optimize a mining context string (job description, strategy config) for token efficiency.

        Returns optimization result with original/optimized token counts.
        """
        if self.token_optimizer is None:
            return {
                "optimized_prompt": context,
                "original_tokens": len(context) // 4,
                "optimized_tokens": len(context) // 4,
                "tokens_saved": 0,
                "compression_ratio": 1.0,
                "strategy": "none",
            }

        try:
            from hyba_genesis_api.api.agentic_intelligence_service.service import (
                TokenOptimizationConfig,
            )

            config = TokenOptimizationConfig(
                enable_compression=True,
                target_reduction_ratio=0.85,
                use_pulvini=enable_pulvini and (self.pulvini_core is not None),
                preserve_semantic_integrity=True,
            )
            return self.token_optimizer.optimize_prompt(context, config)
        except Exception as exc:
            logger.warning("Token optimization failed: %s", exc)
            return {
                "optimized_prompt": context,
                "original_tokens": len(context) // 4,
                "optimized_tokens": len(context) // 4,
                "tokens_saved": 0,
                "compression_ratio": 1.0,
                "strategy": "fallback",
            }

    # ------------------------------------------------------------------
    # Evidence sealing for mining events
    # ------------------------------------------------------------------

    def seal_mining_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Create a cryptographic evidence seal for a mining event."""
        if self.mining_evidence_seal is None:
            return None
        try:
            return self.mining_evidence_seal(event_type, payload)
        except Exception as exc:
            logger.warning("Mining evidence seal failed: %s", exc)
            return None

    def seal_autonomous_decision(self, decision: Any) -> Optional[Dict[str, Any]]:
        """Seal an AutonomousDecision."""
        try:
            from pythia_mining.mining_evidence_seal import seal_autonomous_decision

            return seal_autonomous_decision(decision)
        except Exception as exc:
            logger.warning("Decision seal failed: %s", exc)
            return None

    def seal_reflexive_proposal(self, proposal: Any) -> Optional[Dict[str, Any]]:
        """Seal a SelfOptimizationProposal."""
        try:
            from pythia_mining.mining_evidence_seal import seal_reflexive_proposal

            return seal_reflexive_proposal(proposal)
        except Exception as exc:
            logger.warning("Proposal seal failed: %s", exc)
            return None

    def seal_scaling_plan(self, plan: Any) -> Optional[Dict[str, Any]]:
        """Seal a ScalingPlan."""
        try:
            from pythia_mining.mining_evidence_seal import seal_scaling_plan

            return seal_scaling_plan(plan)
        except Exception as exc:
            logger.warning("Scaling plan seal failed: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Golden-ratio hardware scaling
    # ------------------------------------------------------------------

    def propose_hardware_scaling(
        self,
        current: Dict[str, int],
        coherence: float,
        phi_density: float,
        dimensions: Optional[List[str]] = None,
    ) -> Optional[Any]:
        """Generate a φ-scaled hardware scaling plan.

        Args:
            current: Current hardware values (gpus, batch_size, memory_mb, search_depth)
            coherence: Current φ-coherence (0-1)
            phi_density: Current φ-density
            dimensions: Which dimensions to include (default: all)

        Returns:
            ScalingPlan with proposals and evidence seal, or None on failure
        """
        if self.golden_scaler is None:
            return None

        try:
            if dimensions is None:
                dimensions = ["gpus", "batch_size", "memory_mb", "search_depth"]

            plan = self.golden_scaler.propose_scaling_plan(
                dimensions=dimensions,
                current=current,
                target_coherence=coherence,
                phi_density=phi_density,
            )

            # Attach evidence seal via shared core if available
            if self.pulvini_core is not None and plan.evidence_seal is None:
                try:
                    plan.evidence_seal = self.pulvini_core.seal(
                        {
                            "type": "scaling_plan",
                            "coherence_factor": round(coherence, 6),
                            "phi_density": round(phi_density, 6),
                            "timestamp": plan.timestamp,
                            "proposals": [
                                {
                                    "dimension": p.dimension,
                                    "from": p.current_value,
                                    "to": p.proposed_value,
                                }
                                for p in plan.proposals
                            ],
                        }
                    )
                except Exception:
                    pass

            return plan
        except Exception as exc:
            logger.warning("Hardware scaling proposal failed: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Shared metrics
    # ------------------------------------------------------------------

    def get_aggregate_metrics(self) -> Dict[str, Any]:
        """Combine metrics from all integrated subsystems."""
        metrics: Dict[str, Any] = {
            "pulvini_core": None,
            "token_optimizer": None,
            "gpu_coordinator": None,
            "golden_scaler": None,
        }

        if self.pulvini_core is not None:
            try:
                metrics["pulvini_core"] = self.pulvini_core.get_metrics()
            except Exception as exc:
                logger.debug("PULVINI metrics unavailable: %s", exc)

        if self.token_optimizer is not None:
            try:
                metrics["token_optimizer"] = self.token_optimizer.get_optimization_stats()
            except Exception as exc:
                logger.debug("Token optimizer metrics unavailable: %s", exc)

        if self.gpu_coordinator is not None:
            try:
                metrics["gpu_coordinator"] = self.gpu_coordinator.get_gpu_utilization()
            except Exception as exc:
                logger.debug("GPU coordinator metrics unavailable: %s", exc)

        if self.golden_scaler is not None:
            try:
                metrics["golden_scaler"] = self.golden_scaler.to_dict()
            except Exception as exc:
                logger.debug("Golden scaler metrics unavailable: %s", exc)

        return metrics