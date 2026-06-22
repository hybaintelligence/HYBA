"""Evidence tests for the HYBA quantum finance vertical.

These tests turn the finance blueprint into repo-native evidence. They verify
that HYBA implements finance-specific QUBO/QAOA and QAE/VaR design packets over
QaaS/QIaaS/CIaaS without exposing mining as a product surface.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from hyba_genesis_api.api.quantum_finance_service import (  # noqa: E402
    PortfolioOptimizationRequest,
    RiskPricingRequest,
    construct_portfolio_qubo,
    design_portfolio_qaoa,
    design_risk_qae,
    qubo_to_ising,
)


def _portfolio_request() -> PortfolioOptimizationRequest:
    return PortfolioOptimizationRequest(
        expected_returns=[0.08, 0.12, 0.05, 0.10],
        covariance_matrix=[
            [0.10, 0.02, 0.01, 0.03],
            [0.02, 0.20, 0.04, 0.01],
            [0.01, 0.04, 0.08, 0.02],
            [0.03, 0.01, 0.02, 0.12],
        ],
        budget=2,
        risk_aversion=0.8,
        return_weight=1.4,
        target_return=0.18,
        transaction_costs=[0.002, 0.003, 0.001, 0.002],
        liquidity_scores=[0.9, 0.7, 0.8, 1.0],
        liquidity_penalty=0.05,
        regulatory_constraints={
            "sector_caps": {"growth": [0, 1], "defensive": [2, 3]},
            "max_per_sector": 1,
            "sector_penalty": 2.5,
        },
        surface="qiaas",
        qaoa_layers=4,
    )


def test_portfolio_finance_qubo_and_ising_are_generated_from_domain_terms() -> None:
    request = _portfolio_request()
    qubo = construct_portfolio_qubo(request)
    ising = qubo_to_ising(qubo)

    assert len(qubo) == len(request.expected_returns)
    assert all(len(row) == len(request.expected_returns) for row in qubo)
    assert any(abs(qubo[i][j]) > 0 for i in range(4) for j in range(i + 1, 4))
    assert ising["hamiltonian_form"] == "H = constant + Σ h_i Z_i + Σ J_ij Z_i Z_j"
    assert set(ising["fields"].keys()) == {"z0", "z1", "z2", "z3"}
    assert "z0z1" in ising["couplers"]


def test_portfolio_qaoa_design_returns_auditable_finance_packet_not_trade_execution() -> None:
    design = design_portfolio_qaoa(_portfolio_request())

    assert design["surface"] == "qiaas"
    assert design["asset_count"] == 4
    assert design["qaoa_circuit_design"]["encoding"] == "binary_asset_selection_qubits"
    assert design["qaoa_circuit_design"]["layers"] == 4
    assert "regulatory_constraint_penalty" in design["qaoa_circuit_design"]["finance_specific_terms"]
    assert len(design["selected_candidate"]["selected_indices"]) == 2
    assert design["selected_candidate"]["selection_mode"] == "exact_enumeration"
    assert design["evidence_packet"].claim_class == "A"
    assert design["evidence_packet"].product_boundary == "public_quantum_finance_vertical_not_mining"
    assert "not autonomous trade execution" in " ".join(design["evidence_packet"].verification_notes)


def test_risk_qae_design_records_quadratic_speedup_accounting_and_var_cvar() -> None:
    request = RiskPricingRequest(
        payoff_samples=[-2.0, -1.0, 0.0, 0.5, 1.0, 2.5, 4.0, 8.0],
        confidence_level=0.875,
        precision_epsilon=0.05,
        instrument_type="multi_asset_option_payoff",
        surface="qaas",
    )
    design = design_risk_qae(request)

    assert design["surface"] == "qaas"
    assert design["instrument_type"] == "multi_asset_option_payoff"
    assert design["pricing_summary"]["expected_payoff"] == pytest.approx(1.625)
    assert design["risk_summary"]["value_at_risk"] == pytest.approx(4.0)
    assert design["risk_summary"]["conditional_value_at_risk"] == pytest.approx(6.0)
    assert design["qae_design"]["amplitude_estimation_iterations"] < design["qae_design"]["classical_monte_carlo_samples_for_same_epsilon"]
    assert design["qae_design"]["quadratic_speedup_accounting_factor"] > 1.0
    assert design["evidence_packet"].claim_boundary.startswith("implemented_and_tested_finance_specific")


def test_quantum_finance_is_wired_as_public_vertical_but_not_mining_product() -> None:
    main = (ROOT / "python_backend" / "hyba_genesis_api" / "main.py").read_text(encoding="utf-8")
    module = (ROOT / "python_backend" / "hyba_genesis_api" / "api" / "quantum_finance_service.py").read_text(encoding="utf-8")

    assert "quantum_finance_service" in main
    assert "app.include_router(quantum_finance_service.router)" in main
    assert "prefix=\"/api/quantum-finance\"" in module
    assert "require_customer_api_key" in module
    assert "customer_access.meter" in module
    assert "not mining" in module.lower() or "not_mining" in module.lower()
