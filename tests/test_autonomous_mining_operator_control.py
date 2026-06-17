"""Tests for autonomous mining operator control hardening."""

from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
PYTHON_BACKEND = ROOT / "python_backend"
if str(PYTHON_BACKEND) not in sys.path:
    sys.path.insert(0, str(PYTHON_BACKEND))

from scripts.autonomous_mining_operator_control import OperatorControlInterface  # noqa: E402


class TestAutonomousMiningOperatorControl(unittest.TestCase):
    def test_reset_circuit_flags_repeated_reset_within_cooldown(self) -> None:
        engine = MagicMock()
        controller = MagicMock()
        controller._consecutive_failures = 4
        controller.reset_circuit_breaker = MagicMock(
            return_value={
                "before_state": {"consecutive_failures": 4, "circuit_open": True},
                "after_state": {"consecutive_failures": 0, "circuit_open": False},
            }
        )
        engine.autonomous_controller = controller

        with tempfile.TemporaryDirectory() as tmp:
            interface = OperatorControlInterface(engine)
            interface.audit_log_path = Path(tmp) / "operator_audit.log"
            first = interface.reset_autonomous_circuit(
                operator_id="ops-1",
                operator_reason="incident reset",
                cooldown_seconds=300.0,
            )
            controller._consecutive_failures = 3
            second = interface.reset_autonomous_circuit(
                operator_id="ops-1",
                operator_reason="second incident reset",
                cooldown_seconds=300.0,
            )

        self.assertTrue(first["success"])
        self.assertFalse(first["manual_reset_within_cooldown"])
        self.assertTrue(second["manual_reset_within_cooldown"])
        self.assertEqual(controller.reset_circuit_breaker.call_count, 2)
        self.assertEqual(second["before_state"]["consecutive_failures"], 4)


if __name__ == "__main__":
    unittest.main()
