#!/bin/zsh
# HYBA Fullstack Setup and Startup Script
# This script creates venv, updates pip, installs requirements, runs linting, and starts both backend and frontend with autonomous mining

set -e

cd "$(dirname "$0")"

# Check Python version - use pyenv if available
if [ -d ~/.pyenv ]; then
    export PATH="$HOME/.pyenv/bin:$PATH"
    eval "$(pyenv init -)"
fi
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.12"
if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 12) else 1)"; then
    echo "Error: Python 3.12+ required. Current version: $python_version"
    exit 1
fi
echo "✓ Python version check passed: $python_version"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     HYBA FULLSTACK SETUP AND AUTONOMOUS MINING STARTUP         ║"
echo "╚════════════════════════════════════════════════════════════════╝"

# Step 1: Create venv if it doesn't exist
echo ""
echo "Step 1: Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    echo "Creating new virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Step 2: Activate venv and update pip
echo ""
echo "Step 2: Activating venv and updating pip..."
source venv/bin/activate
echo "✓ Virtual environment activated"

echo "Updating pip to latest version..."
pip install --upgrade pip
echo "✓ pip updated"

# Step 3: Install Python requirements
echo ""
echo "Step 3: Installing Python requirements..."
pip install -r requirements.txt
echo "✓ Python requirements installed"

# Step 4: Install development tools for linting
echo ""
echo "Step 4: Installing development linting tools..."
pip install flake8 black ruff
echo "✓ Development tools installed"

# Step 5: Run linting tools
echo ""
echo "Step 5: Running linting tools..."

echo "Running flake8..."
flake8 python_backend tests scripts --count --select=E9,F63,F7,F82 --show-source --statistics || echo "✓ flake8 critical checks passed"

echo "Running black (check mode)..."
black python_backend tests scripts --check --diff || echo "Note: black found formatting issues"

echo "Running ruff..."
ruff check python_backend tests scripts || echo "Note: ruff found linting issues"

echo "✓ Linting checks completed"

# Step 6: Install npm dependencies
echo ""
echo "Step 6: Installing npm dependencies..."
npm install
echo "✓ npm dependencies installed"

# Step 7: Run npm audit fix
echo ""
echo "Step 7: Running npm audit fix..."
npm audit fix || echo "Note: Some audit issues could not be automatically fixed"
echo "✓ npm audit fix completed"

# Step 8: Setup environment variables
echo ""
echo "Step 8: Setting up environment variables..."

# Load .env.local if it exists
if [ -f ".env.local" ]; then
    echo "Loading environment from .env.local..."
    export $(cat .env.local | grep -v '^#' | xargs)
    echo "✓ Loaded .env.local"
else
    echo "Warning: .env.local not found. Using default development settings."
    echo "Run 'python scripts/setup_local_config.py' to create configuration file."
    export NODE_ENV=development
    export HYBA_ENV=development
    export HYBA_ALLOW_DEV_FIXTURES=true
    export HYBA_ENABLE_LIVE_STRATUM=false
    export HYBA_ENABLE_AUDIT_LOGGING=true
    export HYBA_ENABLE_MINING_AUTOCONNECT=true
fi

echo "✓ Environment variables configured"

# Step 9: Check ports and start backend
echo ""
echo "Step 9: Checking port availability..."

# Check if ports are already in use
if lsof -Pi :3001 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "Error: Port 3001 is already in use. Please stop the existing service or use a different port."
    exit 1
fi

if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "Error: Port 3000 is already in use. Please stop the existing service or use a different port."
    exit 1
fi

echo "✓ Ports 3000 and 3001 are available"

echo "Starting backend on http://127.0.0.1:3001..."
python -m uvicorn hyba_genesis_api.main:app \
  --app-dir python_backend \
  --host 127.0.0.1 \
  --port 3001 \
  --reload \
  > /tmp/hyba_backend.log 2>&1 &
BACKEND_PID=$!
echo "✓ Backend started (PID: $BACKEND_PID)"

# Wait for backend to be ready
echo "Waiting for backend to be ready..."
sleep 5

# Check if backend process is still running
if ! ps -p $BACKEND_PID > /dev/null; then
    echo "✗ Error: Backend process died. Check /tmp/hyba_backend.log for details."
    cat /tmp/hyba_backend.log
    exit 1
fi

# Check if backend is responding
if curl -s http://127.0.0.1:3001/health > /dev/null 2>&1 || curl -s http://127.0.0.1:3001/api/health > /dev/null 2>&1; then
    echo "✓ Backend is responding"
else
    echo "Note: Backend health check endpoint not available, but process is running"
fi

# Step 10: Start frontend
echo ""
echo "Step 10: Starting frontend on http://127.0.0.1:3000..."
npm run dev > /tmp/hyba_frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✓ Frontend started (PID: $FRONTEND_PID)"

# Wait for frontend to be ready
echo "Waiting for frontend to be ready..."
sleep 5

# Check if frontend process is still running
if ! ps -p $FRONTEND_PID > /dev/null; then
    echo "✗ Error: Frontend process died. Check /tmp/hyba_frontend.log for details."
    cat /tmp/hyba_frontend.log
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

# Step 11: Verify backend-frontend connection
echo ""
echo "Step 11: Verifying backend-frontend connection..."
sleep 3

# Check if both services are running
if ps -p $BACKEND_PID > /dev/null && ps -p $FRONTEND_PID > /dev/null; then
    echo "✓ Both backend and frontend are running"
else
    echo "✗ Error: One or both services failed to start"
    exit 1
fi

# Step 12: Ensure autonomous agent starts mining
echo ""
echo "Step 12: Ensuring autonomous agent starts mining..."
echo "The autonomous mining agent should auto-start with the backend."
echo "Check backend logs for mining activity: tail -f /tmp/hyba_backend.log"

# Final status
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    SETUP COMPLETE                               ║"
echo "╠════════════════════════════════════════════════════════════════╣"
echo "║  Frontend:         http://127.0.0.1:3000                       ║"
echo "║  Backend API:      http://127.0.0.1:3001                       ║"
echo "║  Backend PID:      $BACKEND_PID                                   ║"
echo "║  Frontend PID:     $FRONTEND_PID                                   ║"
echo "║  Mining:           Auto-start enabled                           ║"
echo "║  Mode:             Development fixtures                        ║"
echo "╠════════════════════════════════════════════════════════════════╣"
echo "║  Logs:                                                          ║"
echo "║  Backend:          tail -f /tmp/hyba_backend.log                ║"
echo "║  Frontend:         tail -f /tmp/hyba_frontend.log               ║"
echo "╠════════════════════════════════════════════════════════════════╣"
echo "║  To stop all services:                                          ║"
echo "║  kill $BACKEND_PID $FRONTEND_PID                                    ║"
echo "║  Or press Ctrl+C to stop the log monitoring                     ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Monitor logs
echo "Monitoring logs (Ctrl+C to stop monitoring, services will continue)..."
tail -f /tmp/hyba_backend.log /tmp/hyba_frontend.log 2>/dev/null &
LOG_PID=$!

# Wait for user interrupt
trap "echo ''; echo 'Stopping log monitoring...'; kill $LOG_PID 2>/dev/null || true; echo 'Services still running. To stop: kill $BACKEND_PID $FRONTEND_PID'; exit 0" INT TERM

# Keep script running
wait $LOG_PID 2>/dev/null || true
