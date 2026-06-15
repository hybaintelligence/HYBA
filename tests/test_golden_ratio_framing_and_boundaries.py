"""
Golden Ratio Framing and Boundary Tests
========================================

This test suite verifies that φ implementation maintains proper claim boundaries
and avoids framing drift. The golden ratio is implemented as a deterministic
scaling invariant for structured traversal, memory folding, and ensemble weighting,
not as a cryptographic shortcut or guaranteed performance booster.

Key Principles:
1. φ guides structured traversal and scaling; SHA-256/pool acceptance proves truth
2. Projection-only benchmarking when measured hashrate is absent
3. No fabrication of live telemetry in production paths
4. Clear separation between mathematical invariants and performance claims
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# ── Ensure we can import from python_backend ──────────────────────────────
ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from pythia_mining import golden_ratio_library
from pythia_mining.phi_config import PHI as PHI_CONFIG
from pythia_mining.phi_scaling_engine import PHI as PHI_SCALING_ENGINE
from pythia_mining.phi_scaling_engine import benchmark_vs_asic


class TestGoldenRatioConstantConsistency:
    """Verify φ constants are consistent across the codebase."""
    
    def test_phi_constants_match(self) -> None:
        """PHI constant should be consistent across all modules."""
        assert abs(golden_ratio_library.PHI - PHI_CONFIG) < 1e-15
        assert abs(PHI_SCALING_ENGINE - PHI_CONFIG) < 1e-15
        assert abs(golden_ratio_library.PHI - PHI_SCALING_ENGINE) < 1e-15
    
    def test_phi_inverse_constants_match(self) -> None:
        """PHI_INV constant should be consistent across all modules."""
        assert abs(golden_ratio_library.PHI_INV - 1.0/PHI_CONFIG) < 1e-15
        assert abs(1.0/PHI_CONFIG - golden_ratio_library.PHI_INV) < 1e-15


class TestProjectionOnlyBoundary:
    """Verify projection-only mode protects against measurement fabrication."""
    
    def test_benchmark_without_measured_returns_projection_only(self) -> None:
        """When measured_hashes_per_second is None, benchmark must be projection_only."""
        result = benchmark_vs_asic(measured_hashes_per_second=None)
        assert result["benchmark_mode"] == "projection_only"
        assert result["measured_hashes_per_second"] is None
        assert result["projected_vs_asic_ratio"] is None
    
    def test_benchmark_with_measured_returns_measured_input(self) -> None:
        """When measured_hashes_per_second is provided, benchmark must be measured_input."""
        result = benchmark_vs_asic(measured_hashes_per_second=110e12)
        assert result["benchmark_mode"] == "measured_input"
        assert result["measured_hashes_per_second"] == 110e12
        assert result["projected_vs_asic_ratio"] is not None
    
    def test_projection_only_cannot_report_measured_outperformance(self) -> None:
        """Projection-only mode cannot claim measured ASIC outperformance."""
        result = benchmark_vs_asic(measured_hashes_per_second=None)
        # In projection-only mode, effective_hashes_per_second should be None
        # or clearly marked as projection
        assert result["effective_hashes_per_second"] is None
        assert result["benchmark_mode"] == "projection_only"
    
    def test_measured_benchmark_requires_positive_input(self) -> None:
        """Measured benchmark mode requires positive measured input."""
        with pytest.raises(ValueError, match="asic_baseline_hashes_per_second must be positive"):
            benchmark_vs_asic(measured_hashes_per_second=1.0, asic_baseline_hashes_per_second=0)


class TestGoldenRatioPrimitivesArePureMath:
    """Verify φ primitives are deterministic mathematical functions."""
    
    def test_golden_ratio_library_functions_are_deterministic(self) -> None:
        """All golden_ratio_library functions should be deterministic."""
        # Test inverse_phi_distribution
        dist_10_a = golden_ratio_library.inverse_phi_distribution(10)
        dist_10_b = golden_ratio_library.inverse_phi_distribution(10)
        assert dist_10_a == dist_10_b
        
        # Test lucas_ratio_tail
        lucas_tail_5_a = golden_ratio_library.lucas_ratio_tail(5)
        lucas_tail_5_b = golden_ratio_library.lucas_ratio_tail(5)
        assert lucas_tail_5_a == lucas_tail_5_b
        
        # Test normalize
        values = [1.0, 2.0, 3.0, 4.0]
        norm_a = golden_ratio_library.normalize(values)
        norm_b = golden_ratio_library.normalize(values)
        assert norm_a == norm_b
    
    def test_no_side_effects_in_golden_ratio_primitives(self) -> None:
        """Golden ratio primitives should not have side effects."""
        import hashlib
        
        # Capture initial state
        initial_hash = hashlib.md5(str(golden_ratio_library.__dict__).encode()).hexdigest()
        
        # Call various functions
        golden_ratio_library.inverse_phi_distribution(20)
        golden_ratio_library.lucas_ratio_tail(5)
        golden_ratio_library.normalize([1.0, 2.0, 3.0, 4.0, 5.0])
        golden_ratio_library.canonical_json({"test": "data"})
        golden_ratio_library.canonical_sha256({"test": "data"})
        
        # Verify no side effects
        final_hash = hashlib.md5(str(golden_ratio_library.__dict__).encode()).hexdigest()
        assert initial_hash == final_hash, "Golden ratio primitives have side effects"


class TestFramingLanguageBoundaries:
    """Verify implementation avoids overclaiming φ capabilities."""
    
    def test_implementation_does_not_claim_sha256_breakthrough(self) -> None:
        """Code should not contain language claiming SHA-256 breakthroughs."""
        # Check golden_ratio_library
        lib_source = Path(__file__).parent.parent / "python_backend" / "pythia_mining" / "golden_ratio_library.py"
        lib_text = lib_source.read_text().lower()
        
        forbidden_sha256_phrases = [
            "break sha-256",
            "crack sha256",
            "sha256 acceleration",
            "quantum speedup sha256",
            "faster than sha256",
            "bypass sha256",
        ]
        
        for phrase in forbidden_sha256_phrases:
            assert phrase not in lib_text, f"Golden ratio library contains forbidden phrase: {phrase}"
    
    def test_implementation_does_not_claim_asic_supremacy_without_evidence(self) -> None:
        """Code should not claim ASIC supremacy without evidence qualifiers."""
        # Check phi_scaling_engine
        engine_source = Path(__file__).parent.parent / "python_backend" / "pythia_mining" / "phi_scaling_engine.py"
        engine_text = engine_source.read_text()
        
        # Look for projection qualifiers
        assert "projection_only" in engine_text
        assert "measured_input" in engine_text
        assert "benchmark_mode" in engine_text
    
    def test_performance_language_requires_evidence_qualifiers(self) -> None:
        """Performance claims must include evidence requirements."""
        engine_source = Path(__file__).parent.parent / "python_backend" / "pythia_mining" / "phi_scaling_engine.py"
        engine_text = engine_source.read_text()
        
        # Check that performance functions have proper documentation
        assert "measured_hashes_per_second" in engine_text
        # Check for evidence qualifiers in the docstring
        assert "measured" in engine_text.lower() or "telemetry" in engine_text.lower()
        assert "projection" in engine_text.lower() or "projected" in engine_text.lower()


class TestHendrixPhiSolverCorrectImport:
    """Verify HENDRIX-Φ solver imports canonical primitives."""
    
    def test_hendrix_phi_solver_imports_golden_ratio_library(self) -> None:
        """HENDRIX-Φ solver should import from golden_ratio_library, not redefine locally."""
        solver_source = Path(__file__).parent.parent / "python_backend" / "pythia_mining" / "hendrix_phi_solver.py"
        
        try:
            solver_text = solver_source.read_text()
        except FileNotFoundError:
            pytest.skip("hendrix_phi_solver.py not found")
        
        # Should import PHI from canonical sources
        import_patterns = [
            "from pythia_mining.golden_ratio_library import",
            "from .golden_ratio_library import",
            "from golden_ratio_library import",
            "import pythia_mining.golden_ratio_library",
        ]
        
        has_canonical_import = any(pattern in solver_text for pattern in import_patterns)
        assert has_canonical_import, "HENDRIX-Φ solver should import φ primitives from canonical library"
        
        # Should not redefine PHI locally (except possibly as alias)
        # Look for lines that define PHI with a numeric value
        lines = solver_text.split('\n')
        for line in lines:
            line_stripped = line.strip()
            # Check for PHI definitions with numeric values
            if ("PHI =" in line_stripped or "phi =" in line_stripped) and "1.618" in line:
                # Check if it's an import statement
                if "import" not in line_stripped and "from" not in line_stripped:
                    # Check if it's just reassigning from imported value
                    if "PHI," in line or "phi," in line:
                        continue  # This is part of an import statement
                    pytest.fail(f"HENDRIX-Φ solver may redefine φ locally: {line_stripped}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])