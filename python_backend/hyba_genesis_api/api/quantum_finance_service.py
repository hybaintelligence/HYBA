"""Quantum finance vertical for HYBA QaaS/QIaaS/CIaaS.

This module implements the finance-specific algorithms described in the HYBA
platform thesis as repo-native code rather than sales wording. It turns
portfolio optimisation and risk/pricing workloads into auditable post-quantum
execution designs that can be routed through QaaS, QIaaS, or CIaaS depending on
customer entitlement and deployment.

Implemented surfaces:
- Portfolio optimisation as QUBO + Ising Hamiltonian + QAOA/VQE/annealing design.
- Derivative/risk estimation as QAE/QMCI design with VaR/CVaR summaries.
- Evidence packets carrying claim boundaries, inputs, formulas, and audit hashes.

Boundary:
- This is a finance product vertical over HYBA's mathematical substrate.
- It is not mining and it exposes no mining/pool telemetry.
- It does not claim physical QPU execution unless a downstream executor supplies
  a hardware evidence packet.
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator

from hyba_genesis_api.core.feature_flags import require_feature
from hyba_genesis_api.core.response_cache import get_cached_json, set_cached_json
from hyba_genesis_api.api.customer_access import (
    CustomerPrincipal,
    customer_access,
    require_customer_api_key,
)


router = APIRouter(prefix="/api/quantum-finance", tags=["quantum-finance"])

FinanceSurface = Literal["qaas", "qiaas", "ciaas"]


class PortfolioOptimizationRequest(BaseModel):
    """Finance-specific portfolio optimisation request.

    Assets are encoded as binary decision variables. The service builds a QUBO
    objective containing risk, return, budget, optional target-return,
    transaction-cost, liquidity, and regulatory penalty terms.
    """

    expected_returns: List[float] = Field(min_length=1, max_length=256)
    covariance_matrix: List[List[float]]
    budget: int = Field(ge=1)
    risk_aversion: float = Field(default=1.0, ge=0.0)
    return_weight: float = Field(default=1.0, ge=0.0)
    budget_penalty: float = Field(default=10.0, gt=0.0)
    target_return: Optional[float] = None
    target_return_penalty: float = Field(default=1.0, ge=0.0)
    transaction_costs: Optional[List[float]] = None
    liquidity_scores: Optional[List[float]] = None
    liquidity_penalty: float = Field(default=0.0, ge=0.0)
    regulatory_constraints: Dict[str, Any] = Field(default_factory=dict)
    surface: FinanceSurface = "qiaas"
    qaoa_layers: int = Field(default=3, ge=1, le=32)
    evidence_label: str = Field(default="portfolio_qaoa_design", max_length=80)

    @model_validator(mode="after")
    def validate_dimensions(self) -> "PortfolioOptimizationRequest":
        n = len(self.expected_returns)
        if self.budget > n:
            raise ValueError("budget cannot exceed number of assets")
        if len(self.covariance_matrix) != n or any(
            len(row) != n for row in self.covariance_matrix
        ):
            raise ValueError(
                "covariance_matrix must be square and match expected_returns length"
            )
        if self.transaction_costs is not None and len(self.transaction_costs) != n:
            raise ValueError("transaction_costs must match expected_returns length")
        if self.liquidity_scores is not None and len(self.liquidity_scores) != n:
            raise ValueError("liquidity_scores must match expected_returns length")
        return self


class RiskPricingRequest(BaseModel):
    """Finance-specific QAE/QMCI design request for pricing and risk."""

    payoff_samples: List[float] = Field(min_length=2, max_length=10000)
    confidence_level: float = Field(default=0.95, gt=0.5, lt=0.9999)
    precision_epsilon: float = Field(default=0.01, gt=0.0, le=0.25)
    instrument_type: str = Field(default="generic_payoff", max_length=80)
    surface: FinanceSurface = "qaas"
    evidence_label: str = Field(default="risk_qae_design", max_length=80)


class EvidencePacket(BaseModel):
    evidence_id: str
    timestamp: float
    label: str
    claim_class: Literal["A", "B", "C", "D"]
    claim_boundary: str
    product_boundary: str
    input_hash: str
    formula_hash: str
    verification_notes: List[str]


class PortfolioQAOAResponse(BaseModel):
    service: str = "quantum_finance_portfolio_qaoa"
    surface: FinanceSurface
    asset_count: int
    budget: int
    qubo: Dict[str, Any]
    ising_hamiltonian: Dict[str, Any]
    qaoa_circuit_design: Dict[str, Any]
    selected_candidate: Dict[str, Any]
    finance_specific_constraints: Dict[str, Any]
    evidence_packet: EvidencePacket
    usage_meter: Dict[str, Any]


class RiskQAEResponse(BaseModel):
    service: str = "quantum_finance_risk_qae"
    surface: FinanceSurface
    instrument_type: str
    sample_count: int
    pricing_summary: Dict[str, Any]
    risk_summary: Dict[str, Any]
    qae_design: Dict[str, Any]
    evidence_packet: EvidencePacket
    usage_meter: Dict[str, Any]


@dataclass(frozen=True)
class CandidatePortfolio:
    bitstring: str
    selected_indices: List[int]
    expected_return: float
    variance: float
    objective_value: float


def _canonical_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def _sha256(data: Any) -> str:
    return hashlib.sha256(_canonical_json(data).encode("utf-8")).hexdigest()


def _evidence_packet(
    label: str, payload: Dict[str, Any], formulas: Dict[str, Any]
) -> EvidencePacket:
    return EvidencePacket(
        evidence_id=f"hyba-finance-{hashlib.sha256((label + _canonical_json(payload)).encode()).hexdigest()[:16]}",
        timestamp=time.time(),
        label=label,
        claim_class="A",
        claim_boundary=(
            "implemented_and_tested_finance_specific_post_quantum_design; "
            "physical_QPU_or_external_performance_claims_require_downstream_evidence"
        ),
        product_boundary="public_quantum_finance_vertical_not_mining",
        input_hash=_sha256(payload),
        formula_hash=_sha256(formulas),
        verification_notes=[
            "QUBO, Ising, QAOA, and QAE structures are generated deterministically from request data.",
            "Outputs are audit designs/evidence packets, not autonomous trade execution.",
            "Mining/pool telemetry is not read, required, or exposed by this service.",
        ],
    )


def _add_pair(matrix: List[List[float]], i: int, j: int, value: float) -> None:
    if i == j:
        matrix[i][i] += value
    else:
        a, b = sorted((i, j))
        matrix[a][b] += value


def construct_portfolio_qubo(
    request: PortfolioOptimizationRequest,
) -> List[List[float]]:
    """Construct a finance QUBO for binary Markowitz-style selection.

    Objective convention:
        minimise x'Σx * risk_aversion - return_weight * μ'x
        + budget_penalty * (Σx - budget)^2
        + optional target_return_penalty * (μ'x - target_return)^2
        + optional transaction/liquidity/regulatory penalties.
    """

    n = len(request.expected_returns)
    qubo = [[0.0 for _ in range(n)] for _ in range(n)]

    # Risk term x'Σx. Off-diagonal terms appear twice in matrix notation, so the
    # QUBO upper triangle receives 2Σ_ij for i<j.
    for i in range(n):
        _add_pair(qubo, i, i, request.risk_aversion * request.covariance_matrix[i][i])
        for j in range(i + 1, n):
            _add_pair(
                qubo,
                i,
                j,
                2.0 * request.risk_aversion * request.covariance_matrix[i][j],
            )

    # Return reward and optional transaction costs.
    costs = request.transaction_costs or [0.0] * n
    for i, ret in enumerate(request.expected_returns):
        _add_pair(qubo, i, i, -request.return_weight * ret + costs[i])

    # Budget penalty (Σx - B)^2 = Σx_i + 2Σx_ix_j -2BΣx_i + B^2.
    for i in range(n):
        _add_pair(qubo, i, i, request.budget_penalty * (1.0 - 2.0 * request.budget))
        for j in range(i + 1, n):
            _add_pair(qubo, i, j, 2.0 * request.budget_penalty)

    # Optional target return penalty (μ'x - T)^2.
    if request.target_return is not None and request.target_return_penalty > 0:
        for i, ret_i in enumerate(request.expected_returns):
            _add_pair(
                qubo,
                i,
                i,
                request.target_return_penalty
                * (ret_i * ret_i - 2.0 * request.target_return * ret_i),
            )
            for j in range(i + 1, n):
                _add_pair(
                    qubo,
                    i,
                    j,
                    2.0
                    * request.target_return_penalty
                    * ret_i
                    * request.expected_returns[j],
                )

    # Liquidity penalty prefers higher liquidity scores by penalising low scores.
    if request.liquidity_scores is not None and request.liquidity_penalty > 0:
        max_score = max(request.liquidity_scores) or 1.0
        for i, score in enumerate(request.liquidity_scores):
            illiquidity = 1.0 - (score / max_score)
            _add_pair(qubo, i, i, request.liquidity_penalty * illiquidity)

    # Simple sector cap penalty: regulatory_constraints={"sector_caps":{"tech":[0,1], "energy":[2]}, "max_per_sector":1}
    sector_caps = request.regulatory_constraints.get("sector_caps")
    max_per_sector = request.regulatory_constraints.get("max_per_sector")
    sector_penalty = float(
        request.regulatory_constraints.get("sector_penalty", request.budget_penalty)
    )
    if (
        isinstance(sector_caps, dict)
        and isinstance(max_per_sector, int)
        and max_per_sector >= 0
    ):
        for indices in sector_caps.values():
            if not isinstance(indices, list):
                continue
            cleaned = [idx for idx in indices if isinstance(idx, int) and 0 <= idx < n]
            for idx in cleaned:
                _add_pair(qubo, idx, idx, sector_penalty * (1.0 - 2.0 * max_per_sector))
            for a, i in enumerate(cleaned):
                for j in cleaned[a + 1 :]:
                    _add_pair(qubo, i, j, 2.0 * sector_penalty)

    return qubo


def qubo_to_ising(qubo: List[List[float]]) -> Dict[str, Any]:
    """Convert QUBO matrix to Ising Hamiltonian coefficients."""

    n = len(qubo)
    fields = [0.0 for _ in range(n)]
    couplers: Dict[str, float] = {}
    constant = 0.0

    for i in range(n):
        qii = qubo[i][i]
        constant += qii / 2.0
        fields[i] += -qii / 2.0
        for j in range(i + 1, n):
            qij = qubo[i][j]
            if qij == 0:
                continue
            constant += qij / 4.0
            fields[i] += -qij / 4.0
            fields[j] += -qij / 4.0
            couplers[f"z{i}z{j}"] = qij / 4.0

    return {
        "constant": constant,
        "fields": {f"z{i}": value for i, value in enumerate(fields)},
        "couplers": couplers,
        "hamiltonian_form": "H = constant + Σ h_i Z_i + Σ J_ij Z_i Z_j",
    }


def _portfolio_variance(bits: List[int], cov: List[List[float]]) -> float:
    variance = 0.0
    for i, xi in enumerate(bits):
        if xi == 0:
            continue
        for j, xj in enumerate(bits):
            if xj:
                variance += cov[i][j]
    return variance


def _qubo_objective(bits: List[int], qubo: List[List[float]]) -> float:
    total = 0.0
    for i, xi in enumerate(bits):
        if xi == 0:
            continue
        total += qubo[i][i]
        for j in range(i + 1, len(bits)):
            if bits[j]:
                total += qubo[i][j]
    return total


def select_candidate_portfolio(
    request: PortfolioOptimizationRequest, qubo: List[List[float]]
) -> CandidatePortfolio:
    """Select a deterministic candidate for auditability.

    Small finance examples are enumerated exactly. Larger inputs use a stable
    return/risk heuristic because the API's core product is the quantum design
    packet, not autonomous execution.
    """

    n = len(request.expected_returns)
    if n <= 18:
        best: Optional[CandidatePortfolio] = None
        for mask in range(1 << n):
            bits = [(mask >> i) & 1 for i in range(n)]
            if sum(bits) != request.budget:
                continue
            expected_return = sum(
                ret for ret, bit in zip(request.expected_returns, bits) if bit
            )
            variance = _portfolio_variance(bits, request.covariance_matrix)
            objective = _qubo_objective(bits, qubo)
            candidate = CandidatePortfolio(
                bitstring="".join(str(bit) for bit in bits),
                selected_indices=[i for i, bit in enumerate(bits) if bit],
                expected_return=expected_return,
                variance=variance,
                objective_value=objective,
            )
            if best is None or candidate.objective_value < best.objective_value:
                best = candidate
        if best is None:
            raise HTTPException(
                status_code=422, detail="no feasible portfolio candidate"
            )
        return best

    diagonal_risk = [max(request.covariance_matrix[i][i], 1e-12) for i in range(n)]
    ranking = sorted(
        range(n),
        key=lambda i: request.expected_returns[i] / diagonal_risk[i],
        reverse=True,
    )
    selected = sorted(ranking[: request.budget])
    bits = [1 if i in selected else 0 for i in range(n)]
    return CandidatePortfolio(
        bitstring="".join(str(bit) for bit in bits),
        selected_indices=selected,
        expected_return=sum(request.expected_returns[i] for i in selected),
        variance=_portfolio_variance(bits, request.covariance_matrix),
        objective_value=_qubo_objective(bits, qubo),
    )


def build_qaoa_design(
    request: PortfolioOptimizationRequest, qubo: List[List[float]]
) -> Dict[str, Any]:
    return {
        "encoding": "binary_asset_selection_qubits",
        "qubits": len(request.expected_returns),
        "layers": request.qaoa_layers,
        "initial_state": "uniform_superposition_over_binary_allocations",
        "problem_hamiltonian": "risk_return_budget_target_liquidity_regulatory_QUBO",
        "mixer_hamiltonian": "budget_preserving_xy_or_standard_x_mixer",
        "classical_optimizer": "CMA-ES_or_gradient_free_optimizer_for_noisy_substrate",
        "measurement": "sample_bitstrings_decode_portfolios_select_lowest_energy_feasible_allocations",
        "finance_specific_terms": [
            "mean_variance_markowitz_risk",
            "budget_constraint_penalty",
            (
                "target_return_penalty"
                if request.target_return is not None
                else "target_return_not_requested"
            ),
            (
                "transaction_cost_penalty"
                if request.transaction_costs
                else "transaction_costs_not_supplied"
            ),
            (
                "liquidity_penalty"
                if request.liquidity_scores
                else "liquidity_not_supplied"
            ),
            (
                "regulatory_constraint_penalty"
                if request.regulatory_constraints
                else "regulatory_constraints_not_supplied"
            ),
        ],
        "audit_boundary": "design_packet_for_human_risk_review_not_autonomous_trade_execution",
    }


def _finance_units(payload_size: int, surface: FinanceSurface) -> int:
    multiplier = {"qaas": 3, "qiaas": 2, "ciaas": 1}[surface]
    return max(1, multiplier * (payload_size // 2048 + 1))


def _serialise_qubo(qubo: List[List[float]]) -> Dict[str, Any]:
    terms = []
    for i, row in enumerate(qubo):
        for j, value in enumerate(row):
            if j < i or abs(value) < 1e-15:
                continue
            terms.append({"i": i, "j": j, "coefficient": value})
    return {
        "matrix": qubo,
        "terms": terms,
        "convention": "minimise ΣQii xi + ΣQij xi xj for i<j",
    }


def design_portfolio_qaoa(request: PortfolioOptimizationRequest) -> Dict[str, Any]:
    qubo = construct_portfolio_qubo(request)
    ising = qubo_to_ising(qubo)
    candidate = select_candidate_portfolio(request, qubo)
    qaoa = build_qaoa_design(request, qubo)
    formulas = {
        "qubo_objective": "risk_aversion*xΣx - return_weight*μx + budget_penalty*(Σx-B)^2 + optional penalties",
        "ising_transform": "x=(1-Z)/2",
        "qaoa": "alternate problem Hamiltonian and mixer Hamiltonian with classical parameter optimisation",
    }
    payload = request.model_dump()
    return {
        "surface": request.surface,
        "asset_count": len(request.expected_returns),
        "budget": request.budget,
        "qubo": _serialise_qubo(qubo),
        "ising_hamiltonian": ising,
        "qaoa_circuit_design": qaoa,
        "selected_candidate": {
            "bitstring": candidate.bitstring,
            "selected_indices": candidate.selected_indices,
            "expected_return": candidate.expected_return,
            "variance": candidate.variance,
            "objective_value": candidate.objective_value,
            "selection_mode": (
                "exact_enumeration"
                if len(request.expected_returns) <= 18
                else "stable_return_risk_heuristic"
            ),
        },
        "finance_specific_constraints": request.regulatory_constraints,
        "evidence_packet": _evidence_packet(request.evidence_label, payload, formulas),
    }


def design_risk_qae(request: RiskPricingRequest) -> Dict[str, Any]:
    samples = sorted(request.payoff_samples)
    n = len(samples)
    mean_payoff = sum(samples) / n
    variance = sum((x - mean_payoff) ** 2 for x in samples) / (n - 1)
    alpha_index = max(0, min(n - 1, math.ceil(request.confidence_level * n) - 1))
    var_value = samples[alpha_index]
    tail = samples[alpha_index:]
    cvar_value = sum(tail) / len(tail)

    classical_samples = math.ceil(1.0 / (request.precision_epsilon**2))
    qae_iterations = math.ceil(math.pi / (4.0 * request.precision_epsilon))
    quadratic_speedup_factor = classical_samples / qae_iterations

    formulas = {
        "qae_speedup": "O(1/epsilon) quantum amplitude estimation vs O(1/epsilon^2) classical Monte Carlo",
        "var": "empirical quantile at confidence_level",
        "cvar": "tail conditional mean beyond VaR index",
    }
    payload = request.model_dump()
    return {
        "surface": request.surface,
        "instrument_type": request.instrument_type,
        "sample_count": n,
        "pricing_summary": {
            "expected_payoff": mean_payoff,
            "sample_variance": variance,
            "payoff_min": samples[0],
            "payoff_max": samples[-1],
        },
        "risk_summary": {
            "confidence_level": request.confidence_level,
            "value_at_risk": var_value,
            "conditional_value_at_risk": cvar_value,
        },
        "qae_design": {
            "state_preparation": "encode_normalised_payoff_distribution_into_amplitude_oracle",
            "payoff_oracle": "finance_payoff_probability_amplitude_oracle",
            "amplitude_estimation_iterations": qae_iterations,
            "classical_monte_carlo_samples_for_same_epsilon": classical_samples,
            "quadratic_speedup_accounting_factor": quadratic_speedup_factor,
            "precision_epsilon": request.precision_epsilon,
            "verification": "classical_shadow_or_bootstrap_recheck_plus_evidence_packet",
            "audit_boundary": "risk_estimate_for_human_model_risk_review_not_autonomous_execution",
        },
        "evidence_packet": _evidence_packet(request.evidence_label, payload, formulas),
    }


@router.get("/capability-map")
async def quantum_finance_capability_map(
    customer: CustomerPrincipal = Depends(require_customer_api_key),
) -> Dict[str, Any]:
    """Return the implemented finance vertical capability map."""

    require_feature("finance_enabled")
    usage_meter = customer_access.meter(
        customer, product="finance.capability_map", units=1
    )
    cached = get_cached_json("hyba:cache:quantum-finance:capability-map:v1")
    if cached is not None:
        cached["usage_meter"] = usage_meter
        cached["cache"] = {"status": "hit", "ttl_seconds": 300}
        return cached

    response = {
        "vertical": "quantum_finance",
        "product_surfaces": ["QaaS", "QIaaS", "CIaaS"],
        "implemented_algorithms": [
            "portfolio_QUBO",
            "portfolio_Ising_Hamiltonian",
            "QAOA_design_packet",
            "VQE_or_annealing_compatible_QUBO",
            "QAE_QMCI_risk_pricing_design",
            "VaR_CVaR_evidence_packet",
        ],
        "finance_workloads": [
            "portfolio_optimisation",
            "derivative_pricing_design",
            "VaR_CVaR_risk_design",
            "scenario_sampling_design",
            "audit_evidence_generation",
        ],
        "explicit_non_goals": [
            "autonomous_trade_execution",
            "mining_productisation",
            "physical_QPU_superiority_without_hardware_evidence",
        ],
        "usage_meter": usage_meter,
        "cache": {"status": "miss", "ttl_seconds": 300},
    }
    return set_cached_json(
        "hyba:cache:quantum-finance:capability-map:v1", response, ttl_seconds=300
    )


@router.post("/portfolio/qaoa-design", response_model=PortfolioQAOAResponse)
async def portfolio_qaoa_design(
    request: PortfolioOptimizationRequest,
    customer: CustomerPrincipal = Depends(require_customer_api_key),
) -> PortfolioQAOAResponse:
    """Generate a finance-specific QUBO/Ising/QAOA design packet."""
    require_feature("finance_enabled")

    design = design_portfolio_qaoa(request)
    usage_meter = customer_access.meter(
        customer,
        product=f"finance.{request.surface}.portfolio_qaoa",
        units=_finance_units(
            len(_canonical_json(request.model_dump())), request.surface
        ),
    )
    return PortfolioQAOAResponse(**design, usage_meter=usage_meter)


@router.post("/risk/qae-design", response_model=RiskQAEResponse)
async def risk_qae_design(
    request: RiskPricingRequest,
    customer: CustomerPrincipal = Depends(require_customer_api_key),
) -> RiskQAEResponse:
    """Generate a finance-specific QAE/QMCI risk and pricing design packet."""
    require_feature("finance_enabled")

    design = design_risk_qae(request)
    usage_meter = customer_access.meter(
        customer,
        product=f"finance.{request.surface}.risk_qae",
        units=_finance_units(
            len(_canonical_json(request.model_dump())), request.surface
        ),
    )
    return RiskQAEResponse(**design, usage_meter=usage_meter)
