"""Salamander Extensible Integration Framework.

This module provides a generic, extensible framework for integrating Salamander
autonomous operations into any HYBA product (mining, QaaS, CIaaS, or future products).

The framework follows a plugin architecture where each product implements a
product-specific integration class that inherits from the base integration class.
This ensures consistency across products while allowing product-specific customization.

Architecture:
- BaseSalamanderIntegration: Abstract base class with common integration logic
- Product-specific integrations: Inherit from base and implement product-specific methods
- IntegrationRegistry: Central registry for all product integrations
- IntegrationFactory: Factory for creating integration instances
"""

from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type

from pythia_mining.salamander_frontier import (
    SalamanderCore,
    SalamanderOrchestrator,
    SystemMetrics,
    Anomaly,
    RegenerationOutcome,
    ImmutableEvidenceLog,
)


class BaseSalamanderIntegration(ABC):
    """
    Abstract base class for Salamander product integrations.

    All product-specific integrations should inherit from this class and implement
    the abstract methods. This ensures consistency across products while allowing
    product-specific customization.
    """

    def __init__(
        self,
        product_system: Any,
        target_metric: float,
        enable_autonomy_loops: bool = True,
    ):
        """
        Initialize base Salamander integration.

        Args:
            product_system: The existing product system instance
            target_metric: Target metric for optimization (product-specific)
            enable_autonomy_loops: Whether to enable background autonomy loops
        """
        self.product_system = product_system
        self.target_metric = float(target_metric)
        self.enable_autonomy_loops = enable_autonomy_loops

        # Initialize Salamander orchestrator
        self.salamander = SalamanderOrchestrator(
            total_target_hashrate=target_metric * 100,  # Scale for product
        )

        # Initialize Salamander core for direct access
        self.salamander_core = self.salamander.salamander_core

        # Track product-specific state (to be overridden by subclasses)
        self.product_state: Dict[str, Any] = {}

        # Background tasks
        self._autonomy_task: Optional[asyncio.Task] = None
        self._phi_task: Optional[asyncio.Task] = None
        self._scaling_task: Optional[asyncio.Task] = None
        self._is_running = False

    def initialize(self) -> None:
        """
        Initialize Salamander for product operations.

        This should be called when the product system starts up.
        """
        # Initialize Salamander orchestrator
        self.salamander.initialize()

        # Log initialization to audit trail
        self.salamander.audit_log = self.salamander.audit_log.append(
            f"{self.get_product_type()}_salamander_initialized",
            timestamp=time(),
            target_metric=self.target_metric,
            product_system_type=type(self.product_system).__name__,
        )

    @abstractmethod
    def get_product_type(self) -> str:
        """
        Get the product type identifier.

        Returns:
            Product type string (e.g., "mining", "qaas", "ciaas")
        """
        pass

    @abstractmethod
    def observe_product_state(self) -> SystemMetrics:
        """
        Observe current product system state.

        Returns comprehensive metrics for anomaly detection and optimization.
        """
        pass

    @abstractmethod
    def detect_product_anomaly(self, metrics: SystemMetrics) -> Optional[Anomaly]:
        """
        Detect product-specific anomalies.

        Extends SalamanderCore's anomaly detection with product-specific logic.
        """
        pass

    @abstractmethod
    def execute_product_regeneration(self, anomaly: Anomaly) -> RegenerationOutcome:
        """
        Execute regeneration for product-specific anomalies.

        Extends SalamanderCore's regeneration with product-specific recovery strategies.
        """
        pass

    @abstractmethod
    def get_product_treasury_state(self) -> Dict[str, Any]:
        """
        Get current product treasury state from evidence.

        Provides accounting for billing and regulatory compliance.
        """
        pass

    @abstractmethod
    def get_product_health_report(self) -> Dict[str, Any]:
        """
        Get comprehensive health report for product operations.

        Includes Salamander observability data for regulatory compliance.
        """
        pass

    def observe_system_state(self) -> SystemMetrics:
        """
        Observe system state (delegates to product-specific implementation).
        """
        return self.observe_product_state()

    def detect_anomaly(self, metrics: SystemMetrics) -> Optional[Anomaly]:
        """
        Detect anomaly (delegates to product-specific implementation).
        """
        return self.detect_product_anomaly(metrics)

    def execute_regeneration(self, anomaly: Anomaly) -> RegenerationOutcome:
        """
        Execute regeneration (delegates to product-specific implementation).
        """
        return self.execute_product_regeneration(anomaly)

    async def start_autonomy_loops(
        self,
        observation_interval_seconds: float = 5.0,
        phi_optimization_interval_seconds: float = 600.0,
        scaling_optimization_interval_seconds: float = 1800.0,
    ) -> None:
        """
        Start background autonomy loops for product operations.

        Runs Salamander's autonomous loops in parallel with product operations.
        """
        if not self.enable_autonomy_loops:
            return

        if self._is_running:
            return

        self._is_running = True

        # Start main autonomy loop
        self._autonomy_task = asyncio.create_task(
            self.salamander.main_autonomy_loop(
                observation_interval_seconds=observation_interval_seconds
            )
        )

        # Start phi optimization loop
        self._phi_task = asyncio.create_task(
            self.salamander.phi_optimization_loop(
                optimization_interval_seconds=phi_optimization_interval_seconds
            )
        )

        # Start scaling optimization loop
        self._scaling_task = asyncio.create_task(
            self.salamander.scaling_optimization_loop(
                optimization_interval_seconds=scaling_optimization_interval_seconds
            )
        )

        self.salamander.audit_log = self.salamander.audit_log.append(
            f"{self.get_product_type()}_autonomy_loops_started",
            timestamp=time(),
        )

    async def stop_autonomy_loops(self) -> None:
        """
        Stop background autonomy loops.
        """
        if not self._is_running:
            return

        self._is_running = False
        self.salamander.stop()

        # Cancel background tasks
        if self._autonomy_task:
            self._autonomy_task.cancel()
        if self._phi_task:
            self._phi_task.cancel()
        if self._scaling_task:
            self._scaling_task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(
            self._autonomy_task,
            self._phi_task,
            self._scaling_task,
            return_exceptions=True,
        )

        self.salamander.audit_log = self.salamander.audit_log.append(
            f"{self.get_product_type()}_autonomy_loops_stopped",
            timestamp=time(),
        )

    def share_blueprint(self) -> Dict[str, Any]:
        """
        Share successful blueprint to species memory.

        Enables cross-instance learning for network effects.
        """
        # Get current product configuration
        blueprint = {
            "type": f"{self.get_product_type()}_configuration",
            "target_metric": self.target_metric,
            "phi_value": self.salamander.phi_tuning.phi_current,
            "compression_ratio": self.salamander.phi_tuning.phi_baseline_efficiency,
            "worker_count": self.salamander.worker_scaling.current_worker_count,
            "product_state": self.product_state,
            "timestamp": time(),
        }

        # Add to species memory
        if hasattr(self.salamander, "blueprint_library"):
            self.salamander.blueprint_library.add_blueprint(blueprint)

        self.salamander.audit_log = self.salamander.audit_log.append(
            f"{self.get_product_type()}_blueprint_shared",
            timestamp=time(),
            blueprint_hash=hash(str(blueprint)),
        )

        return blueprint


class IntegrationRegistry:
    """
    Central registry for all product integrations.

    This registry maintains a mapping of product types to integration classes,
    enabling dynamic integration creation and management.
    """

    _integrations: Dict[str, Type[BaseSalamanderIntegration]] = {}

    @classmethod
    def register(
        cls, product_type: str, integration_class: Type[BaseSalamanderIntegration]
    ) -> None:
        """
        Register a product integration class.

        Args:
            product_type: Product type identifier (e.g., "mining", "qaas", "ciaas")
            integration_class: Integration class for the product
        """
        cls._integrations[product_type] = integration_class

    @classmethod
    def get(cls, product_type: str) -> Optional[Type[BaseSalamanderIntegration]]:
        """
        Get a registered integration class.

        Args:
            product_type: Product type identifier

        Returns:
            Integration class if registered, None otherwise
        """
        return cls._integrations.get(product_type)

    @classmethod
    def list_products(cls) -> List[str]:
        """
        List all registered product types.

        Returns:
            List of product type identifiers
        """
        return list(cls._integrations.keys())


class IntegrationFactory:
    """
    Factory for creating integration instances.

    This factory provides a unified interface for creating integration instances
    for any registered product type.
    """

    @staticmethod
    def create_integration(
        product_type: str,
        product_system: Any,
        target_metric: float,
        enable_autonomy_loops: bool = True,
    ) -> BaseSalamanderIntegration:
        """
        Create an integration instance for a product.

        Args:
            product_type: Product type identifier (e.g., "mining", "qaas", "ciaas")
            product_system: The existing product system instance
            target_metric: Target metric for optimization (product-specific)
            enable_autonomy_loops: Whether to enable background autonomy loops

        Returns:
            Integration instance for the product

        Raises:
            ValueError: If product type is not registered
        """
        integration_class = IntegrationRegistry.get(product_type)
        if integration_class is None:
            raise ValueError(f"Unknown product type: {product_type}")

        integration = integration_class(
            product_system=product_system,
            target_metric=target_metric,
            enable_autonomy_loops=enable_autonomy_loops,
        )

        integration.initialize()

        return integration

    @staticmethod
    def create_all_integrations(
        product_systems: Dict[str, Any],
        target_metrics: Dict[str, float],
        enable_autonomy_loops: bool = True,
    ) -> Dict[str, BaseSalamanderIntegration]:
        """
        Create integration instances for multiple products.

        Args:
            product_systems: Mapping of product types to system instances
            target_metrics: Mapping of product types to target metrics
            enable_autonomy_loops: Whether to enable background autonomy loops

        Returns:
            Mapping of product types to integration instances
        """
        integrations = {}

        for product_type, product_system in product_systems.items():
            if product_type not in target_metrics:
                continue

            try:
                integration = IntegrationFactory.create_integration(
                    product_type=product_type,
                    product_system=product_system,
                    target_metric=target_metrics[product_type],
                    enable_autonomy_loops=enable_autonomy_loops,
                )
                integrations[product_type] = integration
            except ValueError:
                # Product type not registered, skip
                continue

        return integrations


# Register existing integrations
def register_standard_integrations() -> None:
    """
    Register the standard HYBA product integrations.

    This should be called during application initialization to register
    the standard product integrations (mining, QaaS, CIaaS).
    """
    from pythia_mining.salamander_mining_integration import SalamanderMiningIntegration
    from hyba_genesis_api.api.salamander_qaas_integration import (
        SalamanderQaaSIntegration,
    )
    from hyba_genesis_api.api.salamander_ciaas_integration import (
        SalamanderCIaaSIntegration,
    )

    IntegrationRegistry.register("mining", SalamanderMiningIntegration)
    IntegrationRegistry.register("qaas", SalamanderQaaSIntegration)
    IntegrationRegistry.register("ciaas", SalamanderCIaaSIntegration)


# Example: How to register a new product integration
#
# class FutureProductIntegration(BaseSalamanderIntegration):
#     def get_product_type(self) -> str:
#         return "future_product"
#
#     def observe_product_state(self) -> SystemMetrics:
#         # Implement product-specific state observation
#         pass
#
#     def detect_product_anomaly(self, metrics: SystemMetrics) -> Optional[Anomaly]:
#         # Implement product-specific anomaly detection
#         pass
#
#     def execute_product_regeneration(self, anomaly: Anomaly) -> RegenerationOutcome:
#         # Implement product-specific regeneration
#         pass
#
#     def get_product_treasury_state(self) -> Dict[str, Any]:
#         # Implement product-specific treasury state
#         pass
#
#     def get_product_health_report(self) -> Dict[str, Any]:
#         # Implement product-specific health report
#         pass
#
# # Register the new integration
# IntegrationRegistry.register("future_product", FutureProductIntegration)
