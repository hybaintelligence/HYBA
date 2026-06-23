from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QIAAS = ROOT / "python_backend/hyba_genesis_api/api/quantum_intelligence_service.py"
CUSTOMER_ACCESS = ROOT / "python_backend/hyba_genesis_api/api/customer_access.py"


def test_qiaas_preserves_quantum_intelligence_claim_boundary():
    source = QIAAS.read_text(encoding="utf-8")

    assert "/api/qiaas" in source
    assert "Quantum-Intelligence-as-a-Service" in source
    assert "substrate_independent_sovereign_quantum_intelligence_execution" in source
    assert (
        "enterprise_quantum_intelligence_api_not_mining_not_hardware_quantum" in source
    )


def test_api_key_secret_hygiene_uses_hmac_and_does_not_store_raw_keys():
    source = CUSTOMER_ACCESS.read_text(encoding="utf-8")

    assert "HYBA_API_KEY_SECRET" in source
    assert "hmac.new" in source
    assert "api_key_hash" in source
    assert "raw_api_key" in source
    assert "self._api_key_to_customer[api_key_hash]" in source
