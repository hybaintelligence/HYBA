#!/usr/bin/env python3
"""
HYBA Local Configuration Setup CLI
Interactive script to set up local environment configuration for blockchain pool credentials.
Since blockchain is open book, these credentials are public routing information.
"""

import os
import sys
from pathlib import Path

def get_input(prompt, default=None, required=False):
    """Helper function to get user input with optional default"""
    if default:
        prompt = f"{prompt} [{default}]: "
    else:
        prompt = f"{prompt}: "
    
    value = input(prompt).strip()
    
    if not value and default:
        return default
    if not value and required:
        print(f"  ⚠️  This field is required. Using default: {default}")
        return default
    return value

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
        print("  ⚠️  argon2-cffi not installed, using placeholder hash")
        return "$argon2id$v=19$m=65536,t=3,p=4$placeholder$hash"

def setup_pool_config():
    """Interactive pool configuration setup"""
    print("\n" + "="*60)
    print("BLOCKCHAIN POOL CREDENTIAL CONFIGURATION")
    print("="*60)
    print("Since blockchain is open book, these are public routing parameters")
    print("="*60 + "\n")
    
    config = {}
    
    # ViaBTC Configuration
    print("📡 ViaBTC Pool Configuration (Stratum V2)")
    config['HYBA_POOL_VIABTC_URL'] = get_input(
        "Stratum URL", 
        "stratum2+ssl://btc.viabtc.com:443"
    )
    config['HYBA_POOL_VIABTC_USERNAME'] = get_input(
        "Username", 
        "PYTHIA.001"
    )
    config['HYBA_POOL_VIABTC_PASSWORD'] = get_input(
        "Password", 
        "x"
    )
    config['HYBA_POOL_VIABTC_STRATUM_VERSION'] = get_input(
        "Stratum Version", 
        "2"
    )
    print()
    
    # NiceHash Configuration
    print("📡 NiceHash SHA256 Configuration (Stratum V2)")
    config['HYBA_POOL_NICEHASH_URL'] = get_input(
        "Stratum URL", 
        "stratum2+ssl://sha256.eu.nicehash.com:33334"
    )
    config['HYBA_POOL_NICEHASH_USERNAME'] = get_input(
        "Username", 
        "PYTHIA.001"
    )
    config['HYBA_POOL_NICEHASH_PASSWORD'] = get_input(
        "Password", 
        "x"
    )
    config['HYBA_POOL_NICEHASH_STRATUM_VERSION'] = get_input(
        "Stratum Version", 
        "2"
    )
    print()
    
    # Braiins Configuration
    print("📡 Braiins Pool Configuration (Stratum V2)")
    config['HYBA_POOL_BRAIINS_URL'] = get_input(
        "Stratum URL", 
        "stratum2+ssl://eu.braiins-pool.com:3336"
    )
    config['HYBA_POOL_BRAIINS_USERNAME'] = get_input(
        "Username", 
        "PYTHIA.001"
    )
    config['HYBA_POOL_BRAIINS_PASSWORD'] = get_input(
        "Password", 
        "x"
    )
    config['HYBA_POOL_BRAIINS_STRATUM_VERSION'] = get_input(
        "Stratum Version", 
        "2"
    )
    print()
    
    # CKPool Configuration
    print("📡 Solo CKPool Configuration (Stratum V1)")
    config['HYBA_POOL_CKPOOL_URL'] = get_input(
        "Stratum URL", 
        "stratum+tcp://solo.ckpool.org:3333"
    )
    config['HYBA_POOL_CKPOOL_USERNAME'] = get_input(
        "Username", 
        "PYTHIA.001"
    )
    config['HYBA_POOL_CKPOOL_PASSWORD'] = get_input(
        "Password", 
        "x"
    )
    config['HYBA_POOL_CKPOOL_STRATUM_VERSION'] = get_input(
        "Stratum Version", 
        "1"
    )
    print()
    
    return config

def setup_basic_config():
    """Setup basic application configuration"""
    print("\n" + "="*60)
    print("BASIC APPLICATION CONFIGURATION")
    print("="*60 + "\n")
    
    config = {}
    
    # Runtime mode
    print("🔧 Runtime Configuration")
    mode = get_input("Environment mode (development/production)", "development")
    config['NODE_ENV'] = mode
    config['HYBA_ENV'] = mode
    config['HOST'] = "0.0.0.0"
    config['PORT'] = "3000"
    config['PULVINI_BACKEND_URL'] = "http://127.0.0.1:3001"
    print()
    
    # Auth configuration
    print("🔐 Authentication Configuration")
    use_default_jwt = get_input("Use auto-generated JWT secret? (y/n)", "y").lower() == 'y'
    if use_default_jwt:
        config['JWT_SECRET'] = generate_jwt_secret()
        print(f"  ✓ Generated JWT secret")
    else:
        config['JWT_SECRET'] = get_input("JWT Secret", required=True)
    
    # Operator credentials
    use_default_operator = get_input("Use default operator credentials? (y/n)", "y").lower() == 'y'
    if use_default_operator:
        operator_password = get_input("Operator password", "mining_operator")
        operator_hash = generate_argon2_hash(operator_password)
        config['HYBA_OPERATOR_CREDENTIALS'] = f"operator:{operator_hash}:mining_operator"
        print(f"  ✓ Generated operator credentials")
    else:
        config['HYBA_OPERATOR_CREDENTIALS'] = get_input("Operator credentials", required=True)
    
    config['HYBA_API_KEYS'] = ""
    print()
    
    # Mining safety gates
    print("⚡ Mining Safety Gates")
    autoconnect = get_input("Enable mining autoconnect? (y/n)", "y").lower() == 'y'
    config['HYBA_ENABLE_MINING_AUTOCONNECT'] = str(autoconnect).lower()
    
    live_stratum = get_input("Enable live Stratum? (y/n)", "n").lower() == 'y'
    config['HYBA_ENABLE_LIVE_STRATUM'] = str(live_stratum).lower()
    
    config['HYBA_ENABLE_LIVE_SHARE_SUBMIT'] = "false"
    config['HYBA_LIVE_SHARE_APPROVAL_ID'] = ""
    config['HYBA_ALLOW_DEV_FIXTURES'] = "true" if mode == "development" else "false"
    config['HYBA_ENABLE_AUDIT_LOGGING'] = "true"
    config['HYBA_AUDIT_LOG_DIR'] = "logs/audit"
    config['HYBA_METRICS_DB_PATH'] = "data/metrics.db"
    config['HYBA_INTERNAL_HEALTH_TOKEN'] = ""
    print()
    
    return config

def write_env_file(config, filename):
    """Write configuration to .env file"""
    env_path = Path(filename)
    
    print(f"\n📝 Writing configuration to {filename}...")
    
    with open(env_path, 'w') as f:
        f.write("# HYBA Local Configuration\n")
        f.write("# Generated by setup_local_config.py\n")
        f.write("# Blockchain pool credentials are open book routing parameters\n\n")
        
        for key, value in sorted(config.items()):
            f.write(f"{key}={value}\n")
    
    print(f"  ✓ Configuration written to {filename}")
    print(f"  ✓ File permissions: restricted to user")

def main():
    """Main entry point"""
    print("\n" + "="*60)
    print("HYBA LOCAL CONFIGURATION SETUP")
    print("="*60)
    print("This script creates local environment configuration")
    print("for blockchain pool credentials and application settings.")
    print("="*60)
    
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
    
    # Set file permissions
    os.chmod(env_file, 0o600)
    
    print("\n" + "="*60)
    print("✓ CONFIGURATION SETUP COMPLETE")
    print("="*60)
    print(f"Configuration file: {env_file}")
    print("\nYou can now run:")
    print("  ./setup_and_start.sh")
    print("\nOr manually start services:")
    print("  npm run dev")
    print("  npm run backend:start")
    print("="*60 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        sys.exit(1)
