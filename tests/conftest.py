"""Pytest configuration and async-test compatibility hooks."""

from __future__ import annotations

import asyncio
import inspect
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

# Pin BLAS to single-threaded for deterministic floating-point results
# This prevents threaded BLAS non-associativity from causing test flakiness
# in numerically-sensitive determinism tests (e.g., quantum healing)
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")


def pytest_pyfunc_call(pyfuncitem):
    """Run async test functions without requiring pytest-asyncio in minimal envs."""
    testfunction = pyfuncitem.obj
    if inspect.iscoroutinefunction(testfunction):
        kwargs = {
            name: pyfuncitem.funcargs[name] for name in pyfuncitem._fixtureinfo.argnames
        }
        asyncio.run(testfunction(**kwargs))
        return True
    return None
