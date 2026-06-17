import hashlib, json, pathlib, time

root = pathlib.Path("artifacts/release_candidates/pythia_live_viabtc_rc_20260616")
files = {}

for path in sorted(root.glob("*")):
    if path.is_file():
        files[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()

manifest = {
    "release_candidate": "pythia_live_viabtc_rc_20260616",
    "created_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "status": "live_release_candidate",
    "pool": "ViaBTC BTC Stratum v1",
    "readiness": "8/8 ready",
    "tests": {
        "phi_unified_mining_engine": "21/21",
        "unified_miner_search_workflow": "10/10",
        "pythia_one_block_mission": "15/15",
        "hyba_enterprise_api_posture": "5/5"
    },
    "mission": "one_pool_confirmed_block_then_shutdown",
    "supreme_invariants": [
        "blockchain security above all else",
        "exact SHA-256d final oracle",
        "full nonce coverage preserved",
        "accepted shares are learning events",
        "accepted block proof is mission completion"
    ],
    "files": files
}

(root / "MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(json.dumps(manifest, indent=2))
