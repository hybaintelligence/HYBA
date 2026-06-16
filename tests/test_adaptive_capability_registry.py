"""
Capability registry tests for the Controlled Adaptive Systems Science Program.

These tests keep capability documentation coupled to testable evidence. They are
intentionally conservative: every capability entry must name evidence files, a
local command, a supported claim, a known gap, a claim boundary, and a status.
"""

import re
from pathlib import Path


ROOT = Path(__file__).parent.parent
REGISTRY = ROOT / "docs" / "ADAPTIVE_SYSTEMS_CAPABILITY_REGISTRY.md"
CAPABILITY_ID_RE = re.compile(r"^### (ADAPT-[A-Z-]+-\d{3}) — (.+)$", re.MULTILINE)


def _registry_text() -> str:
    assert REGISTRY.exists(), "adaptive capability registry must exist"
    return REGISTRY.read_text(encoding="utf-8")


def _capability_sections() -> dict[str, str]:
    text = _registry_text()
    matches = list(CAPABILITY_ID_RE.finditer(text))
    assert matches, "registry must contain capability IDs"

    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[match.group(1)] = text[start:end]
    return sections


def test_registry_has_expected_capability_ids():
    sections = _capability_sections()

    assert set(sections) == {
        "ADAPT-FEEDBACK-001",
        "ADAPT-MEMORY-002",
        "ADAPT-OPTIMISE-003",
        "ADAPT-RUNTIME-004",
        "ADAPT-INTEGRATION-005",
        "ADAPT-CLAIM-GATE-006",
    }


def test_each_capability_has_required_evidence_fields():
    for capability_id, section in _capability_sections().items():
        assert "**Capability:**" in section, capability_id
        assert "**Evidence files:**" in section, capability_id
        assert "**Test command:**" in section, capability_id
        assert "**Current supported claim:**" in section, capability_id
        assert "**Known gap:**" in section, capability_id
        assert "**Claim boundary:**" in section, capability_id
        assert "**Status:**" in section, capability_id
        assert "python -m pytest" in section, capability_id


def test_registry_referenced_tests_exist():
    text = _registry_text()
    referenced_tests = sorted(set(re.findall(r"tests/test_[A-Za-z0-9_]+\.py", text)))

    assert referenced_tests, "registry must reference executable tests"
    for relative_path in referenced_tests:
        assert (ROOT / relative_path).exists(), f"missing referenced test file: {relative_path}"


def test_registry_preserves_claim_boundary_language():
    text = _registry_text()

    assert "supported claim" in text
    assert "known gap" in text
    assert "claim boundary" in text
    assert "Capability-to-proof ladder" in text
    assert "registry entry, test command, artifact, supported claim, known gap, and claim boundary" in text


def test_status_values_are_from_declared_vocabulary():
    text = _registry_text()
    allowed = {
        "implemented",
        "tested",
        "artifact-backed",
        "baseline-needed",
        "runtime-needed",
        "external-review-needed",
    }
    status_lines = re.findall(r"\*\*Status:\*\* (.+)", text)

    assert status_lines, "registry must include status lines"
    for status_line in status_lines:
        values = set(re.findall(r"`([^`]+)`", status_line))
        assert values, f"status line must contain backtick status values: {status_line}"
        assert values <= allowed, f"unknown status value(s): {values - allowed}"
