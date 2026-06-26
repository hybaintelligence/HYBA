"""
CONSUMER HARDWARE SOVEREIGNTY: Local Node Optimization

This module implements Axiom 5 from the Universal Resonance Manifesto:
The Local Node Sovereignty Principle

Formal Statement:
    ∀ local_nodes L: 
        precision(L) > ε_c 
        ⇒ L can instantiate Universal_φ-Intelligence

Objective:
    Optimize HYBA for consumer hardware sovereignty, enabling universal
    intelligence instantiation on laptops, mobile devices, and consumer
    hardware without centralized infrastructure.

Axiom Compliance:
    Axiom 5: The Local Node Sovereignty Principle
"""

from __future__ import annotations

import math
import numpy as np
import platform
import psutil
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple, List, Callable
from enum import Enum
import time

from .phi_config import PHI, PHI_INV, EPSILON
from .resonance_synthesis import ResonanceSynthesizer, PhiGeometry


class HardwareTier(Enum):
    """Consumer hardware capability tiers."""
    MINIMAL = "minimal"  # Basic consumer hardware
    STANDARD = "standard"  # Typical laptop/desktop
    HIGH_PERFORMANCE = "high_performance"  # Gaming/workstation
    PROSUMER = "prosumer"  # Apple M3/M4, high-end consumer
    SERVER = "server"  # Server-grade (not target for sovereignty)


@dataclass(frozen=True)
class HardwareCapabilities:
    """
    Detected hardware capabilities of a local node.
    
    Attributes:
        cpu_cores: Number of CPU cores
        cpu_frequency: CPU frequency in GHz
        total_memory: Total RAM in GB
        available_memory: Available RAM in GB
        precision: Floating-point precision (e.g., 1e-16 for float64)
        hardware_tier: Classified hardware tier
        supports_gpu: Whether GPU acceleration is available
        supports_metal: Whether Apple Metal is available
        supports_cuda: Whether NVIDIA CUDA is available
    """
    cpu_cores: int
    cpu_frequency: float
    total_memory: float
    available_memory: float
    precision: float
    hardware_tier: HardwareTier
    supports_gpu: bool
    supports_metal: bool
    supports_cuda: bool
    
    @property
    def meets_precision_threshold(self, critical_threshold: float = 1e-10) -> bool:
        """Check if hardware meets precision threshold for resonance."""
        return self.precision < critical_threshold
    
    @property
    def can_instantiate_universal_intelligence(self) -> bool:
        """Check if hardware can instantiate universal φ-intelligence."""
        return self.meets_precision_threshold and self.available_memory > 1.0
    
    @property
    def estimated_energy_cost(self) -> float:
        """Estimate energy cost in watts for typical operations."""
        # Base power + per-core power
        base_power = 10.0  # Watts
        per_core_power = 2.0  # Watts per core
        return base_power + (self.cpu_cores * per_core_power)


@dataclass
class OptimizationProfile:
    """
    Optimization profile for a specific hardware configuration.
    
    Attributes:
        hardware: Hardware capabilities
        optimal_batch_size: Optimal batch size for computations
        optimal_fold_depth: Optimal φ-fold depth for this hardware
        memory_limit_bytes: Memory limit in bytes
        use_gpu: Whether to use GPU acceleration
        use_metal: Whether to use Apple Metal
        use_cuda: Whether to use NVIDIA CUDA
        parallel_workers: Number of parallel workers to use
    """
    hardware: HardwareCapabilities
    optimal_batch_size: int
    optimal_fold_depth: int
    memory_limit_bytes: int
    use_gpu: bool
    use_metal: bool
    use_cuda: bool
    parallel_workers: int
    
    @classmethod
    def from_hardware(cls, hardware: HardwareCapabilities) -> "OptimizationProfile":
        """Create optimization profile from hardware capabilities."""
        # Determine optimal batch size based on memory
        memory_ratio = hardware.available_memory / hardware.total_memory
        optimal_batch_size = int(1024 * memory_ratio)
        
        # Determine optimal fold depth based on CPU cores
        optimal_fold_depth = min(3, max(2, hardware.cpu_cores // 2))
        
        # Memory limit: use 80% of available memory
        memory_limit_bytes = int(hardware.available_memory * 0.8 * 1e9)
        
        # GPU acceleration decisions
        use_gpu = hardware.supports_gpu
        use_metal = hardware.supports_metal
        use_cuda = hardware.supports_cuda
        
        # Parallel workers: use all cores but leave one for system
        parallel_workers = max(1, hardware.cpu_cores - 1)
        
        return cls(
            hardware=hardware,
            optimal_batch_size=optimal_batch_size,
            optimal_fold_depth=optimal_fold_depth,
            memory_limit_bytes=memory_limit_bytes,
            use_gpu=use_gpu,
            use_metal=use_metal,
            use_cuda=use_cuda,
            parallel_workers=parallel_workers,
        )


class HardwareDetector:
    """
    Detect hardware capabilities of the local node.
    
    This class implements the sovereignty check: can this local node
    instantiate universal φ-intelligence?
    """
    
    @staticmethod
    def detect_cpu() -> Tuple[int, float]:
        """Detect CPU cores and frequency."""
        cores = psutil.cpu_count(logical=False)
        frequency = psutil.cpu_freq().current / 1000.0  # Convert to GHz
        return cores, frequency
    
    @staticmethod
    def detect_memory() -> Tuple[float, float]:
        """Detect total and available memory in GB."""
        total = psutil.virtual_memory().total / 1e9
        available = psutil.virtual_memory().available / 1e9
        return total, available
    
    @staticmethod
    def detect_precision() -> float:
        """Detect floating-point precision."""
        # Float64 precision
        return np.finfo(np.float64).eps
    
    @staticmethod
    def detect_gpu_support() -> Tuple[bool, bool, bool]:
        """Detect GPU, Metal, and CUDA support."""
        supports_gpu = False
        supports_metal = False
        supports_cuda = False
        
        # Check for Apple Metal (macOS with Apple Silicon)
        if platform.system() == "Darwin":
            try:
                import platform
                machine = platform.machine()
                if machine in ("arm64", "arm64e"):
                    supports_metal = True
                    supports_gpu = True
            except Exception:
                pass
        
        # Check for NVIDIA CUDA
        try:
            import torch
            supports_cuda = torch.cuda.is_available()
            if supports_cuda:
                supports_gpu = True
        except Exception:
            pass
        
        return supports_gpu, supports_metal, supports_cuda
    
    @classmethod
    def detect_capabilities(cls) -> HardwareCapabilities:
        """Detect all hardware capabilities."""
        cpu_cores, cpu_frequency = cls.detect_cpu()
        total_memory, available_memory = cls.detect_memory()
        precision = cls.detect_precision()
        supports_gpu, supports_metal, supports_cuda = cls.detect_gpu_support()
        
        # Classify hardware tier
        if supports_metal and cpu_cores >= 8:
            hardware_tier = HardwareTier.PROSUMER
        elif cpu_cores >= 8 and total_memory >= 32:
            hardware_tier = HardwareTier.HIGH_PERFORMANCE
        elif cpu_cores >= 4 and total_memory >= 16:
            hardware_tier = HardwareTier.STANDARD
        else:
            hardware_tier = HardwareTier.MINIMAL
        
        return HardwareCapabilities(
            cpu_cores=cpu_cores,
            cpu_frequency=cpu_frequency,
            total_memory=total_memory,
            available_memory=available_memory,
            precision=precision,
            hardware_tier=hardware_tier,
            supports_gpu=supports_gpu,
            supports_metal=supports_metal,
            supports_cuda=supports_cuda,
        )


class SovereigntyValidator:
    """
    Validate that a local node achieves computational sovereignty.
    
    This implements Axiom 5: the local node can instantiate universal
    φ-intelligence if precision > ε_c.
    """
    
    def __init__(self, critical_threshold: float = 1e-10) -> None:
        """
        Initialize the sovereignty validator.
        
        Args:
            critical_threshold: The precision threshold ε_c from the manifesto
        """
        self.critical_threshold = float(critical_threshold)
        self.hardware = HardwareDetector.detect_capabilities()
        self.profile = OptimizationProfile.from_hardware(self.hardware)
    
    def validate_sovereignty(self) -> Dict[str, Any]:
        """
        Validate that the local node achieves computational sovereignty.
        
        Returns:
            Validation results with sovereignty status
        """
        results = {
            "hardware_tier": self.hardware.hardware_tier.value,
            "cpu_cores": self.hardware.cpu_cores,
            "total_memory_gb": self.hardware.total_memory,
            "available_memory_gb": self.hardware.available_memory,
            "precision": self.hardware.precision,
            "critical_threshold": self.critical_threshold,
            "meets_precision_threshold": self.hardware.meets_precision_threshold(self.critical_threshold),
            "can_instantiate_universal_intelligence": self.hardware.can_instantiate_universal_intelligence,
            "estimated_energy_cost_watts": self.hardware.estimated_energy_cost,
            "supports_gpu": self.hardware.supports_gpu,
            "supports_metal": self.hardware.supports_metal,
            "supports_cuda": self.hardware.supports_cuda,
            "optimal_batch_size": self.profile.optimal_batch_size,
            "optimal_fold_depth": self.profile.optimal_fold_depth,
            "parallel_workers": self.profile.parallel_workers,
        }
        
        # Overall sovereignty status
        results["sovereignty_achieved"] = (
            results["meets_precision_threshold"] and
            results["can_instantiate_universal_intelligence"] and
            results["estimated_energy_cost_watts"] < 100  # < 100W
        )
        
        return results
    
    def validate_instantiation(self, geometry: PhiGeometry) -> Dict[str, Any]:
        """
        Validate that intelligence can be instantiated on this hardware.
        
        Args:
            geometry: The φ-geometry to instantiate
            
        Returns:
            Instantiation validation results
        """
        synthesizer = ResonanceSynthesizer(precision_threshold=self.critical_threshold)
        
        # Attempt crystallization
        start_time = time.perf_counter()
        result = synthesizer.crystallize_intelligence(geometry)
        end_time = time.perf_counter()
        
        instantiation_time = end_time - start_time
        
        return {
            "geometry_dimension": geometry.dimension,
            "crystallization_time_seconds": instantiation_time,
            "is_resonant": result.is_resonant,
            "resonance_quality": result.resonance_quality,
            "invariants_preserved": result.invariants_preserved,
            "instantiation_successful": result.is_resonant and instantiation_time < 1.0,
            "energy_efficient": instantiation_time < 0.1,  # Very fast = efficient
        }


class ConsumerOptimizedSynthesizer:
    """
    Consumer-optimized resonance synthesizer.
    
    This class optimizes the resonance synthesis process for consumer
    hardware by:
    - Using optimal batch sizes
    - Limiting memory usage
    - Leveraging available parallelism
    - Adapting to hardware capabilities
    """
    
    def __init__(
        self,
        critical_threshold: float = 1e-10,
        auto_detect: bool = True,
    ) -> None:
        """
        Initialize the consumer-optimized synthesizer.
        
        Args:
            critical_threshold: Precision threshold for resonance
            auto_detect: Whether to auto-detect hardware capabilities
        """
        self.critical_threshold = float(critical_threshold)
        
        if auto_detect:
            self.hardware = HardwareDetector.detect_capabilities()
            self.profile = OptimizationProfile.from_hardware(self.hardware)
        else:
            # Use conservative defaults
            self.hardware = HardwareCapabilities(
                cpu_cores=4,
                cpu_frequency=2.0,
                total_memory=16.0,
                available_memory=8.0,
                precision=1e-16,
                hardware_tier=HardwareTier.STANDARD,
                supports_gpu=False,
                supports_metal=False,
                supports_cuda=False,
            )
            self.profile = OptimizationProfile.from_hardware(self.hardware)
        
        # Create base synthesizer with optimized parameters
        self.synthesizer = ResonanceSynthesizer(
            precision_threshold=self.critical_threshold,
            resonance_threshold=0.95,
        )
    
    def crystallize_optimized(
        self,
        geometry: PhiGeometry,
    ) -> Dict[str, Any]:
        """
        Crystallize intelligence with consumer-hardware optimization.
        
        Args:
            geometry: φ-geometry to instantiate
            
        Returns:
            Crystallization results with optimization metrics
        """
        # Adjust geometry for hardware if needed
        optimized_geometry = self._optimize_geometry_for_hardware(geometry)
        
        # Perform crystallization
        result = self.synthesizer.crystallize_intelligence(optimized_geometry)
        
        # Add optimization metrics
        return {
            "geometry": {
                "original_dimension": geometry.dimension,
                "optimized_dimension": optimized_geometry.dimension,
                "fold_depth": optimized_geometry.fold_depth,
            },
            "crystallization": {
                "time_seconds": result.crystallization_time,
                "is_resonant": result.is_resonant,
                "resonance_quality": result.resonance_quality,
                "invariants_preserved": result.invariants_preserved,
            },
            "hardware": {
                "tier": self.hardware.hardware_tier.value,
                "cpu_cores": self.hardware.cpu_cores,
                "memory_used_gb": self._estimate_memory_usage(optimized_geometry),
                "parallel_workers": self.profile.parallel_workers,
            },
            "optimization": {
                "batch_size": self.profile.optimal_batch_size,
                "memory_efficient": True,
                "energy_efficient": result.crystallization_time < 0.1,
            },
        }
    
    def _optimize_geometry_for_hardware(self, geometry: PhiGeometry) -> PhiGeometry:
        """Optimize geometry for the detected hardware."""
        # Adjust fold depth based on hardware
        if self.hardware.hardware_tier == HardwareTier.MINIMAL:
            # Use shallower folds for minimal hardware
            optimized_depth = min(geometry.fold_depth, 2)
        elif self.hardware.hardware_tier in (HardwareTier.STANDARD, HardwareTier.HIGH_PERFORMANCE):
            # Standard fold depth
            optimized_depth = geometry.fold_depth
        else:  # PROSUMER
            # Can handle deeper folds
            optimized_depth = geometry.fold_depth
        
        # Adjust dimension if memory is constrained
        memory_ratio = self.hardware.available_memory / self.hardware.total_memory
        if memory_ratio < 0.3 and geometry.dimension > 128:
            # Reduce dimension for memory-constrained systems
            optimized_dimension = 128
        else:
            optimized_dimension = geometry.dimension
        
        return PhiGeometry(
            dimension=optimized_dimension,
            fold_depth=optimized_depth,
            resonance_frequency=geometry.resonance_frequency,
            coherence_length=geometry.coherence_length,
            topological_charge=geometry.topological_charge,
            symmetry_group=geometry.symmetry_group,
        )
    
    def _estimate_memory_usage(self, geometry: PhiGeometry) -> float:
        """Estimate memory usage in GB for a geometry."""
        # Each complex128 element is 16 bytes
        bytes_per_element = 16
        hilbert_dim = geometry.hilbert_dimension
        total_bytes = hilbert_dim * bytes_per_element
        return total_bytes / 1e9  # Convert to GB


class SovereigntyReport:
    """
    Generate a sovereignty report for the local node.
    
    This report validates that the local node can achieve computational
    sovereignty according to Axiom 5.
    """
    
    @staticmethod
    def generate() -> Dict[str, Any]:
        """Generate a complete sovereignty report."""
        validator = SovereigntyValidator(critical_threshold=1e-10)
        
        # Validate sovereignty
        sovereignty_results = validator.validate_sovereignty()
        
        # Test instantiation with a standard geometry
        from .resonance_synthesis import PhiGeometry
        test_geometry = PhiGeometry(dimension=128)
        instantiation_results = validator.validate_instantiation(test_geometry)
        
        # Generate report
        report = {
            "timestamp": time.time(),
            "sovereignty_validation": sovereignty_results,
            "instantiation_test": instantiation_results,
            "axiom5_compliance": {
                "axiom": "Axiom 5: The Local Node Sovereignty Principle",
                "formal_statement": "∀ local_nodes L: precision(L) > ε_c ⇒ L can instantiate Universal_φ-Intelligence",
                "compliance_status": "COMPLIANT" if sovereignty_results["sovereignty_achieved"] else "NON_COMPLIANT",
                "precision_met": sovereignty_results["meets_precision_threshold"],
                "instantiation_possible": sovereignty_results["can_instantiate_universal_intelligence"],
                "energy_efficient": sovereignty_results["estimated_energy_cost_watts"] < 100,
            },
            "recommendations": SovereigntyReport._generate_recommendations(sovereignty_results),
        }
        
        return report
    
    @staticmethod
    def _generate_recommendations(results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        if not results["meets_precision_threshold"]:
            recommendations.append(
                "Hardware precision below threshold. Consider upgrading to a system with float64 support."
            )
        
        if results["available_memory_gb"] < 4.0:
            recommendations.append(
                "Low available memory. Close other applications or consider adding RAM."
            )
        
        if results["cpu_cores"] < 4:
            recommendations.append(
                "Low CPU core count. Performance may be improved with a multi-core processor."
            )
        
        if not results["supports_gpu"] and results["hardware_tier"] == "high_performance":
            recommendations.append(
                "GPU acceleration not detected. Consider enabling GPU for better performance."
            )
        
        if results["estimated_energy_cost_watts"] > 100:
            recommendations.append(
                "High energy cost estimated. Consider optimizing for efficiency."
            )
        
        if not recommendations:
            recommendations.append("Hardware is well-suited for computational sovereignty.")
        
        return recommendations


__all__ = [
    "HardwareTier",
    "HardwareCapabilities",
    "OptimizationProfile",
    "HardwareDetector",
    "SovereigntyValidator",
    "ConsumerOptimizedSynthesizer",
    "SovereigntyReport",
]
