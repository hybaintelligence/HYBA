from __future__ import annotations

import json
from pathlib import Path

import pytest

from pythia_mining.ctd_formalism import compute_phi_resonance

FIXTURE = Path("docs/evidence/datasets/bitcoin_block_nonce_fixture.json")


def _blocks() -> list[dict[str, object]]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["blocks"]


@pytest.mark.parametrize("data", _blocks())
def test_phi_resonance_on_fixture_nonces(data: dict[str, object]) -> None:
    score = compute_phi_resonance(int(data["nonce"]))

    assert 0.0 <= score <= 1.0
    assert score > 0.5


def test_phi_resonance_fixture_beats_local_counterfactual_window() -> None:
    """Fixture nonces should beat nearby deterministic counterfactual offsets.

    This is an empirical regression over the checked-in fixture, not a universal
    claim that Bitcoin proof-of-work is caused by Φ-resonance.
    """

    blocks = _blocks()
    observed = [compute_phi_resonance(int(row["nonce"])) for row in blocks]
    counterfactual = [
        compute_phi_resonance((int(row["nonce"]) + 10_000_019) & 0xFFFFFFFF)
        for row in blocks
    ]

    assert sum(observed) / len(observed) > sum(counterfactual) / len(counterfactual)
