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

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

if HAS_NUMPY:
    from pythia_mining.pulvini_autonomics import (  # noqa: E402
        AutonomicOrchestrator,
        BuresOptimizer,
        DodecahedronIcosahedronCompound,
        ManifoldHomeostasis,
        NodeTelemetry,
        PulviniAutonomicsEngine,
        ReducedDensityMatrix,
        ThermalGovernor,
    )
else:
    AutonomicOrchestrator = BuresOptimizer = DodecahedronIcosahedronCompound = (
        ManifoldHomeostasis
    ) = None
    NodeTelemetry = PulviniAutonomicsEngine = ReducedDensityMatrix = ThermalGovernor = (
        None
    )


def healthy_telemetry(
    node_id: int, *, hash_rate: float = 1000.0, watts: float = 100.0
) -> NodeTelemetry:
    return NodeTelemetry(
        node_id=node_id,
        tres=25.0,
        phi_eff=0.95,
        chi_sync=0.92,
        thermal_entropy=watts,
        hash_rate=hash_rate,
    )


@unittest.skipUnless(HAS_NUMPY, "NumPy is required for PULVINI autonomics tests")
class PulviniAutonomicsUnitTests(unittest.TestCase):
    def test_di_compound_uses_exact_phase_one_degree_profile(self) -> None:
        compound = DodecahedronIcosahedronCompound()
        proof = compound.redundancy_proof()
        self.assertEqual(120, proof["total_degree"])
        self.assertAlmostEqual(3.75, proof["redundancy_factor"])
        self.assertTrue(proof["verified"])
        self.assertTrue(proof["bipartite"])
        self.assertTrue(np.all(compound.degrees[:20] == 3))
        self.assertTrue(np.all(compound.degrees[20:] == 5))

    def test_telemetry_validation_and_threshold_detection(self) -> None:
        compound = DodecahedronIcosahedronCompound()
        homeostasis = ManifoldHomeostasis(compound)
        homeostasis.update_telemetry(0, healthy_telemetry(0))
        homeostasis.update_telemetry(
            1,
            NodeTelemetry(
                node_id=1,
                tres=250.0,
                phi_eff=0.05,
                chi_sync=0.02,
                thermal_entropy=500.0,
                hash_rate=50.0,
            ),
        )
        self.assertNotIn(0, homeostasis.monitor_heartbeat())
        self.assertIn(1, homeostasis.monitor_heartbeat())
        with self.assertRaises(ValueError):
            NodeTelemetry(
                node_id=0,
                tres=-1,
                phi_eff=1.0,
                chi_sync=1.0,
                thermal_entropy=1.0,
                hash_rate=1.0,
            )

    def test_density_matrix_projection_and_amplitudes_are_invariants(self) -> None:
        rho = ReducedDensityMatrix(np.eye(32, dtype=np.complex128) * 2.0)
        rho.assert_invariants()
        amplitudes = np.zeros(32)
        amplitudes[7] = 10.0
        rho.set_amplitudes(amplitudes)
        rho.assert_invariants()
        self.assertAlmostEqual(1.0, rho.diagonal()[7])
        with self.assertRaises(ValueError):
            rho.set_amplitudes(np.zeros(32))

    def test_bures_optimizer_moves_mass_toward_efficient_live_nodes(self) -> None:
        engine = PulviniAutonomicsEngine()
        engine.ingest_telemetry(
            healthy_telemetry(node_id, hash_rate=1000.0 + 100.0 * node_id, watts=100.0)
            for node_id in range(32)
        )
        before = engine.homeostasis.rho.diagonal()
        after = engine.optimizer.find_bures_optima(learning_rate=0.25)
        self.assertGreater(float(np.sum(after[28:32])), float(np.sum(before[28:32])))
        self.assertAlmostEqual(1.0, float(np.sum(after)), places=12)


@unittest.skipUnless(HAS_NUMPY, "NumPy is required for PULVINI autonomics tests")
class PulviniThermalGovernorTests(unittest.TestCase):
    def test_energy_fade_zones_follow_first_principles_thresholds(self) -> None:
        governor = ThermalGovernor(warning_temp=0.70, critical_temp=0.95)
        self.assertEqual(1.0, governor.calculate_fade_factor(0.30))
        self.assertEqual(1.0, governor.calculate_fade_factor(100.0))
        self.assertAlmostEqual(
            1.0 - ((0.80 - 0.70) / (0.85 - 0.70)), governor.calculate_fade_factor(0.80)
        )
        self.assertAlmostEqual(
            np.exp(-10.0 * (0.90 - 0.85)), governor.calculate_fade_factor(0.90)
        )
        self.assertEqual(0.0, governor.calculate_fade_factor(0.98))

    def test_thermal_cascade_fades_icosahedron_hubs_to_dodecahedron_workers(
        self,
    ) -> None:
        governor = ThermalGovernor()
        rho = np.diag(np.ones(32, dtype=np.float64) / 32.0).astype(np.complex128)
        telemetry = [healthy_telemetry(node_id, watts=0.30) for node_id in range(32)]
        by_node = {item.node_id: item for item in telemetry}
        for node_id in range(20, 25):
            by_node[node_id] = NodeTelemetry(
                node_id=node_id,
                tres=25.0,
                phi_eff=0.95,
                chi_sync=0.92,
                thermal_entropy=0.90,
                hash_rate=1000.0,
            )
        by_node[31] = NodeTelemetry(
            node_id=31,
            tres=25.0,
            phi_eff=0.95,
            chi_sync=0.92,
            thermal_entropy=0.98,
            hash_rate=1000.0,
        )

        evolved_rho, event = governor.apply_thermal_governance(rho, by_node)
        amplitudes = np.real(np.diag(evolved_rho))

        self.assertAlmostEqual(1.0, float(np.sum(amplitudes)), places=12)
        self.assertGreater(event.rho_purity, 0.9)
        self.assertEqual([31], event.sacrificed_nodes)
        self.assertLess(float(amplitudes[20]), 1.0 / 32.0)
        self.assertEqual(0.0, float(amplitudes[31]))
        self.assertGreater(float(np.sum(amplitudes[:20])), 20.0 / 32.0)

    def test_thermal_sacrifice_bridges_to_silent_lattice_healing_once(self) -> None:
        lattice_commands = []
        engine = PulviniAutonomicsEngine(lattice_repoint_sink=lattice_commands.append)
        telemetry = [healthy_telemetry(node_id, watts=0.30) for node_id in range(32)]
        telemetry[31] = NodeTelemetry(
            node_id=31,
            tres=25.0,
            phi_eff=0.95,
            chi_sync=0.92,
            thermal_entropy=0.98,
            hash_rate=1000.0,
        )

        thermal_event, rebalance = engine.thermal_tick(telemetry)
        second_event, second_rebalance = engine.thermal_tick(telemetry)

        self.assertEqual([31], thermal_event.sacrificed_nodes)
        self.assertIsNotNone(rebalance)
        assert rebalance is not None
        self.assertTrue(rebalance.coverage_maintained)
        self.assertEqual([31], rebalance.failed_nodes)
        self.assertGreater(len(lattice_commands), 0)
        self.assertEqual([31], sorted(engine.sacrificed_nodes))
        self.assertEqual(0.0, float(engine.optimizer.target_distribution()[31]))
        self.assertEqual([31], second_event.sacrificed_nodes)
        self.assertIsNone(second_rebalance)

    def test_autonomic_orchestrator_exposes_bridge_controls(self) -> None:
        lattice_commands = []
        engine = PulviniAutonomicsEngine(lattice_repoint_sink=lattice_commands.append)
        orchestrator = AutonomicOrchestrator(engine)
        telemetry = [healthy_telemetry(node_id, watts=0.30) for node_id in range(32)]
        telemetry[30] = NodeTelemetry(
            node_id=30,
            tres=25.0,
            phi_eff=0.95,
            chi_sync=0.92,
            thermal_entropy=0.98,
            hash_rate=1000.0,
        )

        thermal_event, healing_event = orchestrator.tick(telemetry)

        self.assertEqual([30], thermal_event.sacrificed_nodes)
        self.assertIsNotNone(healing_event)
        self.assertIn(30, orchestrator.sacrificed_set)
        self.assertGreater(orchestrator.get_manifold_purity(), 0.0)
        self.assertGreater(len(lattice_commands), 0)


@unittest.skipUnless(HAS_NUMPY, "NumPy is required for PULVINI autonomics tests")
class PulviniAutonomicsIntegrationTests(unittest.TestCase):
    def test_engine_detects_five_failures_heals_and_emits_lattice_commands(
        self,
    ) -> None:
        audit_events = []
        lattice_commands = []
        engine = PulviniAutonomicsEngine(
            audit_sink=audit_events.append, lattice_repoint_sink=lattice_commands.append
        )
        failed = {0, 8, 15, 25, 30}
        telemetry = []
        for node_id in range(32):
            if node_id in failed:
                telemetry.append(
                    NodeTelemetry(
                        node_id=node_id,
                        tres=300.0,
                        phi_eff=0.01,
                        chi_sync=0.01,
                        thermal_entropy=450.0,
                        hash_rate=10.0,
                    )
                )
            else:
                telemetry.append(healthy_telemetry(node_id))
        engine.ingest_telemetry(telemetry)
        event = engine.heartbeat_and_heal(reason="integration_test")
        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(sorted(failed), event.failed_nodes)
        self.assertTrue(event.coverage_maintained)
        self.assertEqual(
            0.0, float(np.sum(engine.homeostasis.rho.diagonal()[list(failed)]))
        )
        self.assertGreater(len(lattice_commands), 0)
        self.assertTrue(
            any(
                item["event_type"] == "autonomic_critical_nodes_detected"
                for item in audit_events
            )
        )
        engine.homeostasis.rho.assert_invariants()

    def test_energy_envelope_updates_engine_snapshot(self) -> None:
        engine = PulviniAutonomicsEngine()
        engine.ingest_telemetry(
            healthy_telemetry(node_id, hash_rate=500.0 + node_id, watts=200.0 - node_id)
            for node_id in range(32)
        )
        event = engine.optimizer.optimize_energy_envelope(
            target_watts=100.0, learning_rate=0.1
        )
        snapshot = engine.snapshot()
        self.assertEqual("energy_constraint_triggered", event["action"])
        self.assertEqual("ok", snapshot["status"])
        self.assertAlmostEqual(1.0, snapshot["rho"]["trace"], places=12)
        self.assertEqual(1, len(snapshot["optimizations"]))


@unittest.skipUnless(HAS_NUMPY, "NumPy is required for PULVINI autonomics tests")
class PulviniAutonomicsPropertyAndEdgeTests(unittest.TestCase):
    def test_all_single_node_failures_redistribute_exactly_to_live_neighbors(
        self,
    ) -> None:
        for failed_node in range(32):
            engine = PulviniAutonomicsEngine()
            engine.ingest_telemetry(healthy_telemetry(node_id) for node_id in range(32))
            event = engine.rebalancer.rebalance_lattice_topology(
                failed_node, reason="property_single_failure"
            )
            fractions = event.redistribution[failed_node]
            self.assertAlmostEqual(1.0, sum(fractions.values()), places=12)
            self.assertTrue(event.coverage_maintained)
            self.assertEqual(0.0, engine.homeostasis.rho.diagonal()[failed_node])
            engine.homeostasis.rho.assert_invariants()

    def test_representative_five_failure_combinations_preserve_density_trace(
        self,
    ) -> None:
        combinations = [
            (0, 1, 2, 3, 4),
            (0, 8, 15, 25, 30),
            (20, 21, 22, 23, 24),
            (5, 11, 17, 26, 31),
            (2, 6, 13, 19, 28),
        ]
        for failed in combinations:
            engine = PulviniAutonomicsEngine()
            engine.ingest_telemetry(healthy_telemetry(node_id) for node_id in range(32))
            event = engine.rebalancer.rebalance_lattice_topology(
                failed, reason="property_five_failure"
            )
            self.assertTrue(event.coverage_maintained, failed)
            self.assertAlmostEqual(1.0, engine.homeostasis.rho.trace(), places=12)
            self.assertTrue(np.all(engine.homeostasis.rho.diagonal() >= -1e-12))

    def test_bures_learning_rate_edges_are_stable(self) -> None:
        engine = PulviniAutonomicsEngine()
        engine.ingest_telemetry(
            healthy_telemetry(node_id, hash_rate=100.0 + node_id, watts=50.0)
            for node_id in range(32)
        )
        current = engine.homeostasis.rho.diagonal().copy()
        self.assertTrue(
            np.allclose(current, engine.optimizer.find_bures_optima(learning_rate=0.0))
        )
        target = BuresOptimizer(
            engine.compound, engine.homeostasis
        ).target_distribution()
        self.assertTrue(
            np.allclose(target, engine.optimizer.find_bures_optima(learning_rate=1.0))
        )
        with self.assertRaises(ValueError):
            engine.optimizer.find_bures_optima(learning_rate=1.1)


@unittest.skipUnless(HAS_NUMPY, "NumPy is required for PULVINI autonomics tests")
class PulviniAutonomicsMiningIntegrationTests(unittest.TestCase):
    def test_overlay_generates_runtime_telemetry_and_repoints_failed_nonce_range(
        self,
    ) -> None:
        from pythia_mining.pulvini_overlay import (
            PulviniOverlayConcentrator,
            nonce_range_inclusive,
        )

        overlay = PulviniOverlayConcentrator(worker_name="PULVINI.singularity")
        job = type(
            "Job", (), {"job_id": "autonomic-job", "target": 1, "extranonce2_size": 4}
        )()
        overlay.register_pool_job(job, pool_name="Pool")
        overlay.record_node_progress(
            0, nonce_range_inclusive(0)[0] + 64, hashes=4096, best_diff=10
        )
        overlay.record_link_latency(0, 20, 0.002)

        telemetry = overlay.autonomic_telemetry(power_scale=1.5)
        self.assertEqual(32, len(telemetry))
        self.assertGreater(telemetry[0].hash_rate, 0.0)
        self.assertGreater(telemetry[0].thermal_entropy, 0.0)

        engine = PulviniAutonomicsEngine(
            lattice_repoint_sink=overlay.apply_lattice_repoint
        )
        engine.ingest_telemetry(telemetry)
        event = engine.rebalancer.rebalance_lattice_topology(
            0, reason="integration_repoint"
        )
        self.assertTrue(event.coverage_maintained)
        overlay_snapshot = overlay.snapshot()
        self.assertGreater(len(overlay_snapshot["healing_routes"]), 0)
        self.assertTrue(overlay_snapshot["healing_ranges_overlap_free"])
        reassigned = overlay.assignment_for_nonce(nonce_range_inclusive(0)[0] + 1)
        self.assertIsNotNone(reassigned)
        assert reassigned is not None
        self.assertNotEqual(0, reassigned.node_id)
        self.assertGreater(len(reassigned.healing_ranges), 0)

    def test_bures_distribution_updates_live_manifold_work_distribution(self) -> None:
        from pythia_mining.pulvini_overlay import PulviniOverlayConcentrator

        overlay = PulviniOverlayConcentrator(worker_name="PULVINI.singularity")
        job = type(
            "Job", (), {"job_id": "bures-job", "target": 1, "extranonce2_size": 4}
        )()
        overlay.register_pool_job(job, pool_name="Pool")
        engine = PulviniAutonomicsEngine()
        engine.ingest_telemetry(
            healthy_telemetry(node_id, hash_rate=100.0 + 50.0 * node_id, watts=100.0)
            for node_id in range(32)
        )
        before = overlay.manifold.work_distribution().copy()
        amplitudes = engine.optimizer.find_bures_optima(learning_rate=0.5)
        applied = overlay.apply_autonomic_distribution(
            amplitudes.tolist(), reason="test_bures"
        )
        after = overlay.manifold.work_distribution()

        self.assertAlmostEqual(1.0, sum(applied), places=12)
        self.assertGreater(float(np.sum(after[28:32])), float(np.sum(before[28:32])))
        self.assertIn(
            "autonomic_distribution_applied",
            [event["phase"] for event in overlay.snapshot()["lifecycle"]],
        )

    def test_three_node_wipeout_keeps_pool_identity_and_job_session_stable(
        self,
    ) -> None:
        from pythia_mining.pulvini_overlay import (
            PulviniOverlayConcentrator,
            nonce_range_inclusive,
        )

        overlay = PulviniOverlayConcentrator(worker_name="PULVINI.singularity")
        job = type(
            "Job", (), {"job_id": "wipeout-job", "target": 1, "extranonce2_size": 4}
        )()
        overlay.mark_pool_bound("Pool", "stratum+tcp://pool.example:3333", 2)
        overlay.register_pool_job(job, pool_name="Pool")
        before = overlay.snapshot()

        engine = PulviniAutonomicsEngine(
            lattice_repoint_sink=overlay.apply_lattice_repoint
        )
        engine.ingest_telemetry(healthy_telemetry(node_id) for node_id in range(32))
        event = engine.rebalancer.rebalance_lattice_topology(
            [0, 8, 15], reason="three_node_wipeout"
        )
        after = overlay.snapshot()

        self.assertTrue(event.coverage_maintained)
        self.assertEqual(before["worker_name"], after["worker_name"])
        self.assertEqual(before["pool_visible_workers"], after["pool_visible_workers"])
        self.assertEqual(before["active_job_id"], after["active_job_id"])
        self.assertEqual(before["active_pool_name"], after["active_pool_name"])
        self.assertTrue(after["healing_ranges_overlap_free"])
        self.assertGreater(len(after["healing_routes"]), 0)
        for failed_node in [0, 8, 15]:
            reassigned = overlay.assignment_for_nonce(
                nonce_range_inclusive(failed_node)[0]
            )
            self.assertIsNotNone(reassigned)
            assert reassigned is not None
            self.assertNotEqual(failed_node, reassigned.node_id)

    def test_genesis_status_includes_autonomics_snapshot_without_fixture_jobs(
        self,
    ) -> None:
        from pythia_mining.genesis_ai import GenesisAI

        genesis = GenesisAI({"pools": {}, "autonomics": {"target_watts": 10_000.0}})
        status = genesis.get_system_status()
        self.assertIn("pulvini_autonomics", status)
        self.assertIn("topology", status["pulvini_autonomics"])
        self.assertEqual(
            3.75, status["pulvini_autonomics"]["topology"]["redundancy_factor"]
        )
        self.assertFalse(status["fixture_jobs_enabled"])


if __name__ == "__main__":
    unittest.main()
