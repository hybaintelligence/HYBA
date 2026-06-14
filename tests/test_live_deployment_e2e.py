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

from pythia_mining.pulvini_compressed_solver import PulviniCompressedQuantumSolver  # noqa: E402
from pythia_mining.pulvini_overlay import PulviniOverlayConcentrator  # noqa: E402
from pythia_mining.pulvini_propagation import SharePropagationController  # noqa: E402
from pythia_mining.stratum_client import (
    MiningJob,
    PoolManager,
    StratumClient,
)  # noqa: E402


class InterleavedHandshakeTransport:
    def __init__(self) -> None:
        self.sent: list[str] = []
        self.closed = False
        self.responses = [
            json.dumps(
                {"id": None, "method": "mining.set_difficulty", "params": [8.0]}
            ),
            json.dumps({"id": 1, "result": [[], "0a0b", 4], "error": None}),
            json.dumps(
                {
                    "id": None,
                    "method": "mining.notify",
                    "params": [
                        "preauth-job",
                        "00" * 32,
                        "0100000001",
                        "ffffffff",
                        [],
                        "20000000",
                        "1d00ffff",
                        "6578ab4e",
                        True,
                    ],
                }
            ),
            json.dumps({"id": 2, "result": True, "error": None}),
        ]

    async def connect(self) -> None:
        return None

    async def send_line(self, line: str) -> None:
        self.sent.append(line)

    async def read_line(self, timeout: float | None = None) -> str:
        return self.responses.pop(0)

    async def close(self) -> None:
        self.closed = True


class LiveDeploymentEndToEndTests(unittest.TestCase):
    def test_live_pool_connect_job_mine_and_submit_pipeline(self) -> None:
        async def run_case() -> dict:
            with tempfile.TemporaryDirectory() as tmpdir:
                env = {
                    "NODE_ENV": "production",
                    "HYBA_ENV": "production",
                    "HYBA_ENABLE_LIVE_STRATUM": "true",
                    "HYBA_ENABLE_LIVE_SHARE_SUBMIT": "true",
                    "HYBA_LIVE_SHARE_APPROVAL_ID": "ci-e2e-approval",
                    "HYBA_METRICS_DB_PATH": str(Path(tmpdir) / "metrics.db"),
                    "HYBA_AUDIT_LOG_DIR": str(Path(tmpdir) / "audit"),
                }
                with patch.dict(os.environ, env, clear=False):
                    client = StratumClient(
                        pool_url="stratum+tcp://example.com:3333",
                        username="worker",
                        password="ci-secret",
                        pool_name="Example Pool",
                        stratum_version=1,
                    )
                    client.extranonce1 = "0a0b"
                    client.extranonce2_size = 4
                    client.is_connected = True
                    client.is_authenticated = True
                    client.live_session = type(
                        "FakeLiveSession",
                        (),
                        {
                            "submit_share": staticmethod(
                                lambda **kwargs: _accepted_submit_result(
                                    kwargs["job_id"]
                                )
                            )
                        },
                    )()
                    client.connection_state = "AUTHENTICATED"
                    overlay = PulviniOverlayConcentrator(
                        worker_name="PULVINI.singularity"
                    )
                    propagation = SharePropagationController(overlay.manifold)
                    solver = PulviniCompressedQuantumSolver(configured_capacity_ehs=1.0)
                    job = MiningJob(
                        job_id="live-job-1",
                        prevhash="00" * 32,
                        coinbase_parts=("0100000001", "ffffffff"),
                        merkle_branch=[],
                        version="20000000",
                        nbits="1d00ffff",
                        ntime="5e9a5c00",
                        target=2**256 - 1,
                        extranonce1=client.extranonce1,
                        extranonce2_size=client.extranonce2_size,
                    )
                    overlay.register_pool_job(job, pool_name=client.pool_name)
                    await solver.configure_compressed_search(
                        job.target, overlay.nonce_plan
                    )
                    nonce = await solver.solve(max_iterations=16, timeout=5.0)
                    self.assertIsNotNone(nonce)
                    assert nonce is not None
                    assignment = overlay.assignment_for_nonce(nonce)
                    self.assertIsNotNone(assignment)
                    assert assignment is not None
                    result = await propagation.handle_share_found(
                        job=job,
                        finder_id=assignment.node_id,
                        nonce=nonce,
                        extranonce2=assignment.extranonce2,
                        submitter=client.submit_validated_share,
                    )
                    overlay.record_share_outcome(
                        assignment.node_id, nonce, result.share_result
                    )
                    return {
                        "accepted": result.share_result.accepted,
                        "status": client.get_status(),
                        "solver": solver.get_metrics(),
                        "overlay": overlay.snapshot(),
                        "cancelled": len(result.cancelled_nodes),
                    }

        outcome = asyncio.run(run_case())
        self.assertTrue(outcome["accepted"])
        self.assertEqual(1, outcome["status"]["performance"]["shares_submitted"])
        self.assertEqual(1, outcome["status"]["performance"]["shares_accepted"])
        self.assertEqual(32, outcome["cancelled"])
        self.assertEqual(1, outcome["overlay"]["pool_visible_workers"])
        self.assertEqual(32, outcome["overlay"]["internal_nodes"])
        self.assertLessEqual(outcome["solver"]["hashrate_ehs"], 1.0)
        self.assertTrue(outcome["solver"]["complete_nonce_coverage"])

    def test_pool_manager_uses_dict_key_when_connecting_degraded_best_pool(
        self,
    ) -> None:
        async def run_case() -> str | None:
            manager = PoolManager(
                {
                    "alpha": {
                        "name": "Alpha",
                        "url": "stratum+tcp://alpha.example:3333",
                        "username": "worker",
                        "password": "x",
                    }
                }
            )
            pool = manager.pools["alpha"]
            pool.is_connected = False
            pool.connection_failures = 1

            async def fake_connect() -> bool:
                pool.is_connected = True
                pool.is_authenticated = True
                pool.connection_state = "AUTHENTICATED"
                return True

            pool.connect = fake_connect  # type: ignore[method-assign]
            selected = await manager.get_best_pool()
            self.assertIs(selected, pool)
            return manager.current_pool_key

        self.assertEqual("alpha", asyncio.run(run_case()))

    def test_stratum_handshake_tolerates_interleaved_notifications(self) -> None:
        async def run_case() -> tuple[object, InterleavedHandshakeTransport]:
            from pythia_mining.live_stratum_session import LiveStratumSession
            from pythia_mining.pool_profiles import build_profile

            transport = InterleavedHandshakeTransport()
            session = LiveStratumSession(
                build_profile(
                    "alpha",
                    name="Alpha",
                    url="stratum+tcp://example.com:3333",
                    username="worker",
                    password="x",
                ),
                transport=transport,
            )
            await session.connect()
            handshake = await session.subscribe_and_authorize()
            return handshake, transport

        handshake, transport = asyncio.run(run_case())
        self.assertEqual("0a0b", handshake.extranonce1)
        self.assertTrue(handshake.authorized)
        self.assertIn("mining.subscribe", transport.sent[0])
        self.assertIn("mining.authorize", transport.sent[1])


def _accepted_submit_result(job_id: str):
    from pythia_mining.live_stratum_session import SubmitResult

    async def inner(**kwargs):
        return SubmitResult(
            accepted=True,
            error=None,
            response={"id": 3, "result": True, "error": None, "job_id": job_id},
        )

    return inner()


if __name__ == "__main__":
    unittest.main()
