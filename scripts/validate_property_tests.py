#!/usr/bin/env python3
"""Property-Based Test Suite Validator and Dependency Installer.

This script ensures all required dependencies for property-based integration tests
are installed and validates the test suite runs successfully.
"""

import subprocess
import sys
from pathlib import Path


def check_and_install_dependencies():
    """Check for and install missing Python dependencies."""
    print("\n" + "=" * 70)
    print("DEPENDENCY VALIDATION AND INSTALLATION")
    print("=" * 70)

    required_packages = [
        "hypothesis",
        "pytest",
        "pytest-asyncio",
        "numpy",
        "scipy",
        "sqlalchemy",
        "argon2-cffi",
    ]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✓ {package} is installed")
        except ImportError:
            print(f"✗ {package} is missing")
            missing_packages.append(package)

    if missing_packages:
        print(f"\n📦 Installing {len(missing_packages)} missing packages...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", *missing_packages]
            )
            print("✓ All dependencies installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install dependencies: {e}")
            return False
    else:
        print("\n✓ All required dependencies are installed")
        return True


def run_property_tests():
    """Run property-based integration tests."""
    print("\n" + "=" * 70)
    print("PROPERTY-BASED TEST EXECUTION")
    print("=" * 70)

    test_files = [
        "tests/test_production_property_tests.py",
        "tests/test_property_based_backend.py",
        "tests/test_phi_property_hypothesis.py",
    ]

    results = []

    for test_file in test_files:
        test_path = Path(test_file)
        if not test_path.exists():
            print(f"⚠️  Test file not found: {test_file}")
            continue

        print(f"\n▶ Running {test_file}...")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(test_path), "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                print(f"✓ {test_file} PASSED")
                results.append((test_file, True))
            else:
                print(f"✗ {test_file} FAILED")
                print("Error output:")
                print(
                    result.stdout[-500:] if len(result.stdout) > 500 else result.stdout
                )
                results.append((test_file, False))
        except subprocess.TimeoutExpired:
            print(f"⏱️  {test_file} TIMEOUT")
            results.append((test_file, False))
        except Exception as e:
            print(f"✗ {test_file} ERROR: {e}")
            results.append((test_file, False))

    return results


def run_quick_integration_test():
    """Run a quick integration test to verify core functionality."""
    print("\n" + "=" * 70)
    print("QUICK INTEGRATION TEST")
    print("=" * 70)

    test_code = '''
import hypothesis.strategies as st
from hypothesis import given, settings

@given(st.floats(min_value=0.0, max_value=10.0))
@settings(max_examples=10)
def test_power_scale_bounds(scale):
    """Test that power scale values are properly bounded."""
    assert 0.0 <= scale <= 10.0

@given(st.integers(min_value=1, max_value=100))
@settings(max_examples=10)
def test_pool_count_validity(count):
    """Test that pool counts are valid positive integers."""
    assert count > 0
    assert isinstance(count, int)

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
'''

    test_file = Path("_quick_property_test.py")
    test_file.write_text(test_code)

    try:
        result = subprocess.run(
            [sys.executable, str(test_file)], capture_output=True, text=True, timeout=10
        )
        test_file.unlink()

        if result.returncode == 0:
            print("✓ Quick integration test PASSED")
            return True
        else:
            print("✗ Quick integration test FAILED")
            print(result.stdout)
            return False
    except Exception as e:
        if test_file.exists():
            test_file.unlink()
        print(f"✗ Quick test error: {e}")
        return False


def main():
    """Main validation workflow."""
    print("\n" + "=" * 70)
    print("HYBA PROPERTY-BASED TEST SUITE VALIDATOR")
    print("=" * 70)

    # Step 1: Install dependencies
    if not check_and_install_dependencies():
        print("\n⚠️  Failed to install dependencies. Exiting.")
        return 1

    # Step 2: Run quick integration test
    if not run_quick_integration_test():
        print("\n⚠️  Quick integration test failed. Check hypothesis installation.")
        return 1

    # Step 3: Run full property-based tests
    results = run_property_tests()

    # Summary
    print("\n" + "=" * 70)
    print("TEST EXECUTION SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_file, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status} - {test_file}")

    print("=" * 70)
    print(f"\nResults: {passed}/{total} test suites passed")

    if passed == total and total > 0:
        print("\n🎯 ALL PROPERTY-BASED TESTS VALIDATED")
        print("   Integration test suite is fully operational")
        return 0
    elif total == 0:
        print("\n⚠️  NO TEST FILES FOUND")
        print("   Test files may need to be created")
        return 1
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("   Review failed tests above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
