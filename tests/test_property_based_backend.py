"""Property-based tests for HYBA backend mathematical primitives using Hypothesis.

These tests validate that pure mathematical invariants hold across a vast
range of random inputs, not just hand-picked examples. This is the gold
standard for first-principles quantum math verification.

Run with:
    PYTHONPATH=python_backend python -m pytest tests/test_property_based_backend.py -v
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_BACKEND = str(REPO_ROOT / "python_backend")
if PYTHON_BACKEND not in sys.path:
    sys.path.insert(0, PYTHON_BACKEND)


# =============================================================================
# STRATEGIES
# =============================================================================


@st.composite
def positive_dimension_strategy(draw, min_dim: int = 2, max_dim: int = 128) -> int:
    """Generate a positive integer dimension for Hilbert spaces."""
    return draw(st.integers(min_value=min_dim, max_value=max_dim))


# =============================================================================
# PROPERTY 1: Compact to target produces well-formed targets
# =============================================================================


@pytest.mark.skipif(
    "pythia_mining.mining_validation" not in sys.modules and __import__ is not None,
    reason="mining_validation module not available",
)
@given(
    exponent=st.integers(min_value=0x18, max_value=0x1E),
    mantissa=st.integers(min_value=0x000000, max_value=0xFFFFFE),
)
@settings(max_examples=100)
def test_property_compact_to_target_valid_range(exponent: int, mantissa: int) -> None:
    """Property: compact_to_target must produce a positive, finite target ≤ 2²²⁴ - 1."""
    from pythia_mining.mining_validation import compact_to_target

    compact = (exponent << 24) | mantissa
    target = compact_to_target(compact)
    assert target > 0, f"Target must be positive, got {target} for compact 0x{compact:08x}"
    assert (
        target < 2**224
    ), f"Target must be less than 2²²⁴, got {target} for compact 0x{compact:08x}"
    assert math.isfinite(target), f"Target must be finite, got {target}"


# =============================================================================
# PROPERTY 2: Quantum solver entropy bounds
# =============================================================================


@given(
    seed=st.integers(min_value=0, max_value=10_000),
)
@settings(max_examples=100)
def test_property_entropy_always_bounded(seed: int) -> None:
    """Property: Integrated entropy must always be in [0, log2(DODECAHEDRON_VERTICES)]."""
    from pythia_mining.quantum_solver import (
        DODECAHEDRON_VERTICES,
        DodecahedralQuantumSolver,
    )

    solver = DodecahedralQuantumSolver()
    rng = np.random.default_rng(seed)
    real = rng.uniform(-1.0, 1.0, size=DODECAHEDRON_VERTICES)
    imag = rng.uniform(-1.0, 1.0, size=DODECAHEDRON_VERTICES)
    amplitudes = real + 1j * imag

    entropy = solver.calculate_integrated_entropy(amplitudes)
    max_entropy = math.log2(DODECAHEDRON_VERTICES)
    assert (
        0.0 <= entropy <= max_entropy + 1e-12
    ), f"Entropy {entropy} outside bounds [0, {max_entropy}]"


# =============================================================================
# PROPERTY 3: Solver metrics monotonic with power scale
# =============================================================================


@given(
    scales=st.lists(
        st.floats(min_value=0.1, max_value=100.0, allow_nan=False, allow_infinity=False),
        min_size=3,
        max_size=10,
        unique=True,
    ),
)
@settings(max_examples=50)
def test_property_hashrate_monotonic_in_power_scale(scales: list[float]) -> None:
    """Property: Hashrate must be monotonic non-decreasing with power scale."""
    from pythia_mining.quantum_solver import DodecahedralQuantumSolver

    solver = DodecahedralQuantumSolver(configured_capacity_ehs=10.0)
    sorted_scales = sorted(scales)
    hashrates = []
    for scale in sorted_scales:
        solver.set_power_scale(scale)
        metrics = solver.get_metrics()
        hashrates.append(metrics["hashrate_ehs"])

    for i in range(1, len(hashrates)):
        assert hashrates[i] >= hashrates[i - 1], (
            f"Hashrate decreased when power scale increased from {sorted_scales[i - 1]} to {sorted_scales[i]}: "
            f"{hashrates[i - 1]} -> {hashrates[i]}"
        )


# =============================================================================
# PROPERTY 4: Solver basis has correct dimensions
# =============================================================================


@given(
    seed=st.integers(min_value=0, max_value=100),
)
@settings(max_examples=20)
def test_property_solver_basis_has_correct_dimensions(seed: int) -> None:
    """Property: The quantum solver must always have exactly DODECAHEDRON_VERTICES basis states."""
    from pythia_mining.quantum_solver import (
        DODECAHEDRON_VERTICES,
        DodecahedralQuantumSolver,
    )

    solver = DodecahedralQuantumSolver()
    assert solver.basis_states.shape == (
        DODECAHEDRON_VERTICES,
        3,
    ), f"Basis states shape {solver.basis_states.shape}, expected ({DODECAHEDRON_VERTICES}, 3)"
    # All row norms must be 1
    row_norms = np.linalg.norm(solver.basis_states, axis=1)
    assert np.allclose(row_norms, 1.0, atol=1e-12), "Basis state rows are not normalized"
    # All entries must be finite
    assert np.isfinite(solver.basis_states).all(), "Basis states contain non-finite values"


# =============================================================================
# PROPERTY 5: Substrate initialization is deterministic
# =============================================================================


@settings(max_examples=5)
def test_property_substrate_initialization_deterministic() -> None:
    """Property: Substrate initialization must produce identical results on repeated calls."""
    from hyba_genesis_api.core.substrate import (
        initialize_substrate,
        shutdown_substrate,
    )

    # Reinitialize multiple times and verify consistency
    states = []
    for _ in range(3):
        state = initialize_substrate()
        states.append(state)

    # All should have 'ready' true, same initialization order
    for i, state in enumerate(states):
        assert state["ready"], f"Substrate initialization {i} failed"
    assert (
        states[0]["initialization_order"] == states[1]["initialization_order"]
    ), "Substrate initialization order is not deterministic"

    shutdown_state = shutdown_substrate()
    assert shutdown_state["shutdown_at"] is not None
    assert isinstance(shutdown_state["shutdown_at"], str)


# =============================================================================
# PROPERTY 6: Token bucket rate limiter invariants
# =============================================================================


@given(
    burst=st.integers(min_value=1, max_value=20),
    rate=st.floats(min_value=1.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    request_ids=st.lists(
        st.text(
            min_size=1,
            max_size=10,
            alphabet=st.characters(whitelist_categories=("L", "N")),
        ),
        min_size=1,
        max_size=30,
        unique=True,
    ),
)
@settings(max_examples=50)
def test_property_token_bucket_never_exceeds_burst(
    burst: int, rate: float, request_ids: list[str]
) -> None:
    """Property: The token bucket must never allow more than `burst` consecutive requests."""
    from hyba_genesis_api.core.midas_controls import TokenBucketRateLimiter

    limiter = TokenBucketRateLimiter(rate_per_second=rate, burst_capacity=burst)
    consecutive_accepted = 0
    max_consecutive = 0

    for rid in request_ids:
        try:
            limiter.allow(rid)
            consecutive_accepted += 1
            max_consecutive = max(max_consecutive, consecutive_accepted)
        except Exception:
            consecutive_accepted = 0

    assert (
        max_consecutive <= burst
    ), f"Token bucket allowed {max_consecutive} consecutive requests but burst capacity is {burst}"


# =============================================================================
# PROPERTY 7: Backpressure guard invariants
# =============================================================================


@given(
    max_inflight=st.integers(min_value=1, max_value=10),
    request_ids=st.lists(
        st.text(
            min_size=1,
            max_size=10,
            alphabet=st.characters(whitelist_categories=("L", "N")),
        ),
        min_size=1,
        max_size=20,
        unique=True,
    ),
)
@settings(max_examples=50)
def test_property_backpressure_never_exceeds_inflight_limit(
    max_inflight: int, request_ids: list[str]
) -> None:
    """Property: Backpressure guard must never admit more than max_inflight concurrent requests."""
    from hyba_genesis_api.core.midas_controls import BackpressureGuard

    guard = BackpressureGuard(max_inflight=max_inflight, max_queue_depth=100)
    # Admit as many as possible
    admitted = 0
    for rid in request_ids:
        try:
            guard.admit(rid)
            admitted += 1
        except Exception:
            pass
    assert (
        admitted <= max_inflight
    ), f"Backpressure guard admitted {admitted} requests but max_inflight is {max_inflight}"

    # Cleanup
    for _ in range(admitted):
        guard.release()


# =============================================================================
# PROPERTY 8: Mining request tracker idempotency keys
# =============================================================================


@given(
    keys=st.lists(
        st.text(
            min_size=1,
            max_size=20,
            alphabet=st.characters(whitelist_categories=("L", "N")),
        ),
        min_size=1,
        max_size=10,
        unique=True,
    ),
)
@settings(max_examples=50)
def test_property_idempotency_keys_produce_same_request_id(keys: list[str]) -> None:
    """Property: The same idempotency key must always resolve to the same request ID."""
    from hyba_genesis_api.core.midas_controls import MiningRequestTracker, RequestStatus

    tracker = MiningRequestTracker()
    for key in keys:
        first = tracker.create_request("start", {"miner": "alpha"}, idempotency_key=key)
        second = tracker.create_request("start", {"miner": "alpha"}, idempotency_key=key)
        assert (
            first.request_id == second.request_id
        ), f"Idempotency key '{key}' produced different request IDs"
        # Verify cleanup doesn't break things
        tracker.update_request_status(first.request_id, RequestStatus.FAILED, error="cleanup test")


# =============================================================================
# PROPERTY 9: Nonce ranges must be valid after solver configuration
# =============================================================================


@given(
    start=st.integers(min_value=0, max_value=1_000_000),
    range_size=st.integers(min_value=0, max_value=500),
    target=st.integers(min_value=1, max_value=2**224),
)
@settings(max_examples=50)
async def test_property_nonce_in_range(start: int, range_size: int, target: int) -> None:
    """Property: Every nonce returned by the solver must be within its declared range."""
    from pythia_mining.quantum_solver import DodecahedralQuantumSolver

    end = start + range_size
    solver = DodecahedralQuantumSolver()
    await solver.configure_search(target=target, nonce_ranges=[(start, end)])
    nonce = await solver.solve(max_iterations=25, timeout=5.0)
    assert nonce is not None, "Solver returned None for valid range"
    assert start <= nonce <= end, f"Nonce {nonce} outside declared range [{start}, {end}]"


# =============================================================================
# PROPERTY 10: Uniform vector norm properties
# =============================================================================


@given(dim=positive_dimension_strategy(2, 100))
@settings(max_examples=200)
def test_property_uniform_vector_always_unit_norm(dim: int) -> None:
    """Property: Every uniform vector must have exactly unit L2 norm.

    This test directly tests the folded_probability_amplifier module.
    """
    # Import the module directly - it's the most isolated
    import importlib.util

    spec = importlib.util.find_spec(
        "euclid.pythagoras.quantum.operators.folded_probability_amplifier"
    )
    if spec is None:
        pytest.skip("pythagoras module not available")

    from euclid.pythagoras.quantum.operators.folded_probability_amplifier import (
        uniform_vector,
    )

    vec = uniform_vector(dim)
    norm = np.linalg.norm(vec)
    assert np.isclose(
        norm, 1.0, atol=1e-12
    ), f"Uniform vector of dimension {dim} has norm {norm}, expected 1.0"

# =============================================================================
# PROPERTY 7: Merkle-root determinism and byte sensitivity
# =============================================================================


@st.composite
def mining_job_strategy(draw):
    """Generate structurally valid, side-effect-free Stratum mining jobs."""
    from pythia_mining.stratum_client import MiningJob

    coinbase1 = draw(st.binary(min_size=1, max_size=32)).hex()
    coinbase2 = draw(st.binary(min_size=1, max_size=32)).hex()
    extranonce1 = draw(st.binary(min_size=0, max_size=8)).hex()
    extranonce2_size = draw(st.integers(min_value=0, max_value=8))
    merkle_branch = draw(
        st.lists(st.binary(min_size=32, max_size=32).map(bytes.hex), min_size=0, max_size=6)
    )
    return MiningJob(
        job_id=draw(
            st.text(
                min_size=1,
                max_size=24,
                alphabet=st.characters(whitelist_categories=("L", "N")),
            )
        ),
        prevhash=draw(st.binary(min_size=32, max_size=32)).hex(),
        coinbase_parts=(coinbase1, coinbase2),
        merkle_branch=merkle_branch,
        version=draw(st.binary(min_size=4, max_size=4)).hex(),
        nbits="1d00ffff",
        ntime=draw(st.binary(min_size=4, max_size=4)).hex(),
        target=int("00000000ffff" + "0" * 52, 16),
        extranonce1=extranonce1,
        extranonce2_size=extranonce2_size,
    )


@given(job=mining_job_strategy(), extranonce_seed=st.binary(min_size=8, max_size=8))
@settings(max_examples=100, deadline=None)
def test_property_merkle_root_is_deterministic_and_byte_sensitive(
    job, extranonce_seed: bytes
) -> None:
    """Property: identical coinbase/branch inputs produce one 32-byte root; any byte flip changes it."""
    from pythia_mining.mining_validation import coinbase_hash_hex, compute_merkle_root

    extranonce2 = extranonce_seed[: job.extranonce2_size].hex()
    coinbase_hash = coinbase_hash_hex(job, extranonce2)
    first_root = compute_merkle_root(coinbase_hash, job.merkle_branch)
    second_root = compute_merkle_root(coinbase_hash, list(job.merkle_branch))

    assert first_root == second_root
    assert len(first_root) == 64
    assert int(first_root, 16) >= 0

    mutated = bytearray(bytes.fromhex(coinbase_hash))
    mutated[0] ^= 0x01
    assert compute_merkle_root(mutated.hex(), job.merkle_branch) != first_root

# =============================================================================
# PROPERTY 8: PULVINI phi-folding compression is reversible
# =============================================================================


@given(
    values=st.lists(
        st.floats(
            min_value=-1_000.0,
            max_value=1_000.0,
            allow_nan=False,
            allow_infinity=False,
            width=32,
        ),
        min_size=2,
        max_size=89,
    )
)
@settings(max_examples=75, deadline=None)
def test_property_phi_folding_compression_round_trips_generated_vectors(
    values: list[float],
) -> None:
    """Property: retained phi-fold kernels reconstruct every generated dense vector."""
    from pythia_mining.phi_folding import PhiFoldingOperator

    operator = PhiFoldingOperator()
    payload = np.asarray(values, dtype=np.float64)
    folded, kernel, original_size = operator.fold(payload)
    reconstructed = operator.unfold(folded, kernel, original_size)

    assert original_size == payload.size
    assert folded.size <= payload.size
    assert kernel.size == folded.size
    assert np.allclose(reconstructed, payload, rtol=1e-9, atol=1e-9)


# =============================================================================
# PROPERTY 9: Phi-scaled ensemble decisions remain bounded and auditable
# =============================================================================


@given(
    scores=st.lists(
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        min_size=1,
        max_size=12,
    ),
    indicator_values=st.lists(
        st.floats(min_value=-10.0, max_value=10.0, allow_nan=False, allow_infinity=False),
        min_size=1,
        max_size=12,
    ),
)
@settings(max_examples=75, deadline=None)
def test_property_phi_scaled_ensemble_outputs_stay_bounded(
    scores: list[float], indicator_values: list[float]
) -> None:
    """Property: golden-ratio scaling cannot emit out-of-range decisions."""
    from pythia_mining.phi_scaling_engine import PhiScaledEnsemble

    engine = PhiScaledEnsemble({"memory_limit": 8})
    predictions = {f"model_{index:02d}": {"score": score} for index, score in enumerate(scores)}
    indicators = {
        "quantum": {f"q_{index:02d}": value for index, value in enumerate(indicator_values)}
    }

    result = engine.predict_with_phi_scaling(predictions, indicators)
    weights = result["phi_weights"]

    assert result["method"] == "golden_ratio_scaling"
    assert len(weights) == len(scores)
    assert all(math.isfinite(float(weight)) and float(weight) > 0.0 for weight in weights)
    assert 0.0 <= result["phi_score"] <= 1.0
    assert 0.0 <= result["indicator_harmony"] <= 1.0
    assert 0.0 <= result["final_score"] <= 1.0
    assert 0.0 <= result["coherence"] <= 1.0
    assert len(engine.memory) <= 8
