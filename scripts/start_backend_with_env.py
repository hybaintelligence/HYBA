"""Start the backend with correct env from .env file."""

import logging
import os
import sys

logger = logging.getLogger("start_backend")

# Load .env file at the project root
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                # DON'T overwrite already-set env vars
                if key not in os.environ:
                    os.environ[key] = value
    logger.info(
        "Loaded env from %s (set %d vars)",
        env_path,
        sum(1 for k in os.environ if k not in ("NODE_ENV", "HYBA_ENV")),
    )

# Also explicitly set NODE_ENV and HYBA_ENV
os.environ.setdefault("NODE_ENV", "production")
os.environ.setdefault("HYBA_ENV", "production")

# Start uvicorn
sys.argv = [
    "uvicorn",
    "hyba_genesis_api.main:app",
    "--app-dir",
    "python_backend",
    "--host",
    "127.0.0.1",
    "--port",
    "3001",
]

import uvicorn

uvicorn.run(
    "hyba_genesis_api.main:app",
    app_dir="python_backend",
    host="127.0.0.1",
    port=3001,
)
