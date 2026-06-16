from __future__ import annotations

import json
import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from pythia_mining.stratum_protocol import (  # noqa: E402
    StratumProtocolError,
    build_authorize,
    build_submit,
    build_subscribe,
    dumps_message,
    parse_authorize_result,
    parse_json_line,
    parse_notify_params,
    parse_server_message,
    parse_set_difficulty,
    parse_set_extranonce,
    parse_set_version_mask,
    parse_subscribe_result,
)
from pythia_mining.stratum_transport import (  # noqa: E402
    StratumLineTransport,
    StratumTransportError,
    parse_endpoint,
)


class GoLiveStratumPropertyTests(unittest.TestCase):
    """Final deterministic property/unit/integration/E2E tests for go-live protocol safety."""

    def test_property_build_submit_preserves_lowercase_hex_fields(self) -> None:
        rng = random.Random(1300)
        alphabet = "0123456789ABCDEFabcdef"
        for _ in range(250):
            extranonce2 = "".join(rng.choice(alphabet) for _ in range(8))
            ntime = "".join(rng.choice(alphabet) for _ in range(8))
            nonce = "".join(rng.choice(alphabet) for _ in range(8))
            payload = json.loads(build_submit(1, "worker", "job", extranonce2, ntime, nonce))
            self.assertEqual("mining.submit", payload["method"])
            self.assertEqual(
                ["worker", "job", extranonce2.lower(), ntime.lower(), nonce.lower()],
                payload["params"],
            )

    def test_property_parse_notify_round_trips_arbitrary_valid_merkle_branches(
        self,
    ) -> None:
        rng = random.Random(20260614)
        for branch_len in range(33):
            branch = [f"{rng.getrandbits(256):064x}" for _ in range(branch_len)]
            params = [
                "job",
                "00" * 32,
                "01",
                "02",
                branch,
                "20000000",
                "1d00ffff",
                "65aa00ff",
                bool(branch_len % 2),
            ]
            message = parse_notify_params(params)
            self.assertEqual(branch, message.merkle_branch)
            self.assertEqual(bool(branch_len % 2), message.clean_jobs)
            self.assertEqual(params[0], message.to_dict()["job_id"])

    def test_unit_rejects_all_malformed_stratum_boundaries(self) -> None:
        invalid_calls = [
            lambda: dumps_message(0, "mining.subscribe", []),
            lambda: dumps_message(1, "", []),
            lambda: build_authorize(1, "", "x"),
            lambda: build_authorize(1, "worker", None),
            lambda: build_submit(1, "worker", "job", "abc", "65aa00ff", "00000000"),
            lambda: build_submit(1, "worker", "job", "zz", "65aa00ff", "00000000"),
            lambda: build_submit(1, "", "job", "00", "65aa00ff", "00000000"),
            lambda: parse_json_line("[1, 2, 3]"),
            lambda: parse_json_line("{"),
            lambda: parse_subscribe_result({"error": "boom"}),
            lambda: parse_subscribe_result({"result": []}),
            lambda: parse_subscribe_result({"result": [[], "0a", 0]}),
            lambda: parse_set_difficulty([]),
            lambda: parse_set_difficulty([0]),
            lambda: parse_set_extranonce(["00"]),
            lambda: parse_set_extranonce(["00", 33]),
            lambda: parse_set_version_mask([]),
            lambda: parse_server_message('{"params":[]}'),
            lambda: parse_endpoint("http://example.com:3333"),
            lambda: parse_endpoint("stratum+tcp:///missing-host"),
        ]
        for call in invalid_calls:
            with self.assertRaises((StratumProtocolError, StratumTransportError)):
                call()

    def test_integration_server_message_dispatches_supported_and_future_messages(
        self,
    ) -> None:
        cases = [
            (
                {"method": "mining.set_difficulty", "params": [4]},
                "mining.set_difficulty",
                4.0,
            ),
            (
                {"method": "mining.set_extranonce", "params": ["0a0b", 4]},
                "mining.set_extranonce",
                4,
            ),
            (
                {"method": "mining.set_version_mask", "params": ["1fffe000"]},
                "mining.set_version_mask",
                "1fffe000",
            ),
            (
                {"method": "client.show_message", "params": ["ready"]},
                "unknown",
                "client.show_message",
            ),
            ({"id": 7, "result": True, "error": None}, "response", True),
        ]
        for wire, expected_kind, expected_value in cases:
            kind, payload = parse_server_message(json.dumps(wire))
            self.assertEqual(expected_kind, kind)
            if kind == "mining.set_difficulty":
                self.assertEqual(expected_value, payload.difficulty)
            elif kind == "mining.set_extranonce":
                self.assertEqual(expected_value, payload.extranonce2_size)
            elif kind == "mining.set_version_mask":
                self.assertEqual(expected_value, payload.version_mask)
            elif kind == "unknown":
                self.assertEqual(expected_value, payload["method"])
            else:
                self.assertEqual(expected_value, payload["result"])

    def test_e2e_subscribe_authorize_notify_submit_flow_without_network(self) -> None:
        subscribe = json.loads(build_subscribe(1, "hyba-go-live/1300"))
        self.assertEqual(["hyba-go-live/1300"], subscribe["params"])
        sub = parse_subscribe_result({"id": 1, "result": [[], "0a0b", 4], "error": None})
        self.assertEqual("0a0b", sub.extranonce1)
        self.assertTrue(parse_authorize_result({"id": 2, "result": True, "error": None}))
        kind, notify = parse_server_message(
            json.dumps(
                {
                    "method": "mining.notify",
                    "params": [
                        "job",
                        "00" * 32,
                        "01",
                        "02",
                        [],
                        "20",
                        "1d00ffff",
                        "65aa00ff",
                        True,
                    ],
                }
            )
        )
        self.assertEqual("mining.notify", kind)
        submit = json.loads(
            build_submit(3, "worker", notify.job_id, "00000001", notify.ntime, "00000002")
        )
        self.assertEqual(["worker", "job", "00000001", "65aa00ff", "00000002"], submit["params"])
        endpoint = parse_endpoint("stratum+tls://pool.example.com:3334")
        transport = StratumLineTransport(
            "stratum+tls://pool.example.com:3334", connect_timeout=1, read_timeout=1
        )
        self.assertTrue(endpoint.use_tls)
        self.assertFalse(transport.connected)


if __name__ == "__main__":
    unittest.main()
