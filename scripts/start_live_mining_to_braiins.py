#!/usr/bin/env python3
"""Start live mining to Braiins pool."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python_backend"))

# Connect to pool and start mining
import requests
import json
import time

BASE_URL = "http://127.0.0.1:3001"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJvcGVyYXRvci1saXZlLXRlc3QiLCJyb2xlIjoibWluaW5nOm9wZXJhdGUiLCJpYXQiOjE3ODE2MjQzMzksImV4cCI6MTc4MTYyNzkzOX0.MxRnXcFGDR6IyvyZqQMYQaP65_nbaqL-I-pX4V0_Su8"

headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

print("=" * 60)
print("STARTING LIVE MINING TO BRAIINS")
print("=" * 60)

# Step 1: Connect to Braiins pool
print("\n1. Connecting to Braiins pool...")
connect_data = {"pool_id": "braiins", "capacity_ehs": 1.0, "switch": True}

try:
    response = requests.post(
        f"{BASE_URL}/api/mining/connect", json=connect_data, headers=headers, timeout=5
    )
    print(f"   Status: {response.status_code}")
    result = response.json()
    print(f"   Pool: {result.get('pool', 'unknown')}")
    print(f"   Status: {result.get('status', 'unknown')}")
except Exception as e:
    print(f"   Error: {e}")
    sys.exit(1)

# Step 2: Start mining daemon
print("\n2. Starting mining daemon...")
try:
    response = requests.post(f"{BASE_URL}/api/mining/start", headers=headers, timeout=10)
    print(f"   Status: {response.status_code}")
    result = response.json()
    print(f"   Result: {json.dumps(result, indent=2)}")
except requests.exceptions.Timeout:
    print("   [Mining daemon start in progress...]")
except Exception as e:
    print(f"   Error: {e}")

# Step 3: Check mining status
print("\n3. Checking mining status...")
time.sleep(2)
try:
    response = requests.get(f"{BASE_URL}/api/mining/status", headers=headers, timeout=5)
    print(f"   Status: {response.status_code}")
    result = response.json()
    print(f"   Mining: {result.get('status', 'unknown')}")
    print(f"   Daemon: {result.get('daemon_running', False)}")
except Exception as e:
    print(f"   Error: {e}")

# Step 4: Get pool metrics
print("\n4. Checking pool metrics...")
try:
    response = requests.get(f"{BASE_URL}/api/mining/pools", headers=headers, timeout=5)
    print(f"   Status: {response.status_code}")
    result = response.json()
    summary = result.get("summary", {})
    print(f"   Active pool: {summary.get('active_pool_name')}")
    print(f"   Total shares (24h): {summary.get('total_shares_24h', 0)}")
    print(f"   Global acceptance rate: {summary.get('global_acceptance_rate', 0) * 100:.1f}%")
except Exception as e:
    print(f"   Error: {e}")

print("\n" + "=" * 60)
print("MINING SESSION INITIATED")
print("=" * 60)
print("\nMonitor audit logs in: logs/audit/audit_20260616.log")
print("Look for: share_submission -> share_accepted (pool: Braiins)")
