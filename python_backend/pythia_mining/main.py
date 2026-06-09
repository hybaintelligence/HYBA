# main.py
import asyncio
import logging
import time
import json
import os
from .genesis_ai import GenesisAI

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("pythia_main")

config = {
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    }
}

async def main():
    pythia = GenesisAI(config)
    logger.info("Initializing PYTHIA Quantum Mining Orchestrator background daemon...")
    if await pythia.start():
        logger.info("PYTHIA Quantum Mining System fully operational & quantum coherent.")
        export_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pythia_state.json")
        logger.info(f"Targeting state vector telemetry export: {export_path}")
        
        while True:
            try:
                status = pythia.get_system_status()
                # Write atomically using temporary file to prevent read conflicts
                temp_path = export_path + ".tmp"
                with open(temp_path, "w") as f:
                    json.dump(status, f, indent=2)
                os.replace(temp_path, export_path)
            except Exception as e:
                logger.error(f"Error updating state JSON: {e}")
            await asyncio.sleep(1.0)
    else:
        logger.error("Quantum execution anomaly matched. Background daemon failed.")

if __name__ == "__main__":
    asyncio.run(main())

