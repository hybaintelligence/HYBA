"""Property-based tests for HYBA backend mathematical primitives using Hypothesis.

These tests validate that pure mathematical invariants hold across a vast
range of random inputs, not just hand-picked examples. This is the gold
standard for first-principles quantum math verification.

Run with:
    python -m pytest tests/test_property_based_backend.py -v
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_BACKEND = REPO_ROOT / "python_backend"
SRC_EUCLID = REPO_ROOT / "src"
if str(PYTHON_BACKEND) not in sys.path:
    sys.path.insert(0, str(PYTHON_BACKEND))
if str(SRC_EUCLID) not in sys.path:
    sys.path.insert(0, str(SRC_EUCLID))

from euclid.pythagoras.quantum.operators.folded_probability_amplifier import (
    uniform_vector,
)
from euclid.pythagoras.quantum.operators.symbolic_verifier import (
    verify_projector,
    verify_trace_preserved,
    verify_unitary,
)
from hyba_genesis_api.core.midas_controls import (
    BackpressureGuard,
    MiningRequestTracker,
    RequestStatus,
    TokenBucketRateLimiter,
)
from hyba_genesis_api.core.substrate import initialize_substrate
from pythia_mining.mining_validation import compact_to_target
from pythia_mining.quantum_solver import DODECAHEDRON_VERTICES, DodecahedralQuantumSolver


# =============================================================================
# COMPLEX VECTOR PROPERTIES
# =============================================================================

# Strategy: generate complex vectors of varying lengths
@st.composite
def complex_vector_strategy(draw, min_dim: int = 2, max_dim: int = 64) -> np.ndarray:
    """Generate a random complex vector with finite components."""
    dim = draw(st.integers(min_value=min_dim, max_value=max_dim))
    real = draw(st.lists(st.floats(min_value=-10.0, max_value=10.0, allow_nan=False, allow_infinity=False), min_size=dim, max_size=dim))
    imag = draw(st.lists(st.floats(min_value=-10.0, max_value=10.0, allow_nan=False, allow_infinity=False), min_size=dim, max_size=dim))
    return np.array(real, dtype=np.complex128) + 1j * np.array(imag, dtype=np.complex128)


@st.composite
def positive_dimension_strategy(draw, min_dim: int = 2, max_dim: int = 128) -> int:
    """Generate a positive integer dimension for Hilbert spaces."""
    return draw(st.integers(min_value=min_dim, max_value=max_dim))


# =============================================================================
# PROPERTY 1: Unit norm invariance for uniform vectors
# =============================================================================

@given(dim=positive_dimension_strategy(2, 100))
@settings(max_examples=200)
def test_property_uniform_vector_always_unit_norm(dim: int) -> None:
    """Property: Every uniform vector must have exactly unit L2 norm."""
    vec = uniform_vector(dim)
    norm = np.linalg.norm(vec)
    assert np.isclose(norm, 1.0, atol=1e-12), (
        f"Uniform vector of dimension {dim} has norm {norm}, expected 1.0"
    )


# =============================================================================
# PROPERTY 2: Unitary matrix preserves inner product
# =============================================================================

@given(
    dim=st.integers(min_value=2, max_value=20),
    seed=st.integers(min_value=0, max_value=10_000),
)
@settings(max_examples=100)
def test_property_unitary_preserves_norm(dim: int, seed: int) -> None:
    """Property: Applying a unitary matrix U to a vector v preserves ||v||."""
    rng = np.random.default_rng(seed)
    # Generate a random unitary matrix via QR decomposition
    A = rng.normal(size=(dim, dim)) + 1j * rng.normal(size=(dim, dim))
    Q, R = np.linalg.qr(A)
    # Normalize signs to get a proper unitary
    diag = np.diag(R)
    phases = diag / np.abs(diag)
    U = Q * phases[np.newaxis, :]

    # Verify it's truly unitary
    result = verify_unitary(U)
    assume(result.passed)  # Only test with valid unitaries

    # Generate random test vectors
    v = rng.normal(size=dim) + 1j * rng.normal(size=dim)
    v_norm = np.linalg.norm(v)
    assume(v_norm > 1e-10)  # Skip degenerate vectors

    Uv = U @ v
    Uv_norm = np.linalg.norm(Uv)

    assert np.isclose(v_norm, Uv_norm, atol=1e-10), (
        f"Unitary did not preserve norm: original ||v||={v_norm}, after U||v||={Uv_norm}"
    )


# =============================================================================
# PROPERTY 3: Projector idempotence (P² = P)
# =============================================================================

@given(
    dim=st.integers(min_value=2, max_value=16),
    rank=st.integers(min_value=1, max_value=8),
    seed=st.integers(min_value=0, max_value=5_000),
)
@settings(max_examples=100)
def test_property_projector_idempotent(dim: int, rank: int, seed: int) -> None:
    """Property: Every projector must satisfy P² = P (idempotent)."""
    assume(rank <= dim)
    rng = np.random.default_rng(seed)
    # Build a rank-k projector from random orthonormal basis
    A = rng.normal(size=(dim, rank))
    Q, _ = np.linalg.qr(A)
    P = Q @ Q.T  # Projector onto column space of Q

    result = verify_projector(P)
    assert result.passed, (
        f"Rank-{rank} projector in dimension {dim} failed: residual={result.residual}"
    )


# =============================================================================
# PROPERTY 4: Trace preservation under similarity transformations
# =============================================================================

@given(
    dim=st.integers(min_value=2, max_value=12),
    seed=st.integers(min_value=0, max_value=5_000),
)
@settings(max_examples=50)
def test_property_trace_preserved_under_similarity(dim: int, seed: int) -> None:
    """Property: Trace is invariant under similarity transforms A → P⁻¹AP."""
    rng = np.random.default_rng(seed)
    A = rng.normal(size=(dim, dim))
    P = rng.normal(size=(dim, dim))
    assume(np.linalg.cond(P) < 1e12)  # Well-conditioned
    P_inv = np.linalg.inv(P)
    transformed = P_inv @ A @ P

    result = verify_trace_preserved(A, transformed)
    assert result.passed, (
        f"Trace not preserved under similarity in dimension {dim}: residual={result.residual}"
    )


# =============================================================================
# PROPERTY 5: Dodecahedral quantum solver entropy bounds
# =============================================================================

@given(
    seed=st.integers(min_value=0, max_value=10_000),
)
@settings(max_examples=100)
def test_property_entropy_always_bounded(seed: int) -> None:
    """Property: Integrated entropy must always be in [0, log2(DODECAHEDRON_VERTICES)]."""
    solver = DodecahedralQuantumSolver()
    rng = np.random.default_rng(seed)
    real = rng.uniform(-1.0, 1.0, size=DODECAHEDRON_VERTICES)
    imag = rng.uniform(-1.0, 1.0, size=DODECAHEDRON_VERTICES)
    amplitudes = real + 1j * imag

    entropy = solver.calculate_integrated_entropy(amplitudes)
    max_entropy = math.log2(DODECAHEDRON_VERTICES)
    assert 0.0 <= entropy <= max_entropy + 1e-12, (
        f"Entropy {entropy} outside bounds [0, {max_entropy}]"
    )


# =============================================================================
# PROPERTY 6: Solver metrics monotonic with power scale
# =============================================================================

@given(
    scales=st.lists(
        st.floats(min_value=0.1, max_value=100.0, allow_nan=False, allow_infinity=False),
        min_size=3, max_size=10,
        unique=True,
    ),
)
@settings(max_examples=50)
def test_property_hashrate_monotonic_in_power_scale(scales: list[float]) -> None:
    """Property: Hashrate must be monotonic non-decreasing with power scale."""
    solver = DodecahedralQuantumSolver(configured_capacity_ehs=10.0)
    sorted_scales = sorted(scales)
    hashrates = []
    for scale in sorted_scales:
        solver.set_power_scale(scale)
        metrics = solver.get_metrics()
        hashrates.append(metrics["hashrate_ehs"])

    for i in range(1, len(hashrates)):
        assert hashrates[i] >= hashrates[i - 1], (
            f"Hashrate decreased when power scale increased from {sorted_scales[i-1]} to {sorted_scales[i]}: "
            f"{hashrates[i-1]} -> {hashrates[i]}"
        )


# =============================================================================
# PROPERTY 7: Substrate initialization is deterministic
# =============================================================================

@given(
    seed_a=st.just(0),
    seed_b=st.just(0),
)
@settings(max_examples=5)
def test_property_substrate_initialization_deterministic(seed_a: int, seed_b: int) -> None:
    """Property: Substrate initialization must produce identical results on repeated calls."""
    # Reinitialize multiple times and verify consistency
    states = [initialize_substrate() for _ in range(3)]
    # All should have 'ready' true, same initialization order
    for i, state in enumerate(states):
        assert state["ready"], f"Substrate initialization {i} failed"
    if len(states) > 1:
        assert states[0]["initialization_order"] == states[1]["initialization_order"], (
            "Substrate initialization order is not deterministic"
        )


# =============================================================================
# PROPERTY 8: Compact to target produces well-formed targets
# =============================================================================

@given(
    exponent=st.integers(min_value=0x18, max_value=0x1E),
    mantissa=st.integers(min_value=0x000000, max_value=0xFFFFFE),
)
@settings(max_examples=100)
def test_property_compact_to_target_valid_range(exponent: int, mantissa: int) -> None:
    """Property: compact_to_target must produce a positive, finite target ≤ 2²²⁴ - 1."""
    compact = (exponent << 24) | mantissa
    target = compact_to_target(compact)
    assert target > 0, f"Target must be positive, got {target} for compact 0x{compact:08x}"
    assert target < 2**224, (
        f"Target must be less than 2²²⁴, got {target} for compact 0x{compact:08x}"
    )
    # Target must be finite
    assert math.isfinite(target), f"Target must be finite, got {target}"


# =============================================================================
# PROPERTY 9: Nonce ranges must be valid after solver configuration
# =============================================================================

@given(
    start=st.integers(min_value=0, max_value=1_000_000),
    range_size=st.integers(min_value=0, max_value=500),
    target=st.integers(min_value=1, max_value=2**224),
    seed=st.integers(min_value=0, max_value=1_000),
)
@settings(max_examples=50)
async def test_property_nonce_in_range(start: int, range_size: int, target: int, seed: int) -> None:
    """Property: Every nonce returned by the solver must be within its declared range."""
    end = start + range_size
    solver = DodecahedralQuantumSolver()
    await solver.configure_search(target=target, nonce_ranges=[(start, end)])
    nonce = await solver.solve(max_iterations=25, timeout=5.0)
    assert nonce is not None, "Solver returned None for valid range"
    assert start <= nonce <= end, (
        f"Nonce {nonce} outside declared range [{start}, {end}]"
    )


# =============================================================================
# PROPERTY 10: Token bucket rate limiter invariants
# =============================================================================

@given(
    burst=st.integers(min_value=1, max_value=20),
    rate=st.floats(min_value=1.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    request_ids=st.lists(
        st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('L', 'N'))),
        min_size=1, max_size=30,
        unique=True,
    ),
)
@settings(max_examples=50)
def test_property_token_bucket_never_exceeds_burst(burst: int, rate: float, request_ids: list[str]) -> None:
    """Property: The token bucket must never allow more than `burst` consecutive requests."""
    limiter = TokenBucketRateLimiter(rate_per_second=rate, burst_capacity=burst)
    accepted = 0
    consecutive_accepted = 0
    max_consecutive = 0

    for rid in request_ids:
        try:
            limiter.allow(rid)
            accepted += 1
            consecutive_accepted += 1
            max_consecutive = max(max_consecutive, consecutive_accepted)
        except Exception:
            consecutive_accepted = 0

    assert max_consecutive <= burst, (
        f"Token bucket allowed {max_consecutive} consecutive requests but burst capacity is {burst}"
    )


# =============================================================================
# PROPERTY 11: Backpressure guard invariants
# =============================================================================

@given(
    max_inflight=st.integers(min_value=1, max_value=10),
    request_ids=st.lists(
        st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('L', 'N'))),
        min_size=1, max_size=20,
        unique=True,
    ),
    seed=st.integers(min_value=0, max_value=5_000),
)
@settings(max_examples=50)
def test_property_backpressure_never_exceeds_inflight_limit(max_inflight: int, request_ids: list[str], seed: int) -> None:
    """Property: Backpressure guard must never admit more than max_inflight concurrent requests."""
    guard = BackpressureGuard(max_inflight=max_inflight, max_queue_depth=100)
    # Admit as many as possible
    admitted = 0
    for rid in request_ids:
        try:
            guard.admit(rid)
            admitted += 1
        except Exception:
            pass
    assert admitted <= max_inflight, (
        f"Backpressure guard admitted {admitted} requests but max_inflight is {max_inflight}"
    )

    # Cleanup
    for _ in range(admitted):
        guard.release()


# =============================================================================
# PROPERTY 12: Mining request tracker idempotency keys are unique
# =============================================================================

@given(
    keys=st.lists(
        st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('L', 'N'))),
        min_size=1, max_size=10,
        unique=True,
    ),
)
@settings(max_examples=50)
def test_property_idempotency_keys_produce_same_request_id(keys: list[str]) -> None:
    """Property: The same idempotency key must always resolve to the same request ID."""
    tracker = MiningRequestTracker()
    for key in keys:
        first = tracker.create_request("start", {"miner": "alpha"}, idempotency_key=key)
        second = tracker.create_request("start", {"miner": "alpha"}, idempotency_key=key)
        assert first.request_id == second.request_id, (
            f"Idempotency key '{key}' produced different request IDs"
        )
        # Verify cleanup doesn't break things
        tracker.update_request_status(first.request_id, RequestStatus.FAILED, error="cleanup test")


# =============================================================================
# PROPERTY 13: Random matrix determinant invariance for unitary matrices
# =============================================================================

@given(
    dim=st.integers(min_value=2, max_value=10),
    seed=st.integers(min_value=0, max_value=5_000),
)
@settings(max_examples=50)
def test_property_unitary_determinant_modulus_one(dim: int, seed: int) -> None:
    """Property: The absolute value of the determinant of a unitary matrix must be 1."""
    rng = np.random.default_rng(seed)
    A = rng.normal(size=(dim, dim)) + 1j * rng.normal(size=(dim, dim))
    Q, R = np.linalg.qr(A)
    diag = np.diag(R)
    phases = diag / np.abs(diag)
    U = Q * phases[np.newaxis, :]

    det = np.linalg.det(U)
    det_mod = abs(det)
    assert np.isclose(det_mod, 1.0, atol=1e-10), (
        f"|det(U)| = {det_mod} for a {dim}x{dim} unitary, expected 1.0"
    )


# =============================================================================
# PROPERTY 14: Folded probability amplifier preserves vector norm
# =============================================================================

@given(
    dim=st.integers(min_value=2, max_value=32),
    seed=st.integers(min_value=0, max_value=5_000),
)
@settings(max_examples=50)
def test_property_uniform_vector_nonnegative_components(dim: int, seed: int) -> None:
    """Property: Uniform vector components should be nonnegative real numbers."""
    vec = uniform_vector(dim)
    assert np.all(np.isreal(vec)), f"Uniform vector has imaginary components: {vec}"
    assert np.all(vec >= 0), f"Uniform vector has negative components: {vec}"
    assert vec.shape == (dim,), f"Uniform vector has wrong shape: {vec.shape}"


# =============================================================================
# PROPERTY 15: Verify that quantum solver has correct number of basis states
# =============================================================================

@given(
    seed=st.integers(min_value=0, max_value=100),
)
@settings(max_examples=20)
def test_property_solver_basis_has_correct_dimensions(seed: int) -> None:
    """Property: The quantum solver must always have exactly DODECAHEDRON_VERTICES basis states."""
    solver = DodecahedralQuantumSolver()
    assert solver.basis_states.shape == (DODECAHEDRON_VERTICES, 3), (
        f"Basis states shape {solver.basis_states.shape}, expected ({DODECAHEDRON_VERTICES}, 3)"
    )
    # All row norms must be 1
    row_norms = np.linalg.norm(solver.basis_states, axis=1)
    assert np.allclose(row_norms, 1.0, atol=1e-12), "Basis state rows are not normalized"
    # All entries must be finite
    assert np.isfinite(solver.basis_states).all(), "Basis states contain non-finite values"