"""Start a 5-minute Braiins mining session and capture evidence."""
import requests
import json
import time
import sys
from datetime import datetime, timezone

BASE = "http://127.0.0.1:3001"
BRIDGE = "http://127.0.0.1:3000"

def log(msg):
    print(f"[{datetime.now(timezone.utc).isoformat()}] {msg}", flush=True)

# 1. Login
log("Logging in as operator...")
r = requests.post(f"{BASE}/api/auth/login", json={"username": "operator", "password": "operator123"})
r.raise_for_status()
token = r.json()["token"]
log(f"Token obtained: {token[:20]}...")

headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# 2. Configure Braiins pool
log("Configuring Braiins pool...")
r = requests.post(f"{BASE}/api/mining/pool-config", 
    json={"pool_id": "braiins", "url": "stratum2+tcp://stratum.braiins.com:3333/9awtMD5KQgvRUh2yFbjVeT7b6hjipWcAsQHd6wEhgtDT9soosna", "username": "PYTHAGOROS.workerName", "password": "anything123", "enabled": True},
    headers=headers)
log(f"Pool config: {r.status_code} {r.text[:200]}")

# 3. Save mining status BEFORE start
log("Saving mining status BEFORE start...")
r = requests.get(f"{BASE}/api/mining/status", headers=headers)
log(f"Pre-connect status: {r.status_code} {r.json()}")
with open("HYBA_FULLSTACK_COMMAND_ROOM_20260612/mining_status_before_start.json", "w") as f:
    json.dump(r.json(), f, indent=2)

# 4. Connect to Braiins
log("Connecting to Braiins pool...")
r = requests.post(f"{BASE}/api/mining/connect",
    json={"pool_id": "braiins", "capacity_ehs": 0.1, "switch": True},
    headers=headers)
log(f"Connect response: {r.status_code}")
if r.status_code == 200:
    log(f"Connected: {json.dumps(r.json(), indent=2)[:500]}")
else:
    log(f"Connect failed: {r.text[:500]}")
    sys.exit(1)

# 5. Mining session - 5 minutes
log("=" * 50)
log("MINING SESSION STARTED — 5 MINUTES")
log("=" * 50)

for minute in range(5):
    time.sleep(60)
    try:
        r = requests.get(f"{BASE}/api/mining/status", headers=headers)
        status = r.json()
        shares = status.get("shares", {})
        log(f"Minute {minute+1}/5: submitted={shares.get('submitted',0)} accepted={shares.get('accepted',0)} rejected={shares.get('rejected',0)} hashrate={status.get('hashrate_ehs')} EH/s active={status.get('active')}")
        
        # Check bridge health
        r2 = requests.get(f"{BRIDGE}/bridge/health")
        log(f"  Bridge health: {r2.json().get('status')}")
    except Exception as e:
        log(f"  Status check error: {e}")

# 6. Capture final mining status
log("=" * 50)
log("MINING SESSION COMPLETE — CAPTURING EVIDENCE")
log("=" * 50)
r = requests.get(f"{BASE}/api/mining/status", headers=headers)
final_status = r.json()
log(f"Final status: {json.dumps(final_status, indent=2)[:1000]}")
with open("HYBA_FULLSTACK_COMMAND_ROOM_20260612/mining_status_after_start.json", "w") as f:
    json.dump(final_status, f, indent=2)

# 7. Get pools
r = requests.get(f"{BASE}/api/mining/pools", headers=headers)
with open("HYBA_FULLSTACK_COMMAND_ROOM_20260612/pools_status.json", "w") as f:
    json.dump(r.json(), f, indent=2)
log(f"Pools: {json.dumps(r.json(), indent=2)[:500]}")

# 8. Update treasury note
log("Session evidence captured. Disconnect? (yes)")
try:
    r = requests.post(f"{BASE}/api/mining/disconnect", headers=headers)
    log(f"Disconnect: {r.status_code} {r.text[:200]}")
except:
    log("Disconnect not needed (maybe server was already stopped)")

log("DONE - Check HYBA_FULLSTACK_COMMAND_ROOM_20260612/ for evidence")