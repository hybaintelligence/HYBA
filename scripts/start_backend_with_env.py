"""Start the backend with correct env from .env file."""
import os
import sys

# Load .env file at the project root
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                # DON'T overwrite already-set env vars
                if key not in os.environ:
                    os.environ[key] = value
    print(f"[start_backend] Loaded env from {env_path}, found {len([k for k in os.environ])} env vars")
    # Verify the credential
    cred = os.environ.get('HYBA_OPERATOR_CREDENTIALS', 'NOT_SET')
    print(f"[start_backend] HYBA_OPERATOR_CREDENTIALS = {cred[:40]}...")

# Also explicitly set NODE_ENV and HYBA_ENV
os.environ.setdefault('NODE_ENV', 'production')
os.environ.setdefault('HYBA_ENV', 'production')

# Start uvicorn
sys.argv = ['uvicorn', 'hyba_genesis_api.main:app', '--app-dir', 'python_backend', '--host', '127.0.0.1', '--port', '3001']

import uvicorn
uvicorn.run(
    'hyba_genesis_api.main:app',
    app_dir='python_backend',
    host='127.0.0.1',
    port=3001,
)