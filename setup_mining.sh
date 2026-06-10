#!/bin/bash
#
# HYBA Mining Setup Script
# Configures environment for live mining operations
#

set -e

echo "🔧 HYBA Mining Configuration Setup"
echo "===================================="
echo ""

# Check if we're in the right directory
if [[ ! -f "python_backend/hyba_genesis_api/main.py" ]]; then
    echo "❌ Error: Run this script from the HYBA_FULLSTACK directory"
    exit 1
fi

# Create .env file if it doesn't exist
ENV_FILE=".env.mining"
if [[ -f "$ENV_FILE" ]]; then
    echo "⚠️  Warning: $ENV_FILE already exists"
    read -p "Overwrite? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Keeping existing file"
        exit 0
    fi
fi

echo "📝 Creating mining environment configuration..."

cat > "$ENV_FILE" << 'EOF'
# HYBA Mining Environment Configuration
# Generated: $(date)

# ──────────────────────────────────────────────────────
# ENVIRONMENT
# ──────────────────────────────────────────────────────
NODE_ENV=development
HYBA_ENV=development

# ──────────────────────────────────────────────────────
# MINING CONFIGURATION
# ──────────────────────────────────────────────────────

# Enable live Stratum connections (required for real mining)
HYBA_ENABLE_LIVE_STRATUM=true

# Allow development fixtures (disable in production!)
HYBA_ALLOW_DEV_FIXTURES=false

# Pool rotation interval (seconds)
HYBA_POOL_ROTATION_INTERVAL_SECONDS=180

# ──────────────────────────────────────────────────────
# OPERATOR AUTHENTICATION
# ──────────────────────────────────────────────────────
# Format: username:sha256_password_hash:role
# Example: mining_op:5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8:mining_operator
# (Above hash is for password "password" - CHANGE THIS!)

HYBA_OPERATOR_CREDENTIALS="mining_op:5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8:mining_operator"

# ──────────────────────────────────────────────────────
# JWT CONFIGURATION
# ──────────────────────────────────────────────────────
JWT_SECRET_KEY="$(openssl rand -hex 32)"
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# ──────────────────────────────────────────────────────
# POOL: NICEHASH (Recommended for beginners)
# ──────────────────────────────────────────────────────
# URL: Server location (eu, usa, jp, etc.)
HYBA_POOL_NICEHASH_URL="stratum+ssl://sha256.eu.nicehash.com:33334"

# Username: Your Bitcoin address + worker name
# Example: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa.PYTHIA001
HYBA_POOL_NICEHASH_USERNAME="YOUR_BTC_ADDRESS.PYTHIA001"

# Password: Usually just "x" for NiceHash
HYBA_POOL_NICEHASH_PASSWORD="x"

# Stratum version
HYBA_POOL_NICEHASH_STRATUM_VERSION=1

# ──────────────────────────────────────────────────────
# POOL: VIABTC (Alternative pool)
# ──────────────────────────────────────────────────────
HYBA_POOL_VIABTC_URL="stratum+tcp://btc.viabtc.io:3333"

# Username: YourPoolUsername.WorkerName
HYBA_POOL_VIABTC_USERNAME="YOUR_VIABTC_USERNAME.PYTHIA001"

# Password: Your worker password
HYBA_POOL_VIABTC_PASSWORD="YOUR_VIABTC_PASSWORD"

HYBA_POOL_VIABTC_STRATUM_VERSION=1

# ──────────────────────────────────────────────────────
# POOL: BRAIINS (Stratum V2 - Advanced)
# ──────────────────────────────────────────────────────
# HYBA_POOL_BRAIINS_URL="stratum2+tcp://eu.braiins-pool.com:3336"
# HYBA_POOL_BRAIINS_USERNAME="YOUR_BRAIINS_USERNAME.PYTHIA001"
# HYBA_POOL_BRAIINS_PASSWORD="YOUR_BRAIINS_PASSWORD"
# HYBA_POOL_BRAIINS_STRATUM_VERSION=2

# ──────────────────────────────────────────────────────
# POOL: CKPOOL (Solo mining - For testing only)
# ──────────────────────────────────────────────────────
# HYBA_POOL_CKPOOL_URL="stratum+tcp://solo.ckpool.org:3333"
# HYBA_POOL_CKPOOL_USERNAME="YOUR_BTC_ADDRESS"
# HYBA_POOL_CKPOOL_PASSWORD="x"
# HYBA_POOL_CKPOOL_STRATUM_VERSION=1

# ──────────────────────────────────────────────────────
# LOGGING
# ──────────────────────────────────────────────────────
LOG_LEVEL=INFO
PYTHIA_LOG_LEVEL=INFO

EOF

echo "✅ Created $ENV_FILE"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Edit $ENV_FILE and configure:"
echo "   - HYBA_OPERATOR_CREDENTIALS (change default password!)"
echo "   - HYBA_POOL_NICEHASH_USERNAME (your Bitcoin address)"
echo "   - Pool credentials for your preferred pools"
echo ""
echo "2. Generate secure password hash:"
echo "   echo -n 'your_password' | shasum -a 256"
echo ""
echo "3. Source the environment:"
echo "   source $ENV_FILE"
echo ""
echo "4. Start the API:"
echo "   cd python_backend"
echo "   python -m hyba_genesis_api.main"
echo ""
echo "5. Get authentication token:"
echo "   curl -X POST http://localhost:8000/api/auth/login \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"username\":\"mining_op\",\"password\":\"password\"}'"
echo ""
echo "6. Connect to pool (use token from step 5):"
echo "   curl -X POST http://localhost:8000/api/mining/connect \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -H 'Authorization: Bearer YOUR_TOKEN' \\"
echo "     -d '{\"pool_id\":\"nicehash\",\"worker\":\"PYTHIA.001\",\"password\":\"x\",\"capacity_ehs\":1.0}'"
echo ""
echo "⚠️  IMPORTANT SECURITY NOTES:"
echo "  - Change the default operator password immediately"
echo "  - Never commit .env files to version control"
echo "  - Use unique passwords for each pool"
echo "  - Enable 2FA on pool accounts"
echo "  - Monitor acceptance rates regularly"
echo ""
echo "📚 Documentation: MINING_SECURITY_FIXES.md"
echo ""
