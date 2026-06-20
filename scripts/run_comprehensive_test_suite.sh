#!/bin/bash
# Comprehensive test suite runner for autonomous mining system
# Runs unit, integration, stress, adversarial, and property-based tests

set -e  # Exit on error

# Colors for output
RED='\033[0:31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}HYBA Comprehensive Test Suite${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check Python environment
echo -e "${YELLOW}Checking Python environment...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ python3 not found${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✅ ${PYTHON_VERSION}${NC}"
echo ""

# Set PYTHONPATH
export PYTHONPATH="${PWD}/python_backend:${PYTHONPATH}"

# Test categories
UNIT_TESTS="tests/test_autonomous_mining_controller.py tests/test_boot_self_heal_behavioral.py tests/test_create_mining_env_cli.py"
STRESS_TESTS="tests/test_autonomous_mining_stress.py"
ADVERSARIAL_TESTS="tests/test_autonomous_mining_adversarial.py"
PROPERTY_TESTS="tests/test_autonomous_mining_properties.py"

# Run unit tests
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}1. Unit & Integration Tests${NC}"
echo -e "${BLUE}========================================${NC}"
if pytest ${UNIT_TESTS} -v --tb=short; then
    echo -e "${GREEN}✅ Unit tests passed${NC}"
else
    echo -e "${RED}❌ Unit tests failed${NC}"
    exit 1
fi
echo ""

# Run stress tests
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}2. Stress Tests${NC}"
echo -e "${BLUE}========================================${NC}"
if pytest ${STRESS_TESTS} -v -m stress --tb=short; then
    echo -e "${GREEN}✅ Stress tests passed${NC}"
else
    echo -e "${YELLOW}⚠️  Stress tests failed (non-blocking)${NC}"
fi
echo ""

# Run adversarial tests
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}3. Adversarial Tests${NC}"
echo -e "${BLUE}========================================${NC}"
if pytest ${ADVERSARIAL_TESTS} -v -m adversarial --tb=short; then
    echo -e "${GREEN}✅ Adversarial tests passed${NC}"
else
    echo -e "${YELLOW}⚠️  Adversarial tests failed (non-blocking)${NC}"
fi
echo ""

# Run property-based tests
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}4. Property-Based Tests${NC}"
echo -e "${BLUE}========================================${NC}"
if pytest ${PROPERTY_TESTS} -v -m property --tb=short; then
    echo -e "${GREEN}✅ Property-based tests passed${NC}"
else
    echo -e "${YELLOW}⚠️  Property-based tests failed (non-blocking)${NC}"
fi
echo ""

# Run command-room game day
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}5. Command-Room Game Day${NC}"
echo -e "${BLUE}========================================${NC}"
if python scripts/command_room_game_day.py --json; then
    echo -e "${GREEN}✅ Game day scenarios passed${NC}"
else
    echo -e "${RED}❌ Game day scenarios failed${NC}"
    exit 1
fi
echo ""

# Run metrics load test
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}6. Metrics Load Test${NC}"
echo -e "${BLUE}========================================${NC}"
if python scripts/test_metrics_under_load.py; then
    echo -e "${GREEN}✅ Metrics load test passed${NC}"
else
    echo -e "${RED}❌ Metrics load test failed${NC}"
    exit 1
fi
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Test Suite Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ Core tests: PASS${NC}"
echo -e "${GREEN}✅ Operational tests: PASS${NC}"
echo -e "${YELLOW}⚠️  Extended tests: See output above${NC}"
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ COMPREHENSIVE TEST SUITE COMPLETE${NC}"
echo -e "${GREEN}========================================${NC}"
