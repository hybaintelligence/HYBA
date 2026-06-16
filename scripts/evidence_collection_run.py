#!/usr/bin/env python3
"""Evidence collection run - deploy to Docker and capture telemetry for 10 minutes."""

from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "artifacts" / "evidence_collection"
DURATION_SECONDS = 600  # 10 minutes


def timestamp() -> str:
    """Return ISO timestamp."""
    return datetime.now(timezone.utc).isoformat()


def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run command and return result."""
    print(f"[{timestamp()}] Running: {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=check)


def collect_health_check(service_url: str, name: str) -> dict:
    """Collect health check from service."""
    try:
        result = run_command(["curl", "-fsS", service_url], check=False)
        if result.returncode == 0:
            try:
                return {"status": "ok", "data": json.loads(result.stdout)}
            except json.JSONDecodeError:
                return {"status": "ok", "data": result.stdout}
        else:
            return {"status": "error", "error": result.stderr}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def collect_logs(service: str) -> str:
    """Collect logs from Docker service."""
    try:
        result = run_command(
            [
                "docker-compose",
                "-f",
                "docker-compose.production.yml",
                "--env-file",
                ".env.docker",
                "logs",
                "--tail=100",
                service,
            ],
            check=False,
        )
        return result.stdout
    except Exception as e:
        return f"Error collecting logs: {e}"


def main() -> int:
    """Run evidence collection."""

    print("=" * 80)
    print("HYBA QUANTUM PLATFORM - EVIDENCE COLLECTION RUN")
    print("=" * 80)
    print(f"Start time: {timestamp()}")
    print(f"Duration: {DURATION_SECONDS} seconds ({DURATION_SECONDS // 60} minutes)")
    print()

    # Create evidence directory
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = EVIDENCE_DIR / f"run_{run_id}"
    run_dir.mkdir(exist_ok=True)

    print(f"Evidence directory: {run_dir}")
    print()

    # Initialize evidence collection
    evidence = {
        "run_id": run_id,
        "start_time": timestamp(),
        "duration_seconds": DURATION_SECONDS,
        "snapshots": [],
        "events": [],
    }

    # Stop any existing containers
    print("Stopping existing containers...")
    run_command(
        [
            "docker-compose",
            "-f",
            "docker-compose.production.yml",
            "--env-file",
            ".env.docker",
            "down",
        ],
        check=False,
    )
    print()

    # Start services
    print("Starting Docker services...")
    result = run_command(
        [
            "docker-compose",
            "-f",
            "docker-compose.production.yml",
            "--env-file",
            ".env.docker",
            "up",
            "-d",
            "--build",
        ],
        check=False,
    )

    if result.returncode != 0:
        print("❌ Failed to start Docker services")
        print(result.stderr)
        return 1

    evidence["events"].append(
        {
            "timestamp": timestamp(),
            "event": "docker_services_started",
            "status": "success",
        }
    )
    print("✅ Docker services started")
    print()

    # Wait for services to initialize
    print("Waiting 30 seconds for services to initialize...")
    time.sleep(30)
    print()

    # Collection loop
    snapshot_interval = 60  # 1 minute
    snapshots_to_collect = DURATION_SECONDS // snapshot_interval

    print(f"Collecting {snapshots_to_collect} snapshots at {snapshot_interval}s intervals...")
    print()

    for i in range(snapshots_to_collect):
        snapshot_time = timestamp()
        elapsed = (i + 1) * snapshot_interval
        remaining = DURATION_SECONDS - elapsed

        print(
            f"[{snapshot_time}] Snapshot {i + 1}/{snapshots_to_collect} "
            + f"(elapsed: {elapsed}s, remaining: {remaining}s)"
        )

        snapshot = {
            "snapshot_id": i + 1,
            "timestamp": snapshot_time,
            "elapsed_seconds": elapsed,
            "health_checks": {},
            "service_status": {},
        }

        # Collect health checks
        print("  Collecting health checks...")
        snapshot["health_checks"]["bridge"] = collect_health_check(
            "http://localhost:3000/bridge/health", "bridge"
        )
        snapshot["health_checks"]["backend_readiness"] = collect_health_check(
            "http://localhost:3001/api/health/readiness", "backend_readiness"
        )
        snapshot["health_checks"]["substrate"] = collect_health_check(
            "http://localhost:3001/api/substrate", "substrate"
        )

        # Check service status
        print("  Checking service status...")
        ps_result = run_command(
            [
                "docker-compose",
                "-f",
                "docker-compose.production.yml",
                "--env-file",
                ".env.docker",
                "ps",
                "--format",
                "json",
            ],
            check=False,
        )

        if ps_result.returncode == 0:
            try:
                snapshot["service_status"] = json.loads(ps_result.stdout)
            except json.JSONDecodeError:
                snapshot["service_status"] = {"error": "Failed to parse service status"}

        evidence["snapshots"].append(snapshot)

        # Print summary
        for service, health in snapshot["health_checks"].items():
            status_icon = "✅" if health.get("status") == "ok" else "❌"
            print(f"    {status_icon} {service}: {health.get('status', 'unknown')}")

        print()

        # Save intermediate results
        with open(run_dir / "evidence.json", "w") as f:
            json.dump(evidence, f, indent=2)

        # Wait for next snapshot (unless this is the last one)
        if i < snapshots_to_collect - 1:
            time.sleep(snapshot_interval)

    # Final log collection
    print("Collecting final logs...")
    print()

    logs = {}
    for service in ["hyba-bridge", "hyba-backend", "hyba-runtime"]:
        print(f"  Collecting logs from {service}...")
        logs[service] = collect_logs(service)

    evidence["final_logs"] = logs
    evidence["end_time"] = timestamp()

    # Save final evidence
    print()
    print("Saving evidence...")
    with open(run_dir / "evidence.json", "w") as f:
        json.dump(evidence, f, indent=2)

    # Save individual log files
    for service, log_content in logs.items():
        log_file = run_dir / f"{service}.log"
        log_file.write_text(log_content, encoding="utf-8")
        print(f"  Saved {log_file}")

    # Stop services
    print()
    print("Stopping Docker services...")
    run_command(
        [
            "docker-compose",
            "-f",
            "docker-compose.production.yml",
            "--env-file",
            ".env.docker",
            "down",
        ],
        check=False,
    )

    evidence["events"].append(
        {
            "timestamp": timestamp(),
            "event": "docker_services_stopped",
            "status": "success",
        }
    )

    # Final save
    with open(run_dir / "evidence.json", "w") as f:
        json.dump(evidence, f, indent=2)

    # Generate summary
    print()
    print("=" * 80)
    print("EVIDENCE COLLECTION COMPLETE")
    print("=" * 80)
    print(f"Run ID: {run_id}")
    print(f"Evidence directory: {run_dir}")
    print(f"Total snapshots: {len(evidence['snapshots'])}")
    print(f"Duration: {DURATION_SECONDS}s")
    print()

    # Calculate success rate
    successful_snapshots = sum(
        1
        for s in evidence["snapshots"]
        if all(h.get("status") == "ok" for h in s["health_checks"].values())
    )
    success_rate = (
        (successful_snapshots / len(evidence["snapshots"]) * 100) if evidence["snapshots"] else 0
    )

    print(
        f"Health check success rate: {success_rate:.1f}% ({successful_snapshots}/{len(evidence['snapshots'])})"
    )
    print()
    print("Artifacts:")
    print(f"  - Evidence JSON: {run_dir / 'evidence.json'}")
    for service in logs.keys():
        print(f"  - {service} logs: {run_dir / f'{service}.log'}")
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
