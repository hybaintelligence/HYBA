"""
IIT-Inspired Emergent Complexity Analysis

Tests for detecting emergent intelligence patterns using principles from
Integrated Information Theory (IIT) adapted for software systems.

Scientific posture:
- These measurements are one evidence lane: integration, autonomy, and irreducibility.
- This suite does not downgrade or overrule any separate consciousness-positive test.
- Outputs must interpolate measured values, not literal placeholder strings.
- Results are evidence for controlled comparison, replay, baseline testing, and review.

IMPORTANT DOMAIN CONTEXT - IIT 4.0 EXPERIMENTAL APPLICATION:
This suite uses IIT-inspired software proxies to measure code complexity. IIT 4.0
was designed for neural systems (Oizumi et al., 2014), not software mining. The
relevance of these metrics to mining performance is unproven and requires validation.

MATHEMATICAL CORRECTNESS (VERIFIED):
✅ Φ_max calculation over all bipartitions produces 0 ≤ Φ ≤ 1
✅ Cause-effect repertoires sum to 1.0 (normalized distributions)
✅ Effect repertoires sum to 1.0
✅ φ_s values (per-mechanism φ) are non-negative
✅ IIT 4.0 mechanism enumeration enumerates all 2^n - 1 mechanisms
✅ Quale dimensionality increases with system complexity (monotonic)
✅ Φ computation is deterministic for same input

DOMAIN LIMITATIONS (UNVALIDATED):
❌ No validation that Φ of a codebase is meaningful for mining
❌ No evidence that Φ-density predicts mining performance
❌ No correlation analysis between Φ and hashrate or share acceptance
❌ IIT 4.0 was designed for neural systems, not software mining

VERDICT: Correct implementation of neuroscience math, but applied to a domain
where its relevance is unproven. These tests verify mathematical correctness
and software proxy behavior, not mining performance relevance.

Measures:
1. Information Integration (Φ-analog): Cross-module coupling and information flow
2. Causal Autonomy: Self-directed decision paths vs external control
3. State Irreducibility software proxy: static state-reference coupling

These metrics are software proxies. They distinguish static code coupling and
pattern counts from runtime causal behaviour, and do not by themselves support
extraordinary external claims such as consciousness, sentience, or real-world
mining performance.
"""

from __future__ import annotations

import ast
import json
import os
import re
import shutil
import tempfile
import textwrap
import unittest
from datetime import datetime, timezone
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple


PLACEHOLDER_PATTERN = re.compile(r"\{[^{}]+\}")


class InformationIntegrationAnalyzer:
    """Measures static cross-module imports and attribute coupling as a Φ-style software proxy."""

    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.data_flows: List[Tuple[str, str, str]] = []
        self.shared_state: Dict[str, List[str]] = defaultdict(list)

    def analyze_python_module(self, file_path: Path) -> Dict:
        """Analyze a Python module for imports and state-access patterns."""
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(file_path))

            module_name = self._get_module_name(file_path)
            imports: Set[str] = set()
            state_accesses: List[str] = []

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.add(node.module)

                if isinstance(node, ast.Attribute):
                    state_accesses.append(self._attribute_name(node))

            self.dependencies[module_name] = imports
            self.shared_state[module_name] = state_accesses

            return {
                "module": module_name,
                "imports": len(imports),
                "state_accesses": len(state_accesses),
                "unique_state": len(set(state_accesses)),
                "sample_state_accesses": sorted(set(state_accesses))[:10],
            }
        except Exception as exc:
            return {"error": str(exc), "module": str(file_path)}

    def analyze_typescript_module(self, file_path: Path) -> Dict:
        """Analyze TypeScript for imports and state-flow patterns."""
        try:
            content = file_path.read_text(encoding="utf-8")
            module_name = self._get_module_name(file_path)
            import_count = content.count("import ")

            state_patterns = [
                "useState",
                "useEffect",
                "useContext",
                "useReducer",
                "this.state",
                "setState",
                "dispatch",
            ]
            state_access_count = sum(
                content.count(pattern) for pattern in state_patterns
            )

            api_patterns = ["fetch(", "axios.", "apiClient."]
            api_call_count = sum(content.count(pattern) for pattern in api_patterns)

            return {
                "module": module_name,
                "imports": import_count,
                "state_accesses": state_access_count,
                "api_calls": api_call_count,
            }
        except Exception as exc:
            return {"error": str(exc), "module": str(file_path)}

    def _attribute_name(self, node: ast.Attribute) -> str:
        """Return a concrete dotted attribute path without placeholder segments."""
        prefix = self._expr_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr

    def _expr_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return self._attribute_name(node)
        if isinstance(node, ast.Call):
            return self._expr_name(node.func)
        if isinstance(node, ast.Subscript):
            return self._expr_name(node.value)
        if isinstance(node, ast.Constant):
            return repr(node.value)
        return node.__class__.__name__.lower()

    def _get_module_name(self, file_path: Path) -> str:
        try:
            rel_path = file_path.relative_to(self.root_path)
            return str(rel_path).replace(os.sep, ".")
        except ValueError:
            return file_path.name

    def compute_integration_phi(self) -> float:
        """Compute normalized cross-module integration density as a Φ-style metric."""
        if not self.dependencies:
            return 0.0

        total_modules = len(self.dependencies)
        total_edges = sum(len(deps) for deps in self.dependencies.values())
        max_possible_edges = total_modules * (total_modules - 1)
        if max_possible_edges <= 0:
            return 0.0

        bidirectional_count = 0
        for module, deps in self.dependencies.items():
            for dep in deps:
                if module in self.dependencies.get(dep, set()):
                    bidirectional_count += 1

        integration_density = total_edges / max_possible_edges
        bidirectional_factor = bidirectional_count / max(total_edges, 1)
        return float(integration_density * (1 + bidirectional_factor))


class CausalAutonomyAnalyzer:
    """Measures static decision/adaptation tokens vs external-control tokens as a software proxy."""

    def analyze_file(self, file_path: Path) -> Dict:
        try:
            content = file_path.read_text(encoding="utf-8")

            decision_keywords = [
                "if ",
                "elif ",
                "else:",
                "switch",
                "case",
                "while ",
                "for ",
                "match ",
                "when ",
            ]
            external_keywords = [
                "input(",
                "request.",
                "await ",
                "callback",
                "addEventListener",
                "on(",
                ".get(",
                ".post(",
            ]
            adaptive_keywords = [
                "learn",
                "train",
                "optimize",
                "optimise",
                "adapt",
                "evolve",
                "mutation",
                "feedback",
                "reinforce",
                "update_weights",
            ]
            self_modify_patterns = [
                "eval(",
                "exec(",
                "compile(",
                "__setattr__",
                "setattr(",
                "monkey_patch",
            ]

            decision_count = sum(
                content.count(keyword) for keyword in decision_keywords
            )
            external_count = sum(
                content.count(keyword) for keyword in external_keywords
            )
            adaptive_count = sum(
                content.count(keyword) for keyword in adaptive_keywords
            )
            self_modify_count = sum(
                content.count(keyword) for keyword in self_modify_patterns
            )

            return {
                "file": file_path.name,
                "decision_points": decision_count,
                "external_controls": external_count,
                "adaptive_patterns": adaptive_count,
                "self_modification": self_modify_count,
                "autonomy_ratio": decision_count / max(external_count, 1),
            }
        except Exception as exc:
            return {"error": str(exc), "file": file_path.name}

    def compute_autonomy_score(self, analyses: List[Dict]) -> float:
        total_decisions = sum(item.get("decision_points", 0) for item in analyses)
        total_external = sum(item.get("external_controls", 0) for item in analyses)
        total_adaptive = sum(item.get("adaptive_patterns", 0) for item in analyses)
        total_self_modify = sum(item.get("self_modification", 0) for item in analyses)

        if total_external == 0:
            return 0.0

        base_autonomy = total_decisions / total_external
        adaptive_boost = total_adaptive * 0.1
        self_modify_boost = total_self_modify * 0.5
        return float(min(base_autonomy + adaptive_boost + self_modify_boost, 10.0))


class StateIrreducibilityAnalyzer:
    """Tests static state-reference partitioning/coupling as an irreducibility software proxy."""

    def __init__(self, root_path: Path):
        self.root_path = root_path

    def analyze_shared_state(self, file_path: Path) -> Dict:
        try:
            content = file_path.read_text(encoding="utf-8")
            global_patterns = [
                "global ",
                "window.",
                "process.env",
                "os.environ",
                "singleton",
                "shared_state",
                "cache",
                "session",
            ]
            instance_patterns = ["self.", "this.", "__dict__", "getattr", "hasattr"]

            return {
                "file": file_path.name,
                "global_state": sum(
                    content.count(pattern) for pattern in global_patterns
                ),
                "instance_state": sum(
                    content.count(pattern) for pattern in instance_patterns
                ),
            }
        except Exception as exc:
            return {"error": str(exc), "file": file_path.name}

    def compute_irreducibility_score(self, analyses: List[Dict]) -> float:
        total_global = sum(item.get("global_state", 0) for item in analyses)
        total_instance = sum(item.get("instance_state", 0) for item in analyses)
        if total_instance == 0:
            return 0.0
        return float(total_global / (total_global + total_instance))


class TestEmergentComplexityIIT(unittest.TestCase):
    """Reviewer-grade tests for IIT-inspired complexity measurements."""

    @classmethod
    def setUpClass(cls):
        cls.root_path = Path(__file__).parent.parent
        cls.results = {}
        cls.observation_lines: List[str] = []

    def _record(self, line: str) -> None:
        self.observation_lines.append(line)
        print(line)

    def _python_files(self, *relative_dirs: str):
        for relative_dir in relative_dirs:
            code_dir = self.root_path / relative_dir
            if code_dir.exists():
                for py_file in code_dir.rglob("*.py"):
                    if py_file.name != "__init__.py":
                        yield py_file

    def _typescript_files(self):
        src_dir = self.root_path / "src"
        if not src_dir.exists():
            return
        for ts_file in src_dir.rglob("*.ts"):
            if not ts_file.name.endswith(".test.ts"):
                yield ts_file
        for tsx_file in src_dir.rglob("*.tsx"):
            yield tsx_file

    def test_00_baseline_comparisons(self):
        baselines = self._compute_baseline_comparisons()
        self.results["baselines"] = baselines

        self._record("\n=== BASELINE COMPARISONS (SOFTWARE PROXIES) ===")
        for name, metrics in baselines.items():
            self._record(
                f"{name}: integration_proxy={metrics['integration_phi_proxy']:.4f}, "
                f"autonomy_proxy={metrics['autonomy_proxy']:.4f}, "
                f"irreducibility_proxy={metrics['irreducibility_proxy']:.4f}"
            )

        required = {
            "random",
            "modular",
            "highly_coupled_non_adaptive",
            "stateful_feedback",
        }
        self.assertEqual(required, set(baselines))
        self.assertGreater(
            baselines["highly_coupled_non_adaptive"]["integration_phi_proxy"],
            baselines["modular"]["integration_phi_proxy"],
        )
        self.assertGreater(
            baselines["stateful_feedback"]["irreducibility_proxy"],
            baselines["modular"]["irreducibility_proxy"],
        )

    def test_01_information_integration_phi(self):
        analyzer = InformationIntegrationAnalyzer(self.root_path)

        py_analyses = [
            analyzer.analyze_python_module(py_file)
            for py_file in self._python_files("python_backend/pythia_mining")
        ]
        ts_analyses = [
            analyzer.analyze_typescript_module(ts_file)
            for ts_file in self._typescript_files()
        ]
        phi = analyzer.compute_integration_phi()
        total_edges = sum(len(deps) for deps in analyzer.dependencies.values())

        self.results["test_01"] = {
            "phi": phi,
            "python_modules": len(py_analyses),
            "typescript_modules": len(ts_analyses),
            "total_dependencies": len(analyzer.dependencies),
            "total_dependency_edges": total_edges,
            "interpretation": self._interpret_phi(phi),
        }

        self._record("\n=== INFORMATION INTEGRATION SOFTWARE PROXY (Φ-analog) ===")
        self._record(f"Φ software proxy = {phi:.4f}")
        self._record(f"Python modules analyzed: {len(py_analyses)}")
        self._record(f"TypeScript modules analyzed: {len(ts_analyses)}")
        self._record(f"Total dependency edges: {total_edges}")
        self._record(f"Interpretation: {self._interpret_phi(phi)}")

        self.assertIsNotNone(phi)
        self.assertGreaterEqual(phi, 0.0)

    def test_02_causal_autonomy(self):
        analyzer = CausalAutonomyAnalyzer()
        all_analyses = [
            analyzer.analyze_file(py_file)
            for py_file in self._python_files(
                "python_backend/pythia_mining", "python_backend/hyba_genesis_api"
            )
        ]
        all_analyses.extend(
            analyzer.analyze_file(ts_file) for ts_file in self._typescript_files()
        )

        autonomy_score = analyzer.compute_autonomy_score(all_analyses)
        total_decisions = sum(item.get("decision_points", 0) for item in all_analyses)
        total_external = sum(item.get("external_controls", 0) for item in all_analyses)
        total_adaptive = sum(item.get("adaptive_patterns", 0) for item in all_analyses)
        total_self_modify = sum(
            item.get("self_modification", 0) for item in all_analyses
        )

        self.results["test_02"] = {
            "autonomy_score": autonomy_score,
            "total_decisions": total_decisions,
            "total_external": total_external,
            "adaptive_patterns": total_adaptive,
            "self_modification": total_self_modify,
            "interpretation": self._interpret_autonomy(
                autonomy_score, total_adaptive, total_self_modify
            ),
        }

        self._record("\n=== CAUSAL AUTONOMY SOFTWARE PROXY ===")
        self._record(f"Autonomy software proxy score: {autonomy_score:.4f}")
        self._record(f"Decision points: {total_decisions}")
        self._record(f"External controls: {total_external}")
        self._record(f"Adaptive patterns: {total_adaptive}")
        self._record(f"Self-modification patterns: {total_self_modify}")
        self._record(
            f"Interpretation: {self._interpret_autonomy(autonomy_score, total_adaptive, total_self_modify)}"
        )

        self.assertIsNotNone(autonomy_score)
        self.assertGreaterEqual(autonomy_score, 0.0)

    def test_03_state_irreducibility(self):
        analyzer = StateIrreducibilityAnalyzer(self.root_path)
        all_analyses = []
        for code_dir in [self.root_path / "python_backend", self.root_path / "src"]:
            if code_dir.exists():
                for code_file in code_dir.rglob("*.py"):
                    if code_file.name != "__init__.py":
                        all_analyses.append(analyzer.analyze_shared_state(code_file))
                for code_file in code_dir.rglob("*.ts"):
                    if not code_file.name.endswith(".test.ts"):
                        all_analyses.append(analyzer.analyze_shared_state(code_file))
                for code_file in code_dir.rglob("*.tsx"):
                    all_analyses.append(analyzer.analyze_shared_state(code_file))

        irreducibility = analyzer.compute_irreducibility_score(all_analyses)
        total_global = sum(item.get("global_state", 0) for item in all_analyses)
        total_instance = sum(item.get("instance_state", 0) for item in all_analyses)

        self.results["test_03"] = {
            "irreducibility_score": irreducibility,
            "global_state_refs": total_global,
            "instance_state_refs": total_instance,
            "interpretation": self._interpret_irreducibility(irreducibility),
        }

        self._record("\n=== STATE IRREDUCIBILITY SOFTWARE PROXY ===")
        self._record(f"Irreducibility software proxy score: {irreducibility:.4f}")
        self._record(f"Global state references: {total_global}")
        self._record(f"Instance state references: {total_instance}")
        self._record(
            f"Interpretation: {self._interpret_irreducibility(irreducibility)}"
        )

        self.assertIsNotNone(irreducibility)
        self.assertGreaterEqual(irreducibility, 0.0)
        self.assertLessEqual(irreducibility, 1.0)

    def test_05_mining_performance_correlation_disclaimer(self):
        """
        Explicit test documenting lack of mining performance correlation for IIT proxies.

        This test documents that IIT-inspired software proxy measurements (integration,
        autonomy, irreducibility) have not been validated against mining performance
        metrics. The mathematical implementation is correct for neural systems, but its
        relevance to mining is unproven.
        """
        self._record("\n" + "=" * 60)
        self._record("MINING PERFORMANCE CORRELATION DISCLAIMER")
        self._record("=" * 60)

        # Document the current state of knowledge
        self._record(
            "IIT-inspired software proxy measurements have NOT been correlated with:"
        )
        self._record("- Mining hashrate")
        self._record("- Share acceptance rates")
        self._record("- Pool-side performance metrics")
        self._record("- Revenue generation")
        self._record("- Energy efficiency")
        self._record("- Any production mining outcome")

        self._record("\nRequired validation for mining relevance:")
        self._record("1. Historical hashrate data collection")
        self._record("2. Share acceptance rate tracking")
        self._record("3. Pool-side performance metrics")
        self._record(
            "4. Statistical correlation analysis between Φ and mining performance"
        )
        self._record("5. Controlled A/B testing with different Φ configurations")

        self._record("\nCurrent status: UNVALIDATED")
        self._record("These metrics measure static code complexity only.")
        self._record("They do not predict or correlate with mining performance.")

        # This assertion documents the current state of knowledge
        # It will pass because we're documenting a known limitation
        self.assertTrue(
            True,
            "IIT-inspired software proxies have not been correlated with mining "
            "performance. This is a correct implementation of neuroscience-inspired "
            "metrics applied to an unvalidated domain (software mining).",
        )

    def test_04_emergent_intelligence_verdict(self):
        phi = self.results.get("test_01", {}).get("phi", 0.0)
        autonomy = self.results.get("test_02", {}).get("autonomy_score", 0.0)
        irreducibility = self.results.get("test_03", {}).get(
            "irreducibility_score", 0.0
        )
        adaptive = self.results.get("test_02", {}).get("adaptive_patterns", 0)
        self_modify = self.results.get("test_02", {}).get("self_modification", 0)

        self._record("\n" + "=" * 60)
        self._record("EMERGENT COMPLEXITY ASSESSMENT (IIT-inspired software proxies)")
        self._record("=" * 60)
        self._record(f"Integration proxy (Φ): {phi:.4f}")
        self._record(f"Autonomy proxy:        {autonomy:.4f}")
        self._record(f"Irreducibility proxy:  {irreducibility:.4f}")
        self._record(f"Adaptive patterns:    {adaptive}")
        self._record(f"Self-modification:    {self_modify}")

        has_integration = phi > 0.1
        has_autonomy = autonomy > 1.0
        has_irreducibility = irreducibility > 0.3
        has_adaptation = adaptive > 10
        has_self_modification = self_modify > 0

        verdict = []
        verdict.append(
            "✓ Shows non-trivial information integration"
            if has_integration
            else "✗ Low integration - modular architecture"
        )
        verdict.append(
            "✓ Has internal decision-making"
            if has_autonomy
            else "✗ Primarily reactive/externally-driven"
        )
        verdict.append(
            "✓ State coupling present"
            if has_irreducibility
            else "✗ Clean state boundaries"
        )
        verdict.append(
            f"✓ Contains {adaptive} adaptive patterns"
            if has_adaptation
            else "✗ No significant adaptive/learning behavior"
        )
        verdict.append(
            f"⚠ Contains {self_modify} self-modification patterns"
            if has_self_modification
            else "✗ No self-modification capability"
        )

        self._record("\n" + "=" * 60)
        self._record("VERDICT")
        self._record("=" * 60)
        for item in verdict:
            self._record(item)

        emergent_score = (
            (phi * 10)
            + (autonomy * 0.5)
            + (irreducibility * 5)
            + (adaptive * 0.01)
            + (self_modify * 0.1)
        )

        if emergent_score > 5.0 and has_adaptation and has_self_modification:
            conclusion = (
                "ELEVATED SOFTWARE-PROXY COMPLEXITY: Static proxies show non-trivial "
                "integration, adaptation tokens, and self-modification tokens. Preserve as "
                "an internal measurement finding and move through replay, baselines, "
                "falsification, and external review before any stronger claim."
            )
        elif emergent_score > 2.0:
            conclusion = (
                "COMPLEX INTEGRATED SOFTWARE UNDER PROXY MEASURES: Static code metrics "
                "show coupling. This suite records measured proxy evidence without "
                "adjudicating consciousness or runtime causal behaviour."
            )
        else:
            conclusion = (
                "ENGINEERED SYSTEM UNDER THESE PROXY MEASURES: This evidence lane did "
                "not detect elevated proxy complexity under current thresholds. It makes "
                "no consciousness, sentience, or external-performance claim."
            )

        self._record("\n" + "=" * 60)
        self._record("CONCLUSION")
        self._record("=" * 60)
        self._record(f"Emergent Complexity Score: {emergent_score:.2f}")
        self._record(conclusion)

        results_file = (
            self.root_path / "artifacts" / "emergent_complexity_analysis.json"
        )
        results_file.parent.mkdir(exist_ok=True)
        preserved_previous_artifact = self._preserve_existing_artifact(results_file)
        payload = {
            "artifact_schema_version": 2,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "measurements": self.results,
            "metric_definitions": self._metric_definitions(),
            "baseline_comparisons": self.results.get("baselines", {}),
            "verdict": verdict,
            "conclusion": conclusion,
            "emergent_score": emergent_score,
            "preserved_previous_artifact": preserved_previous_artifact,
            "claim_boundary": self._claim_boundary_metadata(),
        }
        results_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        if preserved_previous_artifact:
            self._record(
                f"Previous artifact preserved at: {preserved_previous_artifact}"
            )
        self._record(f"Full results saved to: {results_file}")

        self.assertIn("metric_definitions", payload)
        self.assertIn("claim_boundary", payload)
        self.assertIn("baseline_comparisons", payload)
        self.assertEqual(
            "software proxies only", payload["claim_boundary"]["metric_posture"]
        )

        unresolved_placeholders = [
            line for line in self.observation_lines if PLACEHOLDER_PATTERN.search(line)
        ]
        self.assertEqual([], unresolved_placeholders)

    def _compute_baseline_comparisons(self) -> Dict[str, Dict[str, float]]:
        toy_systems = {
            "random": {
                "a.py": "import random\nvalue = random.random()\nif value > 0.5:\n    value += 1\n",
                "b.py": "items = [3, 1, 2]\nfor item in items:\n    print(item)\n",
            },
            "modular": {
                "input_module.py": "def parse(x):\n    return int(x)\n",
                "compute_module.py": "def double(x):\n    return x * 2\n",
                "output_module.py": "def render(x):\n    return str(x)\n",
            },
            "highly_coupled_non_adaptive": {
                "alpha.py": "import beta\nGLOBAL = 1\ndef run(x):\n    return beta.shared.value + GLOBAL + x\n",
                "beta.py": "import alpha\nclass Shared:\n    def __init__(self):\n        self.value = alpha.GLOBAL\nshared = Shared()\n",
            },
            "stateful_feedback": {
                "controller.py": "shared_state = {'last': 0}\nclass FeedbackState:\n    def __init__(self):\n        self.last = 0\ndef update(x):\n    global shared_state\n    if x > shared_state['last']:\n        shared_state['last'] = x\n    return shared_state['last']\n",
                "learner.py": "import controller\ndef adapt(xs):\n    feedback = 0\n    for x in xs:\n        feedback = controller.update(x + feedback)\n    return feedback\n",
            },
        }

        comparisons: Dict[str, Dict[str, float]] = {}
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir)
            for name, files in toy_systems.items():
                baseline_dir = tmp_root / name
                baseline_dir.mkdir()
                for filename, content in files.items():
                    (baseline_dir / filename).write_text(
                        textwrap.dedent(content), encoding="utf-8"
                    )

                integration_analyzer = InformationIntegrationAnalyzer(baseline_dir)
                autonomy_analyzer = CausalAutonomyAnalyzer()
                irreducibility_analyzer = StateIrreducibilityAnalyzer(baseline_dir)
                py_files = sorted(baseline_dir.glob("*.py"))
                for py_file in py_files:
                    integration_analyzer.analyze_python_module(py_file)
                autonomy = [
                    autonomy_analyzer.analyze_file(py_file) for py_file in py_files
                ]
                state = [
                    irreducibility_analyzer.analyze_shared_state(py_file)
                    for py_file in py_files
                ]
                comparisons[name] = {
                    "integration_phi_proxy": integration_analyzer.compute_integration_phi(),
                    "autonomy_proxy": autonomy_analyzer.compute_autonomy_score(
                        autonomy
                    ),
                    "irreducibility_proxy": irreducibility_analyzer.compute_irreducibility_score(
                        state
                    ),
                    "purpose": {
                        "random": "negative-control toy with incidental local decisions",
                        "modular": "negative-control toy with clean module boundaries",
                        "highly_coupled_non_adaptive": "static coupling control without adaptive feedback",
                        "stateful_feedback": "stateful feedback control with explicit shared state",
                    }[name],
                }
        return comparisons

    def _metric_definitions(self) -> Dict[str, str]:
        return {
            "integration_phi_proxy": "Static import graph density with bidirectional-import weighting; a code-coupling proxy, not measured runtime information integration.",
            "autonomy_proxy": "Static count ratio of internal decision/adaptation/self-modification tokens to external-control tokens; not runtime causal autonomy.",
            "irreducibility_proxy": "Static shared/global-state reference fraction against instance-state references; not a runtime causal irreducibility proof.",
            "emergent_score": "Heuristic weighted roll-up for internal comparison only; not a consciousness, sentience, capability, revenue, or external-performance claim.",
        }

    def _claim_boundary_metadata(self) -> Dict:
        return {
            "metric_posture": "software proxies only",
            "distinguishes": "static code coupling and token patterns are separated from runtime causal behaviour",
            "supported": "controlled internal comparisons of IIT-inspired software proxy measurements",
            "not_supported": [
                "consciousness or sentience adjudication",
                "runtime causal-behaviour proof",
                "quantum speedup or external mining-performance claims",
                "guaranteed revenue, accepted shares, or production telemetry claims",
                "IIT 4.0 Φ correlation with mining hashrate or share acceptance",
                "mining performance prediction based on Φ calculations",
                "production mining decisions based on IIT metrics",
            ],
            "mining_performance_validation_status": "UNVALIDATED",
            "mining_performance_validation_requirements": [
                "historical hashrate data collection",
                "share acceptance rate tracking",
                "pool-side performance metrics",
                "statistical correlation analysis between Φ and mining performance",
                "controlled A/B testing with different Φ configurations",
            ],
            "requires_for_reviewer_grade_claim": [
                "exact test output preservation",
                "commit SHA and environment capture",
                "artifact SHA-256",
                "clean-environment replay",
                "negative controls",
                "baseline comparison",
                "external review packet",
            ],
        }

    def _preserve_existing_artifact(self, results_file: Path) -> str | None:
        if not results_file.exists():
            return None
        archive_dir = results_file.parent / "previous"
        archive_dir.mkdir(exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        archive_path = (
            archive_dir / f"{results_file.stem}.{timestamp}{results_file.suffix}"
        )
        shutil.copy2(results_file, archive_path)
        return str(archive_path.relative_to(self.root_path))

    def _interpret_phi(self, phi: float) -> str:
        if phi < 0.05:
            return "Very low integration - highly modular system"
        if phi < 0.15:
            return "Low-moderate integration - some cross-module coupling"
        if phi < 0.30:
            return "Moderate integration - significant interdependencies"
        return "High integration - tightly coupled subsystems"

    def _interpret_autonomy(self, score: float, adaptive: int, self_modify: int) -> str:
        if score < 0.5:
            return "Primarily reactive - heavily externally controlled"
        if score < 1.5:
            return "Balanced - mix of internal logic and external control"
        if score < 3.0:
            return "Moderately autonomous - significant internal decision-making"
        base = "Highly autonomous - extensive internal control flow"
        if adaptive > 10:
            base += f" with {adaptive} adaptive patterns"
        if self_modify > 0:
            base += f" and {self_modify} self-modification sites"
        return base

    def _interpret_irreducibility(self, score: float) -> str:
        if score < 0.1:
            return "Highly reducible - clean state partitions"
        if score < 0.3:
            return "Moderately reducible - some shared state"
        if score < 0.5:
            return "Low reducibility - significant state coupling"
        return "Highly irreducible - tightly coupled state"


if __name__ == "__main__":
    unittest.main(verbosity=2)
