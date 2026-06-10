"""Unit, property, integration-smoke, and adversarial tests for HYBA backend paths."""

from __future__ import annotations

import asyncio
import json
import math
import os
import random
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from pydantic import ValidationError

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_BACKEND = REPO_ROOT / "python_backend"
if str(PYTHON_BACKEND) not in sys.path:
    sys.path.insert(0, str(PYTHON_BACKEND))

from hyba_genesis_api.api.mining import PowerScaleRequest  # noqa: E402
from hyba_genesis_api.api.misc import PredictRequest, execute_pulvini  # noqa: E402
from hyba_genesis_api.api.security import ShieldParam  # noqa: E402
from hyba_genesis_api.core.substrate import get_substrate_state, initialize_substrate, shutdown_substrate  # noqa: E402
from pythia_mining.mining_validation import build_block_header, compact_to_target, validate_share  # noqa: E402
from pythia_mining.quantum_solver import (  # noqa: E402
    DODECAHEDRON_VERTICES,
    QuantumSolverConfigurationError,
    DodecahedralQuantumSolver,
)
from pythia_mining.stratum_client import (  # noqa: E402
    AllPoolsOfflineError,
    PoolManager,
    ProductionConfigurationError,
    StratumClient,
)

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
    def test_quantum_solver_capacity_is_not_reported_without_configuration(self) -> None:
        solver = DodecahedralQuantumSolver()
        metrics = solver.get_metrics()
        self.assertTrue(metrics["available"])
        self.assertIsNone(metrics["hashrate_ehs"])
        self.assertEqual("not_configured", metrics["capacity_source"])
        self.assertEqual("derived_runtime_state", metrics["telemetry_source"])
        self.assertAlmostEqual(math.log2(DODECAHEDRON_VERTICES), metrics["von_neumann_entropy"], places=4)

    def test_quantum_solver_configured_capacity_is_monotonic_by_power_scale(self) -> None:
        solver = DodecahedralQuantumSolver(configured_capacity_ehs=10.0)
        previous_hashrate = -math.inf
        for scale in [0.1, 0.5, 1.0, 2.5, 10.0]:
            solver.set_power_scale(scale)
            metrics = solver.get_metrics()
            self.assertEqual("configured_estimate", metrics["capacity_source"])
            self.assertGreaterEqual(metrics["hashrate_ehs"], previous_hashrate)
            previous_hashrate = metrics["hashrate_ehs"]

    def test_connect_search_submit_smoke_uses_validation_before_accounting(self) -> None:
        async def run_smoke() -> dict[str, object]:
            pool_manager = PoolManager()
            active_pool = await pool_manager.get_best_pool()
            job = active_pool.inject_simulated_target_job(difficulty=1.0)
            solver = DodecahedralQuantumSolver()
            await solver.configure_search(job.target, [(0, 2**32 - 1)])
            nonce = await solver.solve(max_iterations=25, timeout=5.0)
            assert nonce is not None
            result = active_pool.validate_and_record_share(job, nonce, "00" * job.extranonce2_size)
            payload = {
                "connected": active_pool.is_connected,
                "authenticated": active_pool.is_authenticated,
                "connection_state": active_pool.connection_state,
                "job_id": job.job_id,
                "nonce": nonce,
                "share_result": result,
                "shares_submitted": active_pool.shares_submitted,
                "shares_accepted": active_pool.shares_accepted,
                "shares_rejected": active_pool.shares_rejected,
            }
            await pool_manager.disconnect_all()
            return payload

        result = asyncio.run(run_smoke())

        self.assertTrue(result["connected"])
        self.assertTrue(result["authenticated"])
        self.assertEqual("AUTHENTICATED", result["connection_state"])
        self.assertIsInstance(result["job_id"], str)
        self.assertIsInstance(result["nonce"], int)
        self.assertEqual(1, result["shares_submitted"])
        self.assertEqual(1, result["shares_accepted"] + result["shares_rejected"])
        self.assertIsNotNone(result["share_result"].block_hash)

    def test_live_stratum_mode_uses_session_handshake_not_fixture_auth(self) -> None:
        class FakeLiveSession:
            def __init__(self, profile):
                self.profile = profile
                self.closed = False

            async def connect(self):
                return None

            async def subscribe_and_authorize(self):
                return SimpleNamespace(extranonce1="abc123", extranonce2_size=8, authorized=True)

            async def close(self):
                self.closed = True

        async def run_case():
            client = StratumClient(
                pool_url="stratum+tcp://example.com:3333",
                username="worker",
                password="secret",
                pool_name="Example Pool",
                stratum_version=1,
            )
            with patch.dict(os.environ, {"HYBA_ENABLE_LIVE_STRATUM": "1"}, clear=False):
                with patch("pythia_mining.stratum_client.LiveStratumSession", FakeLiveSession):
                    connected = await client.connect()
            await client.disconnect()
            return connected, client

        connected, client = asyncio.run(run_case())

        self.assertTrue(connected)
        self.assertEqual("abc123", client.extranonce1)
        self.assertEqual(8, client.extranonce2_size)
        self.assertEqual("DISCONNECTED", client.connection_state)

    def test_live_stratum_v2_fails_closed_until_transport_exists(self) -> None:
        async def run_case():
            client = StratumClient(
                pool_url="stratum2+tcp://example.com:3336",
                username="worker",
                password="secret",
                pool_name="Example V2 Pool",
                stratum_version=2,
            )
            with patch.dict(os.environ, {"HYBA_ENABLE_LIVE_STRATUM": "1"}, clear=False):
                connected = await client.connect()
            return connected, client

        connected, client = asyncio.run(run_case())

        self.assertFalse(connected)
        self.assertFalse(client.is_authenticated)
        self.assertIn("live Stratum v2 transport is not implemented", client.connection_state)

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

    def test_validation_primitives_build_80_byte_header_and_target(self) -> None:
        pool_manager = PoolManager()
        job = pool_manager.get_active_pool().inject_simulated_target_job(difficulty=1.0)
        validation = validate_share(job, nonce=0, extranonce2="00" * job.extranonce2_size)
        header = bytes.fromhex(validation.header_hex)
        self.assertEqual(80, len(header))
        self.assertEqual(header, build_block_header(job, validation.merkle_root, 0))
        self.assertEqual(compact_to_target(job.nbits), validation.target)


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

    def test_production_requires_external_pool_configuration_and_blocks_fixtures(self) -> None:
        clean_env = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith("HYBA_POOL_") and key not in {"NODE_ENV", "HYBA_ENV", "HYBA_ALLOW_DEV_FIXTURES"}
        }
        with patch.dict(os.environ, clean_env, clear=True):
            os.environ["NODE_ENV"] = "production"
            with self.assertRaises(ProductionConfigurationError):
                PoolManager()

        production_pool_env = {
            "NODE_ENV": "production",
            "HYBA_POOL_NICEHASH_URL": "stratum+ssl://sha256.eu.nicehash.com:33334",
            "HYBA_POOL_NICEHASH_USERNAME": "prod-user",
            "HYBA_POOL_NICEHASH_PASSWORD": "prod-secret",
        }
        with patch.dict(os.environ, production_pool_env, clear=True):
            pool_manager = PoolManager()
            active_pool = pool_manager.get_active_pool()
            with self.assertRaises(ProductionConfigurationError):
                active_pool.inject_simulated_target_job(difficulty=1.0)


if __name__ == "__main__":
    unittest.main()
