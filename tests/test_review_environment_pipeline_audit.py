from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from review_environment_pipeline_audit import run_audits  # noqa: E402


def test_review_environment_pipeline_audits_pass_without_live_network() -> None:
    results = asyncio.run(run_audits())

    assert {result.name for result in results} == {
        "pool_failover_circuit_breaker",
        "stale_job_block_height_invalidation",
        "malformed_nonce_validation",
        "bridge_rate_limit_contract",
    }
    assert all(result.status == "pass" for result in results)
    stale = next(result for result in results if result.name == "stale_job_block_height_invalidation")
    assert "stale-review-job" in stale.evidence["stale_job_ids"]
