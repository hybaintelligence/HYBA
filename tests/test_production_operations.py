from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from argon2 import PasswordHasher  # noqa: E402
from fastapi import HTTPException  # noqa: E402

from hyba_genesis_api.api import auth as auth_api  # noqa: E402
from hyba_genesis_api.api.mining_ops import (
    _derive_alerts,
    _parse_audit_line,
)  # noqa: E402
from pythia_mining.metrics_store import MetricsStore, PoolMetrics  # noqa: E402
from pythia_mining.stratum_client import (  # noqa: E402
    MiningJob,
    StratumClient,
    _dev_fixtures_allowed,
    _is_production,
    _live_share_submit_enabled,
    _live_stratum_enabled,
)
from scripts import validate_production_env  # noqa: E402


class ProductionEnvironmentValidatorTests(unittest.TestCase):
    def test_validator_rejects_raw_operator_password_and_placeholders(self) -> None:
        env = {
            "NODE_ENV": "production",
            "HYBA_ENV": "production",
            "JWT_SECRET": "short",
            "HYBA_OPERATOR_CREDENTIALS": "operator:raw-password:mining_operator",
            "PULVINI_BACKEND_URL": "http://127.0.0.1:3001",
            "HYBA_ALLOW_DEV_FIXTURES": "false",
            "HYBA_POOL_NICEHASH_URL": "stratum+ssl://sha256.eu.nicehash.com:3334",
            "HYBA_POOL_NICEHASH_WORKER": "ci-worker",
            "HYBA_POOL_NICEHASH_NICEHASH_POOL_ID": "ci-pool-id",
        }
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(1, validate_production_env.main())

    def test_validator_rejects_legacy_sha256_operator_hash_in_production(self) -> None:
        env = {
            "NODE_ENV": "production",
            "HYBA_ENV": "production",
            "JWT_SECRET": "ci-production-secret-value-at-least-32-chars",
            "HYBA_OPERATOR_CREDENTIALS": "operator:4d967bd2a5dbaeeb3d3fcc6efbb483b3d728ee3000a6daa724b402dfb9a65f45:mining_operator",
            "PULVINI_BACKEND_URL": "http://127.0.0.1:3001",
            "HYBA_ALLOW_DEV_FIXTURES": "false",
            "HYBA_POOL_NICEHASH_URL": "stratum+ssl://sha256.eu.nicehash.com:3334",
            "HYBA_POOL_NICEHASH_WORKER": "ci-worker",
            "HYBA_POOL_NICEHASH_NICEHASH_POOL_ID": "ci-pool-id",
        }
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(1, validate_production_env.main())

    def test_validator_accepts_minimal_valid_production_contract(self) -> None:
        password_hash = PasswordHasher().hash("correct horse battery staple")
        env = {
            "NODE_ENV": "production",
            "HYBA_ENV": "production",
            "JWT_SECRET": "ci-production-secret-value-at-least-32-chars",
            "HYBA_OPERATOR_CREDENTIALS": f"operator:{password_hash}:mining_operator",
            "PULVINI_BACKEND_URL": "http://127.0.0.1:3001",
            "HYBA_ALLOW_DEV_FIXTURES": "false",
            "HYBA_ENABLE_LIVE_STRATUM": "true",
            "HYBA_ENABLE_LIVE_SHARE_SUBMIT": "false",
            "HYBA_ENABLE_MINING_AUTOCONNECT": "false",
            "HYBA_ENABLE_AUDIT_LOGGING": "true",
            "HYBA_POOL_NICEHASH_URL": "stratum+ssl://sha256.eu.nicehash.com:3334",
            "HYBA_POOL_NICEHASH_WORKER": "ci-worker",
            "HYBA_POOL_NICEHASH_NICEHASH_POOL_ID": "ci-open-network-pool-id",
            "HYBA_POOL_NICEHASH_STRATUM_VERSION": "1",
        }
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(0, validate_production_env.main())

    def test_validator_accepts_ckpool_btc_address_without_pool_password(self) -> None:
        password_hash = PasswordHasher().hash("correct horse battery staple")
        env = {
            "NODE_ENV": "production",
            "HYBA_ENV": "production",
            "JWT_SECRET": "ci-production-secret-value-at-least-32-chars",
            "HYBA_OPERATOR_CREDENTIALS": f"operator:{password_hash}:mining_operator",
            "PULVINI_BACKEND_URL": "http://127.0.0.1:3001",
            "HYBA_ALLOW_DEV_FIXTURES": "false",
            "HYBA_ENABLE_LIVE_STRATUM": "true",
            "HYBA_ENABLE_LIVE_SHARE_SUBMIT": "false",
            "HYBA_ENABLE_MINING_AUTOCONNECT": "false",
            "HYBA_ENABLE_AUDIT_LOGGING": "true",
            "HYBA_POOL_CKPOOL_URL": "stratum+tcp://solo.ckpool.org:3333",
            "HYBA_POOL_CKPOOL_BTC_ADDRESS": "bc1qexampleopennetworkpayout000000000000000000",
            "HYBA_POOL_CKPOOL_STRATUM_VERSION": "1",
        }
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(0, validate_production_env.main())

    def test_validator_accepts_viabtc_stratum_v2_live_launch_profile(self) -> None:
        password_hash = PasswordHasher().hash("correct horse battery staple")
        env = {
            "NODE_ENV": "production",
            "HYBA_ENV": "production",
            "JWT_SECRET": "ci-production-secret-value-at-least-32-chars",
            "HYBA_OPERATOR_CREDENTIALS": f"operator:{password_hash}:mining_operator",
            "PULVINI_BACKEND_URL": "http://127.0.0.1:3001",
            "HYBA_ALLOW_DEV_FIXTURES": "false",
            "HYBA_ENABLE_LIVE_STRATUM": "true",
            "HYBA_ENABLE_LIVE_SHARE_SUBMIT": "true",
            "HYBA_LIVE_SHARE_APPROVAL_ID": "launch-approval-ci",
            "HYBA_ENABLE_MINING_AUTOCONNECT": "true",
            "HYBA_ENABLE_AUDIT_LOGGING": "true",
            "HYBA_QUANTUM_CAPACITY_EHS": "1.0",
            "HYBA_POOL_VIABTC_URL": "stratum2+ssl://btc.viabtc.com:443",
            "HYBA_POOL_VIABTC_USERNAME": "PYTHIA.001",
            "HYBA_POOL_VIABTC_PASSWORD": "x",
            "HYBA_POOL_VIABTC_STRATUM_VERSION": "2",
        }
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(0, validate_production_env.main())

    def test_validator_rejects_capacity_above_pulvini_hashrate_cap(self) -> None:
        password_hash = PasswordHasher().hash("correct horse battery staple")
        env = {
            "NODE_ENV": "production",
            "HYBA_ENV": "production",
            "JWT_SECRET": "ci-production-secret-value-at-least-32-chars",
            "HYBA_OPERATOR_CREDENTIALS": f"operator:{password_hash}:mining_operator",
            "PULVINI_BACKEND_URL": "http://127.0.0.1:3001",
            "HYBA_ALLOW_DEV_FIXTURES": "false",
            "HYBA_ENABLE_LIVE_STRATUM": "true",
            "HYBA_ENABLE_LIVE_SHARE_SUBMIT": "false",
            "HYBA_ENABLE_MINING_AUTOCONNECT": "false",
            "HYBA_ENABLE_AUDIT_LOGGING": "true",
            "HYBA_QUANTUM_CAPACITY_EHS": "1.000001",
            "HYBA_POOL_VIABTC_URL": "stratum2+ssl://btc.viabtc.com:443",
            "HYBA_POOL_VIABTC_USERNAME": "PYTHIA.001",
            "HYBA_POOL_VIABTC_PASSWORD": "x",
            "HYBA_POOL_VIABTC_STRATUM_VERSION": "2",
        }
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(1, validate_production_env.main())

    def test_validator_rejects_v2_url_when_pool_declares_v1(self) -> None:
        password_hash = PasswordHasher().hash("correct horse battery staple")
        env = {
            "NODE_ENV": "production",
            "HYBA_ENV": "production",
            "JWT_SECRET": "ci-production-secret-value-at-least-32-chars",
            "HYBA_OPERATOR_CREDENTIALS": f"operator:{password_hash}:mining_operator",
            "PULVINI_BACKEND_URL": "http://127.0.0.1:3001",
            "HYBA_ALLOW_DEV_FIXTURES": "false",
            "HYBA_ENABLE_LIVE_STRATUM": "true",
            "HYBA_ENABLE_LIVE_SHARE_SUBMIT": "false",
            "HYBA_ENABLE_MINING_AUTOCONNECT": "false",
            "HYBA_ENABLE_AUDIT_LOGGING": "true",
            "HYBA_POOL_VIABTC_URL": "stratum2+ssl://btc.viabtc.com:443",
            "HYBA_POOL_VIABTC_USERNAME": "PYTHIA.001",
            "HYBA_POOL_VIABTC_PASSWORD": "x",
            "HYBA_POOL_VIABTC_STRATUM_VERSION": "1",
        }
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(1, validate_production_env.main())

    def test_live_share_submission_requires_approval_id(self) -> None:
        password_hash = PasswordHasher().hash("correct horse battery staple")
        env = {
            "NODE_ENV": "production",
            "HYBA_ENV": "production",
            "JWT_SECRET": "ci-production-secret-value-at-least-32-chars",
            "HYBA_OPERATOR_CREDENTIALS": f"operator:{password_hash}:mining_operator",
            "PULVINI_BACKEND_URL": "http://127.0.0.1:3001",
            "HYBA_ALLOW_DEV_FIXTURES": "false",
            "HYBA_ENABLE_LIVE_STRATUM": "true",
            "HYBA_ENABLE_LIVE_SHARE_SUBMIT": "true",
            "HYBA_ENABLE_AUDIT_LOGGING": "true",
            "HYBA_POOL_NICEHASH_URL": "stratum+ssl://sha256.eu.nicehash.com:3334",
            "HYBA_POOL_NICEHASH_WORKER": "ci-worker",
            "HYBA_POOL_NICEHASH_NICEHASH_POOL_ID": "ci-open-network-pool-id",
        }
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(1, validate_production_env.main())

    def test_stratum_runtime_gates_match_production_live_profile(self) -> None:
        env = {
            "NODE_ENV": "production",
            "HYBA_ENV": "production",
            "HYBA_ALLOW_DEV_FIXTURES": "false",
            "HYBA_ENABLE_LIVE_STRATUM": "true",
            "HYBA_ENABLE_LIVE_SHARE_SUBMIT": "true",
        }
        with patch.dict(os.environ, env, clear=True):
            self.assertTrue(_is_production())
            self.assertFalse(_dev_fixtures_allowed())
            self.assertTrue(_live_stratum_enabled())
            self.assertTrue(_live_share_submit_enabled())


class OperatorAuthenticationTests(unittest.TestCase):
    def test_production_operator_login_accepts_argon2id_hash(self) -> None:
        password_hash = PasswordHasher().hash("operator-password")
        env = {
            "NODE_ENV": "production",
            "HYBA_ENV": "production",
            "HYBA_OPERATOR_CREDENTIALS": f"operator:{password_hash}:mining_operator",
        }
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(
                ["mining_operator"],
                auth_api._verify_operator("operator", "operator-password"),
            )

    def test_production_operator_login_rejects_legacy_sha256_hash(self) -> None:
        env = {
            "NODE_ENV": "production",
            "HYBA_ENV": "production",
            "HYBA_OPERATOR_CREDENTIALS": "operator:4d967bd2a5dbaeeb3d3fcc6efbb483b3d728ee3000a6daa724b402dfb9a65f45:mining_operator",
        }
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaises(HTTPException) as exc_info:
                auth_api._verify_operator("operator", "operator-password")
            self.assertEqual(500, exc_info.exception.status_code)
            self.assertEqual(
                "operator_credentials_not_production_safe",
                exc_info.exception.detail["error"],
            )


class CommandRoomGateTests(unittest.TestCase):
    def test_prod_check_runs_environment_validation_first(self) -> None:
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        self.assertTrue(
            package["scripts"]["prod:check"].startswith("npm run prod:env:check &&")
        )
        self.assertIn("prod:game-day", package["scripts"])

    def test_game_day_cascade_degrades_to_manual_and_exports_metrics(self) -> None:
        from scripts.command_room_game_day import run_game_day

        evidence = run_game_day(cascades=3, threshold=3)
        self.assertTrue(evidence["passed"])
        self.assertFalse(evidence["pool_network_used"])
        self.assertEqual(0, evidence["shares_submitted"])
        self.assertEqual("manual", evidence["final_autonomy_level"])
        self.assertEqual(3, evidence["metrics"]["degradation_events"])
        self.assertIn("hyba_degradation_events_total 3", evidence["prometheus_metrics"])
        self.assertTrue(all(item["circuit_open"] for item in evidence["transitions"]))


class BridgeRuntimeHardeningTests(unittest.TestCase):
    def test_bridge_defaults_to_explicit_operator_mining_connect(self) -> None:
        server = (ROOT / "server.ts").read_text(encoding="utf-8")
        self.assertIn("HYBA_ENABLE_MINING_AUTOCONNECT", server)
        self.assertIn("Mining auto-connect disabled", server)
        self.assertIn("enableMiningAutoConnect", server)

    def test_bridge_has_csp_and_internal_only_diagnostics(self) -> None:
        server = (ROOT / "server.ts").read_text(encoding="utf-8")
        self.assertIn("contentSecurityPolicy", server)
        self.assertIn('"frame-ancestors": ["\'none\'"]', server)
        self.assertIn("/bridge/internal/health", server)
        self.assertIn("requireInternalAccess", server)
        self.assertNotIn("contentSecurityPolicy: false", server)

    def test_bridge_proxy_error_does_not_return_backend_url(self) -> None:
        server = (ROOT / "server.ts").read_text(encoding="utf-8")
        error_block = server.split('error: "backend_unavailable"', 1)[1].split(
            "});", 1
        )[0]
        self.assertNotIn("backend:", error_block)

    def test_cloudflare_proxy_has_timeout_and_structured_failure(self) -> None:
        worker = (ROOT / "functions" / "api" / "[[path]].ts").read_text(
            encoding="utf-8"
        )
        self.assertIn("AbortController", worker)
        self.assertIn("HYBA_EDGE_PROXY_TIMEOUT_MS", worker)
        self.assertIn("backend_timeout", worker)
        self.assertIn("x-request-id", worker)
        self.assertIn("cache-control", worker)

    def test_docker_runtime_uses_supervised_entrypoint(self) -> None:
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        entrypoint = (ROOT / "scripts" / "hyba-runtime-entrypoint.sh").read_text(
            encoding="utf-8"
        )
        self.assertIn("hyba-runtime-entrypoint.sh", dockerfile)
        self.assertNotIn(
            "uvicorn hyba_genesis_api.main:app --host 127.0.0.1 --port 3001 --log-level warning & node",
            dockerfile,
        )
        self.assertIn("kill -TERM", entrypoint)
        self.assertIn("FastAPI backend exited", entrypoint)


class MiningOperationsTelemetryTests(unittest.TestCase):
    def test_audit_parser_redacts_sensitive_future_fields(self) -> None:
        parsed = _parse_audit_line(
            '2026-06-11 | INFO | hyba.audit | {"event_type":"security_event","pool_name":"x","pool_url":"u","event_data":{"password":"secret","token":"abc","safe":"ok"}}'
        )
        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual("[REDACTED]", parsed["event_data"]["password"])
        self.assertEqual("[REDACTED]", parsed["event_data"]["token"])
        self.assertEqual("ok", parsed["event_data"]["safe"])

    def test_alert_derivation_flags_rejection_failures_latency_and_degraded_health(
        self,
    ) -> None:
        alerts = _derive_alerts(
            [
                {
                    "pool_name": "Pool",
                    "shares_submitted": 20,
                    "shares_rejected": 15,
                    "connection_failures": 3,
                    "avg_latency_ms": 6000,
                    "acceptance_rate": 0.25,
                }
            ],
            {"system_health": "DEGRADED"},
        )
        codes = {alert["code"] for alert in alerts}
        self.assertIn("low_share_acceptance_rate", codes)
        self.assertIn("high_share_rejection_rate", codes)
        self.assertIn("repeated_pool_connection_failures", codes)
        self.assertIn("high_pool_latency", codes)
        self.assertIn("mining_system_health_degraded", codes)

    def test_metrics_store_persists_pool_and_share_history(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = MetricsStore(str(Path(tmpdir) / "metrics.db"))
            store.update_pool_metrics(
                PoolMetrics(
                    pool_name="Pool",
                    pool_url="stratum+tcp://example.com:3333",
                    shares_submitted=10,
                    shares_accepted=8,
                    shares_rejected=2,
                    connection_failures=0,
                    avg_latency_ms=10.0,
                    last_activity_timestamp=1.0,
                    last_pool_event_timestamp=1.0,
                    last_share_submit_timestamp=1.0,
                    current_difficulty=1.0,
                    current_jobs_count=1,
                    acceptance_rate=0.8,
                )
            )
            store.record_share_submission(
                pool_name="Pool",
                pool_url="stratum+tcp://example.com:3333",
                job_id="job-1",
                nonce=1,
                accepted=True,
            )
            self.assertEqual(1, len(store.get_all_pool_metrics()))
            self.assertEqual(1, len(store.get_share_history(limit=10)))
            store.close()


class ExplicitFailureTelemetryTests(unittest.TestCase):
    def test_websocket_metrics_are_derived_from_persisted_activity(self) -> None:
        async def run_case() -> dict:
            with tempfile.TemporaryDirectory() as tmpdir:
                with patch.dict(
                    os.environ,
                    {"HYBA_METRICS_DB_PATH": str(Path(tmpdir) / "metrics.db")},
                    clear=False,
                ):
                    from hyba_genesis_api.websocket.handlers import WebSocketHandler
                    from pythia_mining.metrics_store import (
                        MetricsStore,
                        reset_metrics_store,
                        set_metrics_store,
                    )

                    store = MetricsStore(str(Path(tmpdir) / "metrics.db"))
                    set_metrics_store(store)
                    store.update_pool_metrics(
                        PoolMetrics(
                            pool_name="Pool",
                            pool_url="stratum+tcp://example.com:3333",
                            shares_submitted=4,
                            shares_accepted=3,
                            shares_rejected=1,
                            connection_failures=0,
                            avg_latency_ms=20.0,
                            last_activity_timestamp=1.0,
                            last_pool_event_timestamp=1.0,
                            last_share_submit_timestamp=1.0,
                            current_difficulty=1.0,
                            current_jobs_count=1,
                            acceptance_rate=0.75,
                        )
                    )
                    payload = await WebSocketHandler().get_current_metrics()
                    reset_metrics_store()
                    return payload

        payload = asyncio.run(run_case())
        self.assertEqual("persisted_mining_activity", payload["source"])
        self.assertEqual(4, payload["shares_submitted"])
        self.assertEqual(3, payload["shares_accepted"])
        self.assertEqual(1, payload["shares_rejected"])
        self.assertEqual(0.75, payload["acceptance_rate"])
        self.assertIsNone(payload["hashrate"])
        self.assertIsNone(payload["quantum_speedup"])

    def test_prediction_fails_closed_without_optimizer_runtime(self) -> None:
        from hyba_genesis_api.api.misc import PredictRequest, predict_params

        async def run_case() -> None:
            with self.assertRaises(HTTPException) as exc_info:
                await predict_params(PredictRequest(state={"networkDifficulty": 10}))
            self.assertEqual(503, exc_info.exception.status_code)
            self.assertEqual(
                "optimizer_runtime_not_connected", exc_info.exception.detail["error"]
            )

        asyncio.run(run_case())

    def test_corrupt_pythia_state_raises_diagnostic_error(self) -> None:
        from hyba_genesis_api.api import mining

        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "pythia_state.json"
            state_path.write_text("{not-json", encoding="utf-8")
            with patch.object(mining, "_state_path", return_value=str(state_path)):
                with self.assertRaisesRegex(RuntimeError, "invalid JSON"):
                    mining.get_pythia_state()


class LiveShareSubmitGateTests(unittest.TestCase):
    def test_live_share_submission_is_blocked_until_explicitly_enabled(self) -> None:
        async def run_case():
            with tempfile.TemporaryDirectory() as tmpdir:
                with patch.dict(
                    os.environ,
                    {
                        "HYBA_ENABLE_LIVE_SHARE_SUBMIT": "false",
                        "HYBA_METRICS_DB_PATH": str(Path(tmpdir) / "metrics.db"),
                        "HYBA_AUDIT_LOG_DIR": str(Path(tmpdir) / "audit"),
                    },
                    clear=False,
                ):
                    client = StratumClient(
                        pool_url="stratum+tcp://example.com:3333",
                        username="worker",
                        password="x",
                        pool_name="Example Pool",
                        stratum_version=1,
                    )
                    client.live_session = object()  # type: ignore[assignment]
                    client.is_connected = True
                    client.is_authenticated = True
                    job = MiningJob(
                        job_id="job-1",
                        prevhash="00" * 32,
                        coinbase_parts=("0100000001", "ffffffff"),
                        merkle_branch=[],
                        version="20000000",
                        nbits="1d00ffff",
                        ntime="5e9a5c00",
                        target=2**256 - 1,
                        extranonce1="f000bba1",
                        extranonce2_size=4,
                    )
                    return await client.submit_validated_share(job, 0, "00000000")

        result = asyncio.run(run_case())
        self.assertFalse(result.accepted)
        self.assertEqual(423, result.error_code)
        self.assertEqual("live_share_submit_disabled", result.error_message)


if __name__ == "__main__":
    unittest.main()
