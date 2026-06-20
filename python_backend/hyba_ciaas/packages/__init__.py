"""
HYBA CIaaS Optimization Packages
Pre-built domain-specific optimization solutions
"""

from .government_security_package import GovernmentSecurityPackage
from .energy_optimization_package import EnergyOptimizationPackage
from .protein_folding_package import ProteinFoldingPackage

__all__ = [
    'GovernmentSecurityPackage',
    'EnergyOptimizationPackage',
    'ProteinFoldingPackage',
]


class PackageFactory:
    """Factory for creating optimization packages"""
    
    PACKAGES = {
        'government': GovernmentSecurityPackage,
        'energy': EnergyOptimizationPackage,
        'protein': ProteinFoldingPackage,
    }
    
    @classmethod
    def create(cls, package_name: str, config=None):
        """Create optimization package by name"""
        if package_name not in cls.PACKAGES:
            raise ValueError(f"Unknown package: {package_name}")
        
        return cls.PACKAGES[package_name](config)
    
    @classmethod
    def list_packages(cls):
        """List available packages"""
        return list(cls.PACKAGES.keys())
