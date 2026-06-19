from __future__ import annotations

import pytest

try:
    import numpy as np
except ModuleNotFoundError:  # pragma: no cover
    np = None

try:
    from hypothesis import given, settings
    from hypothesis import strategies as st
except ImportError:  # pragma: no cover
    given = settings = st = None

from pythia_mining.ctd_formalism import BuresManifold, HilbertState

pytestmark_numpy = pytest.mark.skipif(np is None, reason="numpy is not installed")


if given is not None:

    @pytestmark_numpy
    @settings(max_examples=500, deadline=None)
    @given(
        state_vector=st.lists(
            st.complex_numbers(allow_infinity=False, allow_nan=False), min_size=8, max_size=8
        )
    )
    def test_hilbert_normalization_invariant(state_vector: list[complex]) -> None:
        vec = np.array(state_vector, dtype=np.complex128)
        if np.linalg.norm(vec) == 0:
            return

        state = HilbertState(vector=vec)

        np.testing.assert_allclose(state.trace(), 1.0, atol=1e-7)
        eigenvals = state.eigenvalues()
        assert all(ev >= -1e-9 for ev in eigenvals)

    @settings(max_examples=128, deadline=None)
    @given(dim=st.integers(min_value=2, max_value=64))
    def test_manifold_stability_invariant(dim: int) -> None:
        manifold = BuresManifold(dimension=dim)
        curvature = manifold.compute_ricci_scalar()

        assert np.isfinite(curvature)
        assert curvature >= 0.0
else:

    @pytest.mark.skip(reason="hypothesis is not installed")
    def test_hilbert_normalization_invariant() -> None:
        pass

    @pytest.mark.skip(reason="hypothesis is not installed")
    def test_manifold_stability_invariant() -> None:
        pass
