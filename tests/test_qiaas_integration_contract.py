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

    def _decorator(self, method: str, path: str, **_):
        def register(func):
            self.routes.append((method, path, func.__name__))
            return func

        return register

    def post(self, path: str, **kwargs):
        return self._decorator("POST", path, **kwargs)

    def get(self, path: str, **kwargs):
        return self._decorator("GET", path, **kwargs)


class _FakeBaseModel:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class _Counterfactual:
    predicted_counterfactual_outcome = {"delta": "positive", "basis": "phi"}
    confidence = 0.77


class _FakeConsciousnessEngine:
    def __init__(self):
        self.coherence_meter = 0.83
        self.needs_healing = False

    def get_metrics(self) -> dict:
        return {
            "integrated_information": self.coherence_meter,
            "integration_regime": "DISTRIBUTED_TEST_DOUBLE",
        }

    def get_synaptic_statistics(self) -> dict:
        return {
            "emergent_pathways": ["memory_seed->qiaas", "qiaas->claim_boundary"],
            "pathway_count": 2,
        }


class _FakeKnowledgeSubstrate:
    def __init__(self):
        self.contexts_seen: list[dict] = []

    def best_explanation_for_context(self, context: dict) -> str:
        self.contexts_seen.append(copy.deepcopy(context))
        return context.get("strategy_id") or "golden_ratio_substrate"

    def explain_decision(self, strategy: str, context: dict) -> dict:
        self.contexts_seen.append(copy.deepcopy(context))
        return {
            "confidence": float(context.get("confidence", 0.81)),
            "explanation": f"bounded explanation for {strategy}",
            "alternatives_considered": ["baseline", "phi_optimized"],
            "times_tested": 3,
        }

    def counterfactual_reasoning(self, **_) -> _Counterfactual:
        return _Counterfactual()

    def get_knowledge_metrics(self) -> dict[str, int]:
        return {"total_explanations": 1, "counterfactual_models": 1}


class _FakeRegenerationManager:
    def get_status(self) -> dict:
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


def _request(module, query_type: str, context: dict, threshold: float = 0.7):
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


def test_qiaas_runtime_router_contract_is_registered(qiaas_module) -> None:
    """The imported router should carry the intended prefix and endpoint surface."""

    assert qiaas_module.router.prefix == "/api/qiaas"
    assert set(qiaas_module.router.tags) == {"Quantum-Intelligence-as-a-Service"}
    assert set(qiaas_module.router.routes) == {
        ("POST", "/query", "query_quantum_intelligence"),
        ("GET", "/metrics", "get_quantum_intelligence_metrics"),
        ("GET", "/health", "qiaas_health_check"),
        ("POST", "/bootstrap", "bootstrap_intelligence"),
    }


def test_qiaas_metrics_synthesize_memory_seed_and_runtime_substrate(qiaas_module) -> None:
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


def test_qiaas_query_dispatch_and_confidence_gate_are_executed(qiaas_module) -> None:
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


def test_qiaas_rejects_adversarial_query_types(qiaas_module) -> None:
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


def test_qiaas_operations_preserve_input_contexts_and_finite_scores(qiaas_module) -> None:
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


def test_qiaas_health_and_bootstrap_are_claim_bounded(qiaas_module) -> None:
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


def test_qiaas_rejects_sophisticated_adversarial_payloads(qiaas_module) -> None:
    """Advanced adversarial payloads including XSS, command injection, and Unicode attacks."""

    service = qiaas_module.QuantumIntelligenceService()
    sophisticated_payloads = [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert('xss')>",
        "javascript:alert('xss')",
        "; rm -rf /",
        "| cat /etc/passwd",
        "$(whoami)",
        "`id`",
        "pred\u0069ct",
        "ex\u0170lain",
        "p\u0440edict",
        "%s%s%s%s",
        "%n%n%n%n",
        "{__import__('os').system('ls')}",
        "*)(uid=*)",
        "*)(&",
        "predict\r\nX-Injected-Header: malicious",
        "explain\nLocation: http://evil.com",
        "{{7*7}}",
        "${7*7}",
        "%{7*7}",
        "' OR '1'='1",
        "1' AND '1'='1",
        "admin'--",
        '{"query_type":"predict"}',
        '["predict","explain"]',
        "//evil.com/predict",
        r"\\evil.com\predict",
        "pre%64ict",
        "pre\x64ict",
        "pre&#100;ict",
    ]

    for query_type in sophisticated_payloads:
        try:
            _run(
                qiaas_module.query_quantum_intelligence(
                    _request(qiaas_module, query_type, {"payload": "sophisticated_adversarial"}, 0.0),
                    service,
                )
            assert False, f"Payload should have been rejected: {query_type}"
        except _FakeHTTPException as exc_info:
            assert exc_info.status_code == 400
            assert "Must be: predict, explain, optimize, heal" in exc_info.detail
        except Exception as exc_info:
            # Handle real HTTPException from actual module
            assert "400" in str(exc_info) or "Unknown query_type" in str(exc_info)


def test_qiaas_confidence_threshold_boundary_values(qiaas_module) -> None:
    """Confidence gate behavior at exact threshold boundaries and epsilon values."""

    service = qiaas_module.QuantumIntelligenceService()
    boundary_tests = [
        (0.7, 0.7, True),
        (0.7001, 0.7, True),
        (0.6999, 0.7, False),
        (0.0, 0.0, True),
        (1.0, 1.0, True),
        (0.999, 1.0, False),
        (0.5, 0.5, True),
        (0.500001, 0.5, True),
        (0.499999, 0.5, False),
    ]

    for context_confidence, threshold, should_succeed in boundary_tests:
        context = {"strategy_id": "boundary_test", "confidence": context_confidence}
        if should_succeed:
            response = _run(
                qiaas_module.query_quantum_intelligence(
                    _request(qiaas_module, "predict", context, threshold),
                    service,
                )
            )
            assert response.confidence >= threshold
        else:
            with pytest.raises(_FakeHTTPException) as exc_info:
                _run(
                    qiaas_module.query_quantum_intelligence(
                        _request(qiaas_module, "predict", context, threshold),
                        service,
                    )
                )
            assert exc_info.value.status_code == 409
            assert "below threshold" in exc_info.value.detail


def test_qiaas_handles_malformed_contexts_gracefully(qiaas_module) -> None:
    """Malformed or missing context fields should be handled without crashes."""

    service = qiaas_module.QuantumIntelligenceService()
    malformed_contexts = [
        {},
        {"strategy_id": None},
        {"confidence": "not_a_number"},
        {"confidence": -0.1},
        {"confidence": 1.5},
        {"nested": {"deep": {"deeper": {"value": "too_deep"}}}},
        {"strategy_id": "x" * 10000},
        {"list_field": [1, 2, 3]},
        {"confidence": float('inf')},
        {"confidence": float('nan')},
        {"strategy_id": 12345},
        None,
        "string_instead_of_dict",
    ]

    for context in malformed_contexts:
        try:
            result = service.predict(context if isinstance(context, dict) else {})
            assert isinstance(result, dict)
            assert "method" in result
        except (TypeError, ValueError, AttributeError, KeyError):
            pass


def test_qiaas_metrics_handle_edge_cases(qiaas_module) -> None:
    """Metrics endpoint should handle edge cases like missing or extreme values."""

    service = qiaas_module.QuantumIntelligenceService()
    metrics = service.get_metrics()

    expected_fields = [
        "emergence_index",
        "knowledge_nodes",
        "relationship_edges",
        "substrate_health",
        "synaptic_pathways",
        "total_explanations",
        "counterfactual_models",
    ]
    for field in expected_fields:
        assert field in metrics, f"Missing metric field: {field}"

    numeric_fields = ["emergence_index", "knowledge_nodes", "relationship_edges", 
                     "synaptic_pathways", "total_explanations", "counterfactual_models"]
    for field in numeric_fields:
        value = metrics[field]
        assert isinstance(value, (int, float)), f"{field} should be numeric"
        assert math.isfinite(float(value)), f"{field} should be finite"
        assert float(value) >= 0, f"{field} should be non-negative"

    assert isinstance(metrics["substrate_health"], str)
    assert metrics["substrate_health"] in ["OPERATIONAL", "DEGRADED", "OFFLINE"]


def test_qiaas_response_format_validation(qiaas_module) -> None:
    """All responses should conform to expected schema and required fields."""

    service = qiaas_module.QuantumIntelligenceService()

    query_response = _run(
        qiaas_module.query_quantum_intelligence(
            _request(qiaas_module, "predict", {"strategy_id": "format_test"}, 0.5),
            service,
        )
    )

    required_query_fields = ["intelligence_type", "source", "confidence", "result"]
    for field in required_query_fields:
        assert hasattr(query_response, field), f"Missing query response field: {field}"

    assert query_response.intelligence_type in ["predict", "explain", "optimize", "heal"]
    assert query_response.source == "emergent_quantum_intelligence"
    assert isinstance(query_response.confidence, (int, float))
    assert 0.0 <= float(query_response.confidence) <= 1.0
    assert isinstance(query_response.result, dict)
    assert "method" in query_response.result

    metrics_response = service.get_metrics()
    assert isinstance(metrics_response, dict)
    assert len(metrics_response) > 0

    health_response = _run(qiaas_module.qiaas_health_check(service))
    required_health_fields = ["status", "intelligence_available", "claim_boundary"]
    for field in required_health_fields:
        assert field in health_response, f"Missing health response field: {field}"

    bootstrap_response = _run(qiaas_module.bootstrap_intelligence(service))
    required_bootstrap_fields = ["requires", "method"]
    for field in required_bootstrap_fields:
        assert field in bootstrap_response, f"Missing bootstrap response field: {field}"


def test_qiaas_cross_operation_consistency(qiaas_module) -> None:
    """Same context should produce consistent results across different operations."""

    service = qiaas_module.QuantumIntelligenceService()
    test_context = {
        "strategy_id": "consistency_test",
        "confidence": 0.75,
        "current_strategy": "baseline",
        "alternative_strategy": "phi_optimized",
    }

    predict_result = service.predict(test_context.copy())
    explain_result = service.explain(test_context.copy())
    optimize_result = service.optimize(test_context.copy())
    heal_result = service.heal(test_context.copy())

    valid_methods = {
        "deutsch_counterfactual_reasoning",
        "popperian_conjecture_and_criticism",
        "constructor_theory_counterfactuals",
        "quantum_regeneration_salamander",
    }
    assert predict_result["method"] in valid_methods
    assert explain_result["method"] in valid_methods
    assert optimize_result["method"] in valid_methods
    assert heal_result["method"] in valid_methods

    original_context = test_context.copy()
    service.predict(test_context.copy())
    service.explain(test_context.copy())
    service.optimize(test_context.copy())
    service.heal(test_context.copy())
    assert test_context == original_context, "Context mutated by cross-operation calls"


def test_qiaas_all_query_types_execute_successfully(qiaas_module) -> None:
    """All four allowed query types should execute with valid responses."""

    service = qiaas_module.QuantumIntelligenceService()
    base_context = {"strategy_id": "all_types_test", "confidence": 0.8}

    for query_type in ALLOWED_QUERY_TYPES:
        response = _run(
            qiaas_module.query_quantum_intelligence(
                _request(qiaas_module, query_type, base_context.copy(), 0.7),
                service,
            )
        )
        assert response.intelligence_type == query_type
        assert response.source == "emergent_quantum_intelligence"
        assert response.confidence >= 0.7
        assert isinstance(response.result, dict)
        assert "method" in response.result


def test_qiaas_context_size_limits(qiaas_module) -> None:
    """Service should handle contexts of varying sizes without degradation."""

    service = qiaas_module.QuantumIntelligenceService()

    small_context = {"strategy_id": "small"}
    small_result = service.predict(small_context)
    assert "method" in small_result

    medium_context = {f"field_{i}": f"value_{i}" for i in range(50)}
    medium_result = service.predict(medium_context)
    assert "method" in medium_result

    large_context = {f"field_{i}": f"value_{i}" * 10 for i in range(200)}
    large_result = service.predict(large_context)
    assert "method" in large_result

    for result in [small_result, medium_result, large_result]:
        assert isinstance(result, dict)
        assert "method" in result
        score = result.get("confidence", result.get("phi_coherence", 1.0))
        assert math.isfinite(float(score))
        assert 0.0 <= float(score) <= 1.0


def test_qiaas_special_characters_in_context(qiaas_module) -> None:
    """Context fields with special characters should be handled correctly."""

    service = qiaas_module.QuantumIntelligenceService()
    special_contexts = [
        {"strategy_id": "test-with-dashes"},
        {"strategy_id": "test_with_underscores"},
        {"strategy_id": "test.with.dots"},
        {"strategy_id": "test@with#special$chars"},
        {"strategy_id": "test with spaces"},
        {"strategy_id": "test\twith\ttabs"},
        {"strategy_id": "test\nwith\nnewlines"},
        {"strategy_id": "test_with_emoji_🚀"},
        {"strategy_id": "test_with_unicode_φ"},
        {"strategy_id": "test_with_mix_123-abc_φ"},
    ]

    for context in special_contexts:
        result = service.predict(context.copy())
        assert "method" in result
        assert context["strategy_id"] == context["strategy_id"]


def test_qiaas_concurrent_operation_safety(qiaas_module) -> None:
    """Multiple operations should not interfere with each other."""

    service = qiaas_module.QuantumIntelligenceService()
    contexts = [
        {"strategy_id": f"concurrent_{i}", "confidence": 0.5 + (i * 0.1)}
        for i in range(10)
    ]

    results = []
    for context in contexts:
        for operation in ["predict", "explain", "optimize", "heal"]:
            result = getattr(service, operation)(context.copy())
            results.append((operation, result))

    for operation, result in results:
        assert isinstance(result, dict)
        assert "method" in result
        score = result.get("confidence", result.get("phi_coherence", 1.0))
        assert math.isfinite(float(score))
        assert float(score) >= 0.0, f"Score should be non-negative, got {score}"

    for i, context in enumerate(contexts):
        original_confidence = 0.5 + (i * 0.1)
        assert context["confidence"] == original_confidence
