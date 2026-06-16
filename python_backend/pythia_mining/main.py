# main.py
import asyncio
import json
import logging
import os
import signal
import time

from .genesis_ai import GenesisAI

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("pythia_main")

config = {
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    }
}

# Handle signals for graceful shutdown
SHUTDOWN_EVENT = asyncio.Event()


def signal_handler():
    logger.info("Shutdown signal received. Finalizing Φ-cycles...")
    SHUTDOWN_EVENT.set()


def enrich_runtime_sequence(status):
    """Ensure exported state always explains the post-connect job lifecycle."""
    ordered_stages = [
        "connect_requested",
        "pool_bound",
        "subscribed_authorized",
        "awaiting_job",
        "job_received",
        "work_configured",
        "candidate_evaluated",
        "share_submitted",
        "share_outcome_recorded",
    ]
    active_pool = None
    for pool in status.get("pools", []) or []:
        if pool.get("is_active"):
            active_pool = pool
            break
    if active_pool is None and status.get("pools"):
        active_pool = status["pools"][0]

    current_job = status.get("current_job")
    if isinstance(current_job, str):
        current_job_id = current_job
        current_job_payload = None
    elif isinstance(current_job, dict):
        current_job_id = current_job.get("job_id")
        current_job_payload = current_job
    else:
        current_job_id = None
        current_job_payload = None

    if active_pool and not current_job_payload:
        current_job_payload = active_pool.get("current_job")
        if current_job_payload and not current_job_id:
            current_job_id = current_job_payload.get("job_id")

    if current_job_payload:
        stage = "job_received"
    elif active_pool and active_pool.get("is_authenticated"):
        stage = "awaiting_job"
    elif active_pool and active_pool.get("is_connected"):
        stage = "subscribed_authorized"
    elif active_pool:
        stage = "pool_bound"
    else:
        stage = "connect_requested" if status.get("running") else "stopped"

    status["current_job_id"] = current_job_id
    status["current_job"] = current_job_payload or current_job
    status["job_sequence"] = status.get("job_sequence") or {
        "stage": stage,
        "job_id": current_job_id,
        "pool_id": status.get("active_pool_id"),
        "updated_at": time.time(),
        "ordered_stages": ordered_stages,
        "detail": {
            "active_pool": status.get("active_pool"),
            "pool_state": active_pool.get("connection_state") if active_pool else None,
            "shares": {
                "submitted": status.get("total_shares"),
                "accepted": status.get("accepted_shares"),
                "rejected": status.get("rejected_shares"),
            },
        },
    }
    status["connect_ready"] = bool(active_pool) and stage in {
        "pool_bound",
        "subscribed_authorized",
        "awaiting_job",
        "job_received",
    }
    return status


async def main():
    # Register signal handlers for Unix-like environments
    try:
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, signal_handler)
    except NotImplementedError:
        # Fallback for systems where add_signal_handler is not implemented (e.g. Windows)
        pass

    pythia = GenesisAI(config)
    logger.info("Initializing PYTHIA Quantum Mining Orchestrator background daemon...")

    if await pythia.start():
        logger.info("PYTHIA Quantum Mining System fully operational & quantum coherent.")
        export_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "pythia_state.json",
        )
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "mining_config.json",
        )
        logger.info(f"Targeting state vector telemetry export: {export_path}")

        while not SHUTDOWN_EVENT.is_set():
            try:
                # Check for configuration updates from the governance layer
                if os.path.exists(config_path):
                    try:
                        with open(config_path, "r") as f:
                            cmd_config = json.load(f)
                            if "power_scale" in cmd_config:
                                pythia.quantum_solver.set_power_scale(
                                    float(cmd_config["power_scale"])
                                )
                                logger.info(
                                    f"Governance Layer: Power scale adjusted to {cmd_config['power_scale']}x"
                                )
                        # Clear processed config
                        os.remove(config_path)
                    except Exception as ce:
                        logger.error(f"Error processing mining_config: {ce}")

                status = enrich_runtime_sequence(pythia.get_system_status())
                # Write atomically using temporary file to prevent read conflicts
                temp_path = export_path + ".tmp"
                with open(temp_path, "w") as f:
                    json.dump(status, f, indent=2)
                os.replace(temp_path, export_path)
            except Exception as e:
                logger.error(f"Error updating state JSON: {e}")

            try:
                await asyncio.wait_for(SHUTDOWN_EVENT.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                pass

        logger.info("Graceful shutdown sequence finalized. Substrate dormant.")
        await pythia.stop()
    else:
        logger.error("Quantum execution anomaly matched. Background daemon failed.")


if __name__ == "__main__":
    asyncio.run(main())
