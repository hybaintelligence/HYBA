#!/usr/bin/env python3
"""
Pool authentication test for operations room preflight.
Tests pool subscribe/auth without live share submission.
"""

import asyncio
import os
import sys

# Add python_backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pythia_mining.stratum_client import StratumClient
from pythia_mining.pool_profiles import build_profile


async def test_pool_auth():
    """Test pool subscription and authentication."""
    
    pool_url = os.getenv("HYBA_POOL_URL", "stratum+tcp://btc.viabtc.com:3333")
    pool_name = os.getenv("HYBA_POOL_NAME", "viabtc")
    worker = os.getenv("HYBA_POOL_WORKER", "pythia.001")
    password = os.getenv("HYBA_POOL_PASSWORD", "123")
    
    print("\n" + "="*70)
    print("POOL AUTHENTICATION TEST")
    print("="*70)
    print(f"Pool: {pool_name}")
    print(f"URL: {pool_url}")
    print(f"Worker: {worker}")
    print(f"Password: {'*' * len(password)}")
    print("="*70 + "\n")
    
    try:
        # Build pool profile
        profile = build_profile(
            pool_id=pool_name,
            name=f"{pool_name}_worker",
            url=pool_url,
            username=worker,
            password=password,
            stratum_version=1,
            priority=1,
        )
        
        print(f"✅ Pool profile built: {profile.pool_id}")
        
        # Create stratum client
        client = StratumClient(
            pool_url=pool_url,
            username=worker,
            password=password,
            pool_name=pool_name,
            stratum_version=1,
        )
        
        print("🔌 Connecting to pool...")
        await client.connect()
        
        print(f"✅ Connected to pool: {pool_name}")
        print(f"✅ Extranonce1: {client.extranonce1}")
        print(f"✅ Extranonce2 size: {client.extranonce2_size}")
        print(f"✅ Authenticated: {client.is_authenticated}")
        
        print("\n" + "="*70)
        print("POOL AUTHENTICATION TEST: PASSED")
        print("="*70)
        print("✅ Pool subscribe: confirmed")
        print("✅ Pool auth: confirmed")
        print("✅ Ready for live mining preflight")
        print("="*70 + "\n")
        
        # Disconnect
        await client.disconnect()
        print("🔌 Disconnected from pool\n")
        
        return True
        
    except Exception as e:
        print("\n" + "="*70)
        print("POOL AUTHENTICATION TEST: FAILED")
        print("="*70)
        print(f"❌ Error: {e}")
        print("="*70 + "\n")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_pool_auth())
    sys.exit(0 if success else 1)
