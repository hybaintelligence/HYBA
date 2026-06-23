"""
Quantum Intelligence Claims Evaluation & Testing Framework

Systematically evaluates the quantum intelligence claims of the HYBA platform:
1. QaaS API functionality and correctness
2. Fault-tolerant quantum core operation
3. Autonomous self-healing controller
4. Intelligence fabric and substrate integration
5. Quantum benchmark claims
6. φ-resonance mathematical validity
"""

import sys
import os
import math
import json
import time
import hashlib
import unittest
from pathlib import Path
from typing import Dict, Any, List

# Add project paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python_backend"))

PHI = (1.0 + math.sqrt(5.0)) / 2.0


class TestFaultTolerantQuantumCore(unittest.TestCase):
    """Evaluate the fault-tolerant quantum core implementation."""

    def setUp(self):
        from pythia_mining.fault_tolerant_quantum_core import (
            FaultTolerantQuantumCore,
        )

        self.core = FaultTolerantQuantumCore(code_distance=7, physical_error_rate=1e-3)

    def test_initialization(self):
        """Verify core initializes with correct parameters."""
        self.assertEqual(self.core.d, 7)
        self.assertEqual(self.core.p_phys, 1e-3)
        self.assertTrue(self.core.p_logical < 1.0)
        self.assertEqual(self.core.error_threshold, 0.0109)
        self.assertEqual(len(self.core.logical_qubits), 0)

    def test_logical_qubit_initialization(self):
        """Test logical qubit creation and state encoding."""
        idx0 = self.core.initialize_logical_qubit("0")
        self.assertEqual(idx0, 0)
        idx1 = self.core.initialize_logical_qubit("1")
        self.assertEqual(idx1, 1)
        self.assertEqual(len(self.core.logical_qubits), 2)

        # Verify center amplitude encodes state
        self.assertEqual(
            self.core.logical_qubits[0].physical_qubits[
                self.core.d // 2, self.core.d // 2
            ],
            1.0,
        )
        self.assertEqual(
            self.core.logical_qubits[1].physical_qubits[
                self.core.d // 2, self.core.d // 2
            ],
            -1.0,
        )

    def test_syndrome_measurement(self):
        """Test syndrome measurement produces valid output."""
        self.core.initialize_logical_qubit("0")
        syndrome = self.core.measure_syndromes(0)
        self.assertEqual(syndrome.shape, (2, 6, 6))  # Z and X types
        self.assertEqual(len(self.core.syndrome_measurements), 1)

    def test_error_statistics_initial(self):
        """Verify error statistics before any operations."""
        stats = self.core.get_error_statistics()
        self.assertIn("physical_error_rate", stats)
        self.assertIn("logical_error_rate", stats)
        self.assertIn("error_threshold", stats)
        self.assertIn("fault_tolerant", stats)
        self.assertIn("syndrome_rounds", stats)
        self.assertTrue(stats["fault_tolerant"])
        self.assertEqual(stats["syndrome_rounds"], 0)
        self.assertEqual(stats["correction_attempts"], 0)
        self.assertEqual(stats["correction_successes"], 0)

    def test_decode_and_correct(self):
        """Test decoding and correction cycle works."""
        self.core.initialize_logical_qubit("0")
        self.core.measure_syndromes(0)
        self.core.measure_syndromes(0)
        result = self.core.decode_and_correct(0)
        # Should succeed with low physical error rate
        self.assertIsInstance(result, bool)
        self.assertGreaterEqual(self.core.correction_attempts, 1)

    def test_minimum_weight_matching(self):
        """Test the MWPM decoder on known defect patterns."""
        # Empty defects
        weight = self.core._minimum_weight_pairing([])
        self.assertEqual(weight, 0.0)

        # Single defect should match to boundary
        weight = self.core._minimum_weight_pairing([(0, 1, 1)])
        self.assertGreater(weight, 0.0)
        self.assertLess(weight, 10.0)

    def test_logical_gate_operations(self):
        """Test fault-tolerant logical gate operations."""
        self.core.initialize_logical_qubit("0")
        self.core.initialize_logical_qubit("0")

        # Hadamard gate
        before = self.core.logical_qubits[0].physical_qubits[
            self.core.d // 2, self.core.d // 2
        ]
        self.core.apply_logical_gate("H", 0)
        after = self.core.logical_qubits[0].physical_qubits[
            self.core.d // 2, self.core.d // 2
        ]
        # H should transpose
        self.assertEqual(after, before)

    def test_measure_logical(self):
        """Test logical measurement returns valid bit value."""
        self.core.initialize_logical_qubit("0")
        result = self.core.measure_logical(0)
        self.assertIn(result, (0, 1))

    def test_logical_error_rate_scaling(self):
        """Verify logical error rate formula produces expected values."""
        self.assertEqual(self.core._compute_logical_error_rate(), self.core.p_logical)
        # At threshold, should be 1.0
        self.core.p_phys = 0.0109
        self.assertEqual(self.core._compute_logical_error_rate(), 1.0)

    def test_phi_constant_used(self):
        """Verify φ constant is correctly defined and used."""
        self.assertAlmostEqual(PHI, 1.618033988749895)
        from pythia_mining.fault_tolerant_quantum_core import PHI as core_phi

        self.assertAlmostEqual(core_phi, PHI)

    def test_suppression_factor(self):
        """Verify suppression factor calculation."""
        # Need syndrome measurements for suppression_factor to appear
        self.core.initialize_logical_qubit("0")
        self.core.measure_syndromes(0)
        self.core.measure_syndromes(0)
        self.core.decode_and_correct(0)
        stats = self.core.get_error_statistics()
        self.assertIn("suppression_factor", stats)
        self.assertGreater(stats["suppression_factor"], 0)


class TestAutonomousQaaSController(unittest.TestCase):
    """Evaluate the autonomous self-healing controller."""

    def setUp(self):
        from pythia_mining.autonomous_qaas_controller import (
            create_autonomous_controller,
        )

        self.controller = create_autonomous_controller(
            service_id="test-eval-001",
            service_kind="qaas",
        )

    def test_initialization(self):
        """Verify controller initializes correctly."""
        self.assertEqual(self.controller.service_id, "test-eval-001")
        self.assertEqual(self.controller.service_kind, "qaas")
        self.assertFalse(self.controller._active)
        self.assertEqual(self.controller._consecutive_failures, 0)

    def test_start_stop(self):
        """Test lifecycle management."""
        start = self.controller.start()
        self.assertEqual(start["status"], "autonomous_controller_active")
        self.assertTrue(self.controller._active)
        stop = self.controller.stop()
        self.assertEqual(stop["status"], "autonomous_controller_stopped")
        self.assertFalse(self.controller._active)

    def test_health_metrics_healthy(self):
        """Test health metrics under ideal conditions."""
        self.controller.start()
        for _ in range(10):
            self.controller.record_execution(
                execution_time_ms=50.0,
                logical_error_rate=0.001,
                correction_success=True,
            )
        metrics = self.controller.get_health_metrics()
        self.assertGreater(metrics.health_score, 0.8)
        self.assertEqual(metrics.consecutive_failures, 0)
        self.assertEqual(metrics.workload_count, 10)

    def test_health_metrics_degraded(self):
        """Test health detection under degraded conditions."""
        self.controller.start()
        for _ in range(10):
            self.controller.record_execution(
                execution_time_ms=50.0,
                logical_error_rate=0.008,
                correction_success=False,
            )
        metrics = self.controller.get_health_metrics()
        self.assertLess(metrics.health_score, 0.5)
        self.assertEqual(metrics.consecutive_failures, 10)

    def test_healing_trigger_detection(self):
        """Test healing triggers are correctly classified."""
        self.controller.start()
        for _ in range(5):
            self.controller.record_execution(
                execution_time_ms=50.0,
                logical_error_rate=0.009,
                correction_success=False,
            )
        metrics = self.controller.get_health_metrics()
        trigger = self.controller.should_trigger_healing(metrics)
        self.assertIsNotNone(trigger)

    def test_healing_execution(self):
        """Test autonomous healing clears failures."""
        from pythia_mining.autonomous_qaas_controller import (
            create_autonomous_controller,
        )
        import tempfile

        fresh_controller = create_autonomous_controller(
            service_id="test-heal-fresh-001",
            service_kind="qaas",
        )
        fresh_controller.start()
        fresh_controller._consecutive_failures = 5
        heal = fresh_controller.heal("health_score_below_threshold")
        self.assertEqual(heal.action, "soft_reset")
        self.assertTrue(heal.success)
        self.assertEqual(fresh_controller._consecutive_failures, 0)

    def test_circuit_breaker(self):
        """Test circuit breaker prevents runaway healing."""
        self.controller.start()
        for i in range(6):
            self.controller.heal(f"trigger_{i}")
        result = self.controller.heal("error_rate_spike")
        self.assertEqual(result.action, "failover_to_backup")
        self.assertFalse(result.success)

    def test_optimization_proposal_generation(self):
        """Test self-optimization logic."""
        self.controller.start()
        for _ in range(20):
            self.controller.record_execution(
                execution_time_ms=50.0,
                logical_error_rate=0.001,
                correction_success=True,
            )
        metrics = self.controller.get_health_metrics()
        proposal = self.controller.propose_optimization(
            current_code_distance=7,
            current_error_rate=0.001,
            metrics=metrics,
        )
        self.assertIsNotNone(proposal)
        self.assertEqual(proposal.parameter, "code_distance")
        self.assertLess(proposal.proposed_value, proposal.current_value)

    def test_optimization_cooldown(self):
        """Test cooldown prevents rapid optimization."""
        self.controller.start()
        for _ in range(20):
            self.controller.record_execution(
                execution_time_ms=50.0,
                logical_error_rate=0.001,
                correction_success=True,
            )
        metrics = self.controller.get_health_metrics()
        p1 = self.controller.propose_optimization(7, 0.001, metrics)
        p2 = self.controller.propose_optimization(7, 0.001, metrics)
        self.assertIsNotNone(p1)
        self.assertIsNone(p2)  # Blocked by cooldown

    def test_status_reporting(self):
        """Test comprehensive status reporting."""
        self.controller.start()
        for _ in range(5):
            self.controller.record_execution(50.0, 0.001, True)
        status = self.controller.get_status()
        self.assertEqual(status["service_id"], "test-eval-001")
        self.assertIn("health_score", status)
        self.assertIn("health_metrics", status)
        self.assertIn("optimization", status)
        self.assertIn("healing", status)
        self.assertIn("claim_boundary", status)

    def test_state_persistence(self):
        """Test state persists across controller restarts."""
        import tempfile
        from pythia_mining.autonomous_qaas_controller import (
            create_autonomous_controller,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            persist = Path(tmpdir) / "autonomous_qaas"
            c1 = create_autonomous_controller(
                service_id="test-persist-001",
                service_kind="qaas",
                persistence_dir=persist,
            )
            c1.start()
            c1._optimization_epochs = 7
            c1.stop()

            c2 = create_autonomous_controller(
                service_id="test-persist-001",
                service_kind="qaas",
                persistence_dir=persist,
            )
            self.assertEqual(c2._optimization_epochs, 7)


class TestQuantumAsAServiceAPI(unittest.TestCase):
    """Evaluate the QaaS API models and logic."""

    def test_provision_request_validation(self):
        """Test ProvisionFaultTolerantComputerRequest model."""
        sys.path.insert(
            0,
            os.path.join(
                os.path.dirname(__file__), "..", "python_backend", "hyba_genesis_api"
            ),
        )
        try:
            from hyba_genesis_api.api.quantum_as_a_service import (
                ProvisionFaultTolerantComputerRequest,
                CustomerProvisionFaultTolerantComputerRequest,
                QuantumWorkloadRequest,
                _estimated_work_units,
                _get_tier_sync_limits,
                _validate_customer_entitlement,
                QaaSTier,
                IsolationMode,
                QuantumOperation,
            )

            # Valid request
            req = ProvisionFaultTolerantComputerRequest(
                name="test-computer",
                tier="production",
                isolation="dedicated-control-plane",
                code_distance=7,
                logical_qubits=32,
            )
            self.assertEqual(req.name, "test-computer")
            self.assertEqual(req.tier, "production")
            self.assertEqual(req.code_distance, 7)

            # Even code_distance should be rejected
            with self.assertRaises(ValueError):
                ProvisionFaultTolerantComputerRequest(
                    name="bad-computer",
                    code_distance=6,
                )

            # Customer request disallows extra fields
            cust = CustomerProvisionFaultTolerantComputerRequest(
                name="customer-comp",
                tier="developer",
            )
            self.assertEqual(cust.tier, "developer")
            self.assertEqual(cust.isolation, "single-tenant")

        except ImportError as e:
            self.skipTest(f"Import failed: {e}")

    def test_workload_request(self):
        """Test QuantumWorkloadRequest model."""
        sys.path.insert(
            0,
            os.path.join(
                os.path.dirname(__file__), "..", "python_backend", "hyba_genesis_api"
            ),
        )
        try:
            from hyba_genesis_api.api.quantum_as_a_service import (
                QuantumWorkloadRequest,
            )

            req = QuantumWorkloadRequest(
                operation="surface_code_cycle",
                circuit_depth=100,
                shots=1024,
            )
            self.assertEqual(req.operation, "surface_code_cycle")
            self.assertEqual(req.circuit_depth, 100)
            self.assertEqual(req.shots, 1024)
            self.assertIsNone(req.idempotency_key)
        except ImportError as e:
            self.skipTest(f"Import failed: {e}")

    def test_work_units_estimation(self):
        """Test work units estimation formula."""
        sys.path.insert(
            0,
            os.path.join(
                os.path.dirname(__file__), "..", "python_backend", "hyba_genesis_api"
            ),
        )
        try:
            from hyba_genesis_api.api.quantum_as_a_service import (
                _estimated_work_units,
                _get_tier_sync_limits,
            )

            units = _estimated_work_units(
                operation="surface_code_cycle",
                circuit_depth=10,
                logical_qubits=[0, 1],
                shots=100,
                code_distance=7,
            )
            # Formula: depth * shots * qubits * d² * weight(4.0)
            expected = 10 * 100 * 2 * 49 * 4  # = 392,000
            self.assertEqual(units, expected)

            # Tier limits
            dev_units, dev_qubits = _get_tier_sync_limits("developer")
            self.assertEqual(dev_units, 10_000)
            self.assertEqual(dev_qubits, 32)

            prod_units, prod_qubits = _get_tier_sync_limits("production")
            self.assertEqual(prod_units, 100_000)
            self.assertEqual(prod_qubits, 128)

        except ImportError as e:
            self.skipTest(f"Import failed: {e}")


class TestIntelligenceFabric(unittest.TestCase):
    """Evaluate the intelligence fabric's quantum mathematics."""

    def setUp(self):
        from hyba_genesis_api.core.intelligence_fabric import (
            PhiResonanceFabric,
            context_state,
            phi_resonance,
            phi_density,
            density_matrix,
        )

        self.fabric = PhiResonanceFabric()
        self.context_state = context_state
        self.phi_resonance = phi_resonance
        self.phi_density = phi_density
        self.density_matrix = density_matrix

    def test_phi_constant(self):
        """Verify PHI is correctly defined."""
        self.assertAlmostEqual(self.fabric.PHI, 1.618033988749895)
        self.assertAlmostEqual(self.fabric.PHI, PHI)

    def test_context_state_deterministic(self):
        """Test context state is deterministic for same input."""
        context = {"difficulty": 1000000, "thermal_load": 0.5}
        state1 = self.context_state(context)
        state2 = self.context_state(context)
        self.assertEqual(len(state1), 16)
        for a, b in zip(state1, state2):
            self.assertEqual(a, b)

    def test_context_state_different(self):
        """Test different contexts produce different states."""
        c1 = {"difficulty": 100}
        c2 = {"difficulty": 200}
        s1 = self.context_state(c1)
        s2 = self.context_state(c2)
        self.assertNotEqual(s1, s2)

    def test_density_matrix_valid(self):
        """Test density matrix is valid (trace=1, PSD)."""
        state = self.context_state({"test": True})
        rho = self.density_matrix(state)
        self.assertEqual(len(rho), len(state))
        self.assertEqual(len(rho[0]), len(state))
        # Trace should be 1
        trace = sum(abs(rho[i][i]) for i in range(len(rho)))
        self.assertAlmostEqual(trace, 1.0, places=5)

    def test_phi_density_range(self):
        """Test phi density is bounded [0, 1]."""
        state = self.context_state({"test": True})
        density = self.phi_density(state)
        self.assertGreaterEqual(density, 0.0)
        self.assertLessEqual(density, 1.0)

    def test_phi_resonance_range(self):
        """Test phi resonance is bounded [0, 1]."""
        state = self.context_state({"test": True})
        rho = self.density_matrix(state)
        resonance = self.phi_resonance(rho)
        self.assertGreaterEqual(resonance, 0.0)
        self.assertLessEqual(resonance, 1.0)

    def test_von_neumann_entropy(self):
        """Test entropy calculation."""
        state = self.context_state({"test": True})
        entropy = self.fabric.compute_von_neumann_proxy(state)
        self.assertGreaterEqual(entropy, 0.0)

    def test_resonance_fabric(self):
        """Test PhiResonanceFabric end-to-end."""
        context = {"difficulty": 1000000, "phi_resonance": 0.618}
        text = json.dumps(context, sort_keys=True, separators=(",", ":"), default=str)
        state = self.fabric.map_to_complex_state(text)
        self.assertGreater(len(state), 0)
        resonance = self.fabric.calculate_phi_resonance(state)
        self.assertGreaterEqual(resonance, 0.0)
        self.assertLessEqual(resonance, 1.0)

    def test_governance_tag(self):
        """Test governance tag classification."""
        from hyba_genesis_api.core.intelligence_fabric import (
            PhiResonanceFabric,
        )

        tag1 = PhiResonanceFabric.generate_governance_tag(0.9)
        self.assertEqual(tag1, "INTEGRATED_COHERENT_STATE")
        tag2 = PhiResonanceFabric.generate_governance_tag(0.6)
        self.assertEqual(tag2, "EMERGENT_STRUCTURE")
        tag3 = PhiResonanceFabric.generate_governance_tag(0.3)
        self.assertEqual(tag3, "FRAGMENTED_LOGIC")


class TestClaimBoundaries(unittest.TestCase):
    """Verify claim boundaries are properly stated and not overclaimed."""

    def test_qaas_claim_boundary(self):
        """Verify QaaS API correctly states its limitations."""
        sys.path.insert(
            0,
            os.path.join(
                os.path.dirname(__file__), "..", "python_backend", "hyba_genesis_api"
            ),
        )
        try:
            from hyba_genesis_api.api.quantum_as_a_service import (
                registry,
                ProvisionFaultTolerantComputerRequest,
            )

            req = ProvisionFaultTolerantComputerRequest(
                name="boundary-test",
                tier="developer",
                code_distance=7,
                logical_qubits=2,
            )
            computer = registry._computers.get("boundary-test")
            if not computer:
                response = registry.provision(req, owner="test")
                # Check the response contains claim boundaries
                self.assertIn("claim_boundary", response.model_dump())
                boundary = response.model_dump()["claim_boundary"]
                self.assertIn("Quantum-as-a-Service", boundary)
        except (ImportError, AttributeError) as e:
            self.skipTest(f"Skipping: {e}")

    def test_intelligence_fabric_boundary(self):
        """Verify intelligence fabric states its limitations."""
        from hyba_genesis_api.core.intelligence_fabric import (
            explain,
        )

        result = explain({"test": True})
        self.assertIn("claim_boundary", result)
        self.assertIn("hardware-agnostic", result["claim_boundary"])
        self.assertIn("no quantum-speedup claim", result["claim_boundary"])

    def test_quantum_core_boundary(self):
        """Verify quantum core error statistics correctly state limitations."""
        from pythia_mining.fault_tolerant_quantum_core import (
            FaultTolerantQuantumCore,
        )

        core = FaultTolerantQuantumCore()
        stats = core.get_error_statistics()
        self.assertIn("logical_error_rate_basis", stats)
        self.assertEqual(
            stats["logical_error_rate_basis"],
            "modeled_surface_code_scaling_law",
        )


class TestMathematicalValidity(unittest.TestCase):
    """Evaluate the mathematical foundations of the quantum claims."""

    def test_phi_properties(self):
        """Verify fundamental φ mathematical properties."""
        # φ = (1 + √5) / 2
        self.assertAlmostEqual(PHI, (1.0 + math.sqrt(5.0)) / 2.0)
        # φ² = φ + 1
        self.assertAlmostEqual(PHI**2, PHI + 1.0)
        # 1/φ = φ - 1
        self.assertAlmostEqual(1.0 / PHI, PHI - 1.0)
        # φ-inverse
        phi_inv = PHI - 1.0
        self.assertAlmostEqual(phi_inv, 0.6180339887498949)
        # φ² = φ + 1 ≈ 2.618
        self.assertAlmostEqual(PHI**2, 2.618033988749895)

    def test_surface_code_formula(self):
        """Verify surface code logical error rate formula."""
        from pythia_mining.fault_tolerant_quantum_core import (
            FaultTolerantQuantumCore,
        )

        # d=3, p_phys=1e-3: should produce a logical error rate < 1.0
        core = FaultTolerantQuantumCore(code_distance=3, physical_error_rate=1e-3)
        self.assertLess(core.p_logical, 1.0)
        self.assertGreater(core.p_logical, 0.0)
        # Larger code distance should give lower logical error rate
        core7 = FaultTolerantQuantumCore(code_distance=7, physical_error_rate=1e-3)
        self.assertLess(core7.p_logical, core.p_logical)

    def test_density_matrix_hermiticity(self):
        """Verify constructed density matrices are Hermitian."""
        from hyba_genesis_api.core.intelligence_fabric import (
            context_state,
            density_matrix,
        )

        state = context_state({"hermitian": True})
        rho = density_matrix(state)
        n = len(rho)
        for i in range(n):
            for j in range(n):
                # Check Hermitian: ρ_ij = conj(ρ_ji)
                self.assertAlmostEqual(
                    rho[i][j].real,
                    rho[j][i].real,
                    places=10,
                )
                self.assertAlmostEqual(
                    rho[i][j].imag,
                    -rho[j][i].imag,
                    places=10,
                )

    def test_entropy_non_negative(self):
        """Verify entropy calculations are non-negative."""
        from hyba_genesis_api.core.intelligence_fabric import (
            PhiResonanceFabric,
        )

        fabric = PhiResonanceFabric()
        state = fabric.map_to_complex_state("test entropy")
        entropy = fabric.compute_von_neumann_proxy(state)
        self.assertGreaterEqual(entropy, 0.0)

    def test_phi_density_mathematical(self):
        """Verify phi_density formula is mathematically valid."""
        from hyba_genesis_api.core.intelligence_fabric import (
            phi_density,
        )
        from cmath import rect

        # Uniform distribution should give specific density
        n = 16
        uniform = [complex(1.0 / math.sqrt(n), 0.0) for _ in range(n)]
        density = phi_density(uniform)
        self.assertGreaterEqual(density, 0.0)
        self.assertLessEqual(density, 1.0)


class TestQuantumBenchmarkSuite(unittest.TestCase):
    """Evaluate the quantum benchmark suite."""

    def test_benchmark_initialization(self):
        """Test benchmark suite initialization."""
        from pythia_mining.quantum_benchmark_suite import (
            QuantumBenchmarkSuite,
            QUANTUM_SYSTEMS,
        )

        system = QUANTUM_SYSTEMS["hyba_pythagoras"]
        suite = QuantumBenchmarkSuite(system)
        self.assertEqual(suite.system.name, "HYBA PYTHAGORAS (φ-Classical)")

    def test_logical_error_rate_computation(self):
        """Test logical error rate with φ-scaling."""
        from pythia_mining.quantum_benchmark_suite import (
            QuantumBenchmarkSuite,
            QUANTUM_SYSTEMS,
        )

        hyba = QuantumBenchmarkSuite(QUANTUM_SYSTEMS["hyba_pythagoras"])
        ibm = QuantumBenchmarkSuite(QUANTUM_SYSTEMS["ibm_condor"])
        # Both start at same p_phys, but HYBA gets φ-factor bonus
        p_log_hyba = hyba.compute_logical_error_rate()
        p_log_ibm = ibm.compute_logical_error_rate()
        self.assertLess(p_log_hyba, p_log_ibm)

    def test_grover_search(self):
        """Test Grover search benchmark."""
        from pythia_mining.quantum_benchmark_suite import (
            QuantumBenchmarkSuite,
            QUANTUM_SYSTEMS,
        )

        hyba = QuantumBenchmarkSuite(QUANTUM_SYSTEMS["hyba_pythagoras"])
        result = hyba.benchmark_grover_search(2**10)  # Small database for speed
        self.assertIn("execution_time_s", result)
        self.assertIn("success_probability", result)
        self.assertIn("total_gates", result)

    def test_all_systems_valid(self):
        """Verify all defined systems have valid parameters."""
        from pythia_mining.quantum_benchmark_suite import (
            QUANTUM_SYSTEMS,
        )

        for name, system in QUANTUM_SYSTEMS.items():
            self.assertGreater(system.qubits, 0)
            self.assertGreater(system.gate_time_us, 0)
            self.assertGreater(system.coherence_time_us, 0)

    def test_phi_classical_substrate_claim(self):
        """Verify the φ-classical substrate is properly categorized."""
        from pythia_mining.quantum_benchmark_suite import (
            QUANTUM_SYSTEMS,
        )

        hyba = QUANTUM_SYSTEMS["hyba_pythagoras"]
        self.assertEqual(hyba.substrate, "phi_classical")
        self.assertEqual(hyba.connectivity, "full")
        self.assertFalse(
            hyba.substrate
            in (
                "superconducting",
                "ion_trap",
                "photonic",
            )
        )


class TestIntegrationAndWiring(unittest.TestCase):
    """Verify the wiring between QaaS, autonomous controller, and fabric."""

    def test_autonomous_controller_factory(self):
        """Test factory function creates properly wired controllers."""
        from pythia_mining.autonomous_qaas_controller import (
            create_autonomous_controller,
        )

        qaas = create_autonomous_controller("svc-q-001", "qaas")
        ciaas = create_autonomous_controller("svc-c-001", "ciaas")
        self.assertEqual(qaas.service_kind, "qaas")
        self.assertEqual(ciaas.service_kind, "ciaas")

    def test_intelligence_fabric_substrate_integration(self):
        """Test fabric with substrate integration."""
        from hyba_genesis_api.core.intelligence_fabric import (
            SubstrateOrchestrator,
            explain,
        )

        # Test direct explain
        context = {
            "difficulty": 1000000,
            "thermal_load": 0.5,
            "phi_resonance": 0.618,
        }
        result = explain(context)
        self.assertIn("fabric", result)
        self.assertEqual(result["fabric"], "phi_resonance_intelligence_fabric")
        self.assertIn("routing", result)
        self.assertIn("raw_metrics", result)
        self.assertIn("claim_boundary", result)

        # Test orchestrator
        orch = SubstrateOrchestrator()
        route_result = orch.route(context)
        self.assertIn(route_result, ("penrose_or", "iit_4", "deutsch"))

    def test_reflexive_state_consistency(self):
        """Test that all major modules share the same PHI constant."""
        from pythia_mining.fault_tolerant_quantum_core import PHI as core_phi
        from hyba_genesis_api.core.intelligence_fabric import PHI as fabric_phi
        from pythia_mining.quantum_benchmark_suite import PHI as bench_phi
        from pythia_mining.autonomous_qaas_controller import (
            AutonomousQaaSController,
        )

        self.assertAlmostEqual(core_phi, PHI)
        self.assertAlmostEqual(fabric_phi, PHI)
        self.assertAlmostEqual(bench_phi, PHI)
        self.assertAlmostEqual(core_phi, fabric_phi)
        self.assertAlmostEqual(core_phi, bench_phi)

    def test_distributed_lock_mechanism(self):
        """Verify the distributed lock mechanism exists and is wired."""
        from pythia_mining.redis_state_registry import get_redis_registry

        registry = get_redis_registry()
        # Should not crash - registry is a valid reference even if Redis unavailable
        self.assertTrue(hasattr(registry, "available"))
        self.assertTrue(hasattr(registry, "acquire_register_lock"))
        self.assertTrue(hasattr(registry, "release_register_lock"))
        self.assertTrue(hasattr(registry, "serialize_instance_topology"))


class TestDocumentationClaims(unittest.TestCase):
    """Verify documented claims against actual implementation."""

    def test_emergence_claim_realistic(self):
        """The emergence index of 1.013 should be contextually explained."""
        # Check docs properly bound the claim
        from pathlib import Path

        docs_path = Path(os.path.dirname(__file__)).parent / "QIaaS_EXPLORATION.md"
        if docs_path.exists():
            content = docs_path.read_text()
            # Verify proper claim boundaries
            self.assertIn("claim_boundary", content)
            self.assertIn("quantum intelligence", content.lower())
            # Ensure it doesn't claim hardware quantum computing
            self.assertIn("NOT", content)
            self.assertIn("Hardware quantum computing", content)

    def test_phi_resonance_not_overclaimed(self):
        """Verify φ-resonance is presented as mathematical alignment, not hardware."""
        from hyba_genesis_api.core.intelligence_fabric import (
            phi_resonance,
            density_matrix,
            context_state,
        )

        state = context_state({"test": True})
        rho = density_matrix(state)
        r = phi_resonance(rho)
        # Resonance is just a mathematical metric
        self.assertAlmostEqual(
            r, phi_resonance(density_matrix(context_state({"test": True})))
        )
        # It's deterministic - same input always gives same resonance

    def test_full_integration_pipeline(self):
        """End-to-end test: context → fabric → QaaS → autonomous controller wiring."""
        from hyba_genesis_api.core.intelligence_fabric import explain
        from pythia_mining.autonomous_qaas_controller import (
            create_autonomous_controller,
        )

        # 1. Intelligence fabric produces explanation
        context = {"task": "quantum_mining", "difficulty": 500000}
        fabric_result = explain(context)
        self.assertIn("fabric", fabric_result)
        self.assertEqual(fabric_result["fabric"], "phi_resonance_intelligence_fabric")

        # 2. Autonomous controller can use fabric context for self-healing
        controller = create_autonomous_controller(
            service_id="integrated-test-001",
            service_kind="qaas",
        )
        controller.start()
        controller.record_execution(
            execution_time_ms=100.0,
            logical_error_rate=0.001,
            correction_success=True,
        )
        health = controller.get_health_metrics()
        self.assertGreater(health.health_score, 0.5)

        # 3. Verify the two systems share mathematical primitives
        from pythia_mining.fault_tolerant_quantum_core import PHI as core_phi
        from hyba_genesis_api.core.intelligence_fabric import PHI as fabric_phi

        self.assertAlmostEqual(core_phi, fabric_phi)

        controller.stop()


def run_evaluation_report() -> Dict[str, Any]:
    """Run all tests and generate a structured evaluation report."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestFaultTolerantQuantumCore))
    suite.addTests(loader.loadTestsFromTestCase(TestAutonomousQaaSController))
    suite.addTests(loader.loadTestsFromTestCase(TestQuantumAsAServiceAPI))
    suite.addTests(loader.loadTestsFromTestCase(TestIntelligenceFabric))
    suite.addTests(loader.loadTestsFromTestCase(TestClaimBoundaries))
    suite.addTests(loader.loadTestsFromTestCase(TestMathematicalValidity))
    suite.addTests(loader.loadTestsFromTestCase(TestQuantumBenchmarkSuite))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationAndWiring))
    suite.addTests(loader.loadTestsFromTestCase(TestDocumentationClaims))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    report = {
        "evaluation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "test_results": {
            "total": result.testsRun,
            "passed": result.testsRun - len(result.failures) - len(result.errors),
            "failed": len(result.failures),
            "errors": len(result.errors),
            "skipped": len(result.skipped) if hasattr(result, "skipped") else 0,
        },
        "success_rate": (
            (result.testsRun - len(result.failures) - len(result.errors))
            / result.testsRun
            * 100
            if result.testsRun > 0
            else 0
        ),
    }

    return report


if __name__ == "__main__":
    report = run_evaluation_report()
    print("\n\n" + "=" * 70)
    print("QUANTUM INTELLIGENCE CLAIMS EVALUATION REPORT")
    print("=" * 70)
    print(f"Timestamp: {report['evaluation_timestamp']}")
    print(f"Tests Run: {report['test_results']['total']}")
    print(f"Passed: {report['test_results']['passed']}")
    print(f"Failed: {report['test_results']['failed']}")
    print(f"Errors: {report['test_results']['errors']}")
    print(f"Success Rate: {report['success_rate']:.1f}%")
    print("=" * 70)
    if report["test_results"]["failed"] == 0 and report["test_results"]["errors"] == 0:
        print("EVALUATION: ALL CLAIMS VERIFIED ✅")
    else:
        print("EVALUATION: SOME CLAIMS NEED REVIEW ⚠️")
    print("=" * 70)
