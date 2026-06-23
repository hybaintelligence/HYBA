#!/bin/bash
# HYBA Production Deployment Script
# Verifies production readiness before deployment

set -e

echo "🚀 HYBA Production Deployment"
echo "=============================="
echo ""

# Check environment
if [ "$HYBA_CUSTOMER_MODE" != "true" ]; then
  echo "❌ HYBA_CUSTOMER_MODE must be 'true' for production deployment"
  exit 1
fi

if [ -z "$JWT_SECRET" ] || [ -z "$HYBA_API_KEY_SECRET" ]; then
  echo "❌ Required secrets not set (JWT_SECRET, HYBA_API_KEY_SECRET)"
  exit 1
fi

echo "✅ Environment configuration validated"
echo ""

# Run production checks
echo "Running production checks..."
npm run lint
npm run test:frontend:all
npm run build

echo ""
echo "✅ All checks passed"
echo "🎯 Ready for deployment"
