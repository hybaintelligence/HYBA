#!/usr/bin/env python3
"""
HYBA Live Mining Configuration CLI
Configures pools and JWT for live mining run without interactive prompts.
"""

import json
import os
import sys
import secrets
import argparse
from pathlib import Path
from typing import Dict


def generate_jwt_secret(length: int = 32) -> str:
    """Generate a secure JWT secret"""
    return secrets.token_urlsafe(length)


def update_env_file(env_file: Path, config: Dict[str, str]) -> None:
    """Update .env file with new configuration"""
    # Read existing config
    existing_config = {}
    if env_file.exists():
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    existing_config[key] = value

    # Merge with new config (new config takes precedence)
    existing_config.update(config)

    # Write back
    with open(env_file, "w") as f:
        f.write("# HYBA Local Configuration\n")
        f.write("# Auto-configured for live mining\n\n")

        for key, value in sorted(existing_config.items()):
            f.write(f"{key}={value}\n")

    os.chmod(env_file, 0o600)


def update_pool_config(
    config_file: Path,
    viabtc_username: str,
    viabtc_password: str,
    braiins_username: str,
    braiins_password: str,
    set_viabtc_default: bool = True,
) -> None:
    """Update mining pools configuration"""

    with open(config_file, "r") as f:
        config = json.load(f)

    # Update ViaBTC
    if "viabtc" in config["pools"]:
        config["pools"]["viabtc"]["username"] = viabtc_username
        config["pools"]["viabtc"]["password"] = viabtc_password
        config["pools"]["viabtc"]["enabled"] = True
        if set_viabtc_default:
            config["pools"]["viabtc"]["is_default"] = True

    # Update Braiins
    if "braiins" in config["pools"]:
        config["pools"]["braiins"]["username"] = braiins_username
        config["pools"]["braiins"]["password"] = braiins_password
        config["pools"]["braiins"]["enabled"] = True
        if not set_viabtc_default:
            config["pools"]["braiins"]["is_default"] = True

    # Write back
    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Configure HYBA for live mining with ViaBTC and Braiins pools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick setup with default values
  python3 scripts/configure_live_mining.py --quick

  # Setup with custom credentials
  python3 scripts/configure_live_mining.py \\
    --viabtc-user PYTHIA.001 \\
    --viabtc-pass your-password \\
    --braiins-user PYTHAGORAS \\
    --braiins-pass anything123 \\
    --generate-jwt

  # Enable live mining
  python3 scripts/configure_live_mining.py --enable-live
        """,
    )

    parser.add_argument("--quick", action="store_true", help="Quick setup with default values")

    parser.add_argument(
        "--viabtc-user", default="PYTHIA.001", help="ViaBTC username (default: PYTHIA.001)"
    )

    parser.add_argument("--viabtc-pass", default="123", help="ViaBTC password (default: 123)")

    parser.add_argument(
        "--braiins-user", default="PYTHAGORAS", help="Braiins username (default: PYTHAGORAS)"
    )

    parser.add_argument(
        "--braiins-pass", default="anything123", help="Braiins password (default: anything123)"
    )

    parser.add_argument(
        "--generate-jwt", action="store_true", help="Generate and set new JWT secret"
    )

    parser.add_argument("--jwt-secret", help="Use custom JWT secret (overrides --generate-jwt)")

    parser.add_argument(
        "--enable-live", action="store_true", help="Enable live Stratum I/O and share submission"
    )

    parser.add_argument(
        "--disable-live", action="store_true", help="Disable live Stratum I/O (for testing)"
    )

    parser.add_argument(
        "--default-pool",
        choices=["viabtc", "braiins"],
        default="viabtc",
        help="Set default pool (default: viabtc)",
    )

    parser.add_argument(
        "--session-duration",
        type=int,
        default=20,
        help="Mining session duration in minutes (default: 20)",
    )

    parser.add_argument(
        "--show-config", action="store_true", help="Show current configuration and exit"
    )

    args = parser.parse_args()

    # Project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    env_file = project_root / ".env.local"
    pool_config_file = project_root / "config/mining_pools_live.json"

    print("\n" + "=" * 70)
    print("HYBA LIVE MINING CONFIGURATION")
    print("=" * 70)

    # Show current config if requested
    if args.show_config:
        print("\n📋 Current Configuration:\n")
        if env_file.exists():
            print(f"  Environment file: {env_file}")
            with open(env_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        if "=" in line:
                            key, value = line.split("=", 1)
                            if "SECRET" in key or "PASSWORD" in key or "HASH" in key:
                                print(f"    {key}=[redacted]")
                            else:
                                print(f"    {key}={value}")

        if pool_config_file.exists():
            print(f"\n  Pool config: {pool_config_file}")
            with open(pool_config_file, "r") as f:
                config = json.load(f)
            for pool_id, pool in config.get("pools", {}).items():
                enabled = "✓" if pool.get("enabled") else "✗"
                is_default = " [DEFAULT]" if pool.get("is_default") else ""
                print(f"    {enabled} {pool.get('name', pool_id)}{is_default}")
                print(f"      URL: {pool.get('url')}")
                print(f"      User: {pool.get('username', '(none)')}")

        print("\n" + "=" * 70 + "\n")
        return 0

    # Prepare configuration
    env_config = {}

    # Handle JWT
    if args.jwt_secret:
        env_config["JWT_SECRET"] = args.jwt_secret
        print("✓ Using custom JWT secret")
    elif args.generate_jwt:
        jwt = generate_jwt_secret()
        env_config["JWT_SECRET"] = jwt
        print("✓ Generated new JWT secret")
    else:
        print("ℹ JWT secret: not modified (use --generate-jwt to create new)")

    # Handle live mining flags
    if args.enable_live:
        env_config["HYBA_ENABLE_LIVE_STRATUM"] = "true"
        env_config["HYBA_ENABLE_LIVE_SHARE_SUBMIT"] = "true"
        print("✓ Live Stratum I/O: ENABLED")
        print("✓ Live share submission: ENABLED")
    elif args.disable_live:
        env_config["HYBA_ENABLE_LIVE_STRATUM"] = "false"
        env_config["HYBA_ENABLE_LIVE_SHARE_SUBMIT"] = "false"
        print("✓ Live Stratum I/O: DISABLED")
        print("✓ Live share submission: DISABLED")

    # Set environment
    env_config["NODE_ENV"] = "development"
    env_config["HYBA_ENV"] = "development"
    env_config["HYBA_ALLOW_DEV_FIXTURES"] = "false"
    env_config["HYBA_ENABLE_AUDIT_LOGGING"] = "true"
    env_config["HYBA_POOL_CONFIG_PATH"] = "config/mining_pools_live.json"

    # Update .env.local
    print(f"\n📝 Writing environment configuration to {env_file}...")
    update_env_file(env_file, env_config)
    print("✓ Environment file updated")

    # Update pool configuration
    print("\n📡 Configuring pools...")
    update_pool_config(
        pool_config_file,
        viabtc_username=args.viabtc_user,
        viabtc_password=args.viabtc_pass,
        braiins_username=args.braiins_user,
        braiins_password=args.braiins_pass,
        set_viabtc_default=(args.default_pool == "viabtc"),
    )
    print(
        f"✓ ViaBTC: {args.viabtc_user} (default)"
        if args.default_pool == "viabtc"
        else f"✓ ViaBTC: {args.viabtc_user}"
    )
    print(
        f"✓ Braiins: {args.braiins_user}" + (" (default)" if args.default_pool == "braiins" else "")
    )

    # Print next steps
    print("\n" + "=" * 70)
    print("CONFIGURATION COMPLETE")
    print("=" * 70)
    print(f"\n⏱ Session duration: {args.session_duration} minutes\n")
    print("Next steps:\n")
    print("1. Start the backend (in one terminal):")
    print("   npm run backend:start\n")
    print("2. Start the frontend (in another terminal):")
    print("   npm run dev\n")
    print(f"3. Run the {args.session_duration}-minute live mining session:")
    print(f"   bash scripts/START_LIVE_MINING_{args.session_duration}MIN.sh\n")

    print("For verification:")
    print("   python3 scripts/configure_live_mining.py --show-config\n")

    print("=" * 70 + "\n")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Configuration cancelled by user\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        import traceback

        traceback.print_exc()
        sys.exit(1)
