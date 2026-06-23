#!/usr/bin/env python3
"""
HYBA JWT CLI Tool
Generate and test JWT authentication tokens for the HYBA Genesis Platform.
"""

import argparse
import hashlib
import json
import os
import secrets
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add backend to path
BACKEND = Path(__file__).resolve().parents[1] / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

try:
    import jwt
except ImportError:
    print("Error: PyJWT is required. Install with: pip install PyJWT")
    sys.exit(1)


def generate_dev_secret():
    """Generate a cryptographically random dev secret (matches backend logic)."""
    raw = secrets.token_hex(32)
    return hashlib.sha256(raw.encode()).hexdigest()


def get_jwt_secret():
    """Get JWT secret from environment or generate dev secret."""
    secret = os.getenv("JWT_SECRET")
    if not secret:
        env = os.getenv("NODE_ENV", os.getenv("HYBA_ENV", "development")).lower()
        if env == "production":
            print("Error: JWT_SECRET environment variable is required in production")
            sys.exit(1)
        print(f"Warning: JWT_SECRET not set, using dev secret (env={env})")
        secret = generate_dev_secret()
    return secret


def create_token(
    user_id: str,
    username: str,
    roles: list,
    expiry_hours: int = 24,
    secret: str = None,
):
    """Create a JWT token."""
    if secret is None:
        secret = get_jwt_secret()

    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "username": username,
        "roles": roles,
        "exp": now + timedelta(hours=expiry_hours),
        "iat": now,
        "iss": "genesis.hyba.ai",
        "jti": secrets.token_hex(16),
    }

    token = jwt.encode(payload, secret, algorithm="HS256")
    return token, payload


def decode_token(token: str, secret: str = None):
    """Decode and verify a JWT token."""
    if secret is None:
        secret = get_jwt_secret()

    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        print("Error: Token has expired")
        sys.exit(1)
    except jwt.InvalidTokenError as e:
        print(f"Error: Invalid token - {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="HYBA JWT CLI Tool - Generate and test JWT authentication tokens"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generate token command
    gen_parser = subparsers.add_parser("generate", help="Generate a JWT token")
    gen_parser.add_argument(
        "--user-id", default="operator", help="User ID (default: operator)"
    )
    gen_parser.add_argument(
        "--username", default="operator", help="Username (default: operator)"
    )
    gen_parser.add_argument(
        "--roles",
        nargs="+",
        default=["ceo", "mining_operator"],
        help="Roles (default: ceo mining_operator)",
    )
    gen_parser.add_argument(
        "--expiry", type=int, default=24, help="Token expiry in hours (default: 24)"
    )
    gen_parser.add_argument(
        "--secret",
        help="JWT secret (uses JWT_SECRET env var or dev secret if not provided)",
    )
    gen_parser.add_argument(
        "--output",
        choices=["token", "json", "curl"],
        default="token",
        help="Output format (default: token)",
    )

    # Decode token command
    decode_parser = subparsers.add_parser(
        "decode", help="Decode and verify a JWT token"
    )
    decode_parser.add_argument("token", help="JWT token to decode")
    decode_parser.add_argument(
        "--secret",
        help="JWT secret (uses JWT_SECRET env var or dev secret if not provided)",
    )

    # Test authentication command
    test_parser = subparsers.add_parser(
        "test", help="Test authentication with API endpoints"
    )
    test_parser.add_argument(
        "--base-url", default="http://localhost:3001", help="API base URL"
    )
    test_parser.add_argument(
        "--secret",
        help="JWT secret (uses JWT_SECRET env var or dev secret if not provided)",
    )
    test_parser.add_argument(
        "--user-id", default="operator", help="User ID (default: operator)"
    )
    test_parser.add_argument(
        "--username", default="operator", help="Username (default: operator)"
    )
    test_parser.add_argument(
        "--roles",
        nargs="+",
        default=["ceo", "mining_operator"],
        help="Roles (default: ceo mining_operator)",
    )

    args = parser.parse_args()

    if args.command == "generate":
        secret = args.secret or get_jwt_secret()
        token, payload = create_token(
            user_id=args.user_id,
            username=args.username,
            roles=args.roles,
            expiry_hours=args.expiry,
            secret=secret,
        )

        if args.output == "token":
            print(token)
        elif args.output == "json":
            print(json.dumps({"token": token, "payload": payload}, indent=2))
        elif args.output == "curl":
            print(f'export HYBA_JWT_TOKEN="{token}"')
            print(
                '# Use with: curl -H "Authorization: Bearer $HYBA_JWT_TOKEN" http://localhost:3001/api/health'
            )

    elif args.command == "decode":
        secret = args.secret or get_jwt_secret()
        payload = decode_token(args.token, secret)
        print(json.dumps(payload, indent=2, default=str))

    elif args.command == "test":
        secret = args.secret or get_jwt_secret()
        token, payload = create_token(
            user_id=args.user_id,
            username=args.username,
            roles=args.roles,
            secret=secret,
        )

        print(f"Generated token for user: {args.username}")
        print(f"Roles: {', '.join(args.roles)}")
        print(f"\nToken: {token}")
        print("\n--- Testing Authentication ---\n")

        # Test health endpoint
        import subprocess

        try:
            result = subprocess.run(
                [
                    "curl",
                    "-s",
                    f"{args.base_url}/api/health",
                    "-H",
                    f"Authorization: Bearer {token}",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                print("✅ Health endpoint authenticated successfully")
                try:
                    data = json.loads(result.stdout)
                    print(json.dumps(data, indent=2))
                except json.JSONDecodeError:
                    print(result.stdout)
            else:
                print(f"❌ Health endpoint failed: {result.stderr}")
        except subprocess.TimeoutExpired:
            print("❌ Request timed out - API may not be running")
        except FileNotFoundError:
            print("❌ curl command not found")
        except Exception as e:
            print(f"❌ Error: {e}")

        print("\n--- Curl Command for Manual Testing ---\n")
        print(f"curl -s {args.base_url}/api/health \\")
        print(f'  -H "Authorization: Bearer {token}" \\')
        print("  | jq")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
