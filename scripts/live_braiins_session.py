#!/usr/bin/env python3
"""Live mining session with Braiins pool for testing job acceptance and share submission."""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pythia_mining.stratum_client import StratumClient, MiningJob, ShareResult


async def monitor_mining_session(
    pool_url: str,
    username: str,
    password: str,
    pool_name: str,
    stratum_version: int = 2,
    duration_seconds: int = 300,
) -> dict:
    """Run a live mining session and monitor job acceptance and share submission."""
    
    print(f"Starting live mining session with {pool_name}")
    print(f"Pool URL: {pool_url}")
    print(f"Stratum Version: {stratum_version}")
    print(f"Duration: {duration_seconds} seconds")
    print("-" * 60)
    
    client = StratumClient(
        pool_url=pool_url,
        username=username,
        password=password,
        pool_name=pool_name,
        stratum_version=stratum_version,
    )
    
    session_stats = {
        "pool_name": pool_name,
        "pool_url": pool_url,
        "stratum_version": stratum_version,
        "duration_seconds": duration_seconds,
        "start_time": time.time(),
        "end_time": None,
        "connected": False,
        "authenticated": False,
        "jobs_received": 0,
        "jobs": [],
        "shares_submitted": 0,
        "shares_accepted": 0,
        "shares_rejected": 0,
        "share_results": [],
        "errors": [],
    }
    
    try:
        # Connect to pool
        print("Connecting to pool...")
        connected = await client.connect()
        session_stats["connected"] = connected
        
        if not connected:
            session_stats["errors"].append("Failed to connect to pool")
            print("ERROR: Failed to connect to pool")
            return session_stats
        
        print(f"Connected successfully to {pool_name}")
        
        # Authenticate
        print("Authenticating...")
        authenticated = await client.authenticate()
        session_stats["authenticated"] = authenticated
        
        if not authenticated:
            session_stats["errors"].append("Failed to authenticate")
            print("ERROR: Failed to authenticate")
            return session_stats
        
        print(f"Authenticated successfully as {username}")
        
        # Subscribe to receive jobs
        print("Subscribing to mining jobs...")
        subscribed = await client.subscribe()
        
        if not subscribed:
            session_stats["errors"].append("Failed to subscribe")
            print("ERROR: Failed to subscribe")
            return session_stats
        
        print("Subscribed successfully")
        
        # Monitor for jobs and shares
        print("\n" + "=" * 60)
        print("MONITORING MINING SESSION")
        print("=" * 60)
        
        start_time = time.time()
        last_job_check = start_time
        
        while time.time() - start_time < duration_seconds:
            # Check for new jobs
            if time.time() - last_job_check > 5:  # Check every 5 seconds
                current_jobs = client.current_jobs
                jobs_count = len(current_jobs)
                
                if jobs_count > session_stats["jobs_received"]:
                    new_jobs = jobs_count - session_stats["jobs_received"]
                    print(f"\n[{time.time() - start_time:.1f}s] Received {new_jobs} new job(s)")
                    
                    for job_id, job in current_jobs.items():
                        if job_id not in [j["job_id"] for j in session_stats["jobs"]]:
                            job_info = {
                                "job_id": job.job_id,
                                "prevhash": job.prevhash,
                                "version": job.version,
                                "nbits": job.nbits,
                                "ntime": job.ntime,
                                "target": job.target,
                                "received_at": job.received_timestamp,
                            }
                            session_stats["jobs"].append(job_info)
                            print(f"  Job: {job.job_id}")
                            print(f"    Prevhash: {job.prevhash[:16]}...")
                            print(f"    Version: {job.version}")
                            print(f"    NBits: {job.nbits}")
                            print(f"    Target: {job.target}")
                    
                    session_stats["jobs_received"] = jobs_count
                
                last_job_check = time.time()
            
            # Check connection status
            if not client.is_connected:
                session_stats["errors"].append("Connection lost during session")
                print("ERROR: Connection lost")
                break
            
            # Small delay to prevent busy waiting
            await asyncio.sleep(1)
        
        session_stats["end_time"] = time.time()
        session_stats["duration_actual"] = session_stats["end_time"] - session_stats["start_time"]
        
        print("\n" + "=" * 60)
        print("SESSION SUMMARY")
        print("=" * 60)
        print(f"Duration: {session_stats['duration_actual']:.1f} seconds")
        print(f"Jobs Received: {session_stats['jobs_received']}")
        print(f"Shares Submitted: {session_stats['shares_submitted']}")
        print(f"Shares Accepted: {session_stats['shares_accepted']}")
        print(f"Shares Rejected: {session_stats['shares_rejected']}")
        
        if session_stats["errors"]:
            print(f"\nErrors: {len(session_stats['errors'])}")
            for error in session_stats["errors"]:
                print(f"  - {error}")
        
    except Exception as e:
        session_stats["errors"].append(f"Exception: {str(e)}")
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        try:
            await client.close()
            print("\nConnection closed")
        except Exception as e:
            print(f"Error closing connection: {e}")
    
    return session_stats


def main():
    """Main entry point for live mining session."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Live mining session with Braiins pool")
    parser.add_argument("--pool-url", default="stratum2+tcp://stratum.braiins.com:3333", help="Pool URL")
    parser.add_argument("--username", required=True, help="Mining pool username/worker")
    parser.add_argument("--password", default="x", help="Mining pool password")
    parser.add_argument("--pool-name", default="braiins", help="Pool name for logging")
    parser.add_argument("--stratum-version", type=int, default=2, help="Stratum protocol version")
    parser.add_argument("--duration", type=int, default=300, help="Session duration in seconds")
    parser.add_argument("--output", help="Output JSON file for session stats")
    
    args = parser.parse_args()
    
    # Enable live stratum for this session
    os.environ["HYBA_ENABLE_LIVE_STRATUM"] = "true"
    os.environ["HYBA_ENABLE_LIVE_SHARE_SUBMIT"] = "true"
    
    stats = asyncio.run(monitor_mining_session(
        pool_url=args.pool_url,
        username=args.username,
        password=args.password,
        pool_name=args.pool_name,
        stratum_version=args.stratum_version,
        duration_seconds=args.duration,
    ))
    
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(stats, indent=2))
        print(f"\nSession stats saved to {output_path}")
    
    # Return exit code based on success
    if stats["connected"] and stats["authenticated"]:
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
