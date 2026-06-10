"""Unit, property, integration-smoke, and adversarial tests for HYBA backend paths."""

from __future__ import annotations

import asyncio
import json
import math
import random
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock

from pydantic import ValidationError

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_BACKEND = REPO_ROOT / "python_backend"
if str(PYTHON_BACKEND) not in sys.path:
    sys.path.insert(0, str(PYTHON_BACKEND))

from hyba_genesis_api.api.mining import PowerScaleRequest  # noqa: E402
from hyba_genesis_api.api.misc import PredictRequest, execute_pulvini  # noqa: E402
from hyba_genesis_api.api.security import ShieldParam  # noqa: E402
from hyba_genesis_api.core.substrate import get_substrate_state, initialize_substrate, shutdown_substrate  # noqa: E402
from pythia_mining.quantum_solver import (  # noqa: E402
    DODECAHEDRON_VERTICES,
    QuantumSolverConfigurationError,
    DodecahedralQuantumSolver,
)
from pythia_mining.stratum_client import AllPoolsOfflineError, PoolManager  # noqa: E402

EXPECTED_INIT_ORDER = [
    "pulvini_reconstruction_kernel",
    "hilbert_space_warm_start",
    "phi_floor_coherence",
    "pythia_consensus_monitors",
    "mining_engine_optimization_sync",
]


class SubstrateUnitTests(unittest.TestCase):
    def test_substrate_initialization_is_deterministic_and_json_serializable(self) -> None:
        first_state = initialize_substrate()
        second_state = initialize_substrate()

        self.assertTrue(first_state["ready"])
        self.assertTrue(second_state["ready"])
        self.assertEqual(EXPECTED_INIT_ORDER, second_state["initialization_order"])
        self.assertEqual(EXPECTED_INIT_ORDER, get_substrate_state()["initialization_order"])
        self.assertIsInstance(json.dumps(second_state), str)

        shutdown_state = shutdown_substrate()
        self.assertIsNotNone(shutdown_state["shutdown_at"])

    def test_pulvini_execute_returns_normalized_real_operations(self) -> None:
        payload = asyncio.run(execute_pulvini())

        self.assertEqual("success", payload["status"])
        self.assertEqual("PULVINI Memory Engine Executed", payload["message"])
        self.assertEqual(2, len(payload["operations"]))
        self.assertEqual(2**14, payload["operations"][0]["state_vector_entries"])
        self.assertAlmostEqual(1.0, float(payload["operations"][0]["diffusion_norm"]), places=12)
        self.assertEqual(158, payload["operations"][1]["projected_dimensions"])


class MiningPropertyAndIntegrationTests(unittest.TestCase):
    def test_quantum_solver_hashrate_is_monotonic_by_power_scale(self) -> None:
        solver = DodecahedralQuantumSolver()
        previous_hashrate = -math.inf
        for scale in [0.1, 0.5, 1.0, 2.5, 10.0]:
            solver.set_power_scale(scale)
            metrics = solver.get_metrics()
            self.assertTrue(metrics["available"])
            self.assertGreaterEqual(metrics["hashrate_ehs"], previous_hashrate)
            self.assertAlmostEqual(math.log2(DODECAHEDRON_VERTICES), metrics["von_neumann_entropy"], places=4)
            previous_hashrate = metrics["hashrate_ehs"]

    def test_connect_search_submit_smoke_uses_real_pythia_classes(self) -> None:
        async def run_smoke() -> dict[str, object]:
            pool_manager = PoolManager()
            active_pool = await pool_manager.get_best_pool()
            job = active_pool.inject_simulated_target_job(difficulty=1.0)
            solver = DodecahedralQuantumSolver()
            await solver.configure_search(job.target, [(0, 2**32 - 1)])
            nonce = await solver.solve(max_iterations=25, timeout=5.0)
            active_pool.shares_submitted += 1
            if nonce is not None and nonce % 67 != 0:
                active_pool.shares_accepted += 1
            else:
                active_pool.shares_rejected += 1
            result = {
                "connected": active_pool.is_connected,
                "authenticated": active_pool.is_authenticated,
                "connection_state": active_pool.connection_state,
                "job_id": job.job_id,
                "nonce": nonce,
                "shares_submitted": active_pool.shares_submitted,
                "shares_accepted": active_pool.shares_accepted,
                "shares_rejected": active_pool.shares_rejected,
            }
            await pool_manager.disconnect_all()
            return result

        result = asyncio.run(run_smoke())

        self.assertTrue(result["connected"])
        self.assertTrue(result["authenticated"])
        self.assertEqual("AUTHENTICATED", result["connection_state"])
        self.assertIsInstance(result["job_id"], str)
        self.assertIsInstance(result["nonce"], int)
        self.assertEqual(1, result["shares_submitted"])
        self.assertEqual(1, result["shares_accepted"] + result["shares_rejected"])

    def test_configured_solver_projects_nonce_inside_declared_ranges(self) -> None:
        async def run_cases() -> None:
            solver = DodecahedralQuantumSolver()
            rng = random.Random(1337)
            for _ in range(100):
                start = rng.randint(0, 1_000_000)
                end = start + rng.randint(0, 500)
                target = rng.randint(1, 2**224)
                await solver.configure_search(target=target, nonce_ranges=[(start, end)])
                nonce = await solver.solve(max_iterations=25, timeout=5.0)
                self.assertIsInstance(nonce, int)
                self.assertGreaterEqual(nonce, start)
                self.assertLessEqual(nonce, end)

        asyncio.run(run_cases())

    def test_pool_manager_raises_when_all_pools_fail(self) -> None:
        async def run_case() -> None:
            pool_manager = PoolManager()
            for client in pool_manager.pools.values():
                client.connect = AsyncMock(return_value=False)  # type: ignore[method-assign]
                client.is_connected = False
                client.is_authenticated = False
                client.connection_state = "ERROR: forced test outage"

            with self.assertRaises(AllPoolsOfflineError):
                await pool_manager.get_best_pool()

        asyncio.run(run_case())


class AdversarialValidationTests(unittest.TestCase):
    def test_power_scale_rejects_negative_and_extreme_values(self) -> None:
        for scale in [-1, 0, 10_000]:
            with self.assertRaises(ValidationError):
                PowerScaleRequest(scale=scale)
        self.assertEqual(0.8, PowerScaleRequest(scale=0.8).scale)

    def test_shield_strength_rejects_out_of_range_values(self) -> None:
        for strength in [-0.1, 1.1, 2]:
            with self.assertRaises(ValidationError):
                ShieldParam(strength=strength)
        self.assertEqual(0.9, ShieldParam(strength=0.9).strength)

    def test_prediction_rejects_non_positive_difficulty(self) -> None:
        for difficulty in [-1, 0]:
            with self.assertRaises(ValidationError):
                PredictRequest(state={"networkDifficulty": difficulty})
        self.assertEqual(7_234_567_890_123, PredictRequest(state={"networkDifficulty": 7_234_567_890_123}).state.networkDifficulty)

    def test_solver_rejects_invalid_targets_and_nonce_ranges(self) -> None:
        async def run_cases() -> None:
            solver = DodecahedralQuantumSolver()
            invalid_cases = [
                (0, [(0, 10)]),
                (-1, [(0, 10)]),
                (1, []),
                (1, [(-1, 10)]),
                (1, [(10, 9)]),
                (1, [(0, 2**32)]),
            ]
            for target, ranges in invalid_cases:
                with self.assertRaises(QuantumSolverConfigurationError):
                    await solver.configure_search(target=target, nonce_ranges=ranges)

        asyncio.run(run_cases())

    def test_solver_returns_none_for_timeout_without_crashing(self) -> None:
        async def run_case() -> None:
            solver = DodecahedralQuantumSolver()
            await solver.configure_search(target=1, nonce_ranges=[(0, 100)])
            self.assertIsNone(await solver.solve(max_iterations=25, timeout=1e-12))

        asyncio.run(run_case())


if __name__ == "__main__":
    unittest.main()
