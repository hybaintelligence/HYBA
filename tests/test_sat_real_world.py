from __future__ import annotations

from pythia_mining.unified_search_kernel import SatGeodesicDomain, UnifiedSearchKernel


def test_solve_real_sat_problem() -> None:
    clauses = [[1, 2, -3], [-1, -2, 3], [2, 3, 1]]
    domain = SatGeodesicDomain(num_variables=3, clauses=clauses)
    kernel = UnifiedSearchKernel(domain)

    result = kernel.search(budget=100)

    assert result.success is True
    assert result.score == 1.0
    assert result.iterations <= 100
