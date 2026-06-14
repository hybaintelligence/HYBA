"""Property tests for the PULVINI 1 EH/s hashrate governance cap.

These tests sit at the API/runtime seam where PULVINI nonce compression becomes
operator-visible capacity. They verify that configuration, share telemetry, power
scaling, and solver metrics cannot exceed the 1 EH/s cap.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]
PYTHON_BACKEND = ROOT / "python_backend"
if str(PYTHON_BACKEND) not in sys.path:
    sys.path.insert(0, str(PYTHON_BACKEND))

from hyba_genesis_api.api.mining import (  # noqa: E402
    PULVINI_HASHRATE_CAP_EHS as API_HASHRATE_CAP_EHS,
    ConnectRequest,
    PHI_TIERS,
    PowerScaleRequest,
    SubmitJobRequest,
    _capped_hashrate_ehs,
    _effective_hashrate_ehs,
    _phi_tier_composition,
)
from pythia_mining.quantum_solver import (  # noqa: E402
    PULVINI_HASHRATE_CAP_EHS as SOLVER_HASHRATE_CAP_EHS,
    DodecahedralQuantumSolver,
)

finite_nonnegative = st.floats(
    min_value=0.0,
    max_value=10_000.0,
    allow_nan=False,
    allow_infinity=False,
)
valid_connect_capacity = st.floats(
    min_value=0.01,
    max_value=API_HASHRATE_CAP_EHS,
    allow_nan=False,
    allow_infinity=False,
)
above_cap = st.floats(
    min_value=API_HASHRATE_CAP_EHS + 1e-9,
    max_value=10_000.0,
    allow_nan=False,
    allow_infinity=False,
)
power_scales = st.floats(
    min_value=0.1,
    max_value=10.0,
    allow_nan=False,
    allow_infinity=False,
)


def test_power_scale_request_accepts_frontend_phi_tiers_and_defaults_to_1ehs_cap() -> (
    None
):
    request = PowerScaleRequest(scale=1.0, phi_tier=12)
    composition = _phi_tier_composition(request.phi_tier)

    assert request.phi_tier in PHI_TIERS
    assert composition["label"] == "10^12"
    assert composition["hashrate_cap_ehs"] == API_HASHRATE_CAP_EHS
    assert (
        composition["memory_compression_contract"]
        == "pulvini_phi_compressed_pre_search"
    )


def test_power_scale_request_rejects_unknown_phi_tier() -> None:
    with pytest.raises(ValidationError):
        PowerScaleRequest(scale=1.0, phi_tier=11)


@given(capacity=valid_connect_capacity)
@settings(max_examples=100)
def test_connect_request_accepts_capacity_up_to_one_ehs(capacity: float) -> None:
    request = ConnectRequest(pool_id="nicehash", capacity_ehs=capacity)

    assert 0.01 <= request.capacity_ehs <= API_HASHRATE_CAP_EHS


@given(capacity=above_cap)
@settings(max_examples=100)
def test_connect_request_rejects_capacity_above_one_ehs(capacity: float) -> None:
    with pytest.raises(ValidationError):
        ConnectRequest(pool_id="nicehash", capacity_ehs=capacity)


@given(hashrate=above_cap)
@settings(max_examples=100)
def test_submit_job_rejects_reported_hashrate_above_one_ehs(hashrate: float) -> None:
    with pytest.raises(ValidationError):
        SubmitJobRequest(
            pool_id="nicehash",
            worker="PULVINI.singularity",
            job_id="job-property-cap",
            nonce="0x1",
            hashrate_ehs=hashrate,
        )


@given(raw_hashrate=finite_nonnegative)
@settings(max_examples=100)
def test_api_hashrate_clamp_never_exceeds_one_ehs(raw_hashrate: float) -> None:
    capped = _capped_hashrate_ehs(raw_hashrate)

    assert capped is not None
    assert 0.0 <= capped <= API_HASHRATE_CAP_EHS


@given(base_capacity=finite_nonnegative, scale=power_scales)
@settings(max_examples=100)
def test_power_scaled_api_hashrate_never_exceeds_one_ehs(
    base_capacity: float, scale: float
) -> None:
    effective = _effective_hashrate_ehs(base_capacity, scale)

    assert effective is not None
    assert 0.0 <= effective <= API_HASHRATE_CAP_EHS


@given(
    configured_capacity=st.floats(
        min_value=1e-9, max_value=10_000.0, allow_nan=False, allow_infinity=False
    ),
    scale=power_scales,
)
@settings(max_examples=100)
def test_solver_metrics_never_exceed_one_ehs(
    configured_capacity: float, scale: float
) -> None:
    solver = DodecahedralQuantumSolver(configured_capacity_ehs=configured_capacity)
    solver.set_power_scale(scale)

    metrics = solver.get_metrics()

    assert metrics["hashrate_cap_ehs"] == SOLVER_HASHRATE_CAP_EHS
    assert metrics["hashrate_ehs"] is not None
    assert 0.0 < metrics["hashrate_ehs"] <= SOLVER_HASHRATE_CAP_EHS


@given(configured_capacity=above_cap)
@settings(max_examples=100)
def test_solver_clamps_over_cap_configured_capacity_for_legacy_callers(
    configured_capacity: float,
) -> None:
    solver = DodecahedralQuantumSolver(configured_capacity_ehs=configured_capacity)

    assert solver.configured_capacity_ehs == SOLVER_HASHRATE_CAP_EHS
