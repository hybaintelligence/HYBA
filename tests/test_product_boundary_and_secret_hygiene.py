"""Production-readiness guardrails for public product boundaries and secrets.

These tests protect the Chairman/investor narrative by ensuring the repository
presents HYBA as QaaS/QIaaS/CIaaS + quantum finance + PULVINI + phi
hardware/quantum scaling + Salamander, while keeping mining private and
preventing committed runtime secrets from re-entering the tree.
"""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_readme_presents_hyba_as_post_quantum_intelligence_platform() -> None:
    readme = _read("README.md")

    assert "Post-Quantum Intelligence Platform" in readme
    assert "QaaS" in readme
    assert "QIaaS" in readme
    assert "CIaaS" in readme
    assert "PULVINI" in readme
    assert "hardware" in readme.lower()
    assert "Mining infrastructure exists" in readme
    assert "not a public product" in readme


def test_product_boundary_preserves_phi_hardware_and_quantum_scaling_claims() -> None:
    boundary = _read("docs/product/HYBA_PRODUCT_BOUNDARIES.md")

    assert "hardware and quantum scaling" in boundary
    assert "post-quantum mathematical" in boundary
    assert "Golden-ratio scaling is a first-class platform mechanism" in boundary
    assert "Claims to preserve, not dumb down" in boundary
    assert "Mining" in boundary and "private validation" in boundary


def test_product_boundary_includes_code_backed_quantum_finance_vertical() -> None:
    boundary = _read("docs/product/HYBA_PRODUCT_BOUNDARIES.md")
    finance_doc = _read("docs/product/HYBA_QUANTUM_FINANCE_VERTICAL.md")
    finance_api = _read("python_backend/hyba_genesis_api/api/quantum_finance_service.py")

    assert "Quantum finance vertical" in boundary
    assert "/api/quantum-finance" in boundary
    assert "QUBO/QAOA" in boundary
    assert "QAE/QMCI" in boundary
    assert "not autonomous trade execution" in boundary.lower()

    assert "portfolio optimisation" in finance_doc
    assert "QUBO" in finance_doc
    assert "QAE" in finance_doc
    assert "VaR" in finance_doc and "CVaR" in finance_doc

    assert "PortfolioOptimizationRequest" in finance_api
    assert "RiskPricingRequest" in finance_api
    assert "public_quantum_finance_vertical_not_mining" in finance_api


def test_private_validation_doc_keeps_mining_out_of_public_product_surface() -> None:
    private_boundary = _read("docs/private-validation/MINING_INTERNAL_VALIDATION_BOUNDARY.md")

    assert "private validation substrate only" in private_boundary
    assert "not a public HYBA product surface" in private_boundary
    assert "Pool credentials" in private_boundary or "pool credential" in private_boundary


def test_qiaas_is_api_key_gated_and_metered() -> None:
    qiaas = _read("python_backend/hyba_genesis_api/api/quantum_intelligence_service.py")

    assert "require_customer_api_key" in qiaas
    assert "customer_access.meter" in qiaas
    assert "qiaas." in qiaas
    assert "product_boundary" in qiaas
    assert "not_mining" in qiaas


def test_public_ciaas_has_single_canonical_mount() -> None:
    main = _read("python_backend/hyba_genesis_api/main.py")

    assert "public_computational_intelligence_service" not in main
    assert "computational_intelligence_service.public_router" in main
    assert "prefix=\"/api/ciaas\"" not in main


def test_quantum_finance_is_mounted_as_customer_gated_public_vertical() -> None:
    main = _read("python_backend/hyba_genesis_api/main.py")
    finance_api = _read("python_backend/hyba_genesis_api/api/quantum_finance_service.py")

    assert "quantum_finance_service" in main
    assert "app.include_router(quantum_finance_service.router)" in main
    assert "require_customer_api_key" in finance_api
    assert "customer_access.meter" in finance_api
    assert "autonomous trade" in finance_api.lower()
    assert "mining" in finance_api.lower()


def test_no_committed_local_env_or_obvious_runtime_secret_files() -> None:
    forbidden_files = [
        ROOT / ".env.local",
        ROOT / ".env.production.local",
        ROOT / "config" / "production_credentials.env",
        ROOT / "config" / "production_credentials_static.env",
    ]

    for path in forbidden_files:
        assert not path.exists(), f"runtime secret file must not be committed: {path.relative_to(ROOT)}"

    docker_env = _read("config/.env.docker")
    env_example = _read(".env.example")

    for text in (docker_env, env_example):
        assert "secret manager" in text.lower() or "replace-with" in text.lower()
        assert not re.search(r"^JWT_SECRET=[0-9a-fA-F]{32,}$", text, re.MULTILINE)
        assert not re.search(r"_PASSWORD=\S+$", text, re.MULTILINE)
        assert not re.search(r"_CREDENTIALS=\S+:\S+:\S+", text, re.MULTILINE)

    assert "HYBA_API_KEY_SECRET" in env_example
