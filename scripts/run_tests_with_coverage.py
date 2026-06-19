#!/usr/bin/env python3
"""
Run all tests in the project and calculate coverage.
This script attempts to run all test suites and provide a coverage estimate.
"""

import os
import sys
import subprocess
from pathlib import Path


def check_pytest_cov():
    """Check if pytest-cov is available."""
    try:
        import pytest_cov  # noqa: F401

        return True
    except ImportError:
        return False


def run_backend_tests_with_coverage():
    """Run backend tests with coverage using pytest-cov."""
    print("Running backend tests with coverage...")

    # Set up environment
    env = os.environ.copy()
    env["PYTHONPATH"] = "python_backend"

    # Run pytest with coverage
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/",
        "--cov=python_backend",
        "--cov-report=term",
        "--cov-report=html",
        "--cov-report=xml",
        "-v",
    ]

    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        print("STDOUT:")
        print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)

        # Extract coverage percentage
        for line in result.stdout.split("\n"):
            if "TOTAL" in line and "%" in line:
                parts = line.split()
                for part in parts:
                    if "%" in part:
                        coverage = float(part.replace("%", ""))
                        print(f"\nCoverage: {coverage}%")
                        return coverage >= 80.0

        return False
    except Exception as e:
        print(f"Error running tests: {e}")
        return False


def run_frontend_tests():
    """Run frontend tests."""
    print("\nRunning frontend tests...")

    try:
        # Check if vitest is available
        result = subprocess.run(
            ["npx", "vitest", "run", "tests/test_property_frontend.test.ts"],
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running frontend tests: {e}")
        return False


def run_bridge_tests():
    """Run bridge/server tests."""
    print("\nRunning bridge/server tests...")

    try:
        result = subprocess.run(
            ["npx", "vitest", "run", "tests/test_bridge_server.test.ts"],
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running bridge tests: {e}")
        return False


def count_test_files():
    """Count the number of test files in the project."""
    test_dir = Path("tests")
    test_files = list(test_dir.glob("test_*.py")) + list(test_dir.glob("test_*.ts"))
    return len(test_files)


def main():
    print("=" * 80)
    print("Running all tests and checking coverage")
    print("=" * 80)

    # Check if pytest-cov is installed
    if not check_pytest_cov():
        print("ERROR: pytest-cov is not installed.")
        print("Please install it with: pip install pytest-cov")
        sys.exit(1)

    # Count test files
    test_count = count_test_files()
    print(f"Found {test_count} test files")

    # Run backend tests with coverage
    backend_passed = run_backend_tests_with_coverage()

    # Run frontend tests
    frontend_passed = run_frontend_tests()

    # Run bridge tests
    bridge_passed = run_bridge_tests()

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Backend tests: {'PASSED' if backend_passed else 'FAILED'}")
    print(f"Frontend tests: {'PASSED' if frontend_passed else 'FAILED'}")
    print(f"Bridge tests: {'PASSED' if bridge_passed else 'FAILED'}")

    # Check overall coverage
    if backend_passed:
        print("\nCoverage check: Backend tests passed with coverage report")
    else:
        print("\nCoverage check: Backend tests failed or coverage not calculated")

    # Exit with appropriate code
    if backend_passed and frontend_passed and bridge_passed:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
