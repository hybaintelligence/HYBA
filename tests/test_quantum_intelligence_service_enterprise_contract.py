"""Enterprise contract tests for the HYBA Quantum Intelligence API surface.

These tests intentionally validate the API source contract without importing the
full FastAPI application. That keeps the guard fast and prevents unrelated
runtime integrations from masking QIaaS product-boundary regressions.

ARCHIVED: QIaaS service removed per falsifiability policy (2026-06-21).
See .kiro/steering/falsifiability_requirements.md for details.
"""

import pytest

pytestmark = pytest.mark.skip(reason="QIaaS service removed - see FINAL_FIX_VERIFICATION.txt")
