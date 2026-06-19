"""GenesisAI Service Registry for API Integration."""

from typing import Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .genesis_ai import GenesisAI
    from .ai_optimizer import AIOptimizer


class GenesisAIServiceRegistry:
    """Singleton registry for GenesisAI instance to enable API integration."""

    _instance: Optional["GenesisAIServiceRegistry"] = None
    _genesis_ai: Optional["GenesisAI"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register_instance(cls, genesis_ai: "GenesisAI") -> None:
        """Register the GenesisAI instance for API access."""
        cls._genesis_ai = genesis_ai

    @classmethod
    def get_instance(cls) -> Optional["GenesisAI"]:
        """Get the registered GenesisAI instance."""
        return cls._genesis_ai

    @classmethod
    def is_registered(cls) -> bool:
        """Check if a GenesisAI instance is registered."""
        return cls._genesis_ai is not None

    @classmethod
    def get_ai_optimizer(cls) -> Optional["AIOptimizer"]:
        """Get the AI optimizer instance from GenesisAI."""
        if cls._genesis_ai is None:
            return None
        return getattr(cls._genesis_ai, "ai_optimizer", None)

    @classmethod
    def get_consciousness_metrics(cls) -> Dict[str, Any]:
        """Get live consciousness metrics from GenesisAI."""
        if cls._genesis_ai is None:
            return {"status": "not_available", "error": "GenesisAI instance not registered"}

        try:
            return cls._genesis_ai.latest_phi_optimization or {
                "status": "no_data",
                "message": "No phi optimization data available yet",
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    @classmethod
    def get_performance_metrics(cls) -> Dict[str, Any]:
        """Get performance metrics from GenesisAI."""
        if cls._genesis_ai is None:
            return {"status": "not_available", "error": "GenesisAI instance not registered"}

        try:
            return cls._genesis_ai.get_performance_metrics()
        except Exception as e:
            return {"status": "error", "error": str(e)}

    @classmethod
    def get_health_status(cls) -> Dict[str, Any]:
        """Get health status from GenesisAI."""
        if cls._genesis_ai is None:
            return {"status": "not_available", "error": "GenesisAI instance not registered"}

        try:
            return cls._genesis_ai.get_health_status()
        except Exception as e:
            return {"status": "error", "error": str(e)}

    @classmethod
    def get_iit_performance(cls) -> Dict[str, Any]:
        """Get IIT 4.0 performance metrics."""
        if cls._genesis_ai is None:
            return {"status": "not_available", "error": "GenesisAI instance not registered"}

        try:
            return cls._genesis_ai.iit_analyzer.get_performance_metrics()
        except Exception as e:
            return {"status": "error", "error": str(e)}

    @classmethod
    def get_penrose_metrics(cls) -> Dict[str, Any]:
        """Get Penrose OR consciousness metrics."""
        if cls._genesis_ai is None:
            return {"status": "not_available", "error": "GenesisAI instance not registered"}

        try:
            return cls._genesis_ai.penrose_or.get_consciousness_metrics()
        except Exception as e:
            return {"status": "error", "error": str(e)}

    @classmethod
    def get_knowledge_metrics(cls) -> Dict[str, Any]:
        """Get Deutsch knowledge substrate metrics."""
        if cls._genesis_ai is None:
            return {"status": "not_available", "error": "GenesisAI instance not registered"}

        try:
            return cls._genesis_ai.knowledge_substrate.get_knowledge_metrics()
        except Exception as e:
            return {"status": "error", "error": str(e)}


__all__ = ["GenesisAIServiceRegistry"]
