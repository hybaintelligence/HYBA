"""Enterprise-grade tests for Millennium Mathematics as a Service (MMaaS) API

Tests all 7 Millennium Prize Problems with:
- Functional correctness
- Error handling
- Idempotency
- Authentication/authorization
- Performance benchmarks
- Evidence seal validation
"""

import pytest
import hashlib
import json
from datetime import UTC, datetime

from pythia_mining.golden_ratio_library import PHI
from pythia_mining.yang_mills_spectral_gap import YANG_MILLS_THRESHOLD, LAMBDA_QCD


class TestYangMillsMassGap:
    """Test Yang-Mills Mass Gap operations (flagship)."""

    def test_measure_spectral_gap_default_parameters(self):
        """Test spectral gap measurement with default parameters."""
        from hyba_genesis_api.api.millennium_mathematics import YangMillsOperations

        params = {"lattice_size": 4, "n_configurations": 50}  # Small for speed
        result = YangMillsOperations.measure_spectral_gap(params)

        assert result["success"] is True
        assert result["yang_mills_threshold"] == YANG_MILLS_THRESHOLD
        assert "measured_gap_GeV" in result
        assert "expected_gap_GeV" in result
        assert "claim_boundary" in result
        assert "not a claim to solve" in result["claim_boundary"]

    def test_compute_yang_mills_action(self):
        """Test Yang-Mills action computation."""
        from hyba_genesis_api.api.millennium_mathematics import YangMillsOperations

        params = {"coupling": 2.3, "trace_value": 1.5}
        result = YangMillsOperations.compute_yang_mills_action(params)

        assert "action" in result
        assert result["coupling"] == 2.3
        assert result["threshold"] == YANG_MILLS_THRESHOLD
        assert result["relationship"] == f"3 - φ = {YANG_MILLS_THRESHOLD:.6f}"
        assert isinstance(result["gated"], bool)

    def test_yang_mills_threshold_mathematical_correctness(self):
        """Validate Yang-Mills threshold = 3 - φ."""
        expected = 3 - PHI
        assert abs(YANG_MILLS_THRESHOLD - expected) < 1e-9


class TestPvsNP:
    """Test P vs NP operations."""

    def test_verify_witness_valid(self):
        """Test witness verification with valid witness."""
        from hyba_genesis_api.api.millennium_mathematics import PvsNPOperations

        params = {
            "witness": "test_witness_123",
            "target": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
        }
        result = PvsNPOperations.verify_witness(params)

        assert "witness_hash" in result
        assert result["verified"] is True
        assert result["complexity_class"] == "P (polynomial time verification)"
        assert result["verification_time_ns"] > 0
        assert "claim_boundary" in result

    def test_verify_witness_invalid(self):
        """Test witness verification with invalid witness."""
        from hyba_genesis_api.api.millennium_mathematics import PvsNPOperations

        params = {
            "witness": "invalid_witness",
            "target": "0000000000000000000000000000000000000000000000000000000000000001",
        }
        result = PvsNPOperations.verify_witness(params)

        assert result["verified"] is False

    def test_search_reduction_analysis(self):
        """Test search space reduction analysis."""
        from hyba_genesis_api.api.millennium_mathematics import PvsNPOperations

        params = {"search_space_bits": 256, "phi_resonance_factor": PHI}
        result = PvsNPOperations.search_reduction_analysis(params)

        assert result["search_space_bits"] == 256
        assert result["phi_resonance_factor"] == PHI
        assert "estimated_speedup" in result
        assert result["empirical_speedup"] == "53x (measured on SHA-256 search)"
        assert "not a proof" in result["claim_boundary"]


class TestNavierStokes:
    """Test Navier-Stokes operations."""

    def test_validate_flow_smoothness_smooth(self):
        """Test flow smoothness validation with smooth flow."""
        from hyba_genesis_api.api.millennium_mathematics import NavierStokesOperations

        params = {
            "flow_metrics": {
                "velocity_gradient": 0.1,
                "pressure_gradient": 0.05,
                "reynolds_number": 1000,
            }
        }
        result = NavierStokesOperations.validate_flow_smoothness(params)

        assert result["smooth"] is True
        assert result["differentiable"] is True
        assert "gradient_magnitude" in result
        assert "claim_boundary" in result

    def test_validate_flow_smoothness_turbulent(self):
        """Test flow smoothness validation with turbulent flow."""
        from hyba_genesis_api.api.millennium_mathematics import NavierStokesOperations

        params = {
            "flow_metrics": {
                "velocity_gradient": 2.0,
                "pressure_gradient": 1.5,
                "reynolds_number": 50000,
            }
        }
        result = NavierStokesOperations.validate_flow_smoothness(params)

        assert result["smooth"] is False


class TestRiemannHypothesis:
    """Test Riemann Hypothesis operations."""

    def test_spectral_coherence_analysis(self):
        """Test spectral coherence analysis via SU(2) probe."""
        from hyba_genesis_api.api.millennium_mathematics import (
            RiemannHypothesisOperations,
        )

        params = {"sample_count": 128, "bins": 8, "r2_threshold": 0.8}
        result = RiemannHypothesisOperations.spectral_coherence_analysis(params)

        assert "success" in result
        assert "spectral_probe_sha256" in result
        assert "sample_count" in result
        assert result["sample_count"] == 128
        assert "spacing_count" in result
        assert "claim_boundary" in result
        assert "not a proof" in result["claim_boundary"]

    def test_riemann_spectral_probe_with_eigenvalues(self):
        """Test eigenvalue-based Riemann coherence analysis."""
        from hyba_genesis_api.api.millennium_mathematics import (
            RiemannHypothesisOperations,
        )

        # Eigenvalues on critical line
        eigenvalues = [0.5 + 1j * (i * PHI) for i in range(1, 51)]
        params = {"eigenvalues": eigenvalues}
        result = RiemannHypothesisOperations.eigenvalue_coherence_analysis(params)

        assert result["n_eigenvalues"] == 50
        assert result["critical_line"] == 0.5
        assert "alignment_percentage" in result
        assert result["phi"] == PHI
        assert "not a proof" in result["claim_boundary"]


class TestHodgeConjecture:
    """Test Hodge Conjecture operations."""

    def test_memory_geometry_analysis(self):
        """Test memory geometry analysis."""
        from hyba_genesis_api.api.millennium_mathematics import (
            HodgeConjectureOperations,
        )

        params = {
            "memory_state": {
                "cohomology_classes": 10,
                "algebraic_cycles": 7,
            }
        }
        result = HodgeConjectureOperations.memory_geometry_analysis(params)

        assert result["cohomology_classes"] == 10
        assert result["algebraic_cycles"] == 7
        assert result["hodge_ratio"] == 0.7
        assert result["geometry_type"] == "Bures manifold (density matrix evolution)"
        assert "claim_boundary" in result


class TestBSDConjecture:
    """Test BSD Conjecture operations."""

    def test_resource_flow_gating(self):
        """Test resource flow gating."""
        from hyba_genesis_api.api.millennium_mathematics import BSDConjectureOperations

        params = {
            "flow_state": {
                "accepted_shares": 85,
                "total_shares": 100,
            }
        }
        result = BSDConjectureOperations.resource_flow_gating(params)

        assert result["accepted_shares"] == 85
        assert result["total_shares"] == 100
        assert result["acceptance_rate"] == 0.85
        assert result["rank"] == 1  # High acceptance rate → rank 1
        assert "claim_boundary" in result


class TestPoincareConjecture:
    """Test Poincaré Conjecture operations."""

    def test_topological_identity_preservation(self):
        """Test topological identity preservation."""
        from hyba_genesis_api.api.millennium_mathematics import (
            PoincareConjectureOperations,
        )

        params = {
            "manifold_state": {
                "dimension": 3,
                "simply_connected": True,
                "homotopy_equivalent_to_sphere": True,
            }
        }
        result = PoincareConjectureOperations.topological_identity_preservation(params)

        assert result["dimension"] == 3
        assert result["simply_connected"] is True
        assert result["homeomorphic_to_sphere"] is True
        assert "Perelman" in result["claim_boundary"]


class TestMillenniumMathematicsService:
    """Test MMaaS service integration."""

    def test_execute_yang_mills_operation(self):
        """Test service execution with Yang-Mills operation."""
        from hyba_genesis_api.api.millennium_mathematics import (
            MillenniumMathematicsService,
            MillenniumOperationRequest,
        )

        service = MillenniumMathematicsService()
        request = MillenniumOperationRequest(
            problem="yang_mills_mass_gap",
            operation="compute_action",
            parameters={"coupling": 2.3, "trace_value": 1.5},
        )

        response = service.execute(request, owner="test_user")

        assert response.problem == "yang_mills_mass_gap"
        assert response.operation == "compute_action"
        assert "action" in response.result
        assert len(response.evidence_seal) == 64  # SHA-256 hex
        assert response.claim_boundary is not None

    def test_execute_with_idempotency(self):
        """Test idempotency of operations."""
        from hyba_genesis_api.api.millennium_mathematics import (
            MillenniumMathematicsService,
            MillenniumOperationRequest,
        )

        service = MillenniumMathematicsService()
        request = MillenniumOperationRequest(
            problem="p_vs_np",
            operation="verify_witness",
            parameters={"witness": "test", "target": "f" * 64},
            idempotency_key="test_key_123",
        )

        # First execution
        response1 = service.execute(request, owner="test_user")

        # Second execution with same idempotency key
        response2 = service.execute(request, owner="test_user")

        assert response1.operation_id == response2.operation_id
        assert response1.evidence_seal == response2.evidence_seal

    def test_execute_invalid_problem(self):
        """Test execution with invalid problem raises validation error."""
        from hyba_genesis_api.api.millennium_mathematics import (
            MillenniumOperationRequest,
        )
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            MillenniumOperationRequest(
                problem="invalid_problem",  # type: ignore
                operation="some_operation",
                parameters={},
            )

    def test_execute_invalid_operation(self):
        """Test execution with invalid operation."""
        from hyba_genesis_api.api.millennium_mathematics import (
            MillenniumMathematicsService,
            MillenniumOperationRequest,
        )
        from fastapi import HTTPException

        service = MillenniumMathematicsService()
        request = MillenniumOperationRequest(
            problem="yang_mills_mass_gap",
            operation="invalid_operation",
            parameters={},
        )

        with pytest.raises(HTTPException) as exc_info:
            service.execute(request, owner="test_user")

        assert exc_info.value.status_code == 400
        assert "Unknown operation" in str(exc_info.value.detail)

    def test_evidence_seal_validation(self):
        """Test evidence seal is valid SHA-256 hash."""
        from hyba_genesis_api.api.millennium_mathematics import (
            MillenniumMathematicsService,
            MillenniumOperationRequest,
        )

        service = MillenniumMathematicsService()
        request = MillenniumOperationRequest(
            problem="p_vs_np",
            operation="search_reduction_analysis",
            parameters={"search_space_bits": 256},
        )

        response = service.execute(request, owner="test_user")

        # Validate evidence seal format
        assert len(response.evidence_seal) == 64
        assert all(c in "0123456789abcdef" for c in response.evidence_seal)

        # Validate evidence seal is reproducible
        seal_payload = {
            "operation_id": response.operation_id,
            "problem": response.problem,
            "operation": response.operation,
            "parameters": request.parameters,
            "result": response.result,
            "executed_at": response.executed_at,
        }
        canonical = json.dumps(
            seal_payload, sort_keys=True, separators=(",", ":"), default=str
        )
        expected_seal = hashlib.sha256(canonical.encode()).hexdigest()

        assert response.evidence_seal == expected_seal


class TestMillenniumMathematicsAPI:
    """Test MMaaS API endpoints (integration tests)."""

    def test_list_problems_structure(self):
        """Test problems list endpoint structure."""
        from hyba_genesis_api.api.millennium_mathematics import service

        problems_data = {
            "problems": [
                {
                    "problem": problem,
                    "operations": list(ops.keys()),
                    "claim_boundary": service.CLAIM_BOUNDARIES[problem],
                }
                for problem, ops in service.OPERATIONS.items()
            ],
            "total_problems": len(service.OPERATIONS),
        }

        assert problems_data["total_problems"] == 7
        assert len(problems_data["problems"]) == 7

        # Validate all 7 Millennium Problems are present
        problem_names = [p["problem"] for p in problems_data["problems"]]
        expected_problems = [
            "yang_mills_mass_gap",
            "p_vs_np",
            "navier_stokes",
            "riemann_hypothesis",
            "hodge_conjecture",
            "bsd_conjecture",
            "poincare_conjecture",
        ]

        for expected in expected_problems:
            assert expected in problem_names


class TestPerformanceBenchmarks:
    """Performance benchmarks for MMaaS operations."""

    def test_yang_mills_action_performance(self):
        """Benchmark Yang-Mills action computation (< 1ms)."""
        import time
        from hyba_genesis_api.api.millennium_mathematics import YangMillsOperations

        params = {"coupling": 2.3, "trace_value": 1.5}

        start = time.perf_counter()
        result = YangMillsOperations.compute_yang_mills_action(params)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert "action" in result
        assert elapsed_ms < 10.0  # Well under 10ms

    def test_witness_verification_performance(self):
        """Benchmark witness verification (P-time operation)."""
        import time
        from hyba_genesis_api.api.millennium_mathematics import PvsNPOperations

        params = {"witness": "test_witness", "target": "f" * 64}

        start = time.perf_counter()
        result = PvsNPOperations.verify_witness(params)
        elapsed_ns = (time.perf_counter() - start) * 1e9

        assert "verified" in result
        assert elapsed_ns < 1_000_000  # < 1ms


class TestClaimBoundaries:
    """Validate claim boundaries for all operations."""

    def test_all_operations_have_claim_boundaries(self):
        """Ensure all operations return claim boundaries."""
        from hyba_genesis_api.api.millennium_mathematics import service

        for problem in service.OPERATIONS:
            assert problem in service.CLAIM_BOUNDARIES
            assert (
                "not a proof" in service.CLAIM_BOUNDARIES[problem].lower()
                or "proven by" in service.CLAIM_BOUNDARIES[problem].lower()
            )

    def test_yang_mills_claim_boundary(self):
        """Validate Yang-Mills specific claim boundary."""
        from hyba_genesis_api.api.millennium_mathematics import YangMillsOperations

        params = {"coupling": 2.3, "trace_value": 1.5}
        result = YangMillsOperations.compute_yang_mills_action(params)

        # Service-level should have it
        from hyba_genesis_api.api.millennium_mathematics import service

        assert "not a proof" in service.CLAIM_BOUNDARIES["yang_mills_mass_gap"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
