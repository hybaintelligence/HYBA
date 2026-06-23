from __future__ import annotations

import pytest

from pythia_mining.mining_verification_firewall import VerificationFirewallError
from pythia_mining.stratum_client import MiningJob, StratumClient
from pythia_mining.stratum_submission_firewall import (
    PATCH_MARKER,
    install_stratum_submit_firewall,
)


class _NoSubmitSession:
    def __init__(self) -> None:
        self.calls = 0

    async def submit_share(self, **_: object) -> object:
        self.calls += 1
        raise AssertionError("live submit must be unreachable when firewall blocks")


def _job() -> MiningJob:
    return MiningJob(
        job_id="firewall-job",
        prevhash="00" * 32,
        coinbase_parts=("0100000001", "ffffffff"),
        merkle_branch=[],
        version="20000000",
        nbits="207fffff",
        ntime="5e9a5c00",
        target=2**255,
        extranonce1="00000001",
        extranonce2_size=4,
    )


def test_stratum_client_submit_method_is_firewall_wrapped() -> None:
    install_stratum_submit_firewall()

    assert getattr(StratumClient.submit_validated_share, PATCH_MARKER, False) is True


@pytest.mark.asyncio
async def test_firewall_blocks_before_live_session_submit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from pythia_mining import stratum_submission_firewall as seam

    install_stratum_submit_firewall()
    client = StratumClient(
        pool_url="stratum+tcp://pool.example:3333",
        username="worker",
        password="x",
        pool_name="unit-test-pool",
    )
    session = _NoSubmitSession()
    client.live_session = session

    def block(_: object, __: int, ___: object = None) -> dict:
        raise VerificationFirewallError("local_sha256d_verification_failed")

    monkeypatch.setattr(seam, "assert_stratum_submission_firewall", block)
    result = await client.submit_validated_share(_job(), 1)

    assert result.accepted is False
    assert result.error_code == 428
    assert "verification_firewall_blocked" in str(result.error_message)
    assert session.calls == 0
    assert client.shares_rejected >= 1
