from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {
    ".cfg",
    ".css",
    ".env",
    ".html",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".py",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}
SKIP_PARTS = {
    ".git",
    ".hypothesis",
    ".mypy_cache",
    ".pytest_cache",
    ".venv",
    "node_modules",
    "venv",
}
MARKER_PREFIXES = ("<" * 7, ">" * 7)
SEPARATOR_MARKER = "=" * 7


def iter_text_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
            continue
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        files.append(path)
    return files


def test_repository_contains_no_merge_conflict_markers() -> None:
    offenders: list[str] = []
    for path in iter_text_files():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line in text.splitlines():
            stripped = line.strip()
            if (
                any(stripped.startswith(marker) for marker in MARKER_PREFIXES)
                or stripped == SEPARATOR_MARKER
            ):
                offenders.append(str(path.relative_to(ROOT)))
                break

    assert not offenders, "merge-conflict markers remain in: " + ", ".join(sorted(offenders))
