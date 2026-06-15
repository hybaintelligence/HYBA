"""
IIT-Inspired Emergent Complexity Analysis

Tests for detecting emergent intelligence patterns using principles from
Integrated Information Theory (IIT) adapted for software systems.

Scientific posture:
- These measurements are software integration proxies, not consciousness proof.
- Outputs must interpolate measured values, not literal placeholder strings.
- Results are evidence for controlled comparison, baseline testing, and review.

Measures:
1. Information Integration (Φ-analog): Cross-module coupling and information flow
2. Causal Autonomy: Self-directed decision paths vs external control
3. State Irreducibility: Whether system behavior can be decomposed or is truly integrated
"""

from __future__ import annotations

import ast
import json
import os
import re
import unittest
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple


PLACEHOLDER_PATTERN = re.compile(r"\{[^{}]+\}")


class InformationIntegrationAnalyzer:
    """Measures cross-module information flow and coupling as a software Φ-proxy."""

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
            state_access_count = sum(content.count(pattern) for pattern in state_patterns)

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
        if isinstance(node.value, ast.Name):
            return f"{node.value.id}.{node.attr}"
        if isinstance(node.value, ast.Attribute):
            return f"{self._attribute_name(node.value)}.{node.attr}"
        return f"unknown.{node.attr}"

    def _get_module_name(self, file_path: Path) -> str:
        try:
            rel_path = file_path.relative_to(self.root_path)
            return str(rel_path).replace(os.sep, ".")
        except ValueError:
            return file_path.name

    def compute_integration_phi(self) -> float:
        """Compute normalized cross-module integration density as a Φ-analog."""
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
    """Measures internal decision-making patterns vs external-control patterns."""

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

            decision_count = sum(content.count(keyword) for keyword in decision_keywords)
            external_count = sum(content.count(keyword) for keyword in external_keywords)
            adaptive_count = sum(content.count(keyword) for keyword in adaptive_keywords)
            self_modify_count = sum(content.count(keyword) for keyword in self_modify_patterns)

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
    """Tests whether system state is partitioned or coupled across boundaries."""

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
                "global_state": sum(content.count(pattern) for pattern in global_patterns),
                "instance_state": sum(content.count(pattern) for pattern in instance_patterns),
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
    """Reviewer-grade tests for IIT-inspired software-complexity proxies."""

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

    def test_01_information_integration_phi(self):
        analyzer = InformationIntegrationAnalyzer(self.root_path)

        py_analyses = [
            analyzer.analyze_python_module(py_file)
            for py_file in self._python_files("python_backend/pythia_mining")
        ]
        ts_analyses = [analyzer.analyze_typescript_module(ts_file) for ts_file in self._typescript_files()]
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

        self._record("\n=== INFORMATION INTEGRATION (Φ-analog) ===")
        self._record(f"Φ = {phi:.4f}")
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
        all_analyses.extend(analyzer.analyze_file(ts_file) for ts_file in self._typescript_files())

        autonomy_score = analyzer.compute_autonomy_score(all_analyses)
        total_decisions = sum(item.get("decision_points", 0) for item in all_analyses)
        total_external = sum(item.get("external_controls", 0) for item in all_analyses)
        total_adaptive = sum(item.get("adaptive_patterns", 0) for item in all_analyses)
        total_self_modify = sum(item.get("self_modification", 0) for item in all_analyses)

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

        self._record("\n=== CAUSAL AUTONOMY ===")
        self._record(f"Autonomy Score: {autonomy_score:.4f}")
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

        self._record("\n=== STATE IRREDUCIBILITY ===")
        self._record(f"Irreducibility Score: {irreducibility:.4f}")
        self._record(f"Global state references: {total_global}")
        self._record(f"Instance state references: {total_instance}")
        self._record(f"Interpretation: {self._interpret_irreducibility(irreducibility)}")

        self.assertIsNotNone(irreducibility)
        self.assertGreaterEqual(irreducibility, 0.0)
        self.assertLessEqual(irreducibility, 1.0)

    def test_04_emergent_intelligence_verdict(self):
        phi = self.results.get("test_01", {}).get("phi", 0.0)
        autonomy = self.results.get("test_02", {}).get("autonomy_score", 0.0)
        irreducibility = self.results.get("test_03", {}).get("irreducibility_score", 0.0)
        adaptive = self.results.get("test_02", {}).get("adaptive_patterns", 0)
        self_modify = self.results.get("test_02", {}).get("self_modification", 0)

        self._record("\n" + "=" * 60)
        self._record("EMERGENT INTELLIGENCE ASSESSMENT (IIT-inspired)")
        self._record("=" * 60)
        self._record(f"Integration (Φ):      {phi:.4f}")
        self._record(f"Autonomy:             {autonomy:.4f}")
        self._record(f"Irreducibility:       {irreducibility:.4f}")
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
        verdict.append("✓ State coupling present" if has_irreducibility else "✗ Clean state boundaries")
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
                "POSSIBLE EMERGENT PROPERTIES: System shows non-trivial integration, "
                "adaptation, and self-modification. External review and baselines required."
            )
        elif emergent_score > 2.0:
            conclusion = (
                "COMPLEX BUT DETERMINISTIC: System is complex and coupled, but claims remain "
                "bounded to software integration proxies."
            )
        else:
            conclusion = (
                "ENGINEERED SYSTEM: Clean modular architecture with explicit control flow. "
                "No emergent intelligence detected by this proxy."
            )

        self._record("\n" + "=" * 60)
        self._record("CONCLUSION")
        self._record("=" * 60)
        self._record(f"Emergent Complexity Score: {emergent_score:.2f}")
        self._record(conclusion)

        results_file = self.root_path / "artifacts" / "emergent_complexity_analysis.json"
        results_file.parent.mkdir(exist_ok=True)
        payload = {
            "measurements": self.results,
            "verdict": verdict,
            "conclusion": conclusion,
            "emergent_score": emergent_score,
            "claim_boundary": {
                "supported": "IIT-inspired software integration, autonomy, and irreducibility proxy measurement",
                "not_supported_by_this_test_alone": [
                    "consciousness",
                    "AGI",
                    "subjective awareness",
                    "open-ended self-improvement",
                    "validated IIT claim",
                ],
            },
        }
        results_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        self._record(f"Full results saved to: {results_file}")

        unresolved_placeholders = [
            line for line in self.observation_lines if PLACEHOLDER_PATTERN.search(line)
        ]
        self.assertEqual([], unresolved_placeholders)

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
