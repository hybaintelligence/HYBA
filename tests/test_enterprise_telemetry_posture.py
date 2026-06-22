from __future__ import annotations

import asyncio
import importlib
import sys
import types
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
QIAAS_PATH = REPO_ROOT / "python_backend" / "hyba_genesis_api" / "api" / "quantum_intelligence_service.py"
CUSTOMER_ACCESS_PATH = REPO_ROOT / "python_backend" / "hyba_genesis_api" / "api" / "customer_access.py"
POSTURE_PATH = REPO_ROOT / "python_backend" / "hyba_genesis_api" / "core" / "api_posture.py"
QIAAS_MODULE = "hyba_genesis_api.api.quantum_intelligence_service"


class _FakeHTTPException(Exception):
    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class _FakeAPIRouter:
    def __init__(self, *, prefix: str = "", tags: list[str] | None = None):
        self.prefix = prefix
        self.tags = tags or []

    def post(self, *_args, **_kwargs):
        return lambda func: func

    def get(self, *_args, **_kwargs):
        return lambda func: func


class _FakeBaseModel:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class _Service:
    def predict(self, _context):
        return {"confidence": 0.9, "method": "deutsch_counterfactual_reasoning"}

    def heal(self, _context):
        return {"phi_coherence": 0.9, "method": "quantum_regeneration_salamander"}

    def get_metrics(self):
        return {
            "phi_integrated": 0.9,
            "emergence_index": 1.1,
            "substrate_health": "OPERATIONAL",
            "integration_regime": "ENTERPRISE_TEST",
        }


class _Customer:
    def __init__(self, tier: str = "enterprise"):
        self.customer_id = f"tenant-{tier}"
        self.tier = tier


@pytest.fixture()
def qiaas_module(monkeypatch):
    fastapi = types.ModuleType("fastapi")
    fastapi.APIRouter = _FakeAPIRouter
    fastapi.HTTPException = _FakeHTTPException
    fastapi.Depends = lambda dependency: dependency
    fastapi.Header = lambda default=None, **_kwargs: default

    pydantic = types.ModuleType("pydantic")
    pydantic.BaseModel = _FakeBaseModel
    pydantic.Field = lambda default=None, **kwargs: (
        kwargs["default_factory"]() if "default_factory" in kwargs else default
    )

    for name in ("fastapi", "pydantic"):
        monkeypatch.setitem(sys.modules, name, locals()[name])

    dependency_map = {
        "pythia_mining.consciousness_engine": {"ConsciousnessEngine": object},
        "pythia_mining.deutsch_knowledge_substrate": {"KnowledgeSubstrate": object},
        "pythia_mining.regeneration_manager": {"get_regeneration_manager": lambda: object()},
        "pythia_mining.iit_4_analyzer": {"IIT4Analyzer": lambda system_size: object()},
        "pythia_mining.pulvini_phi_memory": {"PulviniPhiMemoryCompressionEngine": object},
    }
    for module_name, attributes in dependency_map.items():
        module = types.ModuleType(module_name)
        for key, value in attributes.items():
            setattr(module, key, value)
        monkeypatch.setitem(sys.modules, module_name, module)

    sys.modules.pop(QIAAS_MODULE, None)
    module = importlib.import_module(QIAAS_MODULE)
    yield module
    sys.modules.pop(QIAAS_MODULE, None)


def _request(module, query_type: str = "predict"):
    return module.QIaaSQueryRequest(
        query_type=query_type,
        context={"strategy_id": "enterprise_gate"},
        confidence_threshold=0.1,
    )


def test_unauthenticated_qiaas_dependency_fails_closed(qiaas_module):
    with pytest.raises(_FakeHTTPException) as exc_info:
        asyncio.run(qiaas_module.require_qiaas_api_key(None))

    assert exc_info.value.status_code == 401
    assert "X-API-Key header required" in exc_info.value.detail


def test_invalid_tier_cannot_call_heal(qiaas_module):
    with pytest.raises(_FakeHTTPException) as exc_info:
        asyncio.run(
            qiaas_module.query_quantum_intelligence(
                _request(qiaas_module, "heal"), _Service(), _Customer("developer")
            )
        )

    assert exc_info.value.status_code == 403
    assert "requires production or enterprise entitlement" in exc_info.value.detail


def test_usage_units_trace_and_evidence_are_present(qiaas_module, monkeypatch):
    captured = {}

    def fake_meter(principal, product, units):
        captured.update({"principal": principal, "product": product, "units": units})
        return {"product": product, "units": units, "quota_enforced": True}

    monkeypatch.setattr(qiaas_module, "meter_qiaas_usage", fake_meter)

    response = asyncio.run(
        qiaas_module.query_quantum_intelligence(_request(qiaas_module), _Service(), _Customer())
    )

    assert captured["product"] == "qiaas.predict"
    assert captured["units"] == 1
    assert response.trace["trace_id"].startswith("qiaas-")
    assert response.evidence_packet["evidence_id"].startswith("ev-")
    assert response.usage_meter["quota_enforced"] is True


def test_qiaas_customer_endpoints_require_api_key_and_metering_by_source():
    source = QIAAS_PATH.read_text(encoding="utf-8")

    assert "Depends(require_qiaas_api_key)" in source
    assert 'product=f"qiaas.{query_type}"' in source
    assert 'product="qiaas.metrics"' in source
    assert 'product="qiaas.health"' in source
    assert 'product="qiaas.bootstrap"' in source


def test_redis_backed_quota_trace_headers_and_sanitized_errors_by_source():
    customer_access = CUSTOMER_ACCESS_PATH.read_text(encoding="utf-8")
    posture = POSTURE_PATH.read_text(encoding="utf-8")

    assert "HYBA_REDIS_URL" in customer_access
    assert "hincrby" in customer_access
    assert "X-Request-ID" in posture
    assert "sanitize_production_errors" in posture
    assert "Authentication required or invalid." in posture
    assert "X-Content-Type-Options" in posture
