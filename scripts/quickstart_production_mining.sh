#!/bin/bash
#
# Quick Start: Production Mining Setup
#
# This script guides you through setting up production mining with real pools.
# Supports both NiceHash and other Stratum v1/v2 pools.
#

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     HYBA Production Mining - Quick Start Setup             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Detect OS
OS="$(uname -s)"
case "${OS}" in
    Linux*)     OS_TYPE="Linux";;
    Darwin*)    OS_TYPE="Mac";;
    MINGW*)     OS_TYPE="Windows";;
    *)          OS_TYPE="Unknown";;
esac

echo -e "${GREEN}✓${NC} Detected OS: ${OS_TYPE}"
echo ""

# Step 1: Detect Python
echo "Step 1: Checking Python environment..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗${NC} Python 3 not found. Please install Python 3.12+"
    exit 1
fi
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓${NC} Python ${PYTHON_VERSION} detected"
echo ""

# Step 2: Pool configuration
echo "Step 2: Pool Configuration"
echo "Choose your setup:"
echo "  1) NiceHash (recommended for beginners)"
echo "  2) Custom Pool (enter manually)"
echo ""
read -p "Enter choice (1-2): " pool_choice

if [ "$pool_choice" = "1" ]; then
    echo ""
    echo "NiceHash Setup:"
    echo "1. Go to https://www.nicehash.com/my/settings/wallets"
    echo "2. Your Bitcoin address is your NiceHash username"
    echo ""
    read -p "Enter your NiceHash Bitcoin address: " nh_address
    
    if [ -z "$nh_address" ]; then
        echo -e "${RED}✗${NC} Bitcoin address cannot be empty"
        exit 1
    fi
    
    # Set NiceHash environment
    export HYBA_POOL_1_NAME="NiceHash Primary"
    export HYBA_POOL_1_URL="stratum+ssl://btc.nicehash.com:3334"
    export HYBA_POOL_1_USERNAME="$nh_address"
    export HYBA_POOL_1_PASSWORD="x"
    export HYBA_POOL_1_STRATUM_VERSION="1"
    export HYBA_POOL_1_PRIORITY="100"
    export HYBA_POOL_1_TLS_REQUIRED="true"
    
    # Optional: Add ViaBTC as backup
    export HYBA_POOL_2_NAME="ViaBTC Backup"
    export HYBA_POOL_2_URL="stratum+ssl://btc.viabtc.com:3333"
    export HYBA_POOL_2_USERNAME="$nh_address.hyba"
    export HYBA_POOL_2_PASSWORD="password"
    export HYBA_POOL_2_STRATUM_VERSION="1"
    export HYBA_POOL_2_PRIORITY="90"
    export HYBA_POOL_2_TLS_REQUIRED="true"
    
    echo -e "${GREEN}✓${NC} NiceHash configuration set"
    echo "  Primary: btc.nicehash.com:3334"
    echo "  Backup: btc.viabtc.com:3333"
    
else
    echo ""
    echo "Custom Pool Setup:"
    read -p "Enter pool URL (e.g., stratum+ssl://pool.example.com:3334): " pool_url
    read -p "Enter username/wallet address: " pool_user
    read -p "Enter password (leave blank for 'x'): " pool_pass
    
    if [ -z "$pool_url" ] || [ -z "$pool_user" ]; then
        echo -e "${RED}✗${NC} Pool URL and username are required"
        exit 1
    fi
    
    pool_pass=${pool_pass:-"x"}
    
    export HYBA_POOL_1_NAME="Custom Pool"
    export HYBA_POOL_1_URL="$pool_url"
    export HYBA_POOL_1_USERNAME="$pool_user"
    export HYBA_POOL_1_PASSWORD="$pool_pass"
    export HYBA_POOL_1_STRATUM_VERSION="1"
    export HYBA_POOL_1_PRIORITY="100"
    
    echo -e "${GREEN}✓${NC} Custom pool configured"
fi

echo ""

# Step 3: Set production mode
echo "Step 3: Configuring Production Mode"
export NODE_ENV="production"
echo -e "${GREEN}✓${NC} Production mode enabled"
echo ""

# Step 4: Mining strategy
echo "Step 4: Mining Strategy"
echo "Choose share submission strategy:"
echo "  1) Failover (default) - submit to first pool, cascade on failure"
echo "  2) Multi-pool - submit to all healthy pools simultaneously"
echo "  3) First-pool - only use primary pool"
echo ""
read -p "Enter choice (1-3, default 1): " strategy_choice
strategy_choice=${strategy_choice:-1}

case $strategy_choice in
    1) export HYBA_MINING_STRATEGY="failover" ;;
    2) export HYBA_MINING_STRATEGY="multi_pool" ;;
    3) export HYBA_MINING_STRATEGY="first_pool" ;;
    *) export HYBA_MINING_STRATEGY="failover" ;;
esac

echo -e "${GREEN}✓${NC} Mining strategy: ${HYBA_MINING_STRATEGY}"
echo ""

# Step 5: Validation
echo "Step 5: Pre-Deployment Validation"
echo ""

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Run deployment gate
echo "Running deployment validation gate..."
python3 "$REPO_ROOT/scripts/production_mining_deployment_gate.py"

if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠${NC}  Deployment gate failed. Review errors above."
    read -p "Continue anyway? (y/N): " continue_anyway
    if [ "$continue_anyway" != "y" ]; then
        exit 1
    fi
fi

echo ""

# Step 6: Start services
echo "Step 6: Starting Services"
echo ""

# Check if backend is running
if pgrep -f "uvicorn.*hyba_genesis_api" > /dev/null; then
    echo -e "${YELLOW}⚠${NC}  Backend already running"
else
    echo "Starting backend API..."
    cd "$REPO_ROOT"
    
    # Use nohup on Unix, start /B on Windows
    if [ "$OS_TYPE" = "Windows" ]; then
        start /B cmd /c "cd $REPO_ROOT && npm run backend:start"
    else
        nohup npm run backend:start > mining-backend.log 2>&1 &
    fi
    
    echo "Waiting for backend to be ready..."
    sleep 5
    
    # Check if backend is responding
    for i in {1..10}; do
        if curl -s http://localhost:3001/health > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} Backend is ready"
            break
        fi
        if [ $i -eq 10 ]; then
            echo -e "${RED}✗${NC} Backend did not start. Check mining-backend.log"
            exit 1
        fi
        sleep 1
    done
fi

echo ""

# Step 7: Initialize mining
echo "Step 7: Initializing Mining Gateway"
echo ""

echo "Calling: POST /api/v1/mining-production/initialize"
response=$(curl -s -X POST http://localhost:3001/api/v1/mining-production/initialize)

if echo "$response" | grep -q "initialized"; then
    echo -e "${GREEN}✓${NC} Mining gateway initialized"
    echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
else
    echo -e "${RED}✗${NC} Failed to initialize mining gateway"
    echo "$response"
    exit 1
fi

echo ""

# Step 8: Start mining
echo "Step 8: Starting Mining Operations"
echo ""

echo "Calling: POST /api/v1/mining-production/start"
response=$(curl -s -X POST http://localhost:3001/api/v1/mining-production/start)

if echo "$response" | grep -q "started"; then
    echo -e "${GREEN}✓${NC} Mining operations started"
    echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
else
    echo -e "${RED}✗${NC} Failed to start mining operations"
    echo "$response"
    exit 1
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║         ${GREEN}✓${NC}  Production Mining Setup Complete         "
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Next Steps:"
echo "  1. Monitor status:"
echo "     watch -n 5 'curl -s http://localhost:3001/api/v1/mining-production/status | jq .'"
echo ""
echo "  2. View pool health:"
echo "     curl http://localhost:3001/api/v1/mining-production/health | jq ."
echo ""
echo "  3. Get mining metrics:"
echo "     curl http://localhost:3001/api/v1/mining-production/metrics | jq ."
echo ""
echo "  4. Stop mining:"
echo "     curl -X POST http://localhost:3001/api/v1/mining-production/stop"
echo ""
echo "Documentation:"
echo "  - Full guide: docs/PRODUCTION_MINING_INTEGRATION.md"
echo "  - Troubleshooting: Check mining-backend.log for errors"
echo ""
