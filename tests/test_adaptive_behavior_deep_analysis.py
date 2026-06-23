"""
Deep Analysis of Adaptive Behavior Patterns

This suite investigates whether adaptive-looking code represents genuine
closed-loop behavior or only naming conventions.

Scientific posture:
- These tests support claims about stateful adaptive computation.
- They do not by themselves prove consciousness, AGI, subjective awareness, or
  open-ended learning.
- The output artifact is evidence for the proof ladder, not a final claim.
"""

from __future__ import annotations

import ast
import json
import re
import unittest
from collections import defaultdict
from pathlib import Path
from typing import Dict, Set


class FeedbackLoopDetector:
    """Detect closed-loop patterns where state is used to update future state."""

    def analyze_python_file(self, file_path: Path) -> Dict:
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(file_path))
            loops = []

            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    lhs_names = self._get_assignment_targets(node)
                    rhs_names = self._get_names_in_expr(node.value)
                    feedback_vars = lhs_names & rhs_names
                    if feedback_vars:
                        loops.append(
                            {
                                "type": "state_feedback",
                                "variables": sorted(feedback_vars),
                                "line": getattr(node, "lineno", 0),
                            }
                        )

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and any(
                    keyword in node.name.lower()
                    for keyword in [
                        "update",
                        "adjust",
                        "tune",
                        "optimize",
                        "optimise",
                        "adapt",
                        "learn",
                    ]
                ):
                    modifies_state = any(
                        isinstance(child, (ast.Assign, ast.AugAssign))
                        and self._assigns_to_self(child)
                        for child in ast.walk(node)
                    )
                    if modifies_state:
                        loops.append(
                            {
                                "type": "update_method",
                                "function": node.name,
                                "line": getattr(node, "lineno", 0),
                            }
                        )

            accumulation_patterns = [
                r"\.append\(",
                r"\.extend\(",
                r"\.update\(",
                r"\[[\w\'\"\.]+\]\s*=",
                r"\+=",
            ]
            for pattern in accumulation_patterns:
                for match in re.finditer(pattern, content):
                    loops.append(
                        {
                            "type": "accumulation",
                            "pattern": pattern,
                            "line": content[: match.start()].count("\n") + 1,
                        }
                    )

            return {
                "file": str(file_path.name),
                "feedback_loops": loops,
                "count": len(loops),
            }
        except Exception as exc:
            return {"file": str(file_path.name), "error": str(exc), "count": 0}

    def _get_assignment_targets(self, node: ast.Assign) -> Set[str]:
        names: Set[str] = set()
        for target in node.targets:
            names.update(self._name_from_assignment_target(target))
        return names

    def _name_from_assignment_target(self, target) -> Set[str]:
        if isinstance(target, ast.Name):
            return {target.id}
        if isinstance(target, ast.Attribute):
            return {self._attribute_name(target)}
        if isinstance(target, (ast.Tuple, ast.List)):
            names: Set[str] = set()
            for element in target.elts:
                names.update(self._name_from_assignment_target(element))
            return names
        return set()

    def _get_names_in_expr(self, node) -> Set[str]:
        names: Set[str] = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                names.add(child.id)
            elif isinstance(child, ast.Attribute):
                names.add(self._attribute_name(child))
        return names

    def _attribute_name(self, node: ast.Attribute) -> str:
        if isinstance(node.value, ast.Name):
            return f"{node.value.id}.{node.attr}"
        return node.attr

    def _assigns_to_self(self, node) -> bool:
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AugAssign):
            targets = [node.target]
        else:
            targets = []

        for target in targets:
            if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
                if target.value.id == "self":
                    return True
        return False


class ParameterOptimizationDetector:
    """Detect parameters that are tuned based on performance or thresholds."""

    def analyze_file(self, file_path: Path) -> Dict:
        try:
            content = file_path.read_text(encoding="utf-8")
            optimizations = []
            optimization_patterns = [
                (r"gradient", "gradient_computation"),
                (r"learning_rate", "learning_rate_usage"),
                (r"loss\s*=", "loss_calculation"),
                (r"minimize|maximize|optimise|optimize", "optimization_call"),
                (r"backprop", "backpropagation"),
                (r"weight.*update|update.*weight", "weight_update"),
                (r"hyperparameter", "hyperparameter_tuning"),
                (r"threshold.*=.*adapt|adapt.*threshold", "adaptive_threshold"),
                (r"auto.*adjust|adjust.*auto", "auto_adjustment"),
                (r"dynamic.*config", "dynamic_configuration"),
            ]
            for pattern, label in optimization_patterns:
                for match in re.finditer(pattern, content, re.IGNORECASE):
                    optimizations.append(
                        {
                            "type": label,
                            "line": content[: match.start()].count("\n") + 1,
                            "snippet": content[
                                max(0, match.start() - 40) : match.end() + 40
                            ],
                        }
                    )
            return {
                "file": str(file_path.name),
                "optimizations": optimizations,
                "count": len(optimizations),
            }
        except Exception as exc:
            return {"file": str(file_path.name), "error": str(exc), "count": 0}


class MemoryAccumulationDetector:
    """Detect systems that accumulate experience or operational memory."""

    def analyze_file(self, file_path: Path) -> Dict:
        try:
            content = file_path.read_text(encoding="utf-8")
            memory_patterns = []
            memory_keywords = [
                (r"memory", "memory_reference"),
                (r"history", "history_tracking"),
                (r"cache", "caching"),
                (r"experience", "experience_accumulation"),
                (r"recall", "recall_mechanism"),
                (r"retain", "retention"),
                (r"remember", "memory_storage"),
                (r"ledger", "ledger_state"),
                (r"manifest", "manifest_state"),
            ]
            for pattern, label in memory_keywords:
                for match in re.finditer(pattern, content, re.IGNORECASE):
                    line_num = content[: match.start()].count("\n") + 1
                    line_start = content.rfind("\n", 0, match.start()) + 1
                    line_end = content.find("\n", match.end())
                    if line_end == -1:
                        line_end = len(content)
                    memory_patterns.append(
                        {
                            "type": label,
                            "line": line_num,
                            "context": content[line_start:line_end].strip()[:120],
                        }
                    )
            return {
                "file": str(file_path.name),
                "memory_patterns": memory_patterns,
                "count": len(memory_patterns),
            }
        except Exception as exc:
            return {"file": str(file_path.name), "error": str(exc), "count": 0}


class SelfModificationDetector:
    """Classify self-modification patterns and isolate dangerous runtime execution."""

    def analyze_file(self, file_path: Path) -> Dict:
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(file_path))
            modifications = []

            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue

                label = None
                severity = None
                context = ""
                if isinstance(node.func, ast.Name) and node.func.id in {"eval", "exec"}:
                    label = f"{node.func.id}_usage"
                    severity = "DANGEROUS"
                elif isinstance(node.func, ast.Name) and node.func.id == "compile":
                    label = "compile_usage"
                    severity = "MODERATE"
                elif isinstance(node.func, ast.Name) and node.func.id == "setattr":
                    label = "setattr_usage"
                    severity = "LOW"
                elif isinstance(node.func, ast.Name) and node.func.id in {
                    "globals",
                    "locals",
                }:
                    label = f"{node.func.id}_access"
                    severity = "MODERATE" if node.func.id == "globals" else "LOW"
                elif isinstance(node.func, ast.Name) and node.func.id == "type":
                    label = "dynamic_type_creation"
                    severity = "MODERATE"
                elif (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr == "__setattr__"
                ):
                    label = "setattr_override"
                    severity = "MODERATE"

                if label is None or severity is None:
                    continue

                line_num = getattr(node, "lineno", 0)
                content.rfind("\n", 0, max(0, getattr(node, "col_offset", 0))) + 1
                lines = content.splitlines()
                if 1 <= line_num <= len(lines):
                    context = lines[line_num - 1].strip()[:160]
                modifications.append(
                    {
                        "type": label,
                        "severity": severity,
                        "line": line_num,
                        "context": context,
                    }
                )

            return {
                "file": str(file_path.name),
                "modifications": modifications,
                "count": len(modifications),
            }
        except Exception as exc:
            return {"file": str(file_path.name), "error": str(exc), "count": 0}


class TestAdaptiveBehaviorDeepAnalysis(unittest.TestCase):
    """Deep dive into adaptive patterns found in the emergence scan."""

    @classmethod
    def setUpClass(cls):
        cls.root_path = Path(__file__).parent.parent
        cls.results = {}

    def _python_files(self):
        for code_dir in [self.root_path / "python_backend", self.root_path / "src"]:
            if code_dir.exists():
                for py_file in code_dir.rglob("*.py"):
                    if py_file.name != "__init__.py":
                        yield py_file

    def test_01_feedback_loops(self):
        detector = FeedbackLoopDetector()
        all_results = []
        for py_file in self._python_files():
            result = detector.analyze_python_file(py_file)
            if result.get("count", 0) > 0:
                all_results.append(result)

        total_loops = sum(r.get("count", 0) for r in all_results)
        all_results.sort(key=lambda x: x.get("count", 0), reverse=True)
        self.results["feedback_loops"] = {
            "total": total_loops,
            "files": len(all_results),
            "top_files": all_results[:5],
        }

        print("\n=== FEEDBACK LOOP ANALYSIS ===")
        print(f"Total feedback patterns found: {total_loops}")
        print(f"Files with feedback loops: {len(all_results)}")
        for index, result in enumerate(all_results[:5], 1):
            print(f"  {index}. {result['file']}: {result['count']} patterns")

        self.assertGreater(total_loops, 0, "Should find feedback patterns")

    def test_02_parameter_optimization(self):
        detector = ParameterOptimizationDetector()
        all_results = []
        for py_file in self._python_files():
            result = detector.analyze_file(py_file)
            if result.get("count", 0) > 0:
                all_results.append(result)

        total_optimizations = sum(r.get("count", 0) for r in all_results)
        self.results["optimizations"] = {
            "total": total_optimizations,
            "files": len(all_results),
        }

        print("\n=== PARAMETER OPTIMIZATION ANALYSIS ===")
        print(f"Total optimization patterns: {total_optimizations}")
        print(f"Files with optimization: {len(all_results)}")

    def test_03_memory_accumulation(self):
        detector = MemoryAccumulationDetector()
        all_results = []
        for py_file in self._python_files():
            result = detector.analyze_file(py_file)
            if result.get("count", 0) > 0:
                all_results.append(result)

        total_memory = sum(r.get("count", 0) for r in all_results)
        type_counts = defaultdict(int)
        for result in all_results:
            for pattern in result.get("memory_patterns", []):
                type_counts[pattern["type"]] += 1

        self.results["memory"] = {
            "total": total_memory,
            "files": len(all_results),
            "by_type": dict(type_counts),
        }

        print("\n=== MEMORY ACCUMULATION ANALYSIS ===")
        print(f"Total memory-related patterns: {total_memory}")
        print(f"Files with memory: {len(all_results)}")
        for mem_type, count in sorted(
            type_counts.items(), key=lambda item: item[1], reverse=True
        ):
            print(f"  {mem_type}: {count}")

        self.assertGreater(total_memory, 0, "Should find memory patterns")

    def test_04_self_modification_sites(self):
        detector = SelfModificationDetector()
        all_results = []
        dangerous_sites = []
        severity_counts = defaultdict(int)

        for py_file in self._python_files():
            result = detector.analyze_file(py_file)
            if result.get("count", 0) > 0:
                all_results.append(result)
                for mod in result.get("modifications", []):
                    severity_counts[mod["severity"]] += 1
                    if mod["severity"] == "DANGEROUS":
                        dangerous_sites.append({"file": result["file"], **mod})

        total_modifications = sum(r.get("count", 0) for r in all_results)
        self.results["self_modification"] = {
            "total": total_modifications,
            "files": len(all_results),
            "dangerous_sites": len(dangerous_sites),
            "by_severity": dict(severity_counts),
            "dangerous_details": dangerous_sites,
        }

        print("\n=== SELF-MODIFICATION SITE ANALYSIS ===")
        print(f"Total self-modification patterns: {total_modifications}")
        print(f"Files with self-modification: {len(all_results)}")
        print(f"DANGEROUS sites (builtin eval/exec): {len(dangerous_sites)}")
        for severity in ["DANGEROUS", "MODERATE", "LOW"]:
            print(f"  {severity}: {severity_counts.get(severity, 0)}")

    def test_05_adaptive_behavior_verdict(self):
        feedback = self.results.get("feedback_loops", {}).get("total", 0)
        optimizations = self.results.get("optimizations", {}).get("total", 0)
        memory = self.results.get("memory", {}).get("total", 0)
        self_mod = self.results.get("self_modification", {}).get("total", 0)
        dangerous = self.results.get("self_modification", {}).get("dangerous_sites", 0)

        genuine_adaptive = optimizations > 5 and feedback > 10 and memory > 20
        has_learning = optimizations > 0 and any(
            keyword in json.dumps(self.results).lower()
            for keyword in [
                "gradient",
                "backpropagation",
                "learning_rate",
                "weight_update",
            ]
        )
        has_dangerous_self_mod = dangerous > 0

        if genuine_adaptive and has_learning:
            conclusion = "ADAPTIVE SYSTEM: Contains learning/optimization evidence that requires follow-up validation."
        elif memory > 50 and feedback > 20:
            conclusion = "STATEFUL SYSTEM: Accumulates memory and uses feedback, but learning remains unproven."
        else:
            conclusion = "DETERMINISTIC SYSTEM: Adaptive keywords are insufficient for adaptive-behavior claim."

        results_file = self.root_path / "artifacts" / "adaptive_behavior_analysis.json"
        results_file.parent.mkdir(exist_ok=True)
        results_file.write_text(
            json.dumps(
                {
                    "measurements": self.results,
                    "genuine_adaptive": genuine_adaptive,
                    "has_learning": has_learning,
                    "has_dangerous_self_mod": has_dangerous_self_mod,
                    "conclusion": conclusion,
                    "claim_boundary": {
                        "supported": "stateful adaptive computation where feedback, optimisation, and memory evidence exist",
                        "not_supported_by_this_test_alone": [
                            "consciousness",
                            "AGI",
                            "subjective awareness",
                            "open-ended self-improvement",
                        ],
                    },
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        print("\n=== ADAPTIVE BEHAVIOR VERDICT ===")
        print(f"Feedback loops:        {feedback}")
        print(f"Optimization patterns: {optimizations}")
        print(f"Memory patterns:       {memory}")
        print(f"Self-modification:     {self_mod} ({dangerous} dangerous)")
        print(conclusion)
        print(f"Full results saved to: {results_file}")

        self.assertFalse(
            has_dangerous_self_mod,
            "Dangerous builtin eval/exec self-modification must be triaged before any emergence claim advances.",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
