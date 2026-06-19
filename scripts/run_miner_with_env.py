#!/usr/bin/env python3
import os
import sys
import dotenv
from pathlib import Path

# Load .env.mining.local
env_path = Path(__file__).resolve().parents[1] / ".env.mining.local"
dotenv.load_dotenv(env_path)

# Now exec the real miner so it inherits the loaded environment
os.execvp(sys.executable, [sys.executable, "python_backend/run_unified_miner.py"])
