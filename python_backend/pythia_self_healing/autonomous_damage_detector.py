"""Autonomous codebase damage detection for the Salamander reactor.

The detector is intentionally deterministic and stdlib-only so it can run in
CI, boot checks, and forensic review contexts. It produces small, structured
``DamageReport`` dictionaries that can be consumed directly by the sovereign
SelfHealingReactor.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


class DamageReport(dict):
    """Dict-compatible damage report used by the reactor and tests.

    The class intentionally subclasses ``dict`` because earlier Salamander
    prototypes constructed reports as ``DamageReport({...})`` and accessed them
    via ``.get``. Keeping that shape preserves compatibility while giving the
    package a named type.
    """

    @property
    def needs_repair(self) -> bool:
        return bool(self.get("needs_repair", False))

    @property
    def issues(self) -> list[str]:
        return list(self.get("issues", []))

    @property
    def module_path(self) -> str | None:
        value = self.get("module_path")
        return str(value) if value is not None else None

    @property
    def target_name(self) -> str | None:
        value = self.get("target_name")
        return str(value) if value is not None else None


@dataclass(frozen=True)
class DamageSignal:
    issue: str
    severity: float
    line_number: int | None = None
    category: str = "quality"


@dataclass
class AutonomousDamageDetector:
    """Scan Python files for drift, brittleness, and repair candidates."""

    max_target_lines: int = 120
    max_file_bytes: int = 512_000
    todo_tokens: tuple[str, ...] = ("TODO", "FIXME", "HACK")
    performance_tokens: tuple[str, ...] = ("time.sleep", "subprocess.run", "shell=True")
    invariant_tokens: tuple[str, ...] = ("assert False", "raise NotImplementedError")
    security_tokens: tuple[str, ...] = ("eval(", "exec(", "pickle.loads")
    ignored_dirs: tuple[str, ...] = (
        ".git",
        "node_modules",
        ".venv",
        "venv",
        "__pycache__",
    )

    def scan_paths(
        self, paths: list[str | Path] | tuple[str | Path, ...]
    ) -> list[DamageReport]:
        """Scan files/directories and return reports sorted by severity."""

        reports: list[DamageReport] = []
        for path in paths:
            p = Path(path)
            for file_path in self._iter_python_files(p):
                reports.extend(self.scan_file(file_path))
        return sorted(
            reports, key=lambda report: report.get("severity_score", 0.0), reverse=True
        )

    def scan_file(self, path: str | Path) -> list[DamageReport]:
        file_path = Path(path)
        if not file_path.exists() or file_path.stat().st_size > self.max_file_bytes:
            return []

        text = file_path.read_text(encoding="utf-8", errors="replace")
        signals = self._text_signals(text)
        signals.extend(self._ast_signals(text))
        if not signals:
            return []

        target_name = self._select_target_name(text, signals)
        severity_score = min(
            1.0, sum(signal.severity for signal in signals) / max(1.0, len(signals))
        )
        categories = sorted({signal.category for signal in signals})
        report = DamageReport(
            {
                "needs_repair": True,
                "module_path": str(file_path),
                "target_name": target_name,
                "issues": [signal.issue for signal in signals],
                "severity_score": severity_score,
                "categories": categories,
                "line_numbers": [
                    signal.line_number
                    for signal in signals
                    if signal.line_number is not None
                ],
                "suggested_goal": self._suggest_goal(categories),
            }
        )
        return [report]

    def _iter_python_files(self, root: Path) -> Iterator[Path]:
        if root.is_file() and root.suffix == ".py":
            yield root
            return
        if not root.exists() or not root.is_dir():
            return
        for path in root.rglob("*.py"):
            if any(part in self.ignored_dirs for part in path.parts):
                continue
            yield path

    def _text_signals(self, text: str) -> list[DamageSignal]:
        signals: list[DamageSignal] = []
        for lineno, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            for token in self.todo_tokens:
                if token in stripped:
                    signals.append(
                        DamageSignal(
                            f"Technical debt marker {token} at line {lineno}",
                            0.45,
                            lineno,
                            "debt",
                        )
                    )
            for token in self.performance_tokens:
                if token in stripped:
                    signals.append(
                        DamageSignal(
                            f"Potential performance or process-risk token {token} at line {lineno}",
                            0.55,
                            lineno,
                            "performance",
                        )
                    )
            for token in self.invariant_tokens:
                if token in stripped:
                    signals.append(
                        DamageSignal(
                            f"Incomplete invariant path {token} at line {lineno}",
                            0.65,
                            lineno,
                            "invariant",
                        )
                    )
            for token in self.security_tokens:
                if token in stripped:
                    signals.append(
                        DamageSignal(
                            f"Potential unsafe dynamic execution token {token} at line {lineno}",
                            0.75,
                            lineno,
                            "security",
                        )
                    )
        return signals

    def _ast_signals(self, text: str) -> list[DamageSignal]:
        try:
            tree = ast.parse(text)
        except SyntaxError as exc:
            return [DamageSignal(f"Syntax drift: {exc.msg}", 1.0, exc.lineno, "syntax")]

        signals: list[DamageSignal] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                end = getattr(node, "end_lineno", node.lineno)
                span = int(end) - int(node.lineno) + 1
                if span > self.max_target_lines:
                    signals.append(
                        DamageSignal(
                            f"Target {node.name} spans {span} lines; exceeds Salamander small-limb limit",
                            0.8,
                            node.lineno,
                            "small_limb",
                        )
                    )
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                signals.append(
                    DamageSignal(
                        "Broad bare except handler detected",
                        0.6,
                        node.lineno,
                        "resilience",
                    )
                )
        return signals

    def _select_target_name(self, text: str, signals: list[DamageSignal]) -> str | None:
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return None
        signal_lines = [
            signal.line_number for signal in signals if signal.line_number is not None
        ]
        candidates: list[tuple[int, str]] = []
        for node in ast.walk(tree):
            if not isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
            ):
                continue
            start = int(node.lineno)
            end = int(getattr(node, "end_lineno", node.lineno))
            overlap = sum(1 for line in signal_lines if start <= line <= end)
            if overlap:
                candidates.append((overlap, node.name))
        if candidates:
            return sorted(candidates, reverse=True)[0][1]
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                return node.name
        return None

    @staticmethod
    def _suggest_goal(categories: list[str]) -> str:
        if "syntax" in categories:
            return "Restore parseability and invariant-safe execution"
        if "security" in categories:
            return "Remove unsafe dynamic execution and preserve security invariants"
        if "performance" in categories:
            return "Repair performance regression while preserving all invariants"
        if "small_limb" in categories:
            return "Split oversized limb into small sovereign-reviewable repair surface"
        if "invariant" in categories:
            return "Restore invariant compliance and add protection"
        if "resilience" in categories:
            return "Strengthen failure handling and resilience"
        return "Repair detected drift and strengthen resilience"
