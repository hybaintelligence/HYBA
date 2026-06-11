from __future__ import annotations

import asyncio
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

from hyba_genesis_api.api.mining_ops import _derive_alerts, _parse_audit_line  # noqa: E402
from pythia_mining.metrics_store import MetricsStore, PoolMetrics  # noqa: E402
from pythia_mining.stratum_client import MiningJob, StratumClient  # noqa: E402
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
            "HYBA_POOL_NICEHASH_USERNAME": "ci-user",
            "HYBA_POOL_NICEHASH_PASSWORD": "ci-secret",
        }
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(1, validate_production_env.main())

    def test_validator_accepts_minimal_valid_production_contract(self) -> None:
        env = {
            "NODE_ENV": "production",
            "HYBA_ENV": "production",
            "JWT_SECRET": "ci-production-secret-value-at-least-32-chars",
            "HYBA_OPERATOR_CREDENTIALS": "operator:4d967bd2a5dbaeeb3d3fcc6efbb483b3d728ee3000a6daa724b402dfb9a65f45:mining_operator",
            "PULVINI_BACKEND_URL": "http://127.0.0.1:3001",
            "HYBA_ALLOW_DEV_FIXTURES": "false",
            "HYBA_ENABLE_LIVE_STRATUM": "true",
            "HYBA_ENABLE_LIVE_SHARE_SUBMIT": "false",
            "HYBA_POOL_NICEHASH_URL": "stratum+ssl://sha256.eu.nicehash.com:3334",
            "HYBA_POOL_NICEHASH_USERNAME": "ci-user",
            "HYBA_POOL_NICEHASH_PASSWORD": "ci-secret",
        }
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(0, validate_production_env.main())


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

    def test_alert_derivation_flags_rejection_failures_latency_and_degraded_health(self) -> None:
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
                        password="secret",
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
