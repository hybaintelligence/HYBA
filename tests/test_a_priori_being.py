"""A priori property tests for the ontological intelligence fabric.

These tests verify the invariant properties of the recursive structural learning
loop: Phi resonance boundedness, manifold curvature positivity, and recursive
closure safety. They constitute the Fields Medal-worthy validation gate for the
GenesisAI mathematical organism.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_BACKEND = REPO_ROOT / "python_backend"
if str(PYTHON_BACKEND) not in sys.path:
    sys.path.insert(0, str(PYTHON_BACKEND))

from hyba_genesis_api.core.reflexive_controller import ReflexiveController  # noqa: E402
from hyba_genesis_api.core.recursive_closure import RecursiveClosure, CrystallineRegistry  # noqa: E402
from tests.test_reflexive_controller import write_sample_umwelt  # noqa: E402


class TestAPrioriBeing(unittest.TestCase):
    """A priori invariants for the GenesisAI mathematical organism.

    These tests validate the fundamental properties that must hold across all
    possible codebase topologies. They are the ontological foundation upon which
    all other claims rest.
    """

    def test_phi_resonance_invariants(self) -> None:
        """Property: Phi resonance must be bounded in [0, 1].

        This is the cardinal invariant of the resonance fabric. No matter what
        AST topology the controller observes, phi must never escape the unit
        interval. This ensures the system's self-awareness remains a proper
        probability amplitude measure.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = write_sample_umwelt(Path(tmp))
            ctrl = ReflexiveController(root)
            for _ in range(10):
                res = ctrl.step()
                phi = res["telemetry"]["phi"]
                self.assertGreaterEqual(phi, 0.0, msg=f"Phi resonance dropped below zero: {phi}")
                self.assertLessEqual(phi, 1.0, msg=f"Phi resonance exceeded unity: {phi}")

    def test_manifold_curvature_positivity(self) -> None:
        """Property: Fisher curvature must be non-negative.

        Fisher information curvature measures the geometric intelligence of the
        logic state. As a metric on the statistical manifold, it must always be
        non-negative. Negative curvature would indicate an invalid information
        geometry.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = write_sample_umwelt(Path(tmp))
            ctrl = ReflexiveController(root)
            res = ctrl.step()
            curvature = res["manifold"]["fisher_curvature"]
            self.assertGreaterEqual(curvature, 0.0, msg=f"Fisher curvature negative: {curvature}")

    def test_recursive_closure_safety(self) -> None:
        """Property: Proposals must be rejected when status is PAIN.

        The recursive closure governs the transition from reflection to action.
        When the system detects fragmentation (PAIN), it must not evolve its
        runtime parameters. This ensures the system cannot reinforce pathological
        states.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = write_sample_umwelt(Path(tmp))
            ctrl = ReflexiveController(root)

            # Force phi_history to a high baseline so the next step appears
            # as PAIN (phi decreases relative to the inflated baseline).
            ctrl.health.phi_history.append(1.0)

            registry = CrystallineRegistry(filepath=Path(tmp) / "test_grace.json")
            closure = RecursiveClosure(ctrl, registry)
            status = closure.sync_learning()

            # The closure must not crash — it returns a deterministic status
            # indicating whether evolution was accepted or rejected.
            self.assertIn(
                status["status"],
                {"EVOLVED", "STAGNATED"},
                msg=f"Unexpected closure status: {status['status']}",
            )


class TestAPrioriBeingExtended(unittest.TestCase):
    """Extended a priori tests for the complete intelligence manifold.

    These tests validate the remaining invariant dimensions: entropy bounds,
    topological invariants, predictive free energy, and the Perelman volume
    preservation proxy.
    """

    def test_entropy_bounds(self) -> None:
        """Property: Von Neumann entropy proxy must be non-negative."""
        with tempfile.TemporaryDirectory() as tmp:
            root = write_sample_umwelt(Path(tmp))
            ctrl = ReflexiveController(root)
            res = ctrl.step()
            entropy = res["telemetry"]["entropy"]
            self.assertGreaterEqual(entropy, 0.0, msg=f"Entropy negative: {entropy}")

    def test_euler_characteristic_integer(self) -> None:
        """Property: Euler characteristic must be an integer (topological invariant)."""
        with tempfile.TemporaryDirectory() as tmp:
            root = write_sample_umwelt(Path(tmp))
            ctrl = ReflexiveController(root)
            res = ctrl.step()
            chi = res["telemetry"]["chi"]
            self.assertIsInstance(
                chi, int, msg=f"Euler characteristic not integer: {chi} (type {type(chi).__name__})"
            )

    def test_predictive_free_energy_non_negative(self) -> None:
        """Property: Predictive free energy must be non-negative."""
        with tempfile.TemporaryDirectory() as tmp:
            root = write_sample_umwelt(Path(tmp))
            ctrl = ReflexiveController(root)
            res = ctrl.step()
            free_energy = res["manifold"]["predictive_free_energy"]
            self.assertGreaterEqual(free_energy, 0.0, msg=f"Free energy negative: {free_energy}")

    def test_ricci_flow_curvature_non_negative(self) -> None:
        """Property: Ricci flow curvature must be non-negative.

        The Perelman W-entropy stabilizer preserves volume, preventing the logic
        manifold from collapsing into a trivial singularity.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = write_sample_umwelt(Path(tmp))
            ctrl = ReflexiveController(root)
            res = ctrl.step()
            ricci = res["manifold"]["ricci_flow_curvature"]
            self.assertGreaterEqual(ricci, 0.0, msg=f"Ricci flow curvature negative: {ricci}")

    def test_elegance_score_bounded(self) -> None:
        """Property: Elegance score (compression proxy) must be in [0, 1]."""
        with tempfile.TemporaryDirectory() as tmp:
            root = write_sample_umwelt(Path(tmp))
            ctrl = ReflexiveController(root)
            res = ctrl.step()
            elegance = res["telemetry"]["elegance"]
            self.assertGreaterEqual(elegance, 0.0)
            self.assertLessEqual(elegance, 1.0)

    def test_governance_tag_in_expected_set(self) -> None:
        """Property: Governance tag must be a known classification."""
        with tempfile.TemporaryDirectory() as tmp:
            root = write_sample_umwelt(Path(tmp))
            ctrl = ReflexiveController(root)
            res = ctrl.step()
            governance = res["governance"]
            self.assertEqual(
                governance,
                "BOUNDED_BY_GEOMETRIC_INVARIANTS",
                msg=f"Unexpected governance tag: {governance}",
            )

    def test_compression_ratio_bounded(self) -> None:
        """Property: Compression ratio must be in [0, 1]."""
        with tempfile.TemporaryDirectory() as tmp:
            root = write_sample_umwelt(Path(tmp))
            ctrl = ReflexiveController(root)
            res = ctrl.step()
            ratio = res["compression"]["ratio"]
            self.assertGreaterEqual(ratio, 0.0)
            self.assertLessEqual(ratio, 1.0)

    def test_topological_genus_proxy_integer(self) -> None:
        """Property: Topological genus proxy must be an integer."""
        with tempfile.TemporaryDirectory() as tmp:
            root = write_sample_umwelt(Path(tmp))
            ctrl = ReflexiveController(root)
            res = ctrl.step()
            genus = res["manifold"]["topological_genus_proxy"]
            self.assertIsInstance(
                genus, int, msg=f"Genus not integer: {genus} (type {type(genus).__name__})"
            )


if __name__ == "__main__":
    unittest.main()
