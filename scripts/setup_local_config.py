#!/usr/bin/env python3
"""
HYBA Local Configuration Setup CLI
Interactive script to set up local environment configuration for blockchain pool credentials.
Since blockchain is open book, these credentials are public routing information.
"""

import os
import sys
from pathlib import Path


def get_input(prompt, default=None, required=False, validator=None):
    """Helper function to get user input with optional default and validation"""
    if default:
        prompt = f"{prompt} [{default}]: "
    else:
        prompt = f"{prompt}: "

    while True:
        value = input(prompt).strip()

        if not value and default:
            value = default

        if not value and required:
            print("  ⚠️  This field is required.")
            continue

        if validator and value:
            try:
                if validator(value):
                    break
                else:
                    print("  ⚠️  Invalid input format. Please try again.")
                    continue
            except Exception as e:
                print(f"  ⚠️  Validation error: {e}")
                continue

        break

    return value


def validate_url(url):
    """Validate URL format"""
    if not url:
        return True
    import re

    url_pattern = re.compile(
        r"^(https?|stratum\+tcp|stratum2\+ssl)://[^:/]+(:\d+)?(/.*)?$"
    )
    return bool(url_pattern.match(url))


def validate_username(username):
    """Validate username format"""
    if not username:
        return True
    import re

    # Allow alphanumeric, dots, underscores, and hyphens
    return bool(re.match(r"^[a-zA-Z0-9._-]+$", username))


def generate_jwt_secret():
    """Generate a random JWT secret"""
    import secrets

    return secrets.token_urlsafe(32)


def generate_argon2_hash(password):
    """Generate argon2id hash for password"""
    try:
        from argon2 import PasswordHasher

        ph = PasswordHasher()
        return ph.hash(password)
    except ImportError:
        print("  ❌ Error: argon2-cffi not installed. Please install it first:")
        print("     pip install argon2-cffi")
        sys.exit(1)


def setup_pool_config():
    """Interactive pool configuration setup"""
    print("\n" + "=" * 60)
    print("BLOCKCHAIN POOL CREDENTIAL CONFIGURATION")
    print("=" * 60)
    print("Since blockchain is open book, these are public routing parameters")
    print("=" * 60 + "\n")

    config = {}

    # ViaBTC Configuration
    print("📡 ViaBTC Pool Configuration (Stratum V2)")
    config["HYBA_POOL_VIABTC_URL"] = get_input(
        "Stratum URL", "stratum2+ssl://btc.viabtc.com:443", validator=validate_url
    )
    config["HYBA_POOL_VIABTC_USERNAME"] = get_input(
        "Username", "PYTHIA.001", validator=validate_username
    )
    config["HYBA_POOL_VIABTC_PASSWORD"] = get_input("Password", "x")
    config["HYBA_POOL_VIABTC_STRATUM_VERSION"] = get_input("Stratum Version", "2")
    print()

    # NiceHash Configuration
    print("📡 NiceHash SHA256 Configuration (Stratum V2)")
    config["HYBA_POOL_NICEHASH_URL"] = get_input(
        "Stratum URL",
        "stratum2+ssl://sha256.eu.nicehash.com:33334",
        validator=validate_url,
    )
    config["HYBA_POOL_NICEHASH_USERNAME"] = get_input(
        "Username", "PYTHIA.001", validator=validate_username
    )
    config["HYBA_POOL_NICEHASH_PASSWORD"] = get_input("Password", "x")
    config["HYBA_POOL_NICEHASH_STRATUM_VERSION"] = get_input("Stratum Version", "2")
    print()

    # Braiins Configuration
    print("📡 Braiins Pool Configuration (Stratum V2)")
    config["HYBA_POOL_BRAIINS_URL"] = get_input(
        "Stratum URL", "stratum2+ssl://eu.braiins-pool.com:3336", validator=validate_url
    )
    config["HYBA_POOL_BRAIINS_USERNAME"] = get_input(
        "Username", "PYTHIA.001", validator=validate_username
    )
    config["HYBA_POOL_BRAIINS_PASSWORD"] = get_input("Password", "x")
    config["HYBA_POOL_BRAIINS_STRATUM_VERSION"] = get_input("Stratum Version", "2")
    print()

    # CKPool Configuration
    print("📡 Solo CKPool Configuration (Stratum V1)")
    config["HYBA_POOL_CKPOOL_URL"] = get_input(
        "Stratum URL", "stratum+tcp://solo.ckpool.org:3333", validator=validate_url
    )
    config["HYBA_POOL_CKPOOL_USERNAME"] = get_input(
        "Username", "PYTHIA.001", validator=validate_username
    )
    config["HYBA_POOL_CKPOOL_PASSWORD"] = get_input("Password", "x")
    config["HYBA_POOL_CKPOOL_STRATUM_VERSION"] = get_input("Stratum Version", "1")
    print()

    return config


def setup_basic_config():
    """Setup basic application configuration"""
    print("\n" + "=" * 60)
    print("BASIC APPLICATION CONFIGURATION")
    print("=" * 60 + "\n")

    config = {}

    # Runtime mode
    print("🔧 Runtime Configuration")
    mode = get_input("Environment mode (development/production)", "development")
    config["NODE_ENV"] = mode
    config["HYBA_ENV"] = mode
    config["HOST"] = "0.0.0.0"
    config["PORT"] = "3000"
    config["PULVINI_BACKEND_URL"] = "http://127.0.0.1:3001"
    print()

    # Auth configuration
    print("🔐 Authentication Configuration")
    use_default_jwt = (
        get_input("Use auto-generated JWT secret? (y/n)", "y").lower() == "y"
    )
    if use_default_jwt:
        config["JWT_SECRET"] = generate_jwt_secret()
        print("  ✓ Generated JWT secret")
    else:
        config["JWT_SECRET"] = get_input("JWT Secret", required=True)

    # Operator credentials
    use_default_operator = (
        get_input("Use default operator credentials? (y/n)", "y").lower() == "y"
    )
    if use_default_operator:
        operator_password = get_input("Operator password", "mining_operator")
        operator_hash = generate_argon2_hash(operator_password)
        config["HYBA_OPERATOR_CREDENTIALS"] = (
            f"operator:{operator_hash}:mining_operator"
        )
        print("  ✓ Generated operator credentials")
    else:
        config["HYBA_OPERATOR_CREDENTIALS"] = get_input(
            "Operator credentials", required=True
        )

    config["HYBA_API_KEYS"] = ""
    print()

    # Mining safety gates
    print("⚡ Mining Safety Gates")
    autoconnect = get_input("Enable mining autoconnect? (y/n)", "y").lower() == "y"
    config["HYBA_ENABLE_MINING_AUTOCONNECT"] = str(autoconnect).lower()

    live_stratum = get_input("Enable live Stratum? (y/n)", "n").lower() == "y"
    config["HYBA_ENABLE_LIVE_STRATUM"] = str(live_stratum).lower()

    config["HYBA_ENABLE_LIVE_SHARE_SUBMIT"] = "false"
    config["HYBA_LIVE_SHARE_APPROVAL_ID"] = ""
    config["HYBA_ALLOW_DEV_FIXTURES"] = "true" if mode == "development" else "false"
    config["HYBA_ENABLE_AUDIT_LOGGING"] = "true"
    config["HYBA_AUDIT_LOG_DIR"] = "logs/audit"
    config["HYBA_METRICS_DB_PATH"] = "data/metrics.db"
    config["HYBA_INTERNAL_HEALTH_TOKEN"] = ""
    print()

    return config


def check_gitignore(env_file):
    """Check if .env.local is in .gitignore"""
    gitignore_path = Path(__file__).parent.parent / ".gitignore"
    if not gitignore_path.exists():
        print("  ⚠️  Warning: .gitignore not found")
        return False

    with open(gitignore_path, "r") as f:
        gitignore_content = f.read()

    if ".env.local" in gitignore_content or ".env*" in gitignore_content:
        return True

    print("  ⚠️  Warning: .env.local is not in .gitignore")
    print("  Consider adding it to prevent accidental commits")
    return False


def write_env_file(config, filename):
    """Write configuration to .env file"""
    env_path = Path(filename)

    # Check if file already exists
    if env_path.exists():
        print(f"\n⚠️  File {filename} already exists.")
        overwrite = input("Overwrite existing configuration? (y/n): ").strip().lower()
        if overwrite != "y":
            print("  Configuration setup cancelled.")
            sys.exit(0)

    print(f"\n📝 Writing configuration to {filename}...")

    try:
        with open(env_path, "w") as f:
            f.write("# HYBA Local Configuration\n")
            f.write("# Generated by setup_local_config.py\n")
            f.write(
                "# Blockchain pool credentials are open book routing parameters\n\n"
            )

            for key, value in sorted(config.items()):
                f.write(f"{key}={value}\n")

        print(f"  ✓ Configuration written to {filename}")

        # Set file permissions
        os.chmod(env_path, 0o600)
        print("  ✓ File permissions: restricted to user (0600)")

        # Check .gitignore
        check_gitignore(filename)

    except IOError as e:
        print(f"  ❌ Error writing configuration file: {e}")
        sys.exit(1)


def main():
    """Main entry point"""
    print("\n" + "=" * 60)
    print("HYBA LOCAL CONFIGURATION SETUP")
    print("=" * 60)
    print("This script creates local environment configuration")
    print("for blockchain pool credentials and application settings.")
    print("=" * 60)

    # Get project root
    script_dir = Path(__file__).parent.parent
    os.chdir(script_dir)

    # Setup configurations
    basic_config = setup_basic_config()
    pool_config = setup_pool_config()

    # Merge configurations
    full_config = {**basic_config, **pool_config}

    # Write to .env.local
    env_file = script_dir / ".env.local"
    write_env_file(full_config, env_file)

    print("\n" + "=" * 60)
    print("✓ CONFIGURATION SETUP COMPLETE")
    print("=" * 60)
    print(f"Configuration file: {env_file}")
    print("\nSecurity reminders:")
    print("  • .env.local contains sensitive configuration")
    print("  • File permissions are set to 0600 (owner read/write only)")
    print("  • Never commit .env.local to version control")
    print("  • Use different credentials for production")
    print("\nYou can now run:")
    print("  ./setup_and_start.sh")
    print("\nOr manually start services:")
    print("  npm run dev")
    print("  npm run backend:start")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        sys.exit(1)
