# main.py
import asyncio
import logging
import time
import json
import os
import signal
from .genesis_ai import GenesisAI

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("pythia_main")

config = {
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    }
}

# Handle signals for graceful shutdown
SHUTDOWN_EVENT = asyncio.Event()

def signal_handler():
    logger.info("Shutdown signal received. Finalizing Φ-cycles...")
    SHUTDOWN_EVENT.set()

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
        export_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pythia_state.json")
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mining_config.json")
        logger.info(f"Targeting state vector telemetry export: {export_path}")
        
        while not SHUTDOWN_EVENT.is_set():
            try:
                # Check for configuration updates from the governance layer
                if os.path.exists(config_path):
                    try:
                        with open(config_path, "r") as f:
                            cmd_config = json.load(f)
                            if "power_scale" in cmd_config:
                                pythia.quantum_solver.set_power_scale(float(cmd_config["power_scale"]))
                                logger.info(f"Governance Layer: Power scale adjusted to {cmd_config['power_scale']}x")
                        # Clear processed config
                        os.remove(config_path)
                    except Exception as ce:
                        logger.error(f"Error processing mining_config: {ce}")

                status = pythia.get_system_status()
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

