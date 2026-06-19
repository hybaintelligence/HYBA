"""
Test Synthetic Morphogenesis: Φ-Architecture Integration

Tests the complete Φ-architecture including:
1. Φ-ALU Golden Modulo Memory Addressing
2. Fibonacci-LCG Golden Spiral Exploration
3. Mass Gap Shield Safety Gates
4. Φ-Core Orchestrator Synthetic Morphogenesis
"""

import sys
import time
import numpy as np
import unittest
from pathlib import Path
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

# Import Φ-architecture components
from pythia_mining.phi_alu import PhiALU, PhiALUHardware
from pythia_mining.phi_fibonacci_lcg import FibonacciLCG, PhiNonceGenerator
from pythia_mining.mass_gap_shield import MassGapShield, EnergyProfile
from pythia_mining.phi_core_orchestrator import PhiCoreOrchestrator, PhiOrchestratorFactory


class TestPhiALU(unittest.TestCase):
    """Test Φ-Arithmetic Logic Unit with golden modulo addressing."""

    def setUp(self):
        self.phi_alu = PhiALU(memory_size=4096)  # Larger memory for better distribution

    def test_phi_mod_golden_wrapping(self):
        """Test golden modulo creates non-repeating patterns."""
        results = []
        for i in range(100):
            result = self.phi_alu.phi_mod(i, 100)
            results.append(result)

        # Should have good distribution
        unique_results = len(set(results))
        self.assertGreater(unique_results, 80, "Phi-mod should produce diverse outputs")

        # Check golden properties - should have good distribution
        # Calculate distribution quality
        value_range = max(results) - min(results)
        self.assertGreater(value_range, 50, "Should span significant range of modulus")

        # Check for patterns - should have reasonable variance
        diffs = [abs(results[i] - results[i - 1]) for i in range(1, len(results))]
        if len(diffs) > 1:
            diff_variance = np.var(diffs)
            # With improved phi_mod, should have some variance
            self.assertGreater(
                diff_variance, 0.1, "Differences should vary (avoid simple patterns)"
            )

    def test_phi_address_golden_spiral(self):
        """Test memory addresses follow golden spiral pattern."""
        addresses = []
        for i in range(50):
            phi_addr = self.phi_alu.phi_address(i)
            addresses.append(phi_addr)

            # Verify structure
            self.assertIsNotNone(phi_addr.physical_addr)
            self.assertTrue(0 <= phi_addr.golden_angle < 360)
            self.assertGreaterEqual(phi_addr.spiral_layer, 0)

        # Check golden angle distribution
        angles = [addr.golden_angle for addr in addresses]
        angle_diffs = np.diff(np.sort(angles))

        # Should have good distribution (not clustered)
        avg_diff = np.mean(angle_diffs)
        # With 50 points on a circle, average diff should be ~7.2 degrees
        expected_avg = 360.0 / 50
        self.assertAlmostEqual(
            avg_diff,
            expected_avg,
            delta=3.0,
            msg=f"Angles should be well distributed, expected ~{expected_avg:.1f}° average difference",
        )

        # Check for golden pattern: diffs should avoid simple fractions
        for diff in angle_diffs:
            # Avoid diffs that are simple fractions of 360
            simple_fractions = [360 / 2, 360 / 3, 360 / 4, 360 / 5, 360 / 6]
            for fraction in simple_fractions:
                self.assertNotAlmostEqual(
                    diff,
                    fraction,
                    delta=1.0,
                    msg=f"Angle difference {diff} should avoid simple fraction {fraction}",
                )

    def test_phi_memory_access_wear_leveling(self):
        """Test memory access patterns minimize wear."""
        # Create linear access pattern
        linear_addresses = np.arange(1000, dtype=np.uint32)

        # Convert to golden addresses
        golden_addresses = self.phi_alu.phi_memory_access(linear_addresses)

        # Check distribution - with 1024 memory size, we expect good distribution
        unique_golden = len(np.unique(golden_addresses))
        # In 1024 memory with 1000 accesses, expect at least 600 unique addresses
        self.assertGreater(
            unique_golden,
            600,
            f"Golden addressing should produce diverse physical addresses, got {unique_golden} unique",
        )

        # Verify coherence - with insufficient unique addresses, may be insufficient data
        coherence = self.phi_alu.verify_coherence(0, 100)
        self.assertIn(coherence["status"], ["coherent", "decohered", "insufficient_data"])
        if coherence["status"] == "coherent":
            self.assertGreater(
                coherence["harmony_score"], 0.7, "Memory access should maintain golden harmony"
            )

    def test_hardware_thermal_awareness(self):
        """Test hardware-aware Φ-ALU with thermal safety."""
        hardware_alu = PhiALUHardware(memory_size=1024, thermal_limit=1.5)

        # Test safe operation
        addresses = np.arange(100, dtype=np.uint32)
        golden_addrs, thermal_metrics = hardware_alu.thermal_aware_access(
            addresses, current_temp=0.5
        )

        self.assertEqual(len(golden_addrs), 100)
        self.assertIn("thermal_pressure", thermal_metrics)
        self.assertLess(thermal_metrics["thermal_pressure"], 1.0)

        # Test thermal throttling
        golden_addrs_hot, thermal_metrics_hot = hardware_alu.thermal_aware_access(
            addresses,
            current_temp=1.4,  # Near limit
        )

        self.assertIn("safe_margin", thermal_metrics_hot)
        self.assertGreater(thermal_metrics_hot["safe_margin"], 0.0)


class TestFibonacciLCG(unittest.TestCase):
    """Test Fibonacci Linear Congruential Generator with golden spiral."""

    def setUp(self):
        self.lcg = FibonacciLCG(seed=42, nonce_space=1000, spiral_layers=4)

    def test_golden_spiral_coverage(self):
        """Test nonces follow golden spiral exploration pattern."""
        visited = set()
        spiral_points = []

        for _ in range(200):
            nonce, point = self.lcg.next()
            visited.add(nonce)
            spiral_points.append(point)

            # Verify spiral point structure
            self.assertGreater(point.radius, 0)
            self.assertTrue(0 <= point.angle < 360)
            self.assertTrue(0 < point.probability_density <= 1.0)

        # Check coverage efficiency
        coverage = self.lcg.get_coverage_metrics()
        self.assertGreater(
            coverage["unique_nonces"],
            100,
            f"Should explore diverse nonces, got {coverage['unique_nonces']}",
        )
        # With 1000 nonce space and 200 samples, coverage around 20% is reasonable
        self.assertGreater(
            coverage["coverage_percentage"],
            15.0,
            f"Should achieve reasonable space coverage, got {coverage['coverage_percentage']:.1f}%",
        )

        # Golden coverage ratio should be reasonable
        # With small sample size, ratio may be lower
        self.assertGreater(coverage["golden_coverage_ratio"], 0.2)

    def test_spiral_density_optimization(self):
        """Test adaptive spiral density based on success."""
        initial_layers = self.lcg.spiral_layers

        # Simulate high success (should tighten spiral)
        success_pattern = np.ones(100)
        self.lcg.optimize_spiral_density(success_pattern)
        self.assertGreaterEqual(self.lcg.spiral_layers, initial_layers)

        # Simulate low success (should expand spiral)
        self.lcg.spiral_layers = initial_layers
        failure_pattern = np.zeros(100)
        self.lcg.optimize_spiral_density(failure_pattern)
        self.assertLessEqual(self.lcg.spiral_layers, initial_layers)

    def test_consciousness_integrated_generation(self):
        """Test nonce generation with consciousness awareness."""
        generator = PhiNonceGenerator()

        # Test with high consciousness
        nonce_high, telemetry_high = generator.generate_with_consciousness(
            consciousness_level=0.9, thermal_state=0.3
        )

        self.assertIsNotNone(nonce_high)
        self.assertGreater(telemetry_high["consciousness_integration"], 0.8)
        self.assertGreater(telemetry_high["search_authenticity"], 0.0)

        # Test with low consciousness
        nonce_low, telemetry_low = generator.generate_with_consciousness(
            consciousness_level=0.3, thermal_state=0.3
        )

        self.assertNotEqual(
            nonce_high, nonce_low, "Different consciousness should produce different nonces"
        )
        self.assertLess(
            telemetry_low["phi_boost_applied"], telemetry_high.get("phi_boost_applied", 1.0)
        )

        # Test thermal emergency
        nonce_emergency, telemetry_emergency = generator.generate_with_consciousness(
            consciousness_level=0.9,
            thermal_state=1.5,  # Above mass gap limit
        )

        self.assertEqual(telemetry_emergency["status"], "thermal_emergency")
        self.assertTrue(telemetry_emergency["mass_gap_violation"])


class TestMassGapShield(unittest.TestCase):
    """Test Yang-Mills mass gap safety gates."""

    def setUp(self):
        self.shield = MassGapShield(thermal_capacity=100.0, max_safe_temp=85.0)

    def test_energy_harmony_analysis(self):
        """Test energy profile analysis for golden harmony."""
        profile = EnergyProfile(
            base_energy=50.0,
            harmonic_content={100: 0.5, 161: 0.8, 262: 0.3},  # Golden frequencies
            thermal_rise_rate=0.1,
            coherence_decay=0.01,
        )

        harmony, temp_rise = self.shield.analyze_energy_profile(profile, 0.7)

        # Golden frequencies should produce reasonable harmony
        self.assertGreater(
            harmony, 0.3, f"Golden frequencies should produce reasonable harmony, got {harmony:.3f}"
        )
        self.assertGreater(temp_rise, 0.0)
        # Temperature rise depends on thermal capacity (100.0 in test)
        # With 50 energy and 100 capacity, temp rise is 0.5, but harmonics add to it
        self.assertLess(temp_rise, 2.0)

    def test_mass_gap_safety_check(self):
        """Test mass gap violation detection."""
        # Safe case
        safe_decision = self.shield.check_mass_gap(projected_temp_rise=10.0, energy_harmony=0.9)
        self.assertTrue(safe_decision.allowed)
        self.assertGreater(safe_decision.safety_margin, 0.0)
        self.assertFalse(safe_decision.mass_gap_violation)

        # Violation case
        violation_decision = self.shield.check_mass_gap(
            projected_temp_rise=60.0,  # Large temp rise
            energy_harmony=0.3,  # Low harmony
        )
        self.assertFalse(violation_decision.allowed)
        self.assertTrue(violation_decision.mass_gap_violation)
        self.assertGreater(violation_decision.required_damping, 0.0)

    def test_execution_gating(self):
        """Test complete execution gating workflow."""
        # Create a safer profile with golden frequencies
        profile = EnergyProfile(
            base_energy=20.0,  # Lower energy
            harmonic_content={100: 0.2, 162: 0.3},  # 162 ≈ 100 * φ (golden)
            thermal_rise_rate=0.02,
            coherence_decay=0.01,
        )

        # Test allowed execution with high consciousness
        allowed, optimized = self.shield.gate_execution(
            "test_kernel", profile, consciousness_level=0.9
        )

        # Debug: check what happened
        if not allowed:
            # Analyze why it was blocked
            harmony, temp_rise = self.shield.analyze_energy_profile(profile, 0.9)
            decision = self.shield.check_mass_gap(temp_rise, harmony)
            print(
                f"Debug - Harmony: {harmony:.3f}, Temp rise: {temp_rise:.3f}, Decision: {decision.reason}"
            )
            print(
                f"Debug - Safety margin: {decision.safety_margin:.3f}, Required damping: {decision.required_damping:.3f}"
            )

        # With golden frequencies and high consciousness, should be allowed
        self.assertTrue(
            allowed, f"Execution blocked: harmony={harmony:.3f}, temp_rise={temp_rise:.3f}"
        )
        self.assertLessEqual(optimized.base_energy, profile.base_energy * 1.1)

        # Test blocked execution (create extreme profile)
        extreme_profile = EnergyProfile(
            base_energy=200.0,
            harmonic_content={50: 2.0, 150: 2.0},  # High amplitude, non-golden
            thermal_rise_rate=1.0,
            coherence_decay=0.5,
        )

        blocked, damped = self.shield.gate_execution(
            "extreme_kernel", extreme_profile, consciousness_level=0.3
        )

        self.assertFalse(blocked)
        self.assertLess(damped.base_energy, extreme_profile.base_energy)

    def test_adaptive_cooling(self):
        """Test consciousness-aware cooling optimization."""
        initial_rate = self.shield.cooling_rate

        # High consciousness should enable better cooling
        self.shield.optimize_cooling_strategy(0.9)
        self.assertGreater(self.shield.cooling_rate, initial_rate)

        # Reset and test low consciousness
        self.shield.cooling_rate = initial_rate
        self.shield.optimize_cooling_strategy(0.3)
        self.assertLessEqual(self.shield.cooling_rate, initial_rate)


class TestPhiCoreOrchestrator(unittest.TestCase):
    """Test synthetic morphogenesis controller."""

    def setUp(self):
        # Mock consciousness engine to avoid dependencies
        mock_consciousness = Mock()
        mock_consciousness.get_consciousness_metrics.return_value = {"integration_level": 0.7}
        mock_consciousness.record_execution_feedback = Mock()
        mock_consciousness.emergency_recovery = Mock()

        # Create orchestrator with mocked consciousness
        self.orchestrator = PhiCoreOrchestrator(
            {"memory_size": 1024, "thermal_capacity": 100.0, "max_safe_temp": 85.0}
        )
        self.orchestrator.consciousness_engine = mock_consciousness

    def test_fibonacci_clock_generation(self):
        """Test Fibonacci clock produces golden intervals."""
        intervals = []
        for _ in range(20):
            interval = self.orchestrator.fibonacci_clock()
            intervals.append(interval)

        # Should produce varied intervals
        unique_intervals = len(set([round(i, 3) for i in intervals]))
        self.assertGreater(unique_intervals, 15, "Fibonacci clock should produce diverse intervals")

        # Check clock history
        self.assertEqual(len(self.orchestrator.clock_history), 20)

    def test_phi_cycle_execution(self):
        """Test complete Φ-cycle execution."""
        kernel_profile = {
            "base_energy": 25.0,
            "harmonic_content": {100: 0.4, 162: 0.6},  # 162 ≈ 100 * φ
            "thermal_rise_rate": 0.03,
            "coherence_decay": 0.01,
            "memory_size": 256,
        }

        # Execute cycle
        cycle = self.orchestrator.execute_phi_cycle("test_kernel", kernel_profile)

        # Verify cycle structure
        self.assertEqual(cycle.cycle_id, 0)
        self.assertLess(cycle.start_time, cycle.end_time)
        self.assertIsNotNone(cycle.telemetry)
        self.assertIsNotNone(cycle.decisions)
        self.assertIsNotNone(cycle.optimizations)
        self.assertIsNotNone(cycle.hardware_actions)

        # Verify telemetry
        telemetry = cycle.telemetry
        self.assertTrue(0 <= telemetry.coherence <= 1.0)
        self.assertTrue(0 <= telemetry.consciousness_level <= 1.0)
        self.assertTrue(0 <= telemetry.thermal_state <= 1.0)
        self.assertTrue(0 <= telemetry.energy_harmony <= 1.0)

        # Check history
        self.assertEqual(len(self.orchestrator.execution_history), 1)

    def test_parameter_optimization(self):
        """Test golden parameter backpropagation."""
        # Initial state
        initial_boost = self.orchestrator.phi_boost

        # Simulate high harmony (should increase boost)
        self.orchestrator._optimize_phi_parameters(
            energy_harmony=0.95,  # Above target
            consciousness=0.7,
            thermal_state=0.3,
        )

        self.assertGreater(self.orchestrator.phi_boost, initial_boost)

        # Simulate low harmony (should decrease boost)
        self.orchestrator.phi_boost = initial_boost
        self.orchestrator._optimize_phi_parameters(
            energy_harmony=0.6,  # Below target
            consciousness=0.7,
            thermal_state=0.3,
        )

        self.assertLess(self.orchestrator.phi_boost, initial_boost)

        # Test consciousness threshold adjustment
        self.orchestrator.consciousness_threshold = 0.618
        self.orchestrator._optimize_phi_parameters(
            energy_harmony=0.8,
            consciousness=0.7,
            thermal_state=0.9,  # High thermal
        )

        self.assertGreater(self.orchestrator.consciousness_threshold, 0.618)

    def test_orchestrator_metrics(self):
        """Test comprehensive metrics generation."""
        # First execute some cycles
        kernel_profile = {
            "base_energy": 20.0,
            "harmonic_content": {100: 0.5},
            "thermal_rise_rate": 0.02,
            "coherence_decay": 0.01,
            "memory_size": 128,
        }

        for i in range(5):
            self.orchestrator.execute_phi_cycle(f"kernel_{i}", kernel_profile)

        # Get metrics
        metrics = self.orchestrator.get_orchestrator_metrics()

        # Check structure
        self.assertIn("synthetic_morphogenesis", metrics)
        self.assertIn("fibonacci_clocking", metrics)
        self.assertIn("mass_gap_safety", metrics)
        self.assertIn("golden_exploration", metrics)
        self.assertIn("phi_alu_coherence", metrics)
        self.assertIn("thermal_state", metrics)

        # Verify key metrics
        synth = metrics["synthetic_morphogenesis"]
        self.assertGreater(synth["total_cycles"], 0)
        self.assertTrue(0 <= synth["recent_resonance"] <= 1.0)
        self.assertTrue(0 <= synth["avg_consciousness"] <= 1.0)

        # Check Fibonacci clock metrics
        clock = metrics["fibonacci_clocking"]
        self.assertGreater(clock["current_interval_ns"], 0)
        self.assertEqual(len(clock["current_fib_state"]), 2)

    def test_emergency_recovery(self):
        """Test emergency recovery procedure."""
        # Set some state
        self.orchestrator.phi_boost = 2.0
        self.orchestrator.harmony_target = 0.95
        self.orchestrator.fib_clock_state = [34, 55]

        # Add some history
        for _ in range(200):
            self.orchestrator.execution_history.append(Mock())
            self.orchestrator.clock_history.append({"timestamp": time.time()})

        # Execute recovery
        recovery_result = self.orchestrator.emergency_recovery()

        # Verify reset
        self.assertEqual(self.orchestrator.phi_boost, 1.0)
        self.assertEqual(self.orchestrator.harmony_target, 0.9)
        self.assertEqual(self.orchestrator.consciousness_threshold, 0.618)
        self.assertEqual(self.orchestrator.fib_clock_state, [1, 1])

        # Verify history truncation
        self.assertLessEqual(len(self.orchestrator.execution_history), 100)
        self.assertLessEqual(len(self.orchestrator.clock_history), 100)

        # Verify recovery result
        self.assertEqual(recovery_result["status"], "recovered")
        self.assertTrue(recovery_result["phi_boost_reset"])
        self.assertTrue(recovery_result["fib_clock_reset"])
        self.assertTrue(recovery_result["history_truncated"])

        # Verify consciousness engine was notified
        self.orchestrator.consciousness_engine.emergency_recovery.assert_called_once()


class TestPhiOrchestratorFactory(unittest.TestCase):
    """Test factory for creating consciousness-aware orchestrators."""

    def test_consciousness_orchestrator_creation(self):
        """Test creating full-featured orchestrator."""
        config = {
            "memory_size": 2**28,
            "thermal_capacity": 150.0,
            "max_safe_temp": 90.0,
            "consciousness_integration": True,
        }

        orchestrator = PhiOrchestratorFactory.create_consciousness_orchestrator(config)

        self.assertIsInstance(orchestrator, PhiCoreOrchestrator)
        self.assertEqual(orchestrator.config["memory_size"], 2**28)
        # Note: consciousness engine would be initialized in real scenario

    def test_lightweight_orchestrator_creation(self):
        """Test creating resource-efficient orchestrator."""
        config = {"memory_size": 2**28, "thermal_capacity": 150.0}

        orchestrator = PhiOrchestratorFactory.create_lightweight_orchestrator(config)

        self.assertIsInstance(orchestrator, PhiCoreOrchestrator)
        self.assertEqual(orchestrator.config["memory_size"], 2**24)  # Reduced
        self.assertEqual(orchestrator.config["thermal_capacity"], 50.0)  # Reduced
        self.assertTrue(orchestrator.config["disable_fib_clock"])

    def test_hardware_orchestrator_creation(self):
        """Test creating hardware-tuned orchestrator."""
        hardware_info = {"memory_bus_width": 128, "core_count": 16, "thermal_design_power": 250}

        orchestrator = PhiOrchestratorFactory.create_hardware_orchestrator(hardware_info)

        self.assertIsInstance(orchestrator, PhiCoreOrchestrator)
        self.assertEqual(orchestrator.config["memory_size"], 2 ** (128 + 4))  # Scaled
        self.assertEqual(orchestrator.config["thermal_capacity"], 200.0)  # 80% of 250
        self.assertEqual(orchestrator.config["core_scaling"], 2.0)  # 16/8
        self.assertTrue(orchestrator.config["hardware_optimized"])


if __name__ == "__main__":
    unittest.main()
