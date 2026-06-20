import asyncio
import json
import logging
import os
import signal
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "python_backend"))

os.chdir(REPO_ROOT)
os.environ["PYTHONPATH"] = "python_backend"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("mining_session")

MAX_MINUTES = 120
MAX_SECONDS = MAX_MINUTES * 60
START = time.time()

from python_backend.run_unified_miner import UnifiedMiner, RUNNING, signal_handler

async def run_bounded():
    miner = UnifiedMiner()
    try:
        await miner.run()
    finally:
        await miner.shutdown()

def main():
    logger.info("Bounded mining session: max %d minutes", MAX_MINUTES)

    def timeout_handler(signum, frame):
        logger.info("Timeout reaimport asyncio
import json
import loMAX_MINUTES)
        signal_handler(signal.SIGTERM, frame)

    old_handler = signal.signal(signal.SIGTERM, tifrom pathdlefrom datetime import da  
REPO_ROOT = Path(__file__).resolve().Keysys.path.insert(0, str(REPO_ROOT / "pytherrupted
os.chdir(REPO_ROOT)
os.environ["PYTHONPATH"] = "pyt, oos.environ["P       
logging.basicConfig(
    level=logging.INer.    level=logging.I.     format="%(asctime) e    dd / 60.0)

if __name__ == "__main__":
    main()
