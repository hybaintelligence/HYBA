#!/usr/bin/env python3
"""
HYBA Internal Mining Operations - CIaaS/QaaS Substrate Validation
Purpose: Validate φ-resonance mathematical primitives for commercial services
Status: Internal infrastructure only - not a commercial offering
"""
import sys
import os
import time
import requests
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python_backend"))

BASE_URL = "http://127.0.0.1:3001"
TOKEN = os.environ.get("HYBA_OPERATOR_JWT", "")

headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}


def print_banner():
    print("=" * 80)
    print("HYBA CIAAS/QAAS INTERNAL MINING OPERATIONS")
    print("=" * 80)
    print()
    print(
        "COMMERCIAL OFFERING: Quantum-as-a-Service (QaaS) & Computational Intelligence"
    )
    print("MINING ROLE:         Internal substrate validation only")
    print()
    print("Mathematical Stack:")
    print("  - φ-resonance primitives (golden ratio computational structures)")
    print("  - PULVINI memory compression (2.0x lossless boundary)")
    print("  - HENDRIX-Φ solver (structured nonce traversal)")
    print("  - IIT 4.0 Φ computation (coherence diagnostics)")
    print("  - Yang-Mills mass gap (anti-simulation shield)")
    print()
    print("Pool: ViaBTC (PYTHIA.001)")
    print("Purpose: Validate mathematical substrate for CIaaS/QaaS customers")
    print("=" * 80)
    print()


def check_backend():
    print("[1/6] Checking backend availability...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("  ✓ Backend is running")
            return True
        else:
            print(f"  ✗ Backend returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"  ✗ Backend not accessible: {e}")
        print("  → Start backend with: python python_backend/hyba_genesis_api/main.py")
        return False


def configure_viabtc_pool():
    print("\n[2/6] Configuring ViaBTC pool...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/mining/pool-config", headers=headers, timeout=5
        )
        pools = response.json().get("pools", [])
        viabtc = next((p for p in pools if p["pool_id"] == "viabtc"), None)

        if viabtc and viabtc.get("configured"):
            print(f"  ✓ ViaBTC pool already configured")
            print(f"    Username: {viabtc.get('username', 'N/A')}")
            print(f"    Worker: {viabtc.get('worker', 'N/A')}")
            return True
        else:
            print("  → Pool not configured, configuring now...")
            config_data = {
                "pool_id": "viabtc",
                "username": "PYTHIA.001",
                "password": "123",
                "worker": "hendrix_phi",
                "enabled": True,
                "priority": 1,
            }
            response = requests.post(
                f"{BASE_URL}/api/mining/pool-config",
                json=config_data,
                headers=headers,
                timeout=5,
            )
            if response.status_code in [200, 201]:
                print("  ✓ ViaBTC pool configured successfully")
                return True
            else:
                print(f"  ✗ Configuration failed: {response.status_code}")
                print(f"    {response.text}")
                return False
    except Exception as e:
        print(f"  ✗ Configuration error: {e}")
        return False


def connect_to_pool():
    print("\n[3/6] Connecting to ViaBTC pool...")
    try:
        connect_data = {"pool_id": "viabtc", "capacity_ehs": 1.0, "switch": True}
        response = requests.post(
            f"{BASE_URL}/api/mining/connect",
            json=connect_data,
            headers=headers,
            timeout=10,
        )
        result = response.json()

        if response.status_code == 200 and result.get("status") == "connected":
            print(f"  ✓ Connected to {result.get('pool', 'ViaBTC')}")
            print(f"    Worker: {result.get('worker', 'N/A')}")
            print(f"    Capacity: {result.get('capacity_ehs', 0)} EH/s")
            print(
                f"    Cap: {result.get('hashrate_cap_ehs', 0)} EH/s (PULVINI boundary)"
            )
            return True
        else:
            print(f"  ✗ Connection failed: {result.get('status', 'unknown')}")
            return False
    except Exception as e:
        print(f"  ✗ Connection error: {e}")
        return False


def start_mining_daemon():
    print("\n[4/6] Starting mining daemon...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/mining/start", headers=headers, timeout=15
        )
        # Daemon start may timeout as it runs in background
        if response.status_code in [200, 202]:
            result = response.json()
            print(f"  ✓ Mining daemon started")
            print(f"    PID: {result.get('pid', 'N/A')}")
            return True
        else:
            print(f"  → Daemon starting (async)...")
            return True
    except requests.exceptions.Timeout:
        print(f"  → Daemon starting (background process)...")
        return True
    except Exception as e:
        print(f"  ✗ Daemon start error: {e}")
        return False


def verify_mining_status():
    print("\n[5/6] Verifying mining status...")
    time.sleep(3)  # Give daemon time to initialize

    try:
        response = requests.get(
            f"{BASE_URL}/api/mining/status", headers=headers, timeout=5
        )
        result = response.json()

        status = result.get("status", "unknown")
        daemon = result.get("daemon_running", False)
        connection = result.get("connection", {})

        print(f"  Status: {status}")
        print(f"  Daemon: {'running' if daemon else 'not running'}")
        print(f"  Pool: {connection.get('pool_id', 'none')}")
        print(f"  Hashrate: {result.get('hashrate_ehs', 0)} EH/s")

        if status == "running" and daemon:
            print("  ✓ Mining operational")
            return True
        else:
            print("  ⚠ Mining not fully operational yet")
            return False
    except Exception as e:
        print(f"  ✗ Status check error: {e}")
        return False


def show_operational_summary():
    print("\n[6/6] Operational Summary")
    print("-" * 80)

    try:
        # Get pool metrics
        response = requests.get(
            f"{BASE_URL}/api/mining/pools", headers=headers, timeout=5
        )
        result = response.json()
        summary = result.get("summary", {})

        print(f"Active Pool:      {summary.get('active_pool_name', 'none')}")
        print(f"Total Hashrate:   {summary.get('total_hashrate', 0)} EH/s")
        print(f"Hashrate Cap:     {summary.get('hashrate_cap_ehs', 0)} EH/s (PULVINI)")
        print(f"Shares (24h):     {summary.get('total_shares_24h', 0)}")
        print(f"Acceptance Rate:  {summary.get('global_acceptance_rate', 0)*100:.1f}%")
        print(f"Daemon Running:   {summary.get('daemon_running', False)}")
        print(f"MIDAS State:      {summary.get('midas_state', 'unknown')}")

        print()
        print("Purpose:")
        print(
            "  This mining infrastructure validates φ-resonance mathematical primitives"
        )
        print("  that power HYBA's commercial CIaaS/QaaS offerings.")
        print()
        print("Commercial Services:")
        print("  - Quantum-as-a-Service (QaaS): Fault-tolerant quantum compute")
        print("  - Computational Intelligence (CIaaS): Optimization & solver services")
        print()
        print("Mining is internal validation only, not a customer-facing product.")

    except Exception as e:
        print(f"Error fetching summary: {e}")

    print("-" * 80)


def main():
    print_banner()

    # Run operational sequence
    steps = [
        check_backend,
        configure_viabtc_pool,
        connect_to_pool,
        start_mining_daemon,
        verify_mining_status,
        show_operational_summary,
    ]

    for step in steps:
        if not step():
            print(f"\n⚠ Step failed: {step.__name__}")
            print("Continuing with remaining steps...\n")

    print("\n" + "=" * 80)
    print("MINING OPERATIONS INITIALIZED")
    print("=" * 80)
    print()
    print("Monitor logs:")
    print("  - Backend: check terminal running hyba_genesis_api")
    print("  - Audit: logs/audit/audit_*.log")
    print()
    print("API Endpoints:")
    print(f"  - Status: {BASE_URL}/api/mining/status")
    print(f"  - Pools:  {BASE_URL}/api/mining/pools")
    print(f"  - Stats:  {BASE_URL}/api/mining/stats")
    print()
    print("Next: Monitor share submissions for φ-resonance validation")
    print()


if __name__ == "__main__":
    main()
