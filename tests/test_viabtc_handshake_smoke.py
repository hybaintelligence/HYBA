from scripts.start_autonomous_mining import REQUIRED_RUNTIME_IMPORTS
from scripts.viabtc_handshake_smoke import run_mock_handshake


def test_startup_dependency_contract_mentions_numpy_requirement() -> None:
    assert REQUIRED_RUNTIME_IMPORTS["numpy"].startswith("numpy==")


def test_viabtc_mock_handshake_exercises_subscribe_authorize_without_share_claim() -> (
    None
):
    evidence = run_mock_handshake()

    assert evidence.connected
    assert evidence.subscribed
    assert evidence.authorized
    assert not evidence.share_submitted
    assert not evidence.accepted_share_claimed
    assert evidence.worker_redacted == "<worker>"
    assert evidence.transcript_sha256
