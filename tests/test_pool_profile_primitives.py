import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from pythia_mining.pool_profiles import (
    PoolProfileError,
    build_profile,
    order_profiles,
    validate_pool_url,
)
from pythia_mining.stratum_transport import parse_endpoint


class PoolProfilePrimitiveTests(unittest.TestCase):
    def test_profile_validation_ordering_and_redaction(self):
        a = build_profile(
            "alpha",
            name="Alpha",
            url="stratum+ssl://example.com:3333",
            username="u",
            password="p",
            priority=2,
        )
        b = build_profile(
            "beta",
            name="Beta",
            url="stratum+tcp://example.net:3333",
            username="u",
            password="p",
            priority=1,
        )
        self.assertEqual(
            ["beta", "alpha"], [item.pool_id for item in order_profiles([a, b])]
        )
        self.assertEqual("<configured>", a.to_dict()["password"])
        self.assertEqual("<configured>", a.to_dict()["username"])

    def test_rejects_invalid_profile_values(self):
        with self.assertRaises(PoolProfileError):
            validate_pool_url("https://example.com")
        with self.assertRaises(PoolProfileError):
            build_profile(
                "bad",
                name="Bad",
                url="stratum+tcp://example.com:3333",
                username="",
                password="p",
            )

    def test_transport_endpoint_parsing(self):
        endpoint = parse_endpoint("stratum+ssl://example.com:4444")
        self.assertEqual("example.com", endpoint.host)
        self.assertEqual(4444, endpoint.port)
        self.assertTrue(endpoint.use_tls)


if __name__ == "__main__":
    unittest.main()
