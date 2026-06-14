#!/usr/bin/env python3
"""Validate HYBA container entrypoint behavior used by Docker Compose.

The production image has one ENTRYPOINT shared by the single-container runtime
and the docker-compose service split. Compose service commands must therefore be
honored; otherwise backend/runtime/bridge services all start the bundled default
runtime instead of their explicit service process.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = ROOT / "scripts" / "hyba-runtime-entrypoint.sh"


def main() -> int:
    syntax = subprocess.run(
        ["sh", "-n", str(ENTRYPOINT)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if syntax.returncode != 0:
        print(syntax.stderr, file=sys.stderr)
        return syntax.returncode

    command = subprocess.run(
        [
            "sh",
            str(ENTRYPOINT),
            "python",
            "-c",
            "print('entrypoint command override honored')",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=5,
        check=False,
    )
    if command.returncode != 0:
        print(command.stdout, file=sys.stderr)
        print(command.stderr, file=sys.stderr)
        return command.returncode
    if "entrypoint command override honored" not in command.stdout:
        print("Entry point did not execute the provided service command", file=sys.stderr)
        print(command.stdout, file=sys.stderr)
        return 1

    print("Runtime entrypoint command override check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
