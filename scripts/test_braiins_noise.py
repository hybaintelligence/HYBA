#!/usr/bin/env python3
"""Test Braiins pool connection with Noise protocol handshake."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pythia_mining.live_stratum_v2_session import (
    LiveStratumV2Session,
    LiveStratumV2SessionError,
)
from pythia_mining.pool_profiles import PoolProfile


async def test_braiins_noise_connection(
    pool_url: str,
    username: str,
    password: str,
    enable_noise: bool = True,
) -> dict:
    """Test Braiins pool connection with Noise protocol."""

    print("Testing Braiins pool connection with Noise protocol")
    print(f"Pool URL: {pool_url}")
    print(f"Username: {username}")
    print(f"Enable Noise: {enable_noise}")
    print("-" * 60)

    # Create pool profile
    profile = PoolProfile(
        pool_id="braiins-test",
        name="Braiins Test Pool",
        url=pool_url,
        username=username,
        password=password,
        stratum_version=2,
        max_reconnect_attempts=3,
        reconnect_backoff_base=1.0,
        reconnect_backoff_max=10.0,
    )

    test_stats = {
        "pool_url": pool_url,
        "username": username,
        "enable_noise": enable_noise,
        "noise_handshake_success": False,
        "setup_connection_success": False,
        "noise_handshake_result": None,
        "setup_connection_result": None,
        "error": None,
    }

    try:
        # Create session with noise protocol enabled
        session = LiveStratumV2Session(
            profile=profile,
            enable_noise=enable_noise,
        )

        print("Connecting to pool...")
        await session.connect()
        print("Connected successfully")

        if session.noise_handshake_result:
            print("Noise handshake completed successfully")
            print(f"  Encrypted: {session.noise_handshake_result.encrypted}")
            print(
                f"  Remote static public: {session.noise_handshake_result.remote_static_public.hex() if session.noise_handshake_result.remote_static_public else 'N/A'}"
            )
            test_stats["noise_handshake_success"] = True
            test_stats["noise_handshake_result"] = {
                "encrypted": session.noise_handshake_result.encrypted,
                "remote_static_public": (
                    session.noise_handshake_result.remote_static_public.hex()
                    if session.noise_handshake_result.remote_static_public
                    else None
                ),
            }
        else:
            print("No noise handshake performed (noise disabled)")

        print("\nPerforming SetupConnection handshake...")
        handshake = await session.setup_connection(timeout=30.0)

        print("SetupConnection completed successfully")
        print(f"  Used version: {handshake.used_version}")
        print(f"  Flags: {handshake.flags}")

        test_stats["setup_connection_success"] = True
        test_stats["setup_connection_result"] = {
            "used_version": handshake.used_version,
            "flags": handshake.flags,
            "setup": handshake.setup,
        }

        print("\n" + "=" * 60)
        print("TEST SUCCESSFUL")
        print("=" * 60)

    except LiveStratumV2SessionError as e:
        print(f"ERROR: {e}")
        test_stats["error"] = str(e)

    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        test_stats["error"] = str(e)
        import traceback

        traceback.print_exc()

    finally:
        try:
            await session.close()
            print("\nConnection closed")
        except Exception as e:
            print(f"Error closing connection: {e}")

    return test_stats


def main():
    """Main entry point for noise protocol test."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Test Braiins pool connection with Noise protocol"
    )
    parser.add_argument(
        "--pool-url", default="stratum2+tcp://stratum.braiins.com:3333", help="Pool URL"
    )
    parser.add_argument("--username", required=True, help="Mining pool username/worker")
    parser.add_argument("--password", default="x", help="Mining pool password")
    parser.add_argument(
        "--enable-noise",
        action="store_true",
        default=False,
        help="Enable Noise protocol",
    )
    parser.add_argument("--output", help="Output JSON file for test results")

    args = parser.parse_args()

    stats = asyncio.run(
        test_braiins_noise_connection(
            pool_url=args.pool_url,
            username=args.username,
            password=args.password,
            enable_noise=args.enable_noise,
        )
    )

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(stats, indent=2))
        print(f"\nTest results saved to {output_path}")

    # Return exit code based on success
    if stats["setup_connection_success"]:
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
