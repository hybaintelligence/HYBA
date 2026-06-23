#!/usr/bin/env python3
import os
import sys
import subprocess


def main():
    # Set up environment variables
    env = os.environ.copy()
    # Add python_backend to PYTHONPATH
    root = os.path.dirname(os.path.abspath(__file__))
    python_backend = os.path.join(root, "python_backend")
    env["PYTHONPATH"] = python_backend + os.pathsep + env.get("PYTHONPATH", "")

    # List of test files to run
    test_files = [
        "tests/test_replay_executor.py",
        "tests/test_manifest_registry.py",
        "tests/test_replay_claim_cli.py",
        "tests/test_replay_reporting.py",
        "tests/test_mining_auto_attester.py",
        "tests/test_replay_properties.py",
    ]

    print("=== Running replay-related tests ===")
    # Run pytest
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        *test_files,
    ]
    print("Command:", " ".join(cmd))
    result = subprocess.run(cmd, cwd=root, env=env, check=False)
    print(f"Test run exited with code: {result.returncode}")

    if result.returncode == 0:
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return result.returncode


if __name__ == "__main__":
    sys.exit(main())
