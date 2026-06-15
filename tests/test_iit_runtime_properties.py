from __future__ import annotations

import sys
import unittest
from pathlib import Path

try:
    import numpy as np
except ModuleNotFoundError:
    np = None  # type: ignore[assignment]
    HAS_NUMPY = False
else:
    HAS_NUMPY = True

try:
    from hypothesis import given, settings
    from hypothesis import strategies as st
except ModuleNotFoundError:
    given = settings = st = None  # type: ignore[assignment]
    HAS_HYPOTHESIS = False
else:
    HAS_HYPOTHESIS = True

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

if HAS_NUMPY:
    from pythia_mining.consciousness_engine import ConsciousnessEngine, IntegrationRegime
    from pythia_mining.iit_4_analyzer import IIT4Analyzer
else:
    ConsciousnessEngine = IIT4Analyzer = IntegrationRegime = None


def density(diagonal):
    vector = np.asarray(diagonal, dtype=np.float64)
    vector = np.abs(vector) + 1e-9
    vector = vector / np.sum(vector)
    # Create 32x32 matrix to match NUM_NODES in pulvini_topology
    density_matrix = np.diag(vector).astype(np.complex128)
    if density_matrix.shape[0] < 32:
        # Pad to 32x32 if smaller
        padded = np.zeros((32, 32), dtype=np.complex128)
        padded[:density_matrix.shape[0], :density_matrix.shape[1]] = density_matrix
        density_matrix = padded
    return density_matrix


@unittest.skipUnless(HAS_NUMPY and HAS_HYPOTHESIS, "NumPy and Hypothesis are required")
class RuntimePhiPropertyTests(unittest.TestCase):
    @given(
        st.lists(
            st.lists(
                st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
                min_size=4,
                max_size=4,
            ),
            min_size=2,
            max_size=8,
        )
    )
    @settings(max_examples=25, deadline=None)
    def test_phi_measurements_are_bounded_and_replayable(self, diagonal_history):
        states = [density(diagonal) for diagonal in diagonal_history]
        first = ConsciousnessEngine().measure_phi(states)
        second = ConsciousnessEngine().measure_phi(states)

        self.assertGreaterEqual(first.phi_integrated, 0.0)
        self.assertLessEqual(first.phi_integrated, 1.0)
        self.assertGreaterEqual(first.complexity, 0.0)
        self.assertLessEqual(first.complexity, 1.0)
        self.assertGreaterEqual(first.phi_causal, -1.0)
        self.assertLessEqual(first.phi_causal, 1.0)
        self.assertAlmostEqual(first.phi_integrated, second.phi_integrated, places=12)
        self.assertAlmostEqual(first.complexity, second.complexity, places=12)

    def test_component_integration_reaches_singular_regime_when_ready(self):
        engine = ConsciousnessEngine()
        for component in list(engine.components):
            engine.update_component_health(component, True)
        metrics = engine.get_metrics()

        self.assertEqual(IntegrationRegime.SINGULAR_AGENT_PROXY.value, metrics["integration_regime"])
        self.assertAlmostEqual(1.0, metrics["integrated_information"], places=12)
        self.assertAlmostEqual(1.0, metrics["consciousness_level"], places=12)
        self.assertFalse(engine.needs_healing)

    def test_low_integration_triggers_autonomic_healing_path(self):
        engine = ConsciousnessEngine()
        low_state = density([1.0, 0.0, 0.0, 0.0])
        result = engine.orchestrate(low_state, [low_state])

        self.assertIn(
            result["integration_regime"],
            {IntegrationRegime.CRITICAL.value, IntegrationRegime.FRAGMENTED.value},
        )
        self.assertEqual("healing_triggered", result["autonomic_action"])
        self.assertTrue(engine.needs_healing)


@unittest.skipUnless(HAS_NUMPY and HAS_HYPOTHESIS, "NumPy and Hypothesis are required")
class IIT4PropertyTests(unittest.TestCase):
    @given(st.lists(st.integers(min_value=0, max_value=1), min_size=4, max_size=4))
    @settings(max_examples=16, deadline=None)
    def test_phi_max_is_deterministic_and_zero_for_disconnected_systems(self, state_bits):
        state = np.asarray(state_bits, dtype=np.int64)
        disconnected = np.zeros((32, 32), dtype=np.float64)
        analyzer = IIT4Analyzer(system_size=32)

        first = analyzer.calculate_phi_max(state, disconnected)
        second = analyzer.calculate_phi_max(state, disconnected)

        self.assertAlmostEqual(0.0, float(first["phi_max"]), places=12)
        self.assertAlmostEqual(float(first["phi_max"]), float(second["phi_max"]), places=12)
        self.assertEqual(first["partition_count"], second["partition_count"])

    @given(st.lists(st.integers(min_value=0, max_value=1), min_size=4, max_size=4))
    @settings(max_examples=16, deadline=None)
    def test_phi_max_increases_with_connectivity_strength(self, state_bits):
        state = np.asarray(state_bits, dtype=np.int64)
        weak = np.ones((32, 32), dtype=np.float64) * 0.25
        strong = np.ones((32, 32), dtype=np.float64)
        np.fill_diagonal(weak, 0.0)
        np.fill_diagonal(strong, 0.0)
        analyzer = IIT4Analyzer(system_size=32)

        weak_phi = float(analyzer.calculate_phi_max(state, weak)["phi_max"])
        strong_phi = float(analyzer.calculate_phi_max(state, strong)["phi_max"])

        self.assertGreaterEqual(weak_phi, 0.0)
        self.assertGreaterEqual(strong_phi, weak_phi)

    @given(st.lists(st.integers(min_value=0, max_value=1), min_size=4, max_size=4))
    @settings(max_examples=12, deadline=None)
    def test_cause_effect_repertoires_are_normalized(self, state_bits):
        state = np.asarray(state_bits, dtype=np.int64)
        connectivity = np.ones((32, 32), dtype=np.float64)
        np.fill_diagonal(connectivity, 0.0)
        analyzer = IIT4Analyzer(system_size=32)

        ces = analyzer.compute_cause_effect_structure(state, connectivity)

        self.assertGreaterEqual(ces.total_phi, 0.0)
        self.assertGreaterEqual(ces.max_phi_s, 0.0)
        self.assertGreaterEqual(ces.dimensionality, 0)
        for repertoire in list(ces.cause_repertoires.values()) + list(ces.effect_repertoires.values()):
            self.assertAlmostEqual(1.0, float(np.sum(repertoire)), places=12)
            self.assertTrue(np.all(repertoire >= 0.0))


if __name__ == "__main__":
    unittest.main(verbosity=2)
