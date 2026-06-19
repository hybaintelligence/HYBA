#!/usr/bin/env python3
"""Run HYBA local governance gates and write an auditable transcript.

This runner is intentionally local-first. It does not depend on GitHub Actions,
paid CI, hosted runners, or external services. Use it before merging,
exporting external materials, sending partner/investor/sovereign claims, or
attempting to advance any mining commercialization stage.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable, NamedTuple


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TRANSCRIPT_DIR = ROOT / "docs" / "governance" / "local_gate_transcripts"


class GateCommand(NamedTuple):
    name: str
    argv: tuple[str, ...]


BASE_COMMANDS: tuple[GateCommand, ...] = (
    GateCommand(
        "claim-tier evidence binding",
        (sys.executable, "scripts/check_validation_claim_tiers.py"),
    ),
    GateCommand(
        "mining commercialization stage gates",
        (sys.executable, "scripts/check_commercialization_gates.py"),
    ),
)

PYTEST_COMMAND = GateCommand(
    "claim-tier regression tests",
    (sys.executable, "-m", "pytest", "tests/test_validation_claim_tiers.py", "-q"),
)


class GateResult(NamedTuple):
    command: GateCommand
    returncode: int
    stdout: str
    stderr: str


def run_command(command: GateCommand) -> GateResult:
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", "python_backend")
    completed = subprocess.run(
        command.argv,
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    return GateResult(
        command=command,
        returncode=completed.returncode,
        stdout=completed.stdout.strip(),
        stderr=completed.stderr.strip(),
    )


def markdown_block(text: str) -> str:
    if not text:
        return "_No output._"
    return "```text\n" + text.replace("```", "`\u200b``") + "\n```"


def write_transcript(results: Iterable[GateResult], transcript_dir: Path) -> Path:
    transcript_dir.mkdir(parents=True, exist_ok=True)
    now = _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    transcript_path = transcript_dir / f"local_governance_gate_{stamp}.md"
    results = list(results)
    passed = all(result.returncode == 0 for result in results)

    sections = [
        "# Local Governance Gate Transcript",
        "",
        f"- Timestamp UTC: `{now.isoformat()}`",
        f"- Repository root: `{ROOT}`",
        f"- Result: `{'PASS' if passed else 'FAIL'}`",
        f"- Python: `{sys.executable}`",
        "",
        "## Commands",
        "",
    ]

    for result in results:
        sections.extend(
            [
                f"### {result.command.name}",
                "",
                "Command:",
                markdown_block(" ".join(result.command.argv)),
                "",
                f"Return code: `{result.returncode}`",
                "",
                "Stdout:",
                markdown_block(result.stdout),
                "",
                "Stderr:",
                markdown_block(result.stderr),
                "",
            ]
        )

    sections.extend(
        [
            "## Operating rule",
            "",
            "A FAIL result blocks merge, external distribution, and mining commercialization-stage promotion until fixed and re-run.",
            "A PASS result is necessary but not sufficient for production claims; the underlying evidence manifest must still support the requested tier.",
            "",
        ]
    )

    transcript_path.write_text("\n".join(sections), encoding="utf-8")
    return transcript_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-pytest",
        action="store_true",
        help="Run only the two fast governance scripts, not the regression pytest.",
    )
    parser.add_argument(
        "--transcript-dir",
        default=str(DEFAULT_TRANSCRIPT_DIR),
        help="Directory where the markdown transcript should be written.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    commands = list(BASE_COMMANDS)
    if not args.skip_pytest:
        commands.append(PYTEST_COMMAND)

    results = [run_command(command) for command in commands]
    transcript_path = write_transcript(results, Path(args.transcript_dir).resolve())
    passed = all(result.returncode == 0 for result in results)

    print(f"Local governance gate transcript: {transcript_path}")
    print(f"Local governance gate result: {'PASS' if passed else 'FAIL'}")

    if not passed:
        for result in results:
            if result.returncode != 0:
                print(f"FAILED: {result.command.name} -> {result.returncode}", file=sys.stderr)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
