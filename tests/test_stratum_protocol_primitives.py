import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from pythia_mining.stratum_protocol import (
    StratumProtocolError,
    build_authorize,
    build_submit,
    build_subscribe,
    parse_authorize_result,
    parse_notify_params,
    parse_set_difficulty,
    parse_subscribe_result,
)


class StratumProtocolPrimitiveTests(unittest.TestCase):
    def test_build_messages(self):
        self.assertEqual("mining.subscribe", json.loads(build_subscribe(1))["method"])
        self.assertEqual("mining.authorize", json.loads(build_authorize(2, "w", "x"))["method"])
        self.assertEqual("mining.submit", json.loads(build_submit(3, "w", "j", "0001", "65aa00ff", "00000002"))["method"])

    def test_parse_results(self):
        sub = parse_subscribe_result({"id": 1, "result": [[], "0a0b", 4], "error": None})
        self.assertEqual("0a0b", sub.extranonce1)
        self.assertEqual(4, sub.extranonce2_size)
        self.assertTrue(parse_authorize_result({"id": 2, "result": True, "error": None}))

    def test_parse_notify_and_difficulty(self):
        notify = parse_notify_params(["j", "00" * 32, "01", "02", [], "20", "1d00ffff", "65aa00ff", True])
        self.assertEqual("j", notify.job_id)
        self.assertTrue(notify.clean_jobs)
        self.assertEqual(2.0, parse_set_difficulty([2.0]).difficulty)

    def test_rejects_bad_inputs(self):
        with self.assertRaises(StratumProtocolError):
            build_submit(1, "w", "j", "zz", "65aa00ff", "00000002")
        with self.assertRaises(StratumProtocolError):
            parse_set_difficulty([0])
        with self.assertRaises(StratumProtocolError):
            parse_notify_params(["short"])


if __name__ == "__main__":
    unittest.main()
