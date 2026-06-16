#!/usr/bin/env python3
"""Fail CI when production runtime files contain fabricated telemetry patterns."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

RUNTIME_PATHS = [
    REPO_ROOT / "server.ts",
    REPO_ROOT / "src",
    REPO_ROOT / "python_backend" / "hyba_genesis_api",
    REPO_ROOT / "python_backend" / "pythia_mining",
]

EXCLUDED_PARTS = {
    "__pycache__",
    ".pytest_cache",
    "node_modules",
}

# Runtime code may use words like "fallback" for operational degradation, so this
# list focuses on high-risk literal values and phrases that previously represented
# fabricated mining, valuation, AI telemetry, or fake semantic audit labels.
BANNED_PATTERNS = [
    (re.compile(r"\b12345678\b"), "fixed optimizer nonce"),
    (re.compile(r"\b1234\b"), "fixed share count"),
    (re.compile(r"\b0\.967\b"), "fixed acceptance rate"),
    (re.compile(r"\b0\.9415\b"), "fixed quantum coherence"),
    (re.compile(r"\b38\.7\b"), "fixed quantum speedup"),
    (re.compile(r"\b0\.0594\b"), "fixed phi resonance"),
    (re.compile(r"\b17432891\.2\b"), "fixed integrated information"),
    (re.compile(r"\b2071\.08\b"), "fixed hashrate"),
    (re.compile(r"\b847249\b"), "fixed block height"),
    (re.compile(r"\b7234567890123(?:\.5)?\b"), "fixed network difficulty"),
    (
        re.compile(r"estimated_revenue_(?:btc|usd)\s*[:=]\s*[0-9]"),
        "fixed revenue estimate",
    ),
    (
        re.compile(r"np\.random|Math\.random|random\.randint"),
        "runtime random telemetry",
    ),
    (
        re.compile(r"inject_simulated_target_job\("),
        "runtime simulated mining job injection",
    ),
    (re.compile(r"Simulated Coherence", re.IGNORECASE), "simulated semantic audit label"),
    (re.compile(r"(?<!no\s)(?<!no\sfabricated,\s)(?<!no\sfabricated,\s)simulated\s+(?:coherence|telemetry|state|audit)", re.IGNORECASE), "simulated semantic audit label"),
    (re.compile(r"(?<!no\s)(?<!no\sfabricated,\s)(?<!no\sfabricated,\s)fixture\s+(?:telemetry|state|audit)", re.IGNORECASE), "fixture semantic audit label"),
    (re.compile(r"(?<!no\s)(?<!no\sfabricated,\s)(?<!no\sfabricated,\s)placeholder\s+(?:telemetry|state|audit)", re.IGNORECASE), "placeholder semantic audit label"),
    (re.compile(r"nonce\s*%\s*67"), "fake share acceptance rule"),
    (re.compile(r"Mock save logic", re.IGNORECASE), "mock credential save"),
    (re.compile(r"demoState", re.IGNORECASE), "frontend demo state payload"),
]

ALLOWED_FILES = {
    "tests/test_backend_workflows.py",
    "scripts/check_no_runtime_mocks.py",
    "docs/QUANTUM_MINING.md",
}

# Dev-only fixture implementation remains in stratum_client, but production must gate it.
ALLOWED_PATTERN_FILES = {
    "runtime simulated mining job injection": {
        "python_backend/pythia_mining/stratum_client.py",
        "python_backend/pythia_mining/genesis_ai.py",
    },
    "runtime random telemetry": {
        "python_backend/hyba_genesis_api/nicehash.py",
        # Consciousness research: perturbation analysis uses random for test signals
        "src/core/perturbation_analyzer.ts",
        # Security: shard rotation seed (should migrate to crypto.randomBytes in production)
        "src/core/security_swarm.ts",
        # Mathematical algorithms: sketch-based error estimation uses random sampling
        "python_backend/pythia_mining/phi_folding.py",
    },
}

TEXT_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".jsx", ".md", ".yml", ".yaml"}


def iter_runtime_files() -> list[Path]:
    files: list[Path] = []
    for root in RUNTIME_PATHS:
        if root.is_file():
            candidates = [root]
        else:
            candidates = [path for path in root.rglob("*") if path.is_file()]
        for path in candidates:
            if any(part in EXCLUDED_PARTS for part in path.parts):
                continue
            if path.suffix not in TEXT_SUFFIXES:
                continue
            rel = path.relative_to(REPO_ROOT).as_posix()
            if rel in ALLOWED_FILES:
                continue
            files.append(path)
    return files


def main() -> int:
    violations: list[str] = []
    for path in iter_runtime_files():
        rel = path.relative_to(REPO_ROOT).as_posix()
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern, label in BANNED_PATTERNS:
            if rel in ALLOWED_PATTERN_FILES.get(label, set()):
                continue
            for match in pattern.finditer(text):
                line_no = text.count("\n", 0, match.start()) + 1
                violations.append(f"{rel}:{line_no}: {label}: {match.group(0)!r}")

    if violations:
        print("Runtime mock/static telemetry guardrail failed:", file=sys.stderr)
        for violation in violations:
            print(f"  - {violation}", file=sys.stderr)
        return 1

    print("Runtime mock/static telemetry guardrail passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
