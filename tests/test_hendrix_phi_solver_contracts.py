from __future__ import annotations

import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from pythia_mining import hendrix_phi_solver as hendrix  # noqa: E402


def test_phi_gradient_proposal_preserves_start_nonce_alias() -> None:
    canonical = hendrix.phi_gradient_proposal(
        nonce=123_456,
        rng=random.Random(42),
        scale=3,
    )
    legacy = hendrix.phi_gradient_proposal(
        start_nonce=123_456,
        rng=random.Random(42),
        scale=3,
    )

    assert legacy == canonical
    assert 0 <= legacy < hendrix.UINT32_SPACE


def test_phi_gradient_proposal_rejects_conflicting_nonce_aliases() -> None:
    with pytest.raises(ValueError, match="nonce and start_nonce"):
        hendrix.phi_gradient_proposal(
            nonce=1,
            start_nonce=2,
            rng=random.Random(42),
        )


def test_phi_gradient_proposal_requires_nonce_material() -> None:
    with pytest.raises(TypeError, match="requires nonce or start_nonce"):
        hendrix.phi_gradient_proposal(rng=random.Random(42))


def test_hendrix_metadata_preserves_claim_boundary() -> None:
    metadata = hendrix.algorithm_metadata()
    boundary = metadata["empirical_validation_status"]["claim_boundary"]

    assert metadata["live_io"] is False
    assert "NO EVIDENCE" in boundary
    assert "pool-side acceptance" in boundary
