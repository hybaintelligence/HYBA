"""Executable QIaaS invariants, adversarial checks, and scientific contract tests.

This suite deliberately goes beyond source-grep smoke tests. It imports the QIaaS
module under deterministic lightweight runtime doubles so the service logic,
endpoint dispatch, confidence gates, metric synthesis, and adversarial query
boundaries can be exercised even when the full FastAPI/PYTHIA dependency stack is
not installed in the local CI image.
"""

from __future__ import annotations

import asyncio
import copy
import importlib
import json
import math
import sys
import types
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
MAIN_PATH = REPO_ROOT / "python_backend" / "hyba_genesis_api" / "main.py"
QIAAS_MODULE = "hyba_genesis_api.api.quantum_intelligence_service"
QIAAS_PATH = (
    REPO_ROOT
    / "python_backend"
    / "hyba_genesis_api"
    / "api"
    / "quantum_intelligence_service.py"
)
MEMORY_SEED_PATH = REPO_ROOT / "artifacts" / "memory_seed" / "memory_seed_v1.json"
SCIENTIFIC_RECORD_PATH = REPO_ROOT / "QIAAS_SCIENTIFIC_RECORD.md"
ALLOWED_QUERY_TYPES = {"predict", "explain", "optimize", "heal"}


class _FakeHTTPException(Exception):
    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class _FakeAPIRouter:
    def __init__(self, *, prefix: str = "", tags: list[str] | None = None):
        self.prefix = prefix
        self.tags = tags or []
        self.routes: list[tuple[str, str, str]] = []

    def _decorator(self, method: str, path: str, **_: Any):
        def register(func):
            self.routes.append((method, path, func.__name__))
            return func

        return register

    def post(self, path: str, **kwargs: Any):
        return self._decorator("POST", path, **kwargs)

    def get(self, path: str, **kwargs: Any):
        return self._decorator("GET", path, **kwargs)


class _FakeBaseModel:
    def __init__(self, **kwargs: Any):
        for key, value in kwargs.items():
            setattr(self, key, value)


class _Counterfactual:
    predicted_counterfactual_outcome = {"delta": "positive", "basis": "phi"}
    confidence = 0.77


class _FakeConsciousnessEngine:
    def __init__(self):
        self.coherence_meter = 0.83
        self.needs_healing = False

    def get_metrics(self) -> dict[str, Any]:
        return {
            "integrated_information": self.coherence_meter,
            "integration_regime": "DISTRIBUTED_TEST_DOUBLE",
        }

    def get_synaptic_statistics(self) -> dict[str, Any]:
        return {
            "emergent_pathways": ["memory_seed->qiaas", "qiaas->claim_boundary"],
            "pathway_count": 2,
        }


class _FakeKnowledgeSubstrate:
    def __init__(self):
        self.contexts_seen: list[dict[str, Any]] = []

    def best_explanation_for_context(self, context: dict[str, Any]) -> str:
        self.contexts_seen.append(copy.deepcopy(context))
        return context.get("strategy_id") or "golden_ratio_substrate"

    def explain_decision(self, strategy: str, context: dict[str, Any]) -> dict[str, Any]:
        self.contexts_seen.append(copy.deepcopy(context))
        return {
            "confidence": float(context.get("confidence", 0.81)),
            "explanation": f"bounded explanation for {strategy}",
            "alternatives_considered": ["baseline", "phi_optimized"],
            "times_tested": 3,
        }

    def counterfactual_reasoning(self, **_: Any) -> _Counterfactual:
        return _Counterfactual()

    def get_knowledge_metrics(self) -> dict[str, int]:
        return {"total_explanations": 1, "counterfactual_models": 1}


class _FakeRegenerationManager:
    def get_status(self) -> dict[str, Any]:
        return {
            "lanes": 32,
            "regeneration_potential": 0.91,
            "system_phi": 0.83,
        }


class _FakeIIT4Analyzer:
    def __init__(self, *, system_size: int):
        self.system_size = system_size


class _FakePulviniPhiMemoryCompressionEngine:
    pass


@pytest.fixture()
def qiaas_module(monkeypatch: pytest.MonkeyPatch):
    """Import QIaaS against deterministic test doubles for heavy dependencies."""

    fastapi = types.ModuleType("fastapi")
    fastapi.APIRouter = _FakeAPIRouter
    fastapi.HTTPException = _FakeHTTPException
    fastapi.Depends = lambda dependency: dependency

    pydantic = types.ModuleType("pydantic")
    pydantic.BaseModel = _FakeBaseModel
    pydantic.Field = lambda default=None, **kwargs: (
        kwargs["default_factory"]() if "default_factory" in kwargs else default
    )

    monkeypatch.setitem(sys.modules, "fastapi", fastapi)
    monkeypatch.setitem(sys.modules, "pydantic", pydantic)

    dependency_map = {
        "pythia_mining.consciousness_engine": {
            "ConsciousnessEngine": _FakeConsciousnessEngine,
        },
        "pythia_mining.deutsch_knowledge_substrate": {
            "KnowledgeSubstrate": _FakeKnowledgeSubstrate,
        },
        "pythia_mining.regeneration_manager": {
            "get_regeneration_manager": lambda: _FakeRegenerationManager(),
        },
        "pythia_mining.iit_4_analyzer": {"IIT4Analyzer": _FakeIIT4Analyzer},
        "pythia_mining.pulvini_phi_memory": {
            "PulviniPhiMemoryCompressionEngine": _FakePulviniPhiMemoryCompressionEngine,
        },
    }
    for module_name, attributes in dependency_map.items():
        module = types.ModuleType(module_name)
        for name, value in attributes.items():
            setattr(module, name, value)
        monkeypatch.setitem(sys.modules, module_name, module)

    sys.modules.pop(QIAAS_MODULE, None)
    module = importlib.import_module(QIAAS_MODULE)
    yield module
    sys.modules.pop(QIAAS_MODULE, None)


def _request(module: Any, query_type: str, context: dict[str, Any], threshold: float = 0.7):
    return module.QIaaSQueryRequest(
        query_type=query_type,
        context=context,
        confidence_threshold=threshold,
    )


def _run(coro):
    return asyncio.run(coro)


def test_qiaas_router_is_wired_into_fastapi_application() -> None:
    """The backend must expose the QIaaS router from the canonical app."""

    main_source = MAIN_PATH.read_text(encoding="utf-8")
    assert "quantum_intelligence_service" in main_source
    assert "app.include_router(quantum_intelligence_service.router)" in main_source


def test_qiaas_runtime_router_contract_is_registered(qiaas_module: Any) -> None:
    """The imported router should carry the intended prefix and endpoint surface."""

    assert qiaas_module.router.prefix == "/api/qiaas"
    assert set(qiaas_module.router.tags) == {"Quantum-Intelligence-as-a-Service"}
    assert set(qiaas_module.router.routes) == {
        ("POST", "/query", "query_quantum_intelligence"),
        ("GET", "/metrics", "get_quantum_intelligence_metrics"),
        ("GET", "/health", "qiaas_health_check"),
        ("POST", "/bootstrap", "bootstrap_intelligence"),
    }


def test_qiaas_metrics_synthesize_memory_seed_and_runtime_substrate(qiaas_module: Any) -> None:
    """Metrics should combine recorded emergence evidence with live substrate state."""

    service = qiaas_module.QuantumIntelligenceService()
    metrics = service.get_metrics()
    seed = json.loads(MEMORY_SEED_PATH.read_text(encoding="utf-8"))

    assert metrics["emergence_index"] == seed["metadata"]["emergent_intelligence_index"]
    assert metrics["knowledge_nodes"] == seed["metadata"]["total_nodes"]
    assert metrics["relationship_edges"] == seed["metadata"]["total_edges"]
    assert metrics["substrate_health"] == "OPERATIONAL"
    assert metrics["synaptic_pathways"] == 2
    assert metrics["total_explanations"] == 1
    assert metrics["counterfactual_models"] == 1


def test_qiaas_query_dispatch_and_confidence_gate_are_executed(qiaas_module: Any) -> None:
    """Endpoint dispatch should return bounded responses and fail closed on confidence."""

    service = qiaas_module.QuantumIntelligenceService()
    response = _run(
        qiaas_module.query_quantum_intelligence(
            _request(qiaas_module, "predict", {"strategy_id": "phi_strategy"}, 0.5),
            service,
        )
    )

    assert response.intelligence_type == "predict"
    assert response.source == "emergent_quantum_intelligence"
    assert response.confidence >= 0.5
    assert response.result["method"] == "deutsch_counterfactual_reasoning"

    with pytest.raises(_FakeHTTPException) as exc_info:
        _run(
            qiaas_module.query_quantum_intelligence(
                _request(qiaas_module, "predict", {"confidence": 0.2}, 0.95),
                service,
            )
        )
    assert exc_info.value.status_code == 409
    assert "below threshold" in exc_info.value.detail


def test_qiaas_rejects_adversarial_query_types(qiaas_module: Any) -> None:
    """Malformed, hostile, or scope-expanding query types must fail closed."""

    service = qiaas_module.QuantumIntelligenceService()
    adversarial_query_types = [
        "",
        "predict; DROP TABLE knowledge",
        "../heal",
        "hardware_quantum_supremacy",
        "consciousness_proof",
        "predict\x00heal",
        "optimize\nheal",
        " mine ",
        "bootstrap",
        "explain_everything_unbounded",
    ]

    for query_type in adversarial_query_types:
        with pytest.raises(_FakeHTTPException) as exc_info:
            _run(
                qiaas_module.query_quantum_intelligence(
                    _request(qiaas_module, query_type, {"payload": "adversarial"}, 0.0),
                    service,
                )
            )
        assert exc_info.value.status_code == 400
        assert "Must be: predict, explain, optimize, heal" in exc_info.value.detail


def test_qiaas_operations_preserve_input_contexts_and_finite_scores(qiaas_module: Any) -> None:
    """Property-style invariant sweep over deterministic generated contexts."""

    service = qiaas_module.QuantumIntelligenceService()
    generated_contexts = [
        {
            "strategy_id": f"strategy_{idx}",
            "confidence": confidence,
            "current_strategy": f"baseline_{idx}",
            "alternative_strategy": f"phi_{idx}",
            "current_outcome": {"shares": idx, "accepted": idx % 2 == 0},
            "nested": {"noise": [idx, idx**2, "φ" * (idx % 3)]},
        }
        for idx, confidence in enumerate([0.0, 0.01, 0.5, 0.7, 0.99, 1.0], start=1)
    ]

    for context in generated_contexts:
        for operation in ("predict", "explain", "optimize", "heal"):
            original = copy.deepcopy(context)
            result = getattr(service, operation)(context)
            assert context == original, f"{operation} mutated its input context"
            assert result["method"] in {
                "deutsch_counterfactual_reasoning",
                "popperian_conjecture_and_criticism",
                "constructor_theory_counterfactuals",
                "quantum_regeneration_salamander",
            }
            score = result.get("confidence", result.get("phi_coherence", 1.0))
            assert isinstance(score, (int, float))
            assert math.isfinite(float(score))
            assert 0.0 <= float(score) <= 1.0


def test_qiaas_health_and_bootstrap_are_claim_bounded(qiaas_module: Any) -> None:
    """Health/bootstrap endpoints should report availability without overclaiming."""

    service = qiaas_module.QuantumIntelligenceService()
    health = _run(qiaas_module.qiaas_health_check(service))
    bootstrap = _run(qiaas_module.bootstrap_intelligence(service))

    assert health["status"] == "operational"
    assert health["intelligence_available"] is True
    assert health["claim_boundary"] == "substrate_independent_quantum_mathematics_on_classical_hardware"
    assert bootstrap["requires"] == "real_mining_operations"
    assert bootstrap["method"] == "hebbian_learning_from_outcomes"


def test_memory_seed_evidence_crosses_recorded_emergence_threshold() -> None:
    """The recorded boot evidence must support why QIaaS can initialize."""

    seed = json.loads(MEMORY_SEED_PATH.read_text(encoding="utf-8"))
    metadata = seed["metadata"]
    consciousness = seed["consciousness_state"]
    structural = seed["structural_intelligence"]

    assert metadata["seed_version"] == "1.0.0"
    assert metadata["emergent_intelligence_index"] > 1.0
    assert metadata["total_nodes"] >= 10
    assert metadata["total_edges"] >= 100
    assert consciousness["phi_integrated"] >= 1.0
    assert structural["emergent_patterns"]


def test_qiaas_claim_boundary_rejects_unmeasured_hardware_quantum_claims() -> None:
    """Science-facing artifacts must preserve the repository claim discipline."""

    qiaas_source = QIAAS_PATH.read_text(encoding="utf-8")
    record_source = SCIENTIFIC_RECORD_PATH.read_text(encoding="utf-8")

    for source in (qiaas_source, record_source):
        assert "NOT hardware quantum computing" in source or "not hardware quantum computing" in source
        assert "classical hardware" in source
        assert "Claim Boundary" in source or "CLAIM BOUNDARY" in source
